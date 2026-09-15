"""Run two admitted upstream GENRAY reference cases; not a reactor validation.
Original orchestration: MIT. Copied upstream inputs retain GPL-3.0-or-later.
"""
from pathlib import Path
import argparse,hashlib,json,math,os,shutil,subprocess,time
import numpy as np
from scipy.io import netcdf_file
PIN='ee443d16e5aaf9bc7227fb3e95581e3ba374df89'
CASES={'canonical_coldray':'genray.dat_CANONICAL_2004_ITER_TEST_one_ray','canonical_relray':'genray.dat_id10iabsorp1'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def clean(v):
 if isinstance(v,bytes):return v.decode('utf-8',errors='replace').replace('\x00','')
 if isinstance(v,np.ndarray):return clean(v.tolist())
 if isinstance(v,np.generic):return clean(v.item())
 if isinstance(v,(list,tuple)):return [clean(x) for x in v]
 if isinstance(v,float) and not math.isfinite(v):return None
 return v

def execute(source,out):
 if out.exists():raise FileExistsError('Evidence directory already exists; do not overwrite runs')
 assert subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()==PIN
 out.mkdir(parents=True);shutil.copyfile(source/'LICENSE',out/'UPSTREAM_LICENSE')
 exe=source/'xgenray';assert exe.is_file();reference=source/'00_Genray_Regression_Tests';reports=[]
 env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',PGPLOT_DEV='/NULL')
 for name,input_name in CASES.items():
  folder=out/name;folder.mkdir();shutil.copyfile(reference/input_name,folder/'genray.dat');shutil.copyfile(reference/'g521022.01000',folder/'g521022.01000')
  started=time.monotonic();timed_out=False
  with (folder/'execution.log').open('w',encoding='utf-8') as log:
   try:p=subprocess.run([str(exe)],cwd=folder,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,timeout=180);exit_code=p.returncode
   except subprocess.TimeoutExpired:exit_code=None;timed_out=True
  result={'case':name,'upstream_pin':PIN,'input_original':input_name,'input_sha256':sha(folder/'genray.dat'),'equilibrium_sha256':sha(folder/'g521022.01000'),'binary_sha256':sha(exe),'exit_code':exit_code,'timeout':timed_out,'seconds':time.monotonic()-started,'experimental_validation':False,'candidate_reactor_run':False,'files':{}}
  nc=folder/'genray.nc'
  if nc.is_file():
   with netcdf_file(nc,'r',mmap=False) as f:
    dataset={'dimensions':dict(f.dimensions),'attributes':{k:clean(v) for k,v in f._attributes.items()},'variables':{k:{'dimensions':list(v.dimensions),'attributes':{a:clean(b) for a,b in v._attributes.items()},'data':clean(v.data.copy())} for k,v in f.variables.items()}}
   (folder/'DATA.json').write_text(json.dumps(dataset,allow_nan=False,separators=(',',':'))+'\n',encoding='utf-8')
   result['variables']={k:{'shape':list(np.shape(v['data'])),'units':v['attributes'].get('units'),'long_name':v['attributes'].get('long_name')} for k,v in dataset['variables'].items()}
   result['scalars']={k:v for k,v in dataset['variables'].items() if np.size(v['data'])<=4}
   result['nc_sha256']=sha(nc)
  else:result['missing_netcdf']=True
  result['files']={p.name:sha(p) for p in folder.iterdir() if p.is_file()}
  (folder/'RESULT.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8');reports.append(result)
  print('REFERENCE_RESULT '+json.dumps(result,allow_nan=False),flush=True)
 summary={'schema':'fusion.genray-reference-run.v1','upstream_pin':PIN,'cases':reports,'matched_candidate_equilibrium':False,'physical_validation':False,'source_equations_modified':False}
 (out/'SUMMARY.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8')
 # Print only active public upstream namelist lines to make settings review possible.
 text=(reference/CASES['canonical_coldray']).read_text(encoding='utf-8',errors='replace');active=[l for l in text.splitlines() if l.strip() and not l.lstrip().startswith(('!','-'))]
 print('UPSTREAM_ACTIVE_INPUT_BEGIN\n'+'\n'.join(active)+'\nUPSTREAM_ACTIVE_INPUT_END',flush=True)
 helptext=(source/'genray_help').read_text(encoding='utf-8',errors='replace').splitlines()
 for i,l in enumerate(helptext):
  if 'ieffic' in l and ('choice' in l.lower() or 'switch' in l.lower()):print('CURRENT_MODEL_DOC\n'+'\n'.join(helptext[max(0,i-2):i+45]),flush=True)
 return 0 if all(r['exit_code']==0 and not r.get('missing_netcdf') for r in reports) else 1
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--upstream',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();raise SystemExit(execute(a.upstream.resolve(),a.output.resolve()))
