"""Same-boundary confinement normalization; no optimization or physical validation.
Original integration code MIT. Formula uses UKAEA PROCESS/IPB98(y,2), with the
existing radiation-definition correction discussed in upstream issue652.
"""
import argparse,hashlib,json,math
from pathlib import Path
HERE=Path(__file__).resolve().parent

def positive(x):
 if isinstance(x,bool) or not isinstance(x,(float,int)) or not math.isfinite(x) or x<=0:raise ValueError('Expected finite positive scalar')
 return x

def convert(h,p_old,p_new,exponent=.69):
 for x in (h,p_old,p_new):positive(x)
 if not math.isfinite(exponent) or not 0<exponent<1:raise ValueError('Invalid loss-power exponent')
 return h*(p_old/p_new)**(1-exponent)

def ipb(v,p):
 return .0562*(v['plasma_current']/1e6)**.93*v['b_plasma_toroidal_on_axis']**.15*(v['nd_plasma_electron_line']/1e19)**.41*positive(p)**(-.69)*v['rmajor']**1.97*v['kappa_ipb']**.78*v['aspect']**(-.58)*v['m_fuel_amu']**.19

def audit_case(case):
 if case['i_confinement_time_from_input']!=34:raise ValueError('This conversion is for IPB98(y,2), not every scaling')
 v=case['values'];h=v['hfact'];p=v['p_plasma_loss_mw'];core=v['p_plasma_inner_rad_mw'];sync=v['p_plasma_sync_mw']
 if v['i_rad_loss']!=1 or sync<0 or core<sync:raise ValueError('Unsupported radiation model or inconsistent radiation')
 heat=v['f_p_alpha_plasma_deposited']*v['p_plasma_alpha_mw']+v['p_non_alpha_charged_mw']+v['p_hcd_injected_total_mw']+v['p_plasma_ohmic_mw']
 if abs(heat-p-core)>1e-7 or abs(heat-v['p_plasma_heating_total_mw'])>1e-7:raise ValueError('Heating/radiation interface fails')
 stored=v['e_plasma_thermal_total']/1e6;old=convert(h,p,p+core+sync);new=convert(h,p,heat);direct=(stored/heat)/ipb(v,heat)
 if abs(old-v['hstar'])>1e-10 or abs(new-direct)>1e-8:raise ValueError('Independent normalization check failed')
 return {'internal_multiplier':h,'reported_hstar_reproduced':old,'same_boundary_thermal_deposited_H':new,'direct_thermal_energy_ratio_H':direct,'difference_H':new-old,'relative_difference_percent':100*(new/old-1),'transport_power_MW':p,'core_radiation_including_synchrotron_MW':core,'synchrotron_MW':sync,'deposited_heating_MW':heat,'thermal_stored_energy_MJ':stored,'global_thermal_time_s':stored/heat,'scaling_time_at_deposited_power_s':ipb(v,heat),'transport_time_replay_error_s':stored/p-v['t_energy_confinement'],'internal_H_replay_error':(stored/p)/ipb(v,p)-h,'thermal_to_total_beta_energy_ratio':v['e_plasma_thermal_total']/v['e_plasma_beta'],'not_a_measured_experimental_H98':True,'plant_power_or_geometry_changed':False}

def run():
 raw=(HERE/'FROZEN_INPUT.json').read_bytes();data=json.loads(raw)
 result={'schema':'fusion.confinement-normalization-result.v1','date':'2026-09-09','frozen_input_sha256':hashlib.sha256(raw).hexdigest(),'cases':{k:audit_case(c) for k,c in data['cases'].items()},'prior_art':data['prior_art'],'disposition':'Known radiation-accounting correction applied to exact candidate records; no novelty claim. Do not equate either internal or converted factor with independent experimental support.','scope':['No new solver optimization, reactor output, measured confinement, transport validation or breeding result.','The model core-radiation quantity already includes synchrotron radiation; only undo the actual subtracted quantity.','Thermal stored energy and deposited heating are held fixed; fast-particle/source power and experimental database definitions still require matching.','Original archived outputs and approved execution manifests remain unchanged.']}
 (HERE/'KEY_RESULTS.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8');return result
if __name__=='__main__':print(json.dumps(run(),indent=2))
