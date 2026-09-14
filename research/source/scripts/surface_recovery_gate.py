#!/usr/bin/env python3
"""Conditional surface/diffusion/downstream recovery gate, not a plant prediction.

A spherical, isotropic diffusion model with a LINEAR Robin boundary. The linear
surface coefficient h [m/s] is NOT the published nonlinear K [m2/(mol s)].
Only the two Arrhenius activation energies motivate the declared sensitivities.
No bulk/surface parameters, Biot numbers or downstream times are fitted to data.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict, replace
from pathlib import Path
import argparse, hashlib, json, math, time
import numpy as np
import scipy
from scipy.constants import R
from scipy.integrate import solve_ivp
from scipy.linalg import expm, solve
from scipy.optimize import brentq

@dataclass(frozen=True)
class Model:
    diameter_m: float = 750e-6
    hot_K: float = 938.15
    cold_K: float = 373.15
    D0_m2_s: float = 5e-11
    E_D_J_mol: float = 20000.
    E_h_J_mol: float = 62000.
    biot_hot: float = 10.
    bulk_multiplier: float = 1.
    # h is held fixed when changing bulk_multiplier, to avoid free surface gains.
    def validate(self):
        for name,x in asdict(self).items():
            if not math.isfinite(x) or x <= 0: raise ValueError(name)
        if self.cold_K > self.hot_K: raise ValueError('temperature ordering')
    @property
    def radius(self): return self.diameter_m/2
    def diffusion(self,T):
        if not math.isfinite(T) or T<=0: raise ValueError('T')
        return self.bulk_multiplier*self.D0_m2_s*math.exp(-self.E_D_J_mol/(R*T))
    def surface(self,T):
        if not math.isfinite(T) or T<=0: raise ValueError('T')
        dhot=self.D0_m2_s*math.exp(-self.E_D_J_mol/(R*self.hot_K))
        hhot=self.biot_hot*dhot/self.radius
        return hhot*math.exp(-self.E_h_J_mol/R*(1/T-1/self.hot_K))
    def mean_residence(self,T):
        d=self.radius**2/(15*self.diffusion(T));s=self.radius/(3*self.surface(T))
        return {'bulk_s':d,'surface_s':s,'total_s':d+s,
                'biot':self.surface(T)*self.radius/self.diffusion(T)}


def mesh(n):
    if isinstance(n,bool) or not isinstance(n,int) or n<4: raise ValueError('mesh n')
    faces=np.linspace(0,1,n+1); weights=np.diff(faces**3)
    return faces,weights


def material_generator(m,T,n):
    """Mass fractions per shell, shell-centered FV, series boundary resistance."""
    m.validate();faces,w=mesh(n);dx=1/n;d=m.diffusion(T)/m.radius**2;h=m.surface(T)/m.radius
    g=3*d*faces[1:-1]**2/dx
    A=np.zeros((n,n));ii=np.arange(n-1)
    A[ii,ii]-=g/w[:-1];A[ii+1,ii]+=g/w[:-1]
    A[ii+1,ii+1]-=g/w[1:];A[ii,ii+1]+=g/w[1:]
    exit_rate=3/(dx/(2*d)+1/h)/w[-1]
    A[-1,-1]-=exit_rate
    return A,exit_rate,w


def full_generator(m,T,n,downstream_s):
    if not math.isfinite(downstream_s) or downstream_s<0: raise ValueError('downstream')
    A,exit_rate,_=material_generator(m,T,n)
    # extra states: material-released but processing, available, cumulative release.
    G=np.zeros((n+3,n+3));G[:n,:n]=A;G[n+2,n-1]=exit_rate
    if downstream_s:
        G[n,n-1]=exit_rate;G[n,n]=-1/downstream_s;G[n+1,n]=1/downstream_s
    else:G[n+1,n-1]=exit_rate
    return G


def initial_hot_steady(m,n):
    A,_,w=material_generator(m,m.hot_K,n)
    inventory=solve(-A,w)
    return inventory/inventory.sum(),float(inventory.sum())


def run_protocol(m,protocol,n=64,downstream_s=360.,initial=None,method='expm'):
    """No generation during the recovery interval. Initial material total = 1.

    Processing begins empty. Thus this is a normalized isolated material cohort,
    not a complete pre-shutdown industrial loop or an operating fuel reserve.
    """
    m.validate();mesh(n)
    if not protocol:raise ValueError('empty protocol')
    x=np.zeros(n+3)
    if initial is None:x[:n]=initial_hot_steady(m,n)[0]
    else:
        v=np.array(initial,dtype=float)
        if v.shape!=(n,) or not np.all(np.isfinite(v)) or v.min()<0 or not np.isclose(v.sum(),1.,atol=1e-10):raise ValueError('initial')
        x[:n]=v
    trace=[];clock=0.;elapsed=0.;min_state=0.;mass_err=0.
    for dt,T in protocol:
        if not math.isfinite(dt) or dt<0:raise ValueError('duration')
        G=full_generator(m,T,n,downstream_s)
        if method=='expm':x=expm(G*dt)@x
        elif method=='Radau':
            if dt:
                sol=solve_ivp(lambda t,y:G@y,(0,dt),x,jac=G,method='Radau',rtol=2e-10,atol=2e-12)
                if not sol.success:raise RuntimeError(sol.message)
                x=sol.y[:,-1]
        else:raise ValueError('method')
        clock+=m.diffusion(T)*dt;elapsed+=dt
        err=abs(float(x[:n+2].sum())-1);mass_err=max(err,mass_err)
        min_state=min(min_state,float(x.min()))
        trace.append({'time_s':elapsed,'temperature_K':T,'material_remaining_fraction':float(x[:n].sum()),
          'released_fraction':float(x[n+2]),'processing_fraction':float(x[n]),'available_fraction':float(x[n+1])})
    if mass_err>1e-8 or min_state< -1e-9:raise ValueError('conservation/positivity failure')
    last=trace[-1]
    return {'model':asdict(m),'protocol':protocol,'cells':n,'downstream_s_assumed':downstream_s,
      'method':method,'diffusion_clock_m2':clock,'trace':trace,'end':last,'mass_balance_max_error':mass_err,
      'min_state':min_state,'material_profile':x[:n].tolist()}


def spectral_hot_steady_survival(m,times,modes=512):
    """Independent Robin-sphere eigenfunction series at the reference hot T.

    mu*cot(mu)=1-Bi. Coefficients for steady uniform generation equal the
    uniform-inventory weights divided by modal decay rate times mean residence.
    """
    if isinstance(modes,bool) or not isinstance(modes,int) or modes<8:raise ValueError('modes')
    ts=np.asarray(times,float)
    if np.any(~np.isfinite(ts)) or np.any(ts<0):raise ValueError('times')
    bi=m.surface(m.hot_K)*m.radius/m.diffusion(m.hot_K)
    roots=np.array([brentq(lambda x:x/math.tan(x)-(1-bi),j*math.pi+1e-9,(j+1)*math.pi-1e-9,xtol=1e-12) for j in range(modes)])
    integ=(np.sin(roots)-roots*np.cos(roots))/roots**2
    norm=.5-np.sin(2*roots)/(4*roots)
    uniform_weights=3*integ**2/norm
    decay=roots**2*m.diffusion(m.hot_K)/m.radius**2
    mean=m.mean_residence(m.hot_K)['total_s'];weights=uniform_weights/(decay*mean)
    return {'remaining':(weights@np.exp(-np.outer(decay,ts))).tolist(),
            'initial_tail_weight':float(1-weights.sum()),'roots':roots.tolist()}


def write(path,obj):
    path.write_text(json.dumps(obj,sort_keys=True,indent=2,allow_nan=False)+'\n')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(output):
    output.mkdir(parents=True,exist_ok=True)
    model=Model();duration=5400.
    protocols={'held_hot':[(duration,model.hot_K)],'held_cold':[(duration,model.cold_K)],
      'hot_then_cold':[(duration/2,model.hot_K),(duration/2,model.cold_K)],
      'cold_then_hot':[(duration/2,model.cold_K),(duration/2,model.hot_K)]}
    frozen={'schema':'fusion.surface-recovery-input.v1','base_model':asdict(model),'models_biot_hot':[.1,1.,10.,100.],
      'downstream_seconds':[0.,360.,14400.],'protocols':protocols,'cells':64,'refinement_cells':[32,64,128,256],
      'bulk_acceleration_factors':[1.,10.], 'recovery_decision_fraction':.50,
      'initial':'Unit total material inventory with each model hot steady-generation profile; downstream initially empty.',
      'provenance':{'diffusion_D0':'Kulsartov2023 Eq5 effective qualitative law, not microscopic measurement',
        'diffusion_E':'Kulsartov2023 Eq5, 20000 J/mol',
        'surface_E':'62000 J/mol borrowed ONLY as an activation-energy sensitivity from nonlinear Eq11',
        'linear_h_hot':'Uncalibrated chosen Biot values; NOT the nonlinear K0 in the paper',
        'diameter':'750 micrometres illustrative; not sample size-distribution weights',
        'temperatures':'Reported approximate experiment endpoints; switched histories are NOT measured traces'},
      'limits':['A linear Robin surface law, not the nonlinear published diffusion-desorption model.',
        'No irradiation generation, decay, trapping, evolving porosity or multiple isotope chemistry during this isolated recovery.',
        'No complete plant fuel cycle, power cost, calibrated uncertainty, or operational safety decision.',
        'Cumulative material release is not immediately available fuel when downstream delay is positive.']}
    h=write(output/'SURFACE_RECOVERY_FROZEN_INPUT.json',frozen);start=time.perf_counter();rows=[]
    for bi in frozen['models_biot_hot']:
        m=replace(model,biot_hot=bi)
        for name,p in protocols.items():
            for tau in frozen['downstream_seconds']:
                row=run_protocol(m,p,n=64,downstream_s=tau);row['protocol_label']=name;rows.append(row)
    refinement=[]
    for n in frozen['refinement_cells']:
        for name in ['hot_then_cold','cold_then_hot']:
            row=run_protocol(model,protocols[name],n=n,downstream_s=360.);row['protocol_label']=name;refinement.append(row)
    steady_checks=[]
    for bi in frozen['models_biot_hot']:
        m=replace(model,biot_hot=bi);exact=m.mean_residence(m.hot_K)['total_s']
        sv=spectral_hot_steady_survival(m,[60.,600.,2700.,5400.])
        for n in [32,64,128]:
            ys=[run_protocol(m,[(t,m.hot_K)],n=n,downstream_s=0.)['end']['material_remaining_fraction'] for t in [60.,600.,2700.,5400.]]
            fv_mean=initial_hot_steady(m,n)[1]
            steady_checks.append({'biot_hot':bi,'n':n,'analytic_mean_s':exact,'fv_mean_s':fv_mean,
              'relative_mean_error':abs(fv_mean/exact-1),'max_spectral_error':float(np.max(abs(np.array(ys)-sv['remaining']))),
              'spectral_initial_tail':sv['initial_tail_weight']})
    crosschecks=[]
    for name in ['hot_then_cold','cold_then_hot']:
        ex=run_protocol(model,protocols[name],n=32,downstream_s=360.)
        iv=run_protocol(model,protocols[name],n=32,downstream_s=360.,method='Radau')
        err=max(abs(ex['end'][key]-iv['end'][key]) for key in ['released_fraction','available_fraction','material_remaining_fraction','processing_fraction'])
        crosschecks.append({'protocol':name,'cells':32,'maximum_expm_vs_Radau_fraction_error':err})
    acceleration=[]
    for bi in frozen['models_biot_hot']:
        m=replace(model,biot_hot=bi)
        for temp in [m.hot_K,m.cold_K]:
            a=m.mean_residence(temp);b=replace(m,bulk_multiplier=10.).mean_residence(temp)
            acceleration.append({'biot_hot':bi,'T_K':temp,'initial_bulk_fraction_of_mean':a['bulk_s']/a['total_s'],
               'mean_s_before':a['total_s'],'mean_s_after_D_times_10':b['total_s'],
               'release_mean_speedup':a['total_s']/b['total_s'],'factor_D_increase':10.})
    # Equal activation energies: same-temperature exposure gives identical material profile.
    equal=replace(model,E_h_J_mol=model.E_D_J_mol)
    a=run_protocol(equal,protocols['hot_then_cold'],n=64,downstream_s=360.)
    b=run_protocol(equal,protocols['cold_then_hot'],n=64,downstream_s=360.)
    control={'E_h_equals_E_D':True,'material_profile_max_difference':float(np.max(abs(np.array(a['material_profile'])-b['material_profile']))),
       'released_difference':abs(a['end']['released_fraction']-b['end']['released_fraction']),
       'available_difference_from_downstream_timing':a['end']['available_fraction']-b['end']['available_fraction']}
    results={'schema':'fusion.surface-recovery-result.v1','input_sha256':h,'frozen_input':frozen,'cases':rows,
      'refinement':refinement,'spectral_checks':steady_checks,'temporal_solver_checks':crosschecks,
      'bulk_acceleration':acceleration,'commuting_material_control':control,'runtime_s':time.perf_counter()-start,
      'environment':{'numpy':np.__version__,'scipy':scipy.__version__},
      'scope':frozen['limits']}
    write(output/'SURFACE_RECOVERY_RESULT.json',results)
    return results

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();r=run(args.output)
    print(json.dumps({'cases':len(r['cases']),'runtime_s':r['runtime_s'],'result':str(args.output/'SURFACE_RECOVERY_RESULT.json')}))
