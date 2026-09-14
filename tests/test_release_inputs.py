"""Release data consistency tests; no physics validation or network requests."""
from pathlib import Path
import hashlib,json,struct,sys,importlib.util
import pytest
ROOT=Path(__file__).resolve().parents[1]

def test_approved_solver_files_and_runtime_hashes():
 m=json.loads((ROOT/'research/SOLVER_MANIFEST.json').read_text())
 assert set(m['configurations'])=={'r838','r900'}
 for entry in list(m['configurations'].values())+list(m['runtime_modules'].values()):
  path=(ROOT/entry['path']).resolve();path.relative_to((ROOT/'research').resolve())
  assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256']

def test_catalog_is_identical_between_native_and_browser():
 assert (ROOT/'native/Content/WorkbenchData/catalog.json').read_bytes()==(ROOT/'app/data/catalog.json').read_bytes()

@pytest.mark.parametrize('name',['r838','r900'])
def test_native_mesh_header_and_provenance(name):
 path=ROOT/'native/Content/WorkbenchData'/f'{name}.fwm'
 data=path.read_bytes();magic,count=struct.unpack_from('<II',data)
 assert magic==0x31425746 and count==34
 assert 1000000<len(data)<16000000

def test_installer_needs_explicit_request(monkeypatch):
 spec=importlib.util.spec_from_file_location('setup_solver',ROOT/'tools/setup_solver.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 monkeypatch.setattr(sys,'argv',['setup_solver.py'])
 with pytest.raises(SystemExit,match='Explicit --install'):m.main()

def test_setup_emits_matching_relative_manifest_configuration(tmp_path,monkeypatch):
 import shutil
 from types import SimpleNamespace
 spec=importlib.util.spec_from_file_location('setup_solver_test',ROOT/'tools/setup_solver.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 shutil.copytree(ROOT/'research',tmp_path/'research')
 (tmp_path/'tools').mkdir();monkeypatch.setattr(m,'__file__',str(tmp_path/'tools/setup_solver.py'))
 monkeypatch.setattr(sys,'argv',['setup_solver.py','--install'])
 monkeypatch.setattr(m.venv,'EnvBuilder',lambda **k:SimpleNamespace(create=lambda p:Path(p).mkdir(parents=True)))
 commands=[]
 def fake_run(command,**kwargs):
  commands.append(command)
  if command[:2]==['git','clone']:Path(command[-1]).mkdir(parents=True)
  return SimpleNamespace(returncode=0)
 monkeypatch.setattr(m.subprocess,'run',fake_run)
 manifest=json.loads((tmp_path/'research/SOLVER_MANIFEST.json').read_text())
 monkeypatch.setattr(m.subprocess,'check_output',lambda *a,**k:manifest['upstream']+'\n')
 m.main();config=json.loads((tmp_path/'.local/execution.json').read_text())
 for key,row in manifest['configurations'].items():
  assert config['configurations'][key]['input']==str(tmp_path/row['path'])
  assert config['configurations'][key]['input_sha256']==row['sha256']
 assert any('-m' in cmd and 'pip' in cmd for cmd in commands)


def test_no_development_file_server_credentials():
 for folder in ('native','unreal'):
  text=(ROOT/folder/'Config/DefaultEngine.ini').read_text()
  assert not any(line.strip().lower().startswith('securitytoken=') for line in text.splitlines())
  project=json.loads((ROOT/folder/'FusionWorkbench.uproject').read_text())
  assert any(p['Name']=='AndroidFileServer' and p['Enabled'] is False for p in project['Plugins'])
