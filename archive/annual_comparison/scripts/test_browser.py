import json
import os
import threading
from datetime import datetime, timezone
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

def run():
    checks, errors, failed_requests = [], [], []
    server = ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=str(ROOT)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    base=f'http://127.0.0.1:{server.server_port}'
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=os.environ.get('CHROME_PATH','/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'),headless=True)
            page=browser.new_page(viewport={'width':1440,'height':1100},reduced_motion='reduce')
            page.on('pageerror',lambda err:errors.append(str(err)))
            page.on('response',lambda r:failed_requests.append(f'{r.status}: {r.url}') if r.status>=400 else None)
            page.goto(base,wait_until='networkidle')
            page.wait_for_selector('.series')
            assert page.locator('.series').count()==4
            assert '2081–2100' in page.locator('#summary').inner_text()
            checks.append('Default chart: four series and calculated late-century summary')
            page.select_option('#region','Northern high latitudes')
            assert 'Northern high latitudes' in page.locator('#summary').inner_text()
            assert '60° to 90°' in page.locator('#bounds').inner_text()
            checks.append('Region selection updates data, bounds and summary')
            page.uncheck('input[value=ssp245]')
            assert page.locator('.series').count()==3
            assert 'SSP2-4.5:' not in page.locator('#summary').inner_text()
            checks.append('Scenario toggle removes series and summary value')
            def slider(id,value):
                page.locator(id).evaluate('(el,value)=>{el.value=value;el.dispatchEvent(new Event("input",{bubbles:true}))}',str(value))
            slider('#start-year',2050)
            assert page.locator('#start-output').inner_text()=='2050'
            assert page.locator('.series').count()==2
            slider('#end-year',2070)
            assert '2051–2070' in page.locator('#summary').inner_text()
            checks.append('Time sliders filter series and calculate matching 20-year summary')
            overlay=page.locator('.overlay').bounding_box()
            page.mouse.move(overlay['x']+overlay['width']*.5,overlay['y']+overlay['height']*.5)
            assert page.locator('#tooltip').is_visible()
            assert '2060' in page.locator('#tooltip').inner_text()
            assert 'SSP5-8.5' in page.locator('#tooltip').inner_text()
            checks.append('Pointer hover shows matching-year exact scenario values')
            page.locator('#chart svg').focus()
            page.keyboard.press('ArrowRight')
            assert '2061' in page.locator('#tooltip').inner_text()
            checks.append('Keyboard arrow inspection advances the inspected year')
            slider('#start-year',2099)
            assert page.locator('#start-output').inner_text()=='2069'
            checks.append('Crossed year controls clamp to a valid noninverted interval')
            page.uncheck('input[value=ssp126]')
            page.uncheck('input[value=ssp585]')
            assert page.locator('.series').count()==0
            assert page.locator('#empty').is_visible()
            assert 'No future scenarios selected' in page.locator('#summary').inner_text()
            checks.append('Empty scenario selection provides explicit usable state')
            page.click('#reset')
            assert page.locator('.series').count()==4
            assert page.locator('#region').input_value()=='Global'
            assert page.locator('#start-year').input_value()=='1995'
            assert page.locator('#end-year').input_value()=='2100'
            checks.append('Reset restores all controls and data')
            slider('#end-year',2014)
            assert page.locator('.series').count()==1
            assert 'historical simulations only' in page.locator('#summary').inner_text()
            checks.append('Historical-only window does not invent a scenario comparison')
            page.click('#reset')
            dataset=json.loads((ROOT/'data/temperature.json').read_text())
            expected=[d for d in dataset if d['region']=='Global' and d['scenario']=='ssp585' and d['year']>=2081]
            mean=sum(d['anomaly'] for d in expected)/len(expected)
            assert f'+{mean:.2f}' in page.locator('#summary').inner_text()
            checks.append('Displayed mean agrees with independently calculated fixture-free data value')
            page.screenshot(path=str(ROOT/'checkpoint/prototype_desktop.png'),full_page=True)
            page.set_viewport_size({'width':390,'height':844})
            page.wait_for_timeout(300)
            assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth')
            assert page.locator('.overlay').bounding_box()['width']>150
            page.screenshot(path=str(ROOT/'checkpoint/prototype_mobile.png'),full_page=True)
            checks.append('390px mobile layout fits viewport and retains operable chart')
            page.set_viewport_size({'width':1440,'height':1000})
            page.goto(base+'/checkpoint/slides.html',wait_until='networkidle')
            assert page.locator('.slide').count()==10
            assert page.locator('#counter').inner_text()=='1 / 10'
            page.click('#next')
            assert page.locator('#counter').inner_text()=='2 / 10'
            page.keyboard.press('ArrowRight')
            assert page.locator('.slide.active img').count()==1
            checks.append('Ten-slide checkpoint deck and keyboard/button navigation')
            for path in ['writeup.html','data/provenance.md','data/temperature.csv','checkpoint/checkpoint_script.md']:
                assert page.request.get(base+'/'+path).status==200
            checks.append('Write-up, provenance, CSV and script links resolve through HTTP')
            assert not errors,errors
            assert not failed_requests,failed_requests
            checks.append('No JavaScript page errors or failed HTTP asset requests')
            browser.close()
    finally:
        server.shutdown()
    report={'passed':True,'timestamp_utc':datetime.now(timezone.utc).isoformat(),'browser':'Installed Google Chrome, Playwright Chromium driver','checks':checks,'page_errors':errors,'failed_http_requests':failed_requests,'limitations':['Automated smoke tests do not replace screen-reader review or human usability testing.','No GitHub Pages deployment was performed.']}
    (ROOT/'checkpoint/test_report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    run()
