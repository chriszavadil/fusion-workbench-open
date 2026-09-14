"""Finite active-session continuation; no recurring service or agent."""
from pathlib import Path
import subprocess,sys,json,time
HERE=Path(__file__).resolve().parent
records=[]
def execute(name):
    log=HERE/(name+'.log');start=time.time()
    try:
        with log.open('w',encoding='utf-8') as out:
            p=subprocess.run([sys.executable,'-u',str(HERE/'run_case.py'),name],cwd=HERE,stdout=out,stderr=subprocess.STDOUT,timeout=600)
        status={'case':name,'returncode':p.returncode,'elapsed_s':time.time()-start}
    except subprocess.TimeoutExpired:
        status={'case':name,'timeout':True,'elapsed_s':time.time()-start}
    path=HERE/name/'RESULT.json'
    result=json.loads(path.read_text()) if path.exists() else {'classification':'execution_error','exception':'No completed result'}
    status.update({'classification':result['classification'],'values':result.get('values'),
                   'conditional_average_net_MW':result.get('conditional_average_net_MW'),'exception':result.get('exception')})
    records.append(status);(HERE/'EXECUTION_SUMMARY.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(status),flush=True);return result
first=execute('H1_direct')
if first['classification']=='solver_not_converged':
    bridge=execute('H11_bridge')
    if bridge['classification']=='numerically_converged':execute('H1_continued')
