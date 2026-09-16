"""Inverse current-budget diagnostic on preserved unqualified equilibria. MIT.
TokaMaker and Redl implementation are reused, not newly invented or fitted here.
"""
from pathlib import Path
import os,sys,json,hashlib,time,traceback
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
os.environ['MPLBACKEND']='Agg'
import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.integrate import simpson
from OpenFUSIONToolkit import OFT_env
from OpenFUSIONToolkit.TokaMaker import TokaMaker
from OpenFUSIONToolkit.TokaMaker.bootstrap import redl_bootstrap,calculate_ln_lambda,get_jphi_from_GS
from scipy.constants import mu_0,e
ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'publication/research/source/experiments/ec_equilibrium_2026_09_16'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def plain(v):
 if isinstance(v,np.ndarray):return v.tolist()
 if isinstance(v,np.generic):return v.item()
 raise TypeError(type(v).__name__)
def calculate(name):
 out=ROOT/'runs'/name;out.mkdir(parents=True,exist_ok=False);os.chdir(out);start=time.monotonic()
 old=json.loads((SOURCE/'runs'/name/'RESULT.json').read_text());inp=json.loads((SOURCE/'EXACT_INPUT.json').read_text());v=inp['scalar'];kin=json.loads((ROOT/'KINETIC_INPUT.json').read_text())
 record={'id':name,'admission_sha256':sha(ROOT/'ADMISSION.json'),'driver_sha256':sha(Path(__file__)),'kinetic_sha256':sha(ROOT/'KINETIC_INPUT.json'),'old_solution_sha256':sha(SOURCE/'runs'/name/'SOLUTION.npz'),'physical_validation':False,'candidate_current_qualified':False}
 (out/'STARTED.json').write_text(json.dumps(record,indent=2)+'\n')
 try:
  with np.load(SOURCE/'runs'/name/'SOLUTION.npz') as f: saved={k:f[k] for k in f.files}
  gs=TokaMaker(OFT_env(nthreads=1,debug_level=0));gs.setup_mesh(saved['points'],saved['triangles'],saved['regions']);gs.setup_regions()
  gs.settings.free_boundary=False;gs.settings.maxits=100;gs.settings.nl_tol=1e-9;gs.setup(order=3,F0=v['rmajor']*v['b_plasma_toroidal_on_axis'])
  gs.set_targets(Ip=v['plasma_current'],estore=v['e_plasma_beta'])
  x=saved['profile_psi'];rhomap=saved['rho_volume_map_used'];pressure=PchipInterpolator(inp['rho'],inp['profiles']['pres_plasma_thermal_total_profile']);ps=pressure(rhomap);ps=(ps-ps[-1])/(ps[0]-ps[-1]);pp=-PchipInterpolator(x,ps).derivative()(x)
  gs.set_profiles(ffp_prof={'type':'linterp','x':x,'y':(1-x)**old['ffprime_exponent']},pp_prof={'type':'linterp','x':x,'y':pp});gs.init_psi();_,iterations=gs.solve(return_its=True)
  qtest=gs.get_q(psi=np.array(old['q_sample_psi']))[1];qerr=float(np.max(abs(qtest/old['q_sample']-1)));glob=gs.get_globals()
  record['restoration']={'q_relative_error':qerr,'Ip_A':glob[0],'energy_J':1.5*glob[3],'nonlinear_iterations':iterations,'psi_bounds':gs.psi_bounds,'q':qtest,'psi_convention':gs.psi_convention}
  if qerr>2e-4 or abs(glob[0]/v['plasma_current']-1)>.002:raise ValueError('Restored state not sufficiently matched')
  qn=np.linspace(.01,.98,401);_,F,Fprime,P,Pprime=gs.get_profiles(psi=qn);_,q,rg,*_=gs.get_q(psi=qn);_,fc,sr,bsq=gs.sauter_fc(psi=qn)
  record['diagnostic']={'psi_abs_0_1':gs.psinorm_to_absolute(np.array([0.,1.])),'profile_sample':{k:val[[0,200,-1]] for k,val in [('F',F),('Fp',Fprime),('Pp',Pprime),('q',q),('fc',fc)]},'sauter_field_shape':bsq.shape,'field_at_axis':gs.get_field_eval('B').eval(gs.o_point)}
  print('RESTORE_AND_UNITS',json.dumps(record,default=plain),flush=True)
  rho=PchipInterpolator(x,rhomap);kfunc={key:PchipInterpolator(kin['rho_geometric'],kin[key]) for key in ['ne_m3','ni_m3','Te_eV','Ti_eV','Zeff','pe_Pa','pi_Pa']};rh=rho(qn)
  arrays={key:fun(rh) for key,fun in kfunc.items()};ne,ni,Te,Ti,Z= [arrays[key] for key in ['ne_m3','ni_m3','Te_eV','Ti_eV','Zeff']]
  if np.any(fc<0) or np.any(fc>1) or any(not np.isfinite(t).all() or np.min(t)<=0 for t in [ne,ni,Te,Ti,Z]):raise ValueError('Invalid kinetic/geometry coefficient')
  psirange=float(np.diff(gs.psinorm_to_absolute(np.array([0.,1.])))[0]);der={key:fun.derivative()(rh)*rho.derivative()(qn)/psirange for key,fun in kfunc.items()}
  ln_e,ln_i=calculate_ln_lambda(Te,Ti,ne,ni,Z,electron_lnLambda_model='NRL',ion_lnLambda_model='Zavg')
  eps=sr['<a>']/sr['<R>'];nue=6.921e-18*np.abs(q)*rg['<R>']*ne*Z*ln_e/(Te**2*eps**1.5);nui=4.90e-18*np.abs(q)*rg['<R>']*ne*Z*ln_i/(Ti**2*eps**1.5)
  jB,coeff=redl_bootstrap(psi_N=qn,Te=Te,Ti=Ti,ne=ne,ni=ni,pe=arrays['pe_Pa'],pi=arrays['pi_Pa'],Zeff=Z,R=rg['<R>'],q=np.abs(q),eps=eps,fT=1-fc,I_psi=F,dT_e_dpsi=der['Te_eV'],dT_i_dpsi=der['Ti_eV'],dn_e_dpsi=der['ne_m3'],dn_i_dpsi=der['ni_m3'],dp_dpsi=der['pe_Pa']+der['pi_Pa'],ln_lambda_e=ln_e,ln_lambda_ii=ln_i,use_sign_q=False,formula_form='jboot1',nu_e_star_override=nue,nu_i_star_override=nui)
  jtotal=get_jphi_from_GS(F*Fprime,Pprime,rg['<R>'],rg['<1/R>']);record['diagnostic']['jB_samples']=jB[[0,200,-1]];record['diagnostic']['jtotal_samples']=jtotal[[0,200,-1]]
  probe=gs.trace_surf(.5,nresample=32);record['diagnostic']['field_probe']=gs.get_field_eval('B').eval(probe[:3]);record['diagnostic']['grad_probe']=gs.get_field_eval('dPSI').eval(probe[:3]);record['diagnostic']['points_probe']=probe[:3]
  (out/'DIAGNOSTIC.json').write_text(json.dumps(record,indent=2,default=plain)+'\n');print('GEOMETRY_DIAGNOSTIC',json.dumps(record['diagnostic'],default=plain),flush=True)
  return locals()
 except Exception:
  record['error']=traceback.format_exc();record['runtime_s']=time.monotonic()-start;(out/'FAILED.json').write_text(json.dumps(record,indent=2,default=plain)+'\n');print(record['error'],flush=True);raise
if __name__=='__main__':state=calculate(sys.argv[1])
