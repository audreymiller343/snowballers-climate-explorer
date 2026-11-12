import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
import requests
from collections.abc import MutableMapping
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class HTTPSStore(MutableMapping):
    def __init__(self, uri):
        self.url = uri.replace('gs://', 'https://storage.googleapis.com/').rstrip('/')
        self.session = requests.Session()
        self.session.mount('https://', HTTPAdapter(max_retries=Retry(total=5, backoff_factor=1, status_forcelist=[429,500,502,503,504]), pool_maxsize=12))
    def __getitem__(self, key):
        response = self.session.get(f'{self.url}/{key}', timeout=120)
        if response.status_code == 404:
            raise KeyError(key)
        response.raise_for_status()
        return response.content
    def __iter__(self):
        return iter(['.zmetadata'])
    def __len__(self):
        return 1
    def __setitem__(self, key, value):
        raise TypeError('Read-only public data')
    def __delitem__(self, key):
        raise TypeError('Read-only public data')

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data'
BANDS = [('Global', -90, 90), ('Northern high latitudes', 60, 90), ('Northern midlatitudes', 30, 60), ('Tropics', -30, 30), ('Southern midlatitudes', -60, -30), ('Southern high latitudes', -90, -60)]
EXPERIMENTS = ['historical', 'ssp126', 'ssp245', 'ssp585']

def annual_mean(a):
    days = a.time.dt.days_in_month
    count = a.time.groupby('time.year').count()
    assert bool((count == 12).all()), 'Incomplete calendar year'
    return (a * days).groupby('time.year').sum('time') / days.groupby('time.year').sum('time')

def run():
    selected = pd.read_csv(OUT / 'selected_sources.csv')
    model, member, grid = selected.iloc[0][['source_id','member_id','grid_label']]
    assert len(selected) == 4
    selected.to_csv(OUT / 'selected_sources.csv', index=False)
    records, sources = [], []
    baseline = None
    for exp in EXPERIMENTS:
        row = selected[selected.experiment_id == exp].iloc[0]
        cache = OUT / f'{model}_{member}_{grid}_{exp}_annual.nc'
        if cache.exists():
            annual = xr.open_dataarray(cache).load()
        else:
            print('Opening', exp, row.zstore, flush=True)
            ds = xr.open_zarr(HTTPSStore(row.zstore), consolidated=True)
            assert ds.tas.attrs['units'] == 'K'
            subset = ds.tas.sel(time=slice('1995-01-01' if exp == 'historical' else '2015-01-01', '2014-12-31' if exp == 'historical' else '2100-12-31'))
            print(subset.sizes, subset.data.chunks, flush=True)
            annual = annual_mean(subset).compute(num_workers=6)
            assert float(annual.min()) > 150 and float(annual.max()) < 350
            annual.attrs = dict(ds.tas.attrs)
            annual.attrs['calendar_used'] = ds.time.encoding.get('calendar', 'unknown')
            annual.to_netcdf(cache)
        expected = np.arange(1995, 2015) if exp == 'historical' else np.arange(2015, 2101)
        np.testing.assert_array_equal(annual.year, expected)
        assert np.isfinite(annual.values).all()
        if baseline is None:
            baseline = annual.mean('year')
            lat = annual.lat.values
            lon = annual.lon.values
            published_bounds = np.array(json.loads((OUT / 'spatial_bounds.json').read_text())['latitude_bounds'])
            bounds = np.concatenate((published_bounds[:,0], [published_bounds[-1,1]]))
            assert np.allclose(np.diff(lon), np.diff(lon)[0])
            assert np.isclose(np.diff(lon)[0] * len(lon), 360)
        else:
            np.testing.assert_array_equal(lat, annual.lat)
            np.testing.assert_array_equal(lon, annual.lon)
        anomaly = annual - baseline
        for name, low, high in BANDS:
            band_weights = xr.DataArray(np.maximum(0, np.sin(np.deg2rad(np.minimum(bounds[1:], high))) - np.sin(np.deg2rad(np.maximum(bounds[:-1], low)))) , dims='lat', coords={'lat': annual.lat})
            series = anomaly.weighted(band_weights).mean(('lat', 'lon'))
            for year, value in zip(series.year.values, series.values):
                records.append({'region': name, 'scenario': exp, 'year': int(year), 'anomaly': round(float(value), 5)})
        if exp != 'historical':
            late = anomaly.sel(year=slice(2081, 2100)).mean('year')
            late.to_netcdf(OUT / f'{exp}_late_century.nc')
        sources.append({'experiment': exp, 'zstore': row.zstore, 'version': int(row.version), 'calendar': annual.attrs['calendar_used'], 'annual_sha256': hashlib.sha256(cache.read_bytes()).hexdigest()})
        print('Processed', exp, flush=True)
    frame = pd.DataFrame(records)
    assert frame.groupby(['scenario', 'region', 'year']).size().max() == 1
    assert frame[frame.scenario == 'historical'].groupby('region').anomaly.mean().abs().max() < 0.00001
    frame.to_csv(OUT / 'temperature.csv', index=False)
    metadata = {'model': model, 'member': member, 'grid': grid, 'variable': 'tas', 'table': 'Amon', 'baseline': '1995–2014', 'accessed_utc': datetime.now(timezone.utc).isoformat(), 'regions': [{'name': n, 'south': l, 'north': h} for n,l,h in BANDS], 'sources': sources, 'records': len(frame), 'method': 'Monthly means weighted by calendar days within each year; equal-weight annual means for baseline and future periods. Spherical latitude-strip areas from published latitude bounds, with fractional overlap at band boundaries; equal-width longitude cells. No land mask. Anomaly subtracts each cell’s 1995–2014 mean before spatial aggregation. Kelvin differences have the same magnitude as Celsius differences; no offset is applied to anomalies.', 'limitations': 'One model and one realization; no ensemble uncertainty. Latitude bands include land and ocean. Historical values are simulations, not observations. Anomalies are relative to 1995–2014, not preindustrial.'}
    (OUT / 'metadata.json').write_text(json.dumps(metadata, indent=2))
    (OUT / 'temperature.json').write_text(json.dumps(records, separators=(',', ':')))
    print('Validated', len(frame), 'records', flush=True)

if __name__ == '__main__':
    run()
