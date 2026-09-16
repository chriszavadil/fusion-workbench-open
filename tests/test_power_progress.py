"""Power-progress score/measurement separation and exact-record regression tests. MIT."""
from pathlib import Path
import copy,hashlib,importlib.util,json,math
import pytest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('power_progress',ROOT/'tools/build_power_progress.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
D=json.loads((ROOT/'docs/power-progress/data.json').read_text(encoding='utf-8'))
def test_best_excludes_retired_higher_claim_and_failures():
 best=m.select_best(D['history']);assert best['id']=='pulsedFixedR30'
 assert best['average_net_MW']==pytest.approx(274.01127289606546)
 retired=next(r for r in D['history'] if r['id']=='retired-screen');assert retired['average_net_MW']==406.53 and not retired['eligible_for_model_best']
 assert max(r['average_net_MW'] or 0 for r in D['history'])>best['average_net_MW']
 assert len(D['history'])==12 and len({r['id'] for r in D['history']})==12

def test_selection_is_data_driven_not_largest_number_or_hardcoded_winner():
 rows=copy.deepcopy(D['history']);future=copy.deepcopy(m.select_best(rows));future.update(id='test-only-new-point',average_net_MW=300.0);rows.append(future);assert m.select_best(rows)['id']==future['id']
 future['numerically_converged']=False;assert m.select_best(rows)['id']=='pulsedFixedR30'
 future.update(numerically_converged=True,eligible_for_model_best=False,average_net_MW=9000.0);assert m.select_best(rows)['id']=='pulsedFixedR30'
 assert m.select_best([]) is None
@pytest.mark.parametrize('r',D['history'],ids=lambda r:r['id'])
def test_every_historical_record_is_sourced_without_hardware_claim(r):
 assert r['source_sha256']==hashlib.sha256((ROOT/r['source_path']).read_bytes()).hexdigest()
 assert r['physical_qualification'] is False and r['measured_net_electric_MW'] is None
 if r['numerically_converged'] is False:assert r['average_net_MW'] is None and r['flat_top_net_MW'] is None and not r['eligible_for_model_best']
 if 'pulse_energy_kWh' in r:assert r['pulse_energy_kWh']*3.6/r['cycle_s']*r['availability']==pytest.approx(r['average_net_MW'],abs=1e-7)

def test_reference_and_control_are_not_confused():
 s=D['summary'];assert s['reference_average_net_MW']==pytest.approx(213.69131801996207)
 control=next(r for r in D['history'] if r['id']==s['controlled_comparison_id'])
 assert control['average_net_MW']==pytest.approx(214.6831275718135)
 assert s['controlled_average_delta_MW']==pytest.approx(59.328145324252)
 assert s['same_case_flat_top_net_MW']==pytest.approx(501.6592774049162)
 assert s['physical_net_electric_MW'] is None and s['physical_result_label']=='Not measured'

@pytest.mark.parametrize('r',D['world']['records'],ids=lambda r:r['id'])
def test_real_measurements_keep_original_boundary_units_and_credit(r):
 assert r['net_electric_MW'] is None and not r['measured_by_workbench']
 assert r['evidence']=='reported_physical_measurement' and r['metric_kind'] in ['fusion_energy_per_pulse','peak_fusion_power']
 assert r['unit']==('MJ' if r['metric_kind']=='fusion_energy_per_pulse' else 'MW_fusion')
 assert all(id in D['world']['sources'] for id in r['source_ids'])
 for d in r['derived_mean_fusion_power_MW']:assert d['MW']==r['value']/d['seconds'] and d['kind']=='derived_interval_mean_not_peak'
 if r['facility']=='NIF':assert r['derived_mean_fusion_power_MW']==[]

def test_latest_is_not_automatically_a_record_and_duration_difference_retained():
 nif=[r for r in D['world']['records'] if r['facility']=='NIF'];best=max(nif,key=lambda r:r['value']);latest=max(nif,key=lambda r:r['experiment_date'])
 assert best['value']==8.6 and latest['value']==7.9 and latest['experiment_date']=='2026-06-20'
 jet=next(r for r in D['world']['records'] if r['id']=='jet-2023-energy');assert [d['seconds'] for d in jet['duration_reports']]==[5.,5.2]
 assert jet['derived_mean_fusion_power_MW'][0]['MW']==13.8
 assert D['world']['verified_date']=='2026-09-16' and not D['world']['net_electric_world_record_claimed']

def test_qualification_event_does_not_invent_another_power_result():
 events=D['qualification_events'];assert any(e['date']=='2026-09-16' and not e['output_changed'] for e in events)
 assert not any(r['study_date']=='2026-09-16' for r in D['history'])
 assert D['no_new_scientific_runs'] and D['snapshot_not_live_monitoring']

def test_read_only_view_and_identical_data_projection():
 assert (ROOT/'app/data/power_progress.json').read_bytes()==(ROOT/'docs/power-progress/data.json').read_bytes()
 js=(ROOT/'docs/power-progress/view.js').read_text(encoding='utf-8');html=(ROOT/'docs/power-progress/index.html').read_text(encoding='utf-8')
 assert "fetch('data.json')" in js and 'innerHTML' not in js and '/api/' not in js and 'method:' not in js and 'localhost' not in js
 assert 'not net electricity' in html and 'Missing data are not plotted as zero' in html
 assert './power-progress/' in (ROOT/'tools/pages/overview.html').read_text(encoding='utf-8')
