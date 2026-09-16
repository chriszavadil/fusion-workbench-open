"""Release-test adapter checks; these do not replace the recorded real-browser run."""
from pathlib import Path
import ast,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
def test_browser_runner_keeps_security_and_revision_gate():
 text=(ROOT/'tools/verify_live_browser.py').read_text(encoding='utf-8');ast.parse(text)
 assert "channel='msedge'" in text and 'chromium_sandbox=True' in text
 assert 'ignore_https_errors=False' in text and 'args.expected_revision' in text
 assert 'wait_for_function' not in text and "not_to_have_value('0'" in text
 assert 'bypass_csp' not in text and '--disable-web-security' not in text
 assert 'storage_state' not in text and 'scientific_jobs_submitted' in text

def test_recorded_success_has_real_browser_and_all_screenshots():
 base=ROOT/'docs/validation/browser-20260916';record=json.loads((base/'RESULT.json').read_text())
 assert record['passed'] and record['browser_channel']=='msedge'
 assert not record['security_settings_changed'] and not record['signed_in_profile_used']
 assert record['page_errors']==[] and record['http_failures']==[]
 assert len(record['pages'])==4 and record['scientific_jobs_submitted']==0
 for name,digest in record['artifacts'].items():
  assert (base/name).is_file() and hashlib.sha256((base/name).read_bytes()).hexdigest()==digest

def test_homepage_punctuation_source_not_double_decoded():
 text=(ROOT/'tools/pages/overview.html').read_text(encoding='utf-8')
 assert '\u00c2\u00b7' not in text and '\u00e2\u2020\u2019' not in text
 assert 'Power history & real-world tests \u2192' in text

def test_current_report_distinguishes_environment_from_application():
 text=(ROOT/'docs/BROWSER_VERIFICATION_2026-09-16.md').read_text(encoding='utf-8')
 assert 'inside the ChatGPT container' in text and 'test-adapter error' in text
 assert 'not a physical iPhone test' in text and 'No new scientific' in text
