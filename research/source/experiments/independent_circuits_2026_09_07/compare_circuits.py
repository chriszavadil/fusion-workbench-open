"""Finite reference-topology comparison, not a full Modelica/PROCESS loop run.
Compressor entropy/enthalpy equations follow ThermoPower CompressorBase.
No source-derived performance maps or empirical manifold coefficients are invented.
"""
from pathlib import Path
import json, hashlib, math, sys
from functools import lru_cache
import numpy as np
from scipy.optimize import brentq
from CoolProp.CoolProp import PropsSI
import CoolProp
HERE=Path(__file__).resolve().parent

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def write(name,obj):
    (HERE/name).write_text(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8',newline='\n')

def check_params(m,dp,pout,tout,eta,drive):
    if not all(math.isfinite(x) for x in (m,dp,pout,tout,eta,drive)): raise ValueError('Nonfinite input')
    if m<0 or pout<=0 or tout<=0 or not 0<=dp<pout or not 0<eta<=1 or not 0<drive<=1: raise ValueError('Invalid compressor input')

@lru_cache(maxsize=2048)
def specific_compression(dp,pout,tout,eta):
    check_params(1.,dp,pout,tout,eta,1.)
    ps=pout-dp; hd=PropsSI('Hmass','P',pout,'T',tout,'Helium')
    if dp==0: return {'suction_T_K':tout,'suction_P_Pa':ps,'suction_h_J_kg':hd,'discharge_h_J_kg':hd,'fluid_work_J_kg':0.,'entropy_error_J_kgK':0.,'compression_residual_J_kg':0.}
    def residual(ts):
        hs=PropsSI('Hmass','P',ps,'T',ts,'Helium'); ss=PropsSI('Smass','P',ps,'T',ts,'Helium')
        his=PropsSI('Hmass','P',pout,'Smass',ss,'Helium')
        return hs+(his-hs)/eta-hd
    ts=brentq(residual,.5*tout,tout,xtol=1e-10)
    hs=PropsSI('Hmass','P',ps,'T',ts,'Helium'); ss=PropsSI('Smass','P',ps,'T',ts,'Helium')
    his=PropsSI('Hmass','P',pout,'Smass',ss,'Helium'); sis=PropsSI('Smass','P',pout,'Hmass',his,'Helium')
    return {'suction_T_K':ts,'suction_P_Pa':ps,'suction_h_J_kg':hs,'discharge_h_J_kg':hd,'fluid_work_J_kg':hd-hs,'entropy_error_J_kgK':sis-ss,'compression_residual_J_kg':residual(ts)}

def loop(m,heat_mw,dp,cfg):
    check_params(m,dp,cfg['pout'],cfg['tout'],cfg['eta'],cfg['drive'])
    if m<=0 or not math.isfinite(heat_mw) or heat_mw<0: raise ValueError('Positive flow and nonnegative heat required')
    c=specific_compression(dp,cfg['pout'],cfg['tout'],cfg['eta']); wf=m*c['fluid_work_J_kg']/1e6
    # Ideal adiabatic pressure losses do not change stagnation enthalpy.
    hhot=c['discharge_h_J_kg']+heat_mw*1e6/m
    thot=PropsSI('T','P',c['suction_P_Pa'],'Hmass',hhot,'Helium')
    hx=m*(hhot-c['suction_h_J_kg'])/1e6
    return {**c,'flow_kg_s':m,'external_heat_MW':heat_mw,'pressure_drop_Pa':dp,'hot_return_T_K':thot,'fluid_shaft_work_MW':wf,'drive_electric_MW':wf/cfg['drive'],'recoverable_HX_heat_MW':hx,'cycle_energy_residual_MW':hx-heat_mw-wf}

def installation(rows,cfg):
    return {'loops':rows,'fluid_shaft_work_MW':sum(r['fluid_shaft_work_MW'] for r in rows),'drive_electric_MW':sum(r['drive_electric_MW'] for r in rows),'recoverable_HX_heat_MW':sum(r['recoverable_HX_heat_MW'] for r in rows)}

def benefit(shared,independent,heat_eff):
    electric=shared['drive_electric_MW']-independent['drive_electric_MW']; heat=shared['recoverable_HX_heat_MW']-independent['recoverable_HX_heat_MW']
    return {'electric_saving_MW':electric,'lost_recoverable_heat_MW':heat,'lost_conversion_output_MW':heat_eff*heat,'fixed_conversion_net_budget_MW':electric-heat_eff*heat}
def run():
    admission=json.loads((HERE/'ADMISSION.json').read_text()); root=HERE.parent
    sp=root/'blanket-interface-20260907/SOLVED_STATE.json'; fp=root/'flow-balance-20260907/RESULT.json'
    if sha(sp)!=admission['full_state_sha256'] or sha(fp)!=admission['prior_result_sha256']: raise ValueError('Evidence hash mismatch')
    state=json.loads(sp.read_text()); previous=json.loads(fp.read_text()); f=state['fwbs']; p=state['primary_pumping']
    cfg={'pout':p['p_he'],'tout':p['t_in_bb'],'eta':f['etaiso'],'drive':f['eta_coolant_pump_electric'],'heat_eff':state['heat_transport']['eta_turbine'],'head_budget':p['dp_he']}
    sides=('inboard','outboard'); flows=previous['nominal_flows_kg_s']
    heats={s:f['p_fw_nuclear_heat_total_mw']*state['first_wall']['a_fw_'+s]/state['first_wall']['a_fw_total']+f['psurffwi' if s=='inboard' else 'psurffwo']+f['p_blkt_nuclear_heat_total_mw']*f['vol_blkt_'+s]/f['vol_blkt_total'] for s in sides}
    sources=[{'property_choice':r['property_choice'],'branch_heads':{s:r['nominal_prescribed_flows'][s]['channel_drop_Pa'] for s in sides}} for r in previous['results']]
    frozen={'admission':admission,'config':cfg,'flows_kg_s':flows,'heats_MW':heats,'head_inputs':sources,'code_sha256':sha(Path(__file__)),'CoolProp_version':CoolProp.__version__}
    write('FROZEN_INPUT.json',frozen); results=[]
    for source in sources:
        heads=source['branch_heads']; shared_head=max(heads.values()); allowance=cfg['head_budget']-shared_head
        if allowance<0: raise ValueError('Channel-only reference exceeds pressure budget')
        for label,common_extra in [('channel_only',0.),('equal_external_loss_at_shared_budget',allowance)]:
            def system(independent,extra=0.):
                return installation([loop(flows[s],heats[s],(heads[s] if independent else shared_head)+common_extra+(extra if independent else 0.),cfg) for s in sides],cfg)
            common=system(False); independent=system(True); delta=benefit(common,independent,cfg['heat_eff'])
            # Diagnostic energy crossover, NOT permission to exceed pressure budget.
            crossover=brentq(lambda x:benefit(common,system(True,x),cfg['heat_eff'])['fixed_conversion_net_budget_MW'],0.,shared_head-min(heads.values())+1.,xtol=1e-5)
            pressure_extra=max(0.,cfg['head_budget']-max(heads.values())-common_extra)
            results.append({'property_choice':source['property_choice'],'external_loss_case':label,'equal_external_loss_Pa':common_extra,'shared_balanced':common,'independent_regional_circuits':independent,'difference':delta,'energy_only_equal_added_head_crossover_Pa':crossover,'pressure_budget_equal_added_head_limit_Pa':pressure_extra,'joint_equal_added_head_limit_Pa':min(crossover,pressure_extra),'crossover_ignores_auxiliary_or_efficiency_changes':True})
    result={'schema':'fusion.independent-circuit-comparison.v1','frozen_input_sha256':sha(HERE/'FROZEN_INPUT.json'),'inputs':frozen,'cases':results,'no_updated_plant_output':True,'Modelica_or_GETTHEM_executed':False,'physical_validation':False}
    write('RESULT.json',result)
    print(json.dumps([{'choice':r['property_choice'],'case':r['external_loss_case'],'delta':r['difference'],'head_crossover_Pa':r['energy_only_equal_added_head_crossover_Pa'],'joint_head_limit_Pa':r['joint_equal_added_head_limit_Pa']} for r in results],indent=2))
    return result

if __name__=='__main__': run()
