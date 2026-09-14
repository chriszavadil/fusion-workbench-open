from pathlib import Path
import importlib.util, math
P=Path(__file__).resolve().parents[1]/'scripts'/'screen_integrated_candidate_path.py'
s=importlib.util.spec_from_file_location('candidate',P); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)

def test_baseline_fatigue_reproduces_authenticated_output():
    assert math.isclose(m.cycles_to_fracture(437993444.0663996,m.conduit_thickness(m.FSTEEL0)),5736.97861814937,rel_tol=0,abs_tol=1e-6)

def test_conservative_cross_study_candidate():
    r=m.build_result(); p=r['power']['conservative_hcpb_60pct_ec_600s']
    assert 406.5 < p['availability_adjusted_net_mw'] < 406.6
    assert 0.5815 < r['power']['ec_efficiency_for_400mw_avg'] < 0.5817

def test_dynamic_conduit_changes_fatigue_frontier():
    r=m.build_result(); c=r['cs']['screen_20000']
    assert 0.7403 < c['dr_cs_m'] < 0.7406
    assert 9.8 < c['conduit_mm'] < 9.9
    assert c['cycles'] >= 19999.999
    assert c['bop_current_density_ratio'] <= .7000000001
