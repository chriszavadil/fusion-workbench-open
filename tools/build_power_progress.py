"""Build an auditable power history without treating simulated MW as measured MW. MIT."""
from pathlib import Path
import hashlib,json,math,re
ROOT=Path(__file__).resolve().parents[1]
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def select_best(rows,metric='average_net_MW'):
 eligible=[r for r in rows if r['eligible_for_model_best'] and r['numerically_converged'] is True and r[metric] is not None]
 return max(eligible,key=lambda r:r[metric]) if eligible else None

def build(root=ROOT):
 cat=read(root/'app/data/catalog.json');exp=root/'research/source/experiments/plant_current_drive_2026_09_14';configs=read(exp/'RECORDED_CONFIGURATIONS.json');study=read(root/'docs/plant-decision/data.json');rows=[]
 def add(id,date,label,avg,flat,status,why,source,eligible=False,converged=None,**extra):
  row={'id':id,'study_date':date,'date_semantics':'Dated study record, not invented run timestamp','order':len(rows)+1,'label':label,'average_net_MW':avg,'flat_top_net_MW':flat,'status':status,'qualification':why,'source_path':source,'source_sha256':sha(root/source),'eligible_for_model_best':eligible,'numerically_converged':converged,'evidence':'model_or_screen','measured_net_electric_MW':None,'physical_qualification':False};row.update(extra);rows.append(row);return row
 lifecycle='research/reports/results/FULL_PROCESS_LIFECYCLE_2026-09-07.md';retired='research/reports/results/INTEGRATED_CANDIDATE_PATH_2026-09-07.md'
 add('retired-screen','2026-09-07','Retired combined screen',406.53,None,'superseded','Cross-study screen with changed efficiency/dwell/pumping. Not a coupled whole-plant result; excluded from the best-model calculation.',retired,precision='Rounded value from preserved report')
 add('baseline-no-fatigue','2026-09-07','Original baseline',216.8187594559644,None,'incomplete_requirements','No solenoid-fatigue constraint; not eligible under the later lifetime scope.',lifecycle,converged=True)
 add('native-20k','2026-09-07','Native 20k-cycle screen',214.1844,None,'failed_crosscheck','Numerically converged in native fatigue calculation; independent adaptive cycle count falls short of20k.',lifecycle,converged=True,precision='Report-rounded MW')
 add('adaptive-20k','2026-09-07','Adaptive 20k-cycle screen',214.1417,None,'limited_lifetime_scope','Meets implemented20k criterion, not the later30-year duty requirement.',lifecycle,converged=True,precision='Report-rounded MW')
 for c in cat['configurations']:
  m=c['metrics'];row=add(c['id'],'2026-09-07',c['id']+' maintained model reference',m['conditional_average_net_MW'],m['flat_top_net_MW'],'reference_model','Maintained numerical reference only; confinement, fuel, materials and availability remain physically unqualified.','app/data/catalog.json',True,True,reference_configuration=True,model_output_sha256=c['provenance']['artifact_sha256'],pulse_energy_kWh=m['pulse_energy_kWh'],cycle_s=m['cycle_s'],availability=c['assumptions']['availability'],assumptions=c['assumptions'])
 for id in ['steady200','steady350']:
  rel=f'research/source/experiments/plant_current_drive_2026_09_14/runs/{id}/RESULT.json';run=read(root/rel);assert not run['numerically_converged']
  add(id,'2026-09-14',id+' attempted solve',None,None,'not_converged','No feasible scored power; failed output fields are not power predictions. Nonconvergence is not proof of impossibility.',rel,False,False,ifail=run['metrics']['ifail'])
 for id,label in [('pulsed200allocated','Zero heat-only reserve bound'),('pulsed200reserve30','30 MW reserve / minimum radius'),('pulsedFixedR75','Fixed-radius power control'),('pulsedFixedR30','Fixed-radius power alternative')]:
  c=configs[id];m=c['metrics'];rel=f'research/source/experiments/plant_current_drive_2026_09_14/runs/{id}/RESULT.json';run=read(root/rel)
  optimistic=id=='pulsed200allocated';why='Optimistic zero-reserve limit; insufficient control capability is unresolved. Excluded from model-record selection.' if optimistic else 'Converged systems model, not physical qualification. EC deposition/current profile, remaining control capacity, matching thermal/fuel geometry and availability are unresolved.'
  add(id,'2026-09-14',label,m['conditional_average_net_MW'],m['flat_top_net_MW'],'optimistic_bound' if optimistic else 'exploratory_model',why,rel,not optimistic,run['numerically_converged'],model_output_sha256=c['provenance']['artifact_sha256'],pulse_energy_kWh=m['pulse_energy_kWh'],cycle_s=m['cycle_s'],availability=.8,heat_only_reserve_MW=run['metrics']['p_hcd_primary_extra_heat_mw'],objective='minimize_radius' if id in ['pulsed200allocated','pulsed200reserve30'] else 'maximize_flat_top_net_at_fixed_major_radius')
 for r in rows:
  if 'pulse_energy_kWh' in r:
   actual=r['pulse_energy_kWh']*3.6/r['cycle_s']*r['availability']
   if abs(actual-r['average_net_MW'])>1e-7:raise ValueError('Power/energy/time mismatch: '+r['id'])
  if r['average_net_MW'] is not None and (not math.isfinite(r['average_net_MW']) or r['average_net_MW']<0):raise ValueError('Invalid history value')
 world=read(root/'research/power_progress/WORLD_MILESTONES.json')
 for r in world['records']:
  if r['net_electric_MW'] is not None or r['evidence']!='reported_physical_measurement':raise ValueError('World metric boundary crossed')
  r['derived_mean_fusion_power_MW']=[{'MW':r['value']/d['seconds'],'seconds':d['seconds'],'source_id':d['source_id'],'kind':'derived_interval_mean_not_peak'} for d in r.get('duration_reports',[]) if r['metric_kind']=='fusion_energy_per_pulse']
  laser=r.get('laser_energy_on_target_MJ');r['derived_target_gain_from_rounded_values']=r['value']/laser if laser else None
 best=select_best(rows);reference=max([r for r in rows if r.get('reference_configuration')],key=lambda r:r['average_net_MW']);control=next(r for r in rows if r['id']=='pulsedFixedR75')
 summary={'best_model_id':best['id'],'best_average_net_MW':best['average_net_MW'],'same_case_flat_top_net_MW':best['flat_top_net_MW'],'reference_model_id':reference['id'],'reference_average_net_MW':reference['average_net_MW'],'controlled_comparison_id':control['id'],'controlled_average_delta_MW':best['average_net_MW']-control['average_net_MW'],'controlled_average_delta_percent':100*(best['average_net_MW']/control['average_net_MW']-1),'physical_net_electric_MW':None,'physical_result_label':'Not measured','best_model_physical_status':'Unqualified design lead; not an experimental record','best_model_study_date':best['study_date']}
 events=[{'date':'2026-09-14','title':'Conditional power lead recorded','detail':'Same-major-radius control and alternative; increased model output requires unqualified extra current-drive credit and higher thermal loads.','output_changed':True,'source_path':'research/reports/results/PLANT_CURRENT_DRIVE_DECISION_2026-09-14.md'}, {'date':'2026-09-16','title':'Equilibrium compatibility remains unresolved','detail':'Four fixed-boundary constructions match current/pressure energy but not the assumed q95. No new candidate power solve or measured electricity; the historical model result remains visible, not promoted.','output_changed':False,'source_path':'research/reports/results/EC_EQUILIBRIUM_INTERFACE_2026-09-16.md'}]
 packet={'schema':'fusion.power-progress.v1','updated_date':'2026-09-16','project':'Fusion Workbench','summary':summary,'history':rows,'qualification_events':events,'world':world,'scope':'Power-focused evidence dashboard. Review chronology, not equal-condition longitudinal experiments. Only the labeled fixed-radius pair is the controlled allocation comparison.','metric_definition':'Conditional average net electric MW = pulse net electric energy(kWh) *3.6 / cycle duration(s) *assumed availability. Includes recorded cycle/dwell loads, excludes additional unscheduled-outage energy.','ranking_scope':'Largest numerically converged whole-plant conditional average among the maintained-lifetime-scope and exploratory records included here. Excludes superseded screens, failed solves and explicitly inadequate-reserve bounds. This is not physical qualification.','no_new_scientific_runs':True,'snapshot_not_live_monitoring':True,'source_base_commit':(root/'research/power_progress/BASE_COMMIT.txt').read_text().strip(),'original_methods_credited':'UKAEA PROCESS and its original contributors; generic tokamak input by James Morris. Physical measurements belong to PPPL, UKAEA/EUROfusion and LLNL collaborators.'}
 raw=(json.dumps(packet,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode('utf-8')
 for p in [root/'app/data/power_progress.json',root/'docs/power-progress/data.json']:
  p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
 return {'history_records':len(rows),'physical_milestones':len(world['records']),'best_average_net_MW':summary['best_average_net_MW'],'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'new_scientific_runs':0}
if __name__=='__main__':print(json.dumps(build()))
