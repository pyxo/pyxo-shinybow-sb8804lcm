"""Shinybow SB-8804LCM optimistic serial control."""
import asyncio
import logging

import serial
import voluptuous as vol

from homeassistant.const import Platform, EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, NAME, CONF_SERIAL_PORT
from .serial_client import SerialClient, route_command

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SELECT]


class Matrix(DataUpdateCoordinator):
    """Publish last commanded routes, never pretend they are hardware feedback."""

    def __init__(self, hass, entry):
        super().__init__(hass, _LOGGER, name=NAME)
        self.entry = entry
        self.client = SerialClient(entry.data[CONF_SERIAL_PORT])
        self.command_lock = asyncio.Lock()
        self.async_set_updated_data({i: None for i in range(1, 9)})

    async def send(self, command, output=None, source=None):
        async with self.command_lock:
            try:
                await self.client.send_command(command)
            except asyncio.CancelledError:
                self.async_set_updated_data({i: None for i in range(1, 9)})
                raise
            except (OSError, serial.SerialException) as err:
                self.async_set_updated_data({i: None for i in range(1, 9)})
                raise HomeAssistantError(f"Serial command failed: {err}") from err
            routes = dict(self.data)
            if source is None:
                routes = {i: None for i in range(1, 9)}
            else:
                for i in (range(1, 9) if output is None else [output]):
                    routes[i] = source
            self.async_set_updated_data(routes)


async def async_setup_entry(hass: HomeAssistant, entry):
    matrix = Matrix(hass, entry)
    try:
        await matrix.client.connect()
    except (OSError, serial.SerialException) as err:
        raise ConfigEntryNotReady(f"Cannot open serial port: {err}") from err
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = matrix
    async def stop(_event):
        await matrix.client.close()
    entry.async_on_unload(hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, stop))
    try:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except BaseException:
        await matrix.client.close()
        hass.data[DOMAIN].pop(entry.entry_id, None)
        raise

    async def handle(call: ServiceCall):
        target = hass.data[DOMAIN].get(call.data["entry_id"])
        if target is None:
            raise HomeAssistantError("The selected matrix is not loaded")
        if call.service == "send_command":
            try:
                await target.send(call.data["command"])
            except ValueError as err:
                raise HomeAssistantError(str(err)) from err
        else:
            source = 0 if call.service == "all_off" else call.data["input"]
            output = call.data.get("output")
            await target.send(route_command(output, source), output, source)

    entry_field = {vol.Required("entry_id"): cv.string}
    schemas = {
        "set_route": vol.Schema({**entry_field, vol.Required("output"): vol.All(vol.Coerce(int), vol.Range(min=1, max=8)), vol.Required("input"): vol.All(vol.Coerce(int), vol.Range(min=0, max=8))}),
        "set_all_outputs": vol.Schema({**entry_field, vol.Required("input"): vol.All(vol.Coerce(int), vol.Range(min=0, max=8))}),
        "all_off": vol.Schema(entry_field),
        "send_command": vol.Schema({**entry_field, vol.Required("command"): cv.string}),
    }
    for name, schema in schemas.items():
        if not hass.services.has_service(DOMAIN, name):
            hass.services.async_register(DOMAIN, name, handle, schema=schema)
    return True


async def async_unload_entry(hass, entry):
    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return False
    matrix = hass.data[DOMAIN].pop(entry.entry_id)
    await matrix.client.close()
    if not hass.data[DOMAIN]:
        for name in ("set_route", "set_all_outputs", "all_off", "send_command"):
            hass.services.async_remove(DOMAIN, name)
    return True
