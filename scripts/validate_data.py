import json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]

def run():
    meta=json.loads((ROOT/'data/metadata.json').read_text())
    df=pd.read_csv(ROOT/'data/temperature.csv')
    records=json.loads((ROOT/'data/temperature.json').read_text(),parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
    pd.testing.assert_frame_equal(df,pd.DataFrame(records),check_exact=False,rtol=0,atol=1e-10)
    assert len(df)==1152 and meta['records']==1152
    assert not df.duplicated(['region','scenario','season','year']).any()
    assert np.isfinite(df.anomaly).all()
    assert set(df.season)=={'DJF','JJA'} and set(df.scenario)=={'historical','ssp245','ssp585'}
    for (_,scenario,season),g in df.groupby(['region','scenario','season']):
        expected=np.arange(1995,2015) if scenario=='historical' else np.arange(2015,2101)
        np.testing.assert_array_equal(g.year,expected)
        if scenario=='historical': assert abs(g.anomaly.mean())<1e-6
    bounds=json.loads((ROOT/'data/seasonal_bounds.json').read_text())
    lat_b=np.array(bounds['latitude'])
    lon_b=np.array(bounds['longitude'])
    assert np.allclose(lat_b[:-1,1],lat_b[1:,0])
    assert np.allclose(lon_b[:-1,1],lon_b[1:,0])
    areas=(np.sin(np.deg2rad(lat_b[:,1]))-np.sin(np.deg2rad(lat_b[:,0])))[:,None]*np.deg2rad(lon_b[:,1]-lon_b[:,0])[None,:]
    assert np.isclose(areas.sum(),4*np.pi)
    independent_weights={}
    for r in meta['regions']:
        north=np.minimum(lat_b[:,1],r['north'])
        south=np.maximum(lat_b[:,0],r['south'])
        latitude=np.where(north>south,np.sin(np.deg2rad(north))-np.sin(np.deg2rad(south)),0)
        longitude=np.zeros(len(lon_b))
        for shift in [-360,0,360]:
            west=np.maximum(lon_b[:,0]+shift,r['west'])
            east=np.minimum(lon_b[:,1]+shift,r['east'])
            longitude+=np.maximum(0,east-west)
        w=latitude[:,None]*np.deg2rad(longitude[None,:])
        analytic=np.deg2rad(r['east']-r['west'])*(np.sin(np.deg2rad(r['north']))-np.sin(np.deg2rad(r['south'])))
        np.testing.assert_allclose(w.sum(),analytic,rtol=1e-13,atol=1e-14)
        independent_weights[r['name']]=w
    caches={s['experiment']:xr.open_dataset(ROOT/'data'/s['cache']).load() for s in meta['sources']}
    for scenario,field in caches.items():
        expected=np.arange(1995,2015) if scenario=='historical' else np.arange(2015,2101)
        np.testing.assert_array_equal(field.year,expected)
        for season in ['DJF','JJA']:
            assert field[season].attrs['units']=='K'
            a=field[season].values
            assert np.isfinite(a).all() and a.min()>150 and a.max()<350
            baseline=caches['historical'][season].values.mean(axis=0)
            for region,weights in independent_weights.items():
                expected_values=np.sum((a-baseline)*weights[None,:,:],axis=(1,2))/weights.sum()
                actual=df[(df.region==region)&(df.scenario==scenario)&(df.season==season)].anomaly.values
                np.testing.assert_allclose(actual,expected_values,rtol=0,atol=5.1e-7)
    rate_df=pd.read_csv(ROOT/'data/seasonal_rates.csv')
    for row in rate_df.itertuples():
        g=df[(df.region==row.region)&(df.scenario==row.scenario)&(df.season==row.season)]
        independent_rate=np.polyfit(g.year.to_numpy(),g.anomaly.to_numpy(),1)[0]*10
        np.testing.assert_allclose(row.rate,independent_rate,rtol=0,atol=1e-12)
    p=df[df.scenario!='historical'].pivot(index=['region','scenario','year'],columns='season',values='anomaly')
    assert p.notna().all().all() and len(p)==516
    for scenario in ['ssp245','ssp585']:
        for region in [r['name'] for r in meta['regions']]:
            q=p.loc[region,scenario]
            gap_rate=np.polyfit(q.index.to_numpy(),(q.DJF-q.JJA).to_numpy(),1)[0]*10
            r=rate_df[(rate_df.region==region)&(rate_df.scenario==scenario)].set_index('season').rate
            np.testing.assert_allclose(gap_rate,r.DJF-r.JJA,atol=1e-12,rtol=0)
    figures=sorted((ROOT/'checkpoint/figures').glob('*.png'))
    assert len(figures)==6
    for path in figures:
        with Image.open(path) as im:
            assert im.size==(2560,1440) and np.array(im).std()>10
    assert 'disappearing' in meta['title'].lower()
    report={'passed':True,'scope':'seasonal DJF/JJA, two scenarios, three regions','timestamp_utc':datetime.now(timezone.utc).isoformat(),'model':meta['model'],'records':len(df),'checks':['CSV and strict JSON agreement','1152 finite, unique scenario/region/season/year values','Complete DJF/JJA season-year coverage and separate zero-mean historical baselines','Published grid-cell bounds span the globe','Every regional weight sum matches its analytic spherical area, including longitude wrap','Independent NumPy regional recomputation agrees with every seasonal anomaly','All seasonal fields have plausible Kelvin values','Independent NumPy polyfit reproduces all 12 default warming rates','Winter and summer have identical matching future years','Slope of seasonal anomaly gap equals difference of seasonal slopes','Six nonblank 2560×1440 seasonal PNG figures'],'limitations':['Raw month-boundary verification is reported separately in remote_validation.json.','Tests do not establish ensemble uncertainty or statistical significance.']}
    (ROOT/'data/validation.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    run()
