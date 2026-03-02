"""Constants for the Plum Ecovent integration."""

DOMAIN = "plum_ecovent"
DEFAULT_NAME = "Plum Ecovent"

# Config keys
CONF_HOST = "host"
CONF_PORT = "port"

# Example register addresses used by built-in entities
REG_SENSOR = 0
REG_BINARY = 1
REG_SWITCH = 2
REG_NUMBER = 3

# Modbus slave address/unit identifier (1–255)
CONF_UNIT = "unit"
DEFAULT_UNIT = 1

# Update rate in seconds for polling registers
CONF_UPDATE_RATE = "update_rate"
DEFAULT_UPDATE_RATE = 30

# Optional entity override settings
CONF_OPTIONAL_FORCE_ENABLE = "optional_force_enable"
CONF_OPTIONAL_DISABLE = "optional_disable"

# Device identity metadata (fetched once via Modbus)
CONF_DEVICE_SERIAL = "device_serial"
CONF_DEVICE_NAME = "device_name"
CONF_FIRMWARE_VERSION = "firmware_version"
CONF_DEVICE_INFO_PENDING_FETCH = "device_info_pending_fetch"
CONF_DEVICE_INFO_FETCH_ATTEMPTED = "device_info_fetch_attempted"

# Integration version (keep in sync with manifest.json)
__version__ = "0.3.0-b1"
