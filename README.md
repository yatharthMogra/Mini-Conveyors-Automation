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

### Quick Start (Simulator Only, No CODESYS)

The Python simulator can run in standalone mode without a CODESYS runtime:

```bash
cd simulation
pip install -r requirements.txt
python process_sim.py --no-viz --duration 300
```

This runs a 5-minute simulation in local mode, logging metrics and events to `data/`.

## Documentation

| Document | Description |
|---|---|
| [`docs/01_requirements.md`](docs/01_requirements.md) | System requirements, I/O lists, success criteria |
| [`docs/02_io_table.md`](docs/02_io_table.md) | Complete I/O address mapping |
| [`docs/03_block_diagram.md`](docs/03_block_diagram.md) | P&ID and signal flow diagrams |
| [`docs/04_state_diagram.md`](docs/04_state_diagram.md) | State machine, truth tables, control logic |
| [`docs/05_testing_protocol.md`](docs/05_testing_protocol.md) | 14 scripted test scenarios |
| [`docs/06_operator_manual.md`](docs/06_operator_manual.md) | One-page operator quick reference |
| [`docs/07_technical_report.md`](docs/07_technical_report.md) | Full technical report (architecture, design, CI experiment) |

## Resume Bullet Points

- Designed and implemented a PLC-controlled conveyor automation system (IEC 61131-3 Structured Text) with modular function blocks for safety interlocks (E-Stop latching, defense-in-depth motor gating), jam detection with configurable thresholds, and accept/reject routing logic.
- Developed a 3-screen HMI (CODESYS Visualization) with real-time conveyor graphics, fault diagnostics, and a metrics dashboard tracking throughput, cycle time, jam rate, and uptime -- enabling data-driven operator decisions.
- Built a Python process simulator with OPC-UA integration and real-time Tkinter visualization, then conducted a continuous improvement experiment that reduced false jam detections by tuning detection parameters, demonstrating a data-driven approach to improving MHE reliability and throughput in a fulfillment-like setting.

## License

This project is for educational and portfolio purposes.
