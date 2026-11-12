import json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]

def run():
    meta = json.loads((ROOT/'data/metadata.json').read_text())
    df = pd.read_csv(ROOT/'data/temperature.csv')
    records = json.loads((ROOT/'data/temperature.json').read_text())
    pd.testing.assert_frame_equal(df,pd.DataFrame(records),check_exact=False,rtol=0,atol=1e-10)
    assert len(df) == 1668
    assert not df.duplicated(['region','scenario','year']).any()
    assert np.isfinite(df.anomaly).all()
    assert set(df.scenario) == {'historical','ssp126','ssp245','ssp585'}
    for (region,scenario),group in df.groupby(['region','scenario']):
        np.testing.assert_array_equal(group.year, np.arange(1995,2015) if scenario=='historical' else np.arange(2015,2101))
        if scenario == 'historical': assert abs(group.anomaly.mean()) < 1e-5
    bounds = np.array(json.loads((ROOT/'data/spatial_bounds.json').read_text())['latitude_bounds'])
    areas = np.sin(np.deg2rad(bounds[:,1]))-np.sin(np.deg2rad(bounds[:,0]))
    assert np.isclose(areas.sum(),2)
    regional_areas = []
    for r in meta['regions'][1:]:
        area = np.maximum(0,np.sin(np.deg2rad(np.minimum(bounds[:,1],r['north'])))-np.sin(np.deg2rad(np.maximum(bounds[:,0],r['south']))))
        regional_areas.append(area)
    np.testing.assert_allclose(np.sum(regional_areas,axis=0), areas,atol=1e-14)
    historical = xr.open_dataarray(ROOT/f'data/{meta["model"]}_{meta["member"]}_{meta["grid"]}_historical_annual.nc').load()
    baseline = historical.values.mean(axis=0)
    for scenario in ['historical','ssp126','ssp245','ssp585']:
        annual = xr.open_dataarray(ROOT/f'data/{meta["model"]}_{meta["member"]}_{meta["grid"]}_{scenario}_annual.nc').load()
        assert annual.attrs['units']=='K'
        assert np.isfinite(annual.values).all()
        assert annual.values.min()>150 and annual.values.max()<350
        for i,r in enumerate(meta['regions']):
            weights = areas if i==0 else regional_areas[i-1]
            independently_averaged = np.average((annual.values-baseline).mean(axis=2),axis=1,weights=weights)
            actual = df[(df.region==r['name']) & (df.scenario==scenario)].anomaly.values
            np.testing.assert_allclose(actual, independently_averaged,atol=5.1e-6,rtol=0)
    for scenario in ['ssp126','ssp245','ssp585']:
        bands = df[(df.scenario==scenario)&(df.region!='Global')].pivot(index='year',columns='region',values='anomaly')
        fractions = [np.sin(np.deg2rad(r['north']))/2-np.sin(np.deg2rad(r['south']))/2 for r in meta['regions'][1:]]
        recombined = bands[[r['name'] for r in meta['regions'][1:]]].values @ np.array(fractions)
        np.testing.assert_allclose(recombined,df[(df.scenario==scenario)&(df.region=='Global')].anomaly,atol=1.1e-5,rtol=0)
    figures = sorted((ROOT/'checkpoint/figures').glob('*.png'))
    assert len(figures)==6
    for path in figures:
        with Image.open(path) as im:
            assert im.size==(2560,1440)
            assert np.array(im).std()>10
    report = {'passed': True,'timestamp_utc': datetime.now(timezone.utc).isoformat(),'model':meta['model'],'member':meta['member'],'records':len(df),'checks':['CSV/JSON agreement','Unique scenario/region/year records','Complete 1995–2014 historical and 2015–2100 scenario coverage','Finite and plausible annual Kelvin values','Zero historical regional baseline means','Published cell bounds cover globe and band fractions sum to each cell','Independent NumPy recomputation of every regional annual anomaly','Area-weighted bands reconstruct global anomalies','Six nonblank 2560×1440 PNG figures'], 'caveat':'Annual month-day weighting is executed and asserted in preprocessing. This offline validation independently checks spatial aggregation from annual caches, not all remote monthly inputs.'}
    (ROOT/'data/validation.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    run()
