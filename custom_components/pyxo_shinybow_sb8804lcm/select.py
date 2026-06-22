from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
  DATA_ROUTE,
  DOMAIN,
  INPUT_COUNT,
  OPTION_OFF,
  OUTPUT_COUNT,
)
from .coordinator import ShinybowSB8804LCMCoordinator
from .helpers import get_input_names, get_output_names


async def async_setup_entry(
  hass: HomeAssistant,
  entry: ConfigEntry,
  async_add_entities: AddEntitiesCallback,
) -> None:
  coordinator: ShinybowSB8804LCMCoordinator = hass.data[DOMAIN][entry.entry_id]

  entities = [
    ShinybowAllOutputsSelect(coordinator, entry),
  ]

  entities.extend(
    ShinybowOutputSelect(coordinator, entry, output_number)
    for output_number in range(1, OUTPUT_COUNT + 1)
  )

  async_add_entities(entities)


def _input_options(entry: ConfigEntry) -> list[str]:
  input_names = get_input_names(entry)

  return [
    OPTION_OFF,
    *[
      input_names[str(number)]
      for number in range(1, INPUT_COUNT + 1)
    ],
  ]


def _input_number_from_option(entry: ConfigEntry, option: str) -> int:
  if option == OPTION_OFF:
    return 0

  input_names = get_input_names(entry)

  return next(
    number
    for number in range(1, INPUT_COUNT + 1)
    if input_names[str(number)] == option
  )


class ShinybowAllOutputsSelect(CoordinatorEntity[ShinybowSB8804LCMCoordinator], SelectEntity):
  def __init__(
    self,
    coordinator: ShinybowSB8804LCMCoordinator,
    entry: ConfigEntry,
  ) -> None:
    super().__init__(coordinator)

    self._entry = entry

    self._attr_unique_id = f"{entry.entry_id}_all_outputs_route"
    self._attr_name = "All Outputs Source"
    self._attr_icon = "mdi:call-split"

  @property
  def device_info(self):
    return self.coordinator.device_info

  @property
  def options(self) -> list[str]:
    return _input_options(self._entry)

  @property
  def current_option(self) -> str | None:
    if self.coordinator.data is None:
      return None

    routes = self.coordinator.data[DATA_ROUTE]

    if not routes:
      return None

    selected_inputs = set(routes.values())

    if len(selected_inputs) != 1:
      return None

    input_number = selected_inputs.pop()

    if input_number == 0:
      return OPTION_OFF

    input_names = get_input_names(self._entry)
    return input_names[str(input_number)]

  async def async_select_option(self, option: str) -> None:
    input_number = _input_number_from_option(self._entry, option)

    await self.coordinator.async_set_all_outputs(input_number)


class ShinybowOutputSelect(CoordinatorEntity[ShinybowSB8804LCMCoordinator], SelectEntity):
  def __init__(
    self,
    coordinator: ShinybowSB8804LCMCoordinator,
    entry: ConfigEntry,
    output_number: int,
  ) -> None:
    super().__init__(coordinator)

    self._entry = entry
    self._output_number = output_number

    self._attr_unique_id = f"{entry.entry_id}_output_{output_number}_route"
    self._attr_icon = "mdi:audio-input-rca"

  @property
  def device_info(self):
    return self.coordinator.device_info

  @property
  def name(self) -> str:
    output_names = get_output_names(self._entry)
    output_name = output_names[str(self._output_number)]
    return f"{output_name} Source"

  @property
  def options(self) -> list[str]:
    return _input_options(self._entry)

  @property
  def current_option(self) -> str | None:
    if self.coordinator.data is None:
      return None

    input_number = self.coordinator.data[DATA_ROUTE].get(self._output_number)

    if input_number is None:
      return None

    if input_number == 0:
      return OPTION_OFF

    input_names = get_input_names(self._entry)
    return input_names[str(input_number)]

  async def async_select_option(self, option: str) -> None:
    input_number = _input_number_from_option(self._entry, option)

    await self.coordinator.async_set_output(
      self._output_number,
      input_number,
    )
