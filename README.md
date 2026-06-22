# Pyxo Shinybow SB-8804LCM

Home Assistant custom integration by **Pyxo Enterprises** for controlling a **Shinybow SB-8804LCM 8x8 Digital Audio Matrix** over a local RS232 serial port.

## Features

- Local RS232 control
- Configurable serial port and RS232 settings
- Named inputs and outputs
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

Input and output names can be customized from the integration options.

## Serial port recommendation

Use `/dev/serial/by-id/...` when possible instead of `/dev/ttyUSB0`, because `/dev/ttyUSB0` can change after reboot.

## Created by

Pyxo Enterprises
