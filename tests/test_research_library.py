"""Reader completeness, safe content handling and candidate-isolation checks."""
from pathlib import Path
import hashlib,importlib.util,json,sys
import pytest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import build_research_library as lib
P=ROOT/'app/data/research_library.json';DATA=json.loads(P.read_text(encoding='utf-8'))

def test_identical_native_browser_packet():
 assert P.read_bytes()==(ROOT/'native/Content/WorkbenchData/research_library.json').read_bytes()
def test_all_reviewed_reports_are_readable():
 expected={r['published_path'] for r in json.loads((ROOT/'research/SNAPSHOT_MANIFEST.json').read_text())['records']}
 found={p for r in DATA['records'] for p in [r['source_path']]+r.get('duplicate_source_paths',[])}
 assert expected<=found and len(expected)==39
 assert len(DATA['records'])>=60
@pytest.mark.parametrize('row',DATA['records'],ids=lambda r:r['id'])
def test_full_text_and_hash_preserved(row):
 raw=(ROOT/row['source_path']).read_bytes();assert row['body']==raw.decode('utf-8-sig')
 assert row['content_sha256']==hashlib.sha256(raw).hexdigest()
 assert row['physical_validation'] is False
 assert len(row['id'])==23

def test_superseded_and_current_work_visible():
 prior=next(r for r in DATA['records'] if 'INTEGRATED_CANDIDATE_PATH_' in r['source_path'])
 assert prior['status']=='superseded' and '406.5' in prior['scope_notice']
 now=next(r for r in DATA['records'] if 'CONFINEMENT_NORMALIZATION_' in r['source_path'])
 assert now['status']=='current update' and now['configuration_scope']=='r838 r900'
def test_coverage_does_not_claim_every_raw_run():
 assert not DATA['coverage']['all_historical_raw_runs_integrated']
 assert not DATA['coverage']['private_correspondence_included']
 assert not DATA['physical_validation']
@pytest.mark.parametrize('url',['file:///etc/passwd','javascript:alert(1)','http://x.invalid/a','https://u:p@x.invalid/a','https://x.invalid/?token=abcd'])
def test_unsafe_external_links_rejected(url):assert not lib.safe_url(url)
def test_public_primary_link_allowed():assert lib.safe_url('https://doi.org/10.1088/example')
def test_changed_reviewed_report_rejected(tmp_path):
 p=tmp_path/'x.md';p.write_text('# Changed\n')
 with pytest.raises(ValueError,match='hash changed'):lib.entry(p,tmp_path,{}, {'x.md':{'published_sha256':'0'*64}})
def test_browser_does_not_interpret_html():
 js=(ROOT/'app/web/research.js').read_text();assert 'innerHTML' not in js and 'textContent=r.body' in js
 assert 'POST' not in js and 'eval(' not in js

def test_search_and_filter_do_not_replace_configuration():
 cpp=(ROOT/'native/Source/FusionWorkbench/FusionResearch.cpp').read_text()
 assert 'SelectConfiguration(' not in cpp
 assert 'ResearchMatches' in cpp and 'ParseIntoArrayWS' in cpp
 assert 'ResearchRecords.Num()>=39' in cpp

def test_full_source_narrative_inventory_accounted_for():
 c=json.loads((ROOT/'research/READER_COVERAGE.json').read_text())
 assert c['tracked_markdown_documents']==64
 assert c['included_scientific_markdown_documents']==57
 assert len(c['withheld_correspondence_access_records'])==7
 assert c['all_scientific_markdown_in_current_source_accounted_for']
 assert not c['raw_runs_fully_integrated']
