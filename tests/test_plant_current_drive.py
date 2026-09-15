"""Candidate-specific plant accounting tests, not experimental fusion validation."""
from pathlib import Path
import hashlib,importlib.util,json,math,re
import pytest
ROOT=Path(__file__).resolve().parents[1]
EXP=ROOT/'research/source/experiments/plant_current_drive_2026_09_14'
spec=importlib.util.spec_from_file_location('plant_inputs',EXP/'prepare_inputs.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
D=json.loads((ROOT/'docs/plant-decision/data.json').read_text(encoding='utf-8'))
@pytest.mark.parametrize('case',D['cases'],ids=lambda c:c['id'])
def test_balance_and_recorded_average(case):
 t,p=case['time_s'],case['net_profile_MW'];assert len(t)==len(p)==7 and all(b>a for a,b in zip(t,t[1:]))
 energy=math.fsum((t[i+1]-t[i])*(p[i]+p[i+1])/2 for i in range(6))/3.6
 assert energy==pytest.approx(case['pulse_energy_kWh'],abs=1e-6)
 assert energy*3.6/t[-1]*D['conditions']['availability_assumed']==pytest.approx(case['average_MW'],abs=1e-8)
 assert case['gross_MW']-case['internal_MW']==pytest.approx(case['net_MW'],abs=1e-7)
 assert case['drive_MW']+case['reserve_MW']==pytest.approx(case['injected_MW'],abs=1e-8)
 assert case['injected_MW']/0.5==pytest.approx(case['heating_electric_MW'],abs=1e-7)
 assert case['required_cycles']==pytest.approx(30*.8*31557600/t[-1],rel=1e-12)
 assert case['fatigue_cycles']>=case['required_cycles']
 assert case['physical_validation'] is False and case['accepted_reference_replaced'] is False
@pytest.mark.parametrize('reserve',[75,30])
def test_exact_executed_input_is_reconstructible(reserve):
 raw=m.make_input((ROOT/'research/approved_inputs/r838.IN.DAT').read_bytes(),reserve)
 assert hashlib.sha256(raw).hexdigest()==m.EXPECTED[reserve]
 text=raw.decode('utf-8');ids=[int(x) for x in re.findall(r'(?m)^\s*icc\s*=\s*(\d+)',text)];variables=[int(x) for x in re.findall(r'(?m)^\s*ixc\s*=\s*(\d+)',text)]
 assert len(ids)==27 and len(variables)==19 and 13 in ids and 90 in ids and 3 not in variables
 assert 'i_figure_merit = -17' in text

def test_only_final_allocation_differs_between_controlled_inputs():
 b=(ROOT/'research/approved_inputs/r838.IN.DAT').read_bytes();left=m.make_input(b,75);right=m.make_input(b,30)
 assert left.replace(b'p_hcd_primary_extra_heat_mw = 75\n',b'p_hcd_primary_extra_heat_mw = 30\n')==right

def test_unapproved_input_is_not_silently_accepted():
 with pytest.raises(ValueError):m.make_input(b'changed base',75)
 with pytest.raises(ValueError):m.make_input((ROOT/'research/approved_inputs/r838.IN.DAT').read_bytes(),10)

def test_gain_not_misrepresented_as_internal_power_saving():
 a,b=D['cases'];assert a['radius_m']==b['radius_m'] and b['internal_MW']>a['internal_MW'] and b['pumps_MW']>a['pumps_MW']
 assert b['net_MW']-a['net_MW']==pytest.approx(D['delta']['net_MW'],abs=1e-8)
 assert b['average_MW']-a['average_MW']==pytest.approx(D['delta']['average_MW'],abs=1e-8)
 assert not D['conditions']['control_reserve_validated'] and not D['physical_validation']

def test_failed_solves_remain_visible_without_feasible_output():
 assert len(D['attempts'])==6
 for row in D['attempts'][:2]:assert row['ifail']==5 and row['feasible_power_MW'] is None

def test_static_view_is_read_only_and_scoped():
 html=(ROOT/'docs/plant-decision/index.html').read_text(encoding='utf-8');js=(ROOT/'docs/plant-decision/view.js').read_text(encoding='utf-8')
 assert 'has <em>not</em> been shown sufficient' in html and 'not identical' in html.lower() or 'not identical' in json.dumps(D).lower()
 assert "fetch('data.json')" in js and 'innerHTML' not in js and 'eval(' not in js
 assert '/api/' not in js and '127.0.0.1' not in js and 'localhost' not in js and 'method:' not in js
 assert "connect-src 'self'" in html and 'Content-Security-Policy' in html
 for name in ['data.json','view.js','style.css']:assert (ROOT/'docs/plant-decision'/name).is_file()
