"""Slides 2-3, v2: icon-led layout + tech stack badges. Reuses the verified
architecture and flowchart SVGs from slides23.html (v1)."""
import re, pathlib
here = pathlib.Path(__file__).parent
v1 = (here / 'slides23.html').read_text()

def grab(view):
    i = v1.index(f'viewBox="{view}"'); a = v1.rfind('<svg', 0, i); b = v1.index('</svg>', i) + 6
    return v1[a:b]
arch = re.sub(r'<svg[^>]*>', '<svg width="432" height="438" viewBox="0 0 432 438">', grab('0 0 432 438'), 1)
flow = re.sub(r'<svg[^>]*>', '<svg width="820" height="556" viewBox="0 0 852 578" style="display:block;margin:0 auto">', grab('0 0 852 578'), 1)

# 24x24 stroke icons (drawn here, not brand logos)
I = {
 'target': '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4M1 12h4M19 12h4"/>',
 'decoy':  '<circle cx="12" cy="12" r="4"/><path d="M4 4l16 16M20 4L4 20"/>',
 'clock':  '<circle cx="12" cy="13" r="8"/><path d="M12 9v4l3 2M9 2h6"/>',
 'orbit':  '<circle cx="12" cy="12" r="3"/><ellipse cx="12" cy="12" rx="10" ry="4" transform="rotate(-25 12 12)"/>',
 'scan':   '<path d="M3 7V4h3M21 7V4h-3M3 17v3h3M21 17v3h-3"/><circle cx="12" cy="12" r="2.5"/>',
 'wave':   '<path d="M2 12h3l2-6 4 12 3-9 2 3h6"/>',
 'track':  '<path d="M3 17c4-8 8-8 12-4s5 1 6-3"/><circle cx="21" cy="10" r="1.6"/>',
 'gear':   '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1L7 17M17 7l2.1-2.1"/>',
 'shield': '<path d="M12 2l8 3v6c0 5-3.5 9-8 11-4.5-2-8-6-8-11V5z"/><path d="M8.5 12l2.5 2.5 4.5-5"/>',
 'loop':   '<path d="M4 12a8 8 0 0 1 14-5l2 2M20 12a8 8 0 0 1-14 5l-2-2"/><path d="M20 4v5h-5M4 20v-5h5"/>',
 'layers': '<path d="M12 3l9 5-9 5-9-5z"/><path d="M3 13l9 5 9-5"/>',
 'check':  '<rect x="3" y="3" width="18" height="18" rx="4"/><path d="M8 12l3 3 5-6"/>',
}
def ico(name, color, size=22):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{I[name]}</svg>')

# tech stack: every entry is used in the repository
STACK = [
 ('ENGINE', '#1665b8', [('Py', 'Python 3.11'), ('Np', 'NumPy'), ('CV', 'OpenCV'), ('Or', 'SGP4 · ISS TLEs'), ('Ym', 'PyYAML scenes')]),
 ('AI / LOGIC', '#b45309', [('Cf', 'CFAR detector'), ('Km', 'IMM Kalman'), ('Hz', 'Goertzel 4 Hz'), ('NN', 'Neural verifier'), ('Sp', 'Smith predictor')]),
 ('APPS & WEB', '#0e7c9a', [('Qt', 'PySide6 GUI'), ('Pg', 'PyQtGraph'), ('JS', 'JavaScript'), ('3D', 'three.js twin'), ('Rt', 'WebRTC camera'), ('Se', 'Web Serial')]),
 ('HARDWARE', '#166534', [('Ar', 'Arduino C++'), ('As', 'AccelStepper'), ('St', 'A4988 + NEMA17'), ('I2', 'AS5600 · I²C')]),
 ('QUALITY & DEPLOY', '#6d28d9', [('Pt', 'pytest · 250 pass'), ('CI', 'GitHub Actions'), ('Ex', 'PyInstaller app'), ('Nf', 'Netlify site')]),
]
def stack_html():
    out = []
    for title, col, items in STACK:
        badges = ''.join(f'<div class="bd"><i style="background:{col}">{ab}</i><span>{lab}</span></div>' for ab, lab in items)
        out.append(f'<div class="sg"><div class="sgh" style="color:{col}">{title}</div><div class="bds">{badges}</div></div>')
    return ''.join(out)

CSS = '''
@page { size: 13.333in 7.5in; margin: 0; }
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:"Liberation Sans",Arial,Helvetica,sans-serif;color:#0f172a;background:#fff}
.slide{width:1280px;height:720px;position:relative;overflow:hidden;page-break-after:always;background:#fff}
.oval{position:absolute;left:28px;top:18px;width:136px;height:62px;border-radius:50%;background:#0b1f3a;border:2px solid #0e7c9a;color:#fff;font-weight:700;font-size:16px;display:flex;align-items:center;justify-content:center}
.sih{position:absolute;right:18px;top:6px;height:92px}
.ttl{position:absolute;left:0;right:0;top:12px;text-align:center}
.ttl h1{font-family:"Liberation Serif","Times New Roman",serif;font-size:44px;letter-spacing:1px;line-height:1}
.ttl .sub{font-size:14.5px;color:#0e5a8a;font-weight:700;margin-top:3px}
.ptr{position:absolute;left:190px;top:80px;font-size:10.5px;color:#64748b;font-style:italic}
.foot{position:absolute;left:0;right:0;bottom:0;height:34px;background:#1665b8;color:#fff;display:flex;align-items:center;justify-content:center;font-size:15px;letter-spacing:.5px}
.foot b{position:absolute;right:26px;font-size:17px}
.tag{display:inline-block;color:#fff;font-weight:700;font-size:13px;letter-spacing:.6px;padding:4px 12px;border-radius:8px 8px 0 0}
.box{border:1.6px solid #cbd5e1;border-radius:0 10px 10px 10px;padding:8px 10px}
/* problem cards */
.pcards{display:grid;grid-template-columns:repeat(3,1fr);gap:7px}
.pc{background:#fff;border:1px solid #f3b4ae;border-radius:9px;padding:9px 9px;display:grid;grid-template-columns:34px 1fr;gap:7px;align-items:start}
.pc .ic{width:34px;height:34px;border-radius:9px;background:#fde8e6;display:flex;align-items:center;justify-content:center}
.pc b{display:block;font-size:13px;color:#b3261e;line-height:1.15}
.pc span{font-size:11.2px;line-height:1.3;color:#1f2937;display:block;margin-top:2px}
.pc em{font-style:italic;font-size:8.8px;color:#64748b}
/* solution */
.one{font-size:13px;font-weight:700;color:#0b1f3a;line-height:1.35;margin-bottom:6px}
.one b{color:#0e5a8a}
.caps{display:grid;grid-template-columns:1fr 1fr;gap:5px 8px}
.cap{display:grid;grid-template-columns:30px 1fr;gap:7px;align-items:center;background:#fff;border:1px solid #9cc4e4;border-radius:8px;padding:7px 8px}
.cap .ic{width:30px;height:30px;border-radius:8px;background:#e3f0fa;display:flex;align-items:center;justify-content:center}
.cap b{font-size:12.2px;color:#0b1f3a;display:block;line-height:1.1}
.cap span{font-size:10.8px;color:#334155;line-height:1.25;display:block}
.cap strong{color:#0e5a8a}
.cap.wide{grid-column:1 / -1}
/* uvp */
.uvp{display:grid;grid-template-columns:repeat(4,1fr);gap:7px}
.uv{background:#fff;border:1px solid #a7d7b5;border-radius:9px;padding:12px 8px;text-align:center}
.uv .ic{width:34px;height:34px;border-radius:50%;background:#dcfce7;display:flex;align-items:center;justify-content:center;margin:0 auto 4px}
.uv b{display:block;font-size:12px;color:#166534;line-height:1.15}
.uv span{display:block;font-size:10.4px;color:#334155;line-height:1.25;margin-top:2px}
.kpis{display:flex;gap:6px;margin-top:6px}
.kpi{flex:1;background:#0b1f3a;color:#fff;border-radius:8px;padding:6px 8px;text-align:center}
.kpi b{display:block;font-size:22px;line-height:1.05;color:#7fe0f8}
.kpi span{font-size:9.6px;color:#cbd5e1}
/* tech stack badges */
.sg{margin-bottom:3px}
.sgh{font-size:9.5px;font-weight:800;letter-spacing:1.2px;margin-bottom:2px}
.bds{display:flex;flex-wrap:wrap;gap:3px}
.bd{display:inline-flex;align-items:center;gap:5px;border:1px solid #cbd5e1;border-radius:7px;padding:1px 6px 1px 1px;background:#fff}
.bd i{font-style:normal;color:#fff;font-weight:800;font-size:9.5px;width:19px;height:19px;border-radius:5px;display:inline-flex;align-items:center;justify-content:center}
.bd span{font-size:10px;font-weight:700;color:#0f172a;white-space:nowrap}
.shots{display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px}
.shots img{width:100%;height:54px;object-fit:cover;border-radius:6px;border:1px solid #94a3b8;display:block}
.shots figure{margin:0}.shots figcaption{font-size:9.2px;color:#334155;text-align:center;margin-top:2px;line-height:1.15}
.res{display:grid;grid-template-columns:repeat(4,1fr);gap:5px;margin-top:6px}
.res div{background:#0b1f3a;border-radius:7px;padding:5px 4px;text-align:center}
.res b{display:block;color:#7fe0f8;font-size:16px;line-height:1.1}
.res span{display:block;color:#cbd5e1;font-size:8.6px;line-height:1.2}
svg text{font-family:"Liberation Sans",Arial,sans-serif}
'''

def frame(title, sub, ptr, n, body):
    return (f'<div class="slide"><div class="oval">ZeroDrift</div><img class="sih" src="sih.png">'
            f'<div class="ttl"><h1>{title}</h1><div class="sub">{sub}</div></div><div class="ptr">❖ {ptr}</div>'
            f'{body}<div class="foot">Team ZeroDrift · SIH 2026 · PS 26169<b>{n}</b></div></div>')

R, B, G = '#b3261e', '#0e5a8a', '#166534'
s2 = f'''
<div style="position:absolute;left:24px;top:98px;width:772px">
  <span class="tag" style="background:{R}">PROBLEM EXISTING</span>
  <div class="box" style="background:#fff6f5;border-color:#f3b4ae">
    <div class="pcards">
      <div class="pc"><div class="ic">{ico('target', R)}</div><div><b>Micro-radian aim</b><span>A hair-thin laser must stay on target while vehicles, drones and masts move. <em>(Kaymak 2018)</em></span></div></div>
      <div class="pc"><div class="ic">{ico('decoy', R)}</div><div><b>Wrong-target lock</b><span>Stars, glints and lamps look like the beacon; brightness-only trackers lock the wrong light.</span></div></div>
      <div class="pc"><div class="ic">{ico('clock', R)}</div><div><b>Delay &amp; dropouts</b><span>≈40 ms command lag and blink gaps drop the beam, forcing slow manual re-alignment.</span></div></div>
    </div>
  </div>
  <div style="height:7px"></div>
  <span class="tag" style="background:{B}">PROPOSED SOLUTION</span>
  <div class="box" style="background:#f4f9fd;border-color:#9cc4e4">
    <div class="one">We propose <b>ZeroDrift</b>: software that finds the partner's <b>4 Hz beacon</b> in a camera image, <b>proves</b> it is the right light and <b>steers</b> the terminal to hold it centred: PS26169 solved without special hardware.</div>
    <div class="caps">
      <div class="cap"><div class="ic">{ico('orbit', B)}</div><div><b>Physics-true virtual camera</b><span>SGP4 orbits, turbulence, decoys: <strong>tested before hardware</strong></span></div></div>
      <div class="cap"><div class="ic">{ico('scan', B)}</div><div><b>Detect</b><span>top-hat · matched filter · CFAR · <strong>sub-pixel</strong></span></div></div>
      <div class="cap"><div class="ic">{ico('wave', B)}</div><div><b>Identify</b><span>4 Hz blink test + neural verifier: <strong>0 / 64 wrong locks</strong></span></div></div>
      <div class="cap"><div class="ic">{ico('track', B)}</div><div><b>Track &amp; coast</b><span>IMM Kalman holds through blinks: <strong>98.3 % held</strong></span></div></div>
      <div class="cap wide"><div class="ic">{ico('gear', B)}</div><div><b>Control</b><span>Smith predictor cancels the command delay: <strong>198 µrad</strong> median error, lock in <strong>1.27 s</strong></span></div></div>
    </div>
  </div>
  <div style="height:7px"></div>
  <span class="tag" style="background:{G}">UVP (UNIQUE VALUE PROPOSITION)</span>
  <div class="box" style="background:#f3fbf5;border-color:#a7d7b5">
    <div class="uvp">
      <div class="uv"><div class="ic">{ico('shield', G)}</div><b>Identity, not brightness</b><span>Locks only on the blink signature</span></div>
      <div class="uv"><div class="ic">{ico('loop', G)}</div><b>Delay-cancelled loop</b><span>Error measured on the image itself</span></div>
      <div class="uv"><div class="ic">{ico('layers', G)}</div><b>One engine, 3 modes</b><span>Simulation · webcam · MK2 terminal</span></div>
      <div class="uv"><div class="ic">{ico('check', G)}</div><b>Measured, not claimed</b><span>Open source · 250 passing tests</span></div>
    </div>
  </div>
</div>
<div style="position:absolute;left:812px;top:98px;width:446px">
  <span class="tag" style="background:#0b1f3a">ARCHITECTURE</span>
  <div class="box" style="background:#fff;border-color:#0b1f3a;padding:6px 6px 8px">{arch}
    <div class="kpis">
      <div class="kpi"><b>1.27 s</b><span>median acquisition · 64 runs</span></div>
      <div class="kpi"><b>98.3 %</b><span>lock held · featured demo run</span></div>
      <div class="kpi"><b>0 / 64</b><span>runs with a wrong-target lock</span></div>
    </div>
  </div>
</div>'''

s3 = f'''
<div style="position:absolute;left:18px;top:98px;width:862px">
  <span class="tag" style="background:#0b1f3a">SOFTWARE FLOWCHART · IMPLEMENTED IN src/fsoc_pat (pipeline · detection · tracking · control)</span>
  <div class="box" style="background:#fff;border-color:#0b1f3a;padding:4px">{flow}</div>
</div>
<div style="position:absolute;left:894px;top:98px;width:370px">
  <span class="tag" style="background:#0b1f3a">TECH STACK</span>
  <div class="box" style="background:#fff;border-color:#0b1f3a;padding:7px 8px 3px">{stack_html()}</div>
  <div style="height:7px"></div>
  <span class="tag" style="background:{G}">PROOF &gt; PROMISE · WORKING PROTOTYPE</span>
  <div class="box" style="background:#f3fbf5;border-color:#a7d7b5;padding:7px">
    <div class="shots">
      <figure><img src="console_track.png"><figcaption>Console replay + test record</figcaption></figure>
      <figure><img src="software_demo_poster.jpg"><figcaption>Live webcam lock, 4.0 Hz</figcaption></figure>
      <figure><img src="mk1_photo.jpg"><figcaption>MK1 rig, closed loop</figcaption></figure>
    </div>
    <div class="res">
      <div><b>1.27 s</b><span>median lock · 64 runs</span></div>
      <div><b>0 / 64</b><span>wrong-target locks</span></div>
      <div><b>198 µrad</b><span>median error · demo</span></div>
      <div><b>8–21 ms</b><span>per 33 ms frame · no GPU</span></div>
    </div>
  </div>
</div>'''

html = ('<!doctype html><html><head><meta charset="utf-8"><style>' + CSS + '</style></head><body>'
        + frame('ZERODRIFT', "AI virtual-camera tracking that finds, identifies and holds the partner terminal's beacon, in software",
                'Proposed solution · Detailed explanation · How it addresses the problem · Innovation and uniqueness', 2, s2)
        + frame('TECHNICAL APPROACH', 'Software flow of the tracker: one camera frame every 33 ms',
                'Technologies to be used · Methodology and process for implementation (flow charts / images / working prototype)', 3, s3)
        + '</body></html>')
(here / 'slides23_v2.html').write_text(html)
print('ok', len(html))
