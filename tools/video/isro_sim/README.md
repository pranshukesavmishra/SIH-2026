# ISRO field simulation video (100 s, 1080p)

`docs/media/ZeroDrift_ISRO_Simulation_1080p.mp4` (and `_720p`) is rendered from this folder.
It is an illustrative, code-rendered visualisation (Three.js), not AI-generated footage.
Every number on screen comes from `docs/PROJECT_STATE.md` §2.

Story: title → LEO satellite, narrow beam → orbit prediction over India → mobile terminal
slews (wide uncertainty cone) → virtual camera rejects star/planet/aircraft/decoy, locks the
4 Hz beacon → closed-loop lock and tracking → hand-off to fine stage, link closes → pipeline + results.

Rebuild (Windows, needs Node, Edge, ffmpeg):
```
npm i playwright-core three
copy ..\..\..\docs\brand\zerodrift_mark.png, isro.png, sih2026.png into this folder
node render.mjs preview 10,55,80          # spot-check frames into prev/
node render.mjs frames 0 100 4            # 3000 JPEG frames into frames/
ffmpeg -framerate 30 -i frames/f%05d.jpg -c:v libx264 -crf 25 -pix_fmt yuv420p out.mp4
```
Live preview: serve the folder and open `index.html?play=1` (add `&t=43` to start at 43 s).
Earth textures: NASA Blue Marble / Black Marble (public domain), via the three-globe examples.
