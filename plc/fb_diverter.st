(* =============================================================================
   FB_Diverter - Accept/Reject Routing Function Block
   Mini-Fulfillment Conveyor System
   
   Controls the diverter gate to route boxes to Station B (accept) or
   Station C (reject). Uses a pattern-based accept/reject decision for
   deterministic testing (every 3rd box is rejected).
   
   Diverter safe state: de-energized (FALSE) = Station B (accept path).
   ============================================================================= *)

FUNCTION_BLOCK FB_Diverter
VAR_INPUT
    bInfeedPE       : BOOL;         (* Infeed photoeye - box arrived *)
    bDiverterPE     : BOOL;         (* Diverter photoeye - box at decision point *)
    bSystemRunning  : BOOL;         (* TRUE when system is RUNNING in AUTO mode *)
    bAutoMode       : BOOL;         (* TRUE when in auto mode *)
END_VAR

VAR_OUTPUT
    bDiverterOutput : BOOL := FALSE;    (* Diverter actuator command *)
    bRejectActive   : BOOL := FALSE;    (* TRUE when current box is being rejected *)
    diBoxCounter    : DINT := 0;        (* Running box counter for pattern *)
END_VAR

VAR
    bInfeedPrev     : BOOL := FALSE;    (* Previous scan infeed PE for edge detection *)
    bDiverterPrev   : BOOL := FALSE;    (* Previous scan diverter PE for edge detection *)
    bInfeedRising   : BOOL := FALSE;    (* Infeed PE rising edge *)
    bDiverterRising : BOOL := FALSE;    (* Diverter PE rising edge *)
    bDiverterFalling : BOOL := FALSE;   (* Diverter PE falling edge *)
    bRejectNext     : BOOL := FALSE;    (* Flag: next box should be rejected *)
    bDiverterLocked : BOOL := FALSE;    (* Diverter position locked while box is at gate *)
END_VAR

(* Only process routing in auto mode while running *)
IF bSystemRunning AND bAutoMode THEN

    (* --- Edge Detection --- *)
    bInfeedRising := bInfeedPE AND NOT bInfeedPrev;
    bDiverterRising := bDiverterPE AND NOT bDiverterPrev;
    bDiverterFalling := NOT bDiverterPE AND bDiverterPrev;
    
    (* --- Box Arrival at Infeed: determine accept/reject --- *)
    IF bInfeedRising THEN
        diBoxCounter := diBoxCounter + 1;
        
        (* Pattern: every 3rd box is rejected *)
        IF (diBoxCounter MOD 3) = 0 THEN
            bRejectNext := TRUE;
        ELSE
            bRejectNext := FALSE;
        END_IF
    END_IF
    
    (* --- Box Reaches Diverter: actuate if reject --- *)
    IF bDiverterRising THEN
        bDiverterLocked := TRUE;
        IF bRejectNext THEN
            bDiverterOutput := TRUE;    (* Energize = route to Station C *)
            bRejectActive := TRUE;
        ELSE
            bDiverterOutput := FALSE;   (* De-energized = route to Station B *)
            bRejectActive := FALSE;
        END_IF
    END_IF
    
    (* --- Box Clears Diverter: return to safe position --- *)
    IF bDiverterFalling AND bDiverterLocked THEN
        bDiverterOutput := FALSE;       (* Return to safe position *)
        bDiverterLocked := FALSE;
        bRejectActive := FALSE;
        bRejectNext := FALSE;           (* Clear flag for next box *)
    END_IF

ELSE
    (* Not running or in manual mode: diverter in safe position *)
    bDiverterOutput := FALSE;
    bRejectActive := FALSE;
    bDiverterLocked := FALSE;
END_IF

(* --- Update previous states --- *)
bInfeedPrev := bInfeedPE;
bDiverterPrev := bDiverterPE;
