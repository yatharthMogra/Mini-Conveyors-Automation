# Python Process Simulator

Simulates the physical conveyor process and communicates with the CODESYS soft PLC via OPC-UA.

## Components

| File | Description |
|---|---|
| `process_sim.py` | Box generation, conveyor physics, photoeye triggers |
| `opc_client.py` | OPC-UA client for reading/writing PLC tags |
| `data_logger.py` | CSV logging of operational metrics |
| `visualizer.py` | Real-time Tkinter visualization of conveyor state |
| `config.yaml` | Simulation parameters (arrival rate, speed, etc.) |

## Usage

```bash
pip install -r requirements.txt
python process_sim.py
```
