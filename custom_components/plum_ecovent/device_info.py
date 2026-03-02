"""Helpers for reading and formatting static device identity registers."""
from __future__ import annotations

from typing import Any


def decode_utf8_registers(registers: list[int]) -> str | None:
    """Decode a UTF-8 string from 16-bit register words.

    Registers are interpreted as big-endian byte pairs and trailing NUL bytes
    are stripped.
    """
    if not registers:
        return None

    payload = bytearray()
    for value in registers:
        word = int(value) & 0xFFFF
        payload.append((word >> 8) & 0xFF)
        payload.append(word & 0xFF)

    raw = bytes(payload).split(b"\x00", 1)[0].strip()
    if not raw:
        return None

    try:
        decoded = raw.decode("utf-8", errors="strict").strip()
    except UnicodeDecodeError:
        decoded = raw.decode("latin-1", errors="ignore").strip()

    return decoded or None


def format_firmware(register_value: Any) -> str | None:
    """Format firmware register value into a readable version string.

    Vendor format for register 16 is documented as SXXX.YYY where high byte is
    major/build and low byte is minor/build.
    """
    if register_value is None:
        return None

    value = int(register_value) & 0xFFFF
    major = (value >> 8) & 0xFF
    minor = value & 0xFF
    return f"S{major}.{minor:03d}"
