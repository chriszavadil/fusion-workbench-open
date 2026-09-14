#!/usr/bin/env python3
"""Reference diffusion calculation and reported-data-anchored material study.

No HCPB plant calibration or experiment is claimed. Input study summaries provide
material-scale values only. The depleted-source benchmark is reimplemented from
the public PathView paper's parameters and TMAP/FESTIM analytical equations.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import argparse, hashlib, json, math
from pathlib import Path
import numpy as np
from scipy.linalg import eigh_tridiagonal
from scipy.optimize import brentq
from scipy.special import zeta
from audit_periodic_fuel import FuelConfig, inherited_schedule, threshold, validate as validate_periodic
from audit_coupled_candidate import load_baseline
from scipy.constants import physical_constants, electron_volt

@dataclass(frozen=True)
class Reference:
    volume_m3:float=5.20e-11
    area_m2:float=2.16e-6
    thickness_m:float=3.3e-5
    temperature_K:float=2373.
    initial_pressure_Pa:float=1e6
    solubility_prefactor:float=7.244e22
    diffusivity_m2_s:float=2.6237e-11
    boltzmann_J_K:float=1.38065e-23 # Match the authors' analytical file exactly.
    def __post_init__(self):
        for key, value in asdict(self).items():
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"Invalid reference parameter: {key}")
    @property
    def L(self):return self.solubility_prefactor*self.area_m2*self.boltzmann_J_K/self.volume_m3
    @property
    def solubility(self):return self.solubility_prefactor/self.temperature_K

def positive(name,x):
    if not math.isfinite(x) or x<=0:raise ValueError(name)

def root_pressure(c:Reference,times_s, modes=1024):
    """Exact bracketed spectral roots: beta*tan(beta)=L*l."""
    ts=np.asarray(times_s,float)
    if np.any(~np.isfinite(ts)) or np.any(ts<0):raise ValueError('times')
    if isinstance(modes,bool) or not isinstance(modes,int) or modes<2:raise ValueError('modes')
    d=c.L*c.thickness_m
    betas=np.array([brentq(lambda b:b*math.tan(b)-d,n*math.pi+1e-10,(n+.5)*math.pi-1e-10,xtol=1e-12) for n in range(modes)])
    weights=2*d/(betas**2+d*d+d)
    pr=weights@np.exp(-np.outer(betas**2*c.diffusivity_m2_s/c.thickness_m**2,ts))
    pr=np.where(ts==0,1.,pr) # exact initial gas inventory; finite series truncates here
    return pr

def enclosure_fv(c:Reference,times_s,n:int=128):
    """Independent conservative FV spatial discretization, exact in time.

    Normalized gas pressure p, wall concentration u=c/(S*P0). Mass weights
    [1,L*dx,...]; internal exchanges symmetric. Outer wall is a perfect sink.
    """
    if isinstance(n,bool) or not isinstance(n,int) or n<4:raise ValueError('grid')
    ts=np.asarray(times_s,float)
    if np.any(~np.isfinite(ts)) or np.any(ts<0):raise ValueError('times')
    dx=c.thickness_m/n;g=c.L*c.diffusivity_m2_s/dx
    mass=np.r_[1.,np.full(n,c.L*dx)]
    edge=np.r_[2*g,np.full(n-1,g)]
    diag=np.zeros(n+1);diag[:-1]-=edge;diag[1:]-=edge;diag[-1]-=2*g
    ev,U=eigh_tridiagonal(diag/mass,edge/np.sqrt(mass[:-1]*mass[1:]))
    initial=np.zeros(n+1);initial[0]=1
    x=(U@((U.T@(np.sqrt(mass)*initial))[:,None]*np.exp(ev[:,None]*ts)))/np.sqrt(mass)[:,None]
    wall=mass[1:]@x[1:];escaped=1-x[0]-wall
    flux=2*c.diffusivity_m2_s*c.solubility*c.initial_pressure_Pa/dx*x[-1]
    return {'pressure_fraction':x[0], 'wall_inventory_fraction':wall,'escaped_fraction':escaped,'downstream_flux_atoms_m2_s':flux}

def sphere_modes(mean_s:float,n:int=256):
    positive('mean',mean_s)
    if isinstance(n,bool) or not isinstance(n,int) or n<4:raise ValueError('modes')
    j=np.arange(1,n+1,dtype=float)
    w=6/(np.pi*np.pi*j*j)
    rates=np.pi*np.pi*j*j/(15*mean_s)
    tail=1-math.fsum(w)
    # Missing modes are replaced by instantaneous release. This conserves mass;
    # the missing mean is explicitly bounded and tested under refinement.
    missing_mean_upper=90*mean_s/(np.pi**4)*float(zeta(4,n+1))
    return w,rates,tail,missing_mean_upper

def fresh_fraction_released(t,mean_s,kind='sphere',n=256):
    positive('mean',mean_s)
    tt=np.asarray(t,float)
    if np.any(~np.isfinite(tt)) or np.any(tt<0):raise ValueError('time')
    if kind=='exponential':return -np.expm1(-tt/mean_s)
    if kind!='sphere':raise ValueError('kernel')
    w,r,tail,_=sphere_modes(mean_s,n)
    ans=1-w@np.exp(-np.outer(r,tt.reshape(-1)))
    ans=ans.reshape(tt.shape)
    return np.where(tt==0,0.,ans)

def steady_shutdown_fraction_released(t,mean_s,n=256):
    # Initial material inventory is the steady profile from uniform production,
    # not uniform concentration. Normalize using the infinite-series mean.
    w,r,tail,_=sphere_modes(mean_s,n)
    tt=np.asarray(t,float)
    if np.any(~np.isfinite(tt)) or np.any(tt<0):raise ValueError('time')
    ans=1-(w/r)@np.exp(-np.outer(r,tt.reshape(-1)))/mean_s
    return np.where(tt==0,0.,ans.reshape(tt.shape))

def sphere_fv_survival(t_over_mean,n=128,steady_initial=False):
    """Independent shell finite volumes on radius=1 with D=1/15 (mean=1).
    Returns retained fraction of the initial inventory. Perfect-sink boundary.
    """
    if isinstance(n,bool) or not isinstance(n,int) or n<4:raise ValueError('grid')
    ts=np.asarray(t_over_mean,float)
    if np.any(~np.isfinite(ts)) or np.any(ts<0):raise ValueError('time')
    edges=np.linspace(0,1,n+1);dx=1/n;D=1/15
    vol=(edges[1:]**3-edges[:-1]**3)/3
    face=D*edges[1:-1]**2/dx;outer=2*D/dx
    diag=np.zeros(n);diag[:-1]-=face;diag[1:]-=face;diag[-1]-=outer
    ev,U=eigh_tridiagonal(diag/vol,face/np.sqrt(vol[:-1]*vol[1:]))
    if steady_initial:
        # Exact steady solution of this FV matrix under uniform generation.
        initial=U@((-U.T@np.sqrt(vol))/ev)/np.sqrt(vol)
        initial/=np.dot(vol,initial)
    else:initial=np.ones(n)/sum(vol)
    coeff=U.T@(np.sqrt(vol)*initial)
    mass=np.sqrt(vol)@U
    return (mass*coeff)@np.exp(np.outer(ev,ts))

# Model adapter: parallel diffusion modes are additional positive reservoirs.
# All routing, recovery, source and reserve assumptions are inherited, not measured.
def modal_case(c:FuelConfig,s,B,mean_s,n=256,reserve=.5,tbr=None):
    validate_periodic(c,s,B,reserve)
    w,r,tail,bound=sphere_modes(mean_s,n)
    lam=c.decay;beta=c.TBR if tbr is None else tbr
    if not math.isfinite(beta) or beta < 0:raise ValueError("TBR")
    inj=(1+c.puff_tritium_core_ratio)*B/c.burn_fraction
    ex=inj-B
    rates=np.r_[1/c.tau_fast_s,1/c.tau_slow_s,r]
    recover=np.r_[c.recycle_yield,c.recycle_yield,np.full(n,c.blanket_yield)]
    q=np.r_[c.direct_recycling_fraction*ex,(1-c.direct_recycling_fraction)*ex,w*beta*B]
    k=rates+lam
    prompt=tail*beta*B*c.blanket_yield
    phases=[(s.before_s,False),(s.burn_s,True),(s.after_s,False)]
    if s.repeats!=1 or s.tail_outage_s:raise ValueError('single pulse only')
    def step(x,dt,on):
        ek=np.exp(-k*dt);el=math.exp(-lam*dt);A=-math.expm1(-lam*dt)/lam
        conv=el*(-np.expm1(-rates*dt))/rates
        source=q if on else np.zeros_like(q)
        h=x[:-1]*ek+(source/k)*(-np.expm1(-k*dt))
        st=x[-1]*el+np.dot(recover*rates,x[:-1]*conv+source/k*(A-conv))+(prompt-inj)*on*A
        return np.r_[h,st]
    x=np.zeros(len(k)+1)
    for dt,on in phases:x=step(x,dt,on)
    d=x.copy();T=s.pulse_s;h0=d[:-1]/(-np.expm1(-k*T))
    S0=(d[-1]+math.exp(-lam*T)*np.dot(recover*(-np.expm1(-rates*T)),h0))/(-math.expm1(-lam*T))
    x=np.r_[h0,S0];initial=x.copy();minimum=S0;minimum_time=0.;clock=0
    # Within a constant-source phase, all parallel holdups are monotone; exactly
    # the same single-extremum argument as prior periodic model applies.
    for dt,on in phases:
        def dS(z):return np.dot(recover*rates,z[:-1])+(prompt-inj)*on-lam*z[-1]
        start=x.copy();end=step(x,dt,on);candidates=[(0.,start[-1]),(dt,end[-1])]
        if on and dS(start)<0<dS(end):
            root=brentq(lambda t:dS(step(start,t,on)),0,dt,xtol=1e-7)
            candidates.append((root,step(start,root,on)[-1]))
        for t,val in candidates:
            if val<minimum:minimum=float(val);minimum_time=clock+t
        x=end;clock+=dt
    return {'min_available_kg':minimum,'reserve_margin_kg':minimum-reserve,'initial_store_kg':float(S0),
       'initial_material_holdup_kg':float(sum(h0[2:])),'period_closure_error_kg':float(max(abs(x-initial))),
       'minimum_time_s':minimum_time,'mean_tail_error_bound_s':bound,'prompt_tail_fraction':tail,
       'sufficient_empty_reservoir_seed_kg':float(S0+np.dot(recover,h0))}

def modal_threshold(c,s,B,mean_s,n=256,reserve=.5):
    root=brentq(lambda t:modal_case(c,s,B,mean_s,n,reserve,t)['reserve_margin_kg'],.5,2,xtol=1e-12)
    return {'critical_TBR':root,**modal_case(c,s,B,mean_s,n,reserve,root)}

def write(path,obj):
    path.write_text(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+'\n')
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(archive:Path,output:Path):
    output.mkdir(parents=True,exist_ok=True)
    c=Reference();v,mhash=load_baseline(archive);s=inherited_schedule(v)
    B=v['p_plasma_dt_mw']*1e6/(17.6e6*electron_volt)*physical_constants['triton mass'][0]
    points=[{'temperature_C':467.,'mean_h':23.34,'D_cm2_s':None,'regime':'in_pile_reported_overall_mean'},
            {'temperature_C':525.,'mean_h':21.3,'D_cm2_s':1.19e-11,'regime':'post_irradiation_reported_diffusion'},
            {'temperature_C':550.,'mean_h':4.7,'D_cm2_s':5.34e-11,'regime':'post_irradiation_reported_diffusion'}]
    frozen={'schema':'fusion.material-reference.inputs.v1','source_prior_commit':'6a8830accf7bc96578c420cba8a311b3a52db7ab',
      'experimental_source_doi':'10.1016/j.net.2023.09.014','evidence_level':'published abstract numerical summaries, NOT raw time histories',
      'observations':points,'external_reference':asdict(c),'reference_source_blob':'34b753e4787aea6f5bda74bd031ef5b374101faa',
      'baseline_mfile_sha256':mhash,'schedule':asdict(s),'B_kg_s':B,'FV_grids':[32,64,128,256],
      'reference_times_s':[1.,2.,5.,10.,20.,40.,80.,140.],
      'pulse_puff_ratios':[0.,10.],'sphere_modes':[64,128,256,512], 'recycle_yield_assumed':.9995,
      'reserve_kg_assumed':.5,'transfer_gate':'REJECT plant calibration: no matched specimen/geometry/temperature field/irradiation dose/release system/uncertainty'}
    h=write(output/'MATERIAL_REFERENCE_FROZEN_INPUT.json',frozen)
    times=np.array(frozen['reference_times_s']);ref=root_pressure(c,times)
    reference=[]
    for n in frozen['FV_grids']:
        z=enclosure_fv(c,times,n)
        reference.append({'n':n,'max_pressure_abs_error':float(max(abs(z['pressure_fraction']-ref))),
            'pressure_fraction':z['pressure_fraction'].tolist(),'wall_inventory_fraction':z['wall_inventory_fraction'].tolist(),
            'escaped_fraction':z['escaped_fraction'].tolist(),'downstream_flux':z['downstream_flux_atoms_m2_s'].tolist()})
    material=[]
    for point in points:
        tau=point['mean_h']*3600
        row={**point,'mean_s':tau,'one_pulse_fraction_of_fresh_uniform_inventory_released_exponential':float(fresh_fraction_released(s.burn_s,tau,'exponential'))}
        if point['D_cm2_s'] is not None:
            D=point['D_cm2_s']*1e-4
            row.update({'D_m2_s':D,'inferred_effective_radius_m_NOT_measured':math.sqrt(15*D*tau),
              'one_pulse_fraction_of_fresh_uniform_inventory_released_sphere':float(fresh_fraction_released(s.burn_s,tau)),
              'one_pulse_fraction_of_steady_inventory_released_after_shutdown_sphere':float(steady_shutdown_fraction_released(s.burn_s,tau))})
        material.append(row)
    geometry={'interpretation':'D and residence time may be derived from the same fit; this is a unit/consistency check, not independent empirical validation.',
      'relative_radius_difference':material[2]['inferred_effective_radius_m_NOT_measured']/material[1]['inferred_effective_radius_m_NOT_measured']-1}
    applied=[]
    for g in frozen['pulse_puff_ratios']:
        cfg=FuelConfig(puff_tritium_core_ratio=g,recycle_yield=.9995)
        for tau_h in [48.,23.34,21.3,4.7]:
            from dataclasses import replace
            exp=threshold(replace(cfg,tau_blanket_s=tau_h*3600),s,B,.5)
            row={'g_assumed':g,'material_mean_h':tau_h,'exponential_critical_TBR':exp['critical_TBR'],
              'exponential_sufficient_seed_kg':exp['sufficient_empty_reservoir_initial_store_kg']}
            if tau_h in (21.3,4.7):
                row['sphere_refinement']=[{'modes':n,**modal_threshold(cfg,s,B,tau_h*3600,n)} for n in frozen['sphere_modes']]
            applied.append(row)
    th=np.array([.005,.02,.1,.5,1.,3.]);surv=1-fresh_fraction_released(th,1.,n=4096)
    sphere_validation=[]
    for n in frozen['FV_grids']:
        fv=sphere_fv_survival(th,n)
        steady=sphere_fv_survival(th,n,True)
        sphere_validation.append({'n':n,'max_fresh_survival_error':float(max(abs(fv-surv))),
          'max_steady_survival_error':float(max(abs(steady-(1-steady_shutdown_fraction_released(th,1.,4096)))))})
    result={'schema':'fusion.material-reference.result.v1','frozen_input_sha256':h,
        'external_reference_exact_pressure_fraction':ref.tolist(),'external_reference_fv_refinement':reference,
        'reported_material_points_and_conditional_kernels':material,'derived_length_consistency':geometry,
        'sphere_fv_validation':sphere_validation,'inherited_ledger_material_sensitivity':applied,
        'scope':['Depleted-source PDE benchmark reimplemented; FESTIM/PathView binaries not run.',
          'Reported point summaries are not raw measurements, error bars, or matched HCPB calibration.',
          'Sphere law assumes uniform generation, diffusion-only constant properties and perfect sink surface.',
          'Physical 99% delivery, gas streams, recycling losses and blanket TBR remain assumed.',
          'No omitted downstream processing delay is claimed to vanish in a real plant; replacement of the old lump is a sensitivity only.',
          'No full PROCESS/OpenMC/experimental net-power result.']}
    write(output/'MATERIAL_REFERENCE_RESULT.json',result)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--archive',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=run(a.archive,a.output);print(json.dumps({'reference':r['external_reference_fv_refinement'][-1], 'sphere':r['sphere_fv_validation'][-1]},indent=2))
