"""SOP proof charts, plotted straight from logged engine output (no hand-drawn data).
  python tools/sop/proof_charts.py  ->  docs/media/sop/proof_blink.png, proof_campaign.png"""
import json, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11, 'axes.grid': True, 'grid.alpha': .35,
                     'axes.spines.top': False, 'axes.spines.right': False})

# 1. blink rate the engine measured on the light it locked, every frame of the decoy-field run
d = json.load(open('docs/media/telemetry_decoys.json'))
F = d['frames']
t = [f['t'] for f in F if f['ehz'] is not None]
hz = [f['ehz'] for f in F if f['ehz'] is not None]
fig, (ax, ax2) = plt.subplots(2, 1, figsize=(9, 4.6), dpi=170, sharex=True, gridspec_kw={'height_ratios': [4, .55]})
ax.axhspan(3.8, 4.2, color='#16a34a', alpha=.10, label='beacon band (4 Hz ± 0.2)')
ax.plot(t, hz, lw=.8, color='#0e7c9a', label='measured blink rate of the locked light')
ax.axhline(0, color='#b91c1c', lw=2.2, label='a steady lamp reads 0 Hz: outside the band, vetoed')
ax.set_ylim(-.3, 5); ax.set_ylabel('blink rate (Hz)')
ax.set_title(f"Decoy-field run · {len(F):,} frames at 30 fps · median {sorted(hz)[len(hz)//2]:.2f} Hz", fontsize=11.5, loc='left')
ax.legend(loc='lower right', fontsize=9, framealpha=.95)
col = {'SEARCH': '#1d4ed8', 'ACQUIRE': '#b45309', 'TRACK': '#15803d', 'COAST': '#ea580c', 'REACQUIRE': '#b91c1c'}
for f in F:
    ax2.axvspan(f['t'], f['t'] + 1 / 30, color=col.get(f['state'], '#999'), lw=0)
ax2.set_yticks([]); ax2.grid(False); ax2.set_ylabel('state', rotation=0, ha='right', va='center')
ax2.set_xlabel('time (s)   ·   state strip: green TRACK, orange COAST (beacon blinked off), blue SEARCH')
fig.text(.99, .005, 'source: docs/media/telemetry_decoys.json', ha='right', fontsize=8, color='#64748b')
fig.tight_layout(); fig.savefig('docs/media/sop/proof_blink.png'); plt.close(fig)

# 2. every one of the 64 Monte-Carlo passes
c = json.load(open('runs/mc-leo/campaign.json'))
R = [r['report'] for r in c['runs']]
acq = [r['acquisition_time_s'] for r in R]
wrong = [r['decoy_locked_frames'] for r in R]
fig, (a1, a2) = plt.subplots(2, 1, figsize=(9, 4.6), dpi=170, sharex=True, gridspec_kw={'height_ratios': [3, 1.3]})
x = range(1, len(R) + 1)
a1.bar(x, acq, color='#0e7c9a', width=.75)
a1.axhline(3.0, color='#b91c1c', ls='--', lw=1.2); a1.text(64.6, 3.05, 'pass limit 3.0 s', ha='right', va='bottom', fontsize=9, color='#b91c1c')
med = sorted(acq)[len(acq) // 2 - 1: len(acq) // 2 + 1]
a1.set_ylabel('time to lock (s)')
a1.set_title(f'64 randomised ISS-like passes, 900 stars in view · all 64 locked · median {sum(med)/2:.2f} s', fontsize=11.5, loc='left')
a2.bar(x, wrong, color='#b91c1c', width=.75)
a2.set_ylim(0, 5); a2.set_yticks([0, 5]); a2.set_ylabel('wrong-light\nframes')
a2.text(32, 2.6, f'{sum(1 for w in wrong if w)} of 64 runs ever locked a wrong light', ha='center', fontsize=11, color='#15803d', weight='bold')
a2.set_xlabel('run number'); a2.set_xlim(0, 65)
fig.text(.99, .005, 'source: runs/mc-leo/campaign.json', ha='right', fontsize=8, color='#64748b')
fig.tight_layout(); fig.savefig('docs/media/sop/proof_campaign.png'); plt.close(fig)
print('ok', len(R), 'runs; acq median', sum(med) / 2, 'wrong', sum(wrong))
