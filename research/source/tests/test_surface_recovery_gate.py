from dataclasses import replace
from pathlib import Path
import sys
import math
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import surface_recovery_gate as s

@pytest.fixture(scope='module')
def result(tmp_path_factory):return s.run(tmp_path_factory.mktemp('surface'))

@pytest.mark.parametrize('kw',[{'diameter_m':0},{'hot_K':math.inf},{'cold_K':-1},{'biot_hot':0},{'bulk_multiplier':float('nan')},{'cold_K':1000}])
def test_invalid_model(kw):
    with pytest.raises(ValueError):replace(s.Model(),**kw).validate()

@pytest.mark.parametrize('n',[True,3,10.5])
def test_bad_mesh(n):
    with pytest.raises(ValueError):s.mesh(n)

@pytest.mark.parametrize('tau',[-1,float('nan')])
def test_bad_downstream(tau):
    with pytest.raises(ValueError):s.run_protocol(s.Model(),[(1,938.15)],downstream_s=tau)


def test_dimensional_biot_and_surface_fixed_when_bulk_improves():
    a=s.Model();b=replace(a,bulk_multiplier=10)
    assert a.surface(a.hot_K)*a.radius/a.diffusion(a.hot_K)==pytest.approx(10)
    assert a.surface(a.hot_K)==b.surface(a.hot_K)
    assert b.diffusion(a.hot_K)==10*a.diffusion(a.hot_K)


def test_generator_conservative_and_positive():
    G=s.full_generator(s.Model(),938.15,48,360.)
    # cumulative-release accounting register is not a separate physical inventory.
    assert np.max(abs(G[:-1,:].sum(axis=0)))<1e-12
    off=G.copy();np.fill_diagonal(off,0)
    assert off.min()>=0


def test_unit_inventory_cannot_be_created(result):
    for row in result['cases']:
        e=row['end']
        assert e['material_remaining_fraction']+e['processing_fraction']+e['available_fraction']==pytest.approx(1,abs=1e-10)
        assert e['released_fraction']==pytest.approx(e['processing_fraction']+e['available_fraction'],abs=1e-10)
        assert e['available_fraction']<=e['released_fraction']+1e-12


def test_empty_source_zero_duration():
    e=s.run_protocol(s.Model(),[(0,938.15)])['end']
    assert e['material_remaining_fraction']==pytest.approx(1)
    assert e['released_fraction']==0
    assert e['available_fraction']==0


def test_instant_downstream_delivers_everything_released(result):
    for r in result['cases']:
        if r['downstream_s_assumed']==0:
            assert r['end']['available_fraction']==pytest.approx(r['end']['released_fraction'],abs=1e-11)


def test_downstream_does_not_change_material_release(result):
    for bi in [.1,1,10,100]:
        for proto in ['held_hot','held_cold','hot_then_cold','cold_then_hot']:
            rows=[r for r in result['cases'] if r['model']['biot_hot']==bi and r['protocol_label']==proto]
            vals=[r['end']['released_fraction'] for r in rows]
            assert max(vals)-min(vals)<1e-10
            delivery=[r['end']['available_fraction'] for r in rows]
            assert delivery[0]>=delivery[1]>=delivery[2]


def test_flux_is_not_recovered_fuel_decision(result):
    row=next(r for r in result['cases'] if r['model']['biot_hot']==10 and r['protocol_label']=='held_hot' and r['downstream_s_assumed']==14400)
    assert row['end']['released_fraction']>.5>row['end']['available_fraction']


def test_mean_matches_closed_form_and_refines(result):
    for bi in [.1,1,10,100]:
        rows=[x for x in result['spectral_checks'] if x['biot_hot']==bi]
        assert rows[0]['relative_mean_error']>rows[1]['relative_mean_error']>rows[2]['relative_mean_error']
        assert rows[2]['relative_mean_error']<1e-4


def test_spectral_remaining_agrees_and_refines(result):
    for bi in [.1,1,10,100]:
        rows=[x for x in result['spectral_checks'] if x['biot_hot']==bi]
        assert rows[0]['max_spectral_error']>rows[1]['max_spectral_error']>rows[2]['max_spectral_error']
        assert rows[-1]['max_spectral_error']<1.7e-5
        assert abs(rows[-1]['spectral_initial_tail'])<1e-10


def test_temporal_algorithms_agree(result):
    assert max(x['maximum_expm_vs_Radau_fraction_error'] for x in result['temporal_solver_checks'])<1e-10


def test_full_step_half_steps_semigroup():
    m=s.Model();x=s.run_protocol(m,[(5400,m.hot_K)])
    y=s.run_protocol(m,[(2700,m.hot_K),(2700,m.hot_K)])
    assert np.max(abs(np.array(x['material_profile'])-y['material_profile']))<1e-12
    assert x['end']['available_fraction']==pytest.approx(y['end']['available_fraction'],abs=1e-12)


def test_equal_diffusion_clock_not_equal_output(result):
    a=next(x for x in result['refinement'] if x['cells']==256 and x['protocol_label']=='hot_then_cold')
    b=next(x for x in result['refinement'] if x['cells']==256 and x['protocol_label']=='cold_then_hot')
    assert a['diffusion_clock_m2']==b['diffusion_clock_m2']
    assert abs(a['end']['released_fraction']-b['end']['released_fraction'])>.004
    assert a['end']['available_fraction']-b['end']['available_fraction']>.04


def test_order_difference_not_discretization(result):
    differences=[]
    for n in [32,64,128,256]:
        a=next(x for x in result['refinement'] if x['cells']==n and x['protocol_label']=='hot_then_cold')
        b=next(x for x in result['refinement'] if x['cells']==n and x['protocol_label']=='cold_then_hot')
        differences.append(b['end']['released_fraction']-a['end']['released_fraction'])
    assert abs(differences[-1]-differences[-2])<4e-6
    assert all(d>.004 for d in differences)


def test_commuting_control_removes_material_but_not_delivery_order_effect(result):
    c=result['commuting_material_control']
    assert c['material_profile_max_difference']<1e-12
    assert c['released_difference']<1e-12
    assert c['available_difference_from_downstream_timing']>.04


def test_bulk_improvement_cannot_remove_surface_time(result):
    for x in result['bulk_acceleration']:
        fraction=x['initial_bulk_fraction_of_mean']
        expected=1/(1-.9*fraction)
        assert x['release_mean_speedup']==pytest.approx(expected,rel=1e-12)
        assert 1<=x['release_mean_speedup']<=10


def test_surface_limited_hot_case_bulk_gain_small(result):
    x=next(x for x in result['bulk_acceleration'] if x['biot_hot']==1 and x['T_K']==938.15)
    assert x['release_mean_speedup']==pytest.approx(1.1764705882352942)


def test_hardware_acceleration_not_material_diffusion_coefficient():
    # The study explicitly describes bulk_multiplier as a physical parameter,
    # never as the runtime speedup of cuEquivariance or other GPU software.
    assert 'surface' in s.__doc__.lower()
    assert 'NOT the published nonlinear K' in s.__doc__


def test_all_study_inputs_saved_before_output(result):
    assert result['frozen_input']['provenance']['linear_h_hot'].startswith('Uncalibrated')
    assert len(result['cases'])==48
    assert len(result['refinement'])==8
    assert result['scope'][0].startswith('A linear Robin')
