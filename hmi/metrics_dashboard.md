# Metrics Dashboard Screen

## Layout

```
+=====================================================================+
|                    MINI-FULFILLMENT CONVEYOR SYSTEM                  |
|                        Metrics Dashboard                             |
+=====================================================================+
|                                                                     |
|  +-------------------+  +-------------------+  +-------------------+|
|  |   BOXES PROCESSED |  |  AVG CYCLE TIME   |  |    THROUGHPUT     ||
|  |                   |  |                   |  |                   ||
|  |      [ 142 ]      |  |    [ 3.2 s ]      |  |  [ 62.5 /hr ]    ||
|  |                   |  |                   |  |                   ||
|  +-------------------+  +-------------------+  +-------------------+|
|                                                                     |
|  +-------------------+  +-------------------+  +-------------------+|
|  |    JAM EVENTS     |  |  LAST CYCLE TIME  |  |    UPTIME %       ||
|  |                   |  |                   |  |                   ||
|  |      [ 3 ]        |  |    [ 2.8 s ]      |  |   [ 97.2% ]      ||
|  |                   |  |                   |  |                   ||
|  +-------------------+  +-------------------+  +-------------------+|
|                                                                     |
+---------------------------------------------------------------------+
|                       TIME STATISTICS                               |
|                                                                     |
|  Running Time:  [ 02:15:32 ]     Fault Time: [ 00:03:48 ]          |
|  Total Time:    [ 02:19:20 ]     Availability: [ 97.3% ]           |
|                                                                     |
+---------------------------------------------------------------------+
|                    ADJUSTABLE PARAMETERS                            |
|                                                                     |
|  Jam Timeout:     [  4.0  ] seconds   (range: 1.0 - 10.0)         |
|  Conveyor Speed:  [  1.0  ]           (range: 0.1 - 1.0)          |
|                                                                     |
|  [ APPLY PARAMETERS ]    [ RESET METRICS ]                          |
|                                                                     |
+=====================================================================+
```

## Element Details

### KPI Tiles (Top Section)

Each tile is a rounded rectangle with a label, large numeric value, and unit.

| Tile | Tag | Format | Unit |
|---|---|---|---|
| Boxes Processed | `GVL.rHMI_BoxCount` | Integer | boxes |
| Avg Cycle Time | `GVL.rHMI_AvgCycleTime` | 1 decimal | seconds |
| Throughput | `GVL.rHMI_Throughput` | 1 decimal | boxes/hr |
| Jam Events | `GVL.rHMI_JamCount` | Integer | events |
| Last Cycle Time | `GVL.stMetrics.rLastCycleTime` | 1 decimal | seconds |
| Uptime % | Calculated | 1 decimal | % |

**Uptime calculation:**
```
Uptime% = (rRunningTime / (rRunningTime + rFaultTime)) * 100
```

### Time Statistics Section

| Field | Tag | Format |
|---|---|---|
| Running Time | `GVL.stMetrics.rRunningTime` | HH:MM:SS (computed from seconds) |
| Fault Time | `GVL.stMetrics.rFaultTime` | HH:MM:SS |
| Total Time | Running + Fault | HH:MM:SS |
| Availability | Uptime % | Percentage with 1 decimal |

### Adjustable Parameters

| Parameter | Tag (Read/Write) | Type | Range | Default |
|---|---|---|---|---|
| Jam Timeout | `GVL.rJamTimeoutSec` | REAL | 1.0 - 10.0 s | 4.0 s |
| Conveyor Speed | `GVL.rConveyorSpeed` | REAL | 0.1 - 1.0 | 1.0 |

- Input fields with numeric entry
- Range validation: reject out-of-range values
- APPLY button writes new values to PLC tags
- RESET METRICS button zeroes all counters/timers (writes to a `bResetMetrics` flag in GVL)

### Color Coding for KPI Tiles

| Metric | Green | Yellow | Red |
|---|---|---|---|
| Throughput | >= 60 | 40 - 59 | < 40 |
| Jam Events | 0 | 1 - 2 | > 2 |
| Uptime % | >= 95 | 80 - 94 | < 80 |
| Avg Cycle Time | <= 4.0 | 4.0 - 6.0 | > 6.0 |

## CODESYS Visualization Implementation

1. Create visualization: `VIS_MetricsDashboard`
2. Canvas size: 1024 x 768 pixels
3. Use rectangles with dynamic color for KPI tiles
4. Use text fields with variable binding for numeric displays
5. Use input fields (Edit-box) for parameter entry
6. Add a navigation bar at the top to switch between all three screens:
   - `VIS_MainOverview`
   - `VIS_AlarmsStatus`
   - `VIS_MetricsDashboard`

## Navigation

All three HMI screens should include a navigation bar:

```
[ Main Overview ]  [ Alarms & Status ]  [ Metrics Dashboard ]
```

Each button navigates to the corresponding visualization using CODESYS's "Change to visualization" action.
