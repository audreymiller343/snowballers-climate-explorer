import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
from process_data import HTTPSStore

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'data'
EXPERIMENTS = ['historical','ssp245','ssp585']
REGIONS = [
    {'name':'North America sector','south':25,'north':70,'west':-170,'east':-50,'description':'25–70°N, 170–50°W · rectangular sector · land + ocean'},
    {'name':'Europe sector','south':35,'north':70,'west':-10,'east':40,'description':'35–70°N, 10°W–40°E · rectangular sector · land + ocean'},
    {'name':'Arctic','south':66.5,'north':90,'west':-180,'east':180,'description':'66.5–90°N · all longitudes · land + ocean'}
]

def region_weights(lat_bounds,lon_bounds,region):
    lat_area = np.maximum(0,np.sin(np.deg2rad(np.minimum(lat_bounds[:,1],region['north'])))-np.sin(np.deg2rad(np.maximum(lat_bounds[:,0],region['south']))))
    overlap = np.zeros(len(lon_bounds))
    for offset in [-360,0,360]:
        overlap += np.maximum(0,np.minimum(lon_bounds[:,1]+offset,region['east'])-np.maximum(lon_bounds[:,0]+offset,region['west']))
    return lat_area[:,None]*np.deg2rad(overlap[None,:])

def seasonal_mean(monthly,season,start,end):
    month=monthly.time.dt.month
    years=monthly.time.dt.year
    keep=month.isin([12,1,2] if season=='DJF' else [6,7,8])
    a=monthly.where(keep,drop=True)
    season_year=years.where(keep,drop=True)+(a.time.dt.month==12 if season=='DJF' else 0)
    a=a.assign_coords(season_year=('time',season_year.values))
    days=a.time.dt.days_in_month
    count=a.time.groupby(a.season_year).count()
    result=(a*days).groupby('season_year').sum('time',skipna=False)/days.groupby(a.season_year).sum('time')
    result=result.sel(season_year=slice(start,end))
    np.testing.assert_array_equal(result.season_year,np.arange(start,end+1))
    assert bool((count.sel(season_year=slice(start,end))==3).all()),'Incomplete season'
    return result.rename(season_year='year')

def trend(years,values):
    x=np.asarray(years,dtype=float)
    y=np.asarray(values,dtype=float)
    return float(np.sum((x-x.mean())*(y-y.mean()))/np.sum((x-x.mean())**2)*10)

def run():
    selected=json.loads((OUT/'selection.json').read_text())
    model,member,grid=selected['model'],selected['member'],selected['grid']
    print('Seasonal selection:',model,member,grid,flush=True)
    sources={s['experiment_id']:s for s in selected['sources']}
    fields={}
    raw_meta=[]
    dec2014=None
    for exp in EXPERIMENTS:
        source=sources[exp]
        print(exp,source['zstore'],'1994-12–2014-12' if exp=='historical' else '2015-01–2100-12; DJF 2015 also uses historical December 2014',flush=True)
        ds=xr.open_zarr(HTTPSStore(source['zstore']),consolidated=True)
        assert ds.tas.attrs['units']=='K'
        if exp=='historical':
            lat_bounds=ds[ds.lat.attrs['bounds']].values
            lon_bounds=ds[ds.lon.attrs['bounds']].values
            lat,lon=ds.lat.values,ds.lon.values
            assert np.isclose((lat_bounds[:,1]-lat_bounds[:,0]).sum(),180)
            assert np.isclose((lon_bounds[:,1]-lon_bounds[:,0]).sum(),360)
            dec2014=ds.tas.sel(time=slice('2014-12-01','2014-12-31')).load()
            assert len(dec2014.time)==1
        else:
            np.testing.assert_array_equal(lat,ds.lat)
            np.testing.assert_array_equal(lon,ds.lon)
        cache=OUT/f'{model}_{member}_{grid}_{exp}_v{source["version"]}_seasonal.nc'
        if cache.exists():
            field=xr.open_dataset(cache).load()
        else:
            start,end=(1995,2014) if exp=='historical' else (2015,2100)
            monthly=ds.tas.sel(time=slice('1994-12-01' if exp=='historical' else '2015-01-01',f'{end}-12-31'))
            if exp!='historical':
                monthly=xr.concat([dec2014,monthly],dim='time')
            assert len(set(zip(monthly.time.dt.year.values,monthly.time.dt.month.values)))==len(monthly.time)
            field=xr.Dataset({s:seasonal_mean(monthly,s,start,end) for s in ['DJF','JJA']}).compute(num_workers=4)
            for s in ['DJF','JJA']:
                assert np.isfinite(field[s]).all() and float(field[s].min())>150 and float(field[s].max())<350
                field[s].attrs={'units':'K','season':s,'source':source['zstore']}
            field.attrs={'model':model,'member':member,'grid':grid,'source_version':str(source['version']),'calendar':ds.time.encoding.get('calendar','unknown')}
            field.to_netcdf(cache)
        fields[exp]=field
        raw_meta.append({'experiment':exp,'zstore':source['zstore'],'version':source['version'],'calendar':ds.time.encoding.get('calendar','unknown'),'available_start':str(ds.time.values[0]),'available_end':str(ds.time.values[-1]),'season_years':[int(field.year.min()),int(field.year.max())],'cache':cache.name,'cache_sha256':hashlib.sha256(cache.read_bytes()).hexdigest(),'license':ds.attrs.get('license','Not supplied'),'institution':ds.attrs.get('institution','CCCma')})
        print('Validated seasonal fields',exp,flush=True)
    records=[]
    weights={r['name']:xr.DataArray(region_weights(lat_bounds,lon_bounds,r),dims=('lat','lon'),coords={'lat':lat,'lon':lon}) for r in REGIONS}
    for exp,field in fields.items():
        for season in ['DJF','JJA']:
            baseline=fields['historical'][season].mean('year')
            anomaly=field[season]-baseline
            for region in REGIONS:
                series=anomaly.weighted(weights[region['name']]).mean(('lat','lon'))
                for year,value in zip(series.year.values,series.values):
                    records.append({'region':region['name'],'scenario':exp,'season':season,'year':int(year),'anomaly':round(float(value),6)})
            if exp!='historical':
                anomaly.sel(year=slice(2081,2100)).mean('year').to_netcdf(OUT/f'{exp}_{season}_seasonal_late.nc')
    frame=pd.DataFrame(records)
    assert len(frame)==1152
    assert frame[frame.scenario=='historical'].groupby(['region','season']).anomaly.mean().abs().max()<1e-6
    frame.to_csv(OUT/'temperature.csv',index=False)
    (OUT/'temperature.json').write_text(json.dumps(records,separators=(',',':'),allow_nan=False))
    bounds={'latitude':lat_bounds.tolist(),'longitude':lon_bounds.tolist()}
    (OUT/'seasonal_bounds.json').write_text(json.dumps(bounds,indent=2))
    meta={'title':'Is Winter Disappearing Faster Than Summer Is Warming?','research_question':'How do the rates of winter and summer warming differ across geographic regions, and how might these seasonal differences change under future emissions scenarios?','model':model,'member':member,'grid':grid,'variable':'tas','table':'Amon','source_units':'K','units':'°C anomaly','baseline':'1995–2014, separately for DJF and JJA','regions':REGIONS,'seasons':{'DJF':'Winter (December–February)','JJA':'Summer (June–August)'},'scenarios':['ssp245','ssp585'],'accessed_utc':datetime.now(timezone.utc).isoformat(),'sources':raw_meta,'records':len(records),'method':'Meteorological Northern Hemisphere seasons: DJF assigned to January/February year, JJA to calendar year. All three months required, weighted by calendar days. Winter 1995 uses December 1994. Winter 2015 joins historical December 2014 to scenario January–February 2015. Winter 2100 uses December 2099, not December 2100. Each cell’s season-specific mean of 20 seasons in 1995–2014 is subtracted. Regions use spherical area of published cell bounds, with fractional latitude and longitude overlap. Period means weight complete season-years equally. Warming rate is ordinary least-squares slope × 10, in °C/decade, with the same years for winter and summer. Trend displays require at least 20 consecutive future season-years.','limitations':'One model and member, no ensemble uncertainty or significance test. North America and Europe are rectangular sectors, not continent masks, and include ocean. Arctic overlaps the northern parts of the other sectors. No snow, frost-day or winter-length data are used. Disappearing is a narrative hook: this does not measure literal disappearance of winter. Spatially varying baseline is recent, not preindustrial. Seasonal anomaly difference is not the same measure as a warming-rate difference.'}
    (OUT/'metadata.json').write_text(json.dumps(meta,indent=2))
    print('Saved',len(records),'real seasonal regional records',flush=True)

if __name__=='__main__':
    run()
