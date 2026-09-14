"""Reporting metadata lookup must not hang or change scientific equations."""
import importlib.util, subprocess, sys, types
from pathlib import Path
import pytest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
spec = importlib.util.spec_from_file_location('worker_reporting_test', ROOT / 'tools/process_worker.py')
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)

def test_git_lookup_is_bounded_and_shell_free(monkeypatch, tmp_path):
    seen = []
    def run(args, **kwargs):
        seen.append((args, kwargs))
        return types.SimpleNamespace(stdout='v3.4.2\n')
    monkeypatch.setattr(w.subprocess, 'run', run)
    assert w.git_output(tmp_path, 'describe', '--tags') == 'v3.4.2'
    args, kwargs = seen[0]
    assert args == ['git', '-C', str(tmp_path), 'describe', '--tags']
    assert kwargs['shell'] is False and kwargs['timeout'] == 15
    assert kwargs['check'] is True

def test_lookup_timeout_is_not_fabricated_success(monkeypatch, tmp_path):
    def fail(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], 15)
    monkeypatch.setattr(w.subprocess, 'run', fail)
    with pytest.raises(subprocess.TimeoutExpired):
        w.git_output(tmp_path, 'describe', '--tags')

def test_adapter_replaces_only_banner_metadata(monkeypatch, tmp_path):
    p = types.ModuleType('process')
    c = types.ModuleType('process.core')
    i = types.ModuleType('process.core.init')
    p.core = c; c.init = i
    untouched = object(); i.scientific_model = untouched
    for name, module in [('process', p), ('process.core', c), ('process.core.init', i)]:
        monkeypatch.setitem(sys.modules, name, module)
    monkeypatch.setattr(w, 'git_output', lambda source, *args: 'HEAD' if args[0] == 'rev-parse' else 'v3.4.2')
    result = w.install_reporting_metadata(tmp_path)
    assert i.get_git_summary() == ('HEAD', 'v3.4.2')
    assert i.scientific_model is untouched
    assert result['adapter_scope'].startswith('reporting-only')

def test_nonzero_git_result_propagates(monkeypatch, tmp_path):
    def fail(*args, **kwargs):
        raise subprocess.CalledProcessError(128, args[0])
    monkeypatch.setattr(w.subprocess, 'run', fail)
    with pytest.raises(subprocess.CalledProcessError):
        w.git_output(tmp_path, 'describe', '--tags')

def test_service_worker_does_not_inherit_terminal(monkeypatch, tmp_path):
    import json, time
    sys.path.insert(0, str(ROOT / 'app'))
    import server
    (tmp_path / '.local').mkdir()
    (tmp_path / '.local/execution.json').write_text(json.dumps({'python': 'test-only'}))
    observed = []
    class FakeChild:
        def __init__(self, command, **kwargs):
            observed.append(kwargs)
            folder = Path(command[command.index('--job-dir') + 1])
            (folder / 'safe-result.json').write_text(json.dumps({'passed': True}))
        def wait(self, **kwargs): return 0
        def poll(self): return 0
        def terminate(self): pass
    monkeypatch.setattr(server.subprocess, 'Popen', FakeChild)
    manager = server.JobManager(tmp_path)
    try:
        job = manager.create('rerun_process', 'r838')
        deadline = time.monotonic() + 5
        while manager.jobs[job['id']]['state'] in ('queued', 'running') and time.monotonic() < deadline:
            time.sleep(0.01)
        assert manager.jobs[job['id']]['state'] == 'completed'
        assert observed[0]['stdin'] == subprocess.DEVNULL
        assert observed[0]['shell'] is False and observed[0]['close_fds'] is True
    finally:
        manager.close()
