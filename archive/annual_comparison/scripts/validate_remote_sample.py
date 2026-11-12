import json
from pathlib import Path
import numpy as np
import xarray as xr
from process_data import HTTPSStore

ROOT = Path(__file__).resolve().parents[1]

def run():
    meta = json.loads((ROOT/'data/metadata.json').read_text())
    checks = []
    for exp,year in [('historical',1995),('ssp585',2100)]:
        source = next(d for d in meta['sources'] if d['experiment']==exp)
        ds = xr.open_zarr(HTTPSStore(source['zstore']),consolidated=True)
        monthly = ds.tas.sel(time=slice(f'{year}-01-01',f'{year}-12-31')).compute(num_workers=2)
        assert monthly.shape[0]==12
        days=monthly.time.dt.days_in_month.values
        np.testing.assert_array_equal(days,[31,28,31,30,31,30,31,31,30,31,30,31])
        independently_averaged=np.average(monthly.values,axis=0,weights=days)
        annual=xr.open_dataarray(ROOT/f'data/{meta["model"]}_{meta["member"]}_{meta["grid"]}_{exp}_annual.nc').sel(year=year).values
        np.testing.assert_allclose(annual,independently_averaged,rtol=0,atol=1e-10)
        checks.append({'experiment':exp,'year':year,'raw_monthly_kelvin_range':[float(monthly.min()),float(monthly.max())],'maximum_annual_difference_K':float(np.max(abs(annual-independently_averaged)))})
    (ROOT/'data/remote_validation.json').write_text(json.dumps({'passed':True,'method':'Independent NumPy day-weighted annual means recomputed from twelve remote monthly fields, at every grid cell for the first selected historical year and last future year. Not an independent verification of every monthly source value.','checks':checks},indent=2))
    print(json.dumps(checks,indent=2))

if __name__=='__main__':
    run()
