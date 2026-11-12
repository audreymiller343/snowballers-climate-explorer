import html
import json
import re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

def write(path, text):
    (ROOT/path).write_text(text.strip()+'\n')

def run():
    meta = json.loads((ROOT/'data/metadata.json').read_text())
    selection = json.loads((ROOT/'data/selection.json').read_text())
    figures = json.loads((ROOT/'data/findings.json').read_text())
    df = pd.read_csv(ROOT/'data/temperature.csv')
    late = df[df.year.between(2081,2100)].groupby(['region','scenario']).anomaly.mean().unstack()
    early = df[(df.region=='Global') & df.year.between(2021,2040)].groupby('scenario').anomaly.mean()
    model, member, grid = meta['model'],meta['member'],meta['grid']
    low,mid,high = [late.loc['Global',s] for s in ['ssp126','ssp245','ssp585']]
    north = late.loc['Northern high latitudes','ssp585']
    south = late.loc['Southern high latitudes','ssp585']
    provenance = f'''# CMIP6 data provenance

Access timestamp (UTC): {meta['accessed_utc']}

Catalog: https://storage.googleapis.com/cmip6/pangeo-cmip6.json

Model: **{model}**. Institution: **{selection['sources'][0]['institution_id']}**. Ensemble member: **{member}**. Grid: **{grid}**, 64 latitude × 128 longitude cells. Variable: **tas**, monthly **Amon**, source units **K**. Calendar: **noleap**. This is actual model simulation output, not measured observations.

## Automatic discovery and selection

`scripts/discover_data.py` reads the catalog definition and CSV, filters tas/Amon and all four experiments, finds complete shared member/grid combinations, and screens one lowest-numbered complete member per model/grid. Every screened candidate’s four store metadata files must be accessible, have compatible regular coordinate dimensions and K units. Candidates are ranked by approximate uncompressed bytes needed, accounting for time chunks. The selected candidate is validated against decoded dates, monthly coverage, coordinates, published latitude bounds and one full spatial sample per experiment. Failures trigger the next candidate. The same member and grid are used throughout.

The run found 276 complete combinations across 43 models. {model} and MIROC-ES2L tied near 166 MB estimated uncompressed reads; the first accessible valid candidate was chosen. These estimates are not actual compressed transfer measurements. See [full discovery report](discovery_report.json), [selection and coverage](selection.json), [discovery log](discovery.log) and [exact catalog rows](selected_sources.csv).

## Exact stores and coverage
'''
    for source in selection['coverage']:
        provenance += f"\n### {source['experiment']}\n\n- Available: {source['available_start']} through {source['available_end']}.\n- Used: {source['selected_years'][0]}–{source['selected_years'][1]}.\n- Store: `{source['zstore']}`\n- Initial monthly spatial sample range: {source['sample_K_range'][0]:.3f}–{source['sample_K_range'][1]:.3f} K.\n"
    provenance += f'''\n## Transformations

{meta['method']}

Absolute temperature in Celsius is K − 273.15. Since these outputs contain differences, applying that offset again would be incorrect. All twelve months must be present in each year. Years receive equal weight in the 1995–2014 baseline and the 2081–2100 comparison. Decades are complete ten-year blocks, 2021–2030 through 2091–2100.

The full global domain is necessary for the spatial heatmap and all six regional views. Only tas for 1995–2014 historical and 2015–2100 future is selected; xarray opens lazily with native time chunks. Annual fields are reduced before storage. The original time chunks mean some data outside the selected historical years may be read; the full 1850–2014 monthly historical series is never intentionally materialized. Concurrent computation is limited to six workers. The compact website data are CSV and JSON; annual NetCDF caches are offline intermediates.

## Regions

| Label | Latitude limits | Coverage |
|---|---|---|
| Global | 90°S–90°N | Land and ocean |
| Northern high latitudes | 60°N–90°N | Land and ocean |
| Northern midlatitudes | 30°N–60°N | Land and ocean |
| Tropics | 30°S–30°N | Land and ocean |
| Southern midlatitudes | 60°S–30°S | Land and ocean |
| Southern high latitudes | 90°S–60°S | Land and ocean |

Boundary cells contribute by their spherical fractional area. Published native cell bounds are retained in spatial_bounds.json. No continental or land-only claims are made. The latitude profile uses equal-width longitude means at each native latitude, rather than averaging across latitudes.

## Reliability and limitations

{meta['limitations']} The model was selected for practical access and computational size, not for representativeness of the CMIP6 ensemble. Large high-latitude anomalies in this realization are not general estimates for all models. Spatial grid cells are coarse and cannot resolve local impacts.

Initial direct gcsfs access failed with a network route error. A requests-based read-only HTTPS Zarr mapping accessed the same public GCS objects successfully. xarray 2026.9.0 passed an incompatible zarr_format argument to Zarr 2; pinning xarray 2025.1.2 and Zarr 2.18.7 resolved the conflict. `pip check` passed. No values were replaced or synthesized. Downloaded D3 is version 7.9.0.

## Reproducibility and attribution

Annual intermediate file SHA-256 hashes, exact store versions and transformation metadata appear in metadata.json. The script assertions check finite temperatures, plausible annual Kelvin ranges, full year coverage and zero historical baseline means. Check validation.json, remote_validation.json and ../checkpoint/test_report.json for executed tests. Independent NumPy averages of the raw monthly fields for 1995 historical and 2100 SSP5-8.5 matched the saved annual fields exactly at every cell (maximum difference 0 K).

CMIP6 data were produced by the Canadian Centre for Climate Modelling and Analysis (CCCma). Acknowledge the World Climate Research Programme’s Working Group on Coupled Modelling, the contributing modeling group and the Earth System Grid Federation infrastructure. Preserve model attribution and consult source dataset license metadata before redistribution beyond this class project.

Workflow references: [Pangeo data access](https://pangeo-data.github.io/pangeo-cmip6-cloud/accessing_data.html), [CMIP6 licensing and citation guidance](https://pangeo-data.github.io/pangeo-cmip6-cloud/licensing_citation.html).
'''
    write('data/provenance.md',provenance)
    narration = f'''# Checkpoint voiceover

Replace the team-name placeholder before recording. Narration below is intended for about 110–115 seconds; rehearse with the slide timings. Do not read these instructions aloud.

---

We are [TEAM NAME]: Sadhana Tadepalli and Saahithi Myneedu. Our project is “Exploring Global Temperature Changes Across Regions and Climate Scenarios.”

We ask how projected warming differs across regions and emissions pathways, and how the gap changes through 2100.

We automatically searched the public CMIP6 catalog and selected {model}, using one shared ensemble member. We analyze monthly near-surface air temperature for historical conditions and three scenarios. Every anomaly uses a 1995 through 2014 baseline, with calendar-aware annual means and area-weighted latitude bands.

Our first graph connects the historical simulation to future pathways. The second shows the global gap between the highest and lowest emissions scenarios reaching {high-low:.2f} degrees Celsius in the 2081 through 2100 average.

The regional bars show that northern high latitudes warm by {north:.2f} degrees Celsius under SSP5-8.5, compared with {high:.2f} degrees globally. These bands include land and ocean.

The spatial heatmap reveals variation within those averages. The latitude profile compares north and south. The decade heatmap shows when warming accumulates. Together, these patterns led us to focus on regional differences and the changing scenario gap.

Our D3 prototype lets viewers select a band, toggle scenarios, focus the time range, inspect annual values, and reset. Its summary recalculates the comparison for the selected data.

Data processing and six exploratory figures are complete. Next, we will gather usability feedback, refine the narration, and publish the prototype. These are conditional projections from one model realization, without ensemble uncertainty.
'''
    write('checkpoint/checkpoint_script.md',narration)
    count = len(narration.split('---\n\n')[1].split())
    print('Narration word count:',count)
    write('checkpoint/checkpoint_storyboard.md',f'''# Checkpoint storyboard

Team: [TEAM NAME]. Members: Sadhana Tadepalli; Saahithi Myneedu. Add any additional actual members before submission.

Open `checkpoint/slides.html` using the local HTTP server. Use arrow keys or the Previous/Next buttons. Six full-resolution images are in `checkpoint/figures/`. The deck includes a live prototype; verified screenshots are separate files, `prototype_desktop.png` and `prototype_mobile.png`. Narration: {count} words; rehearse to finish by 1:55 and leave a short margin below two minutes. Word count does not verify the final recording duration, especially when speaking scenario names and demonstrating controls.

| Time | Screen | Voiceover focus |
|---|---|---|
| 0:00–0:12 | Slide 1: title and members | Team, title, question |
| 0:12–0:30 | Slide 2: data and method | Model, member, monthly tas, scenarios, baseline, weighting |
| 0:30–0:39 | Figure 1 | Historical simulation and future trajectories |
| 0:39–0:49 | Figure 2 | Late-century global scenario gap |
| 0:49–1:00 | Figure 3 | Northern high latitudes versus global warming |
| 1:00–1:08 | Figure 4 | Within-band spatial variation |
| 1:08–1:16 | Figure 5 | Latitude profile and north–south contrast |
| 1:16–1:24 | Figure 6 | Decadal accumulation |
| 1:24–1:45 | Live prototype | Select Northern high latitudes; hide SSP2-4.5; set start to 2050; hover; reset |
| 1:45–1:55 | Progress slide | Completed analysis, scope limitation, next steps |

Record one MP4 with audible narration, at most two minutes. Show the actual prototype; if recording the iframe is difficult, open the main site in another tab. Include all actual members on Gradescope. The assignment currently says teams of 3–4; only two names have been provided, so confirm team registration or any instructor-approved exception. No teammates have been invented.
''')
    write('checkpoint/progress.md','''# Checkpoint progress

## Completed artifacts

- Automatic public CMIP6 catalog discovery, metadata screening, decoded coverage validation and candidate fallback.
- Four real matching experiments; calendar-day annual means, published cell bounds, area-weighted bands and shared historical baseline.
- Six high-resolution exploratory figures, calculated captions and local source records.
- D3 static prototype with region selection, scenario toggles, annual tooltips, keyboard inspection, two year sliders, dynamic summaries and reset.
- Narration, presentation deck, storyboard, reproducible scripts and a draft write-up.

Executed test results are recorded in test_report.json and ../data/validation.json. These reports, rather than this artifact list, determine the verified status of each behavior.

## Human work remaining

- Supply a team name and confirm the complete member list/registration. Current known members: Sadhana Tadepalli and Saahithi Myneedu.
- Review the scientific interpretation and rewrite the draft development narrative to reflect your own work and decisions.
- Enter actual contributions and people-hours; these have not been estimated.
- Rehearse and record the narrated MP4 under two minutes; submit by November 5, 2026, 11:59 PM.
- Gather usability feedback. Approve and carry out GitHub Pages publication for the final prototype; no push or deployment has occurred.
- Submit the final public prototype URL by November 11, 2026, 11:59 PM.
''')
    writeup = f'''# Exploring Global Temperature Changes Across Regions and Climate Scenarios

Draft for team review. Team name: [TEAM NAME]. Members supplied: Sadhana Tadepalli and Saahithi Myneedu. Confirm the complete team before submission.

## Motivation and question

We investigate how projected temperature changes differ across geographic regions and emissions scenarios, and how the gap between scenarios evolves through 2100. A global average can conceal regional differences. A single end-of-century comparison can conceal when trajectories separate. The explorer lets a reader change both place and time while comparing the same model, member and baseline.

## Data and transformations

The data are real CMIP6 monthly near-surface air temperature from {model}, member {member}, grid {grid}. Historical years 1995–2014 provide the baseline; SSP1-2.6, SSP2-4.5 and SSP5-8.5 cover 2015–2100. The automatic discovery procedure screened 43 models with complete combinations and selected a small accessible grid. This practical choice does not imply that this model represents the ensemble.

Months are weighted by calendar days to form annual means. Each cell’s average annual historical temperature is subtracted from its annual temperature. The magnitude of a Kelvin difference equals a Celsius difference. Spherical cell areas use published latitude bounds; longitude spacing is uniform. Cells crossing region edges contribute their overlapping area. Latitude bands include land and ocean; they are not continents. Figures comparing late-century conditions average 2081–2100, while the decade heatmap uses eight complete ten-year periods starting in 2021. See [provenance](data/provenance.md) for exact sources, access time, coverage and limitations.

## Findings that shaped the design

In this realization, 2081–2100 global warming is {low:.2f} °C under SSP1-2.6, {mid:.2f} °C under SSP2-4.5 and {high:.2f} °C under SSP5-8.5. The highest-minus-lowest scenario gap grows from {early.ssp585-early.ssp126:.2f} °C in 2021–2040 to {high-low:.2f} °C in 2081–2100. SSP5-8.5 warming averages {north:.2f} °C in northern high latitudes and {south:.2f} °C in southern high latitudes. These calculations motivate interactive region and period selection. They do not establish the same magnitudes in other models or ensemble members.

## Visual encodings and alternatives

The primary encoding uses horizontal position for year and vertical position for annual temperature anomaly. A common baseline and shared axes support direct scenario comparison. Consistent teal, amber and rose distinguish the three scenarios across website and figures. Historical simulation is gray. Labels and numeric tooltips accompany color, so scenario identification does not depend on color alone. A zero reference line makes the baseline explicit. The y-axis adapts to the selected region and period, preserving space for small changes; readers must use tick labels when comparing separate views.

We retained annual variability rather than smoothing it into an apparently exact trajectory. Bars are useful for the static 2081–2100 comparison but hide the timing of scenario separation. A map is useful for spatial patterns but would require more complex geographic navigation for the primary interaction. A region-by-decade heatmap summarizes timing efficiently but loses annual detail. The six exploratory views therefore support a focused line-chart interface rather than six competing interactive panels. These are implementation alternatives considered during this build; the team should add its own design discussion after reviewing the prototype.

## Interaction design

The region dropdown changes the underlying area-weighted series. Scenario checkboxes reduce overlap and allow a reader to compare a pair. Start and end sliders restrict years and prevent an inverted range. Hover and keyboard arrow inspection report annual values at matching years. Reset restores all scenarios, the global domain and full period. A dynamic summary averages up to the last twenty visible future years, identifies the exact period and sample count, and compares selected scenarios for matching years. Selecting no scenarios or a historical-only window produces an explanatory state. Opacity transitions are brief and respect reduced-motion preferences.

## Limitations and uncertainty

This is one model and one realization. No uncertainty envelope is shown because a single realization cannot estimate between-model or ensemble spread. Scenarios are conditional projections, not precise forecasts. The 1995–2014 baseline is not preindustrial; values must not be compared directly with warming thresholds defined relative to 1850–1900. Coarse spatial cells and latitude bands cannot support claims about a specific city, country or land-only region. Historical simulations are not observations. A changing y-axis means cross-view pixel height alone is not a valid comparison.

## Development and validation

This workspace was created with AI coding assistance. Automatic catalog screening preceded graph generation. Initial gcsfs routing and an xarray/Zarr version conflict were diagnosed; the final reader accesses the same public GCS objects through HTTPS. Annual caches and compact website data separate expensive preprocessing from the static interface. Exact versions are recorded in requirements.txt. Calculated findings and presentation materials are generated from the processed data rather than manually entered values.

Executed scientific and browser checks are recorded in data/validation.json and checkpoint/test_report.json. Review those reports before making claims about verification. The team should replace this draft process section with its own account of review, testing, refinement and division of work. User feedback has not yet been collected, and the site has not been published.

## Contributions and actual time

| Member | Actual contribution | Actual people-hours |
|---|---|---|
| Sadhana Tadepalli | [Fill in actual work] | [Not provided] |
| Saahithi Myneedu | [Fill in actual work] | [Not provided] |
| Additional registered member(s), if any | [Fill in actual work] | [Not provided] |

Total people-hours: [Not provided]. Most time-consuming work: [Team to describe from actual experience]. No human development hours or contributions have been inferred.
'''
    write('writeup.md',writeup)
    def inline(text):
        return re.sub(r'\[([^\]]+)\]\(([^)]+)\)',r'<a href="\2">\1</a>',html.escape(text))
    paragraphs = []
    for block in writeup.strip().split('\n\n'):
        if block.startswith('# '): paragraphs.append(f'<h1>{html.escape(block[2:])}</h1>')
        elif block.startswith('## '): paragraphs.append(f'<h2>{html.escape(block[3:])}</h2>')
        elif block.startswith('|'):
            lines=block.splitlines()
            headers=lines[0].strip('|').split('|')
            table='<table style="width:100%;border-collapse:collapse;font-size:13px"><thead><tr>'+''.join(f'<th style="text-align:left;border-bottom:1px solid #bacac3;padding:10px">{inline(cell.strip())}</th>' for cell in headers)+'</tr></thead><tbody>'
            for line in lines[2:]:
                table+='<tr>'+''.join(f'<td style="border-bottom:1px solid #dce3dc;padding:10px">{inline(cell.strip())}</td>' for cell in line.strip('|').split('|'))+'</tr>'
            paragraphs.append(table+'</tbody></table>')
        else: paragraphs.append(f'<p>{inline(block)}</p>')
    write('writeup.html','<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Design & development write-up</title><link rel="stylesheet" href="style.css"><main style="max-width:850px;padding-top:40px;padding-bottom:60px;line-height:1.8"><a href="./">← Back to explorer</a>'+''.join(paragraphs)+'<p><a href="data/provenance.md">Data provenance</a> · <a href="checkpoint/test_report.json">Browser test report</a></p></main></html>')
    slides = [f'<section class="slide"><p class="eyebrow">DSC 106 / PROJECT 03</p><h1>Exploring Global Temperature Changes Across Regions and Climate Scenarios</h1><p>[TEAM NAME]</p><p>Sadhana Tadepalli · Saahithi Myneedu</p><h2>How does the warming gap evolve across regions and scenarios through 2100?</h2></section>',f'<section class="slide"><p class="eyebrow">THE DATA</p><h1>One model. A consistent comparison.</h1><p>{model} · {member} · {grid} · 64 × 128 cells</p><p>Monthly tas · historical + SSP1-2.6 / SSP2-4.5 / SSP5-8.5</p><p>1995–2014 historical baseline · 2015–2100 projections</p><p>Calendar-day annual means · published cell-area weights · six latitude views</p><p>One model realization. Land and ocean. No ensemble uncertainty.</p></section>']
    for f in figures:
        slides.append(f'<section class="slide figure"><img src="figures/{f["file"]}" alt="{html.escape(f["caption"],quote=True)}"><p>{html.escape(f["caption"].split(chr(10))[0])}</p></section>')
    slides += ['<section class="slide"><p class="eyebrow">LIVE PROTOTYPE</p><p>Select a band → hide a scenario → focus years → inspect → reset. <a href="../index.html" target="_blank">Open full explorer ↗</a></p><iframe title="Interactive climate explorer" src="../index.html"></iframe></section>','<section class="slide"><p class="eyebrow">PROGRESS & NEXT STEPS</p><h1>Analysis complete. Prototype ready for review.</h1><p>✓ Real CMIP6 data and source records<br>✓ Six exploratory figures<br>✓ Interactive D3 comparison</p><p>Next: team review, usability feedback, narrated recording, and GitHub Pages publication.</p><p>Scope: one model realization; conditional projections, with no ensemble uncertainty.</p><a href="../index.html">Return to explorer ↗</a></section>']
    write('checkpoint/slides.html','''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CMIP6 checkpoint presentation</title><link rel="stylesheet" href="../style.css"><style>body{background:#f5f6f1}.slide{display:none;max-width:1250px;height:calc(100vh - 75px);padding:45px 55px;margin:auto;overflow:auto}.slide.active{display:flex;flex-direction:column;justify-content:center}.slide h1{font-size:clamp(28px,4vw,48px)}.slide p{font-size:clamp(15px,2vw,24px);line-height:1.65}.slide.figure{padding:10px 20px}.figure img{max-height:calc(100vh - 170px);width:100%;object-fit:contain}.figure p{font-size:14px;margin:5px 20px}.slide iframe{width:100%;height:75vh;border:1px solid #dce3dc;border-radius:10px}nav{position:fixed;bottom:0;width:100%;height:65px;background:white;border-top:1px solid #dce3dc;display:flex;align-items:center;justify-content:center;gap:25px}nav span{font-size:12px}button{font-size:12px}@media print{.slide,.slide.active{display:flex;height:95vh;break-after:page}nav{display:none}}</style></head><body>'''+''.join(slides)+'''<nav aria-label="Slide navigation"><button id="prev">← Previous</button><span id="counter" aria-live="polite"></span><button id="next">Next →</button></nav><script>const slides=[...document.querySelectorAll('.slide')];let i=0;function show(){slides.forEach((s,j)=>s.classList.toggle('active',i===j));document.querySelector('#counter').textContent=`${i+1} / ${slides.length}`;document.querySelector('#prev').disabled=i===0;document.querySelector('#next').disabled=i===slides.length-1}document.querySelector('#prev').onclick=()=>{i=Math.max(0,i-1);show()};document.querySelector('#next').onclick=()=>{i=Math.min(slides.length-1,i+1);show()};document.addEventListener('keydown',e=>{if(e.key==='ArrowRight')document.querySelector('#next').click();if(e.key==='ArrowLeft')document.querySelector('#prev').click()});show();</script></body></html>''')
    write('README.md',f'''# Climate Explorer — DSC 106 Project 3

A static D3.js explorer of actual CMIP6 {model} temperature projections. No build step or server-side data processing is needed to view the included processed data.

## Preview

From this directory run `python3 -m http.server 8000`, then open http://localhost:8000/ . Stop with Ctrl+C. Open http://localhost:8000/checkpoint/slides.html for the presentation deck. Opening index.html directly with file:// will prevent JSON loading in many browsers.

## Data and reproduction

- Model: {model}; member {member}; grid {grid}; monthly tas/Amon; source units Kelvin.
- Historical baseline: 1995–2014. Three SSP scenarios: 2015–2100.
- Calendar-day annual means; spatial weights from published spherical cell bounds; land and ocean.
- Actual findings: [six figures and captions](checkpoint/checkpoint_findings.md).
- Exact sources and limitations: [provenance](data/provenance.md), [selection](data/selection.json), [discovery report](data/discovery_report.json).

The included CSV/JSON files run the website without cloud access. To repeat the complete analysis, use Python 3.13 and an internet connection:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/discover_data.py
.venv/bin/python scripts/make_figures.py
.venv/bin/python scripts/build_deliverables.py
.venv/bin/python scripts/validate_data.py
.venv/bin/python scripts/validate_remote_sample.py
.venv/bin/python scripts/test_browser.py
```

Discovery prints the exact model/member/grid, coverage and cloud paths before processing. It automatically tries compatible candidates on access or validation failures. The local 77 MB catalog cache and annual NetCDF caches are ignored by Git; the catalog is downloaded when absent. Native time chunks may include extra months around the selected years. Only tas and needed dates are analyzed. The full spatial domain supports all bands and the spatial heatmap. No fake data are substituted.

The tested environment pins xarray 2025.1.2 with Zarr 2.18.7. Direct gcsfs access failed on this host; the read-only HTTPS mapper reads the same Zarr objects with requests. Exact dependency versions are in requirements.txt. Browser tests use an installed Chrome at the macOS path in scripts/test_browser.py; set CHROME_PATH on other systems.

## Files

- `index.html`, `style.css`, `main.js`: responsive D3 interface and accessible native controls.
- `vendor/d3.v7.min.js`: locally bundled D3 7.9.0, ISC license in `vendor/D3-LICENSE`.
- `data/`: compact annual data, exact source records, metadata and validation reports.
- `scripts/`: automatic discovery, preprocessing, figures, documents and tests.
- `checkpoint/figures/`: six 2560 × 1440 PNG figures.
- `checkpoint/`: narration, storyboard, findings, progress, HTML slide deck, test report and screenshots.
- `writeup.md`, `writeup.html`: linked draft design/development account with contribution/hour fields left unfilled.

## Checkpoint submission — November 5, 2026, 11:59 PM

Read [the narration](checkpoint/checkpoint_script.md) and [storyboard](checkpoint/checkpoint_storyboard.md). Replace [TEAM NAME], confirm all members, rehearse, and record one narrated MP4 at most two minutes long. Show the dataset, 5–6 exploratory figures, title/research question and current interactive prototype. Submit the MP4 on Gradescope and add every actual member. Audio/voiceover is required; not every member must appear. No video has been recorded by this build.

Known names: Sadhana Tadepalli; Saahithi Myneedu. The assignment specifies teams of 3–4; confirm complete registration or instructor-approved arrangements. Contributions and actual people-hours must be supplied by the team. Review and personalize the draft write-up.

## GitHub Pages — after explicit approval

No repository push or deployment has occurred. After approval, create/use a public GitHub repository, commit the source and compact data, push to its default branch, then choose Settings → Pages → Deploy from a branch → default branch / root. `.nojekyll` is included and all runtime paths are relative, supporting a project subdirectory URL. Open the resulting public URL and verify it. Submit that URL on Gradescope by November 11, 2026, 11:59 PM, with all members included. The page links the required design and development write-up.

Official assignment: https://dsc106.com/projects/project3/ . Check your course announcements for changes. Website plots use D3 only; Matplotlib is used offline for checkpoint figures.
''')

if __name__ == '__main__':
    run()
