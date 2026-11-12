# Exploring Global Temperature Changes Across Regions and Climate Scenarios

Draft for team review. Team name: [TEAM NAME]. Members supplied: Sadhana Tadepalli and Saahithi Myneedu. Confirm the complete team before submission.

## Motivation and question

We investigate how projected temperature changes differ across geographic regions and emissions scenarios, and how the gap between scenarios evolves through 2100. A global average can conceal regional differences. A single end-of-century comparison can conceal when trajectories separate. The explorer lets a reader change both place and time while comparing the same model, member and baseline.

## Data and transformations

The data are real CMIP6 monthly near-surface air temperature from CanESM5-CanOE, member r1i1p2f1, grid gn. Historical years 1995–2014 provide the baseline; SSP1-2.6, SSP2-4.5 and SSP5-8.5 cover 2015–2100. The automatic discovery procedure screened 43 models with complete combinations and selected a small accessible grid. This practical choice does not imply that this model represents the ensemble.

Months are weighted by calendar days to form annual means. Each cell’s average annual historical temperature is subtracted from its annual temperature. The magnitude of a Kelvin difference equals a Celsius difference. Spherical cell areas use published latitude bounds; longitude spacing is uniform. Cells crossing region edges contribute their overlapping area. Latitude bands include land and ocean; they are not continents. Figures comparing late-century conditions average 2081–2100, while the decade heatmap uses eight complete ten-year periods starting in 2021. See [provenance](data/provenance.md) for exact sources, access time, coverage and limitations.

## Findings that shaped the design

In this realization, 2081–2100 global warming is 1.54 °C under SSP1-2.6, 2.90 °C under SSP2-4.5 and 5.81 °C under SSP5-8.5. The highest-minus-lowest scenario gap grows from 0.29 °C in 2021–2040 to 4.27 °C in 2081–2100. SSP5-8.5 warming averages 12.94 °C in northern high latitudes and 5.73 °C in southern high latitudes. These calculations motivate interactive region and period selection. They do not establish the same magnitudes in other models or ensemble members.

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
