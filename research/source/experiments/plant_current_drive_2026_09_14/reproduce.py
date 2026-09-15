"""Optional bounded reproduction; not executed by the web app or CI. Original MIT.
Use a Python environment with the pinned PROCESS dependencies. No installation,
network requests, accepted-reference changes, or public worker exposure occur.
This portable wrapper is new; the reported runs used preserved local drivers.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,shutil,subprocess,sys
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS'):os.environ[k]='1'
os.environ['MPLBACKEND']='Agg'
PIN='c0ae5b28649f2b20fb7efc7904628b6defe4151c'
HERE=Path(__file__).resolve().parent
from prepare_inputs import make_input

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(source,*args):
 executable=shutil.which('git')
 if not executable:raise RuntimeError('Git is required for source verification')
 return subprocess.check_output([executable,'-C',str(source),*args],text=True,encoding='utf-8',timeout=15).strip()
def child(root,source,out):
 if git(source,'rev-parse','HEAD')!=PIN or git(source,'status','--porcelain'):raise ValueError('Wrong or modified PROCESS source')
 manifest=json.loads((root/'research/SOLVER_MANIFEST.json').read_text(encoding='utf-8'))
 sys.path.insert(0,str(source));sys.path.insert(0,str(root/'tools'))
 for name in ('windows_output_fix.py','adaptive_fatigue.py','mission_constraint.py'):
  row=manifest['runtime_modules'][name];p=root/row['path']
  if digest(p)!=row['sha256']:raise ValueError('Runtime adapter changed: '+name)
  spec=importlib.util.spec_from_file_location(p.stem,p);obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);obj.install()
 import process.core.init as init
 init.get_git_summary=lambda:('pinned-official-source',PIN[:12])
 from process.main import SingleRun
 from evidence import read_mfile,project_configuration
 inp=out/'case_IN.DAT';SingleRun(inp.as_posix()).run();raw=out/'case_MFILE.DAT';v=read_mfile(raw)
 result={'upstream':PIN,'input_sha256':digest(inp),'output_sha256':digest(raw),'numerically_converged':v.get('ifail')==1,'physical_validation':False,'accepted_reference_replaced':False}
 if result['numerically_converged']:
  c=project_configuration(raw,'reproduction','Unaccepted reproduction');result['metrics']=c['metrics'];result['verification']=c['verification']
 (out/'reproduction-result.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
 print(json.dumps(result),flush=True)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workbench',type=Path,required=True);p.add_argument('--process-source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--reserve',type=int,choices=[75,30],required=True);p.add_argument('--child',action='store_true');a=p.parse_args()
 root,source,out=a.workbench.resolve(),a.process_source.resolve(),a.output.resolve()
 if a.child:return child(root,source,out)
 if out.exists():raise FileExistsError('Choose a new case directory; existing results are not overwritten')
 raw=make_input((root/'research/approved_inputs/r838.IN.DAT').read_bytes(),a.reserve)
 if git(source,'rev-parse','HEAD')!=PIN or git(source,'status','--porcelain'):raise ValueError('Wrong or modified PROCESS source')
 out.mkdir(parents=True);(out/'case_IN.DAT').write_bytes(raw)
 command=[sys.executable,str(HERE/'reproduce.py'),'--workbench',str(root),'--process-source',str(source),'--output',str(out),'--reserve',str(a.reserve),'--child']
 with (out/'execution-private.log').open('w',encoding='utf-8') as log:
  try:
   completed=subprocess.run(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,timeout=240)
   status={'exit_code':completed.returncode,'timeout':False}
  except subprocess.TimeoutExpired:status={'exit_code':None,'timeout':True}
 (out/'execution-status.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8');print(json.dumps(status))
 if status['timeout'] or status['exit_code']:raise SystemExit(1)
if __name__=='__main__':main()
