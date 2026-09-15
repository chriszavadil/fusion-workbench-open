"""Offline research reader index. Original code MIT; no private raw data."""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path
from urllib.parse import urlsplit
TRACKS=[('plasma',('confinement','plasma_normalization')),('magnets',('fatigue','solenoid')),('cooling',('cooling','flow_balance','header','circulator','circuits')),('fuel',('fuel','material','surface','recovery')),('control',('freegs','tokamaker','observer','mast','protection','hidden_state','profile_disturbance')),('neutronics',('neutronic','breeding','neutron')),('systems',('plant','process_lifecycle','candidate'))]
SUPERSEDED={'INTEGRATED_CANDIDATE_PATH_2026-09-07.md':'Superseded: the 406.5 MW / 20,000-cycle construction failed the coupled audit.','CS_FATIGUE_GATE_2026-09-07.md':'Historical screen, superseded by adaptive-fatigue and full-framework lifetime studies.'}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def safe_url(t):
 try:
  u=urlsplit(t);return u.scheme=='https' and bool(u.hostname) and not u.username and not u.password and not re.search(r'(?i)(token|password|signature|api_key)=',u.query)
 except ValueError:return False
def entry(p,root,meta,provenance):
 raw=p.read_bytes();body=raw.decode('utf-8-sig');rel=p.relative_to(root).as_posix()
 if len(raw)>2000000:raise ValueError('Oversized record: '+rel)
 m=re.search(r'^#\s+(.+)$',body,re.M);dates=re.findall(r'20\d\d-\d\d-\d\d',p.name)
 track=next((name for name,words in TRACKS if any(w in rel.lower() for w in words)),'project');source=provenance.get(rel,{})
 if source and source['published_sha256']!=sha(raw):raise ValueError('Reviewed hash changed: '+rel)
 e={'id':'record-'+sha(rel.encode())[:16],'title':(m[1].strip() if m else p.stem.replace('_',' '))[:200],'date':dates[-1] if dates else 'Undated','track':track,'status':'scoped research record','configuration_scope':'reference_or_project','scope_notice':'Read this record in its original scope; not automatically a test of the displayed reactor.','source_sha256':source.get('source_sha256',sha(raw)),'privacy_transformed':source.get('privacy_transform_applied',False),'source_revision':'2adb4b5c925dfe7c5fc7c0ab887def3c92deb601' if source else 'reviewed continuation','external_sources':list(dict.fromkeys(u.rstrip('.,;') for u in re.findall(r'https://[^\s<>\)\]\"\']+',body) if safe_url(u)))[:40]}
 if p.name in SUPERSEDED:e.update(status='superseded',scope_notice=SUPERSEDED[p.name])
 e.update(meta.get(rel,{}));e.update(body=body,source_path=rel,content_sha256=sha(raw),physical_validation=False)
 return e
def build(root):
 root=root.resolve();manifest=json.loads((root/'research/SNAPSHOT_MANIFEST.json').read_text(encoding='utf-8'));prov={x['published_path']:x for x in manifest['records']}
 extra=root/'research/ADDITIONAL_REPORT_MANIFEST.json'
 if extra.exists():prov.update({x['published_path']:x for x in json.loads(extra.read_text(encoding='utf-8'))['records']})
 mp=root/'research/library_metadata.json';meta=json.loads(mp.read_text(encoding='utf-8')) if mp.exists() else {};paths=[]
 for parent in (root/'research/reports',root/'research/source/experiments',root/'docs'):
  for p in parent.rglob('*'):
   if p.is_symlink():raise ValueError('Symlink in research source')
   if not p.is_file() or any(x in {'.git','.local','__pycache__'} for x in p.relative_to(root).parts):continue
   if p.name.upper().startswith(('LICENSE','UPSTREAM_LICENSE')) or p.name.startswith('requirements') or p.name=='X_POST_DRAFT.txt':continue
   if p.suffix.lower() in {'.md','.txt'} or p.name=='KEY_RESULTS.json':paths.append(p)
 for rel in prov:
  if not (root/rel).is_file():raise ValueError('Reviewed report missing: '+rel)
 records=[];seen={}
 for p in sorted(set(paths)):
  e=entry(p,root,meta,prov)
  if e['content_sha256'] in seen:seen[e['content_sha256']].setdefault('duplicate_source_paths',[]).append(e['source_path']);continue
  seen[e['content_sha256']]=e;records.append(e)
 records.sort(key=lambda e:(e['date']!='Undated',e['date'],e['status']=='current update',e['title']),reverse=True)
 packet={'schema':'fusion.research-library.v1','updated_date':max((e['date'] for e in records if e['date']!='Undated'),default='Undated'),'records':records,'coverage':{'readable_records':len(records),'reviewed_reports':len(prov),'source_documents_included':len(paths),'historical_catalogued_artifacts':257,'all_historical_raw_runs_integrated':False,'private_correspondence_included':False,'third_party_paper_fulltexts_included':False,'description':'Full text of cleared reports, experiment notes/key summaries and application updates in this release. Scripts/raw datasets remain separate. Restricted or missing data are not fabricated.'},'physical_validation':False,'publication_status':'reviewed_snapshot; live deployment verified separately'}
 data=(json.dumps(packet,ensure_ascii=False,indent=2,sort_keys=True,allow_nan=False)+'\n').encode('utf-8')
 for target in (root/'app/data/research_library.json',root/'native/Content/WorkbenchData/research_library.json'):
  target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
 return {'records':len(records),'documents':len(paths),'bytes':len(data),'sha256':sha(data)}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);a=p.parse_args();print(json.dumps(build(a.root)))
