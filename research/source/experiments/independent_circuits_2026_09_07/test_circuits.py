"""Implementation checks only; not validation of circulators or a power plant."""
import json, math
from pathlib import Path
import pytest
from scipy.optimize import brentq
from CoolProp.CoolProp import PropsSI
import compare_circuits as c
ROOT=Path(__file__).resolve().parent
@pytest.fixture(scope='module')
def results(): return json.loads((ROOT/'RESULT.json').read_text())

@pytest.mark.parametrize('dp',[0.,1e4,3e5,5.5e5])
def test_compression_forward_entropy_and_efficiency(dp):
    x=c.specific_compression(dp,8e6,573.13,.9)
    assert abs(x['compression_residual_J_kg'])<1e-5
    assert abs(x['entropy_error_J_kgK'])<1e-7
    assert x['fluid_work_J_kg']>=0
    assert x['suction_T_K']<=573.13
    if dp:
        ps=8e6-dp; ss=PropsSI('Smass','P',ps,'T',x['suction_T_K'],'Helium')
        his=PropsSI('Hmass','P',8e6,'Smass',ss,'Helium')
        assert (his-x['suction_h_J_kg'])/x['fluid_work_J_kg']==pytest.approx(.9,abs=1e-10)

@pytest.mark.parametrize('eta,drive,dp',[(0.,.87,100.),(1.1,.87,100.),(.9,0.,100.),(.9,.87,-1.),(.9,.87,8e6),(.9,.87,float('nan'))])
def test_bad_inputs_fail(eta,drive,dp):
    with pytest.raises(ValueError):c.check_params(1.,dp,8e6,573.13,eta,drive)
@pytest.mark.parametrize('i',range(4))
def test_saved_comparison_ledger_and_feedback(results,i):
    case=results['cases'][i];cfg=results['inputs']['config']
    for key in ('shared_balanced','independent_regional_circuits'):
        for x in case[key]['loops']:
            replay=c.loop(x['flow_kg_s'],x['external_heat_MW'],x['pressure_drop_Pa'],cfg)
            assert replay['drive_electric_MW']==pytest.approx(x['drive_electric_MW'],abs=1e-9)
            assert abs(replay['cycle_energy_residual_MW'])<1e-9
    diff=case['difference'];shaft=case['shared_balanced']['fluid_shaft_work_MW']-case['independent_regional_circuits']['fluid_shaft_work_MW']
    assert diff['lost_recoverable_heat_MW']==pytest.approx(shaft,abs=1e-9)
    assert diff['fixed_conversion_net_budget_MW']==pytest.approx(shaft*(1/cfg['drive']-cfg['heat_eff']),abs=1e-9)
    assert 0<diff['fixed_conversion_net_budget_MW']<diff['electric_saving_MW']

@pytest.mark.parametrize('i',range(4))
def test_head_crossover_changes_sign_and_joint_limit(results,i):
    case=results['cases'][i];cfg=results['inputs']['config'];common=case['shared_balanced'];ind=case['independent_regional_circuits'];root=case['energy_only_equal_added_head_crossover_Pa']
    def score(extra):
        trial=c.installation([c.loop(x['flow_kg_s'],x['external_heat_MW'],x['pressure_drop_Pa']+extra,cfg) for x in ind['loops']],cfg)
        return c.benefit(common,trial,cfg['heat_eff'])['fixed_conversion_net_budget_MW']
    assert abs(score(root))<1e-7
    assert score(root-1)>0>score(root+1)
    assert case['joint_equal_added_head_limit_Pa']<=case['pressure_budget_equal_added_head_limit_Pa']
    if case['external_loss_case']=='equal_external_loss_at_shared_budget':assert case['joint_equal_added_head_limit_Pa']==0


def test_twin_half_circuits_preserve_frozen_aggregate(results):
    cfg=results['inputs']['config'];x=results['cases'][0]['independent_regional_circuits']['loops'][0]
    half=c.loop(x['flow_kg_s']/2,x['external_heat_MW']/2,x['pressure_drop_Pa'],cfg)
    assert 2*half['drive_electric_MW']==pytest.approx(x['drive_electric_MW'],abs=1e-10)
    assert half['hot_return_T_K']==pytest.approx(x['hot_return_T_K'],abs=1e-10)
def test_ideal_gas_limit_has_independent_closed_form():
    pd=8e4;dp=5500.;td=573.13;eta=.9;ratio=(pd/(pd-dp))**.4
    cp=2.5*PropsSI('gas_constant','Helium')/PropsSI('molar_mass','Helium')
    ts_ideal=td/(1+(ratio-1)/eta);work_ideal=cp*(td-ts_ideal)
    real=c.specific_compression(dp,pd,td,eta)
    assert real['fluid_work_J_kg']==pytest.approx(work_ideal,rel=.002)

def test_efficiency_followon_roots_are_verified():
    import efficiency_requirement as e
    r=e.run()
    assert len(r['results'])==4
    assert all(x['pass_just_above'] and x['fail_just_below'] for x in r['results'])
    assert max(abs(x['root_residual_MW']) for x in r['results'])<1e-7

def test_equal_heads_cannot_create_topology_savings(results):
    cfg=results['inputs']['config'];x=c.installation([c.loop(100.,50.,2e5,cfg),c.loop(200.,100.,2e5,cfg)],cfg)
    assert c.benefit(x,x,cfg['heat_eff'])['fixed_conversion_net_budget_MW']==0.

def test_scope_and_exact_frozen_input(results):
    assert results['frozen_input_sha256']==c.sha(ROOT/'FROZEN_INPUT.json')
    assert results['no_updated_plant_output'] and not results['physical_validation']
    assert not results['Modelica_or_GETTHEM_executed']
