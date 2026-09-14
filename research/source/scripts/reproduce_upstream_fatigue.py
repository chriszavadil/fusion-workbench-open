#!/usr/bin/env python3
"""Bounded independent reproduction of a specific upstream numerical discrepancy.

Executes hash-verified PROCESS method bodies in isolation, not the full systems
code. Decorators/imports are omitted; the method mathematics is unchanged.
A second calculation changes only the explicit crack step; a third integrates
with events and calls the same upstream stress-intensity function. None of these
is a measurement of material life or a certification of an actual magnet.
"""
from __future__ import annotations
import argparse, ast, copy, hashlib, json, math, platform
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import scipy
from scipy.integrate import solve_ivp
from audit_coupled_candidate import load_baseline, fatigue

ROOT = Path(__file__).resolve().parents[1]
VERSIONS = {
 'v3.4.2': ('c0ae5b28649f2b20fb7efc7904628b6defe4151c','cs_fatigue_v3_4_2.py','9252217d4e1b259b02cf9b6c1dc92bba8a29ce9d'),
 'main_at_audit': ('620d1e9a38f1b3c6d2597956c8556e9ab6c17037','cs_fatigue_current.py','eac6720169e18bd884de90bf081c91d1cb2d8a28'),
}
PARAMS = dict(paris_power_law=3.5,walker_coefficient=.436,paris_coefficient=65e-14,
 sf_vertical_crack=2.,sf_radial_crack=2.,fracture_toughness=200.,sf_fast_fracture=1.5)


def git_blob(data: bytes) -> str:
 return hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest()


def methods(version: str, step_m: float|None=None):
 commit, filename, expected = VERSIONS[version]
 source=ROOT/'external/process'/filename; data=source.read_bytes()
 if git_blob(data)!=expected: raise ValueError(f'Upstream source hash mismatch: {source}')
 tree=ast.parse(data); cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='CsFatigue')
 nodes={n.name:copy.deepcopy(n) for n in cls.body if isinstance(n,ast.FunctionDef)}
 selected=[nodes[k] for k in ['ncycle','surface_stress_intensity_factor']]
 body_hashes={n.name:hashlib.sha256(ast.dump(ast.Module(body=n.body,type_ignores=[]),include_attributes=False).encode()).hexdigest() for n in selected}
 # Remove decorators only, retaining all body statements and parameter signatures.
 for n in selected: n.decorator_list=[]
 if step_m is not None:
  if not math.isfinite(step_m) or not 0<step_m<=1e-4: raise ValueError('Invalid crack step')
  targets=[n for n in ast.walk(selected[0]) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='delta' for t in n.targets)]
  if len(targets)!=1 or not isinstance(targets[0].value,ast.Constant) or targets[0].value.value!=1e-4:
   raise ValueError('Expected one explicit native crack-step assignment')
  targets[0].value=ast.Constant(step_m)
 ns={'np':np}; mod=ast.fix_missing_locations(ast.Module(body=selected,type_ignores=[]))
 exec(compile(mod,str(source),'exec'),ns)
 obj=SimpleNamespace(data=SimpleNamespace(cs_fatigue=SimpleNamespace(**PARAMS)),surface_stress_intensity_factor=ns['surface_stress_intensity_factor'])
 return ns['ncycle'],obj,ns['surface_stress_intensity_factor'],{'commit':commit,'source_git_blob':expected,'body_hashes':body_hashes,'step_override_m':step_m}


def native(case: dict, version='main_at_audit', step_m=None) -> float:
 fun,obj,_,_=methods(version,step_m)
 result=fun(obj,case['stress_pa'],case['residual_pa'],case['initial_a_m'],case['conduit_t_m'],case['conduit_w_m'])
 return float(result[0])


def adaptive(case: dict, version='main_at_audit', method='DOP853',rtol=1e-11) -> dict:
 _,_,sif,_=methods(version);m=PARAMS['paris_power_law']
 stress=case['stress_pa']/1e6;res=case['residual_pa']/1e6; t=case['conduit_t_m'];w=case['conduit_w_m']
 a0=case['initial_a_m']; c0=3*a0;limit_a=t/2;limit_c=w/2;Kmax=200/1.5
 if min(stress,t,w,a0)<=0 or not all(map(math.isfinite,[stress,t,w,a0,res])):
  raise ValueError('Invalid physical model input')
 cr=PARAMS['paris_coefficient']/(1-res/(stress+res))**(-m*(PARAMS['walker_coefficient']-1))
 phi=np.array([np.pi/2,0.])
 def k(a,c):return sif(stress,t,w,a,c,phi)
 if a0>=limit_a or c0>=limit_c or np.max(k(a0,c0))>=Kmax:raise ValueError('Initial failure boundary')
 def rhs(a,y):
  ka,kc=k(a,y[0]);return [(kc/ka)**m,1/(2*cr*ka**m)]
 def radial(a,y):return limit_c-y[0]
 def fast_fracture(a,y):return Kmax-float(np.max(k(a,y[0])))
 radial.terminal=fast_fracture.terminal=True;radial.direction=fast_fracture.direction=-1
 sol=solve_ivp(rhs,(a0,limit_a),[c0,0.],events=[radial,fast_fracture],method=method,rtol=rtol,atol=[1e-14,1e-8],max_step=(limit_a-a0)/100)
 if not sol.success:raise RuntimeError(sol.message)
 return {'cycles':float(sol.y[1,-1]),'final_a_m':float(sol.t[-1]),'final_c_m':float(sol.y[0,-1]),
         'termination':'radial_crack' if len(sol.t_events[0]) else 'fast_fracture' if len(sol.t_events[1]) else 'vertical_crack',
         'method':method,'rtol':rtol,'nfev':sol.nfev}


def run(archive: Path, output: Path):
 v,mhash=load_baseline(archive);output.mkdir(parents=True,exist_ok=True)
 # Published fixture + historical project cases. The last case is an explicit
 # adversarial decision witness, selected near the already known boundary.
 common={'residual_pa':240e6,'initial_a_m':.00089}
 cases=[
  {'id':'upstream_regression_fixture',**common,'stress_pa':659999225.25370133,'conduit_t_m':.0063104538380405924,'conduit_w_m':.0063104538380405924,'upstream_expected_native':1113.5875631615095},
  {'id':'authenticated_PR42_baseline',**common,'stress_pa':v['stress_hoop_cs_inner'],'conduit_t_m':v['dz_cs_turn_conduit'],'conduit_w_m':v['dr_cs_turn_conduit'],'upstream_expected_native':v['n_cycle']},
  {'id':'prior_rounded_candidate',**common,'stress_pa':293.95e6,'conduit_t_m':.009813,'conduit_w_m':.009813},
  {'id':'adversarial_20000_cycle_witness',**common,'stress_pa':290e6,'conduit_t_m':.009813,'conduit_w_m':.009813,'selection':'Adaptive to prior audit, not held-out or optimized reactor geometry'}
 ]
 plan={'schema':'fusion-solution-set.upstream-fatigue-plan.v1','versions':VERSIONS,'parameters':PARAMS,'cases':cases,
       'steps_m':[1e-4,5e-5,1e-5,1e-6],'decision_threshold_cycles':20000,'baseline_mfile_sha256':mhash,
       'question':'Does the exact upstream method body reproduce the discrepancy, and can it change the numerical constraint decision?',
       'bounded_stop':'One current/pinned comparison and reproduction packet; no indefinite uncalibrated fatigue sweeps.'}
 (output/'UPSTREAM_FATIGUE_FROZEN_INPUT.json').write_text(json.dumps(plan,indent=2,sort_keys=True)+'\n')
 rows=[]
 for case in cases:
  pin=native(case,'v3.4.2');cur=native(case);dop=adaptive(case);rk=adaptive(case,method='RK45')
  independent=fatigue(case['stress_pa']/1e6,case['conduit_t_m'])
  rows.append({'case':case,'pinned_native_cycles':pin,'current_native_cycles':cur,
   'native_step_refinement':[{'step_m':s,'cycles':native(case,step_m=s)} for s in plan['steps_m']],
   'adaptive_native_SIF_DOP853':dop,'adaptive_native_SIF_RK45':rk,
   'prior_independent_algebra_cycles':independent['cycles'],
   'current_native_minus_adaptive_cycles':cur-dop['cycles'],
   'relative_to_adaptive_percent':100*(cur/dop['cycles']-1),
   'native_pass_20000':cur>=20000,'adaptive_pass_20000':dop['cycles']>=20000})
 out={'schema':'fusion-solution-set.upstream-fatigue-reproduction.v1','frozen_plan_sha256':hashlib.sha256((output/'UPSTREAM_FATIGUE_FROZEN_INPUT.json').read_bytes()).hexdigest(),
      'source_provenance':{k:methods(k)[3] for k in VERSIONS},'results':rows,
      'environment':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__},
      'execution_scope':'Two hash-verified upstream method bodies executed with numpy and supplied data attributes. Imports/decorators and full PROCESS framework were NOT executed.',
      'scientific_scope':'Software numerical verification only; no measured fatigue lifetime, full reactor feasibility, universal error bound, or novel fracture-mechanics method.'}
 (output/'UPSTREAM_FATIGUE_REPRODUCTION.json').write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+'\n')
 print(json.dumps([{'case':r['case']['id'],'native':r['current_native_cycles'],'adaptive':r['adaptive_native_SIF_DOP853']['cycles'],'flip':r['native_pass_20000']!=r['adaptive_pass_20000']} for r in rows],indent=2))
 return out

if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--archive',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args();run(args.archive,args.output)
