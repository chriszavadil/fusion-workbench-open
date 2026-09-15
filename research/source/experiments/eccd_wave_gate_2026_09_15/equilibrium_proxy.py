"""Candidate-linked fixed-boundary interface test using existing TokaMaker. MIT.
No fitted launch, source power increase, free-boundary coil or stability validation.
"""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time,traceback
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='1'
os.environ['MPLBACKEND']='Agg'
import numpy as np
from scipy.interpolate import PchipInterpolator

def serial(v):
 if isinstance(v,np.ndarray):return v.tolist()
 if isinstance(v,np.generic):return v.item()
 if isinstance(v,dict):return {k:serial(x) for k,x in v.items()}
 if isinstance(v,(tuple,list)):return [serial(x) for x in v]
 return v

def solve(profile_path,out,dx):
 from OpenFUSIONToolkit import OFT_env
 from OpenFUSIONToolkit.TokaMaker import TokaMaker
 from OpenFUSIONToolkit.TokaMaker.meshing import gs_Domain
 from OpenFUSIONToolkit.TokaMaker.util import create_isoflux
 d=json.loads(profile_path.read_text());p=d['physics_scalars'];rho=np.asarray(d['rho']);ne=np.asarray(d['ne_m3']);te=np.asarray(d['te_keV'])
 for name in ['rmajor','rminor','kappa','triang','b_plasma_toroidal_on_axis','plasma_current','pres_plasma_thermal_on_axis']:assert name in p,name
 assert len(rho)==len(ne)==len(te) and np.all(np.diff(rho)>0) and np.all(ne>0) and np.all(te>0)
 energy_name=next((k for k in ['e_plasma_beta','e_plasma_thermal_total'] if k in p and p[k]>0),None)
 contour=create_isoflux(240,p['rmajor'],0.,p['rminor'],p['kappa'],p['triang'])
 mesh=gs_Domain();mesh.define_region('plasma',dx,'plasma');mesh.add_polygon(contour,'plasma');points,cells,reg=mesh.build_mesh()
 env=OFT_env(nthreads=1);gs=TokaMaker(env);gs.setup_mesh(points,cells);gs.settings.free_boundary=False;gs.settings.maxits=100;gs.setup(order=2,F0=p['rmajor']*p['b_plasma_toroidal_on_axis'])
 psi=np.linspace(0.,1.,201);shape=PchipInterpolator(rho*rho,(ne*te)/(ne[0]*te[0]));pp=-shape.derivative()(psi);assert np.min(pp)>-1e-10;pp=np.maximum(pp,0);pp/=max(pp)
 ff=1.-psi
 gs.set_profiles(ffp_prof={'type':'linterp','x':psi,'y':ff},pp_prof={'type':'linterp','x':psi,'y':pp})
 if energy_name:gs.set_targets(Ip=p['plasma_current'],estore=p[energy_name])
 else:gs.set_targets(Ip=p['plasma_current'],pax=p['pres_plasma_thermal_on_axis'])
 gs.init_psi();eq,iterations=gs.solve(return_its=True);stats=gs.get_stats();q=gs.get_q(psi=np.linspace(.001,.99,151));profiles=gs.get_profiles(psi=np.linspace(0.,1.,201))
 assert np.isfinite(np.asarray(q[1])).all() and np.isfinite(np.asarray(profiles[3])).all()
 assert profiles[3][0]>profiles[3][-1], 'Pressure convention mismatch; do not export wave equilibrium'
 surfaces={str(x):np.asarray(gs.trace_surf(x)).tolist() for x in [.1,.3,.5,.7,.9]}
 result={'schema':'fusion.provisional-equilibrium.v1','mesh_dx_m':dx,'iterations':iterations,'profile_sha256':hashlib.sha256(profile_path.read_bytes()).hexdigest(),'stats':serial(stats),'q':serial(q),'source_profiles':serial(profiles),'contour_m':contour.tolist(),'surfaces_m':surfaces,'mesh_points_m':gs.r.tolist(),'mesh_triangles':gs.lc.tolist(),'psi_normalized':gs.get_psi().tolist(),'target_Ip_A':p['plasma_current'],'energy_target_name':energy_name,'energy_target_J':p.get(energy_name) if energy_name else None,'target_axis_thermal_pressure_Pa':p['pres_plasma_thermal_on_axis'],'candidate_q0':p.get('q0'),'candidate_q95':p.get('q95'),'candidate_volume_m3':p.get('vol_plasma'),'candidate_beta':p.get('beta_total_vol_avg'),'numerically_converged':True,'matched_current_profile':False,'fixed_boundary_without_xpoint':True,'physical_validation':False,'mapping_assumption':'PROCESS minor-radius profiles are provisionally mapped to sqrt normalized poloidal flux; FFprime shape is decreasing linear and not fitted; total-energy pressure shape shares the thermal shape.','eqdsk_export_passed':False,'eqdsk_edge_pad':.01,'eqdsk_truncate_equilibrium':False}
 dest=out/'EQUILIBRIUM.json';dest.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
 eqfile=out/'candidate_proxy.geqdsk'
 try:
  gs.save_eqdsk(str(eqfile),nr=129,nz=129,rcentr=p['rmajor'],lcfs_pad=.01,truncate_eq=False,run_info='FusionWork provisional fixed boundary')
  result.update(eqdsk_export_passed=True,equilibrium_sha256=hashlib.sha256(eqfile.read_bytes()).hexdigest())
 except Exception as e:result['eqdsk_export_error']=str(e)
 dest.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print('EQUILIBRIUM_RESULT '+json.dumps({k:v for k,v in result.items() if k not in ['q','source_profiles','contour_m','surfaces_m','mesh_points_m','mesh_triangles','psi_normalized']}),flush=True)
 if not result['eqdsk_export_passed']:raise RuntimeError('Equilibrium computed but gEQDSK export failed; no wave transfer')

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--profiles',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--child',action='store_true');ap.add_argument('--dx',type=float);a=ap.parse_args();p=a.profiles.resolve();out=a.output.resolve()
 if a.child:return solve(p,out,a.dx)
 if out.exists():raise FileExistsError('Previous equilibrium evidence exists')
 out.mkdir(parents=True);statuses=[]
 for dx in [.15,.075]:
  folder=out/f'mesh_{dx}';folder.mkdir();start=time.monotonic()
  with (folder/'execution.log').open('w') as log:
   try:r=subprocess.run([sys.executable,__file__,'--profiles',str(p),'--output',str(folder),'--child','--dx',str(dx)],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,timeout=120);status={'exit_code':r.returncode,'timeout':False}
   except subprocess.TimeoutExpired:status={'exit_code':None,'timeout':True}
  status['seconds']=time.monotonic()-start;(folder/'STATUS.json').write_text(json.dumps(status,indent=2)+'\n');statuses.append(status);print('EQUILIBRIUM_STATUS '+json.dumps(status),flush=True)
 return 0 if all(x['exit_code']==0 for x in statuses) else 1
if __name__=='__main__':raise SystemExit(main())
