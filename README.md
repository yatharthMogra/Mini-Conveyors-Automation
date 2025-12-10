# Mini-Fulfillment Automation System

A CODESYS-based PLC automation project simulating a mini fulfillment center conveyor system with box routing, jam detection, and continuous improvement analysis.

## Overview

This project demonstrates industrial automation principles applied to a simplified fulfillment center scenario:

- **Boxes** enter at **Station A** (infeed), pass through a photoeye scanner, and are routed to either **Station B** (accept) or **Station C** (reject) via a diverter gate.
- **PLC logic** (IEC 61131-3 Structured Text) handles start/stop control, safety interlocks, jam detection, and routing decisions.
- An **HMI** provides operator controls, real-time status, alarms, and a metrics dashboard.
- A **Python process simulator** communicates with the CODESYS soft PLC via OPC-UA to simulate box flow, inject faults, and log operational data.
- A **continuous improvement experiment** compares baseline vs. optimized parameters using logged metrics.

## Target Performance

| Metric | Target |
|---|---|
| Throughput | 60 boxes/hour |
| Max jams/hour | 2 |
| Fault recovery time | < 30 seconds |

## Project Structure

```
automation_amz/
├── docs/           # Requirements, I/O tables, state diagrams, reports
├── plc/            # IEC 61131-3 Structured Text source files
├── hmi/            # HMI screen design specs and tag bindings
├── simulation/     # Python process simulator and OPC-UA client
├── data/           # Logged run data and Jupyter analysis
└── tests/          # Test scenarios and validation results
```

## Technology Stack

- **PLC Runtime:** CODESYS V3.5 (free soft PLC on PC)
- **PLC Language:** IEC 61131-3 Structured Text
- **HMI:** CODESYS Visualization (web-based)
- **Communication:** OPC-UA (built into CODESYS)
- **Simulator:** Python 3.10+ (opcua, tkinter, matplotlib)
- **Analysis:** Jupyter Notebook

## Getting Started

1. Install [CODESYS V3.5](https://store.codesys.com/) (free download)
2. Follow the setup guide in [`plc/README.md`](plc/README.md)
3. Install Python dependencies: `pip install -r simulation/requirements.txt`
4. Run the process simulator: `python simulation/process_sim.py`

## License

This project is for educational and portfolio purposes.
