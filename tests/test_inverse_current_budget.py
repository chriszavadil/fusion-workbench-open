"""New current-budget evidence tests. No live solver or experimental qualification. MIT."""
from pathlib import Path
import hashlib,json
import numpy as np
import pytest
from scipy.integrate import simpson
ROOT=Path(__file__).resolve().parents[1];EXP=ROOT/'research/source/experiments/inverse_current_budget_2026_09_16'
CASES=['dx0.18_ff1_v6','dx0.18_ff2_v6','dx0.09_ff1_v6','dx0.09_ff2_v6']
@pytest.mark.parametrize('case',CASES)
def test_all_current_fields_and_integrals_are_traceable(case):
 p=EXP/'runs'/case;r=json.loads((p/'RESULT.json').read_text(encoding='utf-8'));d=r['result']
 assert hashlib.sha256((p/'CURRENT_FIELDS.npz').read_bytes()).hexdigest()==r['fields_sha256']
 assert hashlib.sha256((EXP/'current_budget.py').read_bytes()).hexdigest()==r['driver_sha256']
 assert hashlib.sha256((EXP/'KINETIC_INPUT.json').read_bytes()).hexdigest()==r['kinetic_sha256']
 assert r['completed'] and r['passed_numerical_checks'] and not r['physical_validation']
 assert r['restoration']['q_relative_error']<.0002
 with np.load(p/'CURRENT_FIELDS.npz') as z:
  assert len(z['psi_norm'])==401 and z['psi_norm'][0]==.01 and z['psi_norm'][-1]==.98
  for k in z.files:assert np.isfinite(z[k]).all()
  for k,reported in [('total_A_per_normalized_flux','total_current_in_tested_shell_A'),('bootstrap_A_per_normalized_flux','bootstrap_current_in_tested_shell_A'),('residual_A_per_normalized_flux','remaining_current_in_tested_shell_A')]:assert simpson(z[k],x=z['psi_norm'])==pytest.approx(d[reported],abs=1e-6)
  assert np.array_equal(z['total_A_per_normalized_flux']-z['bootstrap_A_per_normalized_flux'],z['residual_A_per_normalized_flux'])
  assert np.allclose(z['jB_Redl'],-z['jB_raw_unconverted_sign_diagnostic'],rtol=1e-12,atol=1e-7)
  assert (z['residual_A_per_normalized_flux']>0).all()
 assert abs(d['ampere_relative_error'])<.01 and abs(d['bootstrap_201_vs_401_relative_change'])<.01
 assert d['bootstrap_rescale_used'] is False and d['inductive_rescale_used'] is False

def test_not_a_new_power_result_or_complete_bootstrap_total():
 d=json.loads((ROOT/'docs/ec-wave/current-budget.json').read_text(encoding='utf-8'))
 assert d['new_power_result'] is None and not d['physical_validation'] and not d['candidate_current_qualified']
 assert d['interval']==[.01,.98] and len(d['cases'])==4
 for c in d['cases']:
  assert len(c['arrays']['psi_norm'])==401 and not c['summary']['complete_reactor_bootstrap_integral']
  assert c['summary']['EC_shell_lower_bound_with_original_inductive_total_A']<d['original_EC_total_A']

def test_refinement_and_known_alternative_correlations_preserved():
 check=json.loads((EXP/'INDEPENDENT_CHECKS.json').read_text(encoding='utf-8'));assert check['passed'] and len(check['checks'])==4
 for row in check['checks']:
  if 'bootstrap_relative_mesh_change' in row:assert abs(row['bootstrap_relative_mesh_change'])<.001
 original=json.loads((EXP/'EXISTING_SCALING_COMPARISON.json').read_text(encoding='utf-8'));assert original['active_model']=='Sauter'
 assert original['original_other_model_outputs']['f_c_plasma_bootstrap_aries']>original['active_fraction']
 report=(ROOT/'research/reports/results/INVERSE_CURRENT_BUDGET_2026-09-16.md').read_text(encoding='utf-8')
 assert 'already documented in the old output' in report and 'not a new' in report
 assert 'not a new qualified microwave-current target' in report

def test_current_view_is_an_actual_recorded_profile_not_a_new_simulation():
 js=(ROOT/'docs/ec-wave/current-budget.js').read_text(encoding='utf-8');html=(ROOT/'docs/ec-wave/index.html').read_text(encoding='utf-8')
 assert "fetch('current-budget.json')" in js and 'bootstrap_A_per_normalized_flux' in js
 assert 'innerHTML' not in js and '/api/' not in js and 'localhost' not in js
 assert 'new diagnostic' in html and '401 saved samples' in html and 'not a complete reactor' in html
 assert 'id="current-budget"' in html

@pytest.mark.parametrize('case',CASES)
def test_independent_simpson_and_archived_current_accounting(case):
 import math
 folder=EXP/'runs'/case;r=json.loads((folder/'RESULT.json').read_text(encoding='utf-8'));d=r['result']
 with np.load(folder/'CURRENT_FIELDS.npz') as z:
  x=z['psi_norm'];h=(float(x[-1])-float(x[0]))/(len(x)-1)
  assert len(x)%2==1 and np.allclose(np.diff(x),h,rtol=1e-12,atol=1e-15)
  for key,result_key in [('total_A_per_normalized_flux','total_current_in_tested_shell_A'),('bootstrap_A_per_normalized_flux','bootstrap_current_in_tested_shell_A')]:
   y=z[key];manual=h/3*math.fsum([float(y[0]),float(y[-1]),4*math.fsum(map(float,y[1:-1:2])),2*math.fsum(map(float,y[2:-1:2]))])
   assert manual==pytest.approx(d[result_key],abs=1e-6)
  assert d['remaining_current_in_tested_shell_A']==pytest.approx(d['total_current_in_tested_shell_A']-d['bootstrap_current_in_tested_shell_A'],abs=1e-8)
  assert d['EC_shell_lower_bound_with_original_inductive_total_A']==pytest.approx(max(0,d['positive_remaining_current_in_shell_A']-d['original_inductive_total_A']),abs=1e-8)
  assert d['uncomputed_axis_edge_current_A']>0

@pytest.mark.parametrize('case',CASES)
def test_full_coefficient_decomposition_and_pressure_energy_target(case):
 folder=EXP/'runs'/case;r=json.loads((folder/'RESULT.json').read_text(encoding='utf-8'))
 coeff=json.loads((folder/'PROFILES.json').read_text(encoding='utf-8'))['coefficients']
 original=json.loads((ROOT/'research/source/experiments/ec_equilibrium_2026_09_16/EXACT_INPUT.json').read_text(encoding='utf-8'))['scalar']
 assert r['restoration']['energy_J']==pytest.approx(original['e_plasma_beta'],rel=.002)
 with np.load(folder/'CURRENT_FIELDS.npz') as z:
  assert np.allclose(np.asarray(coeff['bra1'])+np.asarray(coeff['bra2'])+np.asarray(coeff['bra3']),z['jB_Redl'],rtol=1e-12,atol=1e-7)
  assert np.allclose(coeff['L31'],coeff['L34'],rtol=0,atol=0)
  assert np.allclose(np.asarray(coeff['F32_ee'])+np.asarray(coeff['F32_ei']),coeff['L32'],rtol=1e-12,atol=1e-14)
  assert not r['full_current_profile_or_equilibrium_self_consistency_solved']
