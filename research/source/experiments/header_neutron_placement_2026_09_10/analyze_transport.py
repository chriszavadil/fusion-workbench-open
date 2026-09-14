"""Analyze the predeclared local header test without treating it as global TBR."""
from pathlib import Path
import hashlib,json,math,xml.etree.ElementTree as ET
import numpy as np
HERE=Path(__file__).resolve().parent

def combine(rows,key):
 means=np.array([r['tallies'][key]['mean'] for r in rows],float);sigma=np.array([r['tallies'][key]['std_dev'] for r in rows],float)
 if means.shape!=sigma.shape or means.shape[0]!=2 or not np.all(np.isfinite(means)):raise ValueError('Invalid repeated-run data')
 return means.mean(axis=0),np.sqrt(np.sum(sigma*sigma,axis=0))/len(rows)

def difference(a,sa,b,sb):
 delta=float(a-b);se=float(math.hypot(sa,sb));return {'difference':delta,'standard_error':se,'interval99':[delta-2.5758293035489004*se,delta+2.5758293035489004*se],'relative_percent':100*delta/b,'normal_interval_only_Monte_Carlo':True}

def run():
 F=json.loads((HERE/'FROZEN_INPUT.json').read_text());admission=json.loads((HERE/'RUN_ADMISSION.json').read_text());result={};raw=[]
 if not json.loads((HERE/'RUN_STATUS.json').read_text())['all_admitted_completed']:raise RuntimeError('Not all admitted runs completed')
 for row in admission['runs']:
  folder=HERE/'candidate_runs'/(row['layout']+'_'+str(row['seed']));r=json.loads((folder/'RESULT.json').read_text());meta=json.loads((folder/'model_metadata.json').read_text());assert r['completed'] and r['seed']==row['seed']
  ids=[e.attrib['id'] for e in ET.parse(folder/'tallies.xml').getroot().findall('filter')];assert len(ids)==len(set(ids))
  r['meta']=meta;raw.append(r)
 if len({r['seed'] for r in raw})!=len(raw):raise ValueError('Random streams are not distinct')
 for name in F['layouts']:
  rows=[r for r in raw if r['layout']==name];t,ts=combine(rows,'total_tritons');h,hs=combine(rows,'total_heating');li,lis=combine(rows,'lithium_tritons');depth,ds=combine(rows,'depth');heat_by,hb_std=combine(rows,'heat_by_cell');tri_by,tb_std=combine(rows,'tritons_by_cell');meta=rows[0]['meta']
  if abs(heat_by.sum()-h[0])>1e-7*abs(h[0]) or abs(tri_by.sum()-t[0])>1e-7*abs(t[0]):raise ValueError('Cell-to-total tally sum mismatch')
  sigma=math.hypot(rows[0]['tallies']['total_tritons']['std_dev'][0],rows[1]['tallies']['total_tritons']['std_dev'][0]);seedz=abs(rows[0]['tallies']['total_tritons']['mean'][0]-rows[1]['tallies']['total_tritons']['mean'][0])/sigma
  cells=[]
  for i,c in enumerate(meta['cells']):cells.append({**c,'heating_eV_per_incident_neutron':float(heat_by[i]),'heating_std_dev':float(hb_std[i]),'tritons_per_incident_neutron':float(tri_by[i]),'tritons_std_dev':float(tb_std[i]),'heating_eV_per_cm3_per_incident_neutron':float(heat_by[i]/c['volume_cm3'])})
  result[name]={'layout':name,'source_histories':sum(r['histories'] for r in rows),'tritons_per_incident_neutron':float(t[0]),'tritons_standard_error':float(ts[0]),'heating_MeV_per_incident_neutron':float(h[0]/1e6),'heating_standard_error_MeV':float(hs[0]/1e6),'lithium_tritons':{'Li6':float(li[0]),'Li7':float(li[1])},'seed_agreement_z':float(seedz),'depth_centres_cm':np.arange(1.25,100,2.5).tolist(),'depth_tritons_per_incident_neutron':depth.reshape(40,2)[:,1].tolist(),'depth_tritons_standard_error':ds.reshape(40,2)[:,1].tolist(),'cells':cells,'elapsed_s':sum(r['elapsed_s'] for r in rows),'physical_validation':False}
 comparisons=[];baseline=result['homogeneous']
 for name in F['layouts'][1:]:
  r=result[name];d=difference(r['tritons_per_incident_neutron'],r['tritons_standard_error'],baseline['tritons_per_incident_neutron'],baseline['tritons_standard_error']);d['layout']=name;d['admitted_geometry_sensitivity_flag']=abs(d['relative_percent'])>2 and (d['interval99'][0]>0 or d['interval99'][1]<0);d['heating_difference']=difference(r['heating_MeV_per_incident_neutron'],r['heating_standard_error_MeV'],baseline['heating_MeV_per_incident_neutron'],baseline['heating_standard_error_MeV']);comparisons.append(d)
 output={'schema':'fusion.local-header-transport-result.v1','date':'2026-09-10','configuration_scope':'r838 local representative cell only','cases':result,'comparisons':comparisons,'frozen_input_sha256':hashlib.sha256((HERE/'FROZEN_INPUT.json').read_bytes()).hexdigest(),'admission_sha256':hashlib.sha256((HERE/'RUN_ADMISSION.json').read_bytes()).hexdigest(),'reference_computational_replay':json.loads((HERE/'REFERENCE_RESULT.json').read_text()),'geometry_checks':{'equal_nuclide_inventory':True,'actual_sampled_point_check':True,'unique_tally_filters':True,'cell_to_total_tally_sums':True},'limits':F['limitations']+['Reported uncertainty is statistical Monte Carlo error only; does not include nuclear data, manufacturing or model-form uncertainty.','Tritons per neutron entering this local slab are not tritons per fusion neutron in a complete plant and are not usable recovered fuel.'],'physical_validation':False,'global_TBR_computed':False,'new_plant_electrical_output_computed':False}
 (HERE/'KEY_RESULTS.json').write_text(json.dumps(output,indent=2,sort_keys=True,allow_nan=False)+'\n');return output
if __name__=='__main__':
 r=run();print(json.dumps({'cases':{k:{n:v[n] for n in ['tritons_per_incident_neutron','tritons_standard_error','heating_MeV_per_incident_neutron','seed_agreement_z']} for k,v in r['cases'].items()},'comparisons':r['comparisons']},indent=2))
