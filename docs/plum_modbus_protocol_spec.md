# Plum ecoVENT Modbus Protocol Specification (Detailed)

## 1) Scope and assumptions

This document describes the Modbus behavior captured in the vendor file **“User Modbus table nano.md”**.

- Physical layer in source: **RS485 / Modbus RTU** on controller slave port (**COM3**).
- Function codes supported by device:
  - `0x03` Read Holding Registers
  - `0x06` Write Single Register
  - `0x10` Write Multiple Registers
- The Home Assistant integration in this repository currently uses Modbus TCP transport semantics, but register logic and function behavior map directly to the same register model.

## 2) Transport and serial parameters

### 2.1 Required line-level settings
All devices on the same RS485 line must use matching serial parameters:

- Device address: `1..247`
- Baud rate: commonly `9600`, `19200`, or `115200` (vendor table also defines additional rates through register config)
- Stop bits: `1` or `2`
- Parity: none/even/odd (vendor text states “none” in one section but register table allows all three values; see nuance below)

### 2.2 Nuance: parity description mismatch
The source contains two statements:

1. Communication settings section says parity setting is available but describes possible setting as “none”.
2. Register table (register `48`) defines `0=None, 1=Even, 2=Odd`.

Implementation guidance:
- Treat register-table definition as authoritative for runtime configuration options.
- If documentation and runtime behavior diverge, probe and validate on hardware.

## 3) Register addressing and data model

### 3.1 Addressing model
The vendor examples use register numbers directly as data addresses (e.g., `0004` = register 4). Practical conventions:

- Addresses are **zero-based** in the protocol examples.
- Multi-register fields are contiguous and ordered by increasing address.
- String fields are UTF-8 bytes packed into 16-bit register payloads.

### 3.2 Data typing in table
Data types in source include:

- `uint8_t`, `int8_t`
- `uint16_t`, `int16_t`
- “Float” values represented in some rows as scaled register values (often `x0.1` scaling from integer source)
- Bitfields where one register encodes multiple flags

### 3.3 Scaling and interpretation
Common interpretation patterns:

- Temperature/humidity/CO2 values may be integer with decimal scale (often `x0.1`).
- Percent controls can be raw `0..100` or wider ranges depending on control mode.
- Registers with "Mix" permission can include both readable and writable bit semantics.

## 4) Function code behavior

## 4.1 Read Holding Registers (`0x03`)

### Request frame fields
- Slave address (1 byte)
- Function (`0x03`, 1 byte)
- Start register (2 bytes)
- Quantity of registers (2 bytes)
- CRC (2 bytes, RTU)

### Response frame fields
- Slave address
- Function (`0x03`)
- Byte count
- Data bytes (`2 * quantity`)
- CRC

### Example from source
- Request: `01 03 00 04 00 02 85 CA`
- Response: `01 03 04 00 03 00 01 CB F3`

Interpretation: read 2 registers from register 4 at unit 1.

## 4.2 Write Single Register (`0x06`)

### Request frame fields
- Slave address
- Function (`0x06`)
- Register address (2 bytes)
- Value (2 bytes)
- CRC

### Success response
- Echo of original request frame.

### Error response
- Slave address
- Function with exception bit set: `0x86`
- Exception code
- CRC

### Example from source
- Request: `01 06 00 04 00 03 88 0A`
- Error response: `01 86 03 02 61`

Interpretation: exception code `0x03` indicates illegal/invalid data value in many Modbus stacks.

## 4.3 Write Multiple Registers (`0x10`)

### Request frame fields
- Slave address
- Function (`0x10`)
- Start register
- Quantity of registers
- Byte count (`2 * quantity`)
- Payload bytes
- CRC

### Success response
- Echoes header fields (address, function, start, quantity) without payload.

### Error response
- Function with exception bit set: `0x90`
- Exception code
- CRC

### Example from source
- Request: `01 10 00 27 00 02 04 00 15 00 16 20 5B`
- Error response: `01 90 03 0C 01`

## 5) Exception handling and robustness guidance

### 5.1 Exception marker rule
Device follows standard Modbus exception pattern: response function = request function + `0x80`.

### 5.2 Typical operational errors
- `Connection timeout / no reply`
- `Illegal data value` when writing out-of-range values
- Unauthorized write for permission-protected registers

### 5.3 Client-side reliability recommendations
- Retry idempotent reads with bounded backoff.
- Do not blindly trust optimistic write state; verify with read-back or coordinator refresh.
- Distinguish transport failure from protocol exception in logs and entity availability.

## 6) Authentication model

Device supports three permission contexts:

- `User` (no password)
- `Service` (default password: `2222`)
- `Manufacturer` (default password: `3333`)

### 6.1 Password write mechanism
- Password is written via register `0` using `0x10`.
- Password field supports up to 32 chars; encoded as UTF-8 bytes; unused bytes zero-filled.
- Session authorization expires after ~1 hour inactivity or power loss.

### 6.2 Unauthorized write behavior
- Writes to protected registers can return exception responses.
- Repeated wrong attempts (3x) can trigger alarm conditions.

## 7) String encoding protocol

String parameters are sent as:

1. UTF-8 encode text
2. Pack bytes into register payload (`2 bytes/register`)
3. Zero-pad to required field length
4. Write with `0x10`

Examples in source include manufacturer password and manufacturer name write sequences.

## 8) Schedule programming workflows

The source defines command workflows where context registers must be set before reading or writing schedule values.

### 8.1 Gear schedule (r61-r68)
- Select day (`r61`)
- Select interval (`r62`)
- Operate on interval time/mode registers (`r63..r67`)
- Optional copy operation via bitmask at `r68`

### 8.2 Temperature schedule (r95-r101)
- Select day and interval boundaries (`r95..r99`)
- Set/read mode in `r100`
- Copy day mapping via `r101`

Nuance: these are stateful operations; stale day/interval selector values can cause unintended writes.

## 9) Alarm bitfield model

Alarm information is spread across multiple 16-bit registers:

- Table1 low bits: register `49`
- Table1 high bits: register `50`
- Table2 low bits: register `51`
- Table2 high bits: register `52`
- Table3 low bits: register `53`
- Table3 high bits: register `54` (table present in register list, mapping detail partly absent in source)

### 9.1 Decoding strategy
- Read registers `49..54` in one poll cycle.
- For each table register, evaluate each documented bit mask.
- Emit:
  - aggregate alarm state
  - per-code binary sensors (`E2`, `E3`, ...)
  - optional severity/category metadata

### 9.2 Confirm-required alarms
Some alarm bit descriptions include service/user confirmation requirements. Integrations should preserve these flags in metadata and avoid auto-clearing assumptions.

## 10) Permissions and write safety

Source permissions include `User`, `Mix`, and other role-based restrictions.

Guidance:
- Enforce client-side write guardrails using documented min/max.
- Expose write constraints in UI (number range, enum mapping, bitmask semantics).
- Handle protected register write failures explicitly and surface diagnostics.

## 11) Interop notes for implementation

- Keep command generation strict on byte count and register quantity.
- Validate scalar ranges before issuing writes.
- For bitmask writes, perform read-modify-write sequence to avoid clobbering unrelated bits.
- For schedule and multi-step operations, serialize writes where possible.
- Prefer grouped reads for related values (e.g., alarms block) for consistency.

## 12) Known documentation ambiguities

From source text:

- Parity capabilities described inconsistently (see section 2.2).
- Some rows label alarm registers as `uint8_t` despite 16-bit bit masks (`0x8000`), implying practical 16-bit handling.
- Full mapping for table `54` (Table 3 high bits) is not fully described in the provided content.

Recommendation: maintain a runtime-validated register metadata layer and annotate uncertain fields as "vendor-doc ambiguous".

## 13) Summary checklist for protocol clients

- Use function codes `0x03`, `0x06`, `0x10` only.
- Treat exception responses as first-class outcomes.
- Implement retries/timeouts and explicit write failure handling.
- Decode alarms from bitfields, not scalar states.
- Respect authentication and permission model.
- Use UTF-8 + zero padding for string writes.
- Validate ranges before write; verify after write when safety-critical.
