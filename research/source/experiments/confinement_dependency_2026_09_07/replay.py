"""Read-only numerical replay in a fresh directory; does not run optimizations."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,sys,tempfile
HERE=Path(__file__).resolve().parent
PIN='c0ae5b28649f2b20fb7efc7904628b6defe4151c'
def main(source:Path):
    actual=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()
    if actual!=PIN:raise ValueError('Wrong reference revision')
    manifest=json.loads((HERE/'MANIFEST.json').read_text())
    for name,expected in manifest['sha256'].items():
        if hashlib.sha256((HERE/name).read_bytes()).hexdigest()!=expected:raise ValueError('Evidence mismatch: '+name)
    root=Path(tempfile.mkdtemp(prefix='fusion-confinement-replay-'));work=root/HERE.name;work.mkdir()
    for p in (HERE/'support').iterdir():shutil.copyfile(p,root/p.name)
    for name in ['audit_results.py','run_case.py','min_h_objective.py','test_confinement.py']:shutil.copyfile(HERE/name,work/name)
    for name in ['H1_direct','H11_bridge','H1_continued','H_min_inverse','H103_native_validation']:shutil.copytree(HERE/name,work/name)
    base=root/'runs-20260907/adaptive30y_warm_fixed';base.mkdir(parents=True)
    shutil.copyfile(HERE/'BASELINE_INPUT.DAT',base/'case_IN.DAT')
    env=os.environ.copy();env['FUSION_PROCESS_SOURCE']=str(source);env['PYTHONUTF8']='1';env['PYTHONIOENCODING']='utf-8'
    env['OPENBLAS_NUM_THREADS']='1';env['OMP_NUM_THREADS']='1'
    p=subprocess.run([sys.executable,'audit_results.py'],cwd=work,env=env,capture_output=True,text=True,timeout=90)
    (work/'audit-replay.log').write_text(p.stdout+p.stderr,encoding='utf-8')
    if p.returncode:raise RuntimeError(p.stderr)
    expected=json.loads((HERE/'VALIDATION.json').read_text());actual=json.loads((work/'VALIDATION.json').read_text())
    if expected['results']!=actual['results']:raise ValueError('Numerical audit differs')
    q=subprocess.run([sys.executable,'-m','pytest','-q','test_confinement.py'],cwd=work,env=env,capture_output=True,text=True,timeout=90)
    print(q.stdout+q.stderr);q.check_returncode()
    print(json.dumps({'read_only_replay_verified':True,'source_hashes_verified':True,'workdir':str(work),'optimizer_rerun':False,'physical_validation':False}))
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--process-source',type=Path,required=True);a=ap.parse_args();main(a.process_source)
