from dataclasses import replace
from pathlib import Path
import math
import sys
import numpy as np
import pytest
from scipy.integrate import solve_ivp
from scipy.linalg import expm

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import audit_periodic_fuel as p

BASE = p.Schedule(700., 7400., 790.)
BURN = 3.66e-6

@pytest.mark.parametrize('kw', [dict(burn_fraction=0),dict(TBR=-1),dict(tau_fast_s=0),dict(half_life_years=math.inf),dict(direct_recycling_fraction=math.nan)])
def test_invalid_physical_parameter(kw):
    with pytest.raises(ValueError): p.periodic_initial(replace(p.FuelConfig(), **kw), BASE, BURN)

@pytest.mark.parametrize('kw', [dict(burn_s=0),dict(before_s=-1),dict(after_s=math.nan),dict(repeats=0),dict(repeats=True),dict(repeats=1.5),dict(tail_outage_s=-1)])
def test_invalid_schedule(kw):
    with pytest.raises(ValueError): p.periodic_initial(p.FuelConfig(), replace(BASE, **kw), BURN)

@pytest.mark.parametrize('r', [-1., math.inf, math.nan])
def test_invalid_reserve(r):
    with pytest.raises(ValueError): p.threshold(p.FuelConfig(), BASE, BURN, r)

@pytest.mark.parametrize('dt', [0.,1.,360.,8000.,10**6])
def test_exact_homogeneous_transition_vs_exponential(dt):
    c=p.FuelConfig(); A=p.matrix_generator(c,0.)[:4,:4]
    assert np.allclose(p.linear_transition(c,dt), expm(A*dt), rtol=2e-12, atol=1e-12)

@pytest.mark.parametrize('g', [0., 1., 10.])
def test_fixed_point_independent_matrix(g):
    c=p.FuelConfig(puff_tritium_core_ratio=g)
    x,_=p.periodic_initial(c,BASE,BURN); y,_=p.periodic_initial(c,BASE,BURN,matrix_method=True)
    assert np.max(abs(x-y))<5e-8

@pytest.mark.parametrize('g', [0., 1., 10.])
def test_limiting_orbit_closes(g):
    c=p.FuelConfig(puff_tritium_core_ratio=g)
    r=p.periodic_assessment(c,BASE,BURN)
    assert r['direct_period_closure_error_kg']<1e-9
    assert 0<r['spectral_radius']<1

@pytest.mark.parametrize('reserve', [0.,.5,2.])
def test_threshold_straddling(reserve):
    c=p.FuelConfig(); t=p.threshold(c,BASE,BURN,reserve)
    assert abs(t['assessment_at_threshold']['reserve_margin_kg'])<1e-7
    low=p.periodic_assessment(replace(c,TBR=t['critical_TBR']-1e-5),BASE,BURN,reserve)
    high=p.periodic_assessment(replace(c,TBR=t['critical_TBR']+1e-5),BASE,BURN,reserve)
    assert low['classification']=='periodic_reserve_fail'
    assert high['classification']=='periodic_reserve_pass'


def test_more_reserve_requires_more_breeding():
    vals=[p.threshold(p.FuelConfig(),BASE,BURN,r)['critical_TBR'] for r in (0.,.5,2.)]
    assert vals[0]<vals[1]<vals[2]


def test_mean_balance_can_pass_when_trough_fails():
    c=p.FuelConfig(puff_tritium_core_ratio=10.,recycle_yield=.9999)
    t=p.threshold(c,BASE,BURN,.5)['critical_TBR']; m=p.mean_balance_lower_bound(c,BASE,BURN,.5)
    assert m<t
    r=p.periodic_assessment(replace(c,TBR=(m+t)/2),BASE,BURN,.5)
    assert r['classification']=='periodic_reserve_fail'
    assert .2<r['min_available_kg']<.5


def test_breeding_response_affine():
    c=p.FuelConfig();xs=[p.periodic_initial(replace(c,TBR=t),BASE,BURN)[0] for t in (1.,1.1,1.2)]
    assert np.allclose((xs[0]+xs[2])/2,xs[1],atol=1e-8,rtol=1e-11)


def test_same_burn_same_mean_bound_not_same_trough_requirement():
    c=p.FuelConfig(puff_tritium_core_ratio=10.,recycle_yield=.9999)
    # Exactly the same burn and calendar time; only outage clustering changes.
    clustered=replace(BASE,repeats=30,tail_outage_s=30*BASE.pulse_s*.25)
    distributed=replace(BASE,after_s=BASE.after_s+BASE.pulse_s*.25)
    lb0=p.mean_balance_lower_bound(c,clustered,BURN,.5);lb1=p.mean_balance_lower_bound(c,distributed,BURN,.5)
    assert lb0==pytest.approx(lb1,abs=1e-12)
    t0=p.threshold(c,clustered,BURN,.5);t1=p.threshold(c,distributed,BURN,.5)
    assert t0['critical_TBR']>t1['critical_TBR']


def test_block_powering_vs_explicit_sequence():
    c=p.FuelConfig();s=replace(BASE,repeats=30,tail_outage_s=70000.)
    F=p.period_map(c,s,BURN); manual=np.eye(5)
    for dt,on,_,_ in s.phases():manual=p.phase_map(c,BURN if on else 0.,dt)@manual
    assert np.allclose(F,manual,atol=2e-13,rtol=2e-12)


def test_threshold_empty_reservoir_seed_dominates_orbit_analytically():
    c=p.FuelConfig();r=p.threshold(c,BASE,BURN,.5);c=replace(c,TBR=r['critical_TBR'])
    xp=np.array(r['assessment_at_threshold']['periodic_initial_state_kg'])
    seed=r['sufficient_empty_reservoir_initial_store_kg']
    delta0=np.array([0.,0.,0.,seed])-xp
    for t in (0.,100.,1e4,1e6,1e8,1e9):
        difference=(p.linear_transition(c,t)@delta0)[3]
        known=math.exp(-c.decay*t)*np.dot(c.yields*xp[:3],np.exp(-t/c.tau))
        assert difference==pytest.approx(known,abs=1e-12)
        assert difference>=-1e-12


def test_threshold_seed_remains_above_reserve_with_zero_initial_holdups():
    c=p.FuelConfig();r=p.threshold(c,BASE,BURN,.5);c=replace(c,TBR=r['critical_TBR'])
    x=np.array([0.,0.,0.,r['sufficient_empty_reservoir_initial_store_kg']])
    for _ in range(100):
        for dt,on,_,_ in BASE.phases():
            for t in np.linspace(0,dt,9):
                assert p.analytic_step(c,x,BURN if on else 0.,t)[3]>=.5-1e-7
            x=p.analytic_step(c,x,BURN if on else 0.,dt)


def test_half_burn_and_half_reserve_scale_inventory_without_changing_threshold():
    c=p.FuelConfig();a=p.threshold(c,BASE,BURN,.5);b=p.threshold(c,BASE,BURN/2,.25)
    assert a['critical_TBR']==pytest.approx(b['critical_TBR'],abs=1e-11)
    assert a['sufficient_empty_reservoir_initial_store_kg']/2==pytest.approx(b['sufficient_empty_reservoir_initial_store_kg'],abs=1e-8)


def test_independent_adaptive_ode_orbit():
    c=p.FuelConfig(puff_tritium_core_ratio=10.,recycle_yield=.9999)
    th=p.threshold(c,BASE,BURN,.5);c=replace(c,TBR=th['critical_TBR'])
    x=np.array(th['assessment_at_threshold']['periodic_initial_state_kg']);x0=x.copy()
    min_sample=math.inf
    for dt,on,_,_ in BASE.phases():
        G=p.matrix_generator(c,BURN if on else 0.);A=G[:4,:4];u=G[:4,8]
        sol=solve_ivp(lambda t,x:A@x+u,(0,dt),x,method='DOP853',rtol=1e-11,atol=1e-12,dense_output=True)
        assert sol.success
        min_sample=min(min_sample,float(np.min(sol.sol(np.linspace(0,dt,257))[3])))
        x=sol.y[:,-1]
    assert np.max(abs(x-x0))<1e-9
    assert min_sample==pytest.approx(.5,abs=1e-7)


def test_finite_initial_stock_does_not_change_bad_asymptotic_orbit():
    c=p.FuelConfig(puff_tritium_core_ratio=10.,recycle_yield=.9995)
    x,_=p.periodic_initial(c,BASE,BURN)
    assert p.orbit_extrema(c,BASE,BURN,x)['min_available_kg']<0
    # At a fixed phase, ANY finite perturbation decays since all eigenvalues <1.
    difference=p.linear_transition(c,1000*p.YEAR_S)@np.array([20.,20.,20.,100.])
    assert np.max(abs(difference))<1e-20


def test_steady_state_lower_bound_in_constant_burn_schedule():
    s=p.Schedule(0.,10000.,0.);c=p.FuelConfig()
    t=p.threshold(c,s,BURN,.5)['critical_TBR'];lb=p.mean_balance_lower_bound(c,s,BURN,.5)
    assert t==pytest.approx(lb,abs=1e-10)


def test_interior_minimum_path_is_exercised():
    # Empty holdup with enough store causes initial drawdown, then rising return.
    c=p.FuelConfig(TBR=2.);s=p.Schedule(10.,8e6,100.)
    x,_=p.periodic_initial(c,s,BURN)
    initial=np.array([0.,0.,0.,30.])
    result=p.orbit_extrema(c,s,BURN,initial)
    assert result['interior_extrema_count']>0
    assert result['min_phase']=='burn'
    assert 0<result['min_local_time_s']<s.burn_s
    at_min=p.analytic_step(c,p.analytic_step(c,initial,0.,s.before_s),BURN,result['min_local_time_s'])
    assert abs(p.stored_derivative(c,at_min,BURN))<1e-12


def test_recycling_is_not_magic_fuel_source():
    for direct in (0.,.8,1.):
        c=p.FuelConfig(puff_tritium_core_ratio=10.,recycle_yield=.9995,direct_recycling_fraction=direct)
        assert p.threshold(c,BASE,BURN,.5)['critical_TBR']>1.15
