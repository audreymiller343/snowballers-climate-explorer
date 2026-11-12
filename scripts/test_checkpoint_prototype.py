import json
import os
import threading
from datetime import datetime, timezone
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_browser import Handler

ROOT=Path(__file__).resolve().parents[1]

def run():
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=str(ROOT)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    base=f'http://127.0.0.1:{server.server_port}'
    checks,errors,failed=[],[],[]
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=os.environ.get('CHROME_PATH','/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'),headless=True)
            page=browser.new_page(viewport={'width':1200,'height':1000},reduced_motion='reduce')
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('response',lambda r:failed.append(f'{r.status}: {r.url}') if r.status>=400 else None)
            page.goto(base+'/checkpoint/prototype.html',wait_until='networkidle')
            page.wait_for_selector('.series')
            assert page.locator('.series').count()==4
            assert page.locator('.rate-card').count()==2
            assert page.locator('.draft-label').count()==0
            assert 'Is Winter Disappearing' in page.locator('h1').inner_text()
            assert page.locator('#error').is_hidden()
            checks.append('Draft page loads real data, four seasonal lines and two rate summaries')
            page.select_option('#region','Europe sector')
            assert all('Summer has the larger' in s for s in page.locator('.rate-answer').all_inner_texts())
            checks.append('Region control updates the data and summer-warming counterexample')
            page.select_option('#measure','gap')
            assert page.locator('.series').count()==2
            page.locator('.overlay').scroll_into_view_if_needed()
            box=page.locator('.overlay').bounding_box()
            page.mouse.move(box['x']+box['width']/2,box['y']+box['height']/2)
            assert page.locator('#tooltip').is_visible()
            assert 'Winter − summer anomaly' in page.locator('#tooltip').inner_text()
            checks.append('Gap view and pointer inspection work')
            page.locator('#chart svg').focus()
            before=page.locator('#tooltip b').inner_text()
            page.keyboard.press('ArrowRight')
            assert before!=page.locator('#tooltip b').inner_text()
            checks.append('Keyboard inspection works')
            page.uncheck('input[value=ssp245]')
            assert page.locator('.series').count()==1
            page.uncheck('input[value=ssp585]')
            assert page.locator('.series').count()==0 and page.locator('#empty').is_visible()
            checks.append('Scenario toggles and empty selection work')
            page.click('#reset')
            for selector,value in [('#start-year',2050),('#end-year',2070)]:
                page.locator(selector).evaluate('(el,value)=>{el.value=value;el.dispatchEvent(new Event("input",{bubbles:true}))}',str(value))
            assert '2050–2070' in page.locator('.rate-period').first.inner_text()
            checks.append('Year controls recompute the rates')
            page.click('#reset')
            assert page.locator('#region').input_value()=='North America sector'
            assert page.locator('#measure').input_value()=='anomaly'
            assert page.locator('.series').count()==4
            checks.append('Reset restores defaults')
            page.mouse.move(0,0)
            page.screenshot(path=str(ROOT/'checkpoint/prototype_draft_desktop.png'),full_page=True)
            page.set_viewport_size({'width':390,'height':844})
            page.wait_for_timeout(250)
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            assert page.locator('.overlay').bounding_box()['width']>150
            page.screenshot(path=str(ROOT/'checkpoint/prototype_draft_mobile.png'),full_page=True)
            checks.append('390px mobile draft fits viewport')
            page.set_viewport_size({'width':1200,'height':1000})
            page.goto(base+'/checkpoint/slides.html',wait_until='networkidle')
            assert page.locator('iframe').get_attribute('src')=='prototype.html'
            for _ in range(8): page.click('#next')
            assert page.locator('#counter').inner_text()=='9 / 10'
            assert page.frame_locator('iframe').locator('.series').count()==4
            checks.append('Slide 9 displays the working bare-bones prototype')
            assert page.request.get(base+'/').status==200
            assert not errors,errors
            assert not failed,failed
            checks.append('Polished main page remains available; no script or asset failures')
            browser.close()
    finally:
        server.shutdown()
    report={'passed':True,'scope':'bare-bones checkpoint prototype','timestamp_utc':datetime.now(timezone.utc).isoformat(),'checks':checks,'page_errors':errors,'failed_requests':failed}
    (ROOT/'checkpoint/prototype_draft_test_report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    run()
