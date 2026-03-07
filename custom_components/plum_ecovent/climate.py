"""Climate platform for Plum Ecovent integration."""
from __future__ import annotations

import logging
from typing import Any

try:
    from homeassistant.components.climate import ClimateEntity
    from homeassistant.components.climate.const import (
        ClimateEntityFeature,
        FAN_HIGH,
        FAN_LOW,
        FAN_MEDIUM,
        FAN_OFF,
        HVACMode,
        PRESET_BOOST,
        PRESET_NONE,
    )
    try:
        from homeassistant.components.climate.const import ATTR_TEMPERATURE
    except ImportError:
        from homeassistant.const import ATTR_TEMPERATURE
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.const import UnitOfTemperature
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
except ImportError:  # Running outside Home Assistant for tests
    class ClimateEntity:  # type: ignore
        pass

    class ClimateEntityFeature:  # type: ignore
        TARGET_TEMPERATURE = 1
        TARGET_HUMIDITY = 2
        FAN_MODE = 4
        PRESET_MODE = 8

    class HVACMode:  # type: ignore
        AUTO = "auto"
        FAN_ONLY = "fan_only"

    class ConfigEntry:  # type: ignore
        pass

    class HomeAssistant:  # type: ignore
        pass

    class UnitOfTemperature:  # type: ignore
        CELSIUS = "°C"

    ATTR_TEMPERATURE = "temperature"  # type: ignore
    FAN_OFF = "off"  # type: ignore
    FAN_LOW = "low"  # type: ignore
    FAN_MEDIUM = "medium"  # type: ignore
    FAN_HIGH = "high"  # type: ignore
    PRESET_NONE = "none"  # type: ignore
    PRESET_BOOST = "boost"  # type: ignore

    from typing import Any as AddEntitiesCallback  # type: ignore

from .const import DOMAIN
from .coordinator import build_definition_key
from .registers_loader import async_get_registers_module

_LOGGER = logging.getLogger(__name__)

_UNIT_ON_OFF_REGISTER_ADDRESS = 59
_AUTO_MODE_REGISTER_ADDRESS = 78
_FAN_MODE_REGISTER_ADDRESS = 69
_BOOST_MODE_REGISTER_ADDRESS = 114

_FAN_MODE_TO_VALUE = {
    FAN_LOW: 1,
    FAN_MEDIUM: 2,
    FAN_HIGH: 3,
}
_VALUE_TO_FAN_MODE = {value: key for key, value in _FAN_MODE_TO_VALUE.items()}


def _definition_by_key(definitions: list[Any], key: str) -> Any | None:
    for definition in definitions:
        if str(getattr(definition, "key", "")) == key:
            return definition
    return None


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    entry_data = getattr(entry, "runtime_data", None)
    if not isinstance(entry_data, dict):
        entry_data = hass.data[DOMAIN][entry.entry_id]

    manager = entry_data["manager"]
    coordinator = entry_data.get("coordinator")
    device_info = entry_data.get("device_info")
    register_support = entry_data.get("register_support", {})
    available_registers_raw = register_support.get("available", []) if isinstance(register_support, dict) else []
    available_registers = {int(value) for value in available_registers_raw if str(value).isdigit()}
    has_availability_snapshot = isinstance(register_support, dict) and "available" in register_support

    registers = await async_get_registers_module(hass)
    number_defs = list(getattr(registers, "NUMBERS", []))
    sensor_defs = list(getattr(registers, "SENSORS", []))

    day_def = _definition_by_key(number_defs, "comfort_temperature_day")
    night_def = _definition_by_key(number_defs, "comfort_temperature_night")
    target_humidity_def = _definition_by_key(number_defs, "max_humidity")
    current_humidity_def = _definition_by_key(sensor_defs, "humidity")
    current_temp_def = _definition_by_key(sensor_defs, "leading_temperature")

    def _is_supported_register(address: int) -> bool:
        if not has_availability_snapshot:
            return True
        return int(address) in available_registers

    if (
        day_def is None
        or night_def is None
        or current_temp_def is None
        or not _is_supported_register(day_def.address)
        or not _is_supported_register(night_def.address)
        or not _is_supported_register(current_temp_def.address)
    ):
        _LOGGER.warning(
            "Climate entity not created for entry %s: missing required register definitions",
            entry.entry_id,
        )
        return

    entity = PlumEcoventClimate(
        manager=manager,
        coordinator=coordinator,
        entry=entry,
        day_def=day_def,
        night_def=night_def,
        current_temp_def=current_temp_def,
        target_humidity_def=target_humidity_def,
        current_humidity_def=current_humidity_def,
        can_power_unit=_is_supported_register(_UNIT_ON_OFF_REGISTER_ADDRESS),
        can_control_fan_stage=_is_supported_register(_FAN_MODE_REGISTER_ADDRESS),
        can_control_auto_mode=_is_supported_register(_AUTO_MODE_REGISTER_ADDRESS),
        can_control_boost_mode=_is_supported_register(_BOOST_MODE_REGISTER_ADDRESS),
        can_set_humidity=(
            target_humidity_def is not None and _is_supported_register(target_humidity_def.address)
        ),
        can_read_current_humidity=(
            current_humidity_def is not None and _is_supported_register(current_humidity_def.address)
        ),
        device_info=device_info,
    )
    async_add_entities([entity], True)


class PlumEcoventClimate(ClimateEntity):
    """Basic read/write climate entity without additional HVAC logic."""

    _attr_has_entity_name = True
    _attr_name = "Climate"
    _attr_should_poll = True
    _attr_hvac_modes = [HVACMode.FAN_ONLY]
    _attr_hvac_mode = HVACMode.FAN_ONLY
    _attr_fan_modes = []
    _attr_preset_modes = [PRESET_NONE]
    _attr_preset_mode = PRESET_NONE
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = 1
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE

    def __init__(
        self,
        *,
        manager,
        coordinator,
        entry: ConfigEntry,
        day_def,
        night_def,
        current_temp_def,
        target_humidity_def,
        current_humidity_def,
        can_power_unit: bool = True,
        can_control_fan_stage: bool = True,
        can_control_auto_mode: bool = True,
        can_control_boost_mode: bool = True,
        can_set_humidity: bool = True,
        can_read_current_humidity: bool = True,
        device_info=None,
    ) -> None:
        super().__init__()
        self._manager = manager
        self._coordinator = coordinator
        self._entry = entry
        self._day_def = day_def
        self._night_def = night_def
        self._current_temp_def = current_temp_def
        self._target_humidity_def = target_humidity_def
        self._current_humidity_def = current_humidity_def
        self._can_power_unit = can_power_unit
        self._can_control_fan_stage = can_control_fan_stage
        self._can_control_auto_mode = can_control_auto_mode
        self._can_control_boost_mode = can_control_boost_mode
        self._can_set_humidity = can_set_humidity and target_humidity_def is not None
        self._can_read_current_humidity = can_read_current_humidity and current_humidity_def is not None

        self._attr_unique_id = f"{entry.entry_id}_climate_main"
        self._attr_min_temp = float(
            self._day_def.min_value if self._day_def.min_value is not None else self._night_def.min_value
        )
        self._attr_max_temp = float(
            self._day_def.max_value if self._day_def.max_value is not None else self._night_def.max_value
        )

        self._attr_current_temperature = None
        self._attr_target_temperature = None
        self._attr_current_humidity = None
        self._attr_target_humidity = None
        self._attr_fan_mode = None

        supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
        if self._can_set_humidity:
            supported_features |= ClimateEntityFeature.TARGET_HUMIDITY
        if self._can_power_unit and self._can_control_fan_stage:
            self._attr_fan_modes = [FAN_OFF, FAN_LOW, FAN_MEDIUM, FAN_HIGH]
            supported_features |= ClimateEntityFeature.FAN_MODE
        if self._can_control_auto_mode:
            self._attr_hvac_modes = [HVACMode.AUTO, HVACMode.FAN_ONLY]
            self._attr_hvac_mode = HVACMode.AUTO
        if self._can_control_boost_mode:
            self._attr_preset_modes = [PRESET_NONE, PRESET_BOOST]
            supported_features |= ClimateEntityFeature.PRESET_MODE
        self._attr_supported_features = supported_features

        missing_controls: list[str] = []
        if not (self._can_power_unit and self._can_control_fan_stage):
            missing_controls.append("fan modes")
        if not self._can_control_auto_mode:
            missing_controls.append("auto hvac mode")
        if not self._can_control_boost_mode:
            missing_controls.append("boost preset")
        if not self._can_set_humidity:
            missing_controls.append("target humidity control")
        if not self._can_read_current_humidity:
            missing_controls.append("current humidity reading")
        if missing_controls:
            _LOGGER.warning(
                "Climate entity %s created with limited capabilities; missing: %s",
                self._attr_unique_id,
                ", ".join(missing_controls),
            )

        self._device_info = device_info or {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": self._entry.title,
            "manufacturer": "Plum",
            "model": "Ecovent",
        }

    @property
    def device_info(self):
        return self._device_info

    async def async_update(self) -> None:
        if self._coordinator is not None and hasattr(self._coordinator, "data"):
            values = self._coordinator.data or {}
            self._attr_current_temperature = self._coordinator_value(self._current_temp_def, values)
            day_target = self._coordinator_value(self._day_def, values)
            night_target = self._coordinator_value(self._night_def, values)
            self._attr_target_temperature = day_target if day_target is not None else night_target
            if self._can_set_humidity and self._target_humidity_def is not None:
                self._attr_target_humidity = self._coordinator_value(self._target_humidity_def, values)
            if self._can_read_current_humidity and self._current_humidity_def is not None:
                self._attr_current_humidity = self._coordinator_value(self._current_humidity_def, values)

        if self._can_control_auto_mode:
            auto_mode = await self._read_register(_AUTO_MODE_REGISTER_ADDRESS)
            if auto_mode is not None:
                self._attr_hvac_mode = HVACMode.AUTO if int(auto_mode) == 1 else HVACMode.FAN_ONLY

        if self._can_power_unit and self._can_control_fan_stage:
            unit_on = await self._read_register(_UNIT_ON_OFF_REGISTER_ADDRESS)
            operation_mode = await self._read_register(_FAN_MODE_REGISTER_ADDRESS)
            if unit_on is not None and int(unit_on) == 0:
                self._attr_fan_mode = FAN_OFF
            elif operation_mode is not None:
                self._attr_fan_mode = _VALUE_TO_FAN_MODE.get(int(operation_mode), FAN_OFF)

        if self._can_control_boost_mode:
            boost_mode = await self._read_register(_BOOST_MODE_REGISTER_ADDRESS)
            if boost_mode is not None:
                self._attr_preset_mode = PRESET_BOOST if int(boost_mode) > 0 else PRESET_NONE

    def _coordinator_value(self, definition, values: dict[str, Any]) -> Any:
        key = build_definition_key(definition)
        return values.get(key)

    async def _read_register(self, address: int) -> int | None:
        response = await self._manager.read_holding_registers(address, 1)
        if response is None or not hasattr(response, "registers") or not response.registers:
            return None
        return int(response.registers[0])

    async def _async_refresh_after_write(self) -> None:
        if self._coordinator is not None and hasattr(self._coordinator, "async_request_refresh"):
            await self._coordinator.async_request_refresh()

    async def _async_verify_register_value(self, address: int, expected: int, context: str) -> None:
        await self._async_refresh_after_write()
        actual = await self._read_register(address)
        if actual is None or int(actual) != int(expected):
            _LOGGER.warning(
                "Climate %s rejected %s change: expected register %s=%s, got %s",
                self._attr_unique_id,
                context,
                address,
                expected,
                actual,
            )
            raise ValueError(f"Unit did not accept {context} change")

    async def _async_verify_temperature_setpoint(self, target: int) -> None:
        await self._async_refresh_after_write()
        day_actual = await self._read_register(int(self._day_def.address))
        night_actual = await self._read_register(int(self._night_def.address))
        if day_actual is None or night_actual is None or int(day_actual) != target or int(night_actual) != target:
            _LOGGER.warning(
                "Climate %s rejected temperature change: expected day/night=%s, got day=%s night=%s",
                self._attr_unique_id,
                target,
                day_actual,
                night_actual,
            )
            raise ValueError("Unit did not accept target temperature change")

    async def async_set_temperature(self, **kwargs: Any) -> None:
        raw_target = kwargs.get(ATTR_TEMPERATURE)
        if raw_target is None:
            return

        target = int(round(float(raw_target)))
        wrote_day = await self._manager.write_register(int(self._day_def.address), target)
        wrote_night = await self._manager.write_register(int(self._night_def.address), target)
        if not (wrote_day and wrote_night):
            raise ValueError("Failed to write comfort temperature setpoint registers")

        await self._async_verify_temperature_setpoint(target)
        self._attr_target_temperature = float(target)

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        if not (self._can_power_unit and self._can_control_fan_stage):
            raise ValueError("Fan mode control is not supported by this ERV")

        if fan_mode == FAN_OFF:
            success = await self._manager.write_register(_UNIT_ON_OFF_REGISTER_ADDRESS, 0)
            if not success:
                raise ValueError("Failed to turn off ERV")
            await self._async_verify_register_value(_UNIT_ON_OFF_REGISTER_ADDRESS, 0, "fan off")
            self._attr_fan_mode = FAN_OFF
            return

        mode_value = _FAN_MODE_TO_VALUE.get(fan_mode)
        if mode_value is None:
            raise ValueError(f"Unsupported fan mode: {fan_mode}")

        turned_on = await self._manager.write_register(_UNIT_ON_OFF_REGISTER_ADDRESS, 1)
        set_mode = await self._manager.write_register(_FAN_MODE_REGISTER_ADDRESS, mode_value)
        if not (turned_on and set_mode):
            raise ValueError("Failed to write fan mode register")
        await self._async_verify_register_value(_UNIT_ON_OFF_REGISTER_ADDRESS, 1, "fan mode")
        await self._async_verify_register_value(_FAN_MODE_REGISTER_ADDRESS, mode_value, "fan mode")
        self._attr_fan_mode = fan_mode

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if not self._can_control_auto_mode:
            raise ValueError("HVAC mode control is not supported by this ERV")

        if hvac_mode not in (HVACMode.AUTO, HVACMode.FAN_ONLY):
            raise ValueError(f"Unsupported HVAC mode: {hvac_mode}")

        if hvac_mode in (HVACMode.AUTO, HVACMode.FAN_ONLY):
            turned_on = await self._async_ensure_unit_on()
            if not turned_on:
                raise ValueError("Failed to turn on ERV before changing HVAC mode")

        target = 1 if hvac_mode == HVACMode.AUTO else 0
        success = await self._manager.write_register(_AUTO_MODE_REGISTER_ADDRESS, target)
        if not success:
            raise ValueError("Failed to write auto mode register")
        await self._async_verify_register_value(_AUTO_MODE_REGISTER_ADDRESS, target, "hvac mode")
        self._attr_hvac_mode = hvac_mode

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        if not self._can_control_boost_mode:
            raise ValueError("Preset mode control is not supported by this ERV")

        if preset_mode not in (PRESET_NONE, PRESET_BOOST):
            raise ValueError(f"Unsupported preset mode: {preset_mode}")

        if preset_mode == PRESET_BOOST:
            turned_on = await self._async_ensure_unit_on()
            if not turned_on:
                raise ValueError("Failed to turn on ERV before enabling boost mode")

        boost_value = 1 if preset_mode == PRESET_BOOST else 0
        success = await self._manager.write_register(_BOOST_MODE_REGISTER_ADDRESS, boost_value)
        if not success:
            raise ValueError("Failed to write boost mode register")
        await self._async_verify_register_value(_BOOST_MODE_REGISTER_ADDRESS, boost_value, "preset mode")
        self._attr_preset_mode = preset_mode

    async def async_set_humidity(self, humidity: int) -> None:
        if not self._can_set_humidity or self._target_humidity_def is None:
            return

        target_humidity = int(round(float(humidity)))
        success = await self._manager.write_register(int(self._target_humidity_def.address), target_humidity)
        if not success:
            raise ValueError("Failed to write target humidity register")

        await self._async_verify_register_value(int(self._target_humidity_def.address), target_humidity, "humidity")
        self._attr_target_humidity = target_humidity

    async def _async_ensure_unit_on(self) -> bool:
        if not self._can_power_unit:
            return True

        current_state = await self._read_register(_UNIT_ON_OFF_REGISTER_ADDRESS)
        if current_state is None:
            return bool(await self._manager.write_register(_UNIT_ON_OFF_REGISTER_ADDRESS, 1))
        if int(current_state) == 1:
            return True
        return bool(await self._manager.write_register(_UNIT_ON_OFF_REGISTER_ADDRESS, 1))
