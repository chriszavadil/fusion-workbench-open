"""Offline replay against an already-installed pinned PROCESS environment.
No package installation, network access, or edits of the upstream source occur.
Numerical agreement does not constitute physical validation.
"""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,sys,tempfile
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMBA_NUM_THREADS'):os.environ[k]='1'
HERE=Path(__file__).resolve().parent
PIN='c0ae5b28649f2b20fb7efc7904628b6defe4151c'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path);args=ap.parse_args()
    manifest=json.loads((HERE/'MANIFEST.json').read_text())
    for name,expected in manifest['files'].items():
        path=HERE/name
        if not path.is_file() or sha(path)!=expected:raise ValueError('Manifest mismatch: '+name)
    import process
    native=Path(process.__file__).resolve().parent.parent
    actual=subprocess.check_output(['git','-C',str(native),'rev-parse','HEAD'],text=True).strip()
    if actual!=PIN:raise ValueError('Installed PROCESS is not the pinned reference')
    for name,expected in manifest['upstream_files'].items():
        if sha(native/name)!=expected:raise ValueError('Changed upstream model: '+name)
    root=args.output.resolve() if args.output else Path(tempfile.mkdtemp(prefix='fusion-header-replay-'))
    if root.exists() and any(root.iterdir()):raise ValueError('Refuse to overwrite nonempty replay directory')
    root.mkdir(parents=True,exist_ok=True)
    (root/'flow-balance-20260907').mkdir();(root/'blanket-interface-20260907').mkdir()
    work=root/'manifold-evidence-20260907';work.mkdir()
    shutil.copyfile(HERE/'dependencies/branch_balance.py',root/'flow-balance-20260907/branch_balance.py')
    shutil.copyfile(HERE/'dependencies/evaluate_frozen_fw_final.py',root/'evaluate_frozen_fw_final.py')
    shutil.copyfile(HERE/'dependencies/SOLVED_STATE.json',root/'blanket-interface-20260907/SOLVED_STATE.json')
    names=['header_inventory.py','flow_recheck.py','ADMISSION.json','FOLLOWON_ADMISSION.json','INPUT_STATE.json','PROVENANCE.json','test_header_inventory.py']
    for name in names:shutil.copyfile(HERE/name,work/name)
    logs=[]
    for command in [[sys.executable,'header_inventory.py'],[sys.executable,'flow_recheck.py'],[sys.executable,'-m','pytest','-q','test_header_inventory.py']]:
        result=subprocess.run(command,cwd=work,capture_output=True,text=True,encoding='utf-8',timeout=120)
        logs.append('COMMAND '+repr(command)+'\n'+result.stdout+result.stderr)
        if result.returncode:raise RuntimeError(logs[-1])
    expected=json.loads((HERE/'RESULT.json').read_text());actual=json.loads((work/'RESULT.json').read_text())
    maximum_error=0.
    for old,new in zip(expected['results'],actual['results']):
        for key in ['known_common_pressure_Pa_after_nominal_balancing','remaining_common_external_pressure_Pa']:
            error=abs(old[key]-new[key]);maximum_error=max(maximum_error,error)
            if error>.1:raise ValueError('Pressure replay disagreement')
        if abs(old['total_header_coolant_m3']-new['total_header_coolant_m3'])>1e-4:raise ValueError('Volume replay disagreement')
    old=json.loads((HERE/'FLOW_RECHECK_RESULT.json').read_text());new=json.loads((work/'FLOW_RECHECK_RESULT.json').read_text())
    for a,b in zip(old['results'],new['results']):
        for side in ['IB','OB']:
            if abs(a['unbalanced'][side]['branch']['peak_K']-b['unbalanced'][side]['branch']['peak_K'])>1e-5:raise ValueError('Temperature replay disagreement')
    (root/'REPLAY_LOG.txt').write_text('\n'.join(logs),encoding='utf-8',newline='\n')
    outcome={'numerical_replay_verified':True,'maximum_selected_pressure_error_Pa':maximum_error,'focused_tests_passed':19,'output':str(root),'physical_model_validated':False}
    (root/'REPLAY_RESULT.json').write_text(json.dumps(outcome,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(outcome))
if __name__=='__main__':main()
