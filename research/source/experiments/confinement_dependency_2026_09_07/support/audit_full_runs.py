"""Independent output/accounting checks for completed full PROCESS runs."""
import json,re,math,hashlib,subprocess
from dataclasses import asdict
from pathlib import Path
import numpy as np
from scipy.integrate import solve_ivp
from run_full_process import parse,digest
from adaptive_fatigue import inspect_case
from process.data_structure.cs_fatigue_variables import CSFatigueData
ROOT=Path(__file__).resolve().parent
DURS=['coil_precharge','plasma_current_ramp_up','fusion_ramp','burn','plasma_current_ramp_down','dwell']
LOADS=['p_plant_electric_base_total','p_hcd_electric_total','p_coolant_pump_elec_total','p_tf_electric_supplies','p_pf_electric_supplies','vachtmw','p_tritium_plant_electric','p_cryo_plant_electric']
def profile(v,key):return np.array([v[f'{key}_profile_mw{i}'] for i in range(7)])
def integral(y,dt):return float(np.dot(.5*(y[1:]+y[:-1]),dt))
def input_list(text,key):
    return sorted(int(m[1]) for line in text.splitlines() if (m:=re.match(r'\s*'+key+r'\s*=\s*(\d+)',line)))
def rk_cycles(v):
    from process.models.cs_fatigue import CsFatigue
    p=CSFatigueData();stress=v['stress_hoop_cs_inner']/1e6;a0=v['t_crack_vertical'];c0=3*a0
    t=v['dz_cs_turn_conduit'];w=v['dr_cs_turn_conduit'];r=(p.residual_sig_hoop/1e6)/(stress+p.residual_sig_hoop/1e6)
    C=p.paris_coefficient/(1-r)**(-p.paris_power_law*(p.walker_coefficient-1))
    def K(a,c):return CsFatigue.surface_stress_intensity_factor(stress,t,w,a,c,np.array([np.pi/2,0.]))
    def rhs(a,y):
        ka,kc=K(a,y[0]);return [(kc/ka)**p.paris_power_law,1/(2*C*ka**p.paris_power_law)]
    def stopc(a,y):return w/p.sf_radial_crack-y[0]
    def stopk(a,y):return p.fracture_toughness/p.sf_fast_fracture-max(K(a,y[0]))
    stopc.terminal=stopk.terminal=True;stopc.direction=stopk.direction=-1
    sol=solve_ivp(rhs,(a0,t/p.sf_vertical_crack),[c0,0.],method='RK45',rtol=1e-10,atol=[1e-13,1e-6],events=[stopc,stopk])
    if not sol.success:raise RuntimeError(sol.message)
    return float(sol.y[1,-1])
def run():
    results=[]
    for folder in sorted((ROOT/'runs-20260907').iterdir()):
        summary=json.loads((folder/'RESULT.json').read_text());row={'case':folder.name,'converged':summary['numerically_converged'],'exception':summary['exception'],'input_sha256':digest(folder/'case_IN.DAT')}
        if not row['converged']:
            row['classification']='execution_error' if row['exception'] else 'solver_not_converged';results.append(row);continue
        v=parse(folder/'case_MFILE.DAT');dt=np.array([v['t_plant_pulse_'+k] for k in DURS]);net=profile(v,'p_plant_electric_net');gross=profile(v,'p_plant_electric_gross')
        mismatch=np.max(abs(net-gross-sum(profile(v,k) for k in LOADS)))
        pulse=integral(net,dt)/3.6
        dose=v['life_plant']*v['f_t_plant_available']*31557600/v['t_plant_pulse_total']
        fatigue=inspect_case(v['stress_hoop_cs_inner'],v['dz_cs_turn_conduit']);rk=rk_cycles(v)
        text=(folder/'case_IN.DAT').read_text();constraints=input_list(text,'icc');variables=input_list(text,'ixc')
        extra=['j_cs_flat_top_end','j_cs_pulse_start','j_cs_critical_pulse_start','j_cs_critical_flat_top_end','f_c_tf_turn_operating_critical','p_plant_imbalance_mw','p_reactor_imbalance_mw','p_plasma_imbalance_mw','p_plasma_outer_rad_mw','p_electric_imbalance','f_t_plant_available']
        row.update({'values':{**summary['values'],**{k:v.get(k) for k in extra}},'constraints':constraints,'iteration_variables':variables,'mfile_sha256':digest(folder/'case_MFILE.DAT'),'pulse_energy_error_kwh':pulse-v['e_plant_net_electric_pulse_kwh'],'profile_balance_error_mw':float(mismatch),'gross_heat_identity_error_mw':gross[3]-v['eta_turbine']*v['p_plant_primary_heat_mw'],'independent_average_net_mw':v['f_t_plant_available']*integral(net,dt)/sum(dt),'30year_required_cycles':dose,'independent_fatigue':{**fatigue,'RK45_cycles':rk,'DOP853_RK45_difference_cycles':fatigue['adaptive_cycles']-rk},'CS_start_current_critical_ratio':v['j_cs_pulse_start']/v['j_cs_critical_pulse_start'],'reported_plasma_residual_plus_outer_radiation_mw':v['p_plasma_imbalance_mw']+v['p_plasma_outer_rad_mw'],'classification':'converged_with_qualifications','physical_plant_validated':False})
        if mismatch>1e-7 or abs(row['pulse_energy_error_kwh'])>1e-5:raise ValueError('Power replay failed')
        if abs(fatigue['adaptive_cycles']-rk)>0.01:raise ValueError('Fatigue cross-check failed')
        results.append(row)
    baseline=next(r for r in results if r['case']=='baseline_iofix')
    for r in results:
        if r['converged']:
            assert set(r['constraints'])>=set(baseline['constraints'])
    status=subprocess.check_output(['git','-C',str(ROOT/'PROCESS-v3.4.2'),'status','--porcelain'],text=True)
    obj={'schema':'fusion.full-run-validation.v1','upstream_source_worktree_status':status,'fatigue_default_assumptions':asdict(CSFatigueData()),'results':results,'limits':['Full PROCESS framework with runtime Windows I/O shim; upstream equations unchanged except explicitly selected adaptive fatigue and mission constraint.','Input-dependent conceptual numerical solutions, not qualified magnet lifetime or proven reactor output.','Plasma diagnostic residual equals negative outer radiation for these i_rad_loss=1 cases; its reporting convention differs from enforced core balance.','Nonzero plant-level residual remains recorded and must be reconciled before energy-closure certification.','No same-design TBR, raw-material calibration, or validated outage/fuel-supply model yet.']}
    (ROOT/'FULL_RUN_VALIDATION.json').write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n');print(json.dumps(obj,allow_nan=False))
if __name__=='__main__':run()
