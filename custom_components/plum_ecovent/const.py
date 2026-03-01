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

# Integration version (keep in sync with manifest.json)
__version__ = "0.2.0"
