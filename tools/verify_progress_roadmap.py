"""Real Edge verification of the reviewed progress snapshot. No security changes. MIT."""
from pathlib import Path
import argparse,hashlib,json
from playwright.sync_api import sync_playwright,expect
p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--expected-revision');a=p.parse_args()
if a.base not in ['http://127.0.0.1:18793/','https://chriszavadil.github.io/fusion-workbench-open/']:raise ValueError('Unapproved test URL')
OUT=a.output;OUT.mkdir(parents=True,exist_ok=False);R={'passed':False,'security_changed':False,'scientific_runs':0,'real_browser':True};errors=[];failed=[]
try:
 with sync_playwright() as p:
  b=p.chromium.launch(channel='msedge',headless=True,chromium_sandbox=True);c=b.new_context(viewport={'width':1440,'height':1050},ignore_https_errors=False)
  response=c.request.get(a.base+'release-status.json');assert response.status==200;revision=response.json()['revision_id']
  if a.base.startswith('https') and revision!=a.expected_revision:raise ValueError('Unexpected deployed revision')
  R['revision']=revision;page=c.new_page();page.set_default_timeout(30000);page.on('pageerror',lambda e:errors.append(str(e)));page.on('response',lambda r:failed.append([r.url,r.status]) if r.status>=400 and r.url.startswith(a.base) else None)
  response=page.goto(a.base+'progress/',wait_until='networkidle',timeout=60000);assert response.status==200;expect(page.locator('body')).to_have_attribute('data-progress-ready','true')
  expect(page.locator('#progress-chart [data-event]')).to_have_count(13);expect(page.locator('#event-detail')).to_have_attribute('data-event','inverse-current-budget-20260916')
  expect(page.locator('#latest-result')).to_contain_text('self-current')
  page.screenshot(path=str(OUT/'progress-desktop.png'));page.locator('#history').screenshot(path=str(OUT/'progress-graph.png'))
  for id in page.locator('#progress-chart [data-event]').evaluate_all('(nodes)=>nodes.map(n=>n.dataset.event)'):
   page.locator(f'#progress-chart [data-event="{id}"]').click();expect(page.locator('#event-detail')).to_have_attribute('data-event',id)
  page.locator('#support-work').uncheck();expect(page.locator('#progress-chart [data-event]')).to_have_count(9);page.locator('#support-work').check()
  expect(page.locator('#goals-list .goal')).to_have_count(6);page.locator('#goal-chart [data-goal="G3"]').click();expect(page.locator('#goal-G3')).to_be_in_viewport()
  expect(page.locator('#goal-G3')).to_contain_text('7.598 MA');expect(page.locator('#goals-list')).to_contain_text('No completion date established')
  page.locator('#goal-chart').screenshot(path=str(OUT/'goal-timeline.png'))
  page.locator('#prior-search').fill('redl');expect(page.locator('#prior-list .prior')).to_have_count(1);page.locator('#prior-list summary').click();expect(page.locator('#prior-list')).to_contain_text('Do not repeat:')
  page.locator('#prior-search').fill('');expect(page.locator('#prior-list .prior')).to_have_count(13)
  page.set_viewport_size({'width':390,'height':844});page.goto(a.base+'progress/',wait_until='networkidle');expect(page.locator('body')).to_have_attribute('data-progress-ready','true')
  assert page.evaluate('() => document.documentElement.scrollWidth <= innerWidth + 1'),'Page-level horizontal overflow'
  page.screenshot(path=str(OUT/'progress-mobile.png'),full_page=True)
  page.set_viewport_size({'width':1440,'height':1050});page.goto(a.base,wait_until='networkidle');expect(page.locator('#progress-overview-chart [data-event]')).to_have_count(13)
  expect(page.locator('#beginner-viewport canvas')).to_be_visible();page.locator('#progress-open').click();expect(page.locator('body')).to_have_attribute('data-progress-ready','true')
  assert not errors,errors;assert not failed,failed
  R.update(passed=True,browser=b.version,event_markers=13,goals=6,reuse_entries=13,interactive_filters=True,shared_homepage_graph=True,narrow_layout_no_page_overflow=True,scope='Real Edge desktop and narrow viewport, not a physical-device or comprehensive accessibility audit')
  b.close()
except Exception as e:R.update(error_type=type(e).__name__,error=str(e))
finally:
 R.update(page_errors=errors,http_failures=failed,artifacts={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*.png')});(OUT/'RESULT.json').write_text(json.dumps(R,indent=2)+'\n',encoding='utf-8');print(json.dumps(R))
 if not R['passed']:raise SystemExit(1)
