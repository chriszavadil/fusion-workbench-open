"""Check the plain-language entry and actual recorded-particle playback. MIT.
Fresh unsigned-in Edge context; no security overrides, profiles, proxies or solver calls.
"""
from pathlib import Path
import argparse,hashlib,json,time
from playwright.sync_api import sync_playwright,expect
P=argparse.ArgumentParser();P.add_argument('--base',required=True);P.add_argument('--output',type=Path,required=True);P.add_argument('--expected-revision');args=P.parse_args()
BASE=args.base
if BASE not in ['http://127.0.0.1:18791/','https://chriszavadil.github.io/fusion-workbench-open/']:raise ValueError('Unapproved test site')
OUT=args.output;OUT.mkdir(parents=True,exist_ok=False);result={'passed':False,'base':BASE,'security_changed':False,'physical_validation':False};errors=[];failures=[]
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(channel='msedge',headless=True,chromium_sandbox=True);context=browser.new_context(viewport={'width':1440,'height':1050},ignore_https_errors=False)
  published=context.request.get(BASE+'release-status.json');assert published.status==200;revision=published.json()['revision_id'];result['published_revision']=revision
  if BASE.startswith('https:') and (not args.expected_revision or args.expected_revision!=revision):raise ValueError('Unexpected deployed revision')
  page=context.new_page();page.set_default_timeout(30000);page.on('pageerror',lambda e:errors.append(str(e)));page.on('response',lambda r:failures.append([r.url,r.status]) if r.status>=400 and r.url.startswith(BASE) else None)
  response=page.goto(BASE,wait_until='networkidle',timeout=60000);assert response and response.status==200 and page.url.startswith(BASE)
  expect(page.locator('.beginner-status')).to_contain_text('We have not produced fusion or generated electricity.')
  expect(page.locator('#beginner-viewport')).to_have_attribute('data-model','r838');expect(page.locator('#beginner-viewport canvas')).to_be_visible()
  assert not page.locator('.beginner-advanced').get_attribute('open');assert not page.locator('#power-summary-best').is_visible()
  page.locator('#beginner-rotate').click();expect(page.locator('#beginner-rotate')).to_have_text('Rotate the view')
  page.screenshot(path=str(OUT/'start-here.png'));page.locator('#beginner-viewport').screenshot(path=str(OUT/'reference-design.png'))
  page.locator('#beginner-watch').click();expect(page.locator('#transport')).to_have_class('view transport-view active');expect(page.locator('#transport-case')).to_have_value('4')
  expect(page.locator('#transport-field')).not_to_be_checked();expect(page.locator('#transport-play')).to_have_text('Pause')
  expect(page.locator('.transport-start-here')).to_contain_text('We begin this calculation with an assumed source of fusion neutrons.')
  before=page.locator('#transport-time').input_value();expect(page.locator('#transport-time')).not_to_have_value(before,timeout=5000)
  image1=page.locator('#transport-viewport').screenshot(path=str(OUT/'particles-frame-a.png'));page.wait_for_timeout(1300);image2=page.locator('#transport-viewport').screenshot(path=str(OUT/'particles-frame-b.png'));assert hashlib.sha256(image1).digest()!=hashlib.sha256(image2).digest()
  page.screenshot(path=str(OUT/'particle-experiment.png'));result['recorded_case']=page.locator('#transport-viewport').get_attribute('data-recorded-case');result['marker_status']=page.locator('#transport-plain-clock').inner_text()
  page.locator('#transport-play').click();expect(page.locator('#transport-play')).to_have_text('Play');page.locator('#transport-time').fill('180');page.locator('#transport-time').dispatch_event('input');expect(page.locator('#transport-plain-clock')).to_contain_text('Paused')
  page.goto(BASE+'#watch',wait_until='networkidle');expect(page.locator('#transport-case')).to_have_value('4')
  page.goto(BASE+'#design',wait_until='networkidle');expect(page.locator('#device')).to_have_class('view active')
  page.goto(BASE,wait_until='networkidle');page.set_viewport_size({'width':390,'height':844});expect(page.locator('#beginner-viewport canvas')).to_be_visible()
  page.locator('#beginner-rotate').click();page.screenshot(path=str(OUT/'start-mobile.png'),full_page=True)
  assert not errors,errors;assert not failures,failures
  result.update(passed=True,whole_reference_mesh_visible=True,hypothetical_score_not_headline=True,actual_recorded_particle_frames_changed=True,controls_and_direct_links_passed=True,narrow_viewport_rendered=True,browser=browser.version,scientific_jobs=0)
  browser.close()
except Exception as e:
 result.update(error_type=type(e).__name__,error=str(e))
finally:
 result.update(page_errors=errors,http_failures=failures);(OUT/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result));
 if not result['passed']:raise SystemExit(1)
