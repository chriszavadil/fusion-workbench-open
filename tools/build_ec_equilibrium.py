"""Project complete, scoped EC/equilibrium evidence into the static app. MIT."""
from pathlib import Path
import hashlib,json,math
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
EQ=ROOT/'research/source/experiments/ec_equilibrium_2026_09_16'
EC=ROOT/'research/source/experiments/ec_launch_2026_09_15'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def build():
 original=json.loads((EQ/'EXACT_INPUT.json').read_text(encoding='utf-8'));records=[]
 for directory in sorted((EQ/'runs').iterdir()):
  r=json.loads((directory/'RESULT.json').read_text(encoding='utf-8'))
  if r.get('error') or not r.get('export_completed') or not r['matched_integrals']:raise ValueError('Unqualified numerical export: '+directory.name)
  if r['solution_sha256']!=sha(directory/'SOLUTION.npz'):raise ValueError('Solution hash changed')
  with np.load(directory/'SOLUTION.npz') as solution:
   r['boundary_rz_m']=solution['boundary'].tolist();r['psi_profile']=solution['profile_psi'].tolist();r['volume_rho_map_used']=solution['rho_volume_map_used'].tolist();r['pressure_Pa']=solution['pressure'].tolist();r['F_Tm']=solution['F'].tolist()
   r['mesh_nodes']=len(solution['points']);r['mesh_triangles']=len(solution['triangles'])
   r['derived_axis_Bt_T']=float(solution['F'][0]/r['magnetic_axis_m'][0])
  r['surfaces']=json.loads((directory/'SURFACES.json').read_text());r['canonical_solution_path']=(directory/'SOLUTION.npz').relative_to(ROOT).as_posix();records.append(r)
 comparison=[]
 for exponent in sorted({r['ffprime_exponent'] for r in records}):
  subset=sorted([r for r in records if r['ffprime_exponent']==exponent],key=lambda r:r['dx_m'],reverse=True);coarse,fine=subset
  comparison.append({'ffprime_exponent':exponent,'coarse_id':coarse['id'],'fine_id':fine['id'],'q95_relative_mesh_change':fine['q_sample'][3]/coarse['q_sample'][3]-1,'near_axis_q_relative_mesh_change':fine['q_sample'][0]/coarse['q_sample'][0]-1,'axis_shift_mesh_change_m':fine['axis_shift_from_geometric_center_m']-coarse['axis_shift_from_geometric_center_m'],'volume_relative_mesh_change':fine['volume_m3']/coarse['volume_m3']-1})
 ec=json.loads((EC/'RESULTS.json').read_text());reference=json.loads((EQ/'GENRAY_REFERENCE.json').read_text())
 if ec['evaluation_count']!=len(ec['all_local_evaluations']) or ec['ray_runs']!=0:raise ValueError('Analytical scope mismatch')
 packet={'schema':'fusion.ec-equilibrium-view.v1','date':'2026-09-16','input':original,'cases':records,'mesh_comparisons':comparison,'analytic_screen':ec,'reference_ray':reference,'evidence_levels':{'analytic_local_seed_evaluations':ec['evaluation_count'],'force_balanced_proxy_cases':len(records),'candidate_ray_runs':0,'candidate_achieved_drive_A':None,'reference_ray_runs':1,'physical_validation':False,'native_binary_rebuilt':False},'limitations':['Smooth fixed boundary is not the single-null candidate separatrix or a PF-coil solution.','Fast pressure is assumed isotropic and co-shaped with thermal pressure; target total pressure energy is matched.','FF-prime shapes are declared closure sensitivities, not measured current profiles or uncertainty bounds.','Geometric-rho pressure is mapped to normalized enclosed volume; this mapping remains a declared physical profile assumption.','Near-axis q is evaluated at normalized poloidal flux0.01, not the exact magnetic axis.','Mesh agreement is numerical verification, not validation against a real plasma.','GENRAY reference uses a different canonical ITER plasma, not our candidate. No reference current is credited toward7.598MA.','No candidate launch/deposition/stability or remaining30MW control sufficiency has been demonstrated.'],'numerical_failures_preserved':json.loads((EQ/'IMPLEMENTATION_FAILURES.json').read_text()),'original_analytic_pressure_roundtrip':json.loads((EQ/'PRESSURE_REPLAY.json').read_text())}
 out=ROOT/'docs/ec-wave';out.mkdir(parents=True,exist_ok=True)
 data=(json.dumps(packet,indent=2,sort_keys=True,allow_nan=False)+'\n').encode('utf-8');(out/'data.json').write_bytes(data)
 (EQ/'SUMMARY.json').write_text(json.dumps({'date':packet['date'],'mesh_comparisons':comparison,'cases':[{k:r[k] for k in ['id','q_sample','q95_relative_difference','axis_shift_from_geometric_center_m','volume_relative_to_PROCESS','current_relative_error','energy_relative_error','mapping_converged','proxy_matches_reference_q_screen','derived_axis_Bt_T','solution_sha256','geqdsk_sha256']} for r in records],'candidate_qualified':False,'physical_validation':False},indent=2,sort_keys=True)+'\n')
 return {'cases':len(records),'analytic_points':len(ec['all_local_evaluations']),'reference_ray_points':reference['recorded_points'],'view_bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'candidate_qualified':False}
if __name__=='__main__':print(json.dumps(build()))
