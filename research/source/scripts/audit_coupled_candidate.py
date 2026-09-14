#!/usr/bin/env python3
"""Audit the PR42 candidate: heat feedback, converged fatigue, and fuel budgets.

This is NOT a full PROCESS optimization, neutronics run, or qualified magnet model.
The fatigue equations are a restricted reimplementation of UKAEA PROCESS (MIT),
commit c0ae5b28649f2b20fb7efc7904628b6defe4151c, for equal conduit dimensions,
a<=c, zero bending, and the two endpoint stress-intensity factors used upstream.
"""
from __future__ import annotations
import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import scipy
from scipy.integrate import solve_ivp
from scipy.optimize import brentq
from audit_plant_closure import DURATIONS, integrate, parse_mfile, profile, required, verify_archive

ARCHIVE_SHA = '5aae03f0d4dc4e7eff11b46488f6c3bddc290d29a759cd38712ea79a0b9b627b'
UPSTREAM = 'c0ae5b28649f2b20fb7efc7904628b6defe4151c'
YEAR_S = 8766.0*3600.0


def finite_range(name: str, value: float, lower: float, upper: float, *, strict_lower=False):
    if not math.isfinite(value) or value > upper or value < lower or (strict_lower and value == lower):
        raise ValueError(f'{name} outside allowed range')


def load_baseline(archive: Path) -> tuple[dict[str,float],str]:
    with verify_archive(archive, ARCHIVE_SHA) as z:
        raw=z.read('cases/baseline/baseline_MFILE.DAT')
    values=parse_mfile(raw.decode())
    if required(values,'ifail') != 1: raise ValueError('Baseline not numerically converged')
    for key in ['stress_hoop_cs_inner','dz_cs_turn_conduit','dr_cs_turn_conduit','n_cycle','eta_turbine',
                'p_plant_primary_heat_mw','p_fw_blkt_heat_deposited_mw','p_fw_blkt_coolant_pump_mw',
                'p_fw_blkt_coolant_pump_elec_mw','p_hcd_ecrh_injected_total_mw','life_plant']:
        required(values,key)
    if not math.isclose(values['dz_cs_turn_conduit'],values['dr_cs_turn_conduit'],abs_tol=1e-14):
        raise ValueError('Fatigue specialization requires equal conduit dimensions')
    gross=profile(values,'p_plant_electric_gross'); on=np.array(gross)/gross[3]
    for key in ['p_hcd_electric_total','p_coolant_pump_elec_total']:
        p=np.array(profile(values,key))
        if not np.allclose(p,p[3]*on,atol=1e-10,rtol=0):
            raise ValueError('Archived pump/heating phase shape differs from gross shape')
    if not math.isclose(gross[3],values['eta_turbine']*values['p_plant_primary_heat_mw'],abs_tol=1e-9):
        raise ValueError('Gross thermal/electric identity failed')
    return values,hashlib.sha256(raw).hexdigest()


def power_case(v:dict[str,float], ec_eff:float=.6, pump_mech_mw:float|None=None,
               dwell_s:float=600., availability:float=.8, turbine_eff:float|None=None,
               *, pump_heat_feedback:bool=True, primary_nonpump_heat_fraction:float=1.,
               extra_running_load_mw:float=0.) -> dict[str,Any]:
    """Retain archived phase shapes, but couple pump electricity and thermal heat.

    Heat-fraction changes are generic stress tests on ALL nonpump primary heat,
    not a plasma-composition solver or a prediction of fusion-power changes.
    """
    finite_range('EC efficiency',ec_eff,0,1,strict_lower=True)
    finite_range('availability',availability,0,1,strict_lower=True)
    finite_range('dwell',dwell_s,0,1e9)
    finite_range('heat fraction',primary_nonpump_heat_fraction,0,2)
    finite_range('extra running load',extra_running_load_mw,0,1e6)
    pump0=v['p_fw_blkt_coolant_pump_mw']
    if pump_mech_mw is None: pump_mech_mw=90*v['p_fw_blkt_heat_deposited_mw']/2400
    finite_range('mechanical pump power',pump_mech_mw,0,1e6)
    eta_p=pump0/v['p_fw_blkt_coolant_pump_elec_mw']
    eta_t0=v['eta_turbine']; eta_t=eta_t0 if turbine_eff is None else turbine_eff
    finite_range('turbine efficiency',eta_t,0,1,strict_lower=True)
    ds=[required(v,'t_plant_pulse_'+k) for k in DURATIONS];ds[-1]=dwell_s
    net0=np.array(profile(v,'p_plant_electric_net'))
    gross0=np.array(profile(v,'p_plant_electric_gross'));on=gross0/gross0[3]
    heat0=v['p_plant_primary_heat_mw']; heat1=heat0+(primary_nonpump_heat_fraction-1)*(heat0-pump0)
    if pump_heat_feedback: heat1+=pump_mech_mw-pump0
    gross1=eta_t*heat1
    heating0=-profile(v,'p_hcd_electric_total')[3]
    heating1=v['p_hcd_ecrh_injected_total_mw']/ec_eff
    delta_net=(gross1-gross0[3])+(pump0-pump_mech_mw)/eta_p+(heating0-heating1)-extra_running_load_mw
    net=net0+on*delta_net
    energy=integrate(net.tolist(),ds)
    return {'ec_efficiency_assumed':ec_eff,'pump_mechanical_mw_assumed':pump_mech_mw,
            'pump_electrical_mw':pump_mech_mw/eta_p,'pump_efficiency':eta_p,'turbine_efficiency_assumed':eta_t,
            'availability_assumed':availability,'dwell_s':dwell_s,'cycle_s':sum(ds),
            'pump_heat_feedback':pump_heat_feedback,'primary_nonpump_heat_fraction':primary_nonpump_heat_fraction,
            'extra_running_load_mw':extra_running_load_mw,'gross_flat_top_mw':gross1,
            'primary_heat_mw':heat1,'flat_top_net_mw':float(net[3]),'net_profile_mw':net.tolist(),
            'cycle_average_net_mw':energy/sum(ds),'availability_adjusted_net_mw':availability*energy/sum(ds),
            'availability_weighted_on_fraction':availability*integrate(on.tolist(),ds)/sum(ds),
            'pulse_energy_kwh':energy/3.6}


@dataclass(frozen=True)
class FatigueParameters:
    residual_mpa:float=240.
    initial_a_m:float=.00089
    paris_coefficient:float=65e-14
    exponent:float=3.5
    walker:float=.436
    crack_safety:float=2.
    fracture_mpa_sqrt_m:float=200/1.5


def stress_intensity_endpoints(stress_mpa:float, thickness_m:float,a:float,c:float)->tuple[float,float]:
    """Endpoint reduction of upstream surface_stress_intensity_factor, a<=c."""
    if min(stress_mpa,thickness_m,a,c)<=0 or not all(map(math.isfinite,[stress_mpa,thickness_m,a,c])):
        raise ValueError('Invalid stress/conduit/crack')
    if a>c*(1+1e-10): raise ValueError('Only the a<=c branch was implemented')
    at=a/thickness_m;ac=a/c
    theta=math.sqrt(at)*math.pi*c/(2*thickness_m)
    if theta>=math.pi/2:raise ValueError('Outside finite-width formula domain')
    q=1+1.464*ac**1.65
    m1=1.13-.09*ac;m2=-.54+.89/(.2+ac);m3=.5-1/(.65+ac)+14*(1-ac)**24
    ka=stress_mpa*(m1+m2*at**2+m3*at**4)*math.sqrt(1/math.cos(theta))*math.sqrt(math.pi*a/q)
    kc=ka*(1.1+.35*at**2)*math.sqrt(ac)
    return ka,kc


def fatigue(stress_mpa:float, thickness_m:float, *, params=FatigueParameters(),
            native_step_m:float|None=None, method:str='DOP853',rtol:float=1e-10)->dict[str,Any]:
    finite_range('stress',stress_mpa,0,1e5,strict_lower=True)
    finite_range('thickness',thickness_m,0,100,strict_lower=True)
    a0=params.initial_a_m;c0=3*a0;limit=thickness_m/params.crack_safety
    k0=max(stress_intensity_endpoints(stress_mpa,thickness_m,a0,c0))
    if a0>=limit or c0>=limit or k0>=params.fracture_mpa_sqrt_m:
        return {'cycles':0.,'termination':'initial_limit_violated','initial_K':k0}
    r=params.residual_mpa/(stress_mpa+params.residual_mpa)
    coeff=params.paris_coefficient/(1-r)**(-params.exponent*(params.walker-1))
    if native_step_m is not None:
        finite_range('native step',native_step_m,0,.001,strict_lower=True)
        a=a0;c=c0;n=0.;kmax=0.;steps=0
        # Intentionally preserve upstream stale-K test and overshoot, for reproduction.
        while a<=limit and c<=limit and kmax<=params.fracture_mpa_sqrt_m:
            ka,kc=stress_intensity_endpoints(stress_mpa,thickness_m,a,c);kmax=max(ka,kc)
            n+=native_step_m/(coeff*kmax**params.exponent)
            a+=native_step_m*(ka/kmax)**params.exponent
            c+=native_step_m*(kc/kmax)**params.exponent;steps+=1
            if steps>1_000_000: raise RuntimeError('Iteration guard exceeded')
        return {'cycles':n/2,'method':'native_Euler_reimplementation','step_m':native_step_m,
                'steps':steps,'final_a_m':a,'final_c_m':c,'last_K':kmax,'termination':'native_loop'}
    def rhs(a,y):
        ka,kc=stress_intensity_endpoints(stress_mpa,thickness_m,a,y[0])
        return [(kc/ka)**params.exponent,1/(2*coeff*ka**params.exponent)]
    def radial(a,y):return limit-y[0]
    def fracture(a,y):return params.fracture_mpa_sqrt_m-max(stress_intensity_endpoints(stress_mpa,thickness_m,a,y[0]))
    radial.terminal=fracture.terminal=True;radial.direction=fracture.direction=-1
    sol=solve_ivp(rhs,(a0,limit),[c0,0.],method=method,events=[radial,fracture],rtol=rtol,atol=[rtol*1e-3,rtol*1e4])
    if not sol.success:raise RuntimeError(sol.message)
    term='radial_crack' if len(sol.t_events[0]) else 'fast_fracture' if len(sol.t_events[1]) else 'vertical_crack'
    return {'cycles':float(sol.y[1,-1]),'method':method,'rtol':rtol,'termination':term,
            'final_a_m':float(sol.t[-1]),'final_c_m':float(sol.y[0,-1]),'nfev':sol.nfev,
            'final_max_K':max(stress_intensity_endpoints(stress_mpa,thickness_m,sol.t[-1],sol.y[0,-1]))}


def fuel_loss_budget(burned_fraction:float,puff_tritium_to_core_ratio:float,tbr:float,
                     blanket_delivery:float, recycle_loss:float)->dict[str,float|bool]:
    """Necessary long-run mass balance, excluding decay/reserves/holdup/growth.

    Ratio is TRITIUM throughput, not the total D+T gas ratio. Recovery loss is
    permanently unavailable T per exhaust pass, not neutron capture inefficiency.
    No values here are claimed as measured device-specific inputs.
    """
    finite_range('burned fraction',burned_fraction,0,1,strict_lower=True)
    finite_range('puff ratio',puff_tritium_to_core_ratio,0,1e6)
    finite_range('TBR',tbr,0,100)
    finite_range('blanket delivery',blanket_delivery,0,1,strict_lower=True)
    finite_range('recycle loss',recycle_loss,0,1)
    exhaust=(1+puff_tritium_to_core_ratio)/burned_fraction-1
    necessary=(1+recycle_loss*exhaust)/blanket_delivery
    margin=blanket_delivery*tbr-1
    max_loss=None if exhaust==0 else max(0.,margin/exhaust)
    return {'effective_core_burn_fraction':burned_fraction,'tritium_puff_core_ratio':puff_tritium_to_core_ratio,
            'blanket_delivery_assumed':blanket_delivery,'TBR_assumed':tbr,'recycle_loss_assumed':recycle_loss,
            'exhaust_flow_per_burned_flow':exhaust,'minimum_TBR_ignoring_decay':necessary,
            'maximum_recycle_loss_ignoring_decay':max_loss,
            'passes_necessary_mass_balance':tbr>=necessary}


def audit(archive:Path)->dict[str,Any]:
    v,mfile_hash=load_baseline(archive)
    pump0=v['p_fw_blkt_coolant_pump_mw'];pump1=90*v['p_fw_blkt_heat_deposited_mw']/2400
    old=power_case(v,pump_heat_feedback=False);corrected=power_case(v)
    original=power_case(v,.5,pump0,1800.)
    if abs(original['pulse_energy_kwh']-v['e_plant_net_electric_pulse_kwh'])>1e-6:raise ValueError('Baseline energy not reproduced')
    required_ec=brentq(lambda e:power_case(v,e)['availability_adjusted_net_mw']-400,.5,1.)
    max_pump=brentq(lambda p:power_case(v,.6,p)['availability_adjusted_net_mw']-400,0.,pump0)
    required_turbine=brentq(lambda e:power_case(v,.6,turbine_eff=e)['availability_adjusted_net_mw']-400,.3,.6)
    # Optional distinct closure: pump ratio refers to NEW total FW+blanket heat.
    k=90/2400;self_consistent_pump=k*(v['p_fw_blkt_heat_deposited_mw']-pump0)/(1-k)
    grid=[power_case(v,e,p,d) for e in [.5,.55,.6,.65,.7,.75] for p in [pump1,80.,60.,40.] for d in [1800.,600.,300.]]
    heat_stress=[power_case(v,.6,primary_nonpump_heat_fraction=x) for x in [1.,.99,.95,.90]]
    baseline_f={'stress_mpa':v['stress_hoop_cs_inner']/1e6,'conduit_m':v['dz_cs_turn_conduit']}
    candidate_f={'stress_mpa':293.95,'conduit_m':.009813,'scope':'rounded values from the prior reduced-order screen, not a reoptimized plant'}
    fr={}
    for key,case in [('baseline',baseline_f),('prior_candidate',candidate_f)]:
        st=case['stress_mpa'];th=case['conduit_m']
        native=fatigue(st,th,native_step_m=1e-4)
        dop=fatigue(st,th);rk=fatigue(st,th,method='RK45')
        conv=[fatigue(st,th,native_step_m=d) for d in [1e-4,5e-5,2.5e-5,1e-5,1e-6]]
        fr[key]={'input':case,'native':native,'DOP853':dop,'RK45':rk,'Euler_refinement':conv,
                 'native_overstatement_relative_to_converged':native['cycles']/dop['cycles']-1,
                 'solver_difference_cycles':abs(dop['cycles']-rk['cycles'])}
    if abs(fr['baseline']['native']['cycles']-v['n_cycle'])>1e-7:raise ValueError('Native fatigue reproduction failed')
    cycles_year=.8*YEAR_S/corrected['cycle_s'];mission_cycles=v['life_plant']*cycles_year
    stress20=brentq(lambda s:fatigue(s,.009813)['cycles']-20000,100.,400.)
    stress30=brentq(lambda s:fatigue(s,.009813)['cycles']-mission_cycles,50.,400.)
    cycles=fr['prior_candidate']['DOP853']['cycles']
    penalties=[]
    for downtime in [0,30,90,180,365]:
        renewal=1+.8*downtime*86400/(cycles*corrected['cycle_s'])
        penalties.append({'replacement_downtime_days_assumed':downtime,
            'effective_availability':.8/renewal,'long_run_average_net_mw':corrected['availability_adjusted_net_mw']/renewal})
    joint_frontier=[]
    for downtime in [0,90]:
        availability=next(x['effective_availability'] for x in penalties if x['replacement_downtime_days_assumed']==downtime)
        for heat_fraction in [1.,.99,.95]:
            eta=brentq(lambda e:power_case(v,.6,turbine_eff=e,availability=availability,primary_nonpump_heat_fraction=heat_fraction)['availability_adjusted_net_mw']-400,.3,.7)
            joint_frontier.append({'replacement_downtime_days_assumed':downtime,'availability_after_replacement':availability,
                'nonpump_primary_heat_fraction':heat_fraction,'required_turbine_efficiency_at_EC60':eta,
                'all_unmentioned_parameters_remain_frozen':True})
    fuel=[fuel_loss_budget(b,g,t,.99,l) for b in [.01,.02,.05] for g in [0.,1.,10.] for t in [1.05,1.10,1.15] for l in [0.,.0001,.0005]]
    return {'schema':'fusion-solution-set.coupled-candidate-audit.v1','date':'2026-09-07',
        'upstream_process_commit':UPSTREAM,'prior_candidate_commit':'c34f433396df78d8240e5e54cc917e033ab10d58',
        'input_archive_sha256':ARCHIVE_SHA,'baseline_mfile_sha256':mfile_hash,'baseline_and_internal_manifest_verified':True,
        'versions':{'numpy':np.__version__,'scipy':scipy.__version__},
        'power':{'original_baseline_replay':original,'prior_candidate_reproduced':old,'corrected_same_pump_assumption':corrected,
            'missing_feedback_penalty_average_mw':old['availability_adjusted_net_mw']-corrected['availability_adjusted_net_mw'],
            'required_EC_efficiency_at_400MW':required_ec,'maximum_pump_mechanical_MW_at_EC60':max_pump,
            'required_turbine_efficiency_at_EC60':required_turbine,
            'self_consistent_pump_heat_scaling_alternative':power_case(v,.6,self_consistent_pump),
            'parameter_grid':grid,'nonpump_heat_stress_tests':heat_stress,'joint_maintenance_heat_requirements':joint_frontier},
        'fatigue':{'parameters':asdict(FatigueParameters()),'cases':fr,'fixed_conduit_max_stress_for_20000_cycles_mpa':stress20,
            'fixed_conduit_max_stress_for_30y_no_replacement_mpa':stress30,
            'cycles_per_calendar_year_at_A80_dwell600':cycles_year,'cycles_for_30y_no_replacement':mission_cycles,
            'years_until_prior_candidate_limit_at_A80':cycles/cycles_year,
            'years_represented_by_20000_cycles_at_A80':20000/cycles_year,
            'replacement_downtime_sensitivities':penalties},
        'fuel_necessary_budgets':fuel,
        'scope':['This is a new executed audit, not a new full PROCESS or OpenMC run.',
                 'Published HCPB pump power remains an external assumption; adding heat feedback does not make the plant material/geometry matched.',
                 'Temperature, cycle shape, plasma heating, fusion power, and other loads remain fixed except explicitly swept assumptions.',
                 'Fatigue is convergence of the same constitutive model, NOT independently qualified material life. Reduced candidate geometry uses rounded archived values.',
                 'Two ODE algorithms share the constitutive model; their agreement is numerical cross-checking, not independent experimental replication.',
                 'Replacement times are diagnostic assumptions; magnet replaceability, outage scheduling and RAMI were not demonstrated.',
                 'Fuel budgets are necessary steady-state mass-balance inequalities only; no claim of full time-dependent inventory closure is made.']}


def main()->int:
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--archive',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();result=audit(args.archive);args.output.mkdir(parents=True,exist_ok=True)
    dest=args.output/'COUPLED_CANDIDATE_AUDIT_2026-09-07.json';dest.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'file':str(dest),'corrected_MW':result['power']['corrected_same_pump_assumption']['availability_adjusted_net_mw'],
        'required_EC_efficiency':result['power']['required_EC_efficiency_at_400MW'],'converged_candidate_cycles':result['fatigue']['cases']['prior_candidate']['DOP853']['cycles']}))
    return 0

if __name__=='__main__':raise SystemExit(main())
