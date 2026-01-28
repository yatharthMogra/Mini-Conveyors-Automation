"""Generate analysis plots from simulation data for the README."""

import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.figsize'] = (12, 5)
plt.rcParams['font.size'] = 11

OUT = Path(__file__).parent.parent / "docs" / "images"
OUT.mkdir(parents=True, exist_ok=True)

def load_latest(directory, prefix):
    files = sorted(Path(directory).glob(f'{prefix}_*.csv'))
    if not files:
        return None
    return pd.read_csv(files[-1])

# Load data
baseline_dir = Path(__file__).parent.parent / "data" / "baseline"
improved_dir = Path(__file__).parent.parent / "data" / "improved"

df_b = load_latest(baseline_dir, "metrics")
df_i = load_latest(improved_dir, "metrics")
ev_b = load_latest(baseline_dir, "events")
ev_i = load_latest(improved_dir, "events")

print(f"Baseline metrics: {len(df_b)} rows" if df_b is not None else "No baseline data")
print(f"Improved metrics: {len(df_i)} rows" if df_i is not None else "No improved data")

# --- Plot 1: Throughput Over Time ---
fig, ax = plt.subplots(figsize=(12, 5))
if df_b is not None:
    ax.plot(df_b['sim_time_sec'] / 60, df_b['throughput_per_hour'],
            label='Baseline (timeout=3.0s)', color='#E74C3C', alpha=0.8, linewidth=1.5)
if df_i is not None:
    ax.plot(df_i['sim_time_sec'] / 60, df_i['throughput_per_hour'],
            label='Improved (timeout=5.5s)', color='#2ECC71', alpha=0.8, linewidth=1.5)
ax.axhline(y=60, color='#3498DB', linestyle='--', alpha=0.7, label='Target (60/hr)')
ax.set_xlabel('Time (minutes)')
ax.set_ylabel('Throughput (boxes/hour)')
ax.set_title('Throughput Over Time: Baseline vs. Improved')
ax.legend()
ax.set_ylim(bottom=0)
plt.tight_layout()
plt.savefig(OUT / 'throughput_comparison.png', dpi=150, bbox_inches='tight')
print(f"Saved: {OUT / 'throughput_comparison.png'}")
plt.close()

# --- Plot 2: Box Count Over Time ---
fig, ax = plt.subplots(figsize=(12, 5))
if df_b is not None:
    ax.plot(df_b['sim_time_sec'] / 60, df_b['box_count'],
            label='Baseline', color='#E74C3C', alpha=0.8, linewidth=2)
if df_i is not None:
    ax.plot(df_i['sim_time_sec'] / 60, df_i['box_count'],
            label='Improved', color='#2ECC71', alpha=0.8, linewidth=2)
ax.set_xlabel('Time (minutes)')
ax.set_ylabel('Cumulative Boxes Processed')
ax.set_title('Cumulative Box Count: Baseline vs. Improved')
ax.legend()
plt.tight_layout()
plt.savefig(OUT / 'box_count_comparison.png', dpi=150, bbox_inches='tight')
print(f"Saved: {OUT / 'box_count_comparison.png'}")
plt.close()

# --- Plot 3: KPI Bar Chart ---
def get_final_metrics(df_m, df_e, label):
    if df_m is None:
        return None
    final = df_m.iloc[-1]
    jam_count = len(df_e[df_e['event_type'] == 'JAM']) if df_e is not None else 0
    box_count = int(final['box_count'])
    dur_min = final['sim_time_sec'] / 60.0
    return {
        'label': label,
        'boxes': box_count,
        'throughput': float(final['throughput_per_hour']),
        'avg_cycle': float(final['avg_cycle_time_sec']),
        'jams': jam_count,
        'jams_hr': jam_count / (dur_min / 60) if dur_min > 0 else 0,
    }

sb = get_final_metrics(df_b, ev_b, 'Baseline')
si = get_final_metrics(df_i, ev_i, 'Improved')

if sb and si:
    fig, axes = plt.subplots(1, 3, figsize=(14, 5))

    # Throughput bars
    labels = ['Baseline\n(timeout=3.0s)', 'Improved\n(timeout=5.5s)']
    colors = ['#E74C3C', '#2ECC71']
    
    axes[0].bar(labels, [sb['throughput'], si['throughput']], color=colors, alpha=0.85, edgecolor='white')
    axes[0].axhline(y=60, color='#3498DB', linestyle='--', alpha=0.7)
    axes[0].set_ylabel('Boxes/Hour')
    axes[0].set_title('Throughput')
    for i, v in enumerate([sb['throughput'], si['throughput']]):
        axes[0].text(i, v + 1, f'{v:.1f}', ha='center', fontweight='bold')

    # Box count bars
    axes[1].bar(labels, [sb['boxes'], si['boxes']], color=colors, alpha=0.85, edgecolor='white')
    axes[1].set_ylabel('Count')
    axes[1].set_title('Boxes Processed')
    for i, v in enumerate([sb['boxes'], si['boxes']]):
        axes[1].text(i, v + 0.2, str(v), ha='center', fontweight='bold')

    # Jam count bars
    axes[2].bar(labels, [sb['jams'], si['jams']], color=colors, alpha=0.85, edgecolor='white')
    axes[2].set_ylabel('Events')
    axes[2].set_title('Jam Events')
    for i, v in enumerate([sb['jams'], si['jams']]):
        axes[2].text(i, v + 0.05, str(v), ha='center', fontweight='bold')

    plt.suptitle('Key Performance Indicators: Before vs. After', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(OUT / 'kpi_comparison.png', dpi=150, bbox_inches='tight')
    print(f"Saved: {OUT / 'kpi_comparison.png'}")
    plt.close()

# --- Plot 4: System State Timeline ---
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 5), sharex=True)
state_colors = {0: '#808080', 1: '#FFD700', 2: '#00CC00', 3: '#FF0000'}
state_names = {0: 'STOPPED', 1: 'STARTING', 2: 'RUNNING', 3: 'FAULT'}

for ax, df, label, title_suffix in [(ax1, df_b, 'Baseline', '(timeout=3.0s)'),
                                      (ax2, df_i, 'Improved', '(timeout=5.5s)')]:
    if df is not None:
        t = df['sim_time_sec'] / 60
        states = df['system_state']
        for s in [0, 1, 2, 3]:
            mask = states == s
            if mask.any():
                ax.fill_between(t, 0, 1, where=mask, alpha=0.7,
                               color=state_colors[s], label=state_names[s])
        ax.set_ylabel(f'{label}\n{title_suffix}')
        ax.set_yticks([])
        ax.legend(loc='upper right', ncol=4, fontsize=8)

ax2.set_xlabel('Time (minutes)')
plt.suptitle('System State Timeline', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(OUT / 'state_timeline.png', dpi=150, bbox_inches='tight')
print(f"Saved: {OUT / 'state_timeline.png'}")
plt.close()

print("\nAll plots generated successfully!")
print(f"Output directory: {OUT}")

# --- Print summary table ---
print("\n" + "=" * 60)
print("  COMPARISON SUMMARY")
print("=" * 60)
if sb and si:
    print(f"  {'Metric':<25} {'Baseline':>12} {'Improved':>12} {'Delta':>10}")
    print(f"  {'-'*25} {'-'*12} {'-'*12} {'-'*10}")
    print(f"  {'Boxes processed':<25} {sb['boxes']:>12} {si['boxes']:>12} {si['boxes']-sb['boxes']:>+10}")
    print(f"  {'Throughput (boxes/hr)':<25} {sb['throughput']:>12.1f} {si['throughput']:>12.1f} {si['throughput']-sb['throughput']:>+10.1f}")
    print(f"  {'Avg cycle time (s)':<25} {sb['avg_cycle']:>12.2f} {si['avg_cycle']:>12.2f} {si['avg_cycle']-sb['avg_cycle']:>+10.2f}")
    print(f"  {'Jam events':<25} {sb['jams']:>12} {si['jams']:>12} {si['jams']-sb['jams']:>+10}")
print("=" * 60)
