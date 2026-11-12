import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from process_seasonal import trend

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'checkpoint/figures'
COLORS={'historical':'#637582','ssp245':'#dc942c','ssp585':'#c75064'}
LABELS={'historical':'Historical','ssp245':'SSP2-4.5','ssp585':'SSP5-8.5'}
SEASONS={'DJF':'Winter (DJF)','JJA':'Summer (JJA)'}
RATE_COLORS={'DJF':'#dc942c','JJA':'#587f99'}
REGIONAL_COLORS={'DJF':'#c75064','JJA':'#508d87'}
STYLES={'DJF':'-','JJA':'--'}
TITLES={
    1:'Winter and summer warming in the North America sector',
    2:'Winter vs. summer warming rates, 2015–2100',
    3:'Regional winter and summer warming, 2081–2100',
    4:'Where is the winter warming anomaly larger than summer’s?',
    5:'Winter–summer anomaly contrast by latitude, 2081–2100',
    6:'The winter–summer warming gap across regions and decades'
}

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    df=pd.read_csv(ROOT/'data/temperature.csv')
    meta=json.loads((ROOT/'data/metadata.json').read_text())
    regions=[r['name'] for r in meta['regions']]
    short=['N. America sector','Europe sector','Arctic']
    future=df[df.scenario!='historical']
    late=future[future.year.between(2081,2100)].groupby(['region','scenario','season']).anomaly.mean()
    rates=[]
    for (region,scenario,season),g in future.groupby(['region','scenario','season']):
        rates.append({'region':region,'scenario':scenario,'season':season,'rate':trend(g.year,g.anomaly)})
    rate_df=pd.DataFrame(rates)
    rate_df.to_csv(ROOT/'data/seasonal_rates.csv',index=False)
    rate=rate_df.set_index(['region','scenario','season']).rate
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold','figure.facecolor':'#fbfcfa','axes.facecolor':'#fbfcfa','savefig.facecolor':'#fbfcfa'})
    findings=[]
    def setup(title,panels=1):
        fig,axes=plt.subplots(1,panels,figsize=(12.8,7.2),squeeze=False)
        fig.suptitle(title,x=.07,ha='left',fontsize=18,weight='bold')
        fig.text(.07,.91,f'{meta["model"]} · {meta["member"]} · Separate DJF/JJA baselines: 1995–2014',color='#536571',fontsize=11)
        fig.subplots_adjust(left=.1,right=.94,top=.8,bottom=.25,wspace=.26)
        return fig,axes[0]
    def save(fig,n,slug,caption):
        fig.text(.07,.04,caption,fontsize=9,va='bottom')
        filename=f'{n:02d}_{slug}.png'
        fig.savefig(OUT/filename,dpi=200)
        plt.close(fig)
        findings.append({'number':n,'title':TITLES[n],'file':filename,'caption':caption})
    fig,axes=setup(f'01 / {TITLES[1]}')
    ax=axes[0]
    for scenario in COLORS:
        for season in SEASONS:
            g=df[(df.region==regions[0])&(df.scenario==scenario)&(df.season==season)]
            ax.plot(g.year,g.anomaly,color=COLORS[scenario],ls=STYLES[season],lw=1.8,label=f'{LABELS[scenario]} · {season}')
    ax.axhline(0,c='#c6d0cb',lw=1)
    ax.axvline(2014.5,c='#c6d0cb',ls=':')
    ax.set(xlabel='Season-year (DJF ends in labeled year)',ylabel='Seasonal temperature anomaly (°C)',xlim=(1995,2100))
    ax.legend(frameon=False,ncol=2,fontsize=9)
    w,s=late.loc[regions[0],'ssp585','DJF'],late.loc[regions[0],'ssp585','JJA']
    save(fig,1,'seasonal_timeline',f'North America sector, SSP5-8.5, 2081–2100: winter {w:.2f} °C; summer {s:.2f} °C; winter minus summer {w-s:+.2f} °C.\nSeason means weight months by calendar days; sector means use cell areas. Historical lines are simulations. Solid = DJF; dashed = JJA.')
    fig,axes=setup(f'02 / {TITLES[2]}',2)
    for ax,scenario in zip(axes,['ssp245','ssp585']):
        x=np.arange(3)
        for i,season in enumerate(SEASONS):
            ax.bar(x+(i-.5)*.32,[rate.loc[r,scenario,season] for r in regions],.32,color=RATE_COLORS[season],hatch=None if i==0 else '//',label=SEASONS[season])
        ax.set(xticks=x,xticklabels=short,ylabel='OLS warming rate (°C/decade)',title=LABELS[scenario],ylim=(0,float(rate_df.rate.max())*1.2))
        ax.tick_params(axis='x',labelsize=9)
        ax.legend(frameon=False,fontsize=9)
    contrast=rate.loc['Arctic','ssp585','DJF']-rate.loc['Arctic','ssp585','JJA']
    save(fig,2,'seasonal_rates',f'Arctic SSP5-8.5 winter trend: {rate.loc["Arctic","ssp585","DJF"]:.3f} °C/decade; summer: {rate.loc["Arctic","ssp585","JJA"]:.3f}; difference: {contrast:+.3f}.\nOrdinary least-squares trends over the same 86 season-years, 2015–2100. No uncertainty interval or significance test is estimated.')
    fig,axes=setup(f'03 / {TITLES[3]}',2)
    maxval=float(late.max())*1.16
    for ax,scenario in zip(axes,['ssp245','ssp585']):
        x=np.arange(3)
        for i,season in enumerate(SEASONS):
            ax.bar(x+(i-.5)*.32,[late.loc[r,scenario,season] for r in regions],.32,color=REGIONAL_COLORS[season],hatch=None if i==0 else '//',label=SEASONS[season])
        ax.set(xticks=x,xticklabels=short,ylabel='2081–2100 mean anomaly (°C)',title=LABELS[scenario],ylim=(0,maxval))
        ax.tick_params(axis='x',labelsize=9)
        ax.legend(frameon=False,fontsize=9)
    contrasts={r:float(late.loc[r,'ssp585','DJF']-late.loc[r,'ssp585','JJA']) for r in regions}
    largest=max(contrasts,key=contrasts.get)
    save(fig,3,'regional_seasons',f'Largest winter-minus-summer anomaly contrast among these regions under SSP5-8.5: {largest}, {contrasts[largest]:+.2f} °C.\nBars average 20 complete seasons, 2081–2100. Geographic sectors include land and ocean; Arctic overlaps parts of the other sectors.')
    winter=xr.open_dataarray(ROOT/'data/ssp585_DJF_seasonal_late.nc').load()
    summer=xr.open_dataarray(ROOT/'data/ssp585_JJA_seasonal_late.nc').load()
    difference=(winter-summer).assign_coords(lon=((winter.lon+180)%360)-180).sortby('lon')
    north=difference.sel(lat=slice(0,90))
    fig,axes=setup(f'04 / {TITLES[4]}')
    ax=axes[0]
    cyclic=xr.concat([north,north.isel(lon=slice(0,1)).assign_coords(lon=[180.])],dim='lon')
    bounds=json.loads((ROOT/'data/seasonal_bounds.json').read_text())
    lat_bounds=np.array(bounds['latitude'])[winter.lat.values>=0]
    lat_edges=np.r_[lat_bounds[:,0],lat_bounds[-1,1]]
    lon_step=float(np.diff(cyclic.lon)[0])
    lon_edges=np.r_[cyclic.lon.values-lon_step/2,cyclic.lon.values[-1]+lon_step/2]
    limit=float(np.abs(north).max())
    im=ax.pcolormesh(lon_edges,lat_edges,cyclic,cmap='RdBu_r',vmin=-limit,vmax=limit,shading='flat')
    ax.set(xlabel='Longitude (° east)',ylabel='Latitude (° north)',xlim=(-180,180),ylim=(0,90))
    fig.colorbar(im,ax=ax,label='DJF anomaly − JJA anomaly (°C)',pad=.025)
    save(fig,4,'seasonal_spatial_contrast',f'Northern Hemisphere grid-cell SSP5-8.5 seasonal anomaly contrast spans {float(north.min()):+.2f} to {float(north.max()):+.2f} °C in 2081–2100.\nRed = larger winter anomaly; blue = larger summer anomaly. Each season uses its own historical baseline. This is not a trend-rate map.')
    fig,axes=setup(f'05 / {TITLES[5]}')
    ax=axes[0]
    for scenario in ['ssp245','ssp585']:
        a=xr.open_dataarray(ROOT/f'data/{scenario}_DJF_seasonal_late.nc')
        b=xr.open_dataarray(ROOT/f'data/{scenario}_JJA_seasonal_late.nc')
        zonal=(a-b).mean('lon').sel(lat=slice(0,90))
        ax.plot(zonal.lat,zonal,color=COLORS[scenario],label=LABELS[scenario],lw=2.3)
    ax.axhline(0,c='#83958b',lw=1,ls=':')
    ax.set(xlabel='Latitude (° north)',ylabel='2081–2100 DJF − JJA anomaly (°C)',xlim=(0,90))
    ax.legend(frameon=False)
    a245=late.loc['Arctic','ssp245','DJF']-late.loc['Arctic','ssp245','JJA']
    a585=late.loc['Arctic','ssp585','DJF']-late.loc['Arctic','ssp585','JJA']
    save(fig,5,'seasonal_latitude_profile',f'Arctic area-mean seasonal anomaly contrast: {a245:+.2f} °C under SSP2-4.5 and {a585:+.2f} °C under SSP5-8.5.\nCurves are equal-width longitude means at each native latitude. Positive values indicate a larger winter warming anomaly, not necessarily a faster local trend.')
    fig,axes=setup(f'06 / {TITLES[6]}')
    ax=axes[0]
    p=future[(future.scenario=='ssp585')&future.year.between(2021,2100)].pivot(index=['region','year'],columns='season',values='anomaly')
    p['gap']=p.DJF-p.JJA
    p=p.reset_index()
    p['decade']=(p.year-2021)//10*10+2021
    matrix=p.groupby(['region','decade']).gap.mean().unstack().loc[regions]
    limit=float(abs(matrix).max().max())
    im=ax.imshow(matrix,cmap='RdBu_r',aspect='auto',vmin=-limit,vmax=limit)
    ax.set(xticks=np.arange(8),xticklabels=[f'{y}–\n{y+9}' for y in matrix.columns],yticks=np.arange(3),yticklabels=short,xlabel='Ten-year period',ylabel='Geographic region')
    fig.subplots_adjust(left=.18)
    fig.colorbar(im,ax=ax,label='SSP5-8.5 DJF − JJA anomaly (°C)',pad=.025)
    for i in range(3):
        for j in range(8):
            v=matrix.iloc[i,j]
            ax.text(j,i,f'{v:+.1f}',ha='center',va='center',color='white' if abs(v)>limit*.55 else '#283d42',fontsize=10)
    save(fig,6,'seasonal_region_decade',f'Arctic SSP5-8.5 winter-minus-summer anomaly contrast: {matrix.loc["Arctic"].iloc[0]:+.2f} °C in 2021–2030; {matrix.loc["Arctic"].iloc[-1]:+.2f} °C in 2091–2100.\nEach cell averages ten complete season-year pairs. A positive contrast measures unequal warming since baseline, not the literal loss of winter.')
    (ROOT/'data/findings.json').write_text(json.dumps(findings,indent=2))
    text=f'# Seasonal exploratory findings\n\n{meta["model"]}, member {meta["member"]}. DJF and JJA each use their own 1995–2014 baseline. All findings describe one realization.\n\n'
    for f in findings:
        text+=f'## Figure {f["number"]} — {f["title"]}\n\n![Figure {f["number"]}](figures/{f["file"]})\n\n{f["caption"]}\n\n'
    (ROOT/'checkpoint/checkpoint_findings.md').write_text(text)
    print(text)

if __name__=='__main__':
    run()
