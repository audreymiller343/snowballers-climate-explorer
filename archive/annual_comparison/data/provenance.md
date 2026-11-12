# CMIP6 data provenance

Access timestamp (UTC): 2026-11-04T23:33:04.413820+00:00

Catalog: https://storage.googleapis.com/cmip6/pangeo-cmip6.json

Model: **CanESM5-CanOE**. Institution: **CCCma**. Ensemble member: **r1i1p2f1**. Grid: **gn**, 64 latitude × 128 longitude cells. Variable: **tas**, monthly **Amon**, source units **K**. Calendar: **noleap**. This is actual model simulation output, not measured observations.

## Automatic discovery and selection

`scripts/discover_data.py` reads the catalog definition and CSV, filters tas/Amon and all four experiments, finds complete shared member/grid combinations, and screens one lowest-numbered complete member per model/grid. Every screened candidate’s four store metadata files must be accessible, have compatible regular coordinate dimensions and K units. Candidates are ranked by approximate uncompressed bytes needed, accounting for time chunks. The selected candidate is validated against decoded dates, monthly coverage, coordinates, published latitude bounds and one full spatial sample per experiment. Failures trigger the next candidate. The same member and grid are used throughout.

The run found 276 complete combinations across 43 models. CanESM5-CanOE and MIROC-ES2L tied near 166 MB estimated uncompressed reads; the first accessible valid candidate was chosen. These estimates are not actual compressed transfer measurements. See [full discovery report](discovery_report.json), [selection and coverage](selection.json), [discovery log](discovery.log) and [exact catalog rows](selected_sources.csv).

## Exact stores and coverage

### historical

- Available: 1850-01-16 12:00:00 through 2014-12-16 12:00:00.
- Used: 1995–2014.
- Store: `gs://cmip6/CMIP6/CMIP/CCCma/CanESM5-CanOE/historical/r1i1p2f1/Amon/tas/gn/v20190429/`
- Initial monthly spatial sample range: 226.203–308.017 K.

### ssp126

- Available: 2015-01-16 12:00:00 through 2100-12-16 12:00:00.
- Used: 2015–2100.
- Store: `gs://cmip6/CMIP6/ScenarioMIP/CCCma/CanESM5-CanOE/ssp126/r1i1p2f1/Amon/tas/gn/v20190429/`
- Initial monthly spatial sample range: 227.070–310.110 K.

### ssp245

- Available: 2015-01-16 12:00:00 through 2100-12-16 12:00:00.
- Used: 2015–2100.
- Store: `gs://cmip6/CMIP6/ScenarioMIP/CCCma/CanESM5-CanOE/ssp245/r1i1p2f1/Amon/tas/gn/v20190429/`
- Initial monthly spatial sample range: 227.045–308.764 K.

### ssp585

- Available: 2015-01-16 12:00:00 through 2100-12-16 12:00:00.
- Used: 2015–2100.
- Store: `gs://cmip6/CMIP6/ScenarioMIP/CCCma/CanESM5-CanOE/ssp585/r1i1p2f1/Amon/tas/gn/v20190429/`
- Initial monthly spatial sample range: 224.342–310.061 K.

## Transformations

Monthly means weighted by calendar days within each year; equal-weight annual means for baseline and future periods. Spherical latitude-strip areas from published latitude bounds, with fractional overlap at band boundaries; equal-width longitude cells. No land mask. Anomaly subtracts each cell’s 1995–2014 mean before spatial aggregation. Kelvin differences have the same magnitude as Celsius differences; no offset is applied to anomalies.

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

One model and one realization; no ensemble uncertainty. Latitude bands include land and ocean. Historical values are simulations, not observations. Anomalies are relative to 1995–2014, not preindustrial. The model was selected for practical access and computational size, not for representativeness of the CMIP6 ensemble. Large high-latitude anomalies in this realization are not general estimates for all models. Spatial grid cells are coarse and cannot resolve local impacts.

Initial direct gcsfs access failed with a network route error. A requests-based read-only HTTPS Zarr mapping accessed the same public GCS objects successfully. xarray 2026.9.0 passed an incompatible zarr_format argument to Zarr 2; pinning xarray 2025.1.2 and Zarr 2.18.7 resolved the conflict. `pip check` passed. No values were replaced or synthesized. Downloaded D3 is version 7.9.0.

## Reproducibility and attribution

Annual intermediate file SHA-256 hashes, exact store versions and transformation metadata appear in metadata.json. The script assertions check finite temperatures, plausible annual Kelvin ranges, full year coverage and zero historical baseline means. Check validation.json, remote_validation.json and ../checkpoint/test_report.json for executed tests. Independent NumPy averages of the raw monthly fields for 1995 historical and 2100 SSP5-8.5 matched the saved annual fields exactly at every cell (maximum difference 0 K).

CMIP6 data were produced by the Canadian Centre for Climate Modelling and Analysis (CCCma). Acknowledge the World Climate Research Programme’s Working Group on Coupled Modelling, the contributing modeling group and the Earth System Grid Federation infrastructure. Preserve model attribution and consult source dataset license metadata before redistribution beyond this class project.

Workflow references: [Pangeo data access](https://pangeo-data.github.io/pangeo-cmip6-cloud/accessing_data.html), [CMIP6 licensing and citation guidance](https://pangeo-data.github.io/pangeo-cmip6-cloud/licensing_citation.html).
