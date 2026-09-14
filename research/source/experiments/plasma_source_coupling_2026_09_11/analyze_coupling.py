"""Aggregate the frozen source-coupled experiment; no physical-accuracy claim. MIT."""
from pathlib import Path
import json,hashlib,math
import numpy as np
HERE=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def combine(rows,name):
 m=np.array([r['tallies'][name]['mean'] for r in rows]);s=np.array([r['tallies'][name]['std_dev'] for r in rows]);return m.mean(axis=0),np.sqrt((s*s).sum(axis=0))/2

def run():
 assert json.loads((HERE/'STATUS.json').read_text())['all_completed'];source=json.loads((HERE/'SOURCE_RESULT.json').read_text());results={};visual=[]
 for layout in ['headers_rear','headers_front']:
  folders=[HERE/'runs'/(layout+'_bank'+str(b)) for b in [0,1]];rows=[json.loads((p/'RESULT.json').read_text()) for p in folders];meta=json.loads((folders[0]/'GEOMETRY.json').read_text());tracks=json.loads((folders[0]/'TRACKS.json').read_text());assert all(r['completed'] and r['histories']==200000 for r in rows)
  total,tse=combine(rows,'total_tritons');heat,hse=combine(rows,'total_heating');field,fse=combine(rows,'volume_heating');tri,trse=combine(rows,'volume_tritons');by,bse=combine(rows,'heat_by_cell');ty,tyse=combine(rows,'tritons_by_cell')
  assert abs(by.sum()-heat[0])<1e-4 and abs(ty.sum()-total[0])<1e-9 and abs(field.sum()-by[2:].sum())<1e-4 and abs(tri.sum()-ty[2:].sum())<1e-9
  pairse=math.hypot(rows[0]['tallies']['total_tritons']['std_dev'][0],rows[1]['tallies']['total_tritons']['std_dev'][0]);pairz=abs(rows[0]['tallies']['total_tritons']['mean'][0]-rows[1]['tallies']['total_tritons']['mean'][0])/pairse
  coef=source['normalized_patch_neutrons_s']*1.602176634e-19;cells=[{**cell,'heat_MW':float(by[i]*coef/1e6),'heat_MW_conditional_MC_se':float(bse[i]*coef/1e6)} for i,cell in enumerate(meta['cells'])]
  r={'layout':layout,'tritons_per_incident_neutron':float(total[0]),'tritons_standard_error':float(tse[0]),'deposited_MeV_per_incident_neutron':float(heat[0]/1e6),'heating_standard_error_MeV':float(hse[0]/1e6),'conditional_module_nuclear_heat_MW':float(heat[0]*coef/1e6),'between_bank_difference_z':float(pairz),'source_histories':400000,'cells':cells,'physical_validation':False};results[layout]=r
  paths=tracks['paths'];tmax=max(s[3] for p in paths for s in p['states']);voxel=rows[0]['voxel_cm3']
  visual.append({'id':'profile_'+layout,'title':'Plasma-linked direct source / '+layout.replace('headers_','')+' headers','layout':layout,'source_law':'r838 profile + parameterized torus, direct view only','source_histories':400000,'tritons_per_source':r['tritons_per_incident_neutron'],'tritons_standard_error':r['tritons_standard_error'],'heating_MeV_per_source':r['deposited_MeV_per_incident_neutron'],'heating_standard_error_MeV':r['heating_standard_error_MeV'],'heating_density':(field/voxel).tolist(),'heating_standard_error_density':(fse/voxel).tolist(),'tritons_by_voxel':tri.tolist(),'tritons_by_voxel_standard_error':trse.tolist(),'paths':paths,'max_track_time_s':tmax,'statepoint_sha256':rows[0]['statepoint_sha256'],'statepoint_replicate_sha256':rows[1]['statepoint_sha256'],'incident_neutrons_s':source['normalized_patch_neutrons_s'],'physical_validation':False,'tallies_averaged_over_banks':2,'paths_bank':0})
  for p in folders:
   row=json.loads((p/'RESULT.json').read_text());assert row['geometry_sha256']==sha(p/'GEOMETRY.json') and row['json_tracks_sha256']==sha(p/'TRACKS.json')
 a=results['headers_front'];b=results['headers_rear'];d=a['tritons_per_incident_neutron']-b['tritons_per_incident_neutron'];se=math.hypot(a['tritons_standard_error'],b['tritons_standard_error'])
 comparison={'front_minus_rear_tritons':d,'standard_error':se,'interval99':[d-2.5758293035489*se,d+2.5758293035489*se],'percent_of_rear':100*d/b['tritons_per_incident_neutron'],'conditional_MC_error_only':True,'source_geometry_and_nuclear_data_uncertainty_excluded':True}
 result={'schema':'fusion.candidate-source-coupling-result.v1','date':'2026-09-11','cases':results,'comparison':comparison,'source_summary':{k:source[k] for k in ['patch_fraction','patch_fraction_scramble_se','normalized_patch_neutrons_s','normalization_DT_rate_s','parameterized_volume_difference_percent','source_shape_total_rate_ratio_to_PROCESS']},'angular_means':[b['mean_mu'] for b in source['banks']],'admission_sha256':sha(HERE/'ADMISSION.json'),'source_result_sha256':sha(HERE/'SOURCE_RESULT.json'),'source_power_geometry_not_reoptimized':True,'experimental_validation':False,'whole_reactor_TBR':False,'extra_electricity':False}
 (HERE/'KEY_RESULTS.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n');(HERE/'NEW_CASES.json').write_text(json.dumps(visual,indent=2,allow_nan=False)+'\n');return result
if __name__=='__main__':print(json.dumps(run(),indent=2))
