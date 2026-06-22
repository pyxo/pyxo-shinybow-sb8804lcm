from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
import re

import serialx

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
  CONF_BAUDRATE,
  CONF_BYTESIZE,
  CONF_FLOW_CONTROL,
  CONF_PARITY,
  CONF_SERIAL_PORT,
  CONF_STOPBITS,
  DATA_BALANCE,
  DATA_ROUTE,
  DATA_VOLUME,
  DEVICE_MANUFACTURER,
  DEVICE_MODEL,
  DOMAIN,
  FLOW_CONTROL_DSRDTR,
  FLOW_CONTROL_RTSCTS,
  FLOW_CONTROL_XONXOFF,
  OUTPUT_COUNT,
)

_LOGGER = logging.getLogger(__name__)

OUTPUTALL_RE = re.compile(r"OUTPUTALL\s+([0-9]{24});", re.IGNORECASE)
VALUE_RE = re.compile(r"#([0-9]{3});", re.IGNORECASE)


class ShinybowSB8804LCMCoordinator(DataUpdateCoordinator[dict[str, dict[int, int | None]]]):
  def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
    self.entry = entry

    self.serial_port = entry.data[CONF_SERIAL_PORT]
    self.baudrate = entry.data[CONF_BAUDRATE]
    self.bytesize = entry.data[CONF_BYTESIZE]
    self.parity = entry.data[CONF_PARITY]
    self.stopbits = entry.data[CONF_STOPBITS]
    self.flow_control = entry.data[CONF_FLOW_CONTROL]

    self._serial_lock = asyncio.Lock()

    super().__init__(
      hass,
      _LOGGER,
      name=DOMAIN,
      update_interval=timedelta(seconds=30),
    )

  @property
  def device_info(self) -> DeviceInfo:
    return DeviceInfo(
      identifiers={(DOMAIN, self.entry.entry_id)},
      manufacturer=DEVICE_MANUFACTURER,
      model=DEVICE_MODEL,
      name=self.entry.title,
      sw_version="RS-232 Protocol V3",
    )

  async def _async_update_data(self) -> dict[str, dict[int, int | None]]:
    routes = {
      output_number: None
      for output_number in range(1, OUTPUT_COUNT + 1)
    }
    volumes = {
      output_number: None
      for output_number in range(1, OUTPUT_COUNT + 1)
    }
    balances = {
      output_number: None
      for output_number in range(1, OUTPUT_COUNT + 1)
    }

    try:
      routes = await self.async_get_all_outputs()

      for output_number in range(1, OUTPUT_COUNT + 1):
        volumes[output_number] = await self.async_get_volume(output_number)
        balances[output_number] = await self.async_get_balance(output_number)

      return {
        DATA_ROUTE: routes,
        DATA_VOLUME: volumes,
        DATA_BALANCE: balances,
      }

    except Exception as err:
      _LOGGER.warning(
        "Could not update Shinybow SB-8804LCM. Device may be disconnected: %s",
        err,
      )

      if self.data is not None:
        return self.data

      return {
        DATA_ROUTE: routes,
        DATA_VOLUME: volumes,
        DATA_BALANCE: balances,
      }

  async def async_send_command(
    self,
    command: str,
    timeout: float = 1.5,
  ) -> str:
    async with self._serial_lock:
      _LOGGER.debug(
        "Opening serial port %s baud=%s bytesize=%s parity=%s stopbits=%s flow=%s",
        self.serial_port,
        self.baudrate,
        self.bytesize,
        self.parity,
        self.stopbits,
        self.flow_control,
      )
      _LOGGER.debug("Sending Shinybow command: %s", command)

      try:
        reader, writer = await serialx.open_serial_connection(
          url=self.serial_port,
          baudrate=self.baudrate,
          bytesize=self.bytesize,
          parity=self.parity,
          stopbits=self.stopbits,
          xonxoff=self.flow_control == FLOW_CONTROL_XONXOFF,
          rtscts=self.flow_control == FLOW_CONTROL_RTSCTS,
          dsrdtr=self.flow_control == FLOW_CONTROL_DSRDTR,
        )

        try:
          writer.write(command.encode("ascii"))
          await writer.drain()

          try:
            response = await asyncio.wait_for(reader.readuntil(b";"), timeout)
          except asyncio.TimeoutError:
            response = b""
          except asyncio.IncompleteReadError as err:
            response = err.partial

          text = response.decode("ascii", errors="ignore").strip()
          _LOGGER.debug("Shinybow response: %s", text)
          return text

        finally:
          writer.close()
          await writer.wait_closed()

      except OSError as err:
        raise RuntimeError(f"Serial port error on {self.serial_port}: {err}") from err

  async def async_get_all_outputs(self) -> dict[int, int]:
    response = await self.async_send_command("OUTPUTALL ?;")

    match = OUTPUTALL_RE.search(response)
    if not match:
      raise RuntimeError(f"Unexpected OUTPUTALL response: {response!r}")

    raw = match.group(1)
    outputs = {}

    for index in range(OUTPUT_COUNT):
      output_number = index + 1
      input_number = int(raw[index * 3:index * 3 + 3])
      outputs[output_number] = input_number

    return outputs

  async def async_get_volume(self, output_number: int) -> int:
    response = await self.async_send_command(f"VOLUME{output_number:03d} ?;")
    return self._parse_value_response(response)

  async def async_get_balance(self, output_number: int) -> int:
    response = await self.async_send_command(f"BALANCE{output_number:03d} ?;")
    return self._parse_value_response(response)

  def _parse_value_response(self, response: str) -> int:
    match = VALUE_RE.search(response)

    if not match:
      raise RuntimeError(f"Unexpected value response: {response!r}")

    return int(match.group(1))

  async def async_set_output(self, output_number: int, input_number: int) -> None:
    command = f"OUTPUT{output_number:03d} {input_number:03d};"
    await self.async_send_command(command, timeout=0.75)
    await self.async_request_refresh()

  async def async_set_all_outputs(self, input_number: int) -> None:
    command = f"OUTPUTALL {input_number:03d};"
    await self.async_send_command(command, timeout=0.75)
    await self.async_request_refresh()

  async def async_set_volume(self, output_number: int, volume: int) -> None:
    command = f"VOLUME{output_number:03d} {volume:03d};"
    await self.async_send_command(command, timeout=0.75)

    if self.data is not None:
      self.data[DATA_VOLUME][output_number] = volume
      self.async_set_updated_data(self.data)

  async def async_set_balance(self, output_number: int, balance: int) -> None:
    command = f"BALANCE{output_number:03d} {balance:03d};"
    await self.async_send_command(command, timeout=0.75)

    if self.data is not None:
      self.data[DATA_BALANCE][output_number] = balance
      self.async_set_updated_data(self.data)
