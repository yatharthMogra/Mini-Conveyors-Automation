(* =============================================================================
   global_vars.st - Global Variables (Global Variable List)
   Mini-Fulfillment Conveyor System
   
   Shared variables used across program blocks and for HMI binding.
   ============================================================================= *)

VAR_GLOBAL
    (* =========================================================================
       SYSTEM STATE
       ========================================================================= *)
    eSystemState    : E_SystemState := STOPPED;    (* Current system state *)
    eOperatingMode  : E_OperatingMode := AUTO;     (* Current operating mode *)
    eFaultCode      : E_FaultCode := NONE;         (* Active fault code *)
    sFaultMessage   : STRING(80) := '';             (* Active fault description *)
    
    (* =========================================================================
       SAFETY FLAGS
       ========================================================================= *)
    bSafeToRun      : BOOL := FALSE;   (* TRUE when all safety checks pass *)
    bFaultActive    : BOOL := FALSE;   (* TRUE when any fault is active *)
    bEStopLatched   : BOOL := FALSE;   (* TRUE when E-Stop has been activated, requires clear *)
    bJamDetected    : BOOL := FALSE;   (* TRUE when any photoeye jam is detected *)
    
    (* =========================================================================
       CONTROL FLAGS
       ========================================================================= *)
    bMotorRunCmd    : BOOL := FALSE;   (* Motor run command from state machine *)
    bRejectNext     : BOOL := FALSE;   (* TRUE = next box routes to Station C *)
    diBoxCounter    : DINT := 0;       (* Running box count for routing pattern *)
    
    (* =========================================================================
       JAM DETECTION STATUS
       ========================================================================= *)
    stJamInfeed     : ST_JamStatus;    (* Jam status for infeed PE *)
    stJamDiverter   : ST_JamStatus;    (* Jam status for diverter PE *)
    stJamOutfeedB   : ST_JamStatus;    (* Jam status for outfeed B PE *)
    stJamOutfeedC   : ST_JamStatus;    (* Jam status for outfeed C PE *)
    
    (* =========================================================================
       METRICS
       ========================================================================= *)
    stMetrics       : ST_Metrics;      (* Aggregated metrics structure *)
    
    (* =========================================================================
       HMI INTERFACE - Commands (HMI -> PLC)
       ========================================================================= *)
    bHMI_Start      : BOOL := FALSE;   (* Start command from HMI *)
    bHMI_Stop       : BOOL := FALSE;   (* Stop command from HMI *)
    bHMI_FaultClear : BOOL := FALSE;   (* Fault clear command from HMI *)
    bHMI_JogFwd     : BOOL := FALSE;   (* Jog forward command from HMI (manual mode) *)
    
    (* =========================================================================
       HMI INTERFACE - Parameters (HMI -> PLC)
       ========================================================================= *)
    rJamTimeoutSec  : REAL := 4.0;     (* Jam detection timeout in seconds (adjustable) *)
    rConveyorSpeed  : REAL := 1.0;     (* Conveyor speed setpoint 0.0 to 1.0 (1.0 = full speed) *)
    
    (* =========================================================================
       HMI INTERFACE - Status (PLC -> HMI)
       ========================================================================= *)
    iHMI_State      : INT := 0;        (* System state as INT for HMI display *)
    sHMI_FaultMsg   : STRING(80) := '';(* Fault message for HMI display *)
    rHMI_BoxCount   : DINT := 0;       (* Box count for HMI display *)
    rHMI_AvgCycleTime : REAL := 0.0;   (* Avg cycle time for HMI display *)
    rHMI_JamCount   : DINT := 0;       (* Jam count for HMI display *)
    rHMI_Throughput : REAL := 0.0;     (* Throughput for HMI display *)
    
    (* =========================================================================
       TIMING
       ========================================================================= *)
    tCycleStartTime : TIME := T#0S;    (* Timestamp when current box entered infeed *)
    bCycleActive    : BOOL := FALSE;   (* TRUE when a box is being tracked through the system *)
END_VAR
