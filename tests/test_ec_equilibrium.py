"""Exact evidence/identity tests, not experimental ECCD validation."""
from pathlib import Path
import hashlib,importlib.util,json,math
import numpy as np
import pytest
from scipy.integrate import simpson
ROOT=Path(__file__).resolve().parents[1];EQ=ROOT/'research/source/experiments/ec_equilibrium_2026_09_16';EC=ROOT/'research/source/experiments/ec_launch_2026_09_15'
D=json.loads((ROOT/'docs/ec-wave/data.json').read_text());E=json.loads((EC/'RESULTS.json').read_text());I=json.loads((EC/'INPUTS.json').read_text())
spec=importlib.util.spec_from_file_location('analytic_screen',EC/'analyze.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
@pytest.mark.parametrize('c',D['cases'],ids=lambda c:c['id'])
def test_complete_case_and_target_integrals(c):
 folder=EQ/'runs'/c['id'];raw=json.loads((folder/'RESULT.json').read_text())
 for k,v in raw.items():assert c[k]==v
 assert c['numerically_solved'] and c['mapping_converged'] and c['export_completed']
 assert abs(c['current_relative_error'])<.002 and abs(c['energy_relative_error'])<.002
 assert c['geqdsk_cocos']==7 and c['geqdsk_sha256']==sha(folder/'equilibrium.geqdsk')
 assert c['solution_sha256']==sha(folder/'SOLUTION.npz')
 assert not c['physical_validation'] and not c['proxy_matches_reference_q_screen']
 with np.load(folder/'SOLUTION.npz') as sol:
  assert np.array_equal(sol['boundary'],c['boundary_rz_m']);assert np.array_equal(sol['pressure'],c['pressure_Pa']);assert np.isfinite(sol['points']).all()
  assert np.all(np.diff(sol['rho_volume_map_used'])>=0) and np.min(sol['pressure'])>=-1e-6
  assert len(sol['points'])==c['mesh_nodes'] and len(sol['triangles'])==c['mesh_triangles']
 assert c['surfaces']==json.loads((folder/'SURFACES.json').read_text())
@pytest.mark.parametrize('c',D['mesh_comparisons'],ids=lambda c:str(c['ffprime_exponent']))
def test_refinement_not_physical_uncertainty(c):
 coarse=next(r for r in D['cases'] if r['id']==c['coarse_id']);fine=next(r for r in D['cases'] if r['id']==c['fine_id'])
 assert c['q95_relative_mesh_change']==fine['q_sample'][3]/coarse['q_sample'][3]-1
 assert abs(c['q95_relative_mesh_change'])<.001 and fine['q95_relative_difference']>.25
 assert fine['mesh_nodes']>coarse['mesh_nodes'] and fine['q_sample_psi'][0]==.01

def test_contour_volume_identity_independently():
 theta=np.linspace(0,2*np.pi,20001)[:-1];R0,r=8.,2.;x=R0+r*np.cos(theta);z=r*np.sin(theta);xn,zn=np.roll(x,-1),np.roll(z,-1)
 volume=abs(np.sum((x+xn)*(x*zn-xn*z))*np.pi/3)
 assert volume==pytest.approx(2*np.pi**2*R0*r*r,rel=2e-8)
@pytest.mark.parametrize('c',I['candidate_parameters'].values())
def test_reconstructed_profile_moments(c):
 rho=np.linspace(0,1,20001);n,t,_=a.reconstructed_profile(c,I['profile_parameters'],rho)
 assert np.min(n)>0 and np.min(t)>0
 assert simpson(2*rho*n,x=rho)==pytest.approx(c['ne_volume_average_m3'],rel=1e-10)
 assert simpson(2*rho*t,x=rho)==pytest.approx(c['Te_volume_average_keV'],abs=1e-7)
def test_all_analytic_identities_and_no_assigned_ray_result():
 assert E['evaluation_count']==56 and len(E['all_local_evaluations'])==56 and E['ray_runs']==0
 for r in E['all_local_evaluations']:
  for k in ['resonance_error','onset_error','independent_root_error','N_formula_disagreement']:assert r[k]<1e-10
  assert r['local_cold_dispersion']['polarization_matrix_residual']<1e-9
  assert r['achieved_current_MA'] is None and not r['physical_validation']
 assert E['inputs_sha256']==sha(EC/'INPUTS.json') and E['admission_sha256']==sha(EC/'ADMISSION.json')
def test_lower_resonance_crossing_is_checked():
 p=next(r for r in E['cases']['alternative30']['fixed_frequency_probes'] if r['frequency_GHz']==170)
 assert not p['nominal_tail_is_minimum_energy_crossing']
 assert p['resonance_crossings']['smaller_energy_keV']<40
 for r in E['all_local_evaluations']:
  fc=a.characteristic(r['ne_local_m3'],r['B_toroidal_proxy_T'])[1]/(2*math.pi*1e9)
  assert a.resonance_crossings(fc,r['frequency_GHz'],r['N_parallel_magnitude'])['smaller_energy_keV']==pytest.approx(r['resonant_energy_keV'],abs=1e-8)
def test_reference_ray_not_candidate_current():
 r=D['reference_ray'];assert r['not_fusion_workbench_reactor'] and not r['physical_validation']
 assert r['recorded_points']==343 and r['ray_stop_status']==2 and r['reference_run_completed']
 assert all(len(v)==343 and np.isfinite(v).all() for v in r['recorded_arrays'].values())
 assert r['final_to_initial_ray_power_ratio']<1e-4
 assert D['evidence_levels']['candidate_ray_runs']==0 and D['evidence_levels']['candidate_achieved_drive_A'] is None

def test_restored_electron_pressure_array():
 c=I['candidate_parameters']['alternative30'];rho=np.asarray(D['input']['rho']);n,t,_=a.reconstructed_profile(c,I['profile_parameters'],rho)
 original=np.asarray(D['input']['profiles']['pres_plasma_electron_profile']);error=float(np.max(abs(n*t*1000*a.e/original-1)))
 assert error<1e-10 and D['original_analytic_pressure_roundtrip']['passed']
 assert len(original)==201 and len(D['input']['profiles']['pres_plasma_thermal_total_profile'])==201

def test_static_interface_only_reads_scoped_data():
 html=(ROOT/'docs/ec-wave/index.html').read_text(encoding='utf-8');js=(ROOT/'docs/ec-wave/view.js').read_text(encoding='utf-8')
 assert "fetch('data.json')" in js and 'innerHTML' not in js and 'eval(' not in js
 assert '/api/' not in js and 'localhost' not in js and '127.0.0.1' not in js and 'method:' not in js
 assert 'not exact q0' in js and 'Not yet a qualified reactor equilibrium' in html
 assert '343' in html and 'canonical ITER' in html and 'display-only' in html
 assert "connect-src 'self'" in html and 'Content-Security-Policy' in html

def test_report_preserves_scientific_rejection_and_attribution():
 text=(ROOT/'research/reports/results/EC_EQUILIBRIUM_INTERFACE_2026-09-16.md').read_text(encoding='utf-8')
 assert text.startswith('# EC equilibrium interface:') and 'GENRAY' in text and 'TokaMaker' in text and 'Lopez' in text
 assert 'not proof the concept is impossible' in text and '1.521368' in text and '3.895664' in text
 assert 'fast' in text and 'COCOS7' in text and 'not exact q0' in text
