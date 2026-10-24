## 0.2.19

- Add optional Pause entity (HA boolean): when on, all current and power values served to the wallbox are forced to 0

## 0.2.18

- Answer non-read Modbus requests with a proper exception reply instead of silently dropping them; RTU frames are now length-decoded per function code rather than assumed to be 8 bytes
- Reply with exception code 4 when a register build fails so one bad live value cannot tear down the charger session
- Clamp out-of-range live values to the IEEE754 single-precision limits instead of raising
- Log session duration, request count, reply count and time since the last reply on every disconnect
- Detect and surface stale Home Assistant data: live data age is shown on the dashboard, exposed in /api/state, and logged when it goes stale or recovers
- Reuse one pooled HTTP session for Home Assistant reads, bound each read with a configurable timeout, and hold a fixed poll cadence
- Treat unavailable/unknown entity states as unavailable rather than read errors
- Close connections gracefully and only send RST when preempting a stale connection, so a reply in flight is never discarded
- Serve a request already in flight before handing over to a newly connected client

## 0.2.17

- Enable TCP_NODELAY on the Modbus client socket so responses are never delayed by Nagle's algorithm
- Recover from RTU CRC errors by resyncing the byte stream instead of disconnecting the charger
- Serve a reconnecting charger or bridge immediately by replacing the stale connection instead of leaving it queued

## 0.2.16

- Show HA, manual override, and effective power offset values in the dashboard
- Default to HA offset on startup and keep manual override as a runtime debug control
- Improve override UX by preventing accidental empty-value submissions

## 0.2.14

- Map power offset to HA entity instead of a fixed numeric value
- Add power offset setup guide to README

## 0.2.12

- Add phase mapping troubleshooting section to README

## 0.2.11

- Add phase remapping setting to reorder output L1/L2/L3
- All six phase order permutations selectable from the dashboard

## 0.2.10

- Add persistent power offset with GUI control
- Power offset can be adjusted from the dashboard and survives restarts

## 0.2.9

- Send TCP RST on disconnect for faster charger reconnect

## 0.2.8

- Disconnect on RTU CRC fail to resync the receive buffer
- Prevents the charger from stopping after a buffer misalignment

## 0.2.7

- Add Modbus output register table to dashboard
- Shows every register value as sent to the charger; negative power highlighted

## 0.2.6

- Fix power unit scaling: divide W values by 1000 before writing PRO380 registers
- Apparent power and power factor are corrected automatically

## 0.2.5

- Replace transport auto-detection with an explicit framing mismatch error
- Wrong transport mode now disconnects immediately with a clear log message

## 0.2.4

- Rebrand UI from BMW Meter Emulator to BMW Wallboxproxy
- Remove outdated HA config callout from the dashboard

## 0.2.3

- Two-phase idle timeout: separate initial connect timeout from established session idle timeout
- Prevents disconnect loops caused by slow charger connections

## 0.2.2

- Clean up dashboard UI
- Fix dashboard state API

## 0.2.1

- Package as Home Assistant add-on with ingress support
- Persist settings to env file across restarts
- Use HA supervisor API proxy for token-free local access
