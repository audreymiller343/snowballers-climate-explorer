import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'checkpoint/figures'
COLORS = {'historical': '#637582', 'ssp126': '#168b82', 'ssp245': '#dc942c', 'ssp585': '#c75064'}
LABELS = {'historical': 'Historical simulation', 'ssp126': 'SSP1-2.6', 'ssp245': 'SSP2-4.5', 'ssp585': 'SSP5-8.5'}

def run():
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(ROOT / 'data/temperature.csv')
    meta = json.loads((ROOT / 'data/metadata.json').read_text())
    regions = [r['name'] for r in meta['regions']]
    future = df[df.scenario != 'historical']
    late = future[future.year.between(2081, 2100)].groupby(['region', 'scenario']).anomaly.mean().unstack()
    findings = []
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11, 'axes.spines.top': False, 'axes.spines.right': False, 'axes.titleweight': 'bold', 'figure.facecolor': '#fbfcfa', 'axes.facecolor': '#fbfcfa', 'savefig.facecolor': '#fbfcfa'})
    def setup(title):
        fig, ax = plt.subplots(figsize=(12.8, 7.2))
        fig.suptitle(title, x=.08, ha='left', fontsize=19, weight='bold')
        fig.text(.08, .91, f'{meta["model"]} · {meta["member"]} · Temperature anomaly relative to 1995–2014', color='#536571')
        fig.subplots_adjust(left=.12, right=.94, top=.82, bottom=.24)
        return fig, ax
    def save(fig, number, slug, caption):
        fig.text(.08, .045, caption, fontsize=9, va='bottom', wrap=True)
        fig.savefig(OUT / f'{number:02d}_{slug}.png', dpi=200)
        plt.close(fig)
        findings.append({'number': number, 'file': f'{number:02d}_{slug}.png', 'caption': caption})
    fig, ax = setup('01 / A historical baseline, then three possible trajectories')
    for s in COLORS:
        a = df[(df.region == 'Global') & (df.scenario == s)]
        ax.plot(a.year, a.anomaly, label=LABELS[s], color=COLORS[s], linewidth=2)
    ax.axhline(0, color='#c5cecc', lw=1)
    ax.axvline(2014.5, color='#c5cecc', ls=':')
    ax.set(xlabel='Year', ylabel='Global temperature anomaly (°C)', xlim=(1995,2100))
    ax.legend(frameon=False, fontsize=9)
    hist = df[(df.region == 'Global') & (df.scenario == 'historical')]
    save(fig, 1, 'global_timeline', f'Global historical anomalies range from {hist.anomaly.min():.2f} to {hist.anomaly.max():.2f} °C during 1995–2014.\nMonthly means are day-weighted within years; global means use spherical cell areas. Historical data are model simulations.')
    fig, ax = setup('02 / Scenario separation grows over the century')
    for s in list(COLORS)[1:]:
        a = future[(future.region == 'Global') & (future.scenario == s)]
        ax.plot(a.year, a.anomaly, color=COLORS[s], label=LABELS[s], lw=2)
    ax.set(xlabel='Year', ylabel='Global temperature anomaly (°C)', xlim=(2015,2100))
    ax.legend(frameon=False)
    early = future[(future.region == 'Global') & future.year.between(2021,2040)].groupby('scenario').anomaly.mean()
    gap = late.loc['Global','ssp585'] - late.loc['Global','ssp126']
    save(fig, 2, 'scenario_comparison', f'The SSP5-8.5 minus SSP1-2.6 global gap is {early.ssp585-early.ssp126:.2f} °C in 2021–2040 and {gap:.2f} °C in 2081–2100.\nLines are day-weighted annual, area-weighted global means. These are conditional projections from one realization.')
    fig, ax = setup('03 / Late-century warming differs across latitude bands')
    short = ['Global','60–90°N','30–60°N','30°S–30°N','30–60°S','60–90°S']
    x = np.arange(6)
    for i,s in enumerate(list(COLORS)[1:]):
        ax.bar(x+(i-1)*.24, late.loc[regions,s], width=.24, color=COLORS[s], label=LABELS[s])
    ax.set(xticks=x, xticklabels=short, ylabel='2081–2100 mean anomaly (°C)', xlabel='Latitude band (land and ocean)')
    ax.legend(frameon=False)
    top = late.ssp585.idxmax()
    save(fig,3,'regional_warming',f'Under SSP5-8.5, {top.lower()} have the largest band mean: {late.loc[top,"ssp585"]:.2f} °C; global: {late.loc["Global","ssp585"]:.2f} °C.\nBars average annual anomalies over 2081–2100, with spherical area weighting and fractional band-edge cells.')
    field = xr.open_dataarray(ROOT / 'data/ssp585_late_century.nc').load()
    field = field.assign_coords(lon=((field.lon+180)%360)-180).sortby('lon')
    fig, ax = setup('04 / The spatial pattern behind the SSP5-8.5 average')
    cyclic = xr.concat([field,field.isel(lon=slice(0,1)).assign_coords(lon=[180.0])],dim='lon')
    lon_step = float(np.diff(cyclic.lon)[0])
    lon_edges = np.r_[cyclic.lon.values-lon_step/2,cyclic.lon.values[-1]+lon_step/2]
    lat_bounds = np.array(json.loads((ROOT/'data/spatial_bounds.json').read_text())['latitude_bounds'])
    lat_edges = np.r_[lat_bounds[:,0],lat_bounds[-1,1]]
    im = ax.pcolormesh(lon_edges, lat_edges, cyclic, cmap='YlOrRd', shading='flat', vmin=0)
    ax.set(xlabel='Longitude (° east)', ylabel='Latitude (° north)', xlim=(-180,180), ylim=(-90,90))
    fig.colorbar(im, ax=ax, label='2081–2100 anomaly (°C)', pad=.025)
    save(fig,4,'spatial_warming',f'Grid-cell 2081–2100 SSP5-8.5 anomalies span {float(field.min()):.2f} to {float(field.max()):.2f} °C.\nThis is a latitude–longitude spatial heatmap, with no coastline overlay. Cell-wise baseline subtraction precedes equal-year averaging.')
    fig, ax = setup('05 / Zonal warming reveals a north–south contrast')
    for s in list(COLORS)[1:]:
        field_s = xr.open_dataarray(ROOT / f'data/{s}_late_century.nc')
        ax.plot(field_s.lat, field_s.mean('lon'), color=COLORS[s], label=LABELS[s], lw=2)
    ax.set(xlabel='Latitude (° north; negative = south)', ylabel='2081–2100 zonal mean anomaly (°C)', xlim=(-90,90))
    ax.legend(frameon=False)
    north, south = late.loc['Northern high latitudes','ssp585'], late.loc['Southern high latitudes','ssp585']
    save(fig,5,'latitude_profile',f'SSP5-8.5 warms the 60–90°N band by {north:.2f} °C and the 60–90°S band by {south:.2f} °C: a {north-south:.2f} °C difference.\nEach curve averages equal-width longitude cells at each native latitude, then averages annual anomalies over 2081–2100.')
    fig, ax = setup('06 / Regional change accumulates across future decades')
    decade_data = future[future.scenario == 'ssp585'].copy()
    decade_data['period'] = ((decade_data.year - 2021)//10)*10+2021
    decade_data = decade_data[decade_data.year.between(2021,2100)]
    matrix = decade_data.groupby(['region','period']).anomaly.mean().unstack().loc[regions]
    im = ax.imshow(matrix, cmap='YlOrRd', aspect='auto', vmin=0)
    ax.set(xticks=np.arange(8), xticklabels=[f'{y}–\n{y+9}' for y in matrix.columns], yticks=np.arange(6), yticklabels=short, xlabel='Ten-year period', ylabel='Latitude band')
    fig.colorbar(im,ax=ax,label='SSP5-8.5 mean anomaly (°C)',pad=.025)
    for i in range(6):
        for j in range(8):
            v=matrix.iloc[i,j]
            ax.text(j,i,f'{v:.1f}',ha='center',va='center',color='white' if v>matrix.max().max()*.58 else '#372a20',fontsize=9)
    save(fig,6,'region_decade',f'Under SSP5-8.5, global warming rises from {matrix.loc["Global"].iloc[0]:.2f} °C in 2021–2030 to {matrix.loc["Global"].iloc[-1]:.2f} °C in 2091–2100.\nCells average ten day-weighted annual anomalies with spherical area weighting. All periods contain ten complete years.')
    (ROOT/'data/findings.json').write_text(json.dumps(findings,indent=2))
    text = f'# Exploratory findings\n\nAll results use {meta["model"]}, {meta["member"]}, relative to 1995–2014. They describe one simulated realization.\n\n'
    for f in findings:
        text += f'## Figure {f["number"]}\n\n![Figure {f["number"]}](figures/{f["file"]})\n\n{f["caption"]}\n\n'
    (ROOT/'checkpoint/checkpoint_findings.md').write_text(text)
    print(text)

if __name__ == '__main__':
    run()
