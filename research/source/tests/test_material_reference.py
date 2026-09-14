from pathlib import Path
import sys, math, json, os
import numpy as np
import pytest
from scipy.linalg import expm
from scipy.integrate import solve_ivp
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import material_release_reference as m
import material_cooldown_bounds as cool

@pytest.fixture(scope='module')
def results(tmp_path_factory):
    archive=os.environ.get('FUSION_POWER_ARCHIVE')
    if not archive:pytest.skip('Set FUSION_POWER_ARCHIVE to the original power archive')
    output=tmp_path_factory.mktemp('material_reference')
    result=m.run(Path(archive),output)
    result['_frozen_input']=json.loads((output/'MATERIAL_REFERENCE_FROZEN_INPUT.json').read_text())
    return result

@pytest.mark.parametrize('n',[16,64,128])
def test_fv_conservation_with_independent_augmented_exponential(n):
    c=m.Reference();dx=c.thickness_m/n;L=c.L;D=c.diffusivity_m2_s
    # Independent time generator with one explicit escaped-inventory state.
    A=np.zeros((n+2,n+2));z=np.zeros(n+2);z[0]=1
    A[0,0]=-2*L*D/dx;A[0,1]=2*L*D/dx
    A[1,0]=2*D/dx**2;A[1,1]=-3*D/dx**2;A[1,2]=D/dx**2
    for i in range(2,n):A[i,i-1]=A[i,i+1]=D/dx**2;A[i,i]=-2*D/dx**2
    A[n,n-1]=D/dx**2;A[n,n]=-3*D/dx**2;A[-1,n]=2*L*D/dx
    mass=np.r_[1.,np.full(n,L*dx),1.]
    assert max(abs(mass@A))<1e-8
    x=expm(A*40)@z;y=m.enclosure_fv(c,[40],n)
    assert x[0]==pytest.approx(y['pressure_fraction'][0],abs=1e-10)
    assert x[-1]==pytest.approx(y['escaped_fraction'][0],abs=1e-9)
    assert np.dot(mass,x)==pytest.approx(1,abs=1e-9)

def test_reference_mesh_converges(results):
    rows=results['external_reference_fv_refinement'];e=[r['max_pressure_abs_error'] for r in rows]
    assert all(a>b for a,b in zip(e,e[1:]))
    assert e[-1]<5e-6

def test_source_pressure_is_not_escaped_inventory(results):
    x=results['external_reference_fv_refinement'][-1]
    for p,w,e in zip(x['pressure_fraction'],x['wall_inventory_fraction'],x['escaped_fraction']):
        assert p+w+e==pytest.approx(1,abs=1e-12)
        assert 1-p>=e
    assert x['wall_inventory_fraction'][3]>.35

def test_spectral_truncation_converged():
    c=m.Reference();t=[1,2,10,40,140]
    assert max(abs(m.root_pressure(c,t,128)-m.root_pressure(c,t,1024)))<1e-12

def test_material_units_and_consistency(results):
    rows=results['reported_material_points_and_conditional_kernels']
    assert rows[1]['D_m2_s']==pytest.approx(1.19e-15)
    assert rows[2]['D_m2_s']==pytest.approx(5.34e-15)
    assert .99<rows[2]['inferred_effective_radius_m_NOT_measured']/rows[1]['inferred_effective_radius_m_NOT_measured']<1.01
    assert 'inferred_effective_radius_m_NOT_measured' not in rows[0]

@pytest.mark.parametrize('n',[32,128,512])
def test_modes_mass_and_mean_bound(n):
    w,k,prompt,bound=m.sphere_modes(3600,n)
    assert sum(w)+prompt==pytest.approx(1,abs=1e-14)
    assert 3600-np.dot(w,1/k)==pytest.approx(bound,abs=1e-10)
    assert prompt>0 and bound>0

def test_sphere_independent_mesh_convergence(results):
    rows=results['sphere_fv_validation']
    for key in ['max_fresh_survival_error','max_steady_survival_error']:
        e=[r[key] for r in rows]
        assert all(a>b for a,b in zip(e,e[1:]))
    assert rows[-1]['max_fresh_survival_error']<2e-4
    assert rows[-1]['max_steady_survival_error']<5e-6

def test_release_depends_on_initial_profile():
    f=float(m.fresh_fraction_released(2,21.3));s=float(m.steady_shutdown_fraction_released(2,21.3))
    e=float(m.fresh_fraction_released(2,21.3,'exponential'))
    assert s<e<f

@pytest.mark.parametrize('x',[0.,.1,1.,20.])
def test_kernel_probability_bounds(x):
    for kind in ['sphere','exponential']:
        y=m.fresh_fraction_released(x,1,kind)
        assert 0<=y<=1
    assert 0<=m.steady_shutdown_fraction_released(x,1)<=1

@pytest.mark.parametrize('bad',[0,-1,math.nan,math.inf])
def test_invalid_mean(bad):
    with pytest.raises(ValueError):m.sphere_modes(bad)

@pytest.mark.parametrize('bad',[-1,math.nan,math.inf])
def test_invalid_time(bad):
    with pytest.raises(ValueError):m.fresh_fraction_released(bad,1)

def test_modal_threshold_refines(results):
    for case in results['inherited_ledger_material_sensitivity']:
        rows=case.get('sphere_refinement')
        if not rows:continue
        assert max(r['period_closure_error_kg'] for r in rows)<1e-9
        assert max(abs(r['reserve_margin_kg']) for r in rows)<1e-6
        assert abs(rows[-1]['critical_TBR']-rows[-2]['critical_TBR'])<1e-10
        assert rows[-1]['mean_tail_error_bound_s']<.001

def test_smaller_material_delay_does_not_rescue_assumed_loss_case(results):
    rows=[x for x in results['inherited_ledger_material_sensitivity'] if x['g_assumed']==10]
    assert all(x['exponential_critical_TBR']>1.29 for x in rows)

def test_modal_both_sides_of_boundary(results):
    import audit_periodic_fuel as p
    cfg=p.FuelConfig(puff_tritium_core_ratio=0)
    source=results['_frozen_input']
    s=p.Schedule(**source['schedule']);B=source['B_kg_s']
    out=m.modal_threshold(cfg,s,B,21.3*3600,256)
    for delta,sign in [(-1e-5,-1),(1e-5,1)]:
        r=m.modal_case(cfg,s,B,21.3*3600,256,.5,out['critical_TBR']+delta)
        assert sign*r['reserve_margin_kg']>0

def test_cooling_diffusion_clock_obeys_endpoint_bounds():
    hot,cold,t=938.15,373.15,5400
    clock,_=cool.diffusion_clock('linear_cooling_sensitivity',t,hot,cold)
    lo,_=cool.diffusion_clock('instant_cold',t,hot,cold)
    hi,_=cool.diffusion_clock('held_hot',t,hot,cold)
    assert lo<clock<hi
    assert hi==pytest.approx(t)
    assert lo==pytest.approx(t*cool.D_kelvin(cold)/cool.D_kelvin(hot))

def test_cooling_clock_independent_time_integration():
    hot,cold,t=938.15,373.15,5400
    ref,_=cool.diffusion_clock('linear_cooling_sensitivity',t,hot,cold)
    errors=[]
    for n in [101,1001,10001]:
        tt=np.linspace(0,t,n);D=np.array([cool.D_kelvin(hot+(cold-hot)*x/t)/cool.D_kelvin(hot) for x in tt])
        errors.append(abs(np.trapezoid(D,tt)-ref))
    assert errors[2]<errors[1]<errors[0]
    assert errors[-1]<2e-5

def test_temperature_fv_independent_time_rescaling():
    # Direct non-autonomous ODE on normalized radial transform v=r*c, vs
    # a constant-coefficient solution evaluated at the integrated diffusion clock.
    n=40;dx=1/(n+1);rho=np.arange(1,n+1)*dx
    A=(np.diag(-2*np.ones(n))+np.diag(np.ones(n-1),1)+np.diag(np.ones(n-1),-1))/dx**2
    hot,cold,t=938.15,373.15,5400
    radius=.000375;v0=rho*(1-rho**2)
    scale=lambda tt:cool.D_kelvin(hot+(cold-hot)*tt/t)/radius**2
    sol=solve_ivp(lambda tt,y:scale(tt)*(A@y),(0,t),v0,method='BDF',rtol=2e-10,atol=2e-12)
    clock,_=cool.diffusion_clock('linear_cooling_sensitivity',t,hot,cold)
    ref=expm(A*cool.D_kelvin(hot)*clock/radius**2)@v0
    assert sol.success
    assert max(abs(sol.y[:,-1]-ref))<1e-8

def test_three_cooling_profiles_order(tmp_path):
    r=cool.run(tmp_path)
    assert r['D_hot_over_cold']==pytest.approx(48.5354749497,rel=1e-9)
    for d in [250,750,1250]:
        rows={x['profile']:x for x in r['cases'] if x['diameter_um']==d}
        f=lambda key:rows[key]['fraction_released_during_shutdown']
        assert f('instant_cold')<f('linear_cooling_sensitivity')<f('held_hot')


@pytest.mark.parametrize('field,bad',[('volume_m3',0),('thickness_m',-1),('temperature_K',math.nan)])
def test_invalid_reference_parameters(field,bad):
    from dataclasses import replace
    with pytest.raises(ValueError):replace(m.Reference(),**{field:bad})

@pytest.mark.parametrize('beta',[math.nan,-1.])
def test_invalid_modal_tbr(beta):
    import audit_periodic_fuel as p
    with pytest.raises(ValueError):m.modal_case(p.FuelConfig(),p.Schedule(700,7400,790),3.66e-6,3600,tbr=beta)

@pytest.mark.parametrize('hot,cold',[(900,math.nan),(math.inf,300),(900,-1)])
def test_invalid_cooling_temperature(hot,cold):
    with pytest.raises(ValueError):cool.diffusion_clock('held_hot',5400,hot,cold)
