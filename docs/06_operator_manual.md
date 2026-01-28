# Operator Manual

## Mini-Fulfillment Conveyor System -- Quick Reference

---

### System Overview

This system moves boxes from Station A (infeed) through a diverter gate to either Station B (accept) or Station C (reject). The conveyor is PLC-controlled with automatic jam detection and safety interlocks.

---

### System States

| State | Indicator | Description |
|---|---|---|
| **STOPPED** | All lights OFF | System is idle. Safe to approach. |
| **STARTING** | Green light BLINKING | Pre-run checks in progress (1 second). |
| **RUNNING** | Green light ON | Conveyor is moving. Boxes are being processed. |
| **FAULT** | Red light BLINKING, Buzzer ON | A fault has occurred. Conveyor is stopped. |

---

### Starting the System

1. Verify E-Stop is **released** (pulled out / reset).
2. Verify no boxes are jammed at any photoeye.
3. Verify mode selector is set to **AUTO**.
4. Press **START** (green button on panel or HMI).
5. Wait for green light to stop blinking and go solid = RUNNING.

---

### Stopping the System

- **Normal stop:** Press **STOP** (red button). System transitions to STOPPED.
- **Emergency stop:** Hit the **E-Stop** mushroom button. Motor stops immediately. System enters FAULT.

---

### Clearing a Fault

1. Identify the fault on the HMI Alarms screen (e.g., "JAM AT INFEED").
2. **Remove the cause:**
   - For jams: physically clear the stuck box so the photoeye is unblocked.
   - For E-Stop: release/reset the E-Stop button.
3. Verify the photoeye indicator on the HMI turns green (CLEAR).
4. Press **FAULT CLEAR** (yellow button).
5. System transitions to STOPPED. You may now press START.

**Note:** Fault Clear will be rejected if the fault condition is still present. You must physically resolve the issue first.

---

### Manual / Jog Mode

1. Switch the mode selector to **MANUAL**.
2. System must be in RUNNING state (press START first if STOPPED).
3. Hold the **JOG** button (blue) to move the conveyor slowly.
4. Release JOG to stop.
5. Use jog mode to inch boxes past a jam point or clear obstructions.
6. Switch back to **AUTO** for normal operation.

**Safety:** E-Stop and jam detection remain active in manual mode.

---

### Dashboard Metrics

| Metric | What It Means |
|---|---|
| Boxes Processed | Total boxes that exited the system |
| Avg Cycle Time | Average time for a box to travel from infeed to outfeed |
| Throughput | Current production rate in boxes per hour |
| Jam Events | Number of times the system faulted due to a jam |
| Uptime % | Percentage of time the system was running vs. faulted |

---

### Adjustable Parameters (Metrics Dashboard Screen)

| Parameter | What It Does | Default | Range |
|---|---|---|---|
| Jam Timeout | How long a PE can be blocked before triggering a jam fault | 4.0 s | 1.0 - 10.0 s |
| Conveyor Speed | Belt speed setpoint (1.0 = full speed) | 1.0 | 0.1 - 1.0 |

Change parameters on the HMI and press **APPLY**. Changes take effect immediately.

---

### Troubleshooting

| Symptom | Likely Cause | Action |
|---|---|---|
| System won't start | E-Stop pressed or fault active | Release E-Stop, clear fault, then START |
| Frequent jams | Jam timeout too low or boxes too close together | Increase jam timeout on dashboard |
| Motor doesn't run in manual | JOG button not held, or not in RUNNING state | Ensure system is started and JOG is held |
| Diverter doesn't move | System in manual mode (no auto routing) | Switch to AUTO mode |
| Throughput below target | Frequent jams causing downtime | Review jam causes, adjust parameters |
