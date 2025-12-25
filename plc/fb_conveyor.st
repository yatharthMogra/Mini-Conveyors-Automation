(* =============================================================================
   FB_Conveyor - Conveyor Motor Control Function Block
   Mini-Fulfillment Conveyor System
   
   Controls the main conveyor belt motor based on system state and mode.
   Provides speed reference output for potential variable-speed drive.
   ============================================================================= *)

FUNCTION_BLOCK FB_Conveyor
VAR_INPUT
    bRunCommand     : BOOL;         (* Motor run command from state machine *)
    bJogCommand     : BOOL;         (* Jog command from manual mode *)
    bManualMode     : BOOL;         (* TRUE when in manual mode *)
    rSpeedSetpoint  : REAL := 1.0;  (* Speed setpoint 0.0 to 1.0 *)
END_VAR

VAR_OUTPUT
    bMotorOutput    : BOOL;         (* Final motor on/off command *)
    rSpeedRef       : REAL;         (* Speed reference output (0.0 to 1.0) *)
    bMotorRunning   : BOOL;         (* Feedback: motor is currently running *)
END_VAR

VAR
    rJogSpeed       : REAL := 0.3;  (* Jog speed as fraction of full speed *)
END_VAR

(* --- Determine motor state --- *)
IF bManualMode THEN
    (* Manual mode: motor runs only while jog is held *)
    bMotorOutput := bJogCommand;
    IF bJogCommand THEN
        rSpeedRef := rJogSpeed;     (* Reduced speed for jogging *)
    ELSE
        rSpeedRef := 0.0;
    END_IF
ELSE
    (* Auto mode: motor runs continuously when commanded *)
    bMotorOutput := bRunCommand;
    IF bRunCommand THEN
        rSpeedRef := rSpeedSetpoint;
    ELSE
        rSpeedRef := 0.0;
    END_IF
END_IF

(* --- Motor running feedback --- *)
bMotorRunning := bMotorOutput;
