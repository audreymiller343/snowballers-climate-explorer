# Climate Explorer — DSC 106 Project 3

A static D3.js explorer of actual CMIP6 CanESM5-CanOE temperature projections. No build step or server-side data processing is needed to view the included processed data.

## Preview

From this directory run `python3 -m http.server 8000`, then open http://localhost:8000/ . Stop with Ctrl+C. Open http://localhost:8000/checkpoint/slides.html for the presentation deck. Opening index.html directly with file:// will prevent JSON loading in many browsers.

## Data and reproduction

- Model: CanESM5-CanOE; member r1i1p2f1; grid gn; monthly tas/Amon; source units Kelvin.
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
