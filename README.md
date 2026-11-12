# Is Winter Disappearing Faster Than Summer Is Warming?

A static D3 explorer of real CMIP6 winter/summer warming across North America and Europe geographic sectors and the Arctic. Main question: How do the rates of winter and summer warming differ across geographic regions, and how might these seasonal differences change under future emissions scenarios?

## Preview

Run `python3 -m http.server 8000` in this directory. Open http://127.0.0.1:8000/ for the explorer or http://127.0.0.1:8000/checkpoint/slides.html for the checkpoint deck. Keep the server running; Ctrl+C stops it. Use HTTP, not HTTPS. The included processed data require no cloud access to view. Direct file:// opening will block JSON in many browsers.

The bare-bones checkpoint prototype is at http://127.0.0.1:8000/checkpoint/prototype.html . It uses the same real data and chart logic with a preliminary interface. Slide 9 embeds this draft. The main index.html retains the polished explorer.

## Current scientific scope

Model: CanESM5-CanOE; member r1i1p2f1; grid gn. Monthly tas. Historical 1995–2014 seasonal baseline; SSP2-4.5 and SSP5-8.5 season-years 2015–2100. DJF is Northern Hemisphere winter, assigned to its January/February year; JJA is summer. December 1994 completes baseline winter 1995; historical December 2014 completes future winter 2015. Separate cell-wise DJF/JJA baselines, day-weighted seasons and spherical region areas are essential.

North America sector: 25–70°N, 170–50°W. Europe sector: 35–70°N, 10°W–40°E. Arctic: 66.5–90°N, all longitudes. These include land and ocean; the sectors are not continent masks. Regions overlap. “Disappearing” is a narrative hook, not a measurement of winter duration or snow.

The primary chart shows seasonal anomalies or their difference in °C. Rate cards separately calculate OLS trends in °C/decade over matching selected future years (minimum 20 years). The default rate window is 2015–2100. This interval can change the answer; there is no ensemble uncertainty or significance test. Europe provides a counterexample to a universal faster-winter claim.

## Reproduction

Use Python 3.13. Exact installed dependencies are pinned in requirements.txt. D3 7.9.0 is bundled locally with its ISC license.

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/process_seasonal.py
MPLCONFIGDIR=.cache/matplotlib .venv/bin/python scripts/make_figures.py
.venv/bin/python scripts/build_deliverables.py
.venv/bin/python scripts/validate_data.py
.venv/bin/python scripts/validate_remote_sample.py
.venv/bin/python scripts/test_browser.py
```

The included selection.json identifies automatically discovered, previously validated sources. To repeat discovery rather than reuse that selection, run `.venv/bin/python scripts/discover_data.py` in place of process_seasonal.py. It searches all four original experiments for a compatible shared model/member/grid, ranks practical candidates, validates and falls back on failures, then processes the two-scenario seasonal scope. Remote preprocessing requires internet; browser tests use installed Chrome, configured with CHROME_PATH if needed. Source details and transformations are in data/provenance.md. Native cloud time chunks may include extra months; only required months contribute to seasonal values.

## Files

`index.html`, `style.css`, `main.js`: responsive D3 website. `data/temperature.csv` and JSON: 1,152 seasonal records. `data/metadata.json`, provenance.md, selection.json and discovery reports: exact sources and methods. `scripts/`: processing, six figures, generated presentation/docs, scientific and browser tests. `checkpoint/figures/`: six 2560 × 1440 seasonal PNGs. `checkpoint/`: narration, storyboard, findings, slides.html, progress, verification and test/screenshot artifacts. `writeup.md` and linked writeup.html: blank files reserved for the team’s own write-up. `archive/annual_comparison/`: preserved earlier annual project, excluded from the current app and deck. Annual and seasonal NetCDF caches and the large catalog are ignored by Git.
