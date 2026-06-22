from __future__ import annotations

from homeassistant.config_entries import ConfigEntry

from .const import (
  CONF_INPUT_NAMES,
  CONF_OUTPUT_NAMES,
  INPUT_COUNT,
  OUTPUT_COUNT,
)


def default_input_names() -> dict[str, str]:
  return {
    str(number): f"Input {number}"
    for number in range(1, INPUT_COUNT + 1)
  }


def default_output_names() -> dict[str, str]:
  return {
    str(number): f"Output {number}"
    for number in range(1, OUTPUT_COUNT + 1)
  }


def get_input_names(entry: ConfigEntry) -> dict[str, str]:
  names = default_input_names()
  names.update(entry.options.get(CONF_INPUT_NAMES, {}))
  return names


def get_output_names(entry: ConfigEntry) -> dict[str, str]:
  names = default_output_names()
  names.update(entry.options.get(CONF_OUTPUT_NAMES, {}))
  return names
