"""Select entities for Scent Diffuser."""
from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, DeviceType
from .device import ScentDiffuserDevice

_LOGGER = logging.getLogger(__name__)

MODE_CUSTOM = "Custom"
MODE_LEVEL = "Level"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up select entities."""
    device: ScentDiffuserDevice = hass.data[DOMAIN][entry.entry_id]

    entities: list[SelectEntity] = []
    # The Custom/Level schedule mode is an AK V3 concept. The entity stays
    # unavailable until the device identifies as V3 on first connect, so it's
    # safe to register for the whole AK family (V2 simply never exposes it).
    if device.device_type == DeviceType.SCENT_MARKETING_AK:
        entities.append(ScheduleModeSelect(device, entry))

    async_add_entities(entities)


class ScheduleModeSelect(SelectEntity):
    """Custom vs Level schedule-mode selector for AK V3 (@Mins95, #8).

    The integration already switches mode implicitly (setting a Work/Pause
    Duration selects Custom, setting Intensity selects Level). This makes the
    mode an explicit control so the user can pin it without accidentally
    flipping it via a side-effect of another change.
    """

    _attr_has_entity_name = True
    _attr_name = "Schedule mode"
    _attr_icon = "mdi:tune-variant"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_options = [MODE_LEVEL, MODE_CUSTOM]

    def __init__(self, device: ScentDiffuserDevice, entry: ConfigEntry) -> None:
        self._device = device
        self._attr_unique_id = f"{device.unique_id}_schedule_mode"
        self._attr_device_info = device.device_info
        device.register_state_callback(self._on_state_update)

    def _on_state_update(self) -> None:
        if self.hass is None:
            return
        self.async_write_ha_state()

    @property
    def current_option(self) -> str | None:
        mode = self._device.state.schedule_custom_mode
        if mode is None:
            return None
        return MODE_CUSTOM if mode else MODE_LEVEL

    @property
    def available(self) -> bool:
        return (
            self._device.available
            and self._device.protocol_is_v3
            and self._device.state.schedule_custom_mode is not None
        )

    async def async_select_option(self, option: str) -> None:
        await self._device.set_schedule_mode(option == MODE_CUSTOM)
