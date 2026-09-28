"""Slide 3, v3: flowchart (left) + core tracking pipeline (right) + tech stack
and proof strip along the bottom. Reuses build_v2.py pieces."""
import re, pathlib, importlib.util
here = pathlib.Path(__file__).parent
spec = importlib.util.spec_from_file_location('v2', here / 'build_v2.py'); v2 = importlib.util.module_from_spec(spec); spec.loader.exec_module(v2)

flow = re.sub(r'<svg[^>]*>', '<svg viewBox="0 0 852 578" style="display:block;width:100%;height:auto">', v2.grab('0 0 852 578'), 1)

# ---------- the core tracking pipeline, redrawn (fixes: 40 ms, ACQUISITION, REACQUIRE) ----------
def stage(x, n, title, col, art, l1, l2):
    return f'''<g transform="translate({x},92)">
  <rect width="118" height="210" rx="10" fill="#fff" stroke="{col}" stroke-width="2"/>
  <path d="M0 10 a10 10 0 0 1 10 -10 h98 a10 10 0 0 1 10 10 v20 h-118z" fill="{col}"/>
  <circle cx="14" cy="15" r="9" fill="#fff"/><text x="14" y="19" font-size="11" font-weight="800" fill="{col}" text-anchor="middle">{n}</text>
  <text x="27" y="19" font-size="8.6" font-weight="800" fill="#fff">{title}</text>
  <g transform="translate(9,38)">{art}</g>
  <text x="59" y="160" font-size="8.4" fill="#334155" text-anchor="middle">{l1}</text>
  <rect x="7" y="170" width="104" height="30" rx="8" fill="{col}" fill-opacity=".12" stroke="{col}" stroke-opacity=".5"/>
  <text x="59" y="189.5" font-size="10.5" font-weight="700" fill="#0b1f3a" text-anchor="middle">{l2}</text>
</g>'''

sky = lambda extra='': ('<rect width="100" height="106" rx="7" fill="#050b16"/>'
       '<g fill="#fff" opacity=".85"><circle cx="12" cy="14" r="1"/><circle cx="40" cy="30" r=".8"/><circle cx="80" cy="12" r="1.1"/><circle cx="66" cy="70" r=".9"/>'
       '<circle cx="22" cy="86" r="1"/><circle cx="90" cy="92" r=".8"/><circle cx="54" cy="50" r=".7"/><circle cx="30" cy="60" r=".8"/><circle cx="88" cy="46" r="1"/></g>' + extra)
ART = {
 'world': sky('<ellipse cx="50" cy="54" rx="34" ry="12" fill="#6d28d9" opacity=".45" transform="rotate(-20 50 54)"/><circle cx="50" cy="54" r="7" fill="#fde68a"/>'
              '<circle cx="78" cy="28" r="3" fill="#ff5555"/><circle cx="24" cy="36" r="2.4" fill="#ff5555"/><text x="50" y="100" font-size="8" fill="#ff8a8a" text-anchor="middle">● decoys</text>'),
 'camera': ('<rect width="100" height="106" rx="7" fill="#e8eef6"/><rect x="30" y="80" width="40" height="10" rx="3" fill="#475569"/><rect x="44" y="58" width="12" height="24" fill="#64748b"/>'
            '<rect x="26" y="30" width="48" height="30" rx="6" fill="#1e293b"/><circle cx="50" cy="45" r="10" fill="#0b1220" stroke="#4FC7EA" stroke-width="2"/><circle cx="50" cy="45" r="4" fill="#4FC7EA"/>'
            '<path d="M12 45 A38 38 0 0 1 20 20" stroke="#0e7c9a" stroke-width="2" fill="none" marker-end="url(#pa)"/><path d="M88 45 A38 38 0 0 0 80 20" stroke="#0e7c9a" stroke-width="2" fill="none"/>'),
 'percept': sky('<rect x="16" y="18" width="10" height="10" fill="none" stroke="#4FC7EA" stroke-width="1.4"/><rect x="70" y="60" width="10" height="10" fill="none" stroke="#4FC7EA" stroke-width="1.4"/>'
                '<rect x="44" y="40" width="12" height="12" fill="none" stroke="#4FC7EA" stroke-width="1.4"/><rect x="76" y="20" width="9" height="9" fill="none" stroke="#4FC7EA" stroke-width="1.4"/>'),
 'decide': sky('<circle cx="50" cy="50" r="3" fill="#ff6b6b"/><path d="M40 40 h-4 v4 M60 40 h4 v4 M40 60 h-4 v-4 M60 60 h4 v-4" stroke="#3BD68C" stroke-width="2" fill="none"/>'
               '<text x="50" y="84" font-size="9" font-weight="700" fill="#3BD68C" text-anchor="middle">LOCK 4.0 Hz</text>'),
 'out': ('<rect width="100" height="106" rx="7" fill="#0b1220"/><rect x="6" y="8" width="58" height="46" rx="3" fill="#050b16" stroke="#18263a"/>'
         '<path d="M10 44 q10 -20 20 -8 t22 -18" stroke="#4FC7EA" stroke-width="1.6" fill="none"/><rect x="68" y="8" width="26" height="9" rx="2" fill="#14532d"/><text x="81" y="15" font-size="6" fill="#3BD68C" text-anchor="middle" font-weight="700">TRACK</text>'
         '<rect x="68" y="21" width="26" height="5" rx="2" fill="#18263a"/><rect x="68" y="30" width="20" height="5" rx="2" fill="#18263a"/><rect x="68" y="39" width="24" height="5" rx="2" fill="#18263a"/>'
         '<rect x="6" y="60" width="88" height="38" rx="3" fill="#050b16" stroke="#18263a"/><path d="M10 90 L28 70 L46 84 L64 66 L90 78" stroke="#3BD68C" stroke-width="1.6" fill="none"/>'),
}
def ctl(x, icon, col, t, s):
    return f'''<g transform="translate({x},346)"><rect width="166" height="56" rx="9" fill="#fff" stroke="#9fd9c9"/>
  <circle cx="26" cy="28" r="17" fill="{col}"/>{icon}
  <text x="50" y="24" font-size="10.5" font-weight="800" fill="#0b1f3a">{t}</text><text x="50" y="39" font-size="9.5" fill="#334155">{s}</text></g>'''
ICO = {
 'wave': '<path d="M14 28 h4 l3 -7 l4 14 l4 -10 l3 3 h5" stroke="#fff" stroke-width="2" fill="none" transform="translate(0,0)"/>',
 'gauge': '<path d="M15 33 a11 11 0 1 1 22 0" stroke="#fff" stroke-width="2" fill="none"/><path d="M26 33 l6 -8" stroke="#fff" stroke-width="2.2"/>',
 'spiral': '<path d="M26 28 m0 0 a2 2 0 1 1 3 1 a5 5 0 1 1 -7 -4 a8 8 0 1 1 11 8" stroke="#fff" stroke-width="1.8" fill="none"/>',
 'target': '<circle cx="26" cy="28" r="8" stroke="#fff" stroke-width="2" fill="none"/><path d="M26 16 v6 M26 34 v6 M14 28 h6 M32 28 h6" stroke="#fff" stroke-width="2"/>',
}
def st(x, col, t, s):
    return f'''<g transform="translate({x},470)"><rect width="128" height="44" rx="8" fill="#fff" stroke="{col}" stroke-width="1.6"/>
  <circle cx="20" cy="22" r="11" fill="{col}"/><circle cx="20" cy="22" r="4.5" fill="#fff"/>
  <text x="38" y="19" font-size="11" font-weight="800" fill="{col}">{t}</text><text x="38" y="33" font-size="9" fill="#334155">{s}</text></g>'''

pipeline = f'''<svg viewBox="0 0 900 560" style="display:block;width:100%;height:auto" font-family="Liberation Sans,Arial,sans-serif">
<defs><marker id="pa" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8z" fill="#1d5fb8"/></marker>
<linearGradient id="hdr" x1="0" x2="1"><stop offset="0" stop-color="#0b1f3a"/><stop offset="1" stop-color="#1d5fb8"/></linearGradient></defs>
<!-- orbital data & AI -->
<rect x="4" y="18" width="138" height="300" rx="14" fill="#f97316"/>
<text x="73" y="42" font-size="12.5" font-weight="800" fill="#fff" text-anchor="middle">ORBITAL DATA &amp; AI</text>
<rect x="14" y="52" width="118" height="124" rx="10" fill="#fff7ed"/>
<text x="24" y="70" font-size="11" font-weight="800" fill="#0b1f3a">ORBIT DATA</text><text x="24" y="83" font-size="8.6" fill="#7c2d12">real ISS TLEs + SGP4</text>
<g transform="translate(24,90)"><rect width="98" height="78" rx="6" fill="#0b1f3a"/><path d="M0 64 q49 -30 98 -6 v20 h-98z" fill="#1d5fb8" opacity=".7"/>
 <rect x="20" y="22" width="18" height="8" fill="#94a3b8"/><rect x="60" y="22" width="18" height="8" fill="#94a3b8"/><rect x="38" y="20" width="22" height="12" rx="2" fill="#e2e8f0"/>
 <path d="M4 50 Q49 6 94 40" stroke="#fde68a" stroke-dasharray="3 3" fill="none"/></g>
<rect x="14" y="184" width="118" height="124" rx="10" fill="#fff7ed"/>
<text x="24" y="202" font-size="11" font-weight="800" fill="#0b1f3a">NEURAL VERIFIER</text><text x="24" y="215" font-size="8.6" fill="#7c2d12">rejects false candidates</text>
<g transform="translate(24,222)" stroke="#ea580c" stroke-width=".7" opacity=".8">
 {''.join(f'<line x1="{8}" y1="{8+i*15}" x2="{49}" y2="{8+j*15}"/>' for i in range(5) for j in range(5))}
 {''.join(f'<line x1="{49}" y1="{8+i*15}" x2="{90}" y2="{38}"/>' for i in range(5))}
</g>
<g fill="#f97316">{''.join(f'<circle cx="32" cy="{230+i*15}" r="4"/><circle cx="73" cy="{230+i*15}" r="4"/>' for i in range(5))}<circle cx="114" cy="260" r="5"/></g>
<!-- header -->
<rect x="156" y="18" width="740" height="56" rx="14" fill="url(#hdr)"/>
<g transform="translate(176,33)" fill="none" stroke="#fff" stroke-width="2.2" stroke-linejoin="round"><path d="M13 2 L26 9 L13 16 L0 9 Z"/><path d="M0 15 L13 22 L26 15"/></g>
<text x="216" y="55" font-size="22" font-weight="800" fill="#fff" letter-spacing="1">CORE TRACKING PIPELINE</text>
<text x="880" y="55" font-size="11" fill="#bfdbfe" text-anchor="end">one frame every 33 ms</text>
{stage(156, 1, 'VIRTUAL WORLD', '#1d5fb8', ART['world'], 'stars, clutter + decoys', '9.2 MPx / s')}
{stage(304, 2, 'VIRTUAL CAMERA', '#0e7c9a', ART['camera'], 'gimbal limits · sensor noise', '30 fps · 40 ms lag')}
{stage(452, 3, 'PERCEPTION', '#7c3aed', ART['percept'], 'top-hat · matched filter · CFAR', '≈ 6 candidates / frame')}
{stage(600, 4, 'DECISION', '#15803d', ART['decide'], 'blink signature + IMM', '1 verified beacon')}
{stage(748, 5, 'OPERATOR OUTPUTS', '#b45309', ART['out'], 'live status + telemetry', 'Console + video')}
<g fill="#1d5fb8">{''.join(f'<path d="M{x} 185 h8 v-5 l10 10 l-10 10 v-5 h-8z"/>' for x in (274, 422, 570, 718))}<path d="M142 190 l12 0" stroke="#1d5fb8" stroke-width="3"/><path d="M154 190 l-8 -6 v12z"/></g>
<path d="M866 302 V326 Q866 334 858 334 H838" stroke="#1d5fb8" stroke-width="4" fill="none" marker-end="url(#pa)"/>
<!-- control module -->
<rect x="156" y="318" width="704" height="96" rx="14" fill="#0f9f84"/>
<text x="176" y="338" font-size="13" font-weight="800" fill="#fff" letter-spacing=".6">⚙ CONTROL MODULE</text>
{ctl(164, ICO['wave'], '#1d5fb8', 'SMITH PREDICTOR', 'cancels 40 ms delay')}
{ctl(338, ICO['gauge'], '#0b1f3a', 'VELOCITY FEED-FWD', 'follows predicted motion')}
{ctl(512, ICO['spiral'], '#7c3aed', 'SPIRAL SEARCH', 'finds unseen targets')}
{ctl(686, ICO['target'], '#15803d', 'CONTROL LOOP', '≈ 30 commands / s')}
<!-- state machine -->
<rect x="4" y="428" width="892" height="126" rx="14" fill="#eef5fd" stroke="#bfd7f2"/>
<text x="20" y="452" font-size="13.5" font-weight="800" fill="#0b1f3a" letter-spacing=".4">◎ ACQUISITION STATE MACHINE</text>
{st(40, '#1d5fb8', 'SEARCH', 'scan predicted region')}
{st(210, '#b45309', 'ACQUIRE', 'detect + validate')}
{st(380, '#15803d', 'TRACK', 'hold lock')}
{st(550, '#c2410c', 'COAST', 'ride the prediction')}
{st(720, '#b91c1c', 'REACQUIRE', 'recover target')}
<g fill="#1d5fb8">{''.join(f'<path d="M{x} 485 l10 7 l-10 7z"/>' for x in (170, 340, 510, 680))}</g>
<path d="M848 514 V534 H24 V492 H38" stroke="#1d5fb8" stroke-width="2.2" fill="none" marker-end="url(#pa)"/>
<rect x="358" y="524" width="184" height="20" rx="6" fill="#fff" stroke="#1d5fb8"/><text x="450" y="538" font-size="10.5" font-weight="700" fill="#0b1f3a" text-anchor="middle">target lost → SEARCH</text>
</svg>'''

CSS = v2.CSS + '''
.col h5{font-size:9.5px;font-weight:800;letter-spacing:1.1px;margin-bottom:3px}
.stackrow{display:grid;grid-template-columns:repeat(5,1fr);gap:8px}
.stackrow .bds{flex-direction:column;align-items:flex-start;gap:2px}
.stackrow .bd{padding:0 5px 0 0}.stackrow .bd i{width:16px;height:16px;font-size:8.2px}.stackrow .bd span{font-size:9.6px}
.proofrow{display:grid;grid-template-columns:1.25fr 1fr;gap:8px;align-items:center}
.kp4{display:grid;grid-template-columns:1fr 1fr;gap:5px}
.kp4 div{background:#0b1f3a;border-radius:7px;padding:4px 3px;text-align:center}
.kp4 b{display:block;color:#7fe0f8;font-size:14.5px;line-height:1.1}
.kp4 span{display:block;color:#cbd5e1;font-size:8.2px;line-height:1.15}
'''
def stack_cols():
    out = []
    for title, col, items in v2.STACK:
        badges = ''.join(f'<div class="bd"><i style="background:{col}">{ab}</i><span>{lab}</span></div>' for ab, lab in items)
        out.append(f'<div class="col"><h5 style="color:{col}">{title}</h5><div class="bds">{badges}</div></div>')
    return ''.join(out)

G = '#166534'
s3 = f'''
<div style="position:absolute;left:14px;top:96px;width:596px">
  <span class="tag" style="background:#0b1f3a;font-size:11.5px">SOFTWARE FLOWCHART · src/fsoc_pat (pipeline · detection · tracking · control)</span>
  <div class="box" style="background:#fff;border-color:#0b1f3a;padding:3px">{flow}</div>
</div>
<div style="position:absolute;left:630px;top:96px;width:636px">
  <span class="tag" style="background:#1d5fb8;font-size:11.5px">SYSTEM ARCHITECTURE · WHAT HAPPENS TO EVERY FRAME</span>
  <div class="box" style="background:#fff;border-color:#1d5fb8;padding:4px 5px">{pipeline}</div>
</div>
<div style="position:absolute;left:14px;top:524px;width:810px">
  <span class="tag" style="background:#0b1f3a;font-size:11.5px">TECH STACK · every item used in the code</span>
  <div class="box" style="background:#fff;border-color:#0b1f3a;padding:6px 8px 5px"><div class="stackrow">{stack_cols()}</div></div>
</div>
<div style="position:absolute;left:836px;top:524px;width:430px">
  <span class="tag" style="background:{G};font-size:11.5px">PROOF &gt; PROMISE · WORKING PROTOTYPE</span>
  <div class="box" style="background:#f3fbf5;border-color:#a7d7b5;padding:6px">
    <div class="proofrow">
      <div class="shots" style="grid-template-columns:1fr 1fr 1fr;gap:4px">
        <figure><img src="console_track.png" style="height:50px"><figcaption>Console replay</figcaption></figure>
        <figure><img src="software_demo_poster.jpg" style="height:50px"><figcaption>Webcam lock 4 Hz</figcaption></figure>
        <figure><img src="mk1_photo.jpg" style="height:50px"><figcaption>MK1 closed loop</figcaption></figure>
      </div>
      <div class="kp4">
        <div><b>1.27 s</b><span>median lock · 64 runs</span></div>
        <div><b>0 / 64</b><span>wrong-target locks</span></div>
        <div><b>198 µrad</b><span>median error</span></div>
        <div><b>8–21 ms</b><span>per 33 ms frame</span></div>
      </div>
    </div>
  </div>
</div>'''

html = ('<!doctype html><html><head><meta charset="utf-8"><style>' + CSS + '</style></head><body>'
        + v2.html.split('<body>')[1].split('<div class="slide">')[1].join(['<div class="slide">', '']) if False else '')
# assemble: slide 2 from v2 + the new slide 3
v2html = (here / 'slides23_v2.html').read_text()
slide2 = v2html[v2html.index('<div class="slide">'):v2html.index('<div class="slide">', v2html.index('<div class="slide">') + 5)]
slide3 = v2.frame('TECHNICAL APPROACH', 'From camera frame to laser command: the flowchart, the architecture and the stack behind it',
                  'Technologies to be used · Methodology and process for implementation (flow charts / images / working prototype)', 3, s3)
html = '<!doctype html><html><head><meta charset="utf-8"><style>' + CSS + '</style></head><body>' + slide2 + slide3 + '</body></html>'
(here / 'slides23_v3.html').write_text(html)
print('ok')
