# Process Block Diagram (P&ID)

## System Layout

```mermaid
graph LR
    subgraph stationA [Station A - Infeed]
        BoxSource["Box Source"]
        InfeedPE["Infeed PE<br/>%IX1.0"]
    end

    subgraph conveyorZone [Main Conveyor]
        Motor["Conveyor Motor<br/>%QX0.0"]
        DiverterPE["Diverter PE<br/>%IX1.1"]
        DiverterGate["Diverter Gate<br/>%QX0.1"]
    end

    subgraph stationB [Station B - Accept]
        OutfeedBPE["Outfeed B PE<br/>%IX1.2"]
        AcceptBin["Accept Bin"]
    end

    subgraph stationC [Station C - Reject]
        OutfeedCPE["Outfeed C PE<br/>%IX1.3"]
        RejectBin["Reject Bin"]
    end

    BoxSource -->|boxes| InfeedPE
    InfeedPE -->|conveyor belt| DiverterPE
    DiverterPE -->|straight path| OutfeedBPE
    DiverterPE -->|diverted path| OutfeedCPE
    OutfeedBPE --> AcceptBin
    OutfeedCPE --> RejectBin
    Motor -.->|drives| InfeedPE
    DiverterGate -.->|controls| DiverterPE
```

## Physical Layout (Top View)

```
                        CONVEYOR DIRECTION --->

    +============================================================+
    |                                                            |
    |  [Box Source]    [Infeed PE]         [Diverter PE]         |
    |       |              |                    |                |
    |       v              v                    v                |
    |   +------+      +--------+          +----------+          |
    |   | FEED |----->| ====== |--------->| ======== |----+     |
    |   +------+      +--------+          +----------+    |     |
    |                                          |          |     |
    |                                   [Diverter Gate]   |     |
    |                                          |          |     |
    |                                          v          v     |
    |                                    +---------+ +--------+ |
    |                                    |Outfeed C| |Outfeed B| |
    |                                    |   PE    | |   PE    | |
    |                                    +---------+ +--------+ |
    |                                          |          |     |
    |                                          v          v     |
    |                                    +---------+ +--------+ |
    |                                    | REJECT  | | ACCEPT | |
    |                                    |  BIN    | |  BIN   | |
    |                                    +---------+ +--------+ |
    |                                                            |
    +============================================================+

    OPERATOR PANEL:
    [START PB]  [STOP PB]  [E-STOP]  [MODE SEL]
      %IX0.0     %IX0.1     %IX0.2     %IX0.3

    STATUS INDICATORS:
    [GREEN LIGHT]  [RED LIGHT]  [BUZZER]
      %QX0.3        %QX0.4      %QX0.2
```

## Signal Flow Diagram

```mermaid
graph TD
    subgraph inputs [Inputs]
        StartPB["Start PB (%IX0.0)"]
        StopPB["Stop PB (%IX0.1)"]
        EStop["E-Stop (%IX0.2)"]
        ModeSel["Mode Sel (%IX0.3)"]
        InfeedPE["Infeed PE (%IX1.0)"]
        DiverterPE["Diverter PE (%IX1.1)"]
        OutBPE["Outfeed B PE (%IX1.2)"]
        OutCPE["Outfeed C PE (%IX1.3)"]
    end

    subgraph plcLogic [PLC Logic Blocks]
        Safety["FB_Safety"]
        ConvCtrl["FB_Conveyor"]
        JamDet["FB_JamDetection"]
        Diverter["FB_Diverter"]
        Metrics["FB_Metrics"]
        MainPrg["PRG_Main<br/>(State Machine)"]
    end

    subgraph outputs [Outputs]
        ConvMotor["Conveyor Motor (%QX0.0)"]
        DivActuator["Diverter (%QX0.1)"]
        Alarm["Buzzer (%QX0.2)"]
        GreenLight["Green Light (%QX0.3)"]
        RedLight["Red Light (%QX0.4)"]
    end

    StartPB --> Safety
    StopPB --> Safety
    EStop --> Safety
    ModeSel --> MainPrg

    InfeedPE --> JamDet
    InfeedPE --> Metrics
    DiverterPE --> JamDet
    DiverterPE --> Diverter
    OutBPE --> JamDet
    OutBPE --> Metrics
    OutCPE --> JamDet
    OutCPE --> Metrics

    Safety --> MainPrg
    MainPrg --> ConvCtrl
    MainPrg --> Diverter
    JamDet --> MainPrg

    ConvCtrl --> ConvMotor
    Diverter --> DivActuator
    MainPrg --> Alarm
    MainPrg --> GreenLight
    MainPrg --> RedLight
```

## Sensor Placement Details

| Sensor | Position | Purpose | Detection Range |
|---|---|---|---|
| Infeed PE | 150 mm from conveyor start | Detect box arrival, start cycle timer | 0-300 mm |
| Diverter PE | At diverter gate, center | Detect box at routing decision point | 0-300 mm |
| Outfeed B PE | 150 mm before Station B end | Confirm box reached accept bin | 0-300 mm |
| Outfeed C PE | 150 mm before Station C end | Confirm box reached reject bin | 0-300 mm |

## Conveyor Dimensions (Simulated)

| Parameter | Value |
|---|---|
| Total conveyor length | 3000 mm |
| Infeed to diverter | 1500 mm |
| Diverter to Outfeed B | 1000 mm |
| Diverter to Outfeed C | 1000 mm |
| Conveyor width | 400 mm |
| Belt speed (nominal) | 0.5 m/s |
| Box size | 200 x 200 x 150 mm |
