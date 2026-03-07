"""Async-safe loader for the registers module."""
from __future__ import annotations

import importlib
from typing import Any

from .const import DOMAIN

_REGISTERS_MODULE_NAME = "custom_components.plum_ecovent.registers"
_REGISTERS_CACHE_KEY = "_registers_module"


async def async_get_registers_module(hass: Any):
    """Load/cached registers module, importing in executor when possible."""
    if hass is not None and hasattr(hass, "data"):
        domain_data = hass.data.setdefault(DOMAIN, {})
        if isinstance(domain_data, dict):
            cached = domain_data.get(_REGISTERS_CACHE_KEY)
            if cached is not None:
                return cached
    else:
        domain_data = None

    if hass is not None and hasattr(hass, "async_add_executor_job"):
        module = await hass.async_add_executor_job(importlib.import_module, _REGISTERS_MODULE_NAME)
    else:
        module = importlib.import_module(_REGISTERS_MODULE_NAME)

    if isinstance(domain_data, dict):
        domain_data[_REGISTERS_CACHE_KEY] = module
    return module
