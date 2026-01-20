# Testing Protocol

Scripted test scenarios for validating the mini-fulfillment conveyor system.

## Test Environment

- **PLC Runtime:** CODESYS Control Win V3 (soft PLC)
- **Simulator:** Python process simulator (`simulation/process_sim.py`)
- **Mode:** OPC-UA connected or local simulation mode
- **Scan Time:** 10 ms (MainTask)

## Test Execution Procedure

1. Start the CODESYS runtime (or use simulator in local mode).
2. For each test case: reset the system to STOPPED state, set initial conditions, execute the test steps, and record results.
3. Document pass/fail, screenshots, and any observations in `tests/results/`.

---

## Test Cases

### TC-01: Normal Startup and Operation

| Field | Value |
|---|---|
| **Objective** | Verify system starts correctly and processes boxes in auto mode |
| **Preconditions** | System in STOPPED state, E-Stop healthy, all PEs clear |
| **Steps** | 1. Press START button. 2. Verify state transitions STOPPED -> STARTING -> RUNNING. 3. Allow 10 boxes to process through the system. 4. Verify box count increments correctly. 5. Press STOP button. 6. Verify state transitions to STOPPED. |
| **Expected Result** | - Green light ON during RUNNING. - Motor ON during RUNNING. - 10 boxes counted. - Boxes 3, 6, 9 routed to Station C (reject pattern). - Remaining boxes routed to Station B. - System stops cleanly on STOP command. |
| **Pass Criteria** | All boxes processed, correct routing, clean stop |

### TC-02: Emergency Stop During Operation

| Field | Value |
|---|---|
| **Objective** | Verify E-Stop immediately halts the system and requires explicit reset |
| **Preconditions** | System in RUNNING state, boxes on conveyor |
| **Steps** | 1. Start system and begin processing boxes. 2. While motor is running, activate E-Stop (set bEStop = FALSE). 3. Verify immediate response. 4. Attempt to press START (should be rejected). 5. Release E-Stop (set bEStop = TRUE). 6. Attempt to press START (should still be rejected -- latch active). 7. Press FAULT CLEAR. 8. Press START. |
| **Expected Result** | - Motor OFF within 1 scan of E-Stop activation. - State transitions to FAULT. - Red light ON (blinking), buzzer ON. - START rejected while fault is latched. - After E-Stop release + Fault Clear: state -> STOPPED. - After START: system restarts normally. |
| **Pass Criteria** | Motor stops within 10ms, fault latches, restart requires explicit clear |

### TC-03: Jam Detection at Infeed

| Field | Value |
|---|---|
| **Objective** | Verify jam detection triggers fault when infeed PE is blocked too long |
| **Preconditions** | System in RUNNING state, jam timeout = 4.0s |
| **Steps** | 1. Start system in auto mode. 2. Force bInfeedPE = TRUE (simulate box stuck at infeed). 3. Hold for 4+ seconds. 4. Observe system response. 5. Clear bInfeedPE = FALSE (simulate jam physically cleared). 6. Press FAULT CLEAR. 7. Press START to restart. |
| **Expected Result** | - After 4.0s with PE blocked: state -> FAULT. - Fault message: "JAM DETECTED AT INFEED (Station A)". - Fault code: 2. - Motor OFF, red light ON, buzzer ON. - Fault Clear accepted only when PE is clear. - System restarts after clear. |
| **Pass Criteria** | Jam detected at correct timeout, fault clears properly |

### TC-04: Jam Detection at Diverter

| Field | Value |
|---|---|
| **Objective** | Verify jam detection at diverter photoeye |
| **Preconditions** | System in RUNNING state, jam timeout = 4.0s |
| **Steps** | 1. Start system. 2. Force bDiverterPE = TRUE for > 4.0s. 3. Observe fault. 4. Clear PE and reset fault. |
| **Expected Result** | - Fault code: 3, message: "JAM DETECTED AT DIVERTER". - Same fault/recovery behavior as TC-03. |
| **Pass Criteria** | Correct fault code and message, clean recovery |

### TC-05: Jam Detection at Outfeed B

| Field | Value |
|---|---|
| **Objective** | Verify jam detection at outfeed B photoeye |
| **Preconditions** | System in RUNNING state |
| **Steps** | Same as TC-03 but with bOutfeedBPE. |
| **Expected Result** | Fault code: 4, message: "JAM DETECTED AT OUTFEED B (Station B)". |
| **Pass Criteria** | Correct fault code, clean recovery |

### TC-06: Jam Detection at Outfeed C

| Field | Value |
|---|---|
| **Objective** | Verify jam detection at outfeed C photoeye |
| **Preconditions** | System in RUNNING state |
| **Steps** | Same as TC-03 but with bOutfeedCPE. |
| **Expected Result** | Fault code: 5, message: "JAM DETECTED AT OUTFEED C (Station C)". |
| **Pass Criteria** | Correct fault code, clean recovery |

### TC-07: Fault Clear Rejected While PE Still Blocked

| Field | Value |
|---|---|
| **Objective** | Verify fault cannot be cleared while the triggering condition persists |
| **Preconditions** | System in FAULT state due to jam, PE still blocked |
| **Steps** | 1. Trigger a jam at infeed (bInfeedPE = TRUE for > 4s). 2. While PE is still blocked, press FAULT CLEAR. 3. Verify fault is NOT cleared. 4. Clear PE (bInfeedPE = FALSE). 5. Press FAULT CLEAR again. |
| **Expected Result** | - Step 2: fault remains active, state stays FAULT. - Step 5: fault clears, state -> STOPPED. |
| **Pass Criteria** | Fault only clears when both conditions met |

### TC-08: Diverter Routing - Accept/Reject Pattern

| Field | Value |
|---|---|
| **Objective** | Verify every 3rd box is rejected (routed to Station C) |
| **Preconditions** | System in RUNNING, auto mode |
| **Steps** | 1. Start system. 2. Process 9 boxes. 3. Record which station each box exits at. |
| **Expected Result** | - Boxes 1, 2 -> Station B (accept). - Box 3 -> Station C (reject). - Boxes 4, 5 -> Station B. - Box 6 -> Station C. - Boxes 7, 8 -> Station B. - Box 9 -> Station C. - Diverter retracts between each box. |
| **Pass Criteria** | Pattern matches 1:2 reject:accept ratio |

### TC-09: Manual Mode - Jog Control

| Field | Value |
|---|---|
| **Objective** | Verify jog control works correctly in manual mode |
| **Preconditions** | System in RUNNING state |
| **Steps** | 1. Start system in auto mode. 2. Switch mode selector to Manual (bModeSelector = TRUE). 3. Verify motor stops (auto run disabled). 4. Hold JOG button. 5. Verify motor runs at reduced speed. 6. Release JOG button. 7. Verify motor stops. 8. Verify diverter does NOT actuate in manual mode. |
| **Expected Result** | - Motor runs only while JOG is held. - Reduced speed in manual mode. - No automatic routing. - Safety interlocks still active (E-Stop would stop jog). |
| **Pass Criteria** | Jog-while-held behavior, no routing, safety active |

### TC-10: Manual Mode - Safety Interlock

| Field | Value |
|---|---|
| **Objective** | Verify safety interlocks remain active in manual mode |
| **Preconditions** | System in RUNNING, manual mode |
| **Steps** | 1. Switch to manual mode. 2. Hold JOG (motor running). 3. Activate E-Stop. 4. Verify motor stops immediately even though JOG is held. |
| **Expected Result** | Motor OFF within 1 scan, state -> FAULT. |
| **Pass Criteria** | E-Stop overrides jog in manual mode |

### TC-11: Adjustable Jam Timeout from HMI

| Field | Value |
|---|---|
| **Objective** | Verify changing jam timeout via HMI affects detection behavior |
| **Preconditions** | System in RUNNING state |
| **Steps** | 1. Set rJamTimeoutSec = 2.0 via HMI. 2. Block infeed PE. 3. Verify jam triggers after ~2.0s (not 4.0s). 4. Clear fault and restart. 5. Set rJamTimeoutSec = 8.0. 6. Block infeed PE for 5.0s. 7. Verify NO jam triggers (within 8.0s timeout). 8. Release PE before 8.0s. |
| **Expected Result** | - Step 3: jam at ~2.0s. - Step 7: no jam at 5.0s (below 8.0s threshold). |
| **Pass Criteria** | Timeout parameter is respected in real-time |

### TC-12: Metrics Accuracy

| Field | Value |
|---|---|
| **Objective** | Verify metrics counters and calculations are accurate |
| **Preconditions** | System in STOPPED state, all metrics at zero |
| **Steps** | 1. Start system. 2. Process exactly 5 boxes. 3. Force 1 jam event. 4. Clear fault and process 3 more boxes. 5. Stop system. 6. Check all metrics. |
| **Expected Result** | - Box count: 8. - Jam count: 1. - Running time: > 0. - Fault time: > 0 (during jam). - Throughput: ~ (8 / running_time_hours). - Avg cycle time: reasonable for conveyor length/speed. |
| **Pass Criteria** | All counters accurate, throughput calculation correct |

### TC-13: Bad Parameter - Extremely Low Jam Timeout

| Field | Value |
|---|---|
| **Objective** | Demonstrate that poor parameter tuning causes excessive false jams |
| **Preconditions** | System in RUNNING state |
| **Steps** | 1. Set rJamTimeoutSec = 0.5 (extremely low). 2. Run system for 5 minutes. 3. Count jam events. 4. Compare to baseline run with timeout = 4.0s. |
| **Expected Result** | - Many more jam events than normal. - Frequent FAULT state entries. - Reduced throughput due to constant stopping. - Demonstrates importance of proper parameter tuning. |
| **Pass Criteria** | Clearly shows degraded performance with bad parameter |

### TC-14: Start Rejected During Fault

| Field | Value |
|---|---|
| **Objective** | Verify system cannot start while a fault is active |
| **Preconditions** | System in FAULT state |
| **Steps** | 1. Put system in FAULT (e.g., E-Stop). 2. Attempt START without clearing fault. |
| **Expected Result** | START is rejected, system stays in FAULT. |
| **Pass Criteria** | No state change on START during active fault |

---

## Test Results Template

For each test case, record:

| Field | Value |
|---|---|
| Test Case | TC-XX |
| Date | YYYY-MM-DD |
| Tester | (name) |
| Result | PASS / FAIL |
| Observations | (notes) |
| Screenshots | (file references) |
| Issues Found | (if any) |
