"""Normal installed-Edge test of recorded current evidence; no physics execution. MIT."""
from pathlib import Path
import argparse,json,hashlib
from playwright.sync_api import sync_playwright,expect
p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--expected-revision');args=p.parse_args()
if args.base not in ['http://127.0.0.1:18797/','https://chriszavadil.github.io/fusion-workbench-open/']:raise ValueError('Unapproved test origin')
args.output.mkdir(parents=True,exist_ok=False);out={'passed':False,'security_changed':False,'scientific_jobs':0};errors=[];http=[]
try:
 with sync_playwright() as p:
  b=p.chromium.launch(channel='msedge',headless=True,chromium_sandbox=True);c=b.new_context(viewport={'width':1440,'height':1050},ignore_https_errors=False)
  r=c.request.get(args.base+'release-status.json');assert r.status==200;out['revision']=r.json()['revision_id']
  if args.base.startswith('https') and out['revision']!=args.expected_revision:raise ValueError('Wrong deployed revision')
  page=c.new_page();page.set_default_timeout(30000);page.on('pageerror',lambda e:errors.append(str(e)));page.on('response',lambda r:http.append(r.status) if r.status>=400 and r.url.startswith(args.base) else None)
  r=page.goto(args.base+'ec-wave/#current-budget',wait_until='networkidle',timeout=60000);assert r.status==200
  expect(page.locator('#current-headline')).to_contain_text('10.87');expect(page.locator('#current-reference')).to_contain_text('not two measurements')
  for i in range(4):
   page.locator('#current-case').select_option(str(i));expect(page.locator('#current-profile-chart [data-current-series]')).to_have_count(3);expect(page.locator('#current-summary')).to_contain_text('MA remaining')
  page.locator('#current-case').select_option('0');page.locator('#current-budget').screenshot(path=str(args.output/'current-profiles.png'))
  page.goto(args.base+'progress/',wait_until='networkidle');expect(page.locator('body')).to_have_attribute('data-progress-ready','true');expect(page.locator('#event-detail')).to_have_attribute('data-event','inverse-current-budget-20260916')
  expect(page.locator('#progress-chart [data-event]')).to_have_count(13)
  page.set_viewport_size({'width':390,'height':844});page.goto(args.base+'ec-wave/#current-budget',wait_until='networkidle');expect(page.locator('#current-headline')).to_contain_text('10.87')
  assert page.evaluate('() => document.documentElement.scrollWidth <= innerWidth + 1'),'Horizontal page overflow'
  assert not errors and not http,(errors,http);out.update(passed=True,browser=b.version,all_four_current_profiles=True,new_scientific_event=True,narrow_layout_no_overflow=True,physical_validation=False);b.close()
except Exception as e:out.update(error=type(e).__name__+': '+str(e))
finally:
 out.update(page_errors=errors,http_failures=http);(args.output/'RESULT.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
 if not out['passed']:raise SystemExit(1)
