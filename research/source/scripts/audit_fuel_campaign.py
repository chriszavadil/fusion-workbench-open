#!/usr/bin/env python3
"""Conditional pulsed tritium-inventory ledger with exact segment propagation.

Three first-order reservoirs (fast recycle, slow recycle, blanket extraction),
one available store, permanent processing loss, radioactive decay, burn and breed.
Not a material-transport model or a plasma/divertor solver. All residence times,
yields, puff ratios and TBR are declared assumptions, not measured PR42 outputs.
"""
from __future__ import annotations
import argparse
from dataclasses import dataclass, asdict
import json
import math
from pathlib import Path
import numpy as np
from scipy.linalg import expm
from scipy.optimize import brentq
from scipy.constants import electron_volt, physical_constants
from audit_coupled_candidate import load_baseline, YEAR_S, fuel_loss_budget


@dataclass(frozen=True)
class FuelConfig:
    burn_fraction:float=.02
    puff_tritium_core_ratio:float=0.
    direct_recycling_fraction:float=.8
    tau_fast_s:float=360.
    tau_slow_s:float=14400.
    tau_blanket_s:float=172800.
    recycle_yield:float=.9995
    blanket_yield:float=.99
    TBR:float=1.15
    half_life_years:float=12.32

    def validate(self):
        for name in ['burn_fraction','recycle_yield','blanket_yield']:
            x=getattr(self,name)
            if not math.isfinite(x) or not 0<x<=1:raise ValueError(name)
        if not 0<=self.direct_recycling_fraction<=1:raise ValueError('direct recycling')
        for name in ['tau_fast_s','tau_slow_s','tau_blanket_s','half_life_years']:
            x=getattr(self,name)
            if not math.isfinite(x) or x<=0:raise ValueError(name)
        for name in ['puff_tritium_core_ratio','TBR']:
            x=getattr(self,name)
            if not math.isfinite(x) or x<0:raise ValueError(name)

    @property
    def decay(self):return math.log(2)/(self.half_life_years*YEAR_S)
    @property
    def tau(self):return np.array([self.tau_fast_s,self.tau_slow_s,self.tau_blanket_s])
    @property
    def yields(self):return np.array([self.recycle_yield,self.recycle_yield,self.blanket_yield])


def rates(c:FuelConfig,burn_kg_s:float):
    if not math.isfinite(burn_kg_s) or burn_kg_s<0:raise ValueError('burn rate')
    injection=(1+c.puff_tritium_core_ratio)*burn_kg_s/c.burn_fraction
    exhaust=injection-burn_kg_s
    q=np.array([c.direct_recycling_fraction*exhaust,(1-c.direct_recycling_fraction)*exhaust,c.TBR*burn_kg_s])
    return q,injection


def analytic_step(c:FuelConfig,x:np.ndarray,burn_kg_s:float,dt:float)->np.ndarray:
    """x=[three holdups, available store]; exact affine solution on constant input."""
    if not math.isfinite(dt) or dt<0:raise ValueError('duration')
    q,injection=rates(c,burn_kg_s);lam=c.decay;k=1/c.tau+lam
    el=math.exp(-lam*dt);ek=np.exp(-k*dt)
    # Stable integrals of exp(-lambda t) and exp(-k t).
    A=-math.expm1(-lam*dt)/lam
    conv=el*(-np.expm1(-(k-lam)*dt))/(k-lam)
    h=x[:3]*ek+(q/k)*(-np.expm1(-k*dt))
    store=x[3]*el+np.sum(c.yields/c.tau*(x[:3]*conv+(q/k)*(A-conv)))-injection*A
    return np.r_[h,store]


def matrix_generator(c:FuelConfig,burn_kg_s:float)->np.ndarray:
    """Independent affine system including cumulative permanent loss and decay.

    State=[Hfast,Hslow,Hblanket,S,Loss,Decay,Burn,Bred,constant_one].
    """
    q,injection=rates(c,burn_kg_s);lam=c.decay;A=np.zeros((9,9));idx=np.arange(3)
    A[idx,idx]=-(1/c.tau+lam);A[:3,8]=q
    A[3,:3]=c.yields/c.tau;A[3,3]=-lam;A[3,8]=-injection
    A[4,:3]=(1-c.yields)/c.tau;A[5,:4]=lam
    A[6,8]=burn_kg_s;A[7,8]=c.TBR*burn_kg_s
    return A


def campaign(c:FuelConfig,burn_kg_s:float,off_before_s:float,burn_s:float,off_after_s:float,
             horizon_s:float)->dict:
    c.validate()
    if min(off_before_s,burn_s,off_after_s,horizon_s)<=0:raise ValueError('positive phase durations required')
    segments=[];t=0.;x=np.zeros(4);required_initial=0.;time_min=0.
    # Superposition: S(t;S0)=S(t;0)+S0 exp(-lambda t).
    # All tank inventories start empty; on-phase holdups remain below on steady
    # states, so returns are monotone within each segment. Any interior maximum
    # of the required initial-store function is the single returns=injection root.
    while t<horizon_s-1e-7:
        for duration,burn in [(off_before_s,0.),(burn_s,burn_kg_s),(off_after_s,0.)]:
            dt=min(duration,horizon_s-t)
            if dt<=1e-7:break
            x0=x.copy();q,inj=rates(c,burn);k=1/c.tau+c.decay
            def derivative_sign(local_t):
                h=x0[:3]*np.exp(-k*local_t)+q/k*(-np.expm1(-k*local_t))
                return inj-float(np.dot(c.yields/c.tau,h))
            points=[0.,dt]
            if derivative_sign(0)>0 and derivative_sign(dt)<0:
                points.append(brentq(derivative_sign,0,dt,xtol=1e-7))
            for dtp in points:
                xp=analytic_step(c,x0,burn,dtp);need=-xp[3]*math.exp(c.decay*(t+dtp))
                if need>required_initial:required_initial=need;time_min=t+dtp
            x=analytic_step(c,x0,burn,dt);segments.append((dt,burn));t+=dt
            if t>=horizon_s-1e-7:break
    # Independent augmented-matrix replay with the calculated NONNEGATIVE stock.
    y=np.zeros(9);y[3]=required_initial;y[8]=1.;cache={};max_balance=0.;min_sampled=required_initial
    for dt,burn in segments:
        key=(dt,burn)
        if key not in cache:cache[key]=expm(matrix_generator(c,burn)*dt)
        y=cache[key]@y
        balance=sum(y[:4])+y[4]+y[5]+y[6]-y[7]-required_initial
        max_balance=max(max_balance,abs(balance));min_sampled=min(min_sampled,y[3])
    exact_final=x.copy();exact_final[3]+=required_initial*math.exp(-c.decay*horizon_s)
    method_error=float(np.max(abs(y[:4]-exact_final)))
    budget=fuel_loss_budget(c.burn_fraction,c.puff_tritium_core_ratio,c.TBR,c.blanket_yield,1-c.recycle_yield)
    return {'config':asdict(c),'burn_rate_kg_s':burn_kg_s,'horizon_days':horizon_s/86400,
        'phase_durations_s':[off_before_s,burn_s,off_after_s],
        'finite_horizon_minimum_initial_available_kg':required_initial,'zero_reserve':True,'empty_initial_process_reservoirs':True,
        'required_stock_peak_time_days':time_min/86400,'final_available_kg':float(y[3]),
        'final_recycling_holdup_kg':float(y[0]+y[1]),'final_blanket_holdup_kg':float(y[2]),
        'permanent_loss_kg':float(y[4]),'decayed_kg':float(y[5]),'burned_kg':float(y[6]),'bred_kg':float(y[7]),
        'max_mass_balance_error_kg':max_balance,'analytic_vs_matrix_final_error_kg':method_error,
        'min_endpoint_available_kg':float(min_sampled),'segments':len(segments),
        'necessary_steady_state_budget':budget,
        'finite_horizon_stock_is_NOT_self_sufficiency':True}


def run(archive:Path,output:Path)->dict:
    v,sha=load_baseline(archive)
    triton_mass=physical_constants['triton mass'][0]
    reaction_energy_j=17.6e6*electron_volt
    burn_rate=v['p_plasma_dt_mw']*1e6/reaction_energy_j*triton_mass
    before=v['t_plant_pulse_coil_precharge']+v['t_plant_pulse_plasma_current_ramp_up']+v['t_plant_pulse_fusion_ramp']
    on=v['t_plant_pulse_burn'];after=v['t_plant_pulse_plasma_current_ramp_down']+600.
    configs=[FuelConfig(puff_tritium_core_ratio=g,direct_recycling_fraction=d,recycle_yield=1-l)
        for g in [0.,1.,10.] for d in [0.,.8] for l in [.0001,.0005]]
    output.mkdir(parents=True,exist_ok=True)
    # Freeze all assumptions BEFORE evaluating the scenarios.
    frozen={'schema':'fusion-solution-set.fuel-campaign-input.v1','configs':[asdict(c) for c in configs],
        'horizon_days':60,'source_baseline_mfile_sha256':sha,'dt_fusion_mw':v['p_plasma_dt_mw'],
        'triton_mass_kg':triton_mass,'reaction_energy_j_assumed':reaction_energy_j,'phase_durations_s':[before,on,after],
        'scope':['Rectangular burn only at the stored flat-top duration; ramp fusion consumption excluded.',
                 'The campaign has no additional maintenance outages. It is NOT an 80%-availability lifecycle simulation.',
                 'This is a conditional inventory ledger, not measured recovery performance, real HCPB release kinetics, or a full fuel-cycle design.']}
    config_path=output/'FUEL_CAMPAIGN_FROZEN_INPUT_2026-09-07.json';config_path.write_text(json.dumps(frozen,indent=2,sort_keys=True,allow_nan=False)+'\n')
    import hashlib
    config_hash=hashlib.sha256(config_path.read_bytes()).hexdigest()
    results=[campaign(c,burn_rate,before,on,after,60*86400.) for c in configs]
    out={'schema':'fusion-solution-set.fuel-campaign-audit.v1','frozen_input_sha256':config_hash,'input':frozen,'results':results}
    (output/'FUEL_CAMPAIGN_AUDIT_2026-09-07.json').write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+'\n')
    return out

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--archive',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    result=run(args.archive,args.output)
    print(json.dumps({'cases':len(result['results']),'maximum_mass_error_kg':max(r['max_mass_balance_error_kg'] for r in result['results']),
                      'maximum_solver_disagreement_kg':max(r['analytic_vs_matrix_final_error_kg'] for r in result['results'])}))
