(* =============================================================================
   PRG_Main - Main Program (State Machine Orchestrator)
   Mini-Fulfillment Conveyor System
   
   Central state machine that coordinates all function blocks.
   Called every scan cycle by MainTask (10 ms).
   ============================================================================= *)

PROGRAM PRG_Main
VAR
    (* Function block instances *)
    fbSafety        : FB_Safety;
    fbConveyor      : FB_Conveyor;
    fbJamDetection  : FB_JamDetection;
    fbDiverter      : FB_Diverter;
    fbManualMode    : FB_ManualMode;
    fbMetrics       : FB_Metrics;
    
    (* Internal state *)
    tonStartDelay   : TON;              (* 1-second startup delay timer *)
    bStartDelayDone : BOOL := FALSE;    (* Startup delay completed *)
    bBlinkToggle    : BOOL := FALSE;    (* For blinking status lights *)
    tonBlink        : TON;              (* Blink timer - 500ms period *)
    tBlinkTime      : TIME := T#500MS;  (* Blink half-period *)
END_VAR

(* =========================================================================
   1. READ OPERATING MODE
   ========================================================================= *)
IF IO_Mapping.bModeSelector THEN
    GVL.eOperatingMode := E_OperatingMode.MANUAL;
ELSE
    GVL.eOperatingMode := E_OperatingMode.AUTO;
END_IF

(* =========================================================================
   2. EXECUTE SAFETY BLOCK
   ========================================================================= *)
fbSafety(
    bEStop      := IO_Mapping.bEStop,
    bStopPB     := IO_Mapping.bStopPB,
    bStartPB    := IO_Mapping.bStartPB OR GVL.bHMI_Start,
    bFaultClear := GVL.bHMI_FaultClear,
    bJamActive  := GVL.bJamDetected
);

(* Update global safety flags *)
GVL.bSafeToRun    := fbSafety.bSafeToRun;
GVL.bFaultActive  := fbSafety.bFaultActive;
GVL.bEStopLatched := fbSafety.bEStopLatched;

(* =========================================================================
   2b. EXECUTE JAM DETECTION BLOCK
   ========================================================================= *)
fbJamDetection(
    bInfeedPE       := IO_Mapping.bInfeedPE,
    bDiverterPE     := IO_Mapping.bDiverterPE,
    bOutfeedBPE     := IO_Mapping.bOutfeedBPE,
    bOutfeedCPE     := IO_Mapping.bOutfeedCPE,
    bSystemRunning  := (GVL.eSystemState = E_SystemState.RUNNING),
    bFaultClear     := GVL.bHMI_FaultClear,
    rJamTimeoutSec  := GVL.rJamTimeoutSec
);

(* Update global jam status *)
GVL.bJamDetected  := fbJamDetection.bJamDetected;
GVL.stJamInfeed   := fbJamDetection.stInfeedJam;
GVL.stJamDiverter := fbJamDetection.stDiverterJam;
GVL.stJamOutfeedB := fbJamDetection.stOutfeedBJam;
GVL.stJamOutfeedC := fbJamDetection.stOutfeedCJam;

(* Use jam fault info if jam is active, otherwise use safety fault info *)
IF fbJamDetection.bJamDetected THEN
    GVL.eFaultCode    := fbJamDetection.eFaultCode;
    GVL.sFaultMessage := fbJamDetection.sFaultMessage;
ELSE
    GVL.eFaultCode    := fbSafety.eFaultCode;
    GVL.sFaultMessage := fbSafety.sFaultMessage;
END_IF

(* =========================================================================
   2c. EXECUTE CONVEYOR BLOCK
   ========================================================================= *)
fbConveyor(
    bRunCommand     := GVL.bMotorRunCmd,
    bJogCommand     := GVL.bHMI_JogFwd,
    bManualMode     := (GVL.eOperatingMode = E_OperatingMode.MANUAL),
    rSpeedSetpoint  := GVL.rConveyorSpeed
);

(* =========================================================================
   3. STATE MACHINE
   ========================================================================= *)
CASE GVL.eSystemState OF

    (* ----- STOPPED ----- *)
    E_SystemState.STOPPED:
        (* Outputs in safe state *)
        GVL.bMotorRunCmd := FALSE;
        IO_Mapping.bDiverterActuator := FALSE;
        IO_Mapping.bAlarmBuzzer := FALSE;
        IO_Mapping.bStatusGreen := FALSE;
        IO_Mapping.bStatusRed := FALSE;
        
        (* Transition: Start command received and safe to run *)
        IF fbSafety.bStartCmd THEN
            GVL.eSystemState := E_SystemState.STARTING;
            tonStartDelay(IN := FALSE);  (* Reset timer *)
            bStartDelayDone := FALSE;
        END_IF
    
    (* ----- STARTING ----- *)
    E_SystemState.STARTING:
        GVL.bMotorRunCmd := FALSE;
        IO_Mapping.bDiverterActuator := FALSE;
        IO_Mapping.bAlarmBuzzer := FALSE;
        
        (* Blink green light during startup *)
        IO_Mapping.bStatusGreen := bBlinkToggle;
        IO_Mapping.bStatusRed := FALSE;
        
        (* 1-second startup delay *)
        tonStartDelay(IN := TRUE, PT := T#1S);
        IF tonStartDelay.Q THEN
            bStartDelayDone := TRUE;
        END_IF
        
        (* Check for faults during startup *)
        IF GVL.bFaultActive THEN
            GVL.eSystemState := E_SystemState.FAULT;
        ELSIF bStartDelayDone AND GVL.bSafeToRun THEN
            (* All pre-run checks passed *)
            GVL.eSystemState := E_SystemState.RUNNING;
        END_IF
    
    (* ----- RUNNING ----- *)
    E_SystemState.RUNNING:
        IO_Mapping.bStatusGreen := TRUE;
        IO_Mapping.bStatusRed := FALSE;
        IO_Mapping.bAlarmBuzzer := FALSE;
        
        (* Motor control depends on mode *)
        IF GVL.eOperatingMode = E_OperatingMode.AUTO THEN
            GVL.bMotorRunCmd := TRUE;
        ELSE
            (* Manual mode: motor controlled by FB_ManualMode *)
            ; (* FB_ManualMode sets bMotorRunCmd *)
        END_IF
        
        (* Transition to FAULT *)
        IF GVL.bFaultActive THEN
            GVL.eSystemState := E_SystemState.FAULT;
            GVL.bMotorRunCmd := FALSE;
        END_IF
        
        (* Transition to STOPPED on stop command *)
        IF fbSafety.bStopCmd OR GVL.bHMI_Stop THEN
            GVL.eSystemState := E_SystemState.STOPPED;
            GVL.bMotorRunCmd := FALSE;
        END_IF
    
    (* ----- FAULT ----- *)
    E_SystemState.FAULT:
        GVL.bMotorRunCmd := FALSE;
        IO_Mapping.bDiverterActuator := FALSE;  (* Safe position *)
        IO_Mapping.bStatusGreen := FALSE;
        IO_Mapping.bStatusRed := bBlinkToggle;  (* Blink red *)
        IO_Mapping.bAlarmBuzzer := TRUE;
        
        (* Transition to STOPPED when fault is cleared *)
        IF NOT GVL.bFaultActive THEN
            GVL.eSystemState := E_SystemState.STOPPED;
            IO_Mapping.bAlarmBuzzer := FALSE;
        END_IF

END_CASE

(* =========================================================================
   4. BLINK TIMER (used for status light blinking)
   ========================================================================= *)
tonBlink(IN := NOT tonBlink.Q, PT := tBlinkTime);
IF tonBlink.Q THEN
    bBlinkToggle := NOT bBlinkToggle;
END_IF

(* =========================================================================
   5. APPLY MOTOR OUTPUT (safety gating)
   ========================================================================= *)
(* Final motor output: run command AND all safety conditions *)
IO_Mapping.bConveyorMotor := GVL.bMotorRunCmd 
                         AND IO_Mapping.bEStop 
                         AND NOT GVL.bEStopLatched 
                         AND IO_Mapping.bStopPB;

(* =========================================================================
   6. UPDATE HMI TAGS
   ========================================================================= *)
GVL.iHMI_State      := TO_INT(GVL.eSystemState);
GVL.sHMI_FaultMsg   := GVL.sFaultMessage;
GVL.rHMI_BoxCount   := GVL.stMetrics.diBoxCount;
GVL.rHMI_AvgCycleTime := GVL.stMetrics.rAvgCycleTime;
GVL.rHMI_JamCount   := GVL.stMetrics.diJamCount;
GVL.rHMI_Throughput := GVL.stMetrics.rThroughput;

(* Reset one-shot HMI commands after processing *)
GVL.bHMI_Start := FALSE;
GVL.bHMI_Stop := FALSE;
GVL.bHMI_FaultClear := FALSE;
