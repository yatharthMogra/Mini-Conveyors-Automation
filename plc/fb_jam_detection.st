(* =============================================================================
   FB_JamDetection - Jam Detection and Fault Handling Function Block
   Mini-Fulfillment Conveyor System
   
   Monitors all photoeyes for jam conditions. A jam is detected when any
   photoeye remains blocked for longer than the configurable timeout.
   Identifies the jam location and provides fault clear logic.
   ============================================================================= *)

FUNCTION_BLOCK FB_JamDetection
VAR_INPUT
    bInfeedPE       : BOOL;         (* Infeed photoeye state *)
    bDiverterPE     : BOOL;         (* Diverter photoeye state *)
    bOutfeedBPE     : BOOL;         (* Outfeed B photoeye state *)
    bOutfeedCPE     : BOOL;         (* Outfeed C photoeye state *)
    bSystemRunning  : BOOL;         (* TRUE when system is in RUNNING state *)
    bFaultClear     : BOOL;         (* Fault clear command *)
    rJamTimeoutSec  : REAL := 4.0;  (* Jam timeout in seconds (configurable from HMI) *)
END_VAR

VAR_OUTPUT
    bJamDetected    : BOOL := FALSE;    (* TRUE when any jam is active *)
    eFaultCode      : E_FaultCode;      (* Fault code identifying jam location *)
    sFaultMessage   : STRING(80);       (* Fault description *)
    stInfeedJam     : ST_JamStatus;     (* Infeed PE jam status *)
    stDiverterJam   : ST_JamStatus;     (* Diverter PE jam status *)
    stOutfeedBJam   : ST_JamStatus;     (* Outfeed B PE jam status *)
    stOutfeedCJam   : ST_JamStatus;     (* Outfeed C PE jam status *)
END_VAR

VAR
    tonInfeed       : TON;      (* Jam timer for infeed PE *)
    tonDiverter     : TON;      (* Jam timer for diverter PE *)
    tonOutfeedB     : TON;      (* Jam timer for outfeed B PE *)
    tonOutfeedC     : TON;      (* Jam timer for outfeed C PE *)
    tJamTimeout     : TIME;     (* Jam timeout as TIME value *)
    bFaultClearPrev : BOOL := FALSE;    (* Previous scan fault clear *)
    bFaultClearRising : BOOL := FALSE;  (* Rising edge of fault clear *)
    bJamLatched     : BOOL := FALSE;    (* Jam fault is latched until cleared *)
END_VAR

(* --- Convert timeout parameter --- *)
tJamTimeout := REAL_TO_TIME(rJamTimeoutSec * 1000.0);  (* seconds to milliseconds *)

(* --- Edge detection on fault clear --- *)
bFaultClearRising := bFaultClear AND NOT bFaultClearPrev;
bFaultClearPrev := bFaultClear;

(* --- Only monitor for jams while system is running or jam is latched --- *)
IF bSystemRunning OR bJamLatched THEN

    (* === Infeed Photoeye Jam Timer === *)
    tonInfeed(IN := bInfeedPE AND bSystemRunning, PT := tJamTimeout);
    stInfeedJam.bBlocked := bInfeedPE;
    stInfeedJam.tBlockedDuration := tonInfeed.ET;
    
    IF tonInfeed.Q AND NOT bJamLatched THEN
        stInfeedJam.bJamDetected := TRUE;
        bJamLatched := TRUE;
        eFaultCode := E_FaultCode.JAM_INFEED;
        sFaultMessage := 'JAM DETECTED AT INFEED (Station A)';
    END_IF
    
    (* === Diverter Photoeye Jam Timer === *)
    tonDiverter(IN := bDiverterPE AND bSystemRunning, PT := tJamTimeout);
    stDiverterJam.bBlocked := bDiverterPE;
    stDiverterJam.tBlockedDuration := tonDiverter.ET;
    
    IF tonDiverter.Q AND NOT bJamLatched THEN
        stDiverterJam.bJamDetected := TRUE;
        bJamLatched := TRUE;
        eFaultCode := E_FaultCode.JAM_DIVERTER;
        sFaultMessage := 'JAM DETECTED AT DIVERTER';
    END_IF
    
    (* === Outfeed B Photoeye Jam Timer === *)
    tonOutfeedB(IN := bOutfeedBPE AND bSystemRunning, PT := tJamTimeout);
    stOutfeedBJam.bBlocked := bOutfeedBPE;
    stOutfeedBJam.tBlockedDuration := tonOutfeedB.ET;
    
    IF tonOutfeedB.Q AND NOT bJamLatched THEN
        stOutfeedBJam.bJamDetected := TRUE;
        bJamLatched := TRUE;
        eFaultCode := E_FaultCode.JAM_OUTFEED_B;
        sFaultMessage := 'JAM DETECTED AT OUTFEED B (Station B)';
    END_IF
    
    (* === Outfeed C Photoeye Jam Timer === *)
    tonOutfeedC(IN := bOutfeedCPE AND bSystemRunning, PT := tJamTimeout);
    stOutfeedCJam.bBlocked := bOutfeedCPE;
    stOutfeedCJam.tBlockedDuration := tonOutfeedC.ET;
    
    IF tonOutfeedC.Q AND NOT bJamLatched THEN
        stOutfeedCJam.bJamDetected := TRUE;
        bJamLatched := TRUE;
        eFaultCode := E_FaultCode.JAM_OUTFEED_C;
        sFaultMessage := 'JAM DETECTED AT OUTFEED C (Station C)';
    END_IF

ELSE
    (* System not running and no latched jam: reset all timers *)
    tonInfeed(IN := FALSE);
    tonDiverter(IN := FALSE);
    tonOutfeedB(IN := FALSE);
    tonOutfeedC(IN := FALSE);
END_IF

(* --- Jam Fault Clear Logic --- *)
(* Clear jam when: operator presses fault clear AND the jammed PE is no longer blocked *)
IF bJamLatched AND bFaultClearRising THEN
    CASE eFaultCode OF
        E_FaultCode.JAM_INFEED:
            IF NOT bInfeedPE THEN
                bJamLatched := FALSE;
                stInfeedJam.bJamDetected := FALSE;
                eFaultCode := E_FaultCode.NONE;
                sFaultMessage := '';
            END_IF
        
        E_FaultCode.JAM_DIVERTER:
            IF NOT bDiverterPE THEN
                bJamLatched := FALSE;
                stDiverterJam.bJamDetected := FALSE;
                eFaultCode := E_FaultCode.NONE;
                sFaultMessage := '';
            END_IF
        
        E_FaultCode.JAM_OUTFEED_B:
            IF NOT bOutfeedBPE THEN
                bJamLatched := FALSE;
                stOutfeedBJam.bJamDetected := FALSE;
                eFaultCode := E_FaultCode.NONE;
                sFaultMessage := '';
            END_IF
        
        E_FaultCode.JAM_OUTFEED_C:
            IF NOT bOutfeedCPE THEN
                bJamLatched := FALSE;
                stOutfeedCJam.bJamDetected := FALSE;
                eFaultCode := E_FaultCode.NONE;
                sFaultMessage := '';
            END_IF
    END_CASE
END_IF

(* --- Aggregate jam status --- *)
bJamDetected := bJamLatched;
