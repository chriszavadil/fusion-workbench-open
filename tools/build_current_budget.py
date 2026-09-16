"""Project all completed inverse-budget values; no new solver execution. MIT."""
from pathlib import Path
import hashlib,json
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
def build(root=ROOT):
 ex=root/'research/source/experiments/inverse_current_budget_2026_09_16';records=[]
 for folder in sorted((ex/'runs').iterdir()):
  r=json.loads((folder/'RESULT.json').read_text());path=folder/'CURRENT_FIELDS.npz'
  if not r.get('completed') or not r.get('passed_numerical_checks'):raise ValueError('Incomplete or unchecked current case')
  if hashlib.sha256(path.read_bytes()).hexdigest()!=r['fields_sha256']:raise ValueError('Canonical current fields changed')
  with np.load(path) as z:a={k:z[k].tolist() for k in z.files}
  records.append({'id':r['id'],'summary':r['result'],'restoration':r['restoration'],'arrays':a,'canonical_fields_sha256':r['fields_sha256'],'canonical_source':folder.relative_to(root).as_posix(),'physical_validation':False})
 if len(records)!=4:raise ValueError('All four declared outcomes are required')
 packet={'schema':'fusion.inverse-current-view.v1','date':'2026-09-16','cases':records,'checks':json.loads((ex/'INDEPENDENT_CHECKS.json').read_text()),'scope':'New thermal bootstrap/current-budget diagnostic on earlier unqualified fixed-boundary proxies, not a full current-profile solution, achieved ECCD or measured power.','interval':[.01,.98],'reference_bootstrap_total_A':records[0]['summary']['original_bootstrap_total_A'],'original_inductive_total_A':records[0]['summary']['original_inductive_total_A'],'original_EC_total_A':records[0]['summary']['original_EC_total_A'],'whole_plasma_current_A':json.loads((ex/'KINETIC_INPUT.json').read_text())['reference_current']['plasma_current'],'physical_validation':False,'new_power_result':None,'candidate_current_qualified':False,'no_inductive_or_bootstrap_rescale':True}
 out=root/'docs/ec-wave/current-budget.json';out.write_text(json.dumps(packet,indent=2,allow_nan=False)+'\n',encoding='utf-8')
 return {'cases':len(records),'points_per_case':[len(c['arrays']['psi_norm']) for c in records],'bytes':out.stat().st_size,'new_power_result':None}
if __name__=='__main__':print(json.dumps(build()))
