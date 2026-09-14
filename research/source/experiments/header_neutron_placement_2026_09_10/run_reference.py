"""Bounded replay of unchanged public OKTAVIAN-Al source/geometry/tallies."""
from pathlib import Path
import json,math,os,subprocess
import numpy as np,pandas as pd,openmc
from materials_and_reference import HERE,F,reference
xs=Path((HERE/'local_cross_sections_path.txt').read_text().strip());openmc.config['cross_sections']=xs
out=HERE/'reference_run'
if out.exists():raise RuntimeError('Refuse to overwrite previous reference')
out.mkdir();model=reference();model.settings.seed=731091;model.settings.batches=40;model.settings.particles=25000
model.export_to_xml(directory=out)
(HERE/'REFERENCE_ADMISSION.json').write_text(json.dumps({'benchmark_pin':F['benchmark_pin'],'exact_code_sha256':F['benchmark_model_sha256'],'changes':'Only batches,particles,thread count and explicit random seed; source,geometry,tallies unchanged.','histories':1000000,'comparison':'Archived OpenMC0.14 ENDFB8 leakage spectra per source neutron per surface area; not reactor breeding validation.','acceptance':'Integrated neutron leakage agrees within3%; populated bin MonteCarlo consistency recorded,not fitted.','experimental_data':'Retained separately; instrument/energy-bin conventions not accepted as calibrated candidate evidence.'},indent=2)+'\n')
env=os.environ.copy();env['OPENMC_CROSS_SECTIONS']=str(xs);env['OMP_NUM_THREADS']='2'
with (out/'execution.log').open('w') as log:r=subprocess.run([str(Path(__import__('sys').executable).with_name('openmc')),'-s','2'],cwd=out,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,timeout=600)
if r.returncode:raise RuntimeError('Reference OpenMC failed; see local log')
result={'physical_validation':False,'benchmark':'OKTAVIAN-Al published CSG computational replay','cases':{}}
with openmc.StatePoint(out/'statepoint.40.h5') as sp:
 for name in ('nspectrum','gspectrum'):
  tally=sp.get_tally(name=name);bins=tally.find_filter(openmc.EnergyFilter).bins;df=pd.DataFrame({'energy low [eV]':bins[:,0],'energy high [eV]':bins[:,1],'mean':tally.mean.ravel(),'std. dev.':tally.std_dev.ravel()});old=pd.read_hdf(HERE/'ofb/results_database/oktavian_al/openmc-0-14-0_endfb80.h5',key=name)
  area=4*math.pi*19.95**2;df['mean']/=area;df['std. dev.']/=area
  if not np.allclose(df['energy low [eV]'],old['energy low [eV]']):raise ValueError('Reference energy bounds differ')
  df.to_csv(out/(name+'.csv'),index=False);sigma=np.sqrt(df['std. dev.']**2+old['std. dev.']**2);usable=(df['mean']>0)&(old['mean']>0)&(sigma>0)
  z=(df['mean']-old['mean'])/sigma;ratio=df['mean'].sum()/old['mean'].sum()
  result['cases'][name]={'integrated_ratio_to_archived':float(ratio),'bins':len(df),'populated_bins':int(usable.sum()),'fraction_populated_within_3sigma':float((abs(z[usable])<=3).mean()),'largest_z':float(abs(z[usable]).max()),'pass_integrated_3percent':bool(abs(ratio-1)<.03)}
result['computational_replay_passed']=result['cases']['nspectrum']['pass_integrated_3percent'];(HERE/'REFERENCE_RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
