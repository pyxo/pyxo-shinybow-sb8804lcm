# Shinybow SB-8804LCM

Home Assistant custom integration by **Pyxo Enterprises** for controlling a **Shinybow SB-8804LCM 8x8 Digital Audio Matrix**.

## Features

- Local RS232 serial control
- TCP/IP to RS232 adapter control
- Configurable local RS232 settings
- Named inputs and outputs
- Per-output source selection
- Per-output volume control
- Per-output balance control
- All-outputs source selector
- Setup can complete without the matrix connected

## Supported device

- Shinybow SB-8804LCM 8x8 Digital Audio Matrix

## Default RS232 settings

- Baud rate: 9600
- Data bits: 8
- Parity: None
- Stop bits: 1
- Flow control: None

## Installation with HACS

1. Open HACS.
2. Go to Integrations.
3. Open the three-dot menu.
4. Choose Custom repositories.
5. Add this repository URL: `https://github.com/pyxo/pyxo-shinybow-sb8804lcm`
6. Select category: Integration.
7. Install **Shinybow SB-8804LCM**.
8. Restart Home Assistant.
9. Go to Settings > Devices & services.
10. Add integration: **Shinybow SB-8804LCM**.

## Connection types

### Local RS232

Use this when the matrix is connected to a serial port on the Home Assistant server, such as a USB-to-RS232 adapter.

The setup flow prefers `/dev/serial/by-id/*` ports when available.

### TCP/IP to RS232

Use this when the matrix is connected through a TCP/IP to RS232 adapter, bridge, or serial server.

Examples include Global Caché, iTach, Flex, GC-100, and other TCP serial servers.

## Entities

The integration creates:

- `All Outputs Source`
- `Output 1 Source`
- `Output 1 Volume`
- `Output 1 Balance`
- ...
- `Output 8 Source`
- `Output 8 Volume`
- `Output 8 Balance`

Input and output names can be customized during setup and later from the integration options.

## Created by

Pyxo Enterprises
