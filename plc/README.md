# PLC Source Files

IEC 61131-3 Structured Text source files for the mini-fulfillment conveyor control system.

## File Overview

| File | Description |
|---|---|
| `types.st` | Enumerations and structures (system states, metrics) |
| `io_mapping.st` | GVL mapping symbolic names to physical I/O addresses |
| `global_vars.st` | GVL for shared variables (state, counters, HMI commands) |
| `prg_main.st` | Main program: state machine orchestrator |
| `fb_safety.st` | Function block: E-Stop, interlocks, safety checks |
| `fb_conveyor.st` | Function block: conveyor motor control |
| `fb_jam_detection.st` | Function block: jam timer and fault logic |
| `fb_diverter.st` | Function block: accept/reject routing |
| `fb_manual_mode.st` | Function block: manual jog control |
| `fb_metrics.st` | Function block: counters, timers, throughput |

## Importing into CODESYS

*(Detailed setup instructions will be added in Phase 4.)*
