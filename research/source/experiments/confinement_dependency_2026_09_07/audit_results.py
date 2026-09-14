"""Read-only independent checks of new full-systems outputs, not physical validation."""
from pathlib import Path
import sys,json,re,hashlib,subprocess,os
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(ROOT))
from audit_full_runs import rk_cycles, profile, integral, DURS, LOADS
from run_warm_fixed_process import parse,digest
from run_case import identifiers
CASES=['H1_direct','H11_bridge','H1_continued','H_min_inverse','H103_native_validation']
def run():
    old=(ROOT/'runs-20260907/adaptive30y_warm_fixed/case_IN.DAT').read_text()
    rows=[]
    for name in CASES:
        folder=HERE/name;r=json.loads((folder/'RESULT.json').read_text());v=parse(folder/'case_MFILE.DAT')
        inp=(folder/'case_IN.DAT').read_text();eq={k:x for k,x in v.items() if re.fullmatch(r'eq_con\d+',k)}
        ine={k:x for k,x in v.items() if re.fullmatch(r'ineq_con\d+',k)}
        keep=[line.split('=')[0].strip() for line in inp.splitlines() if re.match(r'^\s*bound[lu]\(',line)]
        row={'case':name,'classification':r['classification'],'mfile_sha256':digest(folder/'case_MFILE.DAT'),
             'values':r['values'],'same_constraint_identifiers':identifiers(inp,'icc')==identifiers(old,'icc'),
             'same_variable_identifiers':identifiers(inp,'ixc')==identifiers(old,'ixc'),
             'equalities':eq,'inequality_residuals':ine,'max_abs_equality_residual':max(abs(x) for x in eq.values()),
             'most_negative_inequality_residual':min(ine.values()),'conditional_average_MW':r['conditional_average_net_MW'],
             'physical_validation':False,'extra_power_warning_MW':v.get('p_plant_imbalance_mw')}
        if r['numerically_converged']:
            dt=np.array([v['t_plant_pulse_'+k] for k in DURS]);net=profile(v,'p_plant_electric_net');gross=profile(v,'p_plant_electric_gross')
            rk=rk_cycles(v);energy=integral(net,dt)/3.6
            row.update({'RK45_fatigue_cycles':rk,'fatigue_integrator_difference_cycles':v['n_cycle']-rk,
                'independent_pulse_energy_error_kWh':energy-v['e_plant_net_electric_pulse_kwh'],
                'independent_profile_balance_error_MW':float(np.max(abs(net-gross-sum(profile(v,k) for k in LOADS))))})
            row.update({'gross_thermal_identity_error_MW':gross[3]-v['eta_turbine']*v['p_plant_primary_heat_mw'],
                'duty_cycles':30*.8*31557600/sum(dt),'reported_duty_cycles':v['n_cycle_min'],
                'independent_average_MW':.8*integral(net,dt)/sum(dt),
                'printed_objective':v.get('norm_objf'),'plasma_residual_plus_outer_radiation_MW':v['p_plasma_imbalance_mw']+v['p_plasma_outer_rad_mw'],
                'CS_start_current_critical_ratio':v['j_cs_pulse_start']/v['j_cs_critical_pulse_start'],
                'TF_operating_critical_ratio':v['f_c_tf_turn_operating_critical']})
        rows.append(row)
    result={'schema':'fusion.confinement-verification.v1','results':rows,
        'inverse_initialization_deviation':'The inverse admission intended a feasible H1.1 start. The generic driver retained its other20-variable seed values but overwrote initial hfact to the1.2 cap. Saved input shows this; do not claim the first inverse evaluation itself was the H1.1 feasible point. Native1.03 follow-on independently converged.',
        'initialization_not_changed_physics':'Warm start differs from an exact solution, but constraints,feasible bounds and inverse objective are unchanged.',
        'source_clean':subprocess.check_output(['git','-C',str(Path(os.environ.get('FUSION_PROCESS_SOURCE',ROOT/'PROCESS-v3.4.2'))),'status','--porcelain'],text=True)=='',
        'not_a_global_certificate':True,'not_new_thermal_or_TBR_model':True,
        'raw_residual_export_note':'Initial driver looked for normres keys and emitted an empty field. This audit reads actual eq_con/ineq_con keys directly; no missing residual is treated as zero.'}
    (HERE/'VALIDATION.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(result,allow_nan=False),flush=True);return result
if __name__=='__main__':run()
