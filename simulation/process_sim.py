"""
Process Simulator for Mini-Fulfillment Conveyor System

Simulates the physical conveyor process:
- Generates boxes at a configurable arrival rate
- Models box movement along the conveyor based on motor state and speed
- Triggers photoeye inputs as boxes pass sensor positions
- Can inject jam conditions (box stuck at a photoeye)
- Reads PLC outputs (motor, diverter) to determine box routing
- Coordinates data logging and visualization

Usage:
    python process_sim.py [--config config.yaml] [--no-viz] [--output-dir ../data/baseline]
"""

import argparse
import logging
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

import yaml

from opc_client import OPCUAClient
from data_logger import DataLogger

logger = logging.getLogger(__name__)


class BoxState(Enum):
    """Box lifecycle states."""
    QUEUED = "queued"           # Waiting to enter conveyor
    ON_CONVEYOR = "on_conveyor"  # Moving along conveyor
    AT_INFEED = "at_infeed"     # At infeed photoeye
    AT_DIVERTER = "at_diverter" # At diverter photoeye
    AT_OUTFEED_B = "at_outfeed_b"  # At outfeed B photoeye
    AT_OUTFEED_C = "at_outfeed_c"  # At outfeed C photoeye
    COMPLETED = "completed"     # Exited the system
    JAMMED = "jammed"           # Stuck (jam condition)


@dataclass
class Box:
    """Represents a box on the conveyor."""
    box_id: int
    position_mm: float = 0.0       # Position along conveyor (0 = infeed)
    state: BoxState = BoxState.QUEUED
    arrival_time: float = 0.0      # Simulation time when box arrived
    exit_time: float = 0.0         # Simulation time when box exited
    is_reject: bool = False        # Determined by PLC diverter output
    is_jammed: bool = False        # Box is causing a jam
    routed: bool = False           # Routing decision has been read


@dataclass
class ConveyorConfig:
    """Conveyor physical dimensions."""
    total_length_mm: float = 3000.0
    infeed_pe_pos: float = 0.0          # Infeed PE at start
    diverter_pe_pos: float = 1500.0     # Diverter PE at midpoint
    outfeed_b_pos: float = 2500.0       # Outfeed B near end
    outfeed_c_pos: float = 2500.0       # Outfeed C on branch
    belt_speed_mms: float = 500.0       # mm/s at full speed
    box_length_mm: float = 200.0


class ProcessSimulator:
    """
    Simulates the physical conveyor process.
    
    Generates boxes, moves them along the conveyor, triggers photoeyes,
    and responds to PLC outputs (motor on/off, diverter position).
    """

    def __init__(self, config_path: str = "config.yaml",
                 output_dir: Optional[str] = None,
                 enable_viz: bool = True):
        self.config = self._load_config(config_path)
        self.conveyor = self._build_conveyor_config()
        
        # Simulation state
        self.boxes: list[Box] = []
        self.active_boxes: list[Box] = []
        self.completed_boxes: list[Box] = []
        self.sim_time: float = 0.0
        self.next_box_id: int = 1
        self.next_arrival_time: float = 0.0
        self.running: bool = False
        
        # PLC interface
        opcua_cfg = self.config.get("opcua", {})
        self.plc = OPCUAClient(
            server_url=opcua_cfg.get("server_url", "opc.tcp://localhost:4840"),
            namespace=opcua_cfg.get("namespace", "http://codesys.com/UA"),
            timeout_ms=opcua_cfg.get("timeout_ms", 5000),
        )
        
        # Data logger
        log_cfg = self.config.get("logging", {})
        self.output_dir = output_dir or log_cfg.get("output_dir", "../data")
        self.data_logger = DataLogger(
            output_dir=self.output_dir,
            log_interval_sec=log_cfg.get("log_interval_sec", 1.0),
            log_events=log_cfg.get("log_events", True),
        )
        
        # Visualization
        self.enable_viz = enable_viz and self.config.get("visualization", {}).get("enabled", True)
        self.visualizer = None

        # Schedule first box
        self._schedule_next_arrival()

    def _load_config(self, path: str) -> dict:
        """Load configuration from YAML file."""
        config_path = Path(path)
        if config_path.exists():
            with open(config_path) as f:
                return yaml.safe_load(f)
        logger.warning(f"Config file {path} not found, using defaults")
        return {}

    def _build_conveyor_config(self) -> ConveyorConfig:
        """Build conveyor configuration from loaded config."""
        conv = self.config.get("conveyor", {})
        return ConveyorConfig(
            total_length_mm=conv.get("total_length_mm", 3000),
            infeed_pe_pos=0.0,
            diverter_pe_pos=conv.get("infeed_to_diverter_mm", 1500),
            outfeed_b_pos=conv.get("infeed_to_diverter_mm", 1500) + conv.get("diverter_to_outfeed_mm", 1000),
            outfeed_c_pos=conv.get("infeed_to_diverter_mm", 1500) + conv.get("diverter_to_outfeed_mm", 1000),
            belt_speed_mms=conv.get("belt_speed_mms", 500),
            box_length_mm=conv.get("box_length_mm", 200),
        )

    def _schedule_next_arrival(self):
        """Schedule the next box arrival time."""
        box_cfg = self.config.get("boxes", {})
        rate = box_cfg.get("arrival_rate_per_hour", 72)
        jitter_pct = box_cfg.get("arrival_jitter_pct", 20)
        
        if rate <= 0:
            self.next_arrival_time = float("inf")
            return
        
        interval_sec = 3600.0 / rate
        jitter = interval_sec * (jitter_pct / 100.0)
        actual_interval = interval_sec + random.uniform(-jitter, jitter)
        actual_interval = max(actual_interval, 1.0)  # Minimum 1 second
        
        self.next_arrival_time = self.sim_time + actual_interval

    def _should_inject_jam(self) -> bool:
        """Determine if a jam should be injected for the current box."""
        jam_cfg = self.config.get("jams", {})
        if not jam_cfg.get("enabled", True):
            return False
        prob = jam_cfg.get("probability_per_box", 0.03)
        return random.random() < prob

    def _get_jam_location(self) -> str:
        """Get the location where a jam should occur."""
        jam_cfg = self.config.get("jams", {})
        location = jam_cfg.get("jam_location", "random")
        if location == "random":
            return random.choice(["infeed", "diverter", "outfeed_b", "outfeed_c"])
        return location

    def initialize(self):
        """Initialize PLC connection and subsystems."""
        logger.info("Initializing process simulator...")
        
        # Connect to PLC
        self.plc.connect()
        
        # Set initial input states (safe defaults)
        self.plc.write("bEStop", True)       # E-Stop healthy
        self.plc.write("bStopPB", True)      # Stop PB not pressed
        self.plc.write("bStartPB", False)    # Start PB not pressed
        self.plc.write("bModeSelector", False)  # Auto mode
        self.plc.write("bInfeedPE", False)   # All PEs clear
        self.plc.write("bDiverterPE", False)
        self.plc.write("bOutfeedBPE", False)
        self.plc.write("bOutfeedCPE", False)
        
        # Initialize data logger
        self.data_logger.initialize()
        
        # Initialize visualizer
        if self.enable_viz:
            try:
                from visualizer import ConveyorVisualizer
                viz_cfg = self.config.get("visualization", {})
                self.visualizer = ConveyorVisualizer(
                    width=viz_cfg.get("window_width", 1000),
                    height=viz_cfg.get("window_height", 500),
                    conveyor_config=self.conveyor,
                )
                self.visualizer.initialize()
            except ImportError:
                logger.warning("Visualizer not available, continuing without it")
                self.enable_viz = False

        logger.info("Simulator initialized. Mode: " + 
                    ("OPC-UA" if not self.plc.simulation_mode else "Local Simulation"))

    def start_system(self):
        """Send start command to PLC."""
        logger.info("Sending START command to PLC")
        self.plc.write("bHMI_Start", True)
        time.sleep(0.1)
        self.plc.write("bHMI_Start", False)

    def stop_system(self):
        """Send stop command to PLC."""
        logger.info("Sending STOP command to PLC")
        self.plc.write("bHMI_Stop", True)
        time.sleep(0.1)
        self.plc.write("bHMI_Stop", False)

    def clear_fault(self):
        """Send fault clear command to PLC."""
        logger.info("Sending FAULT CLEAR command to PLC")
        self.plc.write("bHMI_FaultClear", True)
        time.sleep(0.1)
        self.plc.write("bHMI_FaultClear", False)

    def update(self, dt: float):
        """
        Main simulation update loop.
        
        Args:
            dt: Time step in seconds
        """
        self.sim_time += dt
        
        # Read PLC outputs
        motor_on = self.plc.read("bConveyorMotor")
        diverter_extended = self.plc.read("bDiverterActuator")
        speed_setpoint = self.plc.read("rConveyorSpeed") or 1.0
        
        # Generate new boxes
        if self.sim_time >= self.next_arrival_time:
            self._generate_box()
            self._schedule_next_arrival()
        
        # Move boxes along conveyor
        if motor_on:
            speed = self.conveyor.belt_speed_mms * speed_setpoint
            self._move_boxes(dt, speed, diverter_extended)
        
        # Update photoeye states
        self._update_photoeyes()
        
        # Log data
        metrics = self.plc.read_metrics() if not self.plc.simulation_mode else {
            "iHMI_State": self.plc.read("iHMI_State"),
            "rHMI_BoxCount": len(self.completed_boxes),
            "rHMI_AvgCycleTime": self._calc_avg_cycle_time(),
            "rHMI_JamCount": sum(1 for b in self.boxes if b.is_jammed),
            "rHMI_Throughput": self._calc_throughput(),
        }
        self.data_logger.log_metrics(self.sim_time, metrics)
        
        # Update visualization
        if self.enable_viz and self.visualizer:
            plc_state = {
                "motor_on": motor_on,
                "diverter_extended": diverter_extended,
                "alarm": self.plc.read("bAlarmBuzzer"),
                "green_light": self.plc.read("bStatusGreen"),
                "red_light": self.plc.read("bStatusRed"),
                "state": self.plc.read("iHMI_State"),
                "fault_msg": self.plc.read("sHMI_FaultMsg"),
            }
            photoeyes = {
                "infeed": self.plc.read("bInfeedPE"),
                "diverter": self.plc.read("bDiverterPE"),
                "outfeed_b": self.plc.read("bOutfeedBPE"),
                "outfeed_c": self.plc.read("bOutfeedCPE"),
            }
            self.visualizer.update(
                boxes=self.active_boxes,
                plc_state=plc_state,
                photoeyes=photoeyes,
                sim_time=self.sim_time,
                metrics=metrics,
            )

    def _generate_box(self):
        """Create a new box and add it to the conveyor."""
        box = Box(
            box_id=self.next_box_id,
            position_mm=0.0,
            state=BoxState.AT_INFEED,
            arrival_time=self.sim_time,
            is_jammed=self._should_inject_jam(),
        )
        self.next_box_id += 1
        self.active_boxes.append(box)
        self.boxes.append(box)
        
        # Log event
        self.data_logger.log_event(self.sim_time, "BOX_ARRIVAL", box.box_id,
                                   f"Box {box.box_id} arrived at infeed" +
                                   (" [WILL JAM]" if box.is_jammed else ""))
        
        logger.debug(f"Box {box.box_id} generated at infeed" +
                     (" (will jam)" if box.is_jammed else ""))

    def _move_boxes(self, dt: float, speed_mms: float, diverter_extended: bool):
        """Move all active boxes along the conveyor."""
        distance = speed_mms * dt
        
        for box in self.active_boxes[:]:  # Copy list since we may modify it
            if box.state == BoxState.JAMMED:
                continue  # Jammed boxes don't move
            
            # Check if box should jam at its current location
            if box.is_jammed and not box.state == BoxState.JAMMED:
                jam_loc = self._get_jam_location()
                jam_pos = {
                    "infeed": self.conveyor.infeed_pe_pos,
                    "diverter": self.conveyor.diverter_pe_pos,
                    "outfeed_b": self.conveyor.outfeed_b_pos,
                    "outfeed_c": self.conveyor.outfeed_c_pos,
                }.get(jam_loc, self.conveyor.infeed_pe_pos)
                
                if box.position_mm >= jam_pos:
                    box.state = BoxState.JAMMED
                    self.data_logger.log_event(
                        self.sim_time, "JAM", box.box_id,
                        f"Box {box.box_id} jammed at {jam_loc}"
                    )
                    logger.info(f"JAM: Box {box.box_id} stuck at {jam_loc}")
                    continue
            
            # Move box
            box.position_mm += distance
            
            # Update state based on position
            if box.position_mm >= self.conveyor.outfeed_b_pos and not box.is_reject:
                box.state = BoxState.AT_OUTFEED_B
                if box.position_mm >= self.conveyor.outfeed_b_pos + self.conveyor.box_length_mm:
                    box.state = BoxState.COMPLETED
                    box.exit_time = self.sim_time
                    self.active_boxes.remove(box)
                    self.completed_boxes.append(box)
                    self.data_logger.log_event(
                        self.sim_time, "BOX_EXIT_B", box.box_id,
                        f"Box {box.box_id} exited at Station B (accept), "
                        f"cycle={box.exit_time - box.arrival_time:.1f}s"
                    )
            elif box.position_mm >= self.conveyor.outfeed_c_pos and box.is_reject:
                box.state = BoxState.AT_OUTFEED_C
                if box.position_mm >= self.conveyor.outfeed_c_pos + self.conveyor.box_length_mm:
                    box.state = BoxState.COMPLETED
                    box.exit_time = self.sim_time
                    self.active_boxes.remove(box)
                    self.completed_boxes.append(box)
                    self.data_logger.log_event(
                        self.sim_time, "BOX_EXIT_C", box.box_id,
                        f"Box {box.box_id} exited at Station C (reject), "
                        f"cycle={box.exit_time - box.arrival_time:.1f}s"
                    )
            elif box.position_mm >= self.conveyor.diverter_pe_pos:
                box.state = BoxState.AT_DIVERTER
                # Read diverter state to determine routing
                if not box.routed:
                    box.is_reject = diverter_extended
                    box.routed = True
            elif box.position_mm >= self.conveyor.infeed_pe_pos:
                box.state = BoxState.AT_INFEED

    def _update_photoeyes(self):
        """Update photoeye states based on box positions."""
        # Check if any box is at each photoeye position
        infeed_blocked = False
        diverter_blocked = False
        outfeed_b_blocked = False
        outfeed_c_blocked = False
        
        for box in self.active_boxes:
            pos = box.position_mm
            half_box = self.conveyor.box_length_mm / 2
            
            # Infeed PE
            if abs(pos - self.conveyor.infeed_pe_pos) < half_box:
                infeed_blocked = True
            
            # Diverter PE
            if abs(pos - self.conveyor.diverter_pe_pos) < half_box:
                diverter_blocked = True
            
            # Outfeed B PE (only for accept boxes)
            if not box.is_reject and abs(pos - self.conveyor.outfeed_b_pos) < half_box:
                outfeed_b_blocked = True
            
            # Outfeed C PE (only for reject boxes)
            if box.is_reject and abs(pos - self.conveyor.outfeed_c_pos) < half_box:
                outfeed_c_blocked = True
        
        # Write photoeye states to PLC
        self.plc.write("bInfeedPE", infeed_blocked)
        self.plc.write("bDiverterPE", diverter_blocked)
        self.plc.write("bOutfeedBPE", outfeed_b_blocked)
        self.plc.write("bOutfeedCPE", outfeed_c_blocked)

    def _calc_avg_cycle_time(self) -> float:
        """Calculate average cycle time from completed boxes."""
        if not self.completed_boxes:
            return 0.0
        total = sum(b.exit_time - b.arrival_time for b in self.completed_boxes)
        return total / len(self.completed_boxes)

    def _calc_throughput(self) -> float:
        """Calculate current throughput in boxes/hour."""
        if self.sim_time <= 0:
            return 0.0
        return len(self.completed_boxes) / (self.sim_time / 3600.0)

    def run(self, duration_sec: Optional[float] = None):
        """
        Run the simulation for the specified duration.
        
        Args:
            duration_sec: How long to run (None = use config value)
        """
        sim_cfg = self.config.get("simulation", {})
        duration = duration_sec or sim_cfg.get("duration_sec", 900)
        time_scale = sim_cfg.get("time_scale", 1.0)
        update_interval = sim_cfg.get("update_interval_ms", 50) / 1000.0
        
        logger.info(f"Starting simulation for {duration}s (time scale: {time_scale}x)")
        self.running = True
        
        # Auto-start the system after a brief delay
        self.start_system()
        
        start_real_time = time.time()
        last_update = start_real_time
        
        try:
            while self.running and self.sim_time < duration:
                current_time = time.time()
                real_dt = current_time - last_update
                sim_dt = real_dt * time_scale
                
                self.update(sim_dt)
                
                last_update = current_time
                
                # Pace the simulation
                elapsed = time.time() - current_time
                sleep_time = max(0, update_interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
                # Handle visualizer events (window close, etc.)
                if self.enable_viz and self.visualizer:
                    if not self.visualizer.process_events():
                        logger.info("Visualizer closed, stopping simulation")
                        self.running = False

        except KeyboardInterrupt:
            logger.info("Simulation interrupted by user")
        finally:
            self.running = False
            self._finalize()

    def _finalize(self):
        """Clean up after simulation run."""
        logger.info(f"Simulation complete. Time: {self.sim_time:.1f}s")
        logger.info(f"  Boxes processed: {len(self.completed_boxes)}")
        logger.info(f"  Avg cycle time: {self._calc_avg_cycle_time():.1f}s")
        logger.info(f"  Throughput: {self._calc_throughput():.1f} boxes/hr")
        logger.info(f"  Jams: {sum(1 for b in self.boxes if b.is_jammed)}")
        
        # Stop system
        self.stop_system()
        
        # Finalize logging
        self.data_logger.finalize(self.completed_boxes)
        
        # Disconnect
        self.plc.disconnect()
        
        # Close visualizer
        if self.enable_viz and self.visualizer:
            self.visualizer.close()


def main():
    """Entry point for the process simulator."""
    parser = argparse.ArgumentParser(
        description="Mini-Fulfillment Conveyor Process Simulator"
    )
    parser.add_argument("--config", default="config.yaml",
                       help="Path to configuration YAML file")
    parser.add_argument("--no-viz", action="store_true",
                       help="Disable real-time visualization")
    parser.add_argument("--output-dir",
                       help="Override output directory for logged data")
    parser.add_argument("--duration", type=float,
                       help="Override simulation duration in seconds")
    parser.add_argument("--time-scale", type=float,
                       help="Override time scale (e.g., 10.0 for 10x speed)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    
    # Override config if CLI args provided
    sim = ProcessSimulator(
        config_path=args.config,
        output_dir=args.output_dir,
        enable_viz=not args.no_viz,
    )
    
    if args.time_scale:
        sim.config.setdefault("simulation", {})["time_scale"] = args.time_scale
    
    # Run
    sim.initialize()
    sim.run(duration_sec=args.duration)


if __name__ == "__main__":
    main()
