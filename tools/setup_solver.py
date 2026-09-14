"""Optional local solver installation. Never expose this worker to the Internet.
Explicit --install creates an isolated environment and fetches the pinned UKAEA source.
"""
import argparse,hashlib,json,os,subprocess,sys,venv
from pathlib import Path
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ROOT=Path(__file__).resolve().parents[1]
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--install',action='store_true');a=p.parse_args()
 if not a.install:raise SystemExit('Explicit --install is required; review README before creating a local solver environment.')
 if not (3,10)<=sys.version_info[:2]<=(3,12):raise SystemExit('Use Python 3.10-3.12; the archived reference was checked on Python 3.10.')
 manifest=json.loads((ROOT/'research/SOLVER_MANIFEST.json').read_text());local=ROOT/'.local';local.mkdir(exist_ok=True)
 src=local/'PROCESS-v3.4.2';v=local/'solver-venv'
 if not src.exists():subprocess.run(['git','clone','--depth','1','--branch','v3.4.2',manifest['upstream_repository'],str(src)],check=True)
 pin=subprocess.check_output(['git','-C',str(src),'rev-parse','HEAD'],text=True).strip()
 if pin!=manifest['upstream']:raise SystemExit('Upstream revision mismatch; no installation performed.')
 if not v.exists():venv.EnvBuilder(with_pip=True).create(v)
 python=v/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
 subprocess.run([str(python),'-m','pip','install','-r',str(ROOT/'research/requirements-solver.txt'),'-e',str(src)],check=True)
 cfg={'python':str(python.resolve()),'source':str(src.resolve()),'upstream':pin,'configurations':{},'runtime_modules':{}}
 for ident,row in manifest['configurations'].items():
  path=ROOT/row['path']
  if digest(path)!=row['sha256']:raise SystemExit('Approved input changed; review before creating a worker configuration.')
  cfg['configurations'][ident]={'input':str(path.resolve()),'input_sha256':row['sha256']}
 for name,row in manifest['runtime_modules'].items():
  path=ROOT/row['path']
  if digest(path)!=row['sha256']:raise SystemExit('Runtime adapter changed; review required.')
  cfg['runtime_modules'][name]={'path':str(path.resolve()),'sha256':row['sha256']}
 (local/'execution.json').write_text(json.dumps(cfg,indent=2)+'\n',encoding='utf-8');print('Local solver configured. Launch the worker separately; no research runs or public services were started.')
if __name__=='__main__':main()
