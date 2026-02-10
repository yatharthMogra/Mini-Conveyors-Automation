"""
Capture a GIF of the conveyor simulator visualizer.

Runs a short simulation, grabs Tkinter canvas frames via PostScript export,
and stitches them into an animated GIF.
"""

import io
import logging
import random
import time
import sys
from pathlib import Path

# Ensure we can import siblings
sys.path.insert(0, str(Path(__file__).parent))

from PIL import Image, ImageDraw, ImageFont
from process_sim import ProcessSimulator, BoxState

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

OUTPUT = Path(__file__).parent.parent / "docs" / "images" / "visualizer_demo.gif"

# --- Configuration ---
SIM_DURATION_SEC = 120      # 120s of sim time – enough for boxes, routing, and a jam
TIME_SCALE = 3.0            # 3x speed  → smoother box movement
CAPTURE_INTERVAL = 0.15     # Capture a frame every 0.15s real time
TARGET_FPS = 8              # GIF playback speed (125ms per frame – easy on the eyes)
SEED = 42
WIDTH, HEIGHT = 1000, 500


def render_frame(sim, frame_idx):
    """Render the current simulator state to a PIL Image (no Tkinter needed)."""
    img = Image.new('RGB', (WIDTH, HEIGHT), '#1a1a2e')
    draw = ImageDraw.Draw(img)

    conv = sim.conveyor
    margin = 40
    scale = (WIDTH - 2 * margin) / conv.total_length_mm
    conv_y = 200
    conv_h = 60

    def mm_to_px(mm):
        return margin + mm * scale

    # --- Conveyor belt ---
    draw.rectangle([margin, conv_y - conv_h//2, WIDTH - margin, conv_y + conv_h//2],
                   fill='#333333', outline='#555555', width=2)
    # Rollers
    for x in range(margin + 20, WIDTH - margin, 40):
        draw.line([(x, conv_y - conv_h//2), (x, conv_y + conv_h//2)], fill='#444444')

    # --- Reject branch ---
    div_x = mm_to_px(conv.diverter_pe_pos)
    branch_x2 = div_x + 150
    branch_y = 350
    draw.polygon([
        (div_x, conv_y + conv_h//2),
        (div_x + 30, conv_y + conv_h//2),
        (branch_x2 + 30, branch_y - 30),
        (branch_x2, branch_y - 30),
    ], fill='#333333', outline='#555555')
    draw.rectangle([branch_x2 - 20, branch_y - 30, branch_x2 + 50, branch_y + 10],
                   fill='#8B0000', outline='#FF4444', width=2)
    draw.text((branch_x2 + 15, branch_y - 15), "Stn C\nReject", fill='white', anchor='mm')

    # --- Station B ---
    bx = WIDTH - margin
    draw.rectangle([bx - 50, conv_y - 25, bx, conv_y + 25],
                   fill='#006600', outline='#44FF44', width=2)
    draw.text((bx - 25, conv_y), "Stn B\nAccept", fill='white', anchor='mm')

    # --- Station A label ---
    draw.text((margin + 30, conv_y + conv_h//2 + 20), "Station A\n(Infeed)",
              fill='#AAAAAA', anchor='mm')

    # --- Photoeyes ---
    pe_positions = {
        'PE1': conv.infeed_pe_pos,
        'PE2': conv.diverter_pe_pos,
        'PE3': conv.outfeed_b_pos,
        'PE4': conv.outfeed_c_pos,
    }
    pe_states = {
        'PE1': sim.plc.read('bInfeedPE'),
        'PE2': sim.plc.read('bDiverterPE'),
        'PE3': sim.plc.read('bOutfeedBPE'),
        'PE4': sim.plc.read('bOutfeedCPE'),
    }
    for name, pos in pe_positions.items():
        x = mm_to_px(pos)
        y = conv_y - conv_h//2 - 20
        blocked = pe_states.get(name, False)
        color = '#FF4444' if blocked else '#44FF44'
        r = 12
        draw.ellipse([x - r, y - r, x + r, y + r], fill=color, outline=color)
        draw.text((x, y - r - 12), name, fill='white', anchor='mm')

    # --- Diverter gate ---
    dx = mm_to_px(conv.diverter_pe_pos)
    dy = conv_y + conv_h//2
    diverter_ext = sim.plc.read('bDiverterActuator')
    gate_color = '#FF8800' if diverter_ext else '#4488FF'
    gate_label = 'DIVERT' if diverter_ext else 'PASS'
    if diverter_ext:
        draw.line([(dx, dy), (dx + 25, dy + 25)], fill=gate_color, width=4)
    else:
        draw.line([(dx, dy), (dx, dy + 25)], fill=gate_color, width=4)
    draw.text((dx + 35, dy + 12), gate_label, fill=gate_color, anchor='lm')

    # --- Boxes ---
    box_size = 30
    for box in sim.active_boxes:
        bx = mm_to_px(box.position_mm)
        by = conv_y
        if box.state == BoxState.JAMMED:
            col = '#FF0000'
        elif box.is_reject:
            col = '#FF8800'
        else:
            col = '#8B6914'
        half = box_size // 2
        draw.rectangle([bx - half, by - half, bx + half, by + half],
                       fill=col, outline='white')
        draw.text((bx, by), str(box.box_id), fill='white', anchor='mm')

    # --- Status panel ---
    panel_y = HEIGHT - 120
    draw.rectangle([0, panel_y, WIDTH, HEIGHT], fill='#0f0f23', outline='#333333')

    state_num = sim.plc.read('iHMI_State') or 0
    state_map = {0: ('STOPPED', '#808080'), 1: ('STARTING', '#FFD700'),
                 2: ('RUNNING', '#00CC00'), 3: ('FAULT', '#FF0000')}
    state_name, state_color = state_map.get(state_num, ('?', '#808080'))
    draw.text((20, panel_y + 15), f"State: {state_name}", fill=state_color, anchor='lm')

    fault_msg = sim.plc.read('sHMI_FaultMsg') or ''
    if fault_msg:
        draw.text((20, panel_y + 40), f"FAULT: {fault_msg}", fill='#FF4444', anchor='lm')

    # Sim time
    mins = int(sim.sim_time) // 60
    secs = int(sim.sim_time) % 60
    draw.text((WIDTH - 20, panel_y + 15), f"Time: {mins:02d}:{secs:02d}",
              fill='#AAAAAA', anchor='rm')

    # Metrics
    metrics_y = panel_y + 60
    box_count = sim.plc.read('rHMI_BoxCount') or 0
    throughput = sim.plc.read('rHMI_Throughput') or 0.0
    avg_ct = sim.plc.read('rHMI_AvgCycleTime') or 0.0
    jam_count = sim.plc.read('rHMI_JamCount') or 0

    items = [
        ('Boxes', str(box_count)),
        ('Cycle', f'{avg_ct:.1f}s'),
        ('Thru', f'{throughput:.0f}/hr'),
        ('Jams', str(jam_count)),
    ]
    spacing = WIDTH // (len(items) + 1)
    for i, (label, value) in enumerate(items):
        x = spacing * (i + 1)
        draw.text((x, metrics_y), label, fill='#888888', anchor='mm')
        draw.text((x, metrics_y + 22), value, fill='#FFFFFF', anchor='mm')

    # Status lights
    motor_on = sim.plc.read('bConveyorMotor')
    green_on = sim.plc.read('bStatusGreen')
    red_on = sim.plc.read('bStatusRed')

    lx, ly = WIDTH // 2, panel_y + 15
    draw.ellipse([lx - 10, ly - 10, lx + 10, ly + 10],
                 fill='#00FF00' if green_on else '#004400')
    draw.ellipse([lx + 20, ly - 10, lx + 40, ly + 10],
                 fill='#FF0000' if red_on else '#440000')
    motor_col = '#00CC00' if motor_on else '#666666'
    draw.text((lx + 55, ly), f"Motor: {'ON' if motor_on else 'OFF'}",
              fill=motor_col, anchor='lm')

    return img


def main():
    random.seed(SEED)

    sim = ProcessSimulator(
        config_path='config_baseline.yaml',
        output_dir='/tmp/gif_capture',
        enable_viz=False,
    )
    sim.config.setdefault('simulation', {})['time_scale'] = TIME_SCALE
    # Boost box generation so the belt stays busy
    sim.config.setdefault('boxes', {})['generation_rate_per_hour'] = 600
    # Higher jam probability for visual drama
    sim.config.setdefault('jams', {})['probability_per_box'] = 0.08
    sim.initialize()
    sim.plc.write('rJamTimeoutSec', 4.0)
    sim.start_system()

    frames = []
    real_start = time.time()
    last_capture = 0
    update_interval = 0.02  # 50 fps physics
    frame_count = 0

    logger.info(f"Capturing {SIM_DURATION_SEC}s of sim at {TIME_SCALE}x speed...")

    while sim.sim_time < SIM_DURATION_SEC:
        real_now = time.time()
        real_dt = update_interval
        sim_dt = real_dt * TIME_SCALE

        sim.update(sim_dt)

        # Capture frame at intervals
        if real_now - last_capture >= CAPTURE_INTERVAL:
            img = render_frame(sim, frame_count)
            frames.append(img)
            frame_count += 1
            last_capture = real_now

        time.sleep(max(0, update_interval - (time.time() - real_now)))

    logger.info(f"Captured {len(frames)} frames")

    # Assemble GIF
    if frames:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        frame_duration = int(1000 / TARGET_FPS)
        frames[0].save(
            OUTPUT,
            save_all=True,
            append_images=frames[1:],
            duration=frame_duration,
            loop=0,
            optimize=True,
        )
        size_kb = OUTPUT.stat().st_size / 1024
        logger.info(f"GIF saved: {OUTPUT} ({size_kb:.0f} KB, {len(frames)} frames, {TARGET_FPS} fps)")
    else:
        logger.error("No frames captured!")

    sim.stop_system()
    sim.plc.disconnect()


if __name__ == '__main__':
    main()
