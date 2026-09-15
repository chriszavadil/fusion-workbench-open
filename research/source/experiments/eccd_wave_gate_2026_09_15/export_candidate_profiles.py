"""One admitted profile reproduction and solver-interface inspection. Original MIT."""
from pathlib import Path
import argparse,dataclasses,hashlib,importlib.util,inspect,json,os,shutil,subprocess,sys
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMBA_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='1'
os.environ['MPLBACKEND']='Agg'
import numpy as np
PIN='c0ae5b28649f2b20fb7efc7904628b6defe4151c'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def numeric(value):
 if isinstance(value,np.ndarray):return value.tolist()
 if isinstance(value,np.generic):return value.item()
 return value

def child(root,source,out):
 assert subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()==PIN
 sys.path.insert(0,str(source));sys.path.insert(0,str(root/'tools'))
 manifest=json.loads((root/'research/SOLVER_MANIFEST.json').read_text(encoding='utf-8'))
 for item in manifest['runtime_modules'].values():
  path=root/item['path'];assert sha(path)==item['sha256'];spec=importlib.util.spec_from_file_location(path.stem,path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);mod.install()
 import process.core.init as init
 init.get_git_summary=lambda:('pinned-source',PIN[:12])
 from process.main import SingleRun
 from evidence import read_mfile
 inp=root/'research/source/experiments/plant_current_drive_2026_09_14/runs/pulsedFixedR30/case_IN.DAT';assert sha(inp)=='6335932f13fe7962a3e81829a6da4ff9055909e8257c275df0a742b723a46f2a'
 shutil.copyfile(inp,out/'case_IN.DAT');run=SingleRun((out/'case_IN.DAT').as_posix());run.run();v=read_mfile(out/'case_MFILE.DAT')
 checks={'ifail':v.get('ifail'),'net_power_relative_difference':abs(v.get('p_plant_electric_net_mw',0)/501.6592774049162-1),'radius_difference_m':abs(v.get('rmajor',0)-8.379532870755202)}
 (out/'REPRODUCTION_CHECK.json').write_text(json.dumps(checks,indent=2)+'\n',encoding='utf-8')
 if checks['ifail']!=1 or checks['net_power_relative_difference']>1e-4 or checks['radius_difference_m']>1e-6:raise ValueError('Candidate reproduction mismatch; do not transfer profiles')
 p=run.data.physics;pr=run.models.plasma_profile
 names=[f.name for f in dataclasses.fields(p)] if dataclasses.is_dataclass(p) else [k for k in dir(p) if not k.startswith('_')]
 items={k:getattr(p,k) for k in names}
 scalars={k:numeric(val) for k,val in items.items() if isinstance(val,(int,float,bool,np.integer,np.floating)) and np.isfinite(val)}
 arrays={k:val.tolist() for k,val in items.items() if isinstance(val,np.ndarray) and val.size<=10000 and np.issubdtype(val.dtype,np.number) and np.isfinite(val).all()}
 data={'schema':'fusion.higher-output-plasma.v1','input_sha256':sha(inp),'mfile_sha256':sha(out/'case_MFILE.DAT'),'upstream_pin':PIN,'physics_scalars':scalars,'physics_arrays':arrays,'rho':pr.neprofile.profile_x.tolist(),'ne_m3':pr.neprofile.profile_y.tolist(),'te_keV':pr.teprofile.profile_y.tolist(),'profile_coordinate':'PROCESS normalized minor radius; not yet a magnetic-flux coordinate','checks':checks,'matched_equilibrium_available':False,'physical_validation':False}
 (out/'PROFILES.json').write_text(json.dumps(data,indent=2,allow_nan=False)+'\n',encoding='utf-8')
 print('PROFILE_EXPORT '+json.dumps({'checks':checks,'rho_points':len(data['rho']),'scalars':scalars}),flush=True)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--source',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--child',action='store_true');a=ap.parse_args();root,source,out=a.root.resolve(),a.source.resolve(),a.output.resolve()
 if a.child:return child(root,source,out)
 if out.exists():raise FileExistsError('Do not overwrite evidence')
 out.mkdir(parents=True)
 from OpenFUSIONToolkit.TokaMaker import TokaMaker
 from OpenFUSIONToolkit.TokaMaker import meshing,util
 selected=['setup_mesh','setup','set_targets','set_profiles','init_psi','solve','get_stats','get_profiles','get_q','save_eqdsk','get_psi','get_vac_flux','flux_surface_average','get_field_eval','trace_surf']
 methods={n:inspect.getsource(getattr(TokaMaker,n)) for n in selected if hasattr(TokaMaker,n)}
 (out/'OFT_INTERFACE.json').write_text(json.dumps(methods,indent=2)+'\n',encoding='utf-8')
 (out/'OFT_CREATE_BOUNDARY.txt').write_text(inspect.getsource(util.create_isoflux),encoding='utf-8')
 with (out/'profile-execution.log').open('w',encoding='utf-8') as log:
  try:p=subprocess.run([sys.executable,__file__,'--root',str(root),'--source',str(source),'--output',str(out),'--child'],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,timeout=240);status={'exit_code':p.returncode,'timeout':False}
  except subprocess.TimeoutExpired:status={'exit_code':None,'timeout':True}
 (out/'STATUS.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8');print('PROFILE_STATUS '+json.dumps(status),flush=True)
 if (out/'PROFILES.json').exists():print('PROFILE_SUMMARY '+(out/'REPRODUCTION_CHECK.json').read_text(),flush=True)
 return 0 if status['exit_code']==0 else 1
if __name__=='__main__':raise SystemExit(main())
