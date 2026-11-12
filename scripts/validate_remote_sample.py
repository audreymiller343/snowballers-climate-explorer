import json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import xarray as xr
from process_data import HTTPSStore

ROOT=Path(__file__).resolve().parents[1]

def run():
    meta=json.loads((ROOT/'data/metadata.json').read_text())
    historical_source=next(s for s in meta['sources'] if s['experiment']=='historical')
    history=xr.open_zarr(HTTPSStore(historical_source['zstore']),consolidated=True)
    dec2014=history.tas.sel(time=slice('2014-12-01','2014-12-31')).compute(num_workers=2)
    checks=[]
    cases=[('historical',1995,'DJF'),('ssp245',2015,'DJF'),('ssp585',2015,'DJF'),('ssp585',2100,'DJF'),('ssp585',2100,'JJA')]
    for scenario,year,season in cases:
        source=next(s for s in meta['sources'] if s['experiment']==scenario)
        ds=history if scenario=='historical' else xr.open_zarr(HTTPSStore(source['zstore']),consolidated=True)
        if season=='DJF':
            if year==2015 and scenario!='historical':
                a=xr.concat([dec2014,ds.tas.sel(time=slice('2015-01-01','2015-02-28'))],dim='time').compute(num_workers=2)
            else:
                a=ds.tas.sel(time=slice(f'{year-1}-12-01',f'{year}-02-28')).compute(num_workers=2)
            expected_months=[12,1,2]
            expected_years=[year-1,year,year]
        else:
            a=ds.tas.sel(time=slice(f'{year}-06-01',f'{year}-08-31')).compute(num_workers=2)
            expected_months=[6,7,8]
            expected_years=[year,year,year]
        np.testing.assert_array_equal(a.time.dt.month,expected_months)
        np.testing.assert_array_equal(a.time.dt.year,expected_years)
        assert len(a.time)==3 and a.attrs['units']=='K'
        expected=np.average(a.values,axis=0,weights=a.time.dt.days_in_month.values)
        cache=xr.open_dataset(ROOT/'data'/source['cache'])
        actual=cache[season].sel(year=year).values
        np.testing.assert_allclose(actual,expected,atol=1e-10,rtol=0)
        checks.append({'experiment':scenario,'season':season,'year':year,'source_months':[str(t) for t in a.time.values],'maximum_difference_K':float(np.max(np.abs(actual-expected)))})
        print('Verified',scenario,season,year,flush=True)
    report={'passed':True,'scope':'seasonal','timestamp_utc':datetime.now(timezone.utc).isoformat(),'method':'Independent NumPy day-weighted means from raw monthly fields, with explicit month/year assertions; includes both 2015 scenario/historical DJF joins. Samples cover every grid cell, not every season-year.','checks':checks}
    (ROOT/'data/remote_validation.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    run()
