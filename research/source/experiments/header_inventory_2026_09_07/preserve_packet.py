"""Freeze the finished checkpoint files; no scientific calculations performed."""
from pathlib import Path
import json,hashlib,datetime
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,value):(HERE/name).write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
result=json.loads((HERE/'RESULT.json').read_text());flows=json.loads((HERE/'FLOW_RECHECK_RESULT.json').read_text())
rows=[]
for r,f in zip(result['results'],flows['results']):
    u=f['unbalanced'];b=f['restored_nominal']
    rows.append({'configuration':r['configuration'],'properties':r['choice'],'nominal_common_drop_Pa':r['known_common_pressure_Pa_after_nominal_balancing'],'nominal_remaining_Pa':r['remaining_common_external_pressure_Pa'],'header_coolant_m3':r['total_header_coolant_m3'],'header_steel_m3':r['total_header_shell_cap_steel_m3'],'inner_radii_m':{k:v['geometry']['inner_radius_m'] for k,v in r['branches'].items()},'nominal_balancing_Pa':r['additional_balancing_drop_Pa'],'unbalanced_common_drop_Pa':u['common_pressure_Pa'],'unbalanced_remaining_Pa':u['remaining_common_allowance_Pa'],'unbalanced_FW_peak_K':{k:u[k]['branch']['peak_K'] for k in ['IB','OB']},'nominal_balanced_FW_peak_K':None if b is None else {k:b[k]['branch']['peak_K'] for k in ['IB','OB']}})
key={'schema':'fusion.header-inventory-key-results.v1','date':'2026-09-07','project_parent':'91648db3ad2d6691dfe57f0b1b632ec20a36235a','upstream':'c0ae5b28649f2b20fb7efc7904628b6defe4151c','results':rows,'tests':{'focused_passed':19,'failed':0,'skipped':0,'all_repository_tests_run':False},'physical_manifold_validated':False,'reactor_power_recomputed':False,'TBR_computed':False,'scope':result['scope']}
key['integrated_with_newer_project_ref']='2629556074609ad89ee44e6e9bf0bf8e8e21ae6d'
key['preferred_topology']='Independent regional circuits retained; cross-region common-pressure balancing is comparator only.'
key['portable_replay']=json.loads((HERE/'PORTABLE_REPLAY_RESULT.json').read_text())
save('KEY_RESULTS.json',key)
native=ROOT/'PROCESS-v3.4.2'
paths=['process/models/fw.py','process/models/blankets/blanket_library.py','process/models/engineering/pumping.py','process/core/coolprop_interface.py']
files={str(p.relative_to(HERE)).replace('\\','/'):sha(p) for p in sorted(HERE.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and '.pytest_cache' not in p.parts and p.name not in ['MANIFEST.json'] and p.suffix!='.zip'}
manifest={'schema':'fusion.header-packet-manifest.v1','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'upstream_ref':key['upstream'],'files':files,'upstream_files':{name:sha(native/name) for name in paths},'physical_validation':False}
save('MANIFEST.json',manifest)
print(json.dumps({'files':len(files),'source_hashes_recorded':len(paths),'manifest_sha256':sha(HERE/'MANIFEST.json')}))
