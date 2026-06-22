from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
  DATA_BALANCE,
  DATA_VOLUME,
  DOMAIN,
  OUTPUT_COUNT,
)
from .coordinator import ShinybowSB8804LCMCoordinator
from .helpers import get_output_names


async def async_setup_entry(
  hass: HomeAssistant,
  entry: ConfigEntry,
  async_add_entities: AddEntitiesCallback,
) -> None:
  coordinator: ShinybowSB8804LCMCoordinator = hass.data[DOMAIN][entry.entry_id]

  entities = []

  for output_number in range(1, OUTPUT_COUNT + 1):
    entities.append(ShinybowOutputVolumeNumber(coordinator, entry, output_number))
    entities.append(ShinybowOutputBalanceNumber(coordinator, entry, output_number))

  async_add_entities(entities)


class ShinybowOutputVolumeNumber(CoordinatorEntity[ShinybowSB8804LCMCoordinator], NumberEntity):
  def __init__(
    self,
    coordinator: ShinybowSB8804LCMCoordinator,
    entry: ConfigEntry,
    output_number: int,
  ) -> None:
    super().__init__(coordinator)

    self._entry = entry
    self._output_number = output_number

    self._attr_unique_id = f"{entry.entry_id}_output_{output_number}_volume"
    self._attr_icon = "mdi:volume-high"
    self._attr_native_min_value = 0
    self._attr_native_max_value = 100
    self._attr_native_step = 1
    self._attr_native_unit_of_measurement = PERCENTAGE
    self._attr_mode = NumberMode.SLIDER

  @property
  def device_info(self):
    return self.coordinator.device_info

  @property
  def name(self) -> str:
    output_names = get_output_names(self._entry)
    return f"{output_names[str(self._output_number)]} Volume"

  @property
  def native_value(self) -> int | None:
    if self.coordinator.data is None:
      return None

    return self.coordinator.data[DATA_VOLUME].get(self._output_number)

  async def async_set_native_value(self, value: float) -> None:
    await self.coordinator.async_set_volume(
      self._output_number,
      int(value),
    )


class ShinybowOutputBalanceNumber(CoordinatorEntity[ShinybowSB8804LCMCoordinator], NumberEntity):
  def __init__(
    self,
    coordinator: ShinybowSB8804LCMCoordinator,
    entry: ConfigEntry,
    output_number: int,
  ) -> None:
    super().__init__(coordinator)

    self._entry = entry
    self._output_number = output_number

    self._attr_unique_id = f"{entry.entry_id}_output_{output_number}_balance"
    self._attr_icon = "mdi:scale-balance"
    self._attr_native_min_value = 0
    self._attr_native_max_value = 100
    self._attr_native_step = 1
    self._attr_native_unit_of_measurement = PERCENTAGE
    self._attr_mode = NumberMode.SLIDER

  @property
  def device_info(self):
    return self.coordinator.device_info

  @property
  def name(self) -> str:
    output_names = get_output_names(self._entry)
    return f"{output_names[str(self._output_number)]} Balance"

  @property
  def native_value(self) -> int | None:
    if self.coordinator.data is None:
      return None

    return self.coordinator.data[DATA_BALANCE].get(self._output_number)

  async def async_set_native_value(self, value: float) -> None:
    await self.coordinator.async_set_balance(
      self._output_number,
      int(value),
    )
