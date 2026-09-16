"""Progress classification, dependency and anti-repeat guard tests, not physics tests. MIT."""
from pathlib import Path
import copy,hashlib,importlib.util,json
import pytest
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('roadmap',ROOT/'tools/build_progress_roadmap.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
D=json.loads((ROOT/'docs/progress/data.json').read_text(encoding='utf-8'));P={p['id'] for p in D['prior_work']['entries']}
def test_every_existing_milestone_has_explicit_evidence_class():
 status=json.loads((ROOT/'project-status.json').read_text(encoding='utf-8'))
 assert {e['milestone_id'] for e in D['events']}=={e['id'] for e in status['milestones']}
 assert len(D['events'])==len({e['id'] for e in D['events']})
 assert all(e['kind'] in m.KINDS for e in D['events'])
@pytest.mark.parametrize('e',D['events'],ids=lambda e:e['id'])
def test_event_sources_and_nonphysical_boundary(e):
 for source in e['sources']:assert hashlib.sha256((ROOT/source['path']).read_bytes()).hexdigest()==source['sha256']
 assert e['net_electricity_measured_MW'] is None and not e['physical_fusion_demonstrated']
 assert e['limit'] and e['decision'] and e['date']<=D['summary']['reviewed_through']

def test_current_scientific_status_is_not_latest_app_change():
 latest=next(e for e in D['events'] if e['id']==D['summary']['latest_scientific_event_id'])
 assert latest['id']=='inverse-current-budget-20260916' and latest['kind']=='model_finding'
 assert any(e['id']=='progress-goals-20260916' and e['kind']=='interface' for e in D['events'])
 assert D['summary']['last_model_power_date']=='2026-09-14'
 assert not D['summary']['whole_reactor_qualified'] and D['new_scientific_runs']==0
 assert D['summary']['hardware_date'] is None

def test_goal_plan_is_checked_not_a_calendar_or_running_worker():
 m.validate_goals(D['goals'],P)
 assert len(D['goals'])==6
 assert all(g['due_date'] is None and g['start_date'] is None and g['execution_status']=='not_running' for g in D['goals'])
 with pytest.raises(ValueError):
  g=copy.deepcopy(D['goals']);g[0]['pass_rule']='';m.validate_goals(g,P)
 with pytest.raises(ValueError):
  g=copy.deepcopy(D['goals']);g[0]['depends_on']=['G6'];m.validate_goals(g,P)
 with pytest.raises(ValueError):
  g=copy.deepcopy(D['goals']);g[0]['reuse_ids']=['made-up-paper'];m.validate_goals(g,P)

def test_unready_current_task_does_not_pass_admission_review():
 task=json.loads((ROOT/'research/progress/NEXT_TASK_REVIEW.json').read_text())
 check=m.check_task_review(task,P)
 assert not check['ready_for_admission_review'] and not check['automatic_execution'] and not check['novelty_proven']
 assert 'Required inputs are not complete' in check['reasons']
 assert any('max_runs' in x for x in check['reasons'])
 assert check==D['next_task_review']

def test_unchanged_repeat_is_rejected_unless_verification_gap_is_named():
 task=json.loads((ROOT/'research/progress/NEXT_TASK_REVIEW.json').read_text());task.update(inputs_complete=True,max_runs=2,timeout_seconds=120,same_inputs_and_question_as_completed=True)
 assert not m.check_task_review(task,P)['ready_for_admission_review']
 task['independent_verification_gap']='Independent check of a changed numerical build, same input and expected output.'
 assert m.check_task_review(task,P)['ready_for_admission_review']
 assert not m.check_task_review(task,P)['novelty_proven']
 task['max_runs']=True
 assert not m.check_task_review(task,P)['ready_for_admission_review']

def test_same_existing_register_and_data_used_by_both_views():
 assert D['prior_work']==json.loads((ROOT/'research/prior_work_register.json').read_text(encoding='utf-8'))
 assert (ROOT/'app/data/progress_roadmap.json').read_bytes()==(ROOT/'docs/progress/data.json').read_bytes()
 js=(ROOT/'docs/progress/view.js').read_text(encoding='utf-8');mini=(ROOT/'tools/pages/progress-preview.js').read_text(encoding='utf-8')
 assert "from './chart.js'" in js and "from './progress/chart.js'" in mini
 assert "fetch('data.json')" in js and '/api/' not in js and 'innerHTML' not in js and 'eval(' not in js
 assert './progress/' in (ROOT/'tools/pages/overview.html').read_text(encoding='utf-8')
 assert 'build_progress_roadmap(root)' in (ROOT/'tools/build_pages.py').read_text(encoding='utf-8')
