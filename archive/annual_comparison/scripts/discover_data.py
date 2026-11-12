import json
import math
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np
import pandas as pd
import requests
import xarray as xr
from process_data import HTTPSStore, EXPERIMENTS

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data'
CATALOG = 'https://storage.googleapis.com/cmip6/pangeo-cmip6.json'

def fetch(url):
    r = requests.get(url, timeout=45)
    r.raise_for_status()
    return r

def member_order(value):
    return tuple(int(n) for n in re.findall(r'\d+', value))

def discover():
    OUT.mkdir(exist_ok=True)
    spec = fetch(CATALOG).json()
    (OUT / 'catalog_definition.json').write_text(json.dumps(spec, indent=2))
    path = OUT / 'catalog.csv'
    if not path.exists():
        path.write_bytes(fetch(spec['catalog_file']).content)
    df = pd.read_csv(path)
    subset = df[(df.variable_id == 'tas') & (df.table_id == 'Amon') & df.experiment_id.isin(EXPERIMENTS)]
    subset.to_csv(OUT / 'tas_catalog.csv', index=False)
    complete = subset.groupby(['source_id', 'member_id', 'grid_label']).experiment_id.nunique()
    complete = complete[complete == 4].reset_index()
    complete['order'] = complete.member_id.map(member_order)
    candidates = complete.sort_values(['source_id','grid_label','order']).drop_duplicates(['source_id','grid_label'])
    print(f'Found {len(complete)} compatible model/member/grid combinations across {complete.source_id.nunique()} models.', flush=True)
    def inspect(row):
        selected = subset[(subset.source_id == row.source_id) & (subset.member_id == row.member_id) & (subset.grid_label == row.grid_label)].sort_values('version').drop_duplicates('experiment_id', keep='last')
        record = {'model': row.source_id, 'member': row.member_id, 'grid': row.grid_label, 'sources': selected.astype(object).where(pd.notnull(selected),None).to_dict('records')}
        try:
            total = 0
            shapes = []
            for exp in EXPERIMENTS:
                source = selected[selected.experiment_id == exp].iloc[0]
                metadata = fetch(source.zstore.replace('gs://','https://storage.googleapis.com/') + '.zmetadata').json()['metadata']
                a = metadata['tas/.zarray']
                attrs = metadata['tas/.zattrs']
                dims = attrs['_ARRAY_DIMENSIONS']
                assert dims == ['time','lat','lon'] and attrs['units'] == 'K'
                shape, chunks = a['shape'], a['chunks']
                shapes.append(shape[1:])
                needed = (20 if exp == 'historical' else 86)*12
                touched = min(shape[0], math.ceil(needed/chunks[0])*chunks[0]+chunks[0])
                total += touched*shape[1]*shape[2]*np.dtype(a['dtype']).itemsize
            assert all(s == shapes[0] for s in shapes)
            record.update(status='metadata-compatible', shape=shapes[0], estimated_uncompressed_read_bytes=total)
        except Exception as exc:
            record.update(status='rejected', reason=str(exc))
        return record
    with ThreadPoolExecutor(max_workers=6) as pool:
        reports = list(pool.map(inspect, candidates.itertuples()))
    valid = sorted([r for r in reports if r['status'] == 'metadata-compatible'], key=lambda r:r['estimated_uncompressed_read_bytes'])
    (OUT / 'discovery_report.json').write_text(json.dumps({'catalog': CATALOG, 'compatible_combinations': len(complete), 'policy': 'One lowest-numbered complete member per model/grid is screened across all four experiments. Rank regular latitude/longitude grids by estimated uncompressed bytes touched, including time-chunk overhead. Then validate decoded coordinates, coverage, units and sample values; try subsequent candidates on failure. Byte estimates exclude compression and are approximate.', 'candidates': reports}, indent=2))
    (OUT / 'candidate_queue.json').write_text(json.dumps(valid, indent=2))
    print('Practical candidates by estimated read size:', flush=True)
    for r in valid[:10]:
        print(r['model'], r['member'], r['grid'], r['shape'], round(r['estimated_uncompressed_read_bytes']/1e6), 'MB uncompressed', flush=True)
    assert valid, 'No compatible accessible candidates'
    return valid

def validate(candidate):
    sources = pd.DataFrame(candidate['sources'])
    reference = None
    coverage = []
    for exp in EXPERIMENTS:
        row = sources[sources.experiment_id == exp].iloc[0]
        ds = xr.open_zarr(HTTPSStore(row.zstore), consolidated=True)
        assert ds.tas.attrs['units'] == 'K'
        assert ds.tas.dims == ('time','lat','lon')
        assert np.all(np.diff(ds.lat) > 0) and np.all(np.diff(ds.lon) > 0)
        assert ds.lat.min() >= -90 and ds.lat.max() <= 90
        assert np.allclose(np.diff(ds.lon), np.diff(ds.lon)[0])
        assert np.isclose(np.diff(ds.lon)[0]*len(ds.lon),360)
        bounds = ds[ds.lat.attrs['bounds']].values
        assert bounds.shape == (len(ds.lat),2)
        assert np.allclose(bounds[:-1,1],bounds[1:,0])
        assert np.isclose(bounds[0,0],-90) and np.isclose(bounds[-1,1],90)
        if exp == 'historical':
            spatial = {'latitude_bounds': bounds.tolist(), 'method':'Published latitude bounds supplied with the CMIP6 model; spherical strip area sin(north) − sin(south), with fractional overlap at region boundaries. Equal-width longitude cells.'}
        if reference is not None:
            np.testing.assert_array_equal(ds.lat, reference[0])
            np.testing.assert_array_equal(ds.lon, reference[1])
        reference = (ds.lat.values, ds.lon.values)
        start, end = (1995,2014) if exp == 'historical' else (2015,2100)
        a = ds.tas.sel(time=slice(f'{start}-01-01',f'{end}-12-31'))
        assert len(a.time) == (end-start+1)*12
        assert len(set(zip(a.time.dt.year.values,a.time.dt.month.values))) == len(a.time)
        sample = a.isel(time=0).compute()
        assert np.isfinite(sample).all() and float(sample.min()) > 150 and float(sample.max()) < 350
        item = {'experiment':exp,'available_start':str(ds.time.values[0]),'available_end':str(ds.time.values[-1]),'selected_years':[start,end],'sample_K_range':[float(sample.min()),float(sample.max())], 'zstore':row.zstore,'calendar':ds.time.encoding.get('calendar','unknown')}
        coverage.append(item)
        print(json.dumps(item), flush=True)
    candidate['coverage'] = coverage
    (OUT / 'spatial_bounds.json').write_text(json.dumps(spatial, indent=2))
    (OUT / 'selection.json').write_text(json.dumps(candidate, indent=2))
    sources.to_csv(OUT / 'selected_sources.csv', index=False)
    print('SELECTED:',candidate['model'],candidate['member'],candidate['grid'],flush=True)
    return candidate

if __name__ == '__main__':
    from process_data import run
    queue = discover()
    failures = []
    for candidate in queue:
        try:
            print('Validating candidate', candidate['model'], candidate['member'], flush=True)
            validate(candidate)
            run()
            break
        except Exception as exc:
            failures.append({'model':candidate['model'],'reason':str(exc)})
            (OUT/'access_failures.json').write_text(json.dumps(failures,indent=2))
            print('Candidate failed; trying next:', str(exc), flush=True)
    else:
        raise RuntimeError('All compatible candidates failed; see data/access_failures.json')
