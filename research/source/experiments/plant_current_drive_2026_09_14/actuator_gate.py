"""Necessary actuator requirements from frozen PROCESS results; original MIT.
No plant optimization, wave propagation, deposition, or current-profile solve.
"""
from pathlib import Path
import hashlib,json,math
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def evaluate(current_kA,efficiency_kA_MW,total_MW,reserve_MW):
 vals=[current_kA,efficiency_kA_MW,total_MW,reserve_MW]
 if any(isinstance(x,bool) or not math.isfinite(x) for x in vals):raise ValueError('Nonfinite or invalid value')
 if min(current_kA,efficiency_kA_MW,total_MW)<=0 or not 0<=reserve_MW<total_MW:raise ValueError('Invalid power/current bounds')
 required=current_kA/efficiency_kA_MW;slack=total_MW-reserve_MW-required
 return {'required_drive_MW':required,'reserved_heat_MW':reserve_MW,'remaining_power_after_reserve_MW':slack,'fixed_point_total_current_condition_met':slack>=-1e-8,'new_net_power_prediction':None}
def run():
 source=json.loads((HERE/'ACTUATOR_SCALARS.json').read_text(encoding='utf-8'));rows=[]
 for name,record in source.items():
  result=json.loads((HERE/'runs'/name/'RESULT.json').read_text(encoding='utf-8'));v=record['values']
  assert result['mfile_sha256']==record['mfile_sha256'] and result['numerically_converged']
  current=v['plasma_current']*v['f_c_plasma_auxiliary']/1000
  efficiency=v['eta_cd_hcd_primary']*1000
  assert abs(current-efficiency*v['p_hcd_primary_injected_mw'])<1e-7
  cap=v['p_hcd_injected_max'];reserve=v['p_hcd_primary_extra_heat_mw'];threshold=current/(cap-reserve)
  examples=[dict(efficiency_kA_per_MW=e,**evaluate(current,e,cap,reserve)) for e in [35.,40.,43.,46.]]
  rows.append({'case':name,'required_current_MA':current/1000,'booked_efficiency_kA_per_MW':efficiency,'minimum_efficiency_at_retained_reserve_kA_per_MW':threshold,'injected_ceiling_MW':cap,'retained_heat_only_allocation_MW':reserve,'model_normalized_gamma':v['eta_cd_norm_ecrh'],'model_dimensionless_efficiency':v['eta_cd_dimensionless_hcd_primary'],'source_sha256':record['mfile_sha256'],'examples':examples,'physical_validation':False})
 result={'schema':'fusion.actuator-requirement-gate.v1','cases':rows,'source_scalars_sha256':sha(HERE/'ACTUATOR_SCALARS.json'),'admission_sha256':sha(HERE/'ACTUATOR_GATE_ADMISSION.json'),'scope':'Necessary fixed-operating-point total-current budget, not sufficient profile/control/heating feasibility. No new output-power estimate is generated.','sources':[{'authors':'T. Seino, K. Yanagihara, H. Takahashi, K. Tobita, K. Nagasaki, A. Fukuyama, A. Matsuyama, T. Oishi and T. Maekawa','url':'https://doi.org/10.1016/j.fusengdes.2024.114460','reading_scope':'Publisher abstract and author-university bibliographic record; no numerical reproduction.','role':'Their 35-46 kA/MW simulated JA-DEMO examples are different-plasma context, not a bound or a distribution for this candidate.'},{'authors':'N. A. Lopez, A. Alieva, S. A. M. McNamara and X. Zhang','url':'https://arxiv.org/abs/2501.04619','reading_scope':'Public preprint abstract and method sections. Method not executed here.','role':'Existing HARE-guided reverse ray tracing avoids an unstructured launcher scan; requires a matching equilibrium and a suitable authorized ray solver.'}],'normalized_gamma_is_not_dimensionless_zeta':True,'new_solver_runs':0,'physical_validation':False,'accepted_reference_replaced':False}
 raw=(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n').encode('utf-8');(HERE/'ACTUATOR_GATE.json').write_bytes(raw)
 (ROOT/'docs/plant-decision/actuator.json').write_bytes(raw)
 return result
if __name__=='__main__':print(json.dumps(run(),indent=2))
