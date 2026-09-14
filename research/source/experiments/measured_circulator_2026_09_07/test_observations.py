from pathlib import Path
import json, copy, math
import pytest
from CoolProp.CoolProp import PropsSI
import assess_observations as a
ROOT=Path(__file__).resolve().parent
@pytest.fixture(scope='module')
def rows(): return json.loads((ROOT/'SOURCE_ROWS.json').read_text())['rows']
@pytest.fixture(scope='module')
def saved(): return json.loads((ROOT/'RESULT.json').read_text())
def test_source_roles(rows):
    assert len([r for r in rows if a.eligible(r)])==2
    assert not a.eligible(rows[2])
def test_rated_row_cannot_become_measured_efficiency(rows):
    with pytest.raises(ValueError,match='Rated'): a.pressure_work_proxy(rows[2],'absolute_inlet')
@pytest.mark.parametrize('mode',['absolute_inlet','absolute_outlet'])
def test_pressure_reference_pair(mode):
    p,q=a.pressure_pair(6.9e6,122200.,mode)
    assert q-p==122200.
    assert (p if mode=='absolute_inlet' else q)==6.9e6
@pytest.mark.parametrize('p,dp,mode',[(0,1,'absolute_inlet'),(1,-1,'absolute_inlet'),(1,2,'absolute_outlet'),(1,1,'unknown'),(math.nan,1,'absolute_inlet')])
def test_bad_pressure_rejected(p,dp,mode):
    with pytest.raises(ValueError):a.pressure_pair(p,dp,mode)
@pytest.mark.parametrize('idx,expected',[(0,.5766746821466827),(1,.7256824420808835)])
def test_published_point_diagnostic_replayed(rows,idx,expected):
    r=a.pressure_work_proxy(rows[idx],'absolute_inlet')
    assert r['conditional_pressure_work_electrical_ratio']==pytest.approx(expected,abs=1e-10)
    assert abs(r['reconstructed_entropy_error_J_kgK'])<1e-7
def test_mass_and_power_scaling(rows):
    x=a.pressure_work_proxy(rows[0],'absolute_inlet'); y=copy.deepcopy(rows[0]);y['massflow_kg_s']*=2;y['power_kW']*=2
    z=a.pressure_work_proxy(y,'absolute_inlet')
    assert z['conditional_pressure_work_electrical_ratio']==pytest.approx(x['conditional_pressure_work_electrical_ratio'])
    assert z['isentropic_pressure_work_MW']==pytest.approx(2*x['isentropic_pressure_work_MW'])
def test_independent_ideal_gas_low_density_limit(rows):
    r=copy.deepcopy(rows[0]);r.update(pressure_MPa=.001,pressure_rise_kPa=.02)
    x=a.pressure_work_proxy(r,'absolute_inlet')
    assert x['real_He_pressure_work_J_kg']==pytest.approx(x['ideal_gas_pressure_work_J_kg'],rel=1e-4)
def test_outlet_vs_inlet_not_uncertainty_bound(saved):
    assert len(saved['diagnostics'])==4
    assert all(not x['usable_as_candidate_efficiency'] for x in saved['diagnostics'])
    assert all(not x['is_reported_efficiency'] for x in saved['diagnostics'])
def test_definition_gate_rejects_unknown():
    x=a.assess_gate({}); assert len(x['missing_evidence'])==7
    assert not x['complete_interface_evidence'] and not x['candidate_efficiency_update_authorized']
def test_truthy_text_not_verified_definition():
    assert not a.assess_gate({k:'yes' for k in a.DEFINITIONS})['complete_interface_evidence']
def test_even_complete_metadata_not_automatic_plant_acceptance():
    x=a.assess_gate({k:True for k in a.DEFINITIONS})
    assert x['complete_interface_evidence'] and not x['candidate_efficiency_update_authorized']
def test_latest_header_case_used(saved):
    x=saved['current_header_envelope']; assert x['known_candidate_ratios']['inboard']==pytest.approx(1.0489402859139816)
    assert x['known_candidate_ratios']['outboard']==pytest.approx(1.0287638872890745)
    assert all(x['candidate_known_ratios_above_observed_points'].values())
def test_source_inconsistency_preserved(saved):
    assert any('4648' in text and '4735.5' in text for text in saved['source_internal_discrepancies'])
    assert saved['excluded_rows']==[{'id':'rated_reference','reason':'rated_design_not_measurement'}]
