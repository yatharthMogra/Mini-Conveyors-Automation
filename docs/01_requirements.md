# System Requirements Document

## 1. Project Scope

This project implements a simulated mini-fulfillment conveyor system controlled by a CODESYS soft PLC. The system demonstrates industrial automation fundamentals: motor control, sensor-based part detection, routing logic, safety interlocks, fault handling, operator HMI, and data-driven continuous improvement.

### 1.1 Simulation vs. Physical

- **Platform:** CODESYS V3.5 soft PLC running on a PC (no physical hardware required).
- **Process simulation:** A Python-based process simulator communicates with the PLC via OPC-UA, modeling box movement, photoeye triggers, and fault injection.
- **HMI:** CODESYS built-in Visualization, accessible via web browser.

## 2. Operational Scenario

### 2.1 Process Description

Boxes arrive at **Station A** (infeed) on a single conveyor belt. Each box passes through a photoeye scanner. Based on an accept/reject decision, the box is routed:

- **Station B** (accept path) -- box continues straight through the diverter.
- **Station C** (reject path) -- diverter actuates to deflect the box onto a reject spur.

After routing, boxes exit at the respective outfeed photoeye and are considered "processed."

### 2.2 Process Flow

```
Station A (Infeed)          Diverter             Station B (Accept Outfeed)
    |                          |                          |
    v                          v                          v
[Infeed PE] ---> [Conveyor] ---> [Diverter PE] ---> [Outfeed B PE]
                                      |
                                      v (when reject)
                               [Outfeed C PE]
                                      |
                                      v
                              Station C (Reject Outfeed)
```

### 2.3 Operating Modes

| Mode | Description |
|---|---|
| **Auto** | Normal operation. PLC manages conveyor, routing, and fault detection automatically. |
| **Manual** | Operator can jog the conveyor forward at reduced speed. No automatic routing. Safety interlocks remain active. |

### 2.4 States

| State | Description |
|---|---|
| **STOPPED** | Conveyor is off. System is idle and safe to interact with. |
| **STARTING** | Pre-run checks in progress. Transitions to RUNNING if all checks pass. |
| **RUNNING** | Conveyor is moving. Boxes are being scanned and routed. |
| **FAULT** | A fault condition (jam, E-Stop) has been detected. Conveyor is stopped. Alarm is active. |

## 3. Sensors (Inputs)

| ID | Name | Type | Description |
|---|---|---|---|
| I0.0 | Start Pushbutton | Momentary NO | Initiates system start sequence |
| I0.1 | Stop Pushbutton | Momentary NC | Stops the system gracefully |
| I0.2 | Emergency Stop | Maintained NC | Immediately de-energizes all outputs; latches fault |
| I0.3 | Mode Selector | Toggle | 0 = Auto, 1 = Manual |
| I1.0 | Infeed Photoeye | Diffuse | Detects box presence at Station A infeed |
| I1.1 | Diverter Photoeye | Diffuse | Detects box presence at the diverter decision point |
| I1.2 | Outfeed B Photoeye | Diffuse | Detects box exiting at Station B (accept) |
| I1.3 | Outfeed C Photoeye | Diffuse | Detects box exiting at Station C (reject) |

## 4. Actuators (Outputs)

| ID | Name | Type | Description |
|---|---|---|---|
| Q0.0 | Conveyor Motor | Digital | Runs the main conveyor belt |
| Q0.1 | Diverter Actuator | Digital | Actuates the diverter gate (0 = Station B, 1 = Station C) |
| Q0.2 | Alarm Buzzer | Digital | Sounds during fault conditions |
| Q0.3 | Status Light Green | Digital | Illuminated when system is RUNNING |
| Q0.4 | Status Light Red | Digital | Illuminated when system is in FAULT |

## 5. Success Criteria

| Criterion | Target | Measurement Method |
|---|---|---|
| Throughput | >= 60 boxes/hour | Box count / running time |
| Jam rate | <= 2 jams/hour | Jam event counter / running time |
| Fault recovery time | < 30 seconds | Time from fault onset to system RUNNING again |
| E-Stop response | Immediate (< 1 PLC scan) | Motor output drops within one scan of E-Stop activation |
| Routing accuracy | 100% | All accept boxes reach Station B; all reject boxes reach Station C |

## 6. Constraints

- All logic runs on the CODESYS soft PLC (no physical hardware).
- Process simulation is handled by an external Python application via OPC-UA.
- Safety logic is simulated; this is not a SIL-rated safety system.
- Target PLC scan time: 10-20 ms.

## 7. Assumptions

- One box on the conveyor at a time (single-box mode for initial implementation).
- Box dimensions are uniform.
- Conveyor speed is constant in auto mode (variable speed may be explored in the CI experiment).
- Accept/reject decision is pattern-based (every 3rd box is rejected) for deterministic testing.
