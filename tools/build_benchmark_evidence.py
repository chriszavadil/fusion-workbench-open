"""Publish full scoped benchmark evidence and prior-work register. No solver runs."""
from pathlib import Path
import argparse,hashlib,json
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def build(root=ROOT):
 root=root.resolve();e=root/'research/source/experiments/oktavian_lif_2026_09_14'
 result=json.loads((e/'KEY_RESULTS.json').read_text(encoding='utf-8'));manifest=json.loads((e/'UPSTREAM_MANIFEST.json').read_text(encoding='utf-8'))
 assert result['schema']=='fusion.lif-benchmark-comparison.v2' and not result['physical_reactor_validation']
 for row in manifest:assert sha(e/'upstream'/row['local_name'])==row['sha256'],row['local_name']
 reg=json.loads((root/'research/prior_work_register.json').read_text(encoding='utf-8'));assert reg['schema']=='fusion.prior-work-register.v1'
 assert len({x['id'] for x in reg['entries']})==len(reg['entries'])
 for entry in reg['entries']:
  for key in ['id','title','attribution','original_date','classification','our_status','our_use','already_known','do_not_repeat','reopen_when','reading_scope','license_scope','report_search']:assert entry.get(key),key
  assert entry['sources']
  for s in entry['sources']:
   u=urlsplit(s['url']);assert u.scheme=='https' and u.netloc and not u.username and not u.password
 packet={'schema':'fusion.lif-benchmark-view.v1','data_date':result['date'],'title':'OKTAVIAN LiF: calculation versus archived evidence','classification':'Reproduction of existing research; not a fusion discovery','result':result,'upstream_manifest':manifest,'attribution_markdown':(e/'ATTRIBUTION.md').read_text(encoding='utf-8'),'original_csvs':{name:(e/'upstream'/name).read_text(encoding='utf-8') for name in ['IAEA_Oktavian_LiF Neutron flux.csv','IAEA_Oktavian_LiF Gamma flux.csv']},'normalization_review':json.loads((e/'INDEPENDENT_NORMALIZATION_REVIEW.json').read_text(encoding='utf-8')),'result_sha256':sha(e/'KEY_RESULTS.json'),'report_search':'Existing lithium benchmark','physical_validation':False,'experimental_points_are_not_our_measurements':True,'native_executable_updated':False}
 for name,obj in [('lif_benchmark.json',packet),('prior_work.json',reg)]:
  raw=(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode('utf-8')
  for d in [root/'app/data',root/'native/Content/WorkbenchData']:(d/name).write_bytes(raw)
 return {'neutron_bins':len(result['spectra']['nspectrum']['energy_high_eV']),'photon_bins':len(result['spectra']['gspectrum']['energy_high_eV']),'prior_work_entries':len(reg['entries']),'all_bins_and_primary_csvs_retained':True,'native_binary_built':False}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT);a=p.parse_args();print(json.dumps(build(a.root)))
