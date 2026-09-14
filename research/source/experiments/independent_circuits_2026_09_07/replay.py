"""Verify saved source/inputs, replay thermodynamic states, then run focused tests.
Does not need the original desktop state, PROCESS, Modelica or internet access.
"""
import hashlib, json, subprocess, sys, shutil, tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent

def main():
    manifest=json.loads((HERE/'MANIFEST.json').read_text(encoding='utf-8'))
    for name,digest in manifest['files'].items():
        path=HERE/name
        if hashlib.sha256(path.read_bytes()).hexdigest()!=digest: raise ValueError('Hash mismatch: '+name)
    # Running in a copy preserves the archived result and follow-on evidence.
    work=Path(tempfile.mkdtemp(prefix='fusion-independent-replay-'))
    for name in manifest['files']: shutil.copyfile(HERE/name,work/name)
    sys.path.insert(0,str(work))
    import compare_circuits as c
    stored=json.loads((work/'RESULT.json').read_text());cfg=stored['inputs']['config']
    max_error=0.;max_ledger=0.
    for case in stored['cases']:
        systems={}
        for key in ('shared_balanced','independent_regional_circuits'):
            rows=[c.loop(x['flow_kg_s'],x['external_heat_MW'],x['pressure_drop_Pa'],cfg) for x in case[key]['loops']]
            systems[key]=c.installation(rows,cfg)
            max_error=max(max_error,abs(systems[key]['drive_electric_MW']-case[key]['drive_electric_MW']))
            max_ledger=max(max_ledger,max(abs(x['cycle_energy_residual_MW']) for x in rows))
        delta=c.benefit(systems['shared_balanced'],systems['independent_regional_circuits'],cfg['heat_eff'])
        max_error=max(max_error,abs(delta['fixed_conversion_net_budget_MW']-case['difference']['fixed_conversion_net_budget_MW']))
    if max_error>1e-7 or max_ledger>1e-7:raise ValueError('Numerical replay failed')
    test=subprocess.run([sys.executable,'-m','pytest','-q','test_circuits.py'],cwd=work,capture_output=True,text=True,timeout=90)
    print(test.stdout);print(test.stderr)
    result={'source_and_input_hashes_verified':True,'maximum_power_replay_error_MW':max_error,'maximum_ledger_residual_MW':max_ledger,'test_exit':test.returncode,'replay_directory':str(work),'physical_validation':False}
    print(json.dumps(result));(HERE/'REPLAY_RESULT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    return test.returncode
if __name__=='__main__':raise SystemExit(main())
