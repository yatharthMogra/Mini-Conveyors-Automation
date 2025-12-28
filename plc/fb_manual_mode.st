(* =============================================================================
   FB_ManualMode - Manual / Jog Control Function Block
   Mini-Fulfillment Conveyor System
   
   Provides manual jog control for the conveyor. In manual mode, the
   conveyor runs only while the jog button is held, at reduced speed.
   Safety interlocks remain active. No automatic routing occurs.
   ============================================================================= *)

FUNCTION_BLOCK FB_ManualMode
VAR_INPUT
    bManualMode     : BOOL;         (* TRUE when mode selector = Manual *)
    bJogFwdPB       : BOOL;         (* Jog forward pushbutton (or HMI button) *)
    bSystemRunning  : BOOL;         (* TRUE when system state = RUNNING *)
    bSafeToRun      : BOOL;         (* Safety permissive from FB_Safety *)
END_VAR

VAR_OUTPUT
    bMotorJogCmd    : BOOL := FALSE;    (* Motor jog command *)
    bJogActive      : BOOL := FALSE;    (* TRUE while jogging *)
END_VAR

VAR
    (* No internal variables needed for basic jog *)
END_VAR

(* --- Jog Logic --- *)
(* Jog is allowed only when:
   1. System is in RUNNING state
   2. Mode selector is set to Manual
   3. Safety permissive is TRUE
   4. Jog button is held
*)

IF bManualMode AND bSystemRunning AND bSafeToRun THEN
    IF bJogFwdPB THEN
        bMotorJogCmd := TRUE;
        bJogActive := TRUE;
    ELSE
        bMotorJogCmd := FALSE;
        bJogActive := FALSE;
    END_IF
ELSE
    bMotorJogCmd := FALSE;
    bJogActive := FALSE;
END_IF
