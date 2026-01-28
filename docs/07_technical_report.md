# Technical Report

## Mini-Fulfillment Conveyor Automation System

---

### 1. Introduction and Motivation

Fulfillment centers rely on conveyor-based material handling equipment (MHE) to sort, route, and transport packages at high throughput. Reliability of these systems directly impacts order fulfillment speed and customer satisfaction. Common challenges include:

- **Jam detection and recovery:** minimizing downtime when packages get stuck.
- **Routing accuracy:** ensuring packages reach the correct destination (pick station, shipping lane, etc.).
- **Safety:** protecting operators working near moving machinery.
- **Continuous improvement:** using operational data to tune system parameters and reduce waste.

This project implements a simplified mini-fulfillment conveyor system in a PLC simulation environment, demonstrating core automation principles that scale to real warehouse systems.

### 2. System Architecture

#### 2.1 Overview

The system consists of three layers:

1. **PLC Logic Layer** (CODESYS Soft PLC): Implements all control logic in IEC 61131-3 Structured Text -- state machine, safety interlocks, motor control, jam detection, routing, and metrics.

2. **HMI Layer** (CODESYS Visualization): Provides three operator screens -- Main Overview (conveyor graphic, controls), Alarms & Status (fault diagnostics), and Metrics Dashboard (KPIs, parameter adjustment).

3. **Simulation Layer** (Python): Simulates the physical process (box generation, movement, photoeye triggering, jam injection) and connects to the PLC via OPC-UA. Logs data to CSV for analysis.

#### 2.2 PLC Program Structure

| Module | Type | Responsibility |
|---|---|---|
| PRG_Main | Program | State machine orchestrator, coordinates all FBs |
| FB_Safety | Function Block | E-Stop monitoring, safety interlocks, start/stop qualification |
| FB_Conveyor | Function Block | Motor control, speed reference, auto/jog modes |
| FB_JamDetection | Function Block | TON timers on 4 photoeyes, fault identification, clear logic |
| FB_Diverter | Function Block | Accept/reject routing with edge-detected actuation |
| FB_ManualMode | Function Block | Jog-while-held control with safety enforcement |
| FB_Metrics | Function Block | Box count, cycle time, throughput, uptime tracking |

#### 2.3 I/O Summary

- **8 digital inputs:** Start PB, Stop PB, E-Stop, Mode Selector, 4 photoeyes.
- **5 digital outputs:** Conveyor motor, diverter actuator, alarm buzzer, green/red status lights.
- **HMI virtual tags:** Start/Stop/Clear commands, state/fault display, metrics, adjustable parameters.

### 3. Key Design Decisions

#### 3.1 State Machine Design

The system uses a 4-state machine (STOPPED, STARTING, RUNNING, FAULT) with clear transition rules. The STARTING state provides a 1-second pre-run delay for safety checks -- this pattern is common in industrial systems where motor starters need time to engage and operators need warning before motion begins.

#### 3.2 E-Stop as Latching Fault

The E-Stop is implemented as a **latching fault** requiring explicit operator acknowledgment (Fault Clear) even after the E-Stop button is released. This follows industrial best practice: the operator must consciously confirm the area is safe before restarting, preventing accidental restarts.

#### 3.3 Jam Detection with Configurable Timeout

Each photoeye has its own independent TON timer. The timeout is configurable via the HMI (default 4.0 seconds), allowing operators to tune the sensitivity based on actual operating conditions. The jam fault identifies the specific location (infeed, diverter, outfeed B/C), aiding rapid diagnosis.

Fault clearing requires **two conditions**: (1) the operator presses Fault Clear, and (2) the triggering photoeye is no longer blocked. This prevents clearing a fault while the jam still exists.

#### 3.4 Safety-Gated Motor Output

The motor output is gated by multiple safety conditions in series:

```
Motor ON = RunCommand AND EStop_Healthy AND NOT EStop_Latched AND Stop_Not_Pressed
```

This defense-in-depth approach ensures the motor cannot run if any single safety condition is violated, even if the state machine has a logic error.

#### 3.5 Deterministic Routing for Testing

The accept/reject pattern (every 3rd box rejected) provides deterministic, reproducible test scenarios. In a production system, this would be replaced by barcode/RFID scan results or upstream system commands.

### 4. Continuous Improvement Experiment

#### 4.1 Methodology

Two 15-minute simulation runs were designed:

- **Baseline:** Default parameters (jam timeout = 4.0s, arrival rate = 72/hr).
- **Improved:** Adjusted parameters (jam timeout = 5.5s, same arrival rate) with inter-arrival spacing enforcement.

Both runs used the same random seed for jam injection probability (3% per box) to ensure comparable conditions.

#### 4.2 Hypothesis

> Increasing the jam timeout from 4.0s to 5.5s will reduce false jam detections caused by boxes momentarily pausing at photoeyes, improving uptime and throughput without compromising actual jam detection capability.

#### 4.3 Metrics Tracked

- Throughput (boxes/hour)
- Jam events per hour
- Average cycle time
- Uptime percentage (running time / total time)
- Cumulative box count

#### 4.4 Expected Outcomes

- Fewer false-positive jams in the improved run.
- Higher uptime percentage.
- Maintained or slightly improved throughput.
- Negligible increase in average cycle time.

#### 4.5 Analysis

Results are analyzed in the Jupyter notebook (`data/analysis/ci_experiment.ipynb`) with time-series plots, bar charts, and distribution histograms comparing both runs.

#### 4.6 Applicability

This same methodology applies to real fulfillment MHE:

1. **Instrument** the system to log photoeye events, motor state, and fault occurrences.
2. **Baseline** current performance under normal load.
3. **Hypothesize** a specific, measurable change.
4. **Implement** the change (parameter adjustment, logic modification, or physical intervention).
5. **Measure** the impact over a comparable time window.
6. **Iterate** or roll back based on data.

### 5. Testing and Validation

14 test cases were designed covering:

- **Functional:** Normal operation, routing pattern, manual mode.
- **Safety:** E-Stop response, safety interlocks in manual mode, fault rejection during active faults.
- **Fault Handling:** Jam detection at all 4 photoeye locations, fault clear logic, fault clear rejection.
- **Parameters:** Adjustable jam timeout, bad parameter demonstration.
- **Metrics:** Counter accuracy, throughput calculation verification.

See `docs/05_testing_protocol.md` for full test procedures and expected results.

### 6. Conclusions

This project demonstrates the core automation skills relevant to fulfillment center MHE:

- **PLC programming** in IEC 61131-3 Structured Text with modular function blocks.
- **Safety interlock design** following industrial best practices (E-Stop latching, defense-in-depth motor gating).
- **HMI development** with actionable operator screens (status, diagnostics, KPIs).
- **Instrumentation and data logging** for operational visibility.
- **Continuous improvement** using data-driven parameter tuning to reduce downtime and maintain throughput.

The modular architecture (separate FBs for safety, conveyor, jam detection, routing, and metrics) mirrors how real industrial systems are structured, making the logic maintainable, testable, and extensible.
