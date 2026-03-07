"""Constants for the Plum Ecovent integration."""

DOMAIN = "plum_ecovent"
DEFAULT_NAME = "Plum Ecovent"

# Config keys
CONF_HOST = "host"
CONF_PORT = "port"
CONF_CONNECTION_TYPE = "connection_type"

CONNECTION_TYPE_TCP = "tcp"
CONNECTION_TYPE_RTU = "rtu"

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
CONF_OPTIONS_ACTION = "options_action"
CONF_DEVICE_SETTINGS_VALUES = "device_settings_values"
CONF_DEVICE_SETTINGS_GROUP = "device_settings_group"
CONF_RESPONDING_REGISTERS = "responding_registers"
CONF_AVAILABLE_REGISTERS = "available_registers"
CONF_NON_RESPONDING_REGISTERS = "non_responding_registers"
CONF_UNSUPPORTED_REGISTERS = "unsupported_registers"

# Device identity metadata (fetched once via Modbus)
CONF_DEVICE_SERIAL = "device_serial"
CONF_DEVICE_NAME = "device_name"
CONF_FIRMWARE_VERSION = "firmware_version"
CONF_DEVICE_INFO_PENDING_FETCH = "device_info_pending_fetch"
CONF_DEVICE_INFO_FETCH_ATTEMPTED = "device_info_fetch_attempted"

# Integration version (keep in sync with manifest.json)
__version__ = "0.5.0-b1"
