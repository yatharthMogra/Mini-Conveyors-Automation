# PLC Source Files

IEC 61131-3 Structured Text source files for the mini-fulfillment conveyor control system.

## File Overview

| File | Type | Description |
|---|---|---|
| `types.st` | Type Definitions | Enumerations (`E_SystemState`, `E_FaultCode`, `E_OperatingMode`) and structures (`ST_Metrics`, `ST_JamStatus`) |
| `io_mapping.st` | GVL | Maps symbolic names to physical I/O addresses (`%IX`, `%QX`) |
| `global_vars.st` | GVL | Shared variables: state, flags, metrics, HMI interface tags |
| `prg_main.st` | Program (PRG) | Main state machine orchestrator |
| `fb_safety.st` | Function Block (FB) | E-Stop monitoring, safety interlocks |
| `fb_conveyor.st` | Function Block (FB) | Conveyor motor control |
| `fb_jam_detection.st` | Function Block (FB) | Jam timer and fault logic per photoeye |
| `fb_diverter.st` | Function Block (FB) | Accept/reject routing logic |
| `fb_manual_mode.st` | Function Block (FB) | Manual jog control |
| `fb_metrics.st` | Function Block (FB) | Counters, timers, throughput calculation |

## CODESYS Project Setup (Step-by-Step)

### Prerequisites

1. Download and install **CODESYS V3.5** from [store.codesys.com](https://store.codesys.com/) (free registration required).
2. Install the **CODESYS Control Win V3** soft PLC package from the CODESYS Installer (Package Manager).

### Creating the Project

1. **New Project**
   - Open CODESYS IDE
   - File -> New Project -> Standard Project
   - Name: `MiniFulfillment`
   - Device: `CODESYS Control Win V3 (x64)` (or x86 depending on your system)
   - Language: Structured Text (ST)
   - Click OK

2. **Add Type Definitions**
   - Right-click on `Application` in the device tree
   - Add Object -> DUT (Data Unit Type)
   - For each type in `types.st`, create a DUT and paste the type definition:
     - `E_SystemState` (Enumeration)
     - `E_FaultCode` (Enumeration)
     - `E_OperatingMode` (Enumeration)
     - `ST_Metrics` (Structure)
     - `ST_JamStatus` (Structure)

3. **Add Global Variable Lists**
   - Right-click on `Application` -> Add Object -> Global Variable List
   - Create GVL `IO_Mapping` and paste contents of `io_mapping.st`
   - Create GVL `GVL` and paste contents of `global_vars.st`

4. **Add Function Blocks**
   - Right-click on `Application` -> Add Object -> POU
   - Type: Function Block, Language: Structured Text
   - Create each FB and paste corresponding `.st` file contents:
     - `FB_Safety`
     - `FB_Conveyor`
     - `FB_JamDetection`
     - `FB_Diverter`
     - `FB_ManualMode`
     - `FB_Metrics`

5. **Configure Main Program**
   - The default `PLC_PRG` can be replaced or renamed to `PRG_Main`
   - Paste contents of `prg_main.st`
   - Ensure `PRG_Main` is called in the task configuration (MainTask)

6. **Configure I/O Mapping** (for simulation)
   - Since we are using the soft PLC without physical I/O, the `%IX` and `%QX` addresses will be mapped to simulated values
   - The Python simulator writes to inputs and reads outputs via OPC-UA
   - In Device -> PLC Settings, ensure "Update I/O while in stop" is checked for testing

7. **Enable OPC-UA Server**
   - Right-click on `Application` -> Add Object -> Symbol Configuration
   - Check the variables you want to expose via OPC-UA (all GVL variables)
   - Build the project once to populate the symbol list
   - The OPC-UA server runs on `opc.tcp://localhost:4840` by default

### Building and Running

1. Build: Build -> Build (F11)
2. Connect: Online -> Login (Alt+F8) - select the local CODESYS Control Win V3 runtime
3. Start: Debug -> Start (F5)
4. Monitor variables in the watch window or via the Visualization screens

### Task Configuration

| Task | Priority | Interval | Assigned POU |
|---|---|---|---|
| MainTask | 1 | 10 ms | PRG_Main |
