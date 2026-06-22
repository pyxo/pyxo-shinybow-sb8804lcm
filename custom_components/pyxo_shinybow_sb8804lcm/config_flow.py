from __future__ import annotations

import glob
import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import (
  CONF_BAUDRATE,
  CONF_BYTESIZE,
  CONF_CONNECTION_TYPE,
  CONF_FLOW_CONTROL,
  CONF_HOST,
  CONF_INPUT_NAMES,
  CONF_NAME,
  CONF_OUTPUT_NAMES,
  CONF_PARITY,
  CONF_PORT,
  CONF_SERIAL_PORT,
  CONF_STOPBITS,
  CONNECTION_TYPE_LOCAL,
  CONNECTION_TYPE_TCP,
  DEFAULT_BAUDRATE,
  DEFAULT_BYTESIZE,
  DEFAULT_FLOW_CONTROL,
  DEFAULT_HOST,
  DEFAULT_NAME,
  DEFAULT_PARITY,
  DEFAULT_PORT,
  DEFAULT_SERIAL_PORT,
  DEFAULT_STOPBITS,
  DOMAIN,
  FLOW_CONTROL_DSRDTR,
  FLOW_CONTROL_NONE,
  FLOW_CONTROL_RTSCTS,
  FLOW_CONTROL_XONXOFF,
  INPUT_COUNT,
  OUTPUT_COUNT,
)

_LOGGER = logging.getLogger(__name__)

BAUDRATE_OPTIONS = [
  "1200",
  "2400",
  "4800",
  "9600",
  "19200",
  "38400",
  "57600",
  "115200",
]

BYTESIZE_OPTIONS = ["7", "8"]

PARITY_OPTIONS = [
  selector.SelectOptionDict(value="N", label="None"),
  selector.SelectOptionDict(value="E", label="Even"),
  selector.SelectOptionDict(value="O", label="Odd"),
]

STOPBITS_OPTIONS = ["1", "1.5", "2"]

FLOW_CONTROL_OPTIONS = [
  selector.SelectOptionDict(value=FLOW_CONTROL_NONE, label="None"),
  selector.SelectOptionDict(value=FLOW_CONTROL_RTSCTS, label="RTS/CTS"),
  selector.SelectOptionDict(value=FLOW_CONTROL_XONXOFF, label="XON/XOFF"),
  selector.SelectOptionDict(value=FLOW_CONTROL_DSRDTR, label="DSR/DTR"),
]

CONNECTION_TYPE_OPTIONS = [
  selector.SelectOptionDict(value=CONNECTION_TYPE_LOCAL, label="Local RS232"),
  selector.SelectOptionDict(value=CONNECTION_TYPE_TCP, label="TCP/IP to RS232"),
]


def _default_input_names() -> dict[str, str]:
  return {
    str(number): f"Input {number}"
    for number in range(1, INPUT_COUNT + 1)
  }


def _default_output_names() -> dict[str, str]:
  return {
    str(number): f"Output {number}"
    for number in range(1, OUTPUT_COUNT + 1)
  }


def get_input_names(entry: config_entries.ConfigEntry) -> dict[str, str]:
  names = _default_input_names()
  names.update(entry.options.get(CONF_INPUT_NAMES, {}))
  return names


def get_output_names(entry: config_entries.ConfigEntry) -> dict[str, str]:
  names = _default_output_names()
  names.update(entry.options.get(CONF_OUTPUT_NAMES, {}))
  return names


def _get_serial_ports() -> list[str]:
  ports: list[str] = []

  by_id_ports = sorted(glob.glob("/dev/serial/by-id/*"))
  ports.extend(by_id_ports)

  if not ports:
    try:
      from serial.tools import list_ports

      for port in list_ports.comports():
        if port.device:
          ports.append(port.device)
    except ImportError:
      _LOGGER.debug("serial.tools.list_ports is not available")

  if DEFAULT_SERIAL_PORT not in ports:
    ports.append(DEFAULT_SERIAL_PORT)

  return ports


class PyxoShinybowSB8804LCMConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
  VERSION = 1

  def __init__(self) -> None:
    self._data: dict = {}

  @staticmethod
  def async_get_options_flow(config_entry: config_entries.ConfigEntry):
    return PyxoShinybowSB8804LCMOptionsFlow(config_entry)

  async def async_step_user(self, user_input=None):
    if user_input is not None:
      self._data[CONF_CONNECTION_TYPE] = user_input[CONF_CONNECTION_TYPE]

      if user_input[CONF_CONNECTION_TYPE] == CONNECTION_TYPE_LOCAL:
        return await self.async_step_local()

      return await self.async_step_tcp()

    schema = vol.Schema(
      {
        vol.Required(
          CONF_CONNECTION_TYPE,
          default=CONNECTION_TYPE_LOCAL,
        ): selector.SelectSelector(
          selector.SelectSelectorConfig(
            options=CONNECTION_TYPE_OPTIONS,
            mode=selector.SelectSelectorMode.DROPDOWN,
          )
        ),
      }
    )

    return self.async_show_form(
      step_id="user",
      data_schema=schema,
    )

  async def async_step_local(self, user_input=None):
    errors = {}

    serial_ports = await self.hass.async_add_executor_job(_get_serial_ports)

    if user_input is not None:
      user_input = dict(user_input)

      self._data.update(
        {
          CONF_NAME: user_input[CONF_NAME],
          CONF_SERIAL_PORT: user_input[CONF_SERIAL_PORT],
          CONF_BAUDRATE: int(user_input[CONF_BAUDRATE]),
          CONF_BYTESIZE: int(user_input[CONF_BYTESIZE]),
          CONF_PARITY: user_input[CONF_PARITY],
          CONF_STOPBITS: float(user_input[CONF_STOPBITS]),
          CONF_FLOW_CONTROL: user_input[CONF_FLOW_CONTROL],
        }
      )

      unique_id = f"local:{self._data[CONF_SERIAL_PORT]}"
      await self.async_set_unique_id(unique_id)
      self._abort_if_unique_id_configured()

      return await self.async_step_names()

    schema = vol.Schema(
      {
        vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
        vol.Required(CONF_SERIAL_PORT, default=serial_ports[0]): selector.SelectSelector(
          selector.SelectSelectorConfig(
            options=serial_ports,
            custom_value=True,
            mode=selector.SelectSelectorMode.DROPDOWN,
          )
        ),
        vol.Required(CONF_BAUDRATE, default=str(DEFAULT_BAUDRATE)): selector.SelectSelector(
          selector.SelectSelectorConfig(
            options=BAUDRATE_OPTIONS,
            custom_value=True,
            mode=selector.SelectSelectorMode.DROPDOWN,
          )
        ),
        vol.Required(CONF_BYTESIZE, default=str(DEFAULT_BYTESIZE)): selector.SelectSelector(
          selector.SelectSelectorConfig(
            options=BYTESIZE_OPTIONS,
            mode=selector.SelectSelectorMode.DROPDOWN,
          )
        ),
        vol.Required(CONF_PARITY, default=DEFAULT_PARITY): selector.SelectSelector(
          selector.SelectSelectorConfig(
            options=PARITY_OPTIONS,
            mode=selector.SelectSelectorMode.DROPDOWN,
          )
        ),
        vol.Required(CONF_STOPBITS, default=str(DEFAULT_STOPBITS)): selector.SelectSelector(
          selector.SelectSelectorConfig(
            options=STOPBITS_OPTIONS,
            mode=selector.SelectSelectorMode.DROPDOWN,
          )
        ),
        vol.Required(CONF_FLOW_CONTROL, default=DEFAULT_FLOW_CONTROL): selector.SelectSelector(
          selector.SelectSelectorConfig(
            options=FLOW_CONTROL_OPTIONS,
            mode=selector.SelectSelectorMode.DROPDOWN,
          )
        ),
      }
    )

    return self.async_show_form(
      step_id="local",
      data_schema=schema,
      errors=errors,
    )

  async def async_step_tcp(self, user_input=None):
    errors = {}

    if user_input is not None:
      user_input = dict(user_input)

      self._data.update(
        {
          CONF_NAME: user_input[CONF_NAME],
          CONF_HOST: user_input[CONF_HOST],
          CONF_PORT: int(user_input[CONF_PORT]),
        }
      )

      unique_id = f"tcp:{self._data[CONF_HOST]}:{self._data[CONF_PORT]}"
      await self.async_set_unique_id(unique_id)
      self._abort_if_unique_id_configured()

      return await self.async_step_names()

    schema = vol.Schema(
      {
        vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
        vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
      }
    )

    return self.async_show_form(
      step_id="tcp",
      data_schema=schema,
      errors=errors,
    )

  async def async_step_names(self, user_input=None):
    if user_input is not None:
      input_names = {}
      output_names = {}

      for number in range(1, INPUT_COUNT + 1):
        input_names[str(number)] = user_input[f"input_{number}_name"]

      for number in range(1, OUTPUT_COUNT + 1):
        output_names[str(number)] = user_input[f"output_{number}_name"]

      return self.async_create_entry(
        title=self._data[CONF_NAME],
        data=self._data,
        options={
          CONF_INPUT_NAMES: input_names,
          CONF_OUTPUT_NAMES: output_names,
        },
      )

    input_names = _default_input_names()
    output_names = _default_output_names()
    schema_fields = {}

    for number in range(1, INPUT_COUNT + 1):
      schema_fields[
        vol.Required(
          f"input_{number}_name",
          default=input_names[str(number)],
        )
      ] = str

    for number in range(1, OUTPUT_COUNT + 1):
      schema_fields[
        vol.Required(
          f"output_{number}_name",
          default=output_names[str(number)],
        )
      ] = str

    return self.async_show_form(
      step_id="names",
      data_schema=vol.Schema(schema_fields),
    )


class PyxoShinybowSB8804LCMOptionsFlow(config_entries.OptionsFlow):
  def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
    self._config_entry = config_entry

  async def async_step_init(self, user_input=None):
    if user_input is not None:
      input_names = {}
      output_names = {}

      for number in range(1, INPUT_COUNT + 1):
        input_names[str(number)] = user_input[f"input_{number}_name"]

      for number in range(1, OUTPUT_COUNT + 1):
        output_names[str(number)] = user_input[f"output_{number}_name"]

      return self.async_create_entry(
        title="",
        data={
          CONF_INPUT_NAMES: input_names,
          CONF_OUTPUT_NAMES: output_names,
        },
      )

    input_names = get_input_names(self._config_entry)
    output_names = get_output_names(self._config_entry)
    schema_fields = {}

    for number in range(1, INPUT_COUNT + 1):
      schema_fields[
        vol.Required(
          f"input_{number}_name",
          default=input_names[str(number)],
        )
      ] = str

    for number in range(1, OUTPUT_COUNT + 1):
      schema_fields[
        vol.Required(
          f"output_{number}_name",
          default=output_names[str(number)],
        )
      ] = str

    return self.async_show_form(
      step_id="init",
      data_schema=vol.Schema(schema_fields),
    )
