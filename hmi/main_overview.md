# Main Overview Screen

## Layout

```
+=====================================================================+
|                    MINI-FULFILLMENT CONVEYOR SYSTEM                  |
|                         Main Overview                                |
+=====================================================================+
|                                                                     |
|  SYSTEM STATE: [  RUNNING  ]        MODE: [  AUTO  ]               |
|                                                                     |
+---------------------------------------------------------------------+
|                        CONVEYOR VISUALIZATION                       |
|                                                                     |
|   [Box]    (PE1)                    (PE2)                           |
|    -->  ====|====== CONVEYOR =======|======+---> (PE3) --> [BIN B] |
|         Infeed PE                Diverter  |     Outfeed B          |
|                                    [GATE]  |                        |
|                                            +---> (PE4) --> [BIN C] |
|                                                  Outfeed C          |
|                                                                     |
|   PE Status:  (1) Infeed: CLEAR   (2) Diverter: CLEAR              |
|               (3) Outfeed B: CLEAR (4) Outfeed C: CLEAR            |
|                                                                     |
+---------------------------------------------------------------------+
|                        OPERATOR CONTROLS                            |
|                                                                     |
|   [ START ]    [ STOP ]    [ FAULT CLEAR ]    [ JOG FWD ]          |
|     Green       Red          Yellow            Blue (manual only)   |
|                                                                     |
+---------------------------------------------------------------------+
|  Motor: ON/OFF    Diverter: RETRACTED/EXTENDED    Alarm: OFF        |
|  Green Light: ON  Red Light: OFF                                    |
+=====================================================================+
```

## Element Details

### State Indicator
- **Tag:** `GVL.iHMI_State`
- **Display:** Rectangle with text
- **Colors:** STOPPED = Gray, STARTING = Yellow (blinking), RUNNING = Green, FAULT = Red (blinking)

### Mode Indicator
- **Tag:** `GVL.eOperatingMode`
- **Display:** Rectangle with text
- **Colors:** AUTO = Blue, MANUAL = Orange

### Conveyor Visualization
- Static conveyor graphic (gray belt with rollers)
- Animated box rectangles (brown) that move along the belt when motor is running
- Photoeye indicators: circles that are GREEN when clear, RED when blocked
  - **PE1 Tag:** `IO_Mapping.bInfeedPE`
  - **PE2 Tag:** `IO_Mapping.bDiverterPE`
  - **PE3 Tag:** `IO_Mapping.bOutfeedBPE`
  - **PE4 Tag:** `IO_Mapping.bOutfeedCPE`
- Diverter gate: rectangle that rotates/extends when actuated
  - **Tag:** `IO_Mapping.bDiverterActuator`

### Operator Buttons

| Button | Tag (Write) | Color | Behavior |
|---|---|---|---|
| START | `GVL.bHMI_Start` | Green | Momentary, sets TRUE for one scan |
| STOP | `GVL.bHMI_Stop` | Red | Momentary, sets TRUE for one scan |
| FAULT CLEAR | `GVL.bHMI_FaultClear` | Yellow | Momentary, sets TRUE for one scan |
| JOG FWD | `GVL.bHMI_JogFwd` | Blue | Hold-to-run, TRUE while pressed (only visible in MANUAL mode) |

### Output Status Bar

| Indicator | Tag | TRUE Text | FALSE Text |
|---|---|---|---|
| Motor | `IO_Mapping.bConveyorMotor` | "ON" (green) | "OFF" (gray) |
| Diverter | `IO_Mapping.bDiverterActuator` | "EXTENDED" (orange) | "RETRACTED" (green) |
| Alarm | `IO_Mapping.bAlarmBuzzer` | "ACTIVE" (red blink) | "OFF" (gray) |
| Green Light | `IO_Mapping.bStatusGreen` | "ON" (green) | "OFF" (gray) |
| Red Light | `IO_Mapping.bStatusRed` | "ON" (red) | "OFF" (gray) |

## CODESYS Visualization Implementation

1. Create a new Visualization object: `VIS_MainOverview`
2. Set canvas size: 1024 x 768 pixels
3. Add elements using the Visualization Toolbox:
   - Rectangles for conveyor belt sections
   - Ellipses for photoeye indicators
   - Buttons (Tap-false) for operator controls
   - Text fields with variable binding for state/mode display
4. Configure animations:
   - Use "Change color" on photoeye ellipses based on input tag
   - Use "Visibility" to show/hide JOG button based on mode
   - Use "Text display" with variable for state indicator
