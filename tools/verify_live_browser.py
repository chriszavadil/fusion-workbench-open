"""Authorized public-app verification in installed Edge. No policy changes. MIT.
Uses an isolated unsigned-in test context, normal TLS and browser sandbox.
An access/admin denial stops this run; no alternate channel, proxy or URL retry.
"""
from pathlib import Path
import argparse,hashlib,json,time
from playwright.sync_api import sync_playwright,expect
BASE='https://chriszavadil.github.io/fusion-workbench-open/'

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--output',type=Path,required=True)
 parser.add_argument('--expected-revision',required=True,help='Exact revision_id from docs/release-status.json')
 args=parser.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
 result={'schema':'fusion.real-browser-verification.v1','passed':False,'base_url':BASE,'pages':[],
         'browser_channel':'msedge','headless':True,'tls_errors_ignored':False,
         'browser_sandbox_enabled':True,'security_settings_changed':False,'signed_in_profile_used':False,
         'scientific_jobs_submitted':0,'retry_after_access_denial':False}
 start=time.monotonic();errors=[];failures=[]
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(channel='msedge',headless=True,chromium_sandbox=True)
   result['browser_version']=browser.version
   context=browser.new_context(viewport={'width':1440,'height':1000},ignore_https_errors=False)
   published=context.request.get(BASE+'release-status.json')
   assert published.status==200,'Publication metadata unavailable'
   revision=published.json()['revision_id']
   assert revision==args.expected_revision,'Unexpected deployed revision; stop rather than certify stale files'
   result['published_revision']=revision
   page=context.new_page();page.set_default_timeout(15000)
   page.on('pageerror',lambda e:errors.append(str(e)))
   page.on('response',lambda r:failures.append({'url':r.url,'status':r.status}) if r.status>=400 and r.url.startswith(BASE) else None)
   def visit(path):
    response=page.goto(BASE+path,wait_until='networkidle',timeout=45000)
    assert response and response.status==200, 'Public page did not return HTTP200'
    assert page.url.startswith(BASE),'Unexpected redirect; stop'
   visit('')
   expect(page.locator('#power-summary-best')).to_have_text('274.0 MW')
   expect(page.locator('#power-summary-reference')).to_have_text('213.7 MW')
   expect(page.locator('.power-summary-head a')).to_have_text('Power history & real-world tests \u2192')
   page.screenshot(path=str(out/'homepage-desktop.png'))
   result['pages'].append({'path':'/','homepage_scores_displayed':True})
   visit('power-progress/')
   expect(page.locator('#best-average')).to_have_text('274.0')
   expect(page.locator('#physical-output')).to_have_text('Not measured')
   expect(page.locator('#history-table tr')).to_have_count(12)
   expect(page.locator('#world-table tr')).to_have_count(11)
   page.locator('#show-excluded').check()
   page.locator('[data-history="retired-screen"]').click()
   expect(page.locator('#history-detail')).to_contain_text('Excluded')
   page.locator('#metric-select').select_option('flat_top_net_MW')
   page.locator('[data-history="pulsedFixedR30"]').click()
   expect(page.locator('#history-detail')).to_contain_text('501.659')
   for series in ['nif-energy','jet-energy','tokamak-peak']:
    page.locator('#world-series').select_option(series)
    expect(page.locator('#world-chart [data-world]').first).to_be_visible()
   page.locator('#world-series').select_option('jet-energy')
   page.locator('[data-world="jet-2023-energy"]').click()
   expect(page.locator('#world-detail')).to_contain_text('13.269')
   expect(page.locator('#world-detail')).to_contain_text('13.800')
   with page.expect_download() as download_info:page.locator('#export-history').click()
   download=download_info.value;download.save_as(out/'history.csv')
   csv=(out/'history.csv').read_text(encoding='utf-8');assert '406.53' in csv and 'steady200' in csv
   page.screenshot(path=str(out/'power-progress-desktop.png'),full_page=True)
   page.locator('#history').screenshot(path=str(out/'history-chart.png'))
   page.locator('#experiments').screenshot(path=str(out/'physical-results.png'))
   result['pages'].append({'path':'power-progress/','scores_and_history_verified':True,
    'all_three_physical_series_verified':True,'csv_export_verified':True})
   page.set_viewport_size({'width':390,'height':844})
   page.evaluate('window.scrollTo(0,0)')
   assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth+2'),'Page overflows mobile viewport'
   page.screenshot(path=str(out/'power-progress-mobile.png'),full_page=True)
   result['pages'][-1]['mobile_layout_checked']={'width':390,'height':844,'page_overflow':False}
   page.set_viewport_size({'width':1440,'height':1000})
   visit('ec-wave/')
   expect(page.locator('#equilibrium-select option')).to_have_count(4)
   for index in range(4):
    page.locator('#equilibrium-select').select_option(str(index))
    expect(page.locator('#eq-status')).to_contain_text('NOT PASSED')
   page.locator('#width').select_option('0.1');page.locator('#inclination').select_option('0.5')
   expect(page.locator('#analytic-status')).to_contain_text('7 of56')
   page.locator('#ray-progress').fill('1000')
   expect(page.locator('#ray-inspect')).to_contain_text('343/343')
   page.locator('#ray-progress').fill('0');page.locator('#ray-play').click()
   expect(page.locator('#ray-progress')).not_to_have_value('0',timeout=5000)
   page.locator('#ray-play').click()
   page.screenshot(path=str(out/'ec-wave-desktop.png'),full_page=True)
   result['pages'].append({'path':'ec-wave/','four_equilibria_verified':True,'analytic_filters_verified':True,'actual_ray_playback_verified':True})
   visit('plant-decision/')
   expect(page.locator('#case-select option')).to_have_count(2)
   page.locator('#case-select').select_option('1')
   expect(page.locator('#ledger-note')).to_contain_text('501.7')
   page.locator('#time').fill('1000')
   expect(page.locator('#time-inspect')).to_contain_text('-127.73')
   page.screenshot(path=str(out/'plant-decision-desktop.png'),full_page=True)
   result['pages'].append({'path':'plant-decision/','power_ledger_and_cycle_scrubber_verified':True})
   assert not errors,errors
   assert not failures,failures
   context.close();browser.close();result['passed']=True
 except Exception as exc:
  message=str(exc);result['error_type']=type(exc).__name__
  result['blocked']=any(s in message.lower() for s in ['blocked_by_administrator','access denied','not permitted','forbidden'])
  result['failure_detail']=message
 finally:
  result['elapsed_s']=round(time.monotonic()-start,3)
  result['page_errors']=errors;result['http_failures']=failures
  result['artifacts']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file()}
  (out/'RESULT.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
  print(json.dumps(result,ensure_ascii=False),flush=True)
 return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
