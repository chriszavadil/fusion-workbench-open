"""Read-only canonical GENRAY result extraction, not our reactor's ECCD. MIT.
GENRAY code is GPL-3.0-or-later; upstream authors and reference authors credited.
"""
from pathlib import Path
import hashlib,json
import numpy as np
from netCDF4 import Dataset
ROOT=Path(__file__).resolve().parent;RUN=ROOT/'genray-canonical-EC-CPS'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
with Dataset(RUN/'genray.nc') as d:
 count=int(d['nrayelt'][0]);status=int(d['iray_status_nc'][0,0]);tracks={}
 for k in ['wr','wz','wphi','ws','delpwr']:
  a=np.asarray(d[k][0,:count],float)
  if not np.isfinite(a).all():raise ValueError('Nonfinite actual ray')
  tracks[k]=a.tolist()
 scalars={k:float(d[k][...]) for k in ['power_total','powtot_e','toroidal_cur_total']}
 assert count>2 and status==2
result={'schema':'fusion.genray-reference-smoke.v1','source_pin':'ee443d16e5aaf9bc7227fb3e95581e3ba374df89','case':'Upstream canonical2004 ITER EC one-ray test, with R.Prater','not_fusion_workbench_reactor':True,'physical_validation':False,'replication_of_archived_numeric_reference_completed':False,'reference_run_completed':True,'ray_count':1,'recorded_points':count,'ray_stop_status':status,'stop_meaning':'Residual power below configured termination threshold','frequency_GHz':170,'recorded_arrays':tracks,'native_units':{'wr':'cm','wz':'cm','ws':'cm','wphi':'rad','delpwr':'erg/s'},'scalars':scalars,'final_to_initial_ray_power_ratio':tracks['delpwr'][-1]/tracks['delpwr'][0],'source_input_sha256':sha(RUN/'genray.dat'),'source_equilibrium_sha256':sha(RUN/'g521022.01000'),'netcdf_sha256':sha(RUN/'genray.nc'),'binary_sha256':sha(ROOT/'genray-upstream/xgenray'),'graphics_adapter':json.loads((ROOT/'GENRAY_GRAPHICS_ADAPTER.json').read_text()),'reused_work':'Established GENRAY/Prater reference, not a new method or our candidate current prediction','reproduction_notes':'Complete ray arrays exported without truncation. Upstream reference used unchanged input/equilibrium; plotting deviceVCPS changed toCPS to work with project-local Giza. No physics routine changed.'}
(ROOT/'GENRAY_REFERENCE.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['recorded_arrays','graphics_adapter']},indent=2))
