(* =============================================================================
   io_mapping.st - I/O Address Mapping (Global Variable List)
   Mini-Fulfillment Conveyor System
   
   Maps physical I/O addresses to symbolic names.
   This GVL is the ONLY place where physical addresses appear.
   All other program blocks reference these symbolic names.
   ============================================================================= *)

VAR_GLOBAL
    (* =========================================================================
       DIGITAL INPUTS
       ========================================================================= *)
    
    (* Operator panel *)
    bStartPB       AT %IX0.0 : BOOL;   (* Start pushbutton - NO, TRUE on press *)
    bStopPB        AT %IX0.1 : BOOL;   (* Stop pushbutton - NC, FALSE on press *)
    bEStop         AT %IX0.2 : BOOL;   (* E-Stop - NC, FALSE when activated *)
    bModeSelector  AT %IX0.3 : BOOL;   (* Mode switch - FALSE=Auto, TRUE=Manual *)
    
    (* Photoeyes - TRUE when blocked by a box *)
    bInfeedPE      AT %IX1.0 : BOOL;   (* Infeed photoeye at Station A *)
    bDiverterPE    AT %IX1.1 : BOOL;   (* Diverter photoeye at routing point *)
    bOutfeedBPE    AT %IX1.2 : BOOL;   (* Outfeed B photoeye at Station B (accept) *)
    bOutfeedCPE    AT %IX1.3 : BOOL;   (* Outfeed C photoeye at Station C (reject) *)
    
    (* =========================================================================
       DIGITAL OUTPUTS
       ========================================================================= *)
    
    bConveyorMotor     AT %QX0.0 : BOOL;   (* Main conveyor belt motor *)
    bDiverterActuator  AT %QX0.1 : BOOL;   (* Diverter gate solenoid - FALSE=StationB, TRUE=StationC *)
    bAlarmBuzzer       AT %QX0.2 : BOOL;   (* Fault alarm buzzer *)
    bStatusGreen       AT %QX0.3 : BOOL;   (* Green status light - RUNNING *)
    bStatusRed         AT %QX0.4 : BOOL;   (* Red status light - FAULT *)
END_VAR
