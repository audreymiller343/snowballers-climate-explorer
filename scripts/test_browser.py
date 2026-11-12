import json
import os
import threading
from datetime import datetime, timezone
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import numpy as np
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]

class Handler(SimpleHTTPRequestHandler):
    def log_message(self,*args):
        pass

def run():
    records=json.loads((ROOT/'data/temperature.json').read_text())
    checks,errors,failed_requests=[],[],[]
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=str(ROOT)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    base=f'http://127.0.0.1:{server.server_port}'
    def rate(region,scenario,season,start=2015,end=2100):
        g=[d for d in records if d['region']==region and d['scenario']==scenario and d['season']==season and start<=d['year']<=end]
        return np.polyfit([d['year'] for d in g],[d['anomaly'] for d in g],1)[0]*10
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=os.environ.get('CHROME_PATH','/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'),headless=True)
            page=browser.new_page(viewport={'width':1440,'height':1150},reduced_motion='reduce')
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('response',lambda r:failed_requests.append(f'{r.status}: {r.url}') if r.status>=400 else None)
            page.goto(base,wait_until='networkidle')
            page.wait_for_selector('.series')
            assert 'Is Winter Disappearing' in page.title()
            assert page.locator('.series').count()==4
            assert page.locator('#rate-cards .rate-card').count()==2
            assert page.locator('.series[data-season=JJA]').count()==2
            assert page.locator('.series[data-season=JJA]').first.get_attribute('stroke-dasharray')=='7 5'
            assert '2081–2100' in page.locator('#summary').inner_text()
            checks.append('New title, two scenarios, four seasonal lines, dashed summer and trend cards load')
            for scenario in ['ssp245','ssp585']:
                expected=rate('North America sector',scenario,'DJF')-rate('North America sector',scenario,'JJA')
                card=page.locator(f'.rate-card[data-scenario={scenario}]')
                assert f'{expected:+.3f}' in card.inner_text()
            checks.append('Both default seasonal rate differences agree with independent NumPy polyfit')
            page.select_option('#region','Arctic')
            assert '66.5–90°N' in page.locator('#bounds').inner_text()
            assert 'Arctic' in page.locator('#summary').inner_text()
            expected=rate('Arctic','ssp585','DJF')
            assert f'{expected:+.3f}' in page.locator('.rate-card[data-scenario=ssp585]').inner_text()
            checks.append('Arctic data, bounds, summary and independent winter rate update')
            page.select_option('#region','Europe sector')
            assert page.locator('.rate-answer').count()==2
            assert all('Summer has the larger' in t for t in page.locator('.rate-answer').all_inner_texts())
            checks.append('Europe counterexample correctly reports larger summer rate for both scenarios')
            page.uncheck('input[value=ssp245]')
            assert page.locator('.series').count()==2
            assert page.locator('.rate-card').count()==1
            checks.append('Scenario toggle removes both seasonal lines and matching trend card')
            page.select_option('#measure','gap')
            assert page.locator('.series').count()==1
            assert page.locator('.series').get_attribute('data-season')=='gap'
            assert 'Winter − summer' in page.locator('#chart-description').inner_text()
            checks.append('Anomaly-gap view replaces seasonal pairs with matched-year differences')
            def slider(selector,value):
                page.locator(selector).evaluate('(el,value)=>{el.value=value;el.dispatchEvent(new Event("input",{bubbles:true}))}',str(value))
            slider('#start-year',2050)
            slider('#end-year',2070)
            assert '2051–2070' in page.locator('#summary').inner_text()
            assert '2050–2070' in page.locator('.rate-period').inner_text()
            expected=rate('Europe sector','ssp585','DJF',2050,2070)-rate('Europe sector','ssp585','JJA',2050,2070)
            assert f'{expected:+.3f}' in page.locator('.rate-difference').inner_text().replace('−','-')
            checks.append('Year filters recompute matching means and rates on explicitly distinct windows')
            page.locator('.overlay').scroll_into_view_if_needed()
            page.wait_for_timeout(150)
            overlay=page.locator('.overlay').bounding_box()
            page.mouse.move(overlay['x']+overlay['width']*.5,overlay['y']+overlay['height']*.5)
            assert page.locator('#tooltip').is_visible()
            w=next(d for d in records if d['region']=='Europe sector' and d['scenario']=='ssp585' and d['season']=='DJF' and d['year']==2060)['anomaly']
            s=next(d for d in records if d['region']=='Europe sector' and d['scenario']=='ssp585' and d['season']=='JJA' and d['year']==2060)['anomaly']
            assert '2060' in page.locator('#tooltip').inner_text()
            assert f'{w-s:+.2f}' in page.locator('#tooltip').inner_text().replace('−','-')
            checks.append('Gap hover reports the exact seasonal difference from source data')
            page.locator('#chart svg').focus()
            page.keyboard.press('ArrowRight')
            assert '2061' in page.locator('#tooltip').inner_text()
            checks.append('Keyboard inspection advances one season-year')
            slider('#end-year',2068)
            assert 'Only 19 complete' in page.locator('.rate-card').inner_text()
            assert page.locator('.rate-difference').count()==0
            slider('#end-year',2069)
            assert page.locator('.rate-difference').count()==1
            checks.append('Rates suppressed for 19 years and enabled at the 20-year minimum')
            slider('#start-year',2099)
            assert page.locator('#start-year').input_value()=='2068'
            checks.append('Crossed sliders clamp to a valid interval')
            page.uncheck('input[value=ssp585]')
            assert page.locator('.series').count()==0
            assert page.locator('#empty').is_visible()
            assert page.locator('.rate-card').count()==0
            checks.append('Empty selection removes future lines/cards and gives guidance')
            page.click('#reset')
            assert page.locator('#region').input_value()=='North America sector'
            assert page.locator('#measure').input_value()=='anomaly'
            assert page.locator('#start-year').input_value()=='2015'
            assert page.locator('#end-year').input_value()=='2100'
            assert page.locator('.series').count()==4
            checks.append('Reset restores the complete seasonal default state')
            slider('#start-year',1995)
            assert page.locator('.series').count()==6
            slider('#end-year',2014)
            assert page.locator('.series').count()==2
            assert page.locator('.rate-card').count()==0
            assert 'historical simulations only' in page.locator('#summary').inner_text()
            checks.append('Historical seasons display in gray without invented future rates')
            page.click('#reset')
            page.locator('.overlay').scroll_into_view_if_needed()
            overlay=page.locator('.overlay').bounding_box()
            page.mouse.move(overlay['x']+overlay['width']*.5,overlay['y']+overlay['height']*.5)
            tip=page.locator('#tooltip').inner_text()
            assert 'Winter' in tip and 'Summer' in tip
            assert all(f'{scenario} · {season}:' in tip for scenario in ['SSP2-4.5','SSP5-8.5'] for season in ['Winter','Summer'])
            checks.append('Seasonal hover identifies all four exact season/scenario values')
            point=page.locator('.series').first.evaluate('el => { const p=el.getPointAtLength(el.getTotalLength()/2); const q=new DOMPoint(p.x,p.y).matrixTransform(el.getScreenCTM()); return {x:q.x,y:q.y}; }')
            page.mouse.move(point['x'],point['y'])
            assert 'Highlighted:' in page.locator('#tooltip').inner_text()
            assert '1995–2014' in page.locator('#tooltip').inner_text()
            assert page.locator('.series[stroke-width="4"]').count()==1
            page.locator('#start-year').evaluate('(el)=>{el.value=1995;el.dispatchEvent(new Event("input",{bubbles:true}))}')
            assert page.locator('.experiment-boundary line').count()==1
            assert 'Historical ends 2014' in page.locator('.experiment-boundary').text_content()
            page.click('#reset')
            assert page.locator('.experiment-boundary').count()==0
            checks.append('TA feedback: labeled historical/projection boundary and line-specific hover details with highlighting')
            page.mouse.move(0,0)
            page.screenshot(path=str(ROOT/'checkpoint/prototype_desktop.png'),full_page=True)
            page.select_option('#region','Arctic')
            page.screenshot(path=str(ROOT/'checkpoint/prototype_arctic.png'),full_page=True)
            page.click('#reset')
            page.set_viewport_size({'width':390,'height':844})
            page.wait_for_timeout(300)
            assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth')
            assert page.locator('.overlay').bounding_box()['width']>150
            assert page.locator('#measure').is_visible()
            page.screenshot(path=str(ROOT/'checkpoint/prototype_mobile.png'),full_page=True)
            checks.append('390px mobile layout fits and retains chart, comparison control and rates')
            page.set_viewport_size({'width':1440,'height':1000})
            page.goto(base+'/checkpoint/slides.html',wait_until='networkidle')
            assert page.locator('.slide').count()==10 and page.locator('.slide.figure img').count()==6
            assert 'Is Winter Disappearing' in page.locator('.slide.active h1').inner_text()
            page.click('#next')
            assert page.locator('#counter').inner_text()=='2 / 10'
            page.keyboard.press('ArrowRight')
            assert page.locator('.slide.active img').count()==1
            checks.append('Seasonal checkpoint deck contains six figures, live prototype and working navigation')
            for path in ['writeup.html','data/provenance.md','data/temperature.csv']:
                assert page.request.get(base+'/'+path).status==200
            checks.append('Write-up page and seasonal provenance/data resolve')
            assert not errors,errors
            assert not failed_requests,failed_requests
            checks.append('No JavaScript page errors or failed HTTP asset requests')
            browser.close()
    finally:
        server.shutdown()
    report={'passed':True,'scope':'seasonal revision','timestamp_utc':datetime.now(timezone.utc).isoformat(),'browser':'Installed Google Chrome with Playwright','checks':checks,'page_errors':errors,'failed_http_requests':failed_requests,'limitations':['No human usability or screen-reader evaluation.','No deployed GitHub Pages URL, MP4 audio/duration or Gradescope submission verified.']}
    (ROOT/'checkpoint/test_report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    run()
