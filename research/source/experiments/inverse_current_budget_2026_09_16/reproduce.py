"""Bounded optional reproduction using the preserved source and installed OFT26.9. MIT.
This wrapper was not used for the first executed cases; original drivers are retained.
"""
from pathlib import Path
import argparse,json,shutil,subprocess,sys
HERE=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--case',required=True,choices=['dx0.18_ff1_v6','dx0.18_ff2_v6','dx0.09_ff1_v6','dx0.09_ff2_v6']);p.add_argument('--output',type=Path,required=True);p.add_argument('--child',action='store_true');a=p.parse_args()
out=a.output.resolve()
if a.child:
 import importlib.metadata
 if importlib.metadata.version('openfusiontoolkit')!='26.9':raise ValueError('Use the recorded OFT version or separately investigate a version change')
 import current_budget as c
 from finish_budget import finish
 c.ROOT=out;c.SOURCE=HERE.parent/'ec_equilibrium_2026_09_16'
 state=c.calculate(a.case);finish(state)
else:
 out.mkdir(parents=True,exist_ok=False)
 for name in ['KINETIC_INPUT.json','ADMISSION.json']:shutil.copyfile(HERE/name,out/name)
 command=[sys.executable,str(Path(__file__).resolve()),'--case',a.case,'--output',str(out),'--child']
 with (out/'execution-private.log').open('w',encoding='utf-8') as log:
  try:
   r=subprocess.run(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,timeout=180);result={'exit_code':r.returncode,'timeout':False}
  except subprocess.TimeoutExpired:result={'exit_code':None,'timeout':True}
 (out/'EXECUTION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
 if result['timeout'] or result['exit_code']:raise SystemExit(1)
