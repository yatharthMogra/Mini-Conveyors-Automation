# I/O Table

Complete input/output mapping for the mini-fulfillment conveyor system.

## Digital Inputs

| PLC Address | Symbol | Description | Signal Type | Normal State |
|---|---|---|---|---|
| `%IX0.0` | `bStartPB` | Start pushbutton | Momentary NO | Open (FALSE) |
| `%IX0.1` | `bStopPB` | Stop pushbutton | Momentary NC | Closed (TRUE) |
| `%IX0.2` | `bEStop` | Emergency stop | Maintained NC | Closed (TRUE) |
| `%IX0.3` | `bModeSelector` | Mode selector switch | Toggle | 0 = Auto, 1 = Manual |
| `%IX1.0` | `bInfeedPE` | Infeed photoeye (Station A) | Diffuse reflective | Clear (FALSE), Blocked (TRUE) |
| `%IX1.1` | `bDiverterPE` | Diverter photoeye | Diffuse reflective | Clear (FALSE), Blocked (TRUE) |
| `%IX1.2` | `bOutfeedBPE` | Outfeed B photoeye (Station B, accept) | Diffuse reflective | Clear (FALSE), Blocked (TRUE) |
| `%IX1.3` | `bOutfeedCPE` | Outfeed C photoeye (Station C, reject) | Diffuse reflective | Clear (FALSE), Blocked (TRUE) |

### Input Notes

- **E-Stop and Stop PB** are wired NC (normally closed). A TRUE signal means the circuit is healthy; FALSE means the button is pressed or the wire is cut (fail-safe wiring).
- **Photoeyes** return TRUE when a box is blocking the beam, FALSE when clear.
- **Mode Selector**: FALSE = Auto mode, TRUE = Manual mode.

## Digital Outputs

| PLC Address | Symbol | Description | Load Type | Safe State |
|---|---|---|---|---|
| `%QX0.0` | `bConveyorMotor` | Main conveyor belt motor | Contactor/relay | OFF (FALSE) |
| `%QX0.1` | `bDiverterActuator` | Diverter gate actuator | Solenoid | Retracted (FALSE) = Station B path |
| `%QX0.2` | `bAlarmBuzzer` | Fault alarm buzzer | Buzzer | OFF (FALSE) |
| `%QX0.3` | `bStatusGreen` | Status light - green (RUNNING) | Indicator lamp | OFF (FALSE) |
| `%QX0.4` | `bStatusRed` | Status light - red (FAULT) | Indicator lamp | OFF (FALSE) |

### Output Notes

- **Diverter Actuator**: De-energized (FALSE) = box goes straight to Station B (accept). Energized (TRUE) = box is deflected to Station C (reject). Default safe state routes to accept.
- **Conveyor Motor**: Controlled via a contactor. De-energized on any fault, E-Stop, or stop command.
- **Alarm Buzzer**: Activated during FAULT state; silenced when fault is cleared.

## HMI Virtual I/O (Internal Tags)

These are not physical I/O but are exchanged between the HMI and PLC logic via internal variables.

| Tag Name | Direction | Type | Description |
|---|---|---|---|
| `bHMI_Start` | HMI -> PLC | BOOL | Start command from HMI button |
| `bHMI_Stop` | HMI -> PLC | BOOL | Stop command from HMI button |
| `bHMI_FaultClear` | HMI -> PLC | BOOL | Fault clear command from HMI button |
| `bHMI_JogFwd` | HMI -> PLC | BOOL | Jog forward command (manual mode) |
| `iHMI_State` | PLC -> HMI | INT | Current system state (0=STOPPED, 1=STARTING, 2=RUNNING, 3=FAULT) |
| `sHMI_FaultMsg` | PLC -> HMI | STRING | Active fault description text |
| `rHMI_BoxCount` | PLC -> HMI | DINT | Total boxes processed |
| `rHMI_AvgCycleTime` | PLC -> HMI | REAL | Average cycle time (seconds) |
| `rHMI_JamCount` | PLC -> HMI | DINT | Total jam events |
| `rHMI_Throughput` | PLC -> HMI | REAL | Current throughput (boxes/hour) |
| `rHMI_JamTimeout` | HMI -> PLC | REAL | Jam detection timeout threshold (seconds) |
| `rHMI_ConveyorSpeed` | HMI -> PLC | REAL | Conveyor speed setpoint (0.0 - 1.0) |

## I/O Wiring Summary

```
PLC INPUTS                              PLC OUTPUTS
==========                              ===========
%IX0.0  <--- Start PB (NO)             %QX0.0  ---> Conveyor Motor (Contactor)
%IX0.1  <--- Stop PB (NC)              %QX0.1  ---> Diverter Actuator (Solenoid)
%IX0.2  <--- E-Stop (NC)               %QX0.2  ---> Alarm Buzzer
%IX0.3  <--- Mode Selector             %QX0.3  ---> Status Light Green
%IX1.0  <--- Infeed PE                 %QX0.4  ---> Status Light Red
%IX1.1  <--- Diverter PE
%IX1.2  <--- Outfeed B PE
%IX1.3  <--- Outfeed C PE

Total: 8 DI / 5 DO
```
