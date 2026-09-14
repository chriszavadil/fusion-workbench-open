"""Same-boundary checks, not experimental confinement validation."""
from pathlib import Path
import copy,hashlib,importlib.util,json,math
import pytest
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'research/source/experiments/confinement_normalization_2026_09_09'
spec=importlib.util.spec_from_file_location('normalization',BASE/'audit.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
INPUT=json.loads((BASE/'FROZEN_INPUT.json').read_text());OUTPUT=json.loads((BASE/'KEY_RESULTS.json').read_text())
@pytest.mark.parametrize('name',['r838','r900'])
def test_deterministic_archived_cases(name):
 row=m.audit_case(INPUT['cases'][name]);assert row==OUTPUT['cases'][name]
 assert abs(row['same_boundary_thermal_deposited_H']-row['direct_thermal_energy_ratio_H'])<2e-10
 assert abs(row['transport_time_replay_error_s'])<1e-8
 assert row['same_boundary_thermal_deposited_H']>row['reported_hstar_reproduced']
 assert row['plant_power_or_geometry_changed'] is False

def test_zero_correction_is_identity():assert m.convert(1.2,400.,400.)==1.2
def test_power_normalization_composes():
 assert m.convert(m.convert(1.2,400,500),500,600)==pytest.approx(m.convert(1.2,400,600),rel=1e-13)
@pytest.mark.parametrize('x',[0,-1,True,None,float('nan'),float('inf')])
def test_invalid_power_is_not_silent_zero(x):
 with pytest.raises(ValueError):m.convert(1.,x,600.)
def test_other_scaling_not_mislabeled_ipb98():
 c=copy.deepcopy(INPUT['cases']['r838']);c['i_confinement_time_from_input']=1
 with pytest.raises(ValueError):m.audit_case(c)
def test_added_synchrotron_is_detected_by_boundary_check():
 c=copy.deepcopy(INPUT['cases']['r838']);c['values']['p_plasma_heating_total_mw']+=c['values']['p_plasma_sync_mw']
 with pytest.raises(ValueError,match='interface fails'):m.audit_case(c)
def test_frozen_input_hash():assert OUTPUT['frozen_input_sha256']==hashlib.sha256((BASE/'FROZEN_INPUT.json').read_bytes()).hexdigest()
