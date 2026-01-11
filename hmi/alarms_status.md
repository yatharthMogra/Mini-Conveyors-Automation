# Alarms and Status Screen

## Layout

```
+=====================================================================+
|                    MINI-FULFILLMENT CONVEYOR SYSTEM                  |
|                        Alarms & Status                               |
+=====================================================================+
|                                                                     |
|  SYSTEM STATE: [  FAULT  ]          FAULT CODE: [ 2 ]              |
|                                                                     |
|  ACTIVE ALARM:                                                      |
|  +---------------------------------------------------------------+  |
|  | ! JAM DETECTED AT INFEED (Station A)                          |  |
|  +---------------------------------------------------------------+  |
|                                                                     |
+---------------------------------------------------------------------+
|                         ALARM HISTORY                               |
|                                                                     |
|  #  | Time     | Code | Description                    | Status   |
|  ---|----------|------|--------------------------------|----------|
|  1  | 14:23:05 |  2   | JAM AT INFEED (Station A)      | CLEARED  |
|  2  | 14:15:32 |  1   | EMERGENCY STOP ACTIVATED       | CLEARED  |
|  3  | 14:10:11 |  3   | JAM AT DIVERTER                | CLEARED  |
|                                                                     |
+---------------------------------------------------------------------+
|                       SAFETY STATUS                                 |
|                                                                     |
|  E-Stop Circuit:  [ HEALTHY ]     E-Stop Latched: [ NO ]           |
|  Safe to Run:     [ YES ]         Fault Active:   [ NO ]           |
|  Jam Detected:    [ NO ]                                            |
|                                                                     |
+---------------------------------------------------------------------+
|                      JAM SENSOR STATUS                              |
|                                                                     |
|  Infeed PE:    [ CLEAR ]  Blocked: 0.0s / 4.0s timeout             |
|  Diverter PE:  [ CLEAR ]  Blocked: 0.0s / 4.0s timeout             |
|  Outfeed B PE: [ CLEAR ]  Blocked: 0.0s / 4.0s timeout             |
|  Outfeed C PE: [ CLEAR ]  Blocked: 0.0s / 4.0s timeout             |
|                                                                     |
+=====================================================================+
```

## Element Details

### Active Alarm Banner
- **Tag:** `GVL.sHMI_FaultMsg`
- **Visibility:** Only shown when `GVL.bFaultActive = TRUE`
- **Color:** Red background, white text, blinking border
- **Font:** 18pt bold

### Alarm History Table
- Implemented using CODESYS Alarm Configuration or a simple array-based log
- Each alarm record contains: timestamp, fault code, description, status (ACTIVE/CLEARED)
- Maximum 50 entries, FIFO buffer
- Active alarms highlighted in red; cleared alarms in gray

### Safety Status Indicators

| Label | Tag | TRUE Display | FALSE Display |
|---|---|---|---|
| E-Stop Circuit | `IO_Mapping.bEStop` | "HEALTHY" (green) | "ACTIVATED" (red) |
| E-Stop Latched | `GVL.bEStopLatched` | "YES" (red) | "NO" (green) |
| Safe to Run | `GVL.bSafeToRun` | "YES" (green) | "NO" (red) |
| Fault Active | `GVL.bFaultActive` | "YES" (red) | "NO" (green) |
| Jam Detected | `GVL.bJamDetected` | "YES" (red) | "NO" (green) |

### Jam Sensor Status

| Sensor | Blocked Tag | Duration Tag | Timeout Tag |
|---|---|---|---|
| Infeed PE | `GVL.stJamInfeed.bBlocked` | `GVL.stJamInfeed.tBlockedDuration` | `GVL.rJamTimeoutSec` |
| Diverter PE | `GVL.stJamDiverter.bBlocked` | `GVL.stJamDiverter.tBlockedDuration` | `GVL.rJamTimeoutSec` |
| Outfeed B PE | `GVL.stJamOutfeedB.bBlocked` | `GVL.stJamOutfeedB.tBlockedDuration` | `GVL.rJamTimeoutSec` |
| Outfeed C PE | `GVL.stJamOutfeedC.bBlocked` | `GVL.stJamOutfeedC.tBlockedDuration` | `GVL.rJamTimeoutSec` |

- Each sensor shows a progress-bar style indicator: blocked duration vs timeout threshold
- Color changes from green (clear) to yellow (blocked < 50% timeout) to red (blocked > 50% timeout or jam detected)

## CODESYS Visualization Implementation

1. Create visualization: `VIS_AlarmsStatus`
2. Canvas size: 1024 x 768 pixels
3. For alarm history: use the CODESYS Alarm Manager or implement a shift-register array in PLC code
4. Use bar graphs (rectangles with dynamic width) for jam sensor blocked duration
