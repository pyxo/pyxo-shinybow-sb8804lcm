# Shinybow SB-8804LCM for Home Assistant

Developed by **Pyxo** for the Shinybow SB-8804LCM 8×8 Audio Matrix.

## Version 0.1.0

A fresh, local serial integration with UI setup, port reconfiguration, eight output source selectors, an all-outputs selector, and routing/raw-command actions. Multiple matrices and identical FTDI adapters are supported by selecting a separate serial interface for each matrix.

## Install with HACS

1. In HACS, open **Custom repositories** and add `https://github.com/pyxo/pyxo-shinybow-sb8804lcm` as an **Integration**.
2. Download **Shinybow SB-8804LCM** and restart Home Assistant (2026.4 or later).
3. In **Settings → Devices & services → Add integration**, search for **Shinybow SB-8804LCM**.
4. Select the serial port. Prefer its exact `/dev/serial/by-id/...` path. Each FTDI interface has its own path; adapter model alone does not identify the matrix.

For manual installation, copy `custom_components/shinybow_sb8804lcm` into your configuration's `custom_components` directory, then restart.

The serial device must be accessible to Home Assistant Core. Stop terminal readers or other integrations using that port. Setup saves configuration without requiring a reply; if the port cannot open, Home Assistant retries setup. Use the integration menu's **Reconfigure** to change the port while retaining entity identity.

This is a fresh start with domain `shinybow_sb8804lcm`. Remove any previous `pyxo_shinybow_sb8804lcm` integration and its directory before installing. Old entity IDs and automations are not migrated.

## Protocol and state

- Fixed **9600 baud, 8 data bits, no parity, 1 stop bit, no flow control**.
- Each new connection sends `LINK 001;\r\n`, then waits one second.
- Routing sends `OUTPUT001 003;\r\n` (output 1, input 3).
- All-output routing sends `OUTPUTALL 003;\r\n`; all off sends `OUTPUTALL 000;\r\n`.
- Input 0 means Off; inputs and outputs otherwise range from 1 through 8.
- Commands are serialized. The port stays open until unload, shutdown, or an I/O error. A subsequent action reconnects and repeats LINK after an error; a failed action is not automatically replayed.

**State is assumed, not received from the matrix.** Selectors begin unknown after setup/reload and update only after a successful serial write. Physical changes, power loss, or disconnected RS232 wiring may not be detectable. A successful write does not prove that the matrix accepted the command. Mixed routes make the all-output selector unknown. Raw commands and I/O failures clear assumed routes.

The LINK + output-1/input-3 sequence was physically confirmed in prior troubleshooting. This implementation and the all-output/off commands still need hardware acceptance testing. RX remains unverified; there is no polling, guessed response parser, or acknowledgement requirement. The serial client exposes a separate bounded read method for future feedback support.

TCP bridges, volume, and balance are outside this initial version.

## Actions

Choose the matrix configuration entry in each action's UI. Actions use the domain `shinybow_sb8804lcm`:

| Action | Fields |
| --- | --- |
| `set_route` | `entry_id`, `output` (1–8), `input` (0–8) |
| `set_all_outputs` | `entry_id`, `input` (0–8) |
| `all_off` | `entry_id` |
| `send_command` | `entry_id`, `command` |

Example:

```yaml
action: shinybow_sb8804lcm.set_route
data:
  entry_id: YOUR_CONFIG_ENTRY_ID
  output: 1
  input: 3
```

Raw commands accept one ASCII command, with an optional final semicolon. CR+LF is added automatically. Embedded command separators are rejected. Example: `OUTPUT001 003;`.

## Development and testing

AI tools, including **OpenAI ChatGPT and Codex**, assisted with architecture, code generation, documentation, debugging, and test development. Pyxo is the developer and maintainer. This independent community integration is not affiliated with or endorsed by Shinybow.

Run `python3 -m unittest discover -s tests -v` for isolated protocol/transport tests using a fake serial port. These do not constitute a full Home Assistant runtime or hardware test. CI also runs HACS validation and Home Assistant hassfest.

Hardware acceptance: install, select the correct interface, route output 1 to input 3, test all outputs and Off, unload/reload, disconnect/reconnect the adapter, and test two matrices independently. RX support will require verified device responses.
