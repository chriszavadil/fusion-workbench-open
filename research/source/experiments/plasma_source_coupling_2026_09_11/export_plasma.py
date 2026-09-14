"""Reproduce the approved candidate, export its actual source profiles. MIT."""
from pathlib import Path
import hashlib,importlib.util,json,os,sys,shutil
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMBA_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
os.environ['MPLBACKEND']='Agg'
ROOT=Path(__file__).resolve().parent;HOME=ROOT.parent;APP=HOME/'FusionWorkbench-transport-lab-20260910/Source'
sys.path.insert(0,str(APP/'tools'));from process_worker import install_reporting_metadata,git_output
from evidence import read_mfile
UP=HOME/'PROCESS-v3.4.2';M=json.loads((APP/'research/SOLVER_MANIFEST.json').read_text());pin=git_output(UP,'rev-parse','HEAD')
assert pin==M['upstream'] and not git_output(UP,'status','--porcelain')
for row in M['runtime_modules'].values():
 p=APP/row['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'];s=importlib.util.spec_from_file_location(p.stem,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);m.install()
row=M['configurations']['r838'];p=APP/row['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']
out=ROOT/'plasma_reproduction';out.mkdir(exist_ok=False);shutil.copyfile(p,out/'case_IN.DAT')
install_reporting_metadata(UP)
from process.main import SingleRun
run=SingleRun((out/'case_IN.DAT').as_posix());run.run();v=read_mfile(out/'case_MFILE.DAT');assert v['ifail']==1
from process.models.physics.fusion_reactions import bosch_hale_reactivity,BoschHaleConstants,REACTION_CONSTANTS_DT
import numpy as np
from scipy.integrate import simpson
p=run.data.physics;pr=run.models.plasma_profile;rho=pr.neprofile.profile_x;ne=pr.neprofile.profile_y;te=pr.teprofile.profile_y;ti=te*p.temp_plasma_ion_vol_avg_kev/p.temp_plasma_electron_vol_avg_kev
rate=bosch_hale_reactivity(ti,BoschHaleConstants(**REACTION_CONSTANTS_DT))*(ne/p.nd_plasma_electrons_vol_avg*p.nd_plasma_fuel_ions_vol_avg)**2*p.f_plasma_fuel_deuterium*p.f_plasma_fuel_tritium
integral=simpson(2*rho*rate,x=rho)*p.vol_plasma
obj={'schema':'fusion.candidate-plasma-profile.v1','configuration':'r838','input_sha256':row['sha256'],'mfile_sha256':hashlib.sha256((out/'case_MFILE.DAT').read_bytes()).hexdigest(),'upstream':pin,'rho':rho.tolist(),'electron_density_m3':ne.tolist(),'ion_temperature_keV':ti.tolist(),'DT_emission_m3_s':rate.tolist(),'DT_neutrons_per_second':float(integral),'geometry':{k:float(getattr(p,k)) for k in ['rmajor','rminor','kappa','triang','vol_plasma']},'archived_major_radius_m':8.379532870755202,'new_major_radius_m':v['rmajor'],'physical_validation':False}
(ROOT/'PLASMA_SOURCE.json').write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n',encoding='utf-8');print('EXPORTED_SOURCE',len(rho),integral,v['rmajor'])
