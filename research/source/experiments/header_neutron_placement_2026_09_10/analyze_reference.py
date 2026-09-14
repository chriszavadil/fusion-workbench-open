from pathlib import Path
import json,math
import numpy as np,pandas as pd,openmc
from materials_and_reference import HERE,F
out=HERE/'reference_run'
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
