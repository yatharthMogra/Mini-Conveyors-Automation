(* =============================================================================
   types.st - Type Definitions
   Mini-Fulfillment Conveyor System
   
   Enumerations and structures used throughout the PLC program.
   ============================================================================= *)

(* System operating states *)
TYPE E_SystemState :
(
    STOPPED  := 0,   (* System is idle, motor off, safe to interact *)
    STARTING := 1,   (* Pre-run checks in progress *)
    RUNNING  := 2,   (* Normal operation, conveyor moving *)
    FAULT    := 3    (* Fault condition active, motor off, alarm on *)
);
END_TYPE

(* Fault codes *)
TYPE E_FaultCode :
(
    NONE            := 0,   (* No fault *)
    ESTOP           := 1,   (* Emergency stop activated *)
    JAM_INFEED      := 2,   (* Jam detected at infeed photoeye *)
    JAM_DIVERTER    := 3,   (* Jam detected at diverter photoeye *)
    JAM_OUTFEED_B   := 4,   (* Jam detected at outfeed B photoeye *)
    JAM_OUTFEED_C   := 5    (* Jam detected at outfeed C photoeye *)
);
END_TYPE

(* Operating mode *)
TYPE E_OperatingMode :
(
    AUTO   := 0,   (* Automatic mode - full autonomous operation *)
    MANUAL := 1    (* Manual mode - jog only, no auto routing *)
);
END_TYPE

(* Metrics data structure *)
TYPE ST_Metrics :
STRUCT
    diBoxCount       : DINT;    (* Total boxes processed *)
    rAvgCycleTime    : REAL;    (* Average cycle time in seconds *)
    diJamCount       : DINT;    (* Total jam events *)
    rThroughput      : REAL;    (* Current throughput in boxes/hour *)
    rRunningTime     : REAL;    (* Total running time in seconds *)
    rFaultTime       : REAL;    (* Total fault/downtime in seconds *)
    rLastCycleTime   : REAL;    (* Most recent box cycle time *)
    rCycleTimeSum    : REAL;    (* Sum of all cycle times for averaging *)
END_STRUCT
END_TYPE

(* Jam detection status per photoeye *)
TYPE ST_JamStatus :
STRUCT
    bBlocked         : BOOL;    (* Photoeye currently blocked *)
    bJamDetected     : BOOL;    (* Jam threshold exceeded *)
    tBlockedDuration : TIME;    (* How long PE has been blocked *)
END_STRUCT
END_TYPE
