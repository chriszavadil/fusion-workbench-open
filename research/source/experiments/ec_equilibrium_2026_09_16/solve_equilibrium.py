"""Candidate-linked equilibrium construction, not experimental qualification. MIT.
Numerical Grad-Shafranov solver: TokaMaker/Open FUSION Toolkit, original authors.
"""
from pathlib import Path
import os,sys,json,hashlib,time,traceback
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
os.environ['MPLBACKEND']='Agg'
import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.integrate import cumulative_trapezoid
from OpenFUSIONToolkit import OFT_env
from OpenFUSIONToolkit.TokaMaker import TokaMaker
from OpenFUSIONToolkit.TokaMaker.meshing import gs_Domain
from OpenFUSIONToolkit.TokaMaker.util import create_isoflux
ROOT=Path(__file__).resolve().parent

def plain(x):
 if isinstance(x,np.ndarray):return x.tolist()
 if isinstance(x,np.generic):return x.item()
 raise TypeError(type(x).__name__)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(dx,exponent):
 label=f'dx{dx:.2f}_ff{exponent}_v6';out=ROOT/'equilibria'/label
 out.mkdir(parents=True,exist_ok=False);os.chdir(out)
 data=json.loads((ROOT/'EXACT_INPUT.json').read_text());v=data['scalar'];started=time.monotonic()
 record={'id':label,'dx_m':dx,'ffprime_exponent':exponent,'input_sha256':sha(ROOT/'EXACT_INPUT.json'),'admission_sha256':sha(ROOT/'ADMISSION.json'),'physical_validation':False,'scope':'fixed-boundary construction, not original diverted reactor','mapping_iterations':[]}
 (out/'STARTED.json').write_text(json.dumps(record,indent=2)+'\n')
 try:
  oft=OFT_env(nthreads=1,debug_level=0);gs=TokaMaker(oft)
  boundary=create_isoflux(240,v['rmajor'],0.,v['rminor'],v['kappa'],v['triang'])
  mesh=gs_Domain();mesh.define_region('plasma',dx,'plasma');mesh.add_polygon(boundary,'plasma')
  r,lc,reg=mesh.build_mesh();gs.setup_mesh(r,lc,reg);gs.setup_regions()
  gs.settings.free_boundary=False;gs.settings.maxits=100;gs.settings.nl_tol=1e-9
  gs.setup(order=3,F0=v['rmajor']*v['b_plasma_toroidal_on_axis'])
  gs.set_targets(Ip=v['plasma_current'],estore=v['e_plasma_beta'])
  x=np.linspace(0,1,201);rho_map=np.sqrt(x)
  pressure=PchipInterpolator(data['rho'],data['profiles']['pres_plasma_thermal_total_profile'])
  trace_x=np.linspace(.001,.999,199);last_map=None
  for it in range(6):
   ps=pressure(rho_map);ps=(ps-ps[-1])/(ps[0]-ps[-1])
   pp=-PchipInterpolator(x,ps).derivative()(x)
   if not np.isfinite(pp).all() or np.min(pp)<-1e-9:raise ValueError('Pressure gradient is not monotone')
   gs.set_profiles(ffp_prof={'type':'linterp','x':x,'y':(1-x)**exponent},pp_prof={'type':'linterp','x':x,'y':pp})
   if it==0:gs.init_psi()
   solved,nl_iterations=gs.solve(return_its=True)
   map_x=np.linspace(.01,.98,50);volumes=[]
   for pv in map_x:
    curve=gs.trace_surf(float(pv),nresample=256)
    if curve is None or not np.isfinite(curve).all():raise ValueError('Untraceable interior volume contour')
    rr,zz=curve[:,0],curve[:,1];rn,zn=np.roll(rr,-1),np.roll(zz,-1)
    volumes.append(abs(np.sum((rr+rn)*(rr*zn-rn*zz))*np.pi/3))
   full_volume=gs.get_globals()[2];vv=np.r_[0.,volumes,full_volume]
   if np.any(np.diff(vv)<=0):raise ValueError('Nonmonotone enclosed volumes')
   desired=np.sqrt(PchipInterpolator(np.r_[0,map_x,1],vv/full_volume)(x))
   change=float(np.max(abs(desired-rho_map)))
   np.savez_compressed(out/f'volume_map_iteration{it}.npz',psi_norm=np.r_[0,map_x,1],enclosed_volume_m3=vv)
   record['mapping_iterations'].append({'iteration':it,'nonlinear_iterations':nl_iterations,'maximum_rho_map_change':change})
   last_map=desired
   if change<.002:break
   rho_map=.5*rho_map+.5*desired
  stats=gs.get_stats();glob=gs.get_globals();q=gs.get_q(psi=np.array([.01,.05,.5,.95,.98]))
  record.update(numerically_solved=True,stats=stats,Ip_A=float(glob[0]),volume_m3=float(glob[2]),pressure_energy_J=float(1.5*glob[3]),q_sample_psi=q[0],q_sample=q[1],magnetic_axis_m=gs.o_point.copy(),mapping_converged=change<.002)
  record['current_relative_error']=float(glob[0]/v['plasma_current']-1)
  record['energy_relative_error']=float(1.5*glob[3]/v['e_plasma_beta']-1)
  record['volume_relative_to_PROCESS']=float(glob[2]/v['vol_plasma']-1)
  record['q0_reference']=v['q0'];record['q95_reference']=v['q95']
  record['q95_relative_difference']=float(q[1][3]/v['q95']-1)
  record['axis_shift_from_geometric_center_m']=float(gs.o_point[0]-v['rmajor'])
  record['matched_integrals']=abs(record['current_relative_error'])<.002 and abs(record['energy_relative_error'])<.002
  record['proxy_matches_reference_q_screen']=abs(q[1][0]/v['q0']-1)<.05 and abs(record['q95_relative_difference'])<.05
  surfaces=[]
  for p in [.05,.1,.2,.3,.4,.5,.6,.7,.8,.9,.95,.99]:
   curve=gs.trace_surf(p);surfaces.append({'psi_norm':p,'rz_m':curve})
  psi_nodes=gs.get_psi();ff=gs.get_profiles(psi=x)
  np.savez_compressed(out/'SOLUTION.npz',points=r,triangles=lc,regions=reg,psi_norm=psi_nodes,profile_psi=x,rho_volume_map_used=rho_map,rho_volume_map_next=last_map,boundary=boundary,F=ff[1],pressure=ff[3])
  (out/'SURFACES.json').write_text(json.dumps(surfaces,default=plain,allow_nan=False)+'\n')
  gs.save_eqdsk(str(out/'equilibrium.geqdsk'),nr=129,nz=129,rcentr=v['rmajor'],run_info='unqualified-fixed-boundary-construction',cocos=7)
  record['geqdsk_cocos']=7;record['export_completed']=True;record['geqdsk_sha256']=sha(out/'equilibrium.geqdsk');record['solution_sha256']=sha(out/'SOLUTION.npz')
 except Exception:
  record['error']=traceback.format_exc();record.setdefault('numerically_solved',False);print(record['error'],flush=True)
 record['runtime_s']=time.monotonic()-started
 (out/'RESULT.json').write_text(json.dumps(record,indent=2,default=plain,allow_nan=False)+'\n')
 print(json.dumps(record,default=plain),flush=True)
if __name__=='__main__':run(float(sys.argv[1]),int(sys.argv[2]))
