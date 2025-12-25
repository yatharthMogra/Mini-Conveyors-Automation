(* =============================================================================
   FB_Safety - Safety and Interlock Function Block
   Mini-Fulfillment Conveyor System
   
   Monitors E-Stop, evaluates safety interlocks, and provides a safe-to-run
   permissive signal. E-Stop is latching: once activated, it requires both
   the E-Stop to be reset (circuit closed) AND a Fault Clear command.
   ============================================================================= *)

FUNCTION_BLOCK FB_Safety
VAR_INPUT
    bEStop          : BOOL;     (* E-Stop input - NC circuit: TRUE = healthy, FALSE = activated *)
    bStopPB         : BOOL;     (* Stop pushbutton - NC: TRUE = not pressed, FALSE = pressed *)
    bStartPB        : BOOL;     (* Start pushbutton - NO: TRUE = pressed *)
    bFaultClear     : BOOL;     (* Fault clear command (pushbutton or HMI) *)
    bJamActive      : BOOL;     (* Jam fault from FB_JamDetection *)
END_VAR

VAR_OUTPUT
    bSafeToRun      : BOOL;     (* TRUE when all safety conditions met for running *)
    bFaultActive    : BOOL;     (* TRUE when any fault is active *)
    bEStopLatched   : BOOL;     (* TRUE when E-Stop has been activated and not yet cleared *)
    bStartCmd       : BOOL;     (* Rising edge of start command, qualified by safety *)
    bStopCmd        : BOOL;     (* Stop command detected *)
    eFaultCode      : E_FaultCode;  (* Active fault code *)
    sFaultMessage   : STRING(80);   (* Fault description text *)
END_VAR

VAR
    bEStopPrev      : BOOL := TRUE;     (* Previous scan E-Stop state for edge detection *)
    bStartPrev      : BOOL := FALSE;    (* Previous scan start PB for rising edge *)
    bStopPrev       : BOOL := TRUE;     (* Previous scan stop PB for falling edge *)
    bFaultClearPrev : BOOL := FALSE;    (* Previous scan fault clear for rising edge *)
    bStartRisingEdge : BOOL := FALSE;   (* One-shot start command *)
    bFaultClearRising : BOOL := FALSE;  (* One-shot fault clear *)
END_VAR

(* --- Edge Detection --- *)
bStartRisingEdge := bStartPB AND NOT bStartPrev;
bFaultClearRising := bFaultClear AND NOT bFaultClearPrev;

(* --- E-Stop Latching Logic --- *)
(* E-Stop is NC: TRUE = healthy. When it goes FALSE, latch the fault. *)
IF NOT bEStop THEN
    bEStopLatched := TRUE;
    eFaultCode := E_FaultCode.ESTOP;
    sFaultMessage := 'EMERGENCY STOP ACTIVATED';
END_IF

(* --- E-Stop Latch Clear --- *)
(* Clear only when: E-Stop circuit is healthy again AND operator requests clear *)
IF bEStopLatched AND bFaultClearRising AND bEStop THEN
    bEStopLatched := FALSE;
    (* Only clear fault code if no other faults active *)
    IF NOT bJamActive THEN
        eFaultCode := E_FaultCode.NONE;
        sFaultMessage := '';
    END_IF
END_IF

(* --- Aggregate Fault Status --- *)
bFaultActive := bEStopLatched OR bJamActive;

(* --- Update fault code/message for jam (if E-Stop not the cause) --- *)
IF bJamActive AND NOT bEStopLatched THEN
    (* Fault code for jam is set by FB_JamDetection via global vars *)
    (* We just ensure bFaultActive stays TRUE *)
    ;
END_IF

(* --- Safe-to-Run Permissive --- *)
(* All conditions must be TRUE for the system to be allowed to run *)
bSafeToRun := bEStop              (* E-Stop circuit healthy *)
          AND NOT bEStopLatched   (* No latched E-Stop fault *)
          AND NOT bJamActive      (* No active jam *)
          AND bStopPB;            (* Stop PB not pressed (NC = TRUE when not pressed) *)

(* --- Start Command (qualified) --- *)
(* Only issue start if safety permits *)
bStartCmd := bStartRisingEdge AND bSafeToRun;

(* --- Stop Command --- *)
(* Stop detected on falling edge of NC stop button (TRUE -> FALSE) *)
bStopCmd := bStopPrev AND NOT bStopPB;

(* --- Update previous states for next scan --- *)
bEStopPrev := bEStop;
bStartPrev := bStartPB;
bStopPrev := bStopPB;
bFaultClearPrev := bFaultClear;
