"""
Real-Time Conveyor Visualizer
Mini-Fulfillment Conveyor System

Provides a simple Tkinter-based visualization of the conveyor state:
- Conveyor belt with moving boxes
- Photoeye status indicators
- Diverter gate position
- Status lights and metrics display
"""

import logging
import tkinter as tk
from typing import Any, Optional

logger = logging.getLogger(__name__)

# State name mapping
STATE_NAMES = {0: "STOPPED", 1: "STARTING", 2: "RUNNING", 3: "FAULT"}
STATE_COLORS = {0: "#808080", 1: "#FFD700", 2: "#00CC00", 3: "#FF0000"}


class ConveyorVisualizer:
    """
    Tkinter-based real-time visualization of the conveyor system.
    """

    def __init__(self, width: int = 1000, height: int = 500,
                 conveyor_config=None):
        self.width = width
        self.height = height
        self.conv_cfg = conveyor_config
        self.root: Optional[tk.Tk] = None
        self.canvas: Optional[tk.Canvas] = None
        self._closed = False
        
        # Layout constants
        self.MARGIN = 40
        self.CONVEYOR_Y = 200
        self.CONVEYOR_HEIGHT = 60
        self.PE_RADIUS = 12
        self.BOX_SIZE = 30
        self.BRANCH_Y = 350
        
        # Scale: convert mm to pixels
        total_mm = conveyor_config.total_length_mm if conveyor_config else 3000
        self.scale = (width - 2 * self.MARGIN) / total_mm

    def initialize(self):
        """Create the Tkinter window and canvas."""
        try:
            self.root = tk.Tk()
            self.root.title("Mini-Fulfillment Conveyor Simulator")
            self.root.geometry(f"{self.width}x{self.height}")
            self.root.protocol("WM_DELETE_WINDOW", self._on_close)
            
            self.canvas = tk.Canvas(
                self.root,
                width=self.width,
                height=self.height,
                bg="#1a1a2e",
            )
            self.canvas.pack(fill=tk.BOTH, expand=True)
            
            logger.info("Visualizer window created")
        except tk.TclError as e:
            logger.warning(f"Could not create visualizer window: {e}")
            self._closed = True

    def _on_close(self):
        """Handle window close."""
        self._closed = True
        if self.root:
            self.root.destroy()

    def _mm_to_px(self, mm: float) -> float:
        """Convert millimeters to pixel position."""
        return self.MARGIN + mm * self.scale

    def update(self, boxes: list, plc_state: dict[str, Any],
               photoeyes: dict[str, bool], sim_time: float,
               metrics: dict[str, Any]):
        """
        Redraw the visualization with current state.
        
        Args:
            boxes: List of active Box objects
            plc_state: PLC output states
            photoeyes: Photoeye blocked states
            sim_time: Current simulation time
            metrics: Current metrics
        """
        if self._closed or not self.canvas:
            return
        
        self.canvas.delete("all")
        
        # Draw conveyor belt
        self._draw_conveyor()
        
        # Draw branch to Station C
        self._draw_reject_branch()
        
        # Draw photoeyes
        self._draw_photoeyes(photoeyes)
        
        # Draw diverter gate
        self._draw_diverter(plc_state.get("diverter_extended", False))
        
        # Draw boxes
        self._draw_boxes(boxes)
        
        # Draw station labels
        self._draw_stations()
        
        # Draw status panel
        self._draw_status(plc_state, sim_time, metrics)
        
        # Update display
        try:
            self.root.update_idletasks()
        except tk.TclError:
            self._closed = True

    def _draw_conveyor(self):
        """Draw the main conveyor belt."""
        x1 = self.MARGIN
        x2 = self.width - self.MARGIN
        y1 = self.CONVEYOR_Y - self.CONVEYOR_HEIGHT // 2
        y2 = self.CONVEYOR_Y + self.CONVEYOR_HEIGHT // 2
        
        # Belt background
        self.canvas.create_rectangle(x1, y1, x2, y2,
                                     fill="#333333", outline="#555555", width=2)
        
        # Rollers (decorative)
        roller_spacing = 40
        for x in range(int(x1) + 20, int(x2), roller_spacing):
            self.canvas.create_line(x, y1, x, y2, fill="#444444", width=1)

    def _draw_reject_branch(self):
        """Draw the reject path branch."""
        if not self.conv_cfg:
            return
        
        # Branch point at diverter
        div_x = self._mm_to_px(self.conv_cfg.diverter_pe_pos)
        branch_x2 = div_x + 150
        y_top = self.CONVEYOR_Y + self.CONVEYOR_HEIGHT // 2
        y_bottom = self.BRANCH_Y
        
        # Angled branch
        self.canvas.create_polygon(
            div_x, y_top,
            div_x + 30, y_top,
            branch_x2 + 30, y_bottom - 30,
            branch_x2, y_bottom - 30,
            fill="#333333", outline="#555555", width=2
        )
        
        # Station C bin
        self.canvas.create_rectangle(
            branch_x2 - 20, y_bottom - 30,
            branch_x2 + 50, y_bottom + 10,
            fill="#8B0000", outline="#FF4444", width=2
        )
        self.canvas.create_text(
            branch_x2 + 15, y_bottom - 10,
            text="Station C\n(Reject)", fill="white", font=("Arial", 8),
            anchor="center"
        )

    def _draw_photoeyes(self, photoeyes: dict[str, bool]):
        """Draw photoeye indicators."""
        if not self.conv_cfg:
            return
        
        pe_positions = {
            "infeed": self.conv_cfg.infeed_pe_pos,
            "diverter": self.conv_cfg.diverter_pe_pos,
            "outfeed_b": self.conv_cfg.outfeed_b_pos,
            "outfeed_c": self.conv_cfg.outfeed_c_pos,
        }
        
        pe_labels = {
            "infeed": "PE1",
            "diverter": "PE2",
            "outfeed_b": "PE3",
            "outfeed_c": "PE4",
        }
        
        for name, pos_mm in pe_positions.items():
            x = self._mm_to_px(pos_mm)
            y = self.CONVEYOR_Y - self.CONVEYOR_HEIGHT // 2 - 20
            
            blocked = photoeyes.get(name, False)
            color = "#FF4444" if blocked else "#44FF44"
            outline = "#FF0000" if blocked else "#00CC00"
            
            # PE indicator circle
            self.canvas.create_oval(
                x - self.PE_RADIUS, y - self.PE_RADIUS,
                x + self.PE_RADIUS, y + self.PE_RADIUS,
                fill=color, outline=outline, width=2
            )
            
            # Label
            self.canvas.create_text(
                x, y - self.PE_RADIUS - 10,
                text=pe_labels[name], fill="white", font=("Arial", 9, "bold")
            )

    def _draw_diverter(self, extended: bool):
        """Draw the diverter gate."""
        if not self.conv_cfg:
            return
        
        x = self._mm_to_px(self.conv_cfg.diverter_pe_pos)
        y = self.CONVEYOR_Y + self.CONVEYOR_HEIGHT // 2
        
        color = "#FF8800" if extended else "#4488FF"
        label = "DIVERT" if extended else "PASS"
        
        # Gate indicator
        gate_len = 25
        if extended:
            # Angled gate (deflecting)
            self.canvas.create_line(x, y, x + gate_len, y + gate_len,
                                   fill=color, width=4)
        else:
            # Flat gate (retracted)
            self.canvas.create_line(x, y, x, y + gate_len,
                                   fill=color, width=4)
        
        self.canvas.create_text(
            x + 30, y + 15,
            text=label, fill=color, font=("Arial", 8, "bold")
        )

    def _draw_boxes(self, boxes: list):
        """Draw boxes on the conveyor."""
        for box in boxes:
            x = self._mm_to_px(box.position_mm)
            y = self.CONVEYOR_Y
            
            # Determine color
            if box.is_jammed:
                color = "#FF0000"  # Red for jammed
            elif box.is_reject:
                color = "#FF8800"  # Orange for reject
            else:
                color = "#8B6914"  # Brown for normal
            
            # Draw box
            half = self.BOX_SIZE // 2
            self.canvas.create_rectangle(
                x - half, y - half,
                x + half, y + half,
                fill=color, outline="#FFFFFF", width=1
            )
            
            # Box ID label
            self.canvas.create_text(
                x, y, text=str(box.box_id),
                fill="white", font=("Arial", 8, "bold")
            )

    def _draw_stations(self):
        """Draw station labels."""
        if not self.conv_cfg:
            return
        
        # Station A (Infeed)
        x = self.MARGIN
        self.canvas.create_text(
            x + 30, self.CONVEYOR_Y + self.CONVEYOR_HEIGHT // 2 + 25,
            text="Station A\n(Infeed)", fill="#AAAAAA", font=("Arial", 9),
            anchor="center"
        )
        
        # Station B (Accept)
        x = self.width - self.MARGIN
        self.canvas.create_rectangle(
            x - 50, self.CONVEYOR_Y - 25,
            x, self.CONVEYOR_Y + 25,
            fill="#006600", outline="#44FF44", width=2
        )
        self.canvas.create_text(
            x - 25, self.CONVEYOR_Y,
            text="Station B\n(Accept)", fill="white", font=("Arial", 8),
            anchor="center"
        )

    def _draw_status(self, plc_state: dict, sim_time: float,
                     metrics: dict):
        """Draw the status panel at the bottom."""
        y_base = self.height - 120
        
        # Background
        self.canvas.create_rectangle(
            0, y_base, self.width, self.height,
            fill="#0f0f23", outline="#333333"
        )
        
        # System state
        state_num = plc_state.get("state", 0)
        state_name = STATE_NAMES.get(state_num, "UNKNOWN")
        state_color = STATE_COLORS.get(state_num, "#808080")
        
        self.canvas.create_text(
            20, y_base + 15,
            text=f"State: {state_name}", fill=state_color,
            font=("Arial", 12, "bold"), anchor="w"
        )
        
        # Fault message
        fault_msg = plc_state.get("fault_msg", "")
        if fault_msg:
            self.canvas.create_text(
                20, y_base + 35,
                text=f"FAULT: {fault_msg}", fill="#FF4444",
                font=("Arial", 10, "bold"), anchor="w"
            )
        
        # Simulation time
        mins = int(sim_time) // 60
        secs = int(sim_time) % 60
        self.canvas.create_text(
            self.width - 20, y_base + 15,
            text=f"Time: {mins:02d}:{secs:02d}", fill="#AAAAAA",
            font=("Arial", 11), anchor="e"
        )
        
        # Metrics
        metrics_y = y_base + 55
        metrics_items = [
            ("Boxes", metrics.get("rHMI_BoxCount", 0)),
            ("Cycle", f"{metrics.get('rHMI_AvgCycleTime', 0.0):.1f}s"),
            ("Throughput", f"{metrics.get('rHMI_Throughput', 0.0):.0f}/hr"),
            ("Jams", metrics.get("rHMI_JamCount", 0)),
        ]
        
        spacing = self.width // (len(metrics_items) + 1)
        for i, (label, value) in enumerate(metrics_items):
            x = spacing * (i + 1)
            self.canvas.create_text(
                x, metrics_y, text=label, fill="#888888",
                font=("Arial", 9), anchor="center"
            )
            self.canvas.create_text(
                x, metrics_y + 20, text=str(value), fill="#FFFFFF",
                font=("Arial", 14, "bold"), anchor="center"
            )
        
        # Status lights
        light_y = y_base + 15
        light_x = self.width // 2
        
        # Green light
        green_on = plc_state.get("green_light", False)
        self.canvas.create_oval(
            light_x - 10, light_y - 10,
            light_x + 10, light_y + 10,
            fill="#00FF00" if green_on else "#004400",
            outline="#00FF00" if green_on else "#006600"
        )
        
        # Red light
        red_on = plc_state.get("red_light", False)
        self.canvas.create_oval(
            light_x + 20, light_y - 10,
            light_x + 40, light_y + 10,
            fill="#FF0000" if red_on else "#440000",
            outline="#FF0000" if red_on else "#660000"
        )
        
        # Motor indicator
        motor_on = plc_state.get("motor_on", False)
        motor_color = "#00CC00" if motor_on else "#666666"
        self.canvas.create_text(
            light_x + 70, light_y,
            text=f"Motor: {'ON' if motor_on else 'OFF'}",
            fill=motor_color, font=("Arial", 10, "bold"), anchor="w"
        )

    def process_events(self) -> bool:
        """
        Process Tkinter events.
        
        Returns:
            True if window is still open, False if closed
        """
        if self._closed:
            return False
        try:
            self.root.update()
            return True
        except tk.TclError:
            self._closed = True
            return False

    def close(self):
        """Close the visualizer window."""
        if not self._closed and self.root:
            try:
                self.root.destroy()
            except tk.TclError:
                pass
        self._closed = True
