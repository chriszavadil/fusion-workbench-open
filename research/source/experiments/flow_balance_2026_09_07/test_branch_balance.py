"""Checks the candidate-specific network, not the accuracy of physical inputs."""
import json,math,copy
from pathlib import Path
import numpy as np
import pytest
from scipy.optimize import root, brentq
import branch_balance as b
@pytest.fixture(scope='module')
def net():return b.Network(b.load())
@pytest.fixture(scope='module')
def result():return json.loads((Path(__file__).parent/'RESULT.json').read_text())
@pytest.mark.parametrize('choice',['mean','outlet'])
def test_equal_pressure_and_mass_balance(net,choice):
    r=net.balance(choice)
    assert abs(r['pressure_mismatch_Pa'])<.01
    assert r['IB']['flow_kg_s']+r['OB']['flow_kg_s']==pytest.approx(net.total,abs=1e-8)
    assert abs(r['IB']['native_massflow_identity_error_kg_s'])<1e-6
    assert abs(r['OB']['native_massflow_identity_error_kg_s'])<1e-6
@pytest.mark.parametrize('choice',['mean','outlet'])
def test_independent_two_equation_solver(net,choice):
    def fun(x):
        mi,mo=x
        return [(mi+mo-net.total)/net.total,(net.branch('inboard',mi,choice)['channel_drop_Pa']-net.branch('outboard',mo,choice)['channel_drop_Pa'])/net.allowance]
    solved=root(fun,[net.nominal['inboard']*.75,net.nominal['outboard']*1.1],tol=1e-10)
    assert solved.success and max(abs(np.array(fun(solved.x))))<1e-9
    r=net.balance(choice)
    assert solved.x[0]==pytest.approx(r['IB']['flow_kg_s'],abs=1e-5)
@pytest.mark.parametrize('choice',['mean','outlet'])
def test_balancing_requirement_restores_nominal(net,choice):
    extra=net.branch('inboard',net.nominal['inboard'],choice)['channel_drop_Pa']-net.branch('outboard',net.nominal['outboard'],choice)['channel_drop_Pa']
    r=net.balance(choice,extra)
    assert r['both_below_temperature_limit']
    for side,key in [('inboard','IB'),('outboard','OB')]:assert r[key]['flow_kg_s']==pytest.approx(net.nominal[side],abs=1e-6)
@pytest.mark.parametrize('side',['inboard','outboard'])
def test_minimum_flow_is_actual_temperature_boundary(net,side):
    m=net.minimum_flow(side)
    assert net.branch(side,m)['peak_K']==pytest.approx(net.limit,abs=1e-6)
    assert net.branch(side,m*.999)['temperature_margin_K']<0
    assert net.branch(side,m*1.001)['temperature_margin_K']>0
@pytest.mark.parametrize('side',['inboard','outboard'])
def test_local_pressure_increases_with_flow(net,side):
    drops=[net.branch(side,net.nominal[side]*x)['channel_drop_Pa'] for x in [.7,1.,1.3]]
    assert drops[0]<drops[1]<drops[2]
def test_enthalpy_quadrature_error_is_small(result):
    for r in result['results']:
        for k in ['original_unsplit_unbalanced','selected_split_unbalanced','balanced_split']:
            for side in ['IB','OB']:assert abs(r[k][side]['exact_enthalpy_heat_error_relative'])<1e-4
@pytest.mark.parametrize('choice',['mean','outlet'])
def test_reserving_volume_does_not_create_new_coolant(net,result,choice):
    saved=next(r for r in result['results'] if r['property_choice']==choice)
    for side in net.lengths:
        frac=saved['inventory_reservation_upper_limits'][side]['maximum_reservation_fraction_before_any_header_loss']
        row=net.branch(side,net.nominal[side],choice,frac)
        volume=row['effective_BZ_channels']*math.pi*net.f['radius_fw_channel']**2*net.b['len_blkt_'+side+'_channel_total']
        assert volume+row['reserved_coolant_volume_m3']==pytest.approx(net.f['vfcblkt']*net.f['vol_blkt_'+side],abs=1e-9)
        assert row['channel_drop_Pa']==pytest.approx(net.allowance,abs=.01)
@pytest.mark.parametrize('side',['inboard','outboard'])
def test_greater_hardware_volume_raises_channel_loss(net,side):
    a=net.branch(side,net.nominal[side],reserve_fraction=0.)
    c=net.branch(side,net.nominal[side],reserve_fraction=.1)
    assert c['channel_drop_Pa']>a['channel_drop_Pa']
@pytest.mark.parametrize('flow',[-1.,0.,float('nan'),float('inf')])
def test_invalid_flow_rejected(net,flow):
    with pytest.raises(ValueError):net.branch('inboard',flow)
@pytest.mark.parametrize('fraction',[-.1,1.,float('nan')])
def test_invalid_volume_rejected(net,fraction):
    with pytest.raises(ValueError):net.branch('inboard',net.nominal['inboard'],reserve_fraction=fraction)
def test_original_pass_and_split_failure_are_both_preserved(result):
    for r in result['results']:
        assert r['original_unsplit_unbalanced']['both_below_temperature_limit']
        assert not r['selected_split_unbalanced']['both_below_temperature_limit']
        assert r['balanced_split']['both_below_temperature_limit']
def test_no_power_or_validated_manifold_claim(result):
    assert not result['power_output_recalculated']
    assert not result['validated_manifold_or_plant']
def test_replay_nominal_temperatures(result):
    for r in result['results']:
        assert r['balanced_split']['IB']['peak_K']==pytest.approx(798.2410597947791,abs=1e-6)
        assert r['balanced_split']['OB']['peak_K']==pytest.approx(793.4053516046565,abs=1e-6)
