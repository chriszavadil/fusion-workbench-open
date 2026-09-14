"""Replay the exact numerical study from its checked minimal state subset.
Requires an editable installation of official PROCESS at the recorded commit.
"""
import json,hashlib,sys,tempfile,shutil,subprocess
from pathlib import Path
import process
import pytest
HOME=Path(__file__).resolve().parent
sys.path.insert(0,str(HOME))
import branch_balance as b

def main():
    manifest=json.loads((HOME/'PORTABLE_MANIFEST.json').read_text())
    for name,expected in manifest['files'].items():
        if hashlib.sha256((HOME/name).read_bytes()).hexdigest()!=expected:raise ValueError('Changed input/source: '+name)
    source=Path(process.__file__).resolve().parents[1]
    pin=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()
    if pin!='c0ae5b28649f2b20fb7efc7904628b6defe4151c':raise ValueError('Wrong PROCESS revision')
    data=json.loads((HOME/'INPUT_STATE.json').read_text())
    output=Path(tempfile.mkdtemp(prefix='fusion-flow-replay-',dir=HOME))
    admission=json.loads((HOME/'ADMISSION.json').read_text())
    admission['replay_data_source']='Checked minimal subset; original full-state reference retained for provenance, not fetched by this replay.'
    admission['subset_sha256']=manifest['files']['INPUT_STATE.json']
    b.save(output/'ADMISSION.json',admission)
    b.load=lambda:json.loads((HOME/'INPUT_STATE.json').read_text())
    b.HERE=output
    actual=b.run();reference=json.loads((HOME/'RESULT.json').read_text())
    def same(a,c):
        if isinstance(a,dict):
            assert a.keys()==c.keys()
            for k in a:same(a[k],c[k])
        elif isinstance(a,list):
            assert len(a)==len(c)
            for x,y in zip(a,c):same(x,y)
        elif isinstance(a,(float,int)) and not isinstance(a,bool):
            assert abs(a-c)<=1e-7+1e-9*abs(c),(a,c)
        else:assert a==c,(a,c)
    for key in ('results','nominal_flows_kg_s','minimum_thermal_flows_kg_s'):same(actual[key],reference[key])
    status=pytest.main(['-q',str(HOME/'test_branch_balance.py')])
    if status!=0:raise RuntimeError('Replay tests failed')
    print(json.dumps({'numerical_replay_verified':True,'test_exit':status,'output':str(output),'physical_validation':False}))
if __name__=='__main__':main()
