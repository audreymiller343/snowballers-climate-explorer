# Seasonal CMIP6 data provenance

Accessed (UTC): 2026-11-04T23:48:49.736984+00:00. Model: CanESM5-CanOE; member: r1i1p2f1; grid: gn; variable: monthly tas/Amon; source units: K; calendar: noleap. These are real climate-model simulations, not temperature observations.

## Discovery and source selection

The original automatic search of https://storage.googleapis.com/cmip6/pangeo-cmip6.json found 276 shared member/grid combinations across 43 models with historical, SSP1-2.6, SSP2-4.5 and SSP5-8.5. Metadata screening, estimated read size, coverage checks and access validation selected CanESM5-CanOE on a 64 × 128 grid. See discovery_report.json, selection.json and selected_sources.csv for the exact catalog rows and the original four-experiment search. The revised seasonal question uses historical, SSP2-4.5 and SSP5-8.5 only. SSP1-2.6 is not analyzed in the seasonal project.

The model was selected for accessible complete data and manageable grid size, not because it represents the CMIP6 ensemble. If discovering again, scripts/discover_data.py automatically tries subsequent candidates on access or validation failure. scripts/process_seasonal.py prints exact paths and selected coverage before processing. Scripts use xarray and Zarr v2 with a read-only requests HTTPS mapping to the original public GCS objects. Direct gcsfs routing failed on this host. xarray 2025.1.2 is pinned for compatibility with Zarr 2.18.7; requirements.txt records dependencies.

## Exact seasonal sources

### historical

Store: `gs://cmip6/CMIP6/CMIP/CCCma/CanESM5-CanOE/historical/r1i1p2f1/Amon/tas/gn/v20190429/`

Available dates: 1850-01-16 12:00:00 to 2014-12-16 12:00:00. Complete analyzed season-years: 1995–2014. Source version: 20190429. Seasonal cache: `CanESM5-CanOE_r1i1p2f1_gn_historical_v20190429_seasonal.nc`. SHA-256: `f8951a00c34efea05df9bf56926addb180236022e54fd985c533b0c75c236cea`.

### ssp245

Store: `gs://cmip6/CMIP6/ScenarioMIP/CCCma/CanESM5-CanOE/ssp245/r1i1p2f1/Amon/tas/gn/v20190429/`

Available dates: 2015-01-16 12:00:00 to 2100-12-16 12:00:00. Complete analyzed season-years: 2015–2100. Source version: 20190429. Seasonal cache: `CanESM5-CanOE_r1i1p2f1_gn_ssp245_v20190429_seasonal.nc`. SHA-256: `fcabf5317746239942baa3342685f48377afe9a4fcfcf008ab6bf907b783dc0a`.

### ssp585

Store: `gs://cmip6/CMIP6/ScenarioMIP/CCCma/CanESM5-CanOE/ssp585/r1i1p2f1/Amon/tas/gn/v20190429/`

Available dates: 2015-01-16 12:00:00 to 2100-12-16 12:00:00. Complete analyzed season-years: 2015–2100. Source version: 20190429. Seasonal cache: `CanESM5-CanOE_r1i1p2f1_gn_ssp585_v20190429_seasonal.nc`. SHA-256: `791c4fda6e10bf28927454a1320bb489f4f5efbe6d480422bd47ee6eee5bcb17`.

## Seasonal calculations and boundary handling

Meteorological Northern Hemisphere seasons: DJF assigned to January/February year, JJA to calendar year. All three months required, weighted by calendar days. Winter 1995 uses December 1994. Winter 2015 joins historical December 2014 to scenario January–February 2015. Winter 2100 uses December 2099, not December 2100. Each cell’s season-specific mean of 20 seasons in 1995–2014 is subtracted. Regions use spherical area of published cell bounds, with fractional latitude and longitude overlap. Period means weight complete season-years equally. Warming rate is ordinary least-squares slope × 10, in °C/decade, with the same years for winter and summer. Trend displays require at least 20 consecutive future season-years.

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

One model and member, no ensemble uncertainty or significance test. North America and Europe are rectangular sectors, not continent masks, and include ocean. Arctic overlaps the northern parts of the other sectors. No snow, frost-day or winter-length data are used. Disappearing is a narrative hook: this does not measure literal disappearance of winter. Spatially varying baseline is recent, not preindustrial. Seasonal anomaly difference is not the same measure as a warming-rate difference.

Scientific validation independently recomputes regional anomalies and trends, checks complete season-year coverage and historical baselines, and checks analytic spherical region areas. Raw monthly sample validation tests winter 1995, the historical/scenario join in winter 2015, winter 2100 and a summer sample. Reports: validation.json, remote_validation.json and ../checkpoint/test_report.json. Read their statuses for executed verification.

Original annual-scope artifacts are retained under archive/annual_comparison and are not used by the current explorer or checkpoint presentation. Do not combine their findings with this seasonal question.

## Attribution and definitions

Data producer: Canadian Centre for Climate Modelling and Analysis (CCCma). Acknowledge the World Climate Research Programme Working Group on Coupled Modelling, the modeling group and ESGF. Source dataset license metadata are retained in metadata.json; consult them before redistribution beyond class use.

Workflow: https://pangeo-data.github.io/pangeo-cmip6-cloud/accessing_data.html . Northern Hemisphere meteorological season definitions: https://www.ncei.noaa.gov/news/meteorological-versus-astronomical-seasons .
