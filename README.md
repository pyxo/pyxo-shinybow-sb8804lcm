# Pyxo Shinybow SB-8804LCM

Home Assistant custom integration by **Pyxo Enterprises** for controlling a **Shinybow SB-8804LCM 8x8 Digital Audio Matrix** over a local RS232 serial port.

## Features

- Local RS232 control
- Serial port dropdown prefers `/dev/serial/by-id/*` paths when available
- Configurable baud rate, data bits, parity, stop bits, and flow control
- Setup can complete even when the matrix is not connected or powered on
- Input and output names are entered during setup
- Input and output names can also be edited later from integration options
- Per-output source selection
- Per-output volume control
- Per-output balance control
- All-outputs source selector

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
2. Go to **Integrations**.
3. Open the three-dot menu.
4. Choose **Custom repositories**.
5. Add this repository URL:

   ```text
   https://github.com/pyxo/pyxo-shinybow-sb8804lcm
   ```

6. Select category: **Integration**.
7. Install **Pyxo Shinybow SB-8804LCM**.
8. Restart Home Assistant.
9. Go to **Settings > Devices & services**.
10. Add integration: **Pyxo Shinybow SB-8804LCM**.

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

After naming outputs, entity names use the output names, for example:

- `Theater Source`
- `Theater Volume`
- `Theater Balance`

## Serial port notes

Use `/dev/serial/by-id/...` whenever possible instead of `/dev/ttyUSB0`, because `/dev/ttyUSB0` can change after reboot. The setup dropdown prefers `/dev/serial/by-id/*` paths when they exist.

## Created by

Pyxo Enterprises
