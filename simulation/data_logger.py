"""
Data Logger for Mini-Fulfillment Conveyor Simulator

Logs operational metrics and events to CSV files for later analysis.
Produces two output files per run:
  - metrics_YYYYMMDD_HHMMSS.csv: periodic metrics snapshots
  - events_YYYYMMDD_HHMMSS.csv: individual box events (arrival, exit, jam)
"""

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class DataLogger:
    """
    Logs simulation metrics and events to CSV files.
    """

    def __init__(self, output_dir: str = "../data",
                 log_interval_sec: float = 1.0,
                 log_events: bool = True):
        self.output_dir = Path(output_dir)
        self.log_interval_sec = log_interval_sec
        self.log_events = log_events
        
        # File handles
        self._metrics_file = None
        self._metrics_writer = None
        self._events_file = None
        self._events_writer = None
        
        # Timing
        self._last_log_time: float = 0.0
        
        # Timestamp for file naming
        self._run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def initialize(self):
        """Create output directory and open CSV files."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Metrics CSV
        metrics_path = self.output_dir / f"metrics_{self._run_timestamp}.csv"
        self._metrics_file = open(metrics_path, "w", newline="")
        self._metrics_writer = csv.writer(self._metrics_file)
        self._metrics_writer.writerow([
            "sim_time_sec",
            "system_state",
            "box_count",
            "avg_cycle_time_sec",
            "jam_count",
            "throughput_per_hour",
            "fault_message",
        ])
        logger.info(f"Metrics logging to: {metrics_path}")
        
        # Events CSV
        if self.log_events:
            events_path = self.output_dir / f"events_{self._run_timestamp}.csv"
            self._events_file = open(events_path, "w", newline="")
            self._events_writer = csv.writer(self._events_file)
            self._events_writer.writerow([
                "sim_time_sec",
                "event_type",
                "box_id",
                "description",
            ])
            logger.info(f"Events logging to: {events_path}")

    def log_metrics(self, sim_time: float, metrics: dict[str, Any]):
        """
        Log a metrics snapshot (rate-limited by log_interval_sec).
        
        Args:
            sim_time: Current simulation time in seconds
            metrics: Dictionary of metric values from PLC
        """
        if sim_time - self._last_log_time < self.log_interval_sec:
            return
        
        self._last_log_time = sim_time
        
        if self._metrics_writer:
            self._metrics_writer.writerow([
                f"{sim_time:.2f}",
                metrics.get("iHMI_State", 0),
                metrics.get("rHMI_BoxCount", 0),
                f"{metrics.get('rHMI_AvgCycleTime', 0.0):.2f}",
                metrics.get("rHMI_JamCount", 0),
                f"{metrics.get('rHMI_Throughput', 0.0):.1f}",
                metrics.get("sHMI_FaultMsg", ""),
            ])
            self._metrics_file.flush()

    def log_event(self, sim_time: float, event_type: str,
                  box_id: int, description: str):
        """
        Log an individual event.
        
        Args:
            sim_time: Current simulation time
            event_type: Event type (BOX_ARRIVAL, BOX_EXIT_B, BOX_EXIT_C, JAM, etc.)
            box_id: ID of the box involved
            description: Human-readable description
        """
        if not self.log_events or not self._events_writer:
            return
        
        self._events_writer.writerow([
            f"{sim_time:.2f}",
            event_type,
            box_id,
            description,
        ])
        self._events_file.flush()
        
        logger.debug(f"Event: {event_type} - {description}")

    def finalize(self, completed_boxes=None):
        """
        Close files and write summary.
        
        Args:
            completed_boxes: Optional list of completed Box objects for summary
        """
        # Write summary event
        if completed_boxes and self._events_writer:
            total = len(completed_boxes)
            accept = sum(1 for b in completed_boxes if not b.is_reject)
            reject = sum(1 for b in completed_boxes if b.is_reject)
            self.log_event(
                0.0, "SUMMARY", 0,
                f"Total processed: {total}, Accept: {accept}, Reject: {reject}"
            )
        
        # Close files
        if self._metrics_file:
            self._metrics_file.close()
            self._metrics_file = None
            logger.info("Metrics CSV closed")
        
        if self._events_file:
            self._events_file.close()
            self._events_file = None
            logger.info("Events CSV closed")
