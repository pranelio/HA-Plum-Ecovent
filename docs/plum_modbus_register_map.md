# Plum ecoVENT Register Map and Properties

## 1) Coverage and conventions

This document is a structured register/property catalog derived from the provided vendor file.

- Coverage here includes the registers visible in the provided content (`0..252`).
- Addressing is register-index based (zero-based in protocol examples).
- Types/min/max/permissions reflect vendor data and may require hardware validation where ambiguities exist.

## 2) Field schema

Each row uses these normalized fields:

- `addr`: register address
- `name`: parameter name
- `access`: `R`, `W`, or `R/W` (derived from source `O`, `I`, `I/O`)
- `type`: vendor type (`uint8_t`, `int16_t`, etc.)
- `min`, `max`: declared range (or `-` when not defined)
- `permission`: role scope (`User`, `Mix`, etc.)
- `notes`: enums/scaling/dependencies/bitmasks

## 3) Register catalog by block

## 3.1 Permission/password block

| addr | name | access | type | min | max | permission | notes |
|---:|---|---|---|---:|---:|---|---|
| 0 | Password bits 0..1 | R/W | uint16_t | 0 | 65535 | User | Password entry block start (32-byte credential field spans `0..15`) |
| 1 | Password bits 2..3 | R/W | uint16_t | 0 | 65535 | User |  |
| 2 | Password bits 4..5 | R/W | uint16_t | 0 | 65535 | User |  |
| 3 | Password bits 6..7 | R/W | uint16_t | 0 | 65535 | User |  |
| 4 | Password bits 8..9 | R/W | uint16_t | 0 | 65535 | User |  |
| 5 | Password bits 10..11 | R/W | uint16_t | 0 | 65535 | User |  |
| 6 | Password bits 12..13 | R/W | uint16_t | 0 | 65535 | User |  |
| 7 | Password bits 14..15 | R/W | uint16_t | 0 | 65535 | User |  |
| 8 | Password bits 16..17 | R/W | uint16_t | 0 | 65535 | User |  |
| 9 | Password bits 18..19 | R/W | uint16_t | 0 | 65535 | User |  |
| 10 | Password bits 20..21 | R/W | uint16_t | 0 | 65535 | User |  |
| 11 | Password bits 22..23 | R/W | uint16_t | 0 | 65535 | User |  |
| 12 | Password bits 24..25 | R/W | uint16_t | 0 | 65535 | User |  |
| 13 | Password bits 26..27 | R/W | uint16_t | 0 | 65535 | User |  |
| 14 | Password bits 28..29 | R/W | uint16_t | 0 | 65535 | User |  |
| 15 | Password bits 30..31 | R/W | uint16_t | 0 | 65535 | User |  |

## 3.2 Device identity / metadata

| addr | name | access | type | min | max | permission | notes |
|---:|---|---|---|---:|---:|---|---|
| 16 | Program version | R | uint16_t | - | - | User | Format `SXXX.YYY` (senior/junior byte semantics in source) |
| 17..24 | Device name bytes | R/W | uint16_t | 0 | 65535 | User | UTF-8 packed string |
| 25..29 | Serial number bytes | R | uint16_t | - | - | User | Read-only string payload |

## 3.3 Modbus line configuration

| addr | name | access | type | min | max | permission | notes |
|---:|---|---|---|---:|---:|---|---|
| 45 | Modbus address | R/W | uint8_t | 1 | 247 | User | Slave address |
| 46 | Baudrate index | R/W | uint8_t | 0 | 10 | User | `0=1200,1=2400,2=4800,3=9600,4=19200,5=38400,6=57600,7=115200,8=230400,9=460800,10=921600` |
| 47 | Stop bits | R/W | uint8_t | 1 | 2 | User |  |
| 48 | Parity | R/W | uint8_t | 0 | 2 | User | `0=None,1=Even,2=Odd` |

## 3.4 Alarm registers (bitfields)

| addr | name | access | type | min | max | permission | notes |
|---:|---|---|---|---:|---:|---|---|
| 49 | Alarm table 1 low bits | R/W | bitfield (vendor listed `uint8_t`) | 0 | 65535 | Mix | Includes E2..E15 mapping |
| 50 | Alarm table 1 high bits | R/W | bitfield (vendor listed `uint8_t`) | 0 | 65535 | Mix | Includes E16..E31 mapping |
| 51 | Alarm table 2 low bits | R/W | bitfield (vendor listed `uint8_t`) | 0 | 65535 | Mix | Includes E34..E44 mapping |
| 52 | Alarm table 2 high bits | R/W | bitfield (vendor listed `uint8_t`) | 0 | 65535 | Mix | Includes E53..E63 mapping |
| 53 | Alarm table 3 low bits | R/W | bitfield (vendor listed `uint8_t`) | 0 | 65535 | Mix | Includes E64..E69 mapping |
| 54 | Alarm table 3 high bits | R/W | bitfield | 0 | 65535 | Mix | Declared in table; bit mapping not fully described in provided content |

### Alarm bit masks provided in source

#### Register 49 (Table 1 low)
- `0x04` E2 communication error pressure/flow sensor (supply)
- `0x08` E3 communication error pressure/flow sensor (exhaust)
- `0x10` E4 supply temperature sensor damaged
- `0x20` E5 sensor after heat exchanger damaged
- `0x40` E6 exhaust temperature sensor damaged
- `0x80` E7 supply filter pressure/flow sensor communication error
- `0x100` E8 exhaust filter pressure/flow sensor communication error
- `0x200` E9 intake temperature sensor damaged
- `0x400` E10 extract temperature sensor damaged
- `0x800` E11 fire alarm external signal
- `0x1000` E12 no rotary exchanger confirmation
- `0x2000` E13 GHE sensor damaged
- `0x8000` E15 excessive supply temperature

#### Register 50 (Table 1 high)
- `0x01` E16 secondary electric heater overheating (service confirm)
- `0x02` E17 manufacturer service maintenance required
- `0x04` E18 periodic maintenance approaching (user confirm)
- `0x08` E19 unauthorized startup / lock
- `0x10` E20 primary electric heater overheating (service confirm)
- `0x20` E21 primary heater thermostat signal
- `0x40` E22 secondary heater thermostat signal
- `0x80` E23 too low supply temperature
- `0x100` E24 secondary water heater thermostat active
- `0x200` E25 primary water heater thermostat active
- `0x800` E27 installer settings error
- `0x1000` E28 heater thermostat tripped
- `0x2000` E29 heater thermostat tripped 3x (service confirm)
- `0x4000` E30 manufacturer settings error
- `0x8000` E31 leading temperature sensor damaged

#### Register 51 (Table 2 low)
- `0x04` E34 no supply fan confirmation
- `0x08` E35 supply filter replacement approaching
- `0x10` E36 exhaust filter replacement approaching
- `0x20` E37 supply filter contaminated
- `0x40` E38 exhaust filter contaminated
- `0x200` E41 emergency mode filters worn
- `0x400` E42 filter replacement procedure
- `0x800` E43 unauthorized parameter modification via Modbus
- `0x1000` E44 no exhaust fan confirmation

#### Register 52 (Table 2 high)
- `0x20` E53 unit alarm
- `0x40` E54 no supply fan confirmation (service)
- `0x80` E55 no exhaust fan confirmation (service)
- `0x100` E56 defrost alarm
- `0x200` E57 humidity sensor error
- `0x400` E58 CO2 sensor error
- `0x800` E59 multiplexer communication error
- `0x1000` E60 constant-flow pressure sensor error
- `0x2000` E61 no humidity reading / panel connection
- `0x4000` E62 leading temp reading error / panel connection
- `0x8000` E63 auto mode air-quality sensor error

#### Register 53 (Table 3 low)
- `0x01` E64 smoke detector active
- `0x02` E65 condensate pump failure
- `0x04` E66 primary-heater downstream sensor damaged
- `0x08` E67 secondary-heater downstream sensor damaged
- `0x10` E68 primary heater temperature exceeded
- `0x20` E69 secondary/related heater temperature exceeded (vendor text appears duplicated)

## 3.5 Core user control and operating mode

| addr | name | access | type | min | max | permission | notes |
|---:|---|---|---|---:|---:|---|---|
| 59 | Unit on/off | R/W | uint8_t | 0 | 1 | User | `0=OFF,1=ON` |
| 60 | Gear schedule enable | R/W | uint8_t | 0 | 1 | User | `0=OFF,1=ON` |
| 61 | Gear schedule day selector | R/W | uint8_t | 0 | 6 | User | Monday..Sunday mapping in source |
| 62 | Gear schedule interval selector | R/W | uint8_t | 0 | 4 | User | Context selector |
| 63 | Gear schedule start hour | R/W | uint8_t | 0 | 23 | User |  |
| 64 | Gear schedule start minute step | R/W | uint8_t | 0 | 1 | User | `0=:00,1=:30` |
| 65 | Gear schedule end hour | R/W | uint8_t | 0 | 23 | User |  |
| 66 | Gear schedule end minute step | R/W | uint8_t | 0 | 1 | User | `0=:00,1=:30` |
| 67 | Gear schedule mode | R/W | uint8_t | 0 | 5 | User | `0=Pause,1=Gear1,2=Gear2,3=Gear3,4=Clear interval,5=Clear day` |
| 68 | Gear schedule copy bitmask | W | uint8_t | 0 | 127 | User | Day bitmask copy command |
| 69 | Unit operation mode | R/W | uint8_t | 0 | 5 | User | `0=off,1=gear1,2=gear2,3=gear3,5=pause` |

## 3.6 Fan speed and auto mode

| addr | name | access | type | min | max | permission | notes |
|---:|---|---|---|---:|---:|---|---|
| 70 | Supply fan speed gear 1 | R/W | uint16_t | 0 | 7000 | User | Max depends on control mode registers |
| 71 | Supply fan speed gear 2 | R/W | uint16_t | 0 | 7000 | User | Same dependency |
| 72 | Supply fan speed gear 3 | R/W | uint16_t | 0 | 7000 | User | Same dependency |
| 74 | Extract fan speed gear 1 | R/W | uint16_t | 0 | 7000 | User | Same dependency |
| 75 | Extract fan speed gear 2 | R/W | uint16_t | 0 | 7000 | User | Same dependency |
| 76 | Extract fan speed gear 3 | R/W | uint16_t | 0 | 7000 | User | Same dependency |
| 78 | Auto mode on/off | R/W | uint8_t | 0 | 1 | User | `0=OFF,1=ON` |
| 79 | Auto mode min fan speed | R/W | uint8_t | R366 | R80 | User | Cross-register constrained min |
| 80 | Auto mode max fan speed | R/W | uint8_t | R79 | R367 | User | Cross-register constrained max |
| 81 | Auto mode CO2 setpoint | R/W | uint16_t | 0 | 2000 | User | ppm |
| 82 | Current CO2 | R | Float | - | - | User | runtime value |
| 83 | Auto mode RH setpoint | R/W | uint8_t | 0 | 100 | User | % |
| 84 | Current RH | R | Float | - | - | User | runtime value |

## 3.7 Time modes and fireplace

| addr | name | access | type | min | max | permission | notes |
|---:|---|---|---|---:|---:|---|---|
| 85 | Time mode selector | R/W | uint8_t | 0 | 3 | User | `0=None,1=Output/Away,2=Party,3=Airing` |
| 86 | Away duration | R/W | uint8_t | 1 | 10 | User | hours |
| 87 | Party duration | R/W | uint8_t | 1 | 15 | User | hours |
| 88 | Airing duration | R/W | uint8_t | 1 | 20 | User | minutes |
| 89 | Exhaust fan speed in ventilation mode | R/W | uint16_t | mode-dependent | mode-dependent | User | unit depends on regulation mode: %, Pa, or flow |
| 90 | Fireplace mode | R/W | uint8_t | 0 | 1 | User | `0=OFF,1=ON` |
| 91 | Fan delta in fireplace mode | R/W | int8_t | -100 | 0 | User | percentage |

## 3.8 Temperature schedule and seasonal mode

| addr | name | access | type | min | max | permission | notes |
|---:|---|---|---|---:|---:|---|---|
| 92 | Temperature schedule mode selector | R/W | uint8_t | 0 | 2 | User | `0=Schedule,1=Day only,2=Night only` |
| 93 | Day comfort temperature | R/W | uint8_t | R599 | R600 | User | °C |
| 94 | Night comfort temperature | R/W | uint8_t | R599 | R600 | User | °C |
| 95 | Temperature schedule day | R/W | uint8_t | 0 | 6 | User | Sunday..Saturday mapping |
| 96 | Temperature schedule start hour | R/W | uint8_t | 0 | 23 | User |  |
| 97 | Temperature schedule start minute step | R/W | uint8_t | 0 | 1 | User | `0=:00,1=:30` |
| 98 | Temperature schedule end hour | R/W | uint8_t | 0 | 23 | User |  |
| 99 | Temperature schedule end minute step | R/W | uint8_t | 0 | 1 | User | `0=:00,1=:30` |
| 100 | Temperature interval mode | R/W | uint8_t | 0 | 3 | User | night/day/all-day modes |
| 101 | Temperature schedule day-copy bitmask | W | uint8_t | 0 | 127 | User | copy selected day to others |
| 102 | Seasonal mode state | R/W | uint8_t | 0 | 4 | User | read and write enums differ in source |
| 103 | Winter activation temperature | R/W | int8_t | -20 | 20 | User | °C |
| 104 | Summer activation temperature | R/W | uint8_t | 0 | 20 | User | °C |

## 3.9 Zone schedule

| addr | name | access | type | min | max | permission | notes |
|---:|---|---|---|---:|---:|---|---|
| 105 | Zone schedule enable | R/W | uint8_t | 0 | 1 | User |  |
| 106 | Zone schedule status | R | uint8_t | - | - | User | `0=Night zone,1=Day zone` |
| 107 | Zone schedule day | R/W | uint8_t | 0 | 6 | User | Sunday..Saturday mapping |
| 108 | Zone interval start hour | R/W | uint8_t | 0 | 23 | User |  |
| 109 | Zone interval start minute step | R/W | uint8_t | 0 | 1 | User | `0=:00,1=:30` |
| 110 | Zone interval end hour | R/W | uint8_t | 0 | 23 | User |  |
| 111 | Zone interval end minute step | R/W | uint8_t | 0 | 1 | User | `0=:00,1=:30` |
| 112 | Zone interval mode | R/W | uint8_t | 0 | 3 | User | `0=Off,1=On,2=All-day Off,3=All-day On` |
| 113 | Zone schedule day-copy bitmask | W | uint8_t | 0 | 127 | User | bitmask copy command |

## 3.10 Boost and GHE

| addr | name | access | type | min | max | permission | notes |
|---:|---|---|---|---:|---:|---|---|
| 114 | Boost mode | R/W | uint8_t | 0 | 2 | User | `0=Off,1=Boost1,2=Boost2` |
| 115 | Boost1 supply speed | R/W | int16_t | -7000 | 7000 | User | constraints vary by control mode |
| 116 | Boost1 extract speed | R/W | int16_t | -7000 | 7000 | User | constraints vary by control mode |
| 117 | Boost1 duration | R/W | uint8_t | 1 | 60 | User | minutes |
| 118 | Boost2 supply speed | R/W | int16_t | -7000 | 7000 | User | constraints vary by control mode |
| 119 | Boost2 extract speed | R/W | int16_t | -7000 | 7000 | User | constraints vary by control mode |
| 120 | Boost2 duration | R/W | uint8_t | 1 | 60 | User | minutes |
| 121 | GHE mode | R/W | uint8_t | 0 | 2 | User | `0=Winter,1=Summer,2=Auto` |
| 122 | GHE summer activation temp | R/W | uint8_t | 10 | 30 | User | °C |
| 123 | GHE winter activation temp | R/W | uint8_t | 5 | 20 | User | °C |
| 124 | GHE max opening time | R/W | uint8_t | 1 | 20 | User | hours |
| 125 | GHE regeneration time | R/W | uint8_t | 0 | 20 | User | hours |
| 126 | Manual regeneration start | W | uint8_t | 0 | 1 | User | trigger-like |

## 3.11 Alarm control panel and filters

| addr | name | access | type | min | max | permission | notes |
|---:|---|---|---|---:|---:|---|---|
| 127 | Alarm control panel enable | R/W | uint8_t | 0 | 1 | User |  |
| 128 | Alarm panel logic | R/W | uint8_t | 0 | 1 | User | `0=NO,1=NC` |
| 129 | Alarm panel operation mode | R/W | uint8_t | 0 | 1 | User | fan-off vs fan-set |
| 130 | Supply fan control during active signal | R/W | uint8_t | R366 | R367 | User | % |
| 131 | Extract fan control during active signal | R/W | uint8_t | R376 | R377 | User | % |
| 132 | Ventilation function in alarm panel | R/W | uint8_t | 0 | 1 | User |  |
| 133 | Supply fan in ventilation mode | R/W | uint8_t | R366 | R367 | User | % |
| 134 | Extract fan in ventilation mode | R/W | uint8_t | R376 | R377 | User | % |
| 135 | Ventilation duration | R/W | uint8_t | 1 | 100 | User | minutes |
| 136 | Interval between ventilation durations | R/W | uint8_t | 1 | 24 | User | hours |
| 137 | Secondary heater permission in ventilation | R/W | uint8_t | 0 | 1 | User |  |
| 138 | Exchanger cleaning start time | R/W | uint8_t | 1 | 24 | User | hours |
| 139 | Start filter replacement procedure | R/W | uint8_t | 0 | 1 | User | installer-dependent |
| 140 | Supply filter class | R/W | uint8_t | 1 | 4 | User | enum classes |
| 141 | Exhaust filter class | R/W | uint8_t | 1 | 4 | User | enum classes |
| 142 | Filters status/command | R/W | uint8_t | 0 | 3 | User | read enum differs from write commands |
| 143 | Filter time reset selector | R/W | uint8_t | 1 | 2 | User | `1=Supply,2=Exhaust` |
| 144 | Additional equipment enable bitmask | R/W | uint8_t | 0 | 31 | User | `0x01 Cooler,0x02 Aggregate,0x04 Secondary heater,0x08 GHE,0x10 Duct AC` |

## 3.12 Runtime status and telemetry

| addr | name | access | type | min | max | permission | notes |
|---:|---|---|---|---:|---:|---|---|
| 200 | Current unit status | R | uint8_t | - | - | User | rich enum (`off`, `normal`, `heating`, `alarm airing`, etc.) |
| 201 | Comfort temperature | R | Float | - | - | User |  |
| 202 | Outdoor temperature | R | Float | - | - | User |  |
| 203 | Leading temperature | R | Float | - | - | User |  |
| 204 | Lead sensor type | R | uint8_t | - | - | User | `0 supply,1 extract,2 extract I2C,3 EvoTouch,4 SCP,255 error` |
| 205 | Regulation mode | R | uint8_t | - | - | User | `0 cooling,1 heating` |
| 206 | Intake temperature | R | Float | - | - | User |  |
| 207 | Extract temperature | R | Float | - | - | User |  |
| 208 | Supply temperature | R | Float | - | - | User |  |
| 209 | Exhaust temperature | R | Float | - | - | User |  |
| 210 | Secondary sensor temperature | R | Float | - | - | User |  |
| 211 | SCP temperature | R | Float | - | - | User |  |
| 212 | Panel temperature | R | Float | - | - | User |  |
| 213 | Temperature behind preheater | R | Float | - | - | User |  |
| 214 | Temperature behind secondary heater | R | Float | - | - | User |  |
| 215 | GHE status | R | uint8_t | 0 | 1 | User | `0 off,1 active` |
| 216 | GHE temperature | R | Float | - | - | User |  |
| 217 | GHE regeneration | R | uint8_t | - | - | User | `0 off,1 on` |
| 218 | Cooler status | R | uint8_t | 0 | 1 | User |  |
| 219 | Cooler current control | R | float-like | 0 | 1000 | User | percentage scaled `x0.1` |
| 220 | Cooler blockade remaining time | R | uint8_t | - | - | User |  |
| 221 | Days of operation | R | uint16_t | - | - | User |  |
| 222 | Days to inspection | R | uint16_t | - | - | User |  |
| 223 | Days until lock | R | uint16_t | - | - | User |  |
| 224 | Filter detection type | R | uint8_t | - | - | User | `0 none,1 time,2 pressure switch,3 differential transmitter,255 error` |
| 225 | Supply filter replacement needed | R | uint8_t | - | - | User | boolean-like |
| 226 | Supply filter signal source | R | uint8_t | - | - | User | `0 none,1 AIN,2 I2C/SDP,255 error` |
| 227 | Exhaust filter detection type | R | uint8_t | - | - | User | same enum style |
| 228 | Exhaust filter replacement needed | R | uint8_t | - | - | User | boolean-like |
| 229 | Exhaust filter signal source | R | uint8_t | - | - | User | same enum style |
| 230 | Supply filter dirt level | R | uint8_t | - | - | User | % |
| 231 | Supply filter working days | R | uint16_t | - | - | User |  |
| 232 | Exhaust filter dirt level | R | uint8_t | - | - | User | % |
| 233 | Exhaust filter working days | R | uint16_t | - | - | User |  |
| 234 | Aggregate current control | R | float-like | 0 | 1000 | User | percentage scaled `x0.1` |
| 235 | Chiller alarm | R | uint8_t | - | - | User | boolean-like |
| 236 | Defrosting unit flag | R | uint8_t | - | - | User | boolean-like |
| 237 | Secondary heater type | R | uint8_t | - | - | User | `0 none,1 electric,2 water` |
| 238 | Secondary heater status | R | uint8_t | 0 | 1 | User |  |
| 239 | Secondary heater current control | R | float-like | 0 | 1000 | User | percentage scaled `x0.1` |
| 240 | Secondary heater overtemp reached | R | uint8_t | - | - | User | boolean-like |
| 241 | Preheater type | R | uint8_t | - | - | User | `0 none,1 electric,2 water` |
| 242 | Preheater status | R | uint8_t | 0 | 1 | User |  |
| 243 | Preheater current control | R | float-like | 0 | 1000 | User | percentage scaled `x0.1` |
| 244 | Preheater overtemp reached | R | uint8_t | - | - | User | boolean-like |
| 245 | Unit control mode | R | uint8_t | - | - | User | `0 standard,1 constant pressure,2 constant flow` |
| 246 | Supply fan operation | R | uint8_t | - | - | User | boolean-like |
| 247 | Supply fan current control | R | uint8_t | - | - | User | % |
| 248 | Extract fan operation | R | uint8_t | - | - | User | boolean-like |
| 249 | Extract fan current control | R | uint8_t | - | - | User | % |
| 250 | Bypass current control | R | float-like | 0 | 1000 | User | percentage scaled `x0.1` |
| 251 | Aggregate state | R | uint8_t | 0 | 2 | User | `0 off,1 heating,2 cooling` |
| 252 | Bypass state | R | uint8_t | 0 | 1 | User | `0 off,1 on` |

## 4) Property notes for implementation

### 4.1 Access conversion
Source notation mapped as:

- `O` -> read-only (`R`)
- `I` -> write-only (`W`) or command-like
- `I/O` -> read/write (`R/W`)

### 4.2 Constraint classes
Registers frequently follow one of these validation classes:

- Boolean (`0/1`)
- Enum set (small finite integer domain)
- Scalar numeric with fixed min/max
- Cross-register-constrained min/max (e.g., `R79..R80`)
- Bitmask command/state register
- String payload spans

### 4.3 Ambiguity flags
Items to annotate in code metadata:

- Alarm register type width inconsistency (`uint8_t` label vs 16-bit masks)
- Seasonal mode read/write enum mismatch at register `102`
- Some duplicated/typo alarm descriptions in vendor text

## 5) Suggested machine-friendly metadata keys

For future automation or code generation, store each register using:

- `address`
- `label`
- `rw`
- `datatype`
- `unit`
- `min`
- `max`
- `enum_map`
- `bit_map`
- `scale`
- `permissions`
- `notes`
- `dependencies`
- `confidence` (`high|medium|low` when vendor docs conflict)
