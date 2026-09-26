"""UI setup and port reconfiguration without changing device identity."""
import glob
import os

import voluptuous as vol
from serial.tools import list_ports
from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import CONF_SERIAL_PORT, DOMAIN, NAME


def ports():
    return sorted(set(glob.glob("/dev/serial/by-id/*"))) + sorted({p.device for p in list_ports.comports()})


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        return await self._form("user", user_input)

    async def async_step_reconfigure(self, user_input=None):
        return await self._form("reconfigure", user_input)

    async def _form(self, step, user_input):
        entry = self._get_reconfigure_entry() if step == "reconfigure" else None
        errors = {}
        if user_input is not None:
            path = user_input[CONF_SERIAL_PORT].strip()
            if not path.startswith("/dev/") or not user_input["name"].strip():
                errors["base"] = "invalid_config"
            else:
                paths = [e.data[CONF_SERIAL_PORT] for e in self._async_current_entries() if e != entry]
                resolved = await self.hass.async_add_executor_job(lambda: [os.path.realpath(p) for p in [path, *paths]])
                if resolved[0] in resolved[1:]:
                    return self.async_abort(reason="already_configured")
                data = {CONF_SERIAL_PORT: path, "name": user_input["name"].strip()}
                if entry:
                    return self.async_update_reload_and_abort(entry, data_updates=data, title=data["name"], unique_id=resolved[0])
                await self.async_set_unique_id(resolved[0])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=data["name"], data=data)
        available = await self.hass.async_add_executor_job(ports)
        defaults = user_input or (entry.data if entry else {})
        return self.async_show_form(step_id=step, errors=errors, data_schema=vol.Schema({
            vol.Required("name", default=defaults.get("name", NAME)): str,
            vol.Required(CONF_SERIAL_PORT, default=defaults.get(CONF_SERIAL_PORT, available[0] if available else "/dev/serial/by-id/")): selector.SelectSelector(selector.SelectSelectorConfig(options=available, custom_value=True, mode=selector.SelectSelectorMode.DROPDOWN)),
        }))
