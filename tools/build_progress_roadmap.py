"""Project recorded decisions/goals into a lay-reader timeline; no maturity score. MIT."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
KINDS={'model_finding','unresolved_test','verification_reuse','interface'}
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def validate_goals(goals,prior_ids):
 byid={g['id']:g for g in goals}
 if len(byid)!=len(goals):raise ValueError('Duplicate goal identifiers')
 for g in goals:
  for key in ['title','phase','status','checkpoint','deliverable','pass_rule','stop_rule','reuse_ids','missing_inputs']:
   if not g.get(key):raise ValueError('Missing goal review field: '+g['id']+'/'+key)
  if any(x not in prior_ids for x in g['reuse_ids']):raise ValueError('Unattributed prior-work reference')
  if any(x not in byid or x==g['id'] for x in g['depends_on']):raise ValueError('Invalid dependency')
  if g.get('execution_status')!='not_running':raise ValueError('This plan has no live execution evidence')
 def visit(id,parents):
  if id in parents:raise ValueError('Cyclic goal dependency')
  for dep in byid[id]['depends_on']:visit(dep,parents|{id})
 for id in byid:visit(id,set())

def check_task_review(task,prior_ids):
 reasons=[]
 for field in ['decision','closest_prior_work_ids','what_changes','success_test','falsification','execution_budget','reopen_condition']:
  if not task.get(field):reasons.append('Missing '+field)
 if any(x not in prior_ids for x in task.get('closest_prior_work_ids',[])):reasons.append('Unknown prior-work reference')
 for field in ['max_runs','timeout_seconds']:
  if type(task.get(field)) is not int or task[field]<=0:reasons.append('Missing positive bounded '+field)
 if not task.get('inputs_complete'):reasons.append('Required inputs are not complete')
 if task.get('same_inputs_and_question_as_completed') and not task.get('independent_verification_gap'):reasons.append('Unchanged repeat without a named independent-verification gap')
 if not task.get('reviewed_by_person_or_agent'):reasons.append('Scientific/novelty review is not recorded')
 return {'ready_for_admission_review':not reasons,'reasons':reasons,'novelty_proven':False,'automatic_execution':False}

def build(root=ROOT):
 root=root.resolve();folder=root/'research/progress';events=read(folder/'EVENTS.json');plan=read(folder/'GOALS.json');prior=read(root/'research/prior_work_register.json');status=read(root/'project-status.json');power=read(root/'docs/power-progress/data.json')
 known={p['id'] for p in prior['entries']};validate_goals(plan['goals'],known)
 task_review=check_task_review(read(folder/'NEXT_TASK_REVIEW.json'),known)
 ids=set();covered=set()
 for e in events['events']:
  if e['id'] in ids or e['kind'] not in KINDS:raise ValueError('Invalid timeline classification')
  ids.add(e['id']);covered.add(e['milestone_id']);e['sources']=[]
  for rel in e['source_paths']:
   p=(root/rel).resolve();p.relative_to(root)
   if not p.is_file():raise ValueError('Missing evidence: '+rel)
   e['sources'].append({'path':rel,'sha256':sha(p)})
  e['physical_fusion_demonstrated']=False;e['net_electricity_measured_MW']=None
 unclassified={m['id'] for m in status['milestones']}-covered
 if unclassified:raise ValueError('New milestones need an explicit classification: '+', '.join(sorted(unclassified)))
 ordered=sorted(events['events'],key=lambda e:e['date']);science=[e for e in ordered if e['kind'] in {'model_finding','unresolved_test'}];latest=science[-1]
 summary={'reviewed_through':plan['as_of'],'period_start':ordered[0]['date'],'period_end':plan['as_of'],'latest_scientific_event_id':latest['id'],'latest_scientific_date':latest['date'],'last_model_power_date':power['summary']['best_model_study_date'],'new_power_record_since_last_model_study':False,'physical_fusion':'Not demonstrated by this project','measured_net_electricity':'Not measured','hardware_date':None,'whole_reactor_qualified':False,'current_goal_id':'G1','project_stage':'Computer-based design studies; not a proven complete reactor','change_statement':'The latest current-budget diagnostic questions the fixed microwave-current requirement. Full plasma/current consistency and physical performance remain unqualified.','timeline_notice':'Historical dates are recorded study dates. The next-work timeline is a dependency order, not promised completion dates. No unattended research worker is implied.'}
 packet={'schema':'fusion.progress-roadmap.v1','summary':summary,'event_scope':events['scope'],'events':ordered,'goals':plan['goals'],'plan_notice':plan['schedule_notice'],'plan_status':plan['plan_status'],'prior_work':prior,'next_task_review':task_review,'existing_power_view':'../power-progress/','existing_particles_view':'../#watch','metric_policy':'No combined score or percentage of fusion solved. Marker rows classify evidence, not its scientific magnitude. Unknown or absent physical measurements are not plotted as zero.','new_scientific_runs':0,'source_hashes':{p.relative_to(root).as_posix():sha(p) for p in [folder/'EVENTS.json',folder/'GOALS.json',root/'project-status.json',root/'research/prior_work_register.json']},'base_commit':(folder/'BASE_COMMIT.txt').read_text().strip()}
 raw=(json.dumps(packet,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode('utf-8')
 for p in [root/'app/data/progress_roadmap.json',root/'docs/progress/data.json']:
  p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
 return {'events':len(ordered),'goals':len(plan['goals']),'prior_work_entries':len(prior['entries']),'latest_scientific_date':latest['date'],'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'new_scientific_runs':0}
if __name__=='__main__':print(json.dumps(build()))
