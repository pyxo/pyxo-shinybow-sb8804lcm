"""One source selector per output and an all-output selector."""
from homeassistant.components.select import SelectEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .serial_client import route_command
from .names import channel_name, input_options


async def async_setup_entry(hass, entry, async_add_entities):
    matrix = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([OutputSelect(matrix, output) for output in [None, *range(1, 9)]])


class OutputSelect(CoordinatorEntity, SelectEntity):
    _attr_has_entity_name = True
    _attr_assumed_state = True
    _attr_icon = "mdi:audio-input-rca"

    def __init__(self, matrix, output):
        super().__init__(matrix)
        self.output = output
        self._attr_options = input_options(matrix.entry.options)
        self._attr_unique_id = f"{matrix.entry.entry_id}_output_{output or 'all'}"
        self._attr_name = f"{channel_name(matrix.entry.options, 'output', output)} source" if output else "All outputs source"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, matrix.entry.entry_id)},
            "name": matrix.entry.title, "manufacturer": "Shinybow", "model": "SB-8804LCM",
        }

    @property
    def current_option(self):
        values = set(self.coordinator.data.values()) if self.output is None else {self.coordinator.data[self.output]}
        if len(values) != 1:
            return None
        source = values.pop()
        return self._attr_options[source] if source is not None else None

    async def async_select_option(self, option):
        source = self._attr_options.index(option)
        await self.coordinator.send(route_command(self.output, source), self.output, source)
