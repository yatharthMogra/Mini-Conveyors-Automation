"""
Local PLC Logic Engine
Mini-Fulfillment Conveyor System

Python implementation of the PLC control logic for standalone simulation
(no CODESYS required). Mirrors the Structured Text function blocks:
  FB_Safety, FB_Conveyor, FB_JamDetection, FB_Diverter, FB_Metrics,
  and the PRG_Main state machine.

Called once per simulator update cycle, operating on the OPCUAClient's
local tag dictionary.
"""

import logging
from enum import IntEnum

logger = logging.getLogger(__name__)


class SystemState(IntEnum):
    STOPPED = 0
    STARTING = 1
    RUNNING = 2
    FAULT = 3


class FaultCode(IntEnum):
    NONE = 0
    ESTOP = 1
    JAM_INFEED = 2
    JAM_DIVERTER = 3
    JAM_OUTFEED_B = 4
    JAM_OUTFEED_C = 5


FAULT_MESSAGES = {
    FaultCode.NONE: "",
    FaultCode.ESTOP: "EMERGENCY STOP ACTIVATED",
    FaultCode.JAM_INFEED: "JAM DETECTED AT INFEED (Station A)",
    FaultCode.JAM_DIVERTER: "JAM DETECTED AT DIVERTER",
    FaultCode.JAM_OUTFEED_B: "JAM DETECTED AT OUTFEED B (Station B)",
    FaultCode.JAM_OUTFEED_C: "JAM DETECTED AT OUTFEED C (Station C)",
}


class LocalPLCLogic:
    """
    Executes one PLC scan cycle against the OPCUAClient's in-memory tags.
    Faithfully implements the same logic as the .st files.
    """

    def __init__(self):
        # --- State ---
        self.state = SystemState.STOPPED
        self.fault_code = FaultCode.NONE

        # --- Safety ---
        self.estop_latched = False
        self._prev_start = False
        self._prev_stop = True       # NC button: TRUE = not pressed
        self._prev_estop = True
        self._prev_fault_clear = False

        # --- Start delay ---
        self._start_timer = 0.0
        self._start_delay = 1.0      # seconds

        # --- Jam detection timers (seconds accumulated while PE blocked) ---
        self._jam_timers = {
            "infeed": 0.0,
            "diverter": 0.0,
            "outfeed_b": 0.0,
            "outfeed_c": 0.0,
        }
        self._jam_latched = False
        self._jam_location = ""

        # --- Diverter ---
        self._box_counter = 0
        self._reject_next = False
        self._prev_infeed_pe = False
        self._prev_diverter_pe = False
        self._diverter_locked = False

        # --- Metrics ---
        self._metrics_box_count = 0
        self._metrics_jam_count = 0
        self._cycle_active = False
        self._cycle_timer = 0.0
        self._cycle_time_sum = 0.0
        self._last_cycle_time = 0.0
        self._running_time = 0.0
        self._fault_time = 0.0
        self._prev_outfeed_b = False
        self._prev_outfeed_c = False
        self._prev_jam_event = False
        self._prev_infeed_metrics = False

        # --- Blink ---
        self._blink_timer = 0.0
        self._blink_on = False

    # ------------------------------------------------------------------
    # PUBLIC: call once per simulator update
    # ------------------------------------------------------------------
    def scan(self, tags: dict, dt: float):
        """
        Execute one PLC scan cycle.

        Args:
            tags: the OPCUAClient._local_tags dict (read/write in place)
            dt:   elapsed seconds since last scan
        """
        # ---- read inputs ----
        estop       = tags.get("bEStop", True)
        stop_pb     = tags.get("bStopPB", True)
        start_pb    = tags.get("bStartPB", False) or tags.get("bHMI_Start", False)
        fault_clear = tags.get("bHMI_FaultClear", False)
        mode_manual = tags.get("bModeSelector", False)
        jog_fwd     = tags.get("bHMI_JogFwd", False)

        infeed_pe    = tags.get("bInfeedPE", False)
        diverter_pe  = tags.get("bDiverterPE", False)
        outfeed_b_pe = tags.get("bOutfeedBPE", False)
        outfeed_c_pe = tags.get("bOutfeedCPE", False)

        jam_timeout  = tags.get("rJamTimeoutSec", 4.0)
        conv_speed   = tags.get("rConveyorSpeed", 1.0)

        # ---- edge detection ----
        start_rising  = start_pb and not self._prev_start
        stop_falling  = self._prev_stop and not stop_pb          # NC
        clear_rising  = fault_clear and not self._prev_fault_clear

        # ---- blink timer ----
        self._blink_timer += dt
        if self._blink_timer >= 0.5:
            self._blink_timer = 0.0
            self._blink_on = not self._blink_on

        # ==============================================================
        # 1. SAFETY
        # ==============================================================
        if not estop:
            self.estop_latched = True
            self.fault_code = FaultCode.ESTOP

        if self.estop_latched and clear_rising and estop:
            self.estop_latched = False
            if not self._jam_latched:
                self.fault_code = FaultCode.NONE

        fault_active = self.estop_latched or self._jam_latched
        safe_to_run  = estop and not self.estop_latched and not self._jam_latched and stop_pb
        start_cmd    = start_rising and safe_to_run

        # ==============================================================
        # 2. JAM DETECTION
        # ==============================================================
        if self.state == SystemState.RUNNING or self._jam_latched:
            pe_map = {
                "infeed": (infeed_pe, FaultCode.JAM_INFEED),
                "diverter": (diverter_pe, FaultCode.JAM_DIVERTER),
                "outfeed_b": (outfeed_b_pe, FaultCode.JAM_OUTFEED_B),
                "outfeed_c": (outfeed_c_pe, FaultCode.JAM_OUTFEED_C),
            }
            for loc, (pe_val, fc) in pe_map.items():
                if pe_val and self.state == SystemState.RUNNING:
                    self._jam_timers[loc] += dt
                else:
                    self._jam_timers[loc] = 0.0

                if self._jam_timers[loc] >= jam_timeout and not self._jam_latched:
                    self._jam_latched = True
                    self._jam_location = loc
                    self.fault_code = fc
                    logger.info(f"PLC: {FAULT_MESSAGES[fc]}")
        else:
            for k in self._jam_timers:
                self._jam_timers[k] = 0.0

        # Jam clear
        if self._jam_latched and clear_rising:
            pe_clear = {
                "infeed": not infeed_pe,
                "diverter": not diverter_pe,
                "outfeed_b": not outfeed_b_pe,
                "outfeed_c": not outfeed_c_pe,
            }
            if pe_clear.get(self._jam_location, False):
                self._jam_latched = False
                self._jam_location = ""
                if not self.estop_latched:
                    self.fault_code = FaultCode.NONE

        fault_active = self.estop_latched or self._jam_latched

        # ==============================================================
        # 3. STATE MACHINE
        # ==============================================================
        motor_cmd = False
        diverter_out = False
        alarm = False
        green = False
        red = False

        if self.state == SystemState.STOPPED:
            if start_cmd:
                self.state = SystemState.STARTING
                self._start_timer = 0.0
                logger.info("PLC: STOPPED -> STARTING")

        elif self.state == SystemState.STARTING:
            green = self._blink_on
            self._start_timer += dt
            if fault_active:
                self.state = SystemState.FAULT
                logger.info("PLC: STARTING -> FAULT")
            elif self._start_timer >= self._start_delay and safe_to_run:
                self.state = SystemState.RUNNING
                logger.info("PLC: STARTING -> RUNNING")

        elif self.state == SystemState.RUNNING:
            green = True
            if not mode_manual:
                motor_cmd = True
            else:
                motor_cmd = jog_fwd and safe_to_run

            if fault_active:
                self.state = SystemState.FAULT
                motor_cmd = False
                logger.info("PLC: RUNNING -> FAULT")
            elif stop_falling or tags.get("bHMI_Stop", False):
                self.state = SystemState.STOPPED
                motor_cmd = False
                logger.info("PLC: RUNNING -> STOPPED")

        elif self.state == SystemState.FAULT:
            red = self._blink_on
            alarm = True
            if not fault_active:
                self.state = SystemState.STOPPED
                logger.info("PLC: FAULT -> STOPPED")

        # ==============================================================
        # 4. DIVERTER (auto mode, running only)
        # ==============================================================
        infeed_rising   = infeed_pe and not self._prev_infeed_pe
        diverter_rising = diverter_pe and not self._prev_diverter_pe
        diverter_falling = not diverter_pe and self._prev_diverter_pe

        if self.state == SystemState.RUNNING and not mode_manual:
            if infeed_rising:
                self._box_counter += 1
                self._reject_next = (self._box_counter % 3 == 0)

            if diverter_rising:
                self._diverter_locked = True
                diverter_out = self._reject_next

            if self._diverter_locked:
                diverter_out = self._reject_next

            if diverter_falling and self._diverter_locked:
                self._diverter_locked = False
                self._reject_next = False
                diverter_out = False

        # ==============================================================
        # 5. METRICS
        # ==============================================================
        outfeed_b_rising = outfeed_b_pe and not self._prev_outfeed_b
        outfeed_c_rising = outfeed_c_pe and not self._prev_outfeed_c
        infeed_rising_m  = infeed_pe and not self._prev_infeed_metrics
        jam_rising       = self._jam_latched and not self._prev_jam_event

        if infeed_rising_m and not self._cycle_active:
            self._cycle_active = True
            self._cycle_timer = 0.0

        if self._cycle_active:
            self._cycle_timer += dt

        if self._cycle_active and (outfeed_b_rising or outfeed_c_rising):
            self._last_cycle_time = self._cycle_timer
            self._metrics_box_count += 1
            self._cycle_time_sum += self._cycle_timer
            self._cycle_active = False
            self._cycle_timer = 0.0

        if jam_rising:
            self._metrics_jam_count += 1

        if self.state == SystemState.RUNNING:
            self._running_time += dt
        if self.state == SystemState.FAULT:
            self._fault_time += dt

        avg_cycle = (self._cycle_time_sum / self._metrics_box_count
                     if self._metrics_box_count > 0 else 0.0)
        throughput = (self._metrics_box_count / (self._running_time / 3600.0)
                      if self._running_time > 1.0 else 0.0)

        # ==============================================================
        # 6. SAFETY-GATED MOTOR OUTPUT
        # ==============================================================
        motor_output = motor_cmd and estop and not self.estop_latched and stop_pb

        # ==============================================================
        # 7. WRITE OUTPUTS
        # ==============================================================
        tags["bConveyorMotor"]    = motor_output
        tags["bDiverterActuator"] = diverter_out
        tags["bAlarmBuzzer"]      = alarm
        tags["bStatusGreen"]      = green
        tags["bStatusRed"]        = red

        tags["iHMI_State"]        = int(self.state)
        tags["sHMI_FaultMsg"]     = FAULT_MESSAGES.get(self.fault_code, "")
        tags["rHMI_BoxCount"]     = self._metrics_box_count
        tags["rHMI_AvgCycleTime"] = round(avg_cycle, 2)
        tags["rHMI_JamCount"]     = self._metrics_jam_count
        tags["rHMI_Throughput"]   = round(throughput, 1)

        # ---- save previous states ----
        self._prev_start = start_pb
        self._prev_stop = stop_pb
        self._prev_estop = estop
        self._prev_fault_clear = fault_clear
        self._prev_infeed_pe = infeed_pe
        self._prev_diverter_pe = diverter_pe
        self._prev_outfeed_b = outfeed_b_pe
        self._prev_outfeed_c = outfeed_c_pe
        self._prev_infeed_metrics = infeed_pe
        self._prev_jam_event = self._jam_latched

        # ---- consume one-shot HMI commands ----
        tags["bHMI_Start"]      = False
        tags["bHMI_Stop"]       = False
        tags["bHMI_FaultClear"] = False
