"""Evidence, model-isolation and local-control tests; not reactor validation."""
import copy, importlib.util, json, math, sys, threading, time, http.client
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'));sys.path.insert(0,str(ROOT/'app'))
import evidence as e
import export_release as release
import server as s
CAT=json.loads((ROOT/'app/data/catalog.json').read_text(encoding='utf-8'))
@pytest.mark.parametrize('cfg',CAT['configurations'],ids=lambda c:c['id'])
def test_recorded_energy(cfg):
    r=e.verify_configuration(cfg)
    assert r['passed'] and r['physical_validation'] is False
    assert r['conditional_average_net_MW']==pytest.approx(cfg['metrics']['conditional_average_net_MW'],abs=1e-7)
@pytest.mark.parametrize('cfg',CAT['configurations'],ids=lambda c:c['id'])
def test_edited_result_does_not_pass(cfg):
    c=copy.deepcopy(cfg);c['pulse']['series']['net_MW'][3]+=1
    assert not e.verify_configuration(c)['passed']
@pytest.mark.parametrize('value',[None,True,float('nan'),float('inf'),'0'])
def test_missing_is_not_zero(value):
    with pytest.raises(ValueError):e.required({'x':value},'x')
def test_real_zero():assert e.required({'x':0},'x')==0
def test_known_integral():assert e.integrate_profile([0,2,4],[0,10,0])==pytest.approx(20/3.6)
def test_conflicting_source(tmp_path):
    p=tmp_path/'x.dat';p.write_text('x (a)___ 1\ny (a)___ 2\n')
    with pytest.raises(ValueError):e.read_mfile(p)
@pytest.mark.parametrize('cfg',CAT['configurations'],ids=lambda c:c['id'])
def test_mesh_isolation(cfg):
    raw=(ROOT/'app/web/assets'/f"{cfg['id']}.glb").read_bytes()
    doc=json.loads(release.glb_metadata(raw));nodes=[n for n in doc['nodes'] if 'mesh' in n]
    assert len(nodes)==34
    assert all(n['extras']['configuration_id']==cfg['id'] for n in nodes)
    assert all(n['extras']['source_artifact_sha256']==cfg['provenance']['artifact_sha256'] for n in nodes)
    assert {n['extras']['component_id'] for n in nodes}=={c['id'] for c in cfg['components']}
    assert sum(n['extras']['cutaway_segment'] for n in nodes)==8
def test_no_percent_solved_or_validation_claim():
    assert all(c['status']=='numerically_converged_concept' for c in CAT['configurations'])
    assert not CAT['inventory']['historical_raw_runs_fully_integrated']
    assert len(CAT['tracks'])==8
def test_private_projection_scan():
    deny_path=ROOT/'.local/private-deny.json'
    deny=json.loads(deny_path.read_text())['terms'] if deny_path.exists() else []
    assert release.inspect_file(ROOT/'app/data/catalog.json',deny)==[]
@pytest.mark.parametrize('rel',['.local/execution.json','.git/config','output/test.blend','unreal/Saved/log.txt','docs/.hidden.json'])
def test_private_paths_not_exported(rel):assert not release.allowed(ROOT/rel,ROOT)
def test_secret_rejected(tmp_path):
    p=tmp_path/'data.json';p.write_text('ghp_'+'A'*35)
    assert release.inspect_file(p,[])
def test_private_identifier_rejected(tmp_path):
    p=tmp_path/'README.md';p.write_text('unpublished-owner')
    assert release.inspect_file(p,['unpublished-owner'])
@pytest.fixture(scope='module')
def http_server():
    svc=s.WorkbenchServer(('127.0.0.1',0),ROOT);t=threading.Thread(target=svc.serve_forever,daemon=True);t.start()
    yield svc
    svc.shutdown();svc.manager.close();svc.server_close();t.join()
def request(svc,path,method='GET',payload=None,headers=None):
    port=svc.server_address[1];h={'Host':f'127.0.0.1:{port}'}
    if method=='POST':h.update({'Origin':f'http://127.0.0.1:{port}','X-Workbench-Request':'local-ui-v1','Content-Type':'application/json'})
    h.update(headers or {});c=http.client.HTTPConnection('127.0.0.1',port,timeout=5)
    c.request(method,path,body=None if payload is None else json.dumps(payload),headers=h)
    r=c.getresponse();status=r.status;raw=r.read();c.close();return status,raw
@pytest.mark.parametrize('path',['/.local/execution.json','/vendor/../../.local/execution.json','/assets/../../tools/evidence.py','/api/unknown','/.git/config'])
def test_private_http_denied(http_server,path):assert request(http_server,path)[0]==404
@pytest.mark.parametrize('headers',[{'Host':'other.invalid'},{'Origin':'https://other.invalid'},{'X-Workbench-Request':''}])
def test_cross_origin_write_rejected(http_server,headers):
    assert request(http_server,'/api/jobs','POST',{'kind':'verify_recorded_energy','configuration_id':'r838'},headers)[0]==403
@pytest.mark.parametrize('payload',[{'command':'anything'},{'kind':'arbitrary','configuration_id':'r838'},{'kind':'rerun_process','configuration_id':'unknown'},{'kind':'verify_recorded_energy','configuration_id':'r838','path':'anything'}])
def test_arbitrary_commands_rejected(http_server,payload):assert request(http_server,'/api/jobs','POST',payload)[0]==400
def test_live_verification_job(http_server):
    status,raw=request(http_server,'/api/jobs','POST',{'kind':'verify_recorded_energy','configuration_id':'r838'})
    assert status==202;ident=json.loads(raw)['id']
    for _ in range(100):
        _,raw=request(http_server,'/api/jobs/'+ident);job=json.loads(raw)
        if job['state'] not in ('queued','running'):break
        time.sleep(.01)
    assert job['state']=='completed' and job['result']['passed']
    assert job['result']['physical_validation'] is False
    assert 'private-worker' not in raw.decode()
def test_queue_cancellation_without_execution(tmp_path):
    manager=s.JobManager(tmp_path)
    manager.jobs['sample']={'id':'sample','state':'queued','kind':'verify_recorded_energy','configuration_id':'r838'}
    assert manager.cancel('sample')['state']=='cancelled'
    manager.close()
