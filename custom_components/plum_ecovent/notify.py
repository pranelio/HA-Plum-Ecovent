"""Notify platform for Plum Ecovent integration alarm notifications."""
from __future__ import annotations

import logging
from typing import Any

try:
    from homeassistant.components import persistent_notification
    from homeassistant.components.notify import NotifyEntity
    from homeassistant.components.notify.const import ATTR_TITLE
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeassistant.helpers.update_coordinator import CoordinatorEntity
except Exception:  # Running outside Home Assistant for tests
    class NotifyEntity:  # type: ignore
        pass

    class CoordinatorEntity:  # type: ignore
        def __init__(self, coordinator=None):
            self.coordinator = coordinator

    class ConfigEntry:  # type: ignore
        pass

    class HomeAssistant:  # type: ignore
        pass

    ATTR_TITLE = "title"  # type: ignore

    from typing import Any as AddEntitiesCallback  # type: ignore

from .const import DOMAIN
from .coordinator import build_definition_key

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    entry_data = getattr(entry, "runtime_data", None)
    if not isinstance(entry_data, dict):
        entry_data = hass.data[DOMAIN][entry.entry_id]

    coordinator = entry_data.get("coordinator")
    notification_definitions = list(entry_data.get("notification_definitions", []) or [])
    device_info = entry_data.get("device_info")

    if coordinator is None or not notification_definitions:
        return

    async_add_entities(
        [
            PlumEcoventIssueNotifyEntity(
                coordinator=coordinator,
                entry=entry,
                definitions=notification_definitions,
                device_info=device_info,
            )
        ],
        True,
    )


class PlumEcoventIssueNotifyEntity(CoordinatorEntity, NotifyEntity):
    """Notify entity that surfaces alarm/problem states as persistent notifications."""

    _attr_has_entity_name = True
    _attr_name = "Issues"
    _attr_should_poll = False

    def __init__(self, *, coordinator, entry: ConfigEntry, definitions: list[Any], device_info=None) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._definitions = definitions
        self._active_states: dict[str, bool] = {}
        self._attr_unique_id = f"{entry.entry_id}_notify_issues"
        self._device_info = device_info or {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": self._entry.title,
            "manufacturer": "Plum",
            "model": "Ecovent",
        }

    @property
    def device_info(self):
        return self._device_info

    async def async_added_to_hass(self) -> None:
        if hasattr(super(), "async_added_to_hass"):
            await super().async_added_to_hass()
        self._process_issue_transitions()

    def _handle_coordinator_update(self) -> None:
        self._process_issue_transitions()
        if hasattr(super(), "_handle_coordinator_update"):
            super()._handle_coordinator_update()

    def _notification_id(self, definition: Any) -> str:
        stable_key = getattr(definition, "key", None) or getattr(definition, "name", "alarm")
        key_slug = str(stable_key).replace(" ", "_").lower()
        return f"{DOMAIN}_{self._entry.entry_id}_{key_slug}"

    def _process_issue_transitions(self) -> None:
        if not hasattr(self, "hass") or self.hass is None:
            return

        values = (self.coordinator.data if self.coordinator is not None else {}) or {}

        for definition in self._definitions:
            key = build_definition_key(definition)
            is_active = bool(values.get(key))
            was_active = bool(self._active_states.get(key, False))
            notification_id = self._notification_id(definition)

            if is_active and not was_active:
                persistent_notification.async_create(
                    self.hass,
                    (
                        f"{definition.name} is active on device '{self._entry.title}'. "
                        "The condition reported by the ERV requires attention."
                    ),
                    title=f"{self._entry.title} alarm",
                    notification_id=notification_id,
                )
            elif not is_active and was_active:
                persistent_notification.async_dismiss(self.hass, notification_id)

            self._active_states[key] = is_active

    async def async_send_message(self, message: str, **kwargs: Any) -> None:
        if not hasattr(self, "hass") or self.hass is None:
            return

        title = kwargs.get(ATTR_TITLE) or f"{self._entry.title} notification"
        persistent_notification.async_create(
            self.hass,
            message,
            title=title,
            notification_id=f"{DOMAIN}_{self._entry.entry_id}_manual",
        )
