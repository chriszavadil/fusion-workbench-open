from pathlib import Path
import json, os, sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import reproduce_upstream_fatigue as r

@pytest.fixture(scope='module')
def result(tmp_path_factory):
    path=os.environ.get('FUSION_POWER_ARCHIVE')
    if not path: pytest.skip('Set FUSION_POWER_ARCHIVE to the original verified power ZIP')
    return r.run(Path(path),tmp_path_factory.mktemp('evidence'))


def test_native_cycle_method_body_identical_between_releases():
    a=r.methods('v3.4.2')[3];b=r.methods('main_at_audit')[3]
    assert a['body_hashes']['ncycle']==b['body_hashes']['ncycle']


def test_public_upstream_fixture_is_reproduced(result):
    x=result['results'][0]
    assert x['current_native_cycles']==pytest.approx(x['case']['upstream_expected_native'],abs=1e-9,rel=0)


def test_archived_baseline_is_reproduced(result):
    x=result['results'][1]
    assert x['current_native_cycles']==pytest.approx(x['case']['upstream_expected_native'],abs=1e-9,rel=0)

@pytest.mark.parametrize('index',range(4))
def test_pinned_current_and_adaptive_cross_checks(result,index):
    x=result['results'][index]
    assert x['current_native_cycles']==pytest.approx(x['pinned_native_cycles'],abs=1e-9,rel=0)
    assert x['adaptive_native_SIF_DOP853']['cycles']==pytest.approx(x['adaptive_native_SIF_RK45']['cycles'],abs=1e-5,rel=0)
    assert x['adaptive_native_SIF_DOP853']['cycles']==pytest.approx(x['prior_independent_algebra_cycles'],abs=1e-5,rel=0)
    assert x['adaptive_native_SIF_DOP853']['termination']=='radial_crack'
    assert x['adaptive_native_SIF_DOP853']['final_c_m']==pytest.approx(x['case']['conduit_w_m']/2,abs=1e-12,rel=0)

@pytest.mark.parametrize('index',range(4))
def test_refinement_of_native_method_approaches_adaptive(result,index):
    x=result['results'][index];target=x['adaptive_native_SIF_DOP853']['cycles']
    err=[abs(y['cycles']-target) for y in x['native_step_refinement']]
    assert all(a>b for a,b in zip(err,err[1:]))
    assert err[-1]<.03*err[0]


def test_adversarial_model_constraint_decision_changes(result):
    x=result['results'][3]
    assert x['native_pass_20000'] is True
    assert x['adaptive_pass_20000'] is False
    assert 'not held-out' in x['case']['selection']


def test_source_corruption_is_rejected(tmp_path,monkeypatch):
    root=tmp_path/'external/process';root.mkdir(parents=True)
    (root/'cs_fatigue_current.py').write_text('print("corrupt")')
    monkeypatch.setattr(r,'ROOT',tmp_path)
    with pytest.raises(ValueError,match='hash mismatch'):r.methods('main_at_audit')
