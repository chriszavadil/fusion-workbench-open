"""Static deployment checks: no backend, no workstation access, complete evidence."""
from pathlib import Path
import hashlib,json,re,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'docs'
def test_static_index_and_no_jekyll():
 assert (SITE/'index.html').exists() and (SITE/'.nojekyll').exists()
 html=(SITE/'index.html').read_text(encoding='utf-8')
 assert 'Content-Security-Policy' in html and "connect-src 'self'" in html
 assert not re.search(r'(?:src|href)="/(?!/)',html)
 assert 'app-public.js' in html and 'PUBLISHED SNAPSHOT' in html

def test_no_backend_or_local_machine_requests_in_deployed_javascript():
 for name in ['app-public.js','viewer.js','research.js','neutronics.js','transport-lab.js','pages.js']:
  text=(SITE/name).read_text(encoding='utf-8')
  assert not any(x in text for x in ["fetch('/api/",'127.0.0.1','localhost',"method:'POST'","api(`/api/"])
  assert "fetch('/" not in text

def test_all_scientific_data_byte_identical_to_reviewed_app():
 for name in ['catalog.json','neutronics.json','research_library.json','transport_lab.json','source_context.bin']:
  assert (SITE/'data'/name).read_bytes()==(ROOT/'app/data'/name).read_bytes()
 assert len(json.loads((SITE/'data/research_library.json').read_text(encoding='utf-8'))['records'])>=84

def test_snapshot_not_live_compute_or_experimental_success():
 s=json.loads((SITE/'release-status.json').read_text());assert s['snapshot_only'] and not s['solver_hosted']
 assert any('Experimental' in r['title'] and r['status']=='Not established' for r in s['readiness'])
 assert s['data_date']==json.loads((ROOT/'app/data/research_library.json').read_text(encoding='utf-8'))['updated_date'] and s['public_collaboration_open']

def test_feed_has_dated_evidence_not_future_promise():
 tree=ET.parse(SITE/'feed.xml');ns={'a':'http://www.w3.org/2005/Atom'}
 entries=tree.findall('a:entry',ns);assert len(entries)>=5
 assert all(e.find('a:updated',ns) is not None and e.find('a:summary',ns) is not None for e in entries)
