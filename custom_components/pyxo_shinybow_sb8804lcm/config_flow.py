from __future__ import annotations

from pathlib import Path

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import (
  CONF_BAUDRATE,
  CONF_BYTESIZE,
  CONF_FLOW_CONTROL,
  CONF_INPUT_NAMES,
  CONF_NAME,
  CONF_OUTPUT_NAMES,
  CONF_PARITY,
  CONF_SERIAL_PORT,
  CONF_STOPBITS,
  DEFAULT_BAUDRATE,
  DEFAULT_BYTESIZE,
  DEFAULT_FLOW_CONTROL,
  DEFAULT_NAME,
  DEFAULT_PARITY,
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
from .helpers import (
  default_input_names,
  default_output_names,
  get_input_names,
  get_output_names,
)

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


def _get_by_id_serial_ports() -> list[str]:
  by_id_path = Path("/dev/serial/by-id")

  if by_id_path.exists():
    ports = sorted(str(path) for path in by_id_path.iterdir() if path.exists())
    if ports:
      return ports

  try:
    from serial.tools import list_ports
  except ImportError:
    return [DEFAULT_SERIAL_PORT]

  ports = sorted(port.device for port in list_ports.comports() if port.device)

  if ports:
    return ports

  return [DEFAULT_SERIAL_PORT]


class PyxoShinybowSB8804LCMConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
  VERSION = 1

  def __init__(self) -> None:
    self._setup_data: dict | None = None

  @staticmethod
  def async_get_options_flow(config_entry):
    return PyxoShinybowSB8804LCMOptionsFlow(config_entry)

  async def async_step_user(self, user_input=None):
    errors = {}
    serial_ports = await self.hass.async_add_executor_job(_get_by_id_serial_ports)

    if user_input is not None:
      self._setup_data = dict(user_input)
      self._setup_data[CONF_BAUDRATE] = int(self._setup_data[CONF_BAUDRATE])
      self._setup_data[CONF_BYTESIZE] = int(self._setup_data[CONF_BYTESIZE])
      self._setup_data[CONF_STOPBITS] = float(self._setup_data[CONF_STOPBITS])

      await self.async_set_unique_id(self._setup_data[CONF_SERIAL_PORT])
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
      step_id="user",
      data_schema=schema,
      errors=errors,
    )

  async def async_step_names(self, user_input=None):
    if self._setup_data is None:
      return await self.async_step_user()

    if user_input is not None:
      input_names = {}
      output_names = {}

      for number in range(1, INPUT_COUNT + 1):
        input_names[str(number)] = user_input[f"input_{number}_name"]

      for number in range(1, OUTPUT_COUNT + 1):
        output_names[str(number)] = user_input[f"output_{number}_name"]

      return self.async_create_entry(
        title=self._setup_data[CONF_NAME],
        data=self._setup_data,
        options={
          CONF_INPUT_NAMES: input_names,
          CONF_OUTPUT_NAMES: output_names,
        },
      )

    input_names = default_input_names()
    output_names = default_output_names()
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
