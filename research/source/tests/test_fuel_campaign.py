from pathlib import Path
from dataclasses import replace
import sys
import math
import numpy as np
import pytest
from scipy.linalg import expm
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import audit_fuel_campaign as f

@pytest.mark.parametrize('field,value',[('burn_fraction',0),('burn_fraction',1.1),('tau_fast_s',0),('tau_slow_s',-1),('tau_blanket_s',float('nan')),('half_life_years',0),('direct_recycling_fraction',1.01),('recycle_yield',1.1),('blanket_yield',0),('puff_tritium_core_ratio',-1),('TBR',-1)])
def test_invalid_config(field,value):
    c=replace(f.FuelConfig(),**{field:value})
    with pytest.raises(ValueError):c.validate()

@pytest.mark.parametrize('dt',[0.,1.,360.,7200.,172800.])
def test_analytic_vs_independent_matrix_transition(dt):
    c=f.FuelConfig();x=np.array([.1,.5,1.,2.]);y=np.zeros(9);y[:4]=x;y[8]=1
    direct=f.analytic_step(c,x,3e-6,dt);matrix=(expm(f.matrix_generator(c,3e-6)*dt)@y)[:4]
    assert np.allclose(direct,matrix,rtol=1e-11,atol=1e-11)


def test_segment_semigroup():
    c=f.FuelConfig();x=np.array([.1,.5,1.,2.])
    one=f.analytic_step(c,x,3e-6,8000)
    two=f.analytic_step(c,f.analytic_step(c,x,3e-6,3000),3e-6,5000)
    assert np.allclose(one,two,rtol=1e-12,atol=1e-11)


def test_storage_only_decay():
    c=f.FuelConfig();x=np.array([0.,0.,0.,2.]);dt=1e6
    y=f.analytic_step(c,x,0.,dt)
    assert y[3]==pytest.approx(2*math.exp(-c.decay*dt),abs=1e-12)
    assert np.all(y[:3]==0)


def test_matrix_mass_conservation():
    c=f.FuelConfig();y=np.zeros(9);y[:4]=[.1,.5,1,20];y[8]=1.;initial=sum(y[:4])
    y=expm(f.matrix_generator(c,3e-6)*20000)@y
    assert sum(y[:4])+y[4]+y[5]+y[6]-y[7]==pytest.approx(initial,abs=1e-10)
    assert y[4]>=0 and y[5]>=0


def test_zero_recycle_yield_loss_identity():
    c=f.FuelConfig(recycle_yield=1.,blanket_yield=1.);y=np.zeros(9);y[3]=20;y[8]=1
    y=expm(f.matrix_generator(c,3e-6)*20000)@y
    assert y[4]==0


def test_injection_includes_puffing_and_burn():
    c=f.FuelConfig(puff_tritium_core_ratio=10.);q,inj=f.rates(c,3e-6)
    assert inj==pytest.approx(11*3e-6/.02)
    assert sum(q[:2])==pytest.approx(inj-3e-6)
    assert q[2]==pytest.approx(1.15*3e-6)


def test_campaign_solvers_and_balance():
    r=f.campaign(f.FuelConfig(),3e-6,700,7200,800,20*86400)
    assert r['max_mass_balance_error_kg']<1e-9
    assert r['analytic_vs_matrix_final_error_kg']<1e-9
    assert r['min_endpoint_available_kg']>=-1e-9


def test_lower_than_required_initial_stock_fails():
    c=f.FuelConfig();r=f.campaign(c,3e-6,700,7200,800,20*86400)
    until=r['required_stock_peak_time_days']*86400;stock=r['finite_horizon_minimum_initial_available_kg']
    x=np.array([0.,0.,0.,stock*.999]);t=0.
    while t<until-1e-8:
        for dt,burn in [(700.,0.),(7200.,3e-6),(800.,0.)]:
            dt=min(dt,until-t)
            if dt<=1e-8:break
            x=f.analytic_step(c,x,burn,dt);t+=dt
    assert x[3]<-1e-5


def test_direct_recycling_reduces_finite_horizon_stock():
    no=f.campaign(f.FuelConfig(direct_recycling_fraction=0.),3e-6,700,7200,800,20*86400)
    fast=f.campaign(f.FuelConfig(direct_recycling_fraction=.8),3e-6,700,7200,800,20*86400)
    assert fast['finite_horizon_minimum_initial_available_kg']<no['finite_horizon_minimum_initial_available_kg']
    assert fast['necessary_steady_state_budget']['minimum_TBR_ignoring_decay']==no['necessary_steady_state_budget']['minimum_TBR_ignoring_decay']


def test_finite_stock_does_not_prove_self_sufficiency():
    c=f.FuelConfig(puff_tritium_core_ratio=10.,recycle_yield=.9995)
    short=f.campaign(c,3e-6,700,7200,800,30*86400)
    long=f.campaign(c,3e-6,700,7200,800,60*86400)
    assert not long['necessary_steady_state_budget']['passes_necessary_mass_balance']
    assert long['finite_horizon_minimum_initial_available_kg']>short['finite_horizon_minimum_initial_available_kg']
    assert long['required_stock_peak_time_days']>59
