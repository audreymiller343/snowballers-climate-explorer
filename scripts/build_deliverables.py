import html
import json
import re
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
TEAM_NAME='Snowballers'
MEMBERS='Sadhana Tadepalli · Saahithi Myneedu · Audrey Miller'

def write(path,text):
    (ROOT/path).write_text(text.strip()+'\n')

def inline(text):
    escaped=html.escape(text)
    return re.sub(r'\[([^\]]+)\]\(([^)]+)\)',r'<a href="\2">\1</a>',escaped)

def markdown_html(text):
    parts=[]
    for block in text.strip().split('\n\n'):
        if block.startswith('# '): parts.append(f'<h1>{html.escape(block[2:])}</h1>')
        elif block.startswith('## '): parts.append(f'<h2>{html.escape(block[3:])}</h2>')
        elif block.startswith('|'):
            lines=block.splitlines()
            table='<table><thead><tr>'+''.join(f'<th>{inline(s.strip())}</th>' for s in lines[0].strip('|').split('|'))+'</tr></thead><tbody>'
            for line in lines[2:]: table+='<tr>'+''.join(f'<td>{inline(s.strip())}</td>' for s in line.strip('|').split('|'))+'</tr>'
            parts.append(table+'</tbody></table>')
        else: parts.append(f'<p>{inline(block)}</p>')
    return ''.join(parts)

def run():
    meta=json.loads((ROOT/'data/metadata.json').read_text())
    figures=json.loads((ROOT/'data/findings.json').read_text())
    rates=pd.read_csv(ROOT/'data/seasonal_rates.csv').set_index(['region','scenario','season']).rate
    model,member,grid=meta['model'],meta['member'],meta['grid']
    title=meta['title']
    question=meta['research_question']
    arctic_w=rates.loc['Arctic','ssp585','DJF']
    arctic_s=rates.loc['Arctic','ssp585','JJA']
    europe_w=rates.loc['Europe sector','ssp585','DJF']
    europe_s=rates.loc['Europe sector','ssp585','JJA']
    provenance=f'''# Seasonal CMIP6 data provenance

Accessed (UTC): {meta['accessed_utc']}. Model: {model}; member: {member}; grid: {grid}; variable: monthly tas/Amon; source units: K; calendar: noleap. These are real climate-model simulations, not temperature observations.

## Discovery and source selection

The original automatic search of https://storage.googleapis.com/cmip6/pangeo-cmip6.json found 276 shared member/grid combinations across 43 models with historical, SSP1-2.6, SSP2-4.5 and SSP5-8.5. Metadata screening, estimated read size, coverage checks and access validation selected {model} on a 64 × 128 grid. See discovery_report.json, selection.json and selected_sources.csv for the exact catalog rows and the original four-experiment search. The revised seasonal question uses historical, SSP2-4.5 and SSP5-8.5 only. SSP1-2.6 is not analyzed in the seasonal project.

The model was selected for accessible complete data and manageable grid size, not because it represents the CMIP6 ensemble. If discovering again, scripts/discover_data.py automatically tries subsequent candidates on access or validation failure. scripts/process_seasonal.py prints exact paths and selected coverage before processing. Scripts use xarray and Zarr v2 with a read-only requests HTTPS mapping to the original public GCS objects. Direct gcsfs routing failed on this host. xarray 2025.1.2 is pinned for compatibility with Zarr 2.18.7; requirements.txt records dependencies.

## Exact seasonal sources
'''
    for source in meta['sources']:
        provenance+=f'''\n### {source['experiment']}

Store: `{source['zstore']}`

Available dates: {source['available_start']} to {source['available_end']}. Complete analyzed season-years: {source['season_years'][0]}–{source['season_years'][1]}. Source version: {source['version']}. Seasonal cache: `{source['cache']}`. SHA-256: `{source['cache_sha256']}`.
'''
    provenance+=f'''\n## Seasonal calculations and boundary handling

{meta['method']}

Historical monthly tas is selected from December 1994 through December 2014. Future monthly tas is selected from January 2015 through December 2100. December 2014 is shared from the historical branch to complete the first scenario winter. No scenario December 2015 is incorrectly used for winter 2015. Incomplete winter 2101 is excluded. Each season has a distinct cell-wise climatology: comparing raw winter and summer temperatures would not measure unequal warming. Anomalies in Kelvin and Celsius have the same magnitude, so no 273.15 offset is applied to differences. An absolute K value would require subtracting 273.15 to express °C.

Only tas, coordinates, bounds and necessary months are read. xarray opens lazily with native time chunks; selected seasons are reduced before the compact caches are written. The full grid supports the Northern Hemisphere spatial figure and latitude profile. Native time chunks can transfer months not used by an aggregation. Four workers limit concurrent computation. The static website loads only the compact regional CSV/JSON, never remote monthly grids.

## Geography

| Region | Latitude | Longitude | Interpretation |
|---|---|---|---|
| North America sector | 25–70°N | 170–50°W | Rectangular geographic sector; land and ocean |
| Europe sector | 35–70°N | 10°W–40°E | Rectangular geographic sector; land and ocean |
| Arctic | 66.5–90°N | All | Polar cap; land and ocean |

These sectors are deliberately labeled as sectors, not continent masks. Published latitude and longitude bounds are saved in seasonal_bounds.json. A cell intersecting a region boundary contributes only the spherical overlap area, proportional to longitude width × [sin(north) − sin(south)]. Arctic and geographic sectors overlap; they are not a partition or independent samples.

## Rate versus anomaly contrast

The warming rate is an ordinary least-squares slope over a named interval, multiplied by ten, in °C/decade. Figure 2 uses 2015–2100 (86 points per season). The website recomputes both seasonal rates on exactly the same selected future years and requires at least 20 complete consecutive years. This minimum is a design guard against very short noisy comparisons, not a guarantee of statistical reliability. No confidence interval, statistical significance, causal estimate or ensemble spread is inferred.

A winter-minus-summer anomaly difference in °C measures accumulated unequal warming relative to distinct seasonal baselines. Its magnitude is not itself a rate. The map, latitude profile and decade heatmap show this anomaly contrast, with positive values meaning a larger winter anomaly. The map and latitude profile cover the Northern Hemisphere only, where the named seasons have the stated meaning.

## Validation and limitations

{meta['limitations']}

Scientific validation independently recomputes regional anomalies and trends, checks complete season-year coverage and historical baselines, and checks analytic spherical region areas. Raw monthly sample validation tests winter 1995, the historical/scenario join in winter 2015, winter 2100 and a summer sample. Reports: validation.json, remote_validation.json and ../checkpoint/test_report.json. Read their statuses for executed verification.

Original annual-scope artifacts are retained under archive/annual_comparison and are not used by the current explorer or checkpoint presentation. Do not combine their findings with this seasonal question.

## Attribution and definitions

Data producer: Canadian Centre for Climate Modelling and Analysis (CCCma). Acknowledge the World Climate Research Programme Working Group on Coupled Modelling, the modeling group and ESGF. Source dataset license metadata are retained in metadata.json; consult them before redistribution beyond class use.

Workflow: https://pangeo-data.github.io/pangeo-cmip6-cloud/accessing_data.html . Northern Hemisphere meteorological season definitions: https://www.ncei.noaa.gov/news/meteorological-versus-astronomical-seasons .
'''
    write('data/provenance.md',provenance)
    narration=f'''Hi, we’re Sadhana Tadepalli, Saahithi Myneedu, and Audrey Miller from {TEAM_NAME}. Our project is called “Is Winter Disappearing Faster Than Summer Is Warming?”

We’re comparing winter and summer warming across regions and emissions scenarios.

We use monthly CMIP6 temperatures from {model}, under SSP2-4.5 and SSP5-8.5. Winter is December–February; summer is June–August. Each season uses its own 1995–2014 baseline. Our geographic sectors include land and ocean.

In the first graph, we follow winter and summer warming over time in the North America sector.

In the second graph, we compare warming rates over 2015–2100. Under SSP5-8.5, Arctic winter warms about {arctic_w:.2f} degrees Celsius per decade, compared with {arctic_s:.2f} in summer.

In the third graph, we compare late-century warming across regions. Winter’s lead is largest in the Arctic.

In the fourth graph, the map shows where winter or summer has accumulated more warming.

In the fifth graph, we compare the winter–summer warming gap across latitudes under both scenarios.

In the sixth graph, we follow that gap decade by decade. Europe shows that winter doesn’t always warm more.

Our D3 prototype lets you switch regions and scenarios, change the years, hover for values, and compare calculated warming rates.

The analysis and prototype are complete. Next are usability feedback and publication. These results describe one model run.'''
    count=len(narration.split())
    write('checkpoint/checkpoint_script_updated.md',f'''# Seasonal checkpoint voiceover

Spoken script: {count} words. Rehearse with the storyboard and aim for 1:55. Word count cannot verify the exported video duration; long model/scenario names take time to speak. Do not read this instruction aloud.

Each “In the … graph” paragraph corresponds to one graph slide. Advance to the next graph between paragraphs.

---

{narration}''')
    print('Narration words:',count)
    write('checkpoint/checkpoint_storyboard.md',f'''# Seasonal checkpoint storyboard

Team: {TEAM_NAME}. Members: {MEMBERS}. Confirm all three members are included in the team registration and Gradescope submission.

Run `python3 -m http.server 8000` in the project root and open http://127.0.0.1:8000/checkpoint/slides.html . The ten-slide deck contains six real figures and an embedded bare-bones D3 prototype at checkpoint/prototype.html. Screenshots are separate files. Narration: {count} words. Use arrow keys or the slide buttons.

| Time | Slide | Visual and narration |
|---|---|---|
| 0:00–0:15 | 1 | Team, title and seasonal warming research question |
| 0:15–0:32 | 2 | CMIP6 model, two scenarios, DJF/JJA, separate baselines |
| 0:32–0:40 | 3 / Figure 1 | North America sector trajectories |
| 0:40–0:53 | 4 / Figure 2 | Actual 2015–2100 rates; Arctic winter versus summer |
| 0:53–1:05 | 5 / Figure 3 | Regions and Europe counterexample; sector boundaries |
| 1:05–1:13 | 6 / Figure 4 | Northern Hemisphere spatial anomaly contrast |
| 1:13–1:20 | 7 / Figure 5 | Latitude dependence under two scenarios |
| 1:20–1:27 | 8 / Figure 6 | Decadal seasonal gap; why interactive comparison helps |
| 1:27–1:47 | 9 | Switch to Arctic, then Europe; inspect rates; toggle scenario; change year window; choose anomaly-gap view; hover; reset |
| 1:47–1:55 | 10 | Actual progress, limitations and next steps |

Export one narrated MP4, at most 120 seconds, with readable figures and audible voiceover. One narrator is enough; list every actual member and attach all members on Gradescope. Rehearse the demo because control changes take time. Submit by November 5, 2026, 11:59 PM. The final public GitHub Pages URL is due November 11, 2026, 11:59 PM. No video or publication is claimed complete here.
''')
    write('checkpoint/progress.md',f'''# Seasonal project progress

Current title: {title}

Question: {question}

Implemented: real monthly CMIP6 processing; complete DJF/JJA boundary handling; separate seasonal baselines; three exactly defined geographic regions; two future scenarios; six seasonal exploratory figures; a D3 anomaly/gap explorer with matched-year linear trend calculations; updated narration, storyboard, presentation, provenance and write-up.

See test_report.json, ../data/validation.json and ../data/remote_validation.json for executed checks. Previous annual-scope results are archived and do not verify this revision.

Human work remaining: confirm registration, supply actual contributions and people-hours, review the interpretation and write-up in your own account, gather usability feedback, rehearse and record an MP4 at most two minutes long, submit to Gradescope by November 5, 2026, 11:59 PM. Approve GitHub Pages publication before the final November 11 deadline. No push, deployment, video recording or Gradescope submission has occurred.
''')
    # The team writes the write-up independently; preserve its files.
    slides=[f'<section class="slide"><p class="eyebrow">DSC 106 / PROJECT 03</p><h1>{title}</h1><p>{TEAM_NAME}</p><p>{MEMBERS}</p><h2>{question}</h2><p class="caveat">Seasonal warming rates, not literal winter disappearance.</p></section>',f'<section class="slide"><p class="eyebrow">THE DATA</p><h1>Two seasons. Two pathways.</h1><p>{model} · {member} · {grid} · monthly tas</p><p>Historical + SSP2-4.5 / SSP5-8.5 · 1995–2100</p><p>DJF winter · JJA summer · separate 1995–2014 baselines</p><p>North America sector · Europe sector · Arctic<br>Defined geographic areas, including land and ocean</p><p>Day-weighted seasons · cell-area-weighted regions · OLS trends in °C/decade</p></section>']
    for f in figures:
        slides.append(f'<section class="slide figure"><img src="figures/{f["file"]}" alt="{html.escape(f["caption"],quote=True)}"><p>{html.escape(f["caption"].split(chr(10))[0])}</p></section>')
    slides+=['<section class="slide"><p class="eyebrow">LIVE PROTOTYPE</p><p>Switch Arctic → Europe · inspect rates · focus years · choose gap view · hover · reset. <a href="prototype.html" target="_blank">Open checkpoint prototype ↗</a></p><iframe title="Winter and summer warming prototype" src="prototype.html"></iframe></section>','<section class="slide"><p class="eyebrow">CURRENT PROGRESS</p><h1>Real seasonal analysis. A working comparison.</h1><p>✓ Complete DJF/JJA seasons and separate baselines<br>✓ Six exploratory figures and calculated findings<br>✓ D3 regional, scenario and time comparisons</p><p>Next: team review, usability feedback, narrated MP4 and GitHub Pages publication.</p><p>One model realization · no ensemble uncertainty · no claim about winter duration</p><a href="prototype.html">Open checkpoint prototype ↗</a></section>']
    write('checkpoint/slides.html','''<!doctype html><html lang="en"><head><meta name="color-scheme" content="light"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Seasonal CMIP6 checkpoint</title><link rel="stylesheet" href="../style.css"><style>body{background:#f5f6f1}.slide{display:none;max-width:1250px;height:calc(100vh - 75px);padding:35px 55px;margin:auto;overflow:auto}.slide.active{display:flex;flex-direction:column;justify-content:center}.slide h1{font-size:clamp(28px,4vw,48px)}.slide h2{font-size:clamp(16px,2.2vw,25px);line-height:1.5}.slide p{font-size:clamp(14px,1.7vw,21px);line-height:1.6}.slide .caveat{font-size:14px;color:#617578}.slide.figure{padding:10px 20px}.figure img{max-height:calc(100vh - 170px);width:100%;object-fit:contain}.figure p{font-size:14px;margin:5px 20px}.slide iframe{width:100%;height:75vh;border:1px solid #dce3dc;border-radius:10px}nav{position:fixed;bottom:0;width:100%;height:65px;background:white;border-top:1px solid #dce3dc;display:flex;align-items:center;justify-content:center;gap:25px}nav span{font-size:12px}button{font-size:12px}@media print{.slide,.slide.active{display:flex;height:95vh;break-after:page}nav{display:none}}</style></head><body>'''+''.join(slides)+'''<nav aria-label="Slide navigation"><button id="prev">← Previous</button><span id="counter" aria-live="polite"></span><button id="next">Next →</button></nav><script>const slides=[...document.querySelectorAll('.slide')];let i=0;function show(){slides.forEach((s,j)=>s.classList.toggle('active',i===j));document.querySelector('#counter').textContent=`${i+1} / ${slides.length}`;document.querySelector('#prev').disabled=i===0;document.querySelector('#next').disabled=i===slides.length-1}document.querySelector('#prev').onclick=()=>{i=Math.max(0,i-1);show()};document.querySelector('#next').onclick=()=>{i=Math.min(slides.length-1,i+1);show()};document.addEventListener('keydown',e=>{if(e.key==='ArrowRight')document.querySelector('#next').click();if(e.key==='ArrowLeft')document.querySelector('#prev').click()});show();</script></body></html>''')
    write('checkpoint/checkpoint_verification.md',f'''# Seasonal checkpoint verification

Current scope: {title}. Prior annual-scope verification is archived and does not establish this revision’s test results.

| Checkpoint requirement | Current evidence | Remaining work |
|---|---|---|
| Team name and members | Slide 1; known names {MEMBERS} | Confirm all three members are registered and attached to the submission |
| Dataset and aspects used | Slide 2: real CMIP6 monthly tas, DJF/JJA, two scenarios, geography and baselines | Show slide during narration |
| 5–6 exploratory graphs leading to question | Slides 3–8: six real seasonal figures; narration explains regional counterexample and time comparisons | Show all six in exported MP4 |
| Title and research question | Slide 1 and narration | Preserve in recording |
| Current interactive progress | Live D3 prototype on slide 9; progress slide 10 | Demonstrate actual controls |
| MP4 no longer than two minutes with voiceover | {count}-word script and 1:55 storyboard | Record; listen; verify actual duration ≤120 seconds |
| One team submission, all members attached | Not accessible from local files | Submit on Gradescope by November 5, 2026, 11:59 PM |

The interactive website uses D3 only and compact static files. Offline exploratory images use Matplotlib. Read ../data/validation.json, ../data/remote_validation.json and test_report.json for executed verification of this seasonal revision. No recording or Gradescope submission is claimed. The final public GitHub Pages URL is due November 11, 2026, 11:59 PM, alongside the required design/development account. Actual contributions and hours are still unfilled, and the team must review and personalize the draft write-up. No push or deployment has occurred.
''')
    write('README.md',f'''# {title}

A static D3 explorer of real CMIP6 winter/summer warming across North America and Europe geographic sectors and the Arctic. Main question: {question}

## Preview

Run `python3 -m http.server 8000` in this directory. Open http://127.0.0.1:8000/ for the explorer or http://127.0.0.1:8000/checkpoint/slides.html for the checkpoint deck. Keep the server running; Ctrl+C stops it. Use HTTP, not HTTPS. The included processed data require no cloud access to view. Direct file:// opening will block JSON in many browsers.

The bare-bones checkpoint prototype is at http://127.0.0.1:8000/checkpoint/prototype.html . It uses the same real data and chart logic with a preliminary interface. Slide 9 embeds this draft. The main index.html retains the polished explorer.

## Current scientific scope

Model: {model}; member {member}; grid {grid}. Monthly tas. Historical 1995–2014 seasonal baseline; SSP2-4.5 and SSP5-8.5 season-years 2015–2100. DJF is Northern Hemisphere winter, assigned to its January/February year; JJA is summer. December 1994 completes baseline winter 1995; historical December 2014 completes future winter 2015. Separate cell-wise DJF/JJA baselines, day-weighted seasons and spherical region areas are essential.

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

## Checkpoint and final submission

Members: {MEMBERS}. Confirm all three members are included in the team registration and Gradescope submission. Enter actual contributions and people-hours in the write-up, review the data interpretation, and rewrite the draft development narrative in your own account.

Use checkpoint/checkpoint_script_updated.md and checkpoint/checkpoint_storyboard.md to record one MP4 with voiceover, at most two minutes long. Show team identity, dataset/aspects, all six figures, title/question and current interactive progress. Verify the actual exported duration and audio. Submit one video per team with all actual members attached on Gradescope by November 5, 2026, 11:59 PM. No video has been recorded by this build.

No push or deployment has occurred. After explicit approval, use a public GitHub repository, commit source and compact data, push to the default branch, and enable Settings → Pages → Deploy from a branch → default branch / root. All runtime paths are relative and .nojekyll is included. Verify the public URL and submit it on Gradescope by November 11, 2026, 11:59 PM. The site links the required write-up. Official assignment: https://dsc106.com/projects/project3/ .
''')

if __name__=='__main__':
    run()
