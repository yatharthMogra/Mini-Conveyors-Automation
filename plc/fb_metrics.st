(* =============================================================================
   FB_Metrics - Metrics Tracking Function Block
   Mini-Fulfillment Conveyor System
   
   Tracks operational metrics:
   - Box count (total processed)
   - Cycle time (infeed to outfeed, running average)
   - Jam count
   - Throughput (boxes per hour)
   - Running time vs fault/downtime
   ============================================================================= *)

FUNCTION_BLOCK FB_Metrics
VAR_INPUT
    bInfeedPE       : BOOL;         (* Infeed photoeye *)
    bOutfeedBPE     : BOOL;         (* Outfeed B photoeye *)
    bOutfeedCPE     : BOOL;         (* Outfeed C photoeye *)
    bSystemRunning  : BOOL;         (* TRUE when state = RUNNING *)
    bFaultState     : BOOL;         (* TRUE when state = FAULT *)
    bJamEvent       : BOOL;         (* Rising edge triggers jam count increment *)
    tScanTime       : TIME := T#10MS;   (* PLC scan time for time accumulation *)
END_VAR

VAR_OUTPUT
    stMetrics       : ST_Metrics;   (* Output metrics structure *)
END_VAR

VAR
    (* Edge detection *)
    bInfeedPrev     : BOOL := FALSE;
    bOutfeedBPrev   : BOOL := FALSE;
    bOutfeedCPrev   : BOOL := FALSE;
    bJamEventPrev   : BOOL := FALSE;
    
    (* Cycle time measurement *)
    bCycleActive    : BOOL := FALSE;    (* A box is being tracked *)
    tCycleTimer     : TON;              (* Timer for current box cycle *)
    rCurrentCycle   : REAL := 0.0;      (* Current cycle time in seconds *)
    
    (* Time accumulation *)
    tRunTimer       : TON;              (* Accumulates running time *)
    tFaultTimer     : TON;              (* Accumulates fault time *)
    rScanTimeSec    : REAL;             (* Scan time converted to seconds *)
    
    (* Edge signals *)
    bInfeedRising   : BOOL;
    bOutfeedBRising : BOOL;
    bOutfeedCRising : BOOL;
    bJamRising      : BOOL;
END_VAR

(* --- Compute scan time in seconds --- *)
rScanTimeSec := TIME_TO_REAL(tScanTime) / 1000.0;

(* --- Edge Detection --- *)
bInfeedRising := bInfeedPE AND NOT bInfeedPrev;
bOutfeedBRising := bOutfeedBPE AND NOT bOutfeedBPrev;
bOutfeedCRising := bOutfeedCPE AND NOT bOutfeedCPrev;
bJamRising := bJamEvent AND NOT bJamEventPrev;

(* =========================================================================
   BOX CYCLE TIME TRACKING
   ========================================================================= *)

(* Start cycle timer when box arrives at infeed *)
IF bInfeedRising AND NOT bCycleActive THEN
    bCycleActive := TRUE;
    tCycleTimer(IN := FALSE);   (* Reset timer *)
END_IF

(* Run cycle timer while tracking a box *)
IF bCycleActive THEN
    tCycleTimer(IN := TRUE, PT := T#300S);  (* Max 300s cycle, should never reach *)
END_IF

(* Complete cycle when box reaches either outfeed *)
IF bCycleActive AND (bOutfeedBRising OR bOutfeedCRising) THEN
    (* Record cycle time *)
    rCurrentCycle := TIME_TO_REAL(tCycleTimer.ET) / 1000.0;  (* Convert to seconds *)
    stMetrics.rLastCycleTime := rCurrentCycle;
    
    (* Increment box count *)
    stMetrics.diBoxCount := stMetrics.diBoxCount + 1;
    
    (* Update running average *)
    stMetrics.rCycleTimeSum := stMetrics.rCycleTimeSum + rCurrentCycle;
    IF stMetrics.diBoxCount > 0 THEN
        stMetrics.rAvgCycleTime := stMetrics.rCycleTimeSum / DINT_TO_REAL(stMetrics.diBoxCount);
    END_IF
    
    (* Reset cycle tracking *)
    bCycleActive := FALSE;
    tCycleTimer(IN := FALSE);
END_IF

(* =========================================================================
   JAM COUNT
   ========================================================================= *)
IF bJamRising THEN
    stMetrics.diJamCount := stMetrics.diJamCount + 1;
END_IF

(* =========================================================================
   RUNNING TIME AND FAULT TIME ACCUMULATION
   ========================================================================= *)

(* Accumulate running time using scan-by-scan addition *)
IF bSystemRunning THEN
    stMetrics.rRunningTime := stMetrics.rRunningTime + rScanTimeSec;
END_IF

IF bFaultState THEN
    stMetrics.rFaultTime := stMetrics.rFaultTime + rScanTimeSec;
END_IF

(* =========================================================================
   THROUGHPUT CALCULATION
   ========================================================================= *)

(* Throughput = boxes per hour *)
IF stMetrics.rRunningTime > 1.0 THEN  (* Avoid division by zero, wait at least 1 second *)
    stMetrics.rThroughput := DINT_TO_REAL(stMetrics.diBoxCount) / (stMetrics.rRunningTime / 3600.0);
ELSE
    stMetrics.rThroughput := 0.0;
END_IF

(* =========================================================================
   UPDATE PREVIOUS STATES
   ========================================================================= *)
bInfeedPrev := bInfeedPE;
bOutfeedBPrev := bOutfeedBPE;
bOutfeedCPrev := bOutfeedCPE;
bJamEventPrev := bJamEvent;
