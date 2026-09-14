"""Audited 3D field/trajectory projection and source-boundary contrast. MIT."""
from pathlib import Path
import json,math,hashlib
import numpy as np
HERE=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,o):p.write_text(json.dumps(o,sort_keys=True,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def contrast(a,sa,b,sb):
 d=a-b;s=math.hypot(sa,sb);return {'difference':d,'standard_error':s,'interval99':[d-2.5758293035489*s,d+2.5758293035489*s],'Monte_Carlo_error_only':True}
def run():
 admission=json.loads((HERE/'ADMISSION.json').read_text());cases=[];summary={};scale=0.;checks=[]
 for spec in admission['cases']:
  folder=HERE/'runs'/spec['id'];r=json.loads((folder/'RESULT.json').read_text());meta=json.loads((folder/'GEOMETRY.json').read_text());paths=json.loads((folder/'TRACKS.json').read_text())
  assert r['completed'] and r['histories']==400000 and r['tracks_json_sha256']==sha(folder/'TRACKS.json')
  assert r['geometry_sha256']==sha(folder/'GEOMETRY.json');assert paths['source_histories_recorded']==16
  dims=meta['dimensions_cm'];T=r['tallies'];voxel=r['mesh']['voxel_cm3'];expected=[[x+1,y+1,z+1] for z in range(16) for y in range(16) for x in range(24)]
  assert r['mesh']['indices_1based']==expected
  heating=np.asarray(T['volume_heating']['mean']);hs=np.asarray(T['volume_heating']['std_dev']);tritons=np.asarray(T['volume_tritons']['mean']);ts=np.asarray(T['volume_tritons']['std_dev'])
  assert heating.shape==(6144,) and np.isfinite(heating).all() and np.all(heating>=0) and np.all(hs>=0)
  heat_sum_error=float(heating.sum()-sum(T['heat_by_cell']['mean'][2:]));tri_sum_error=float(tritons.sum()-sum(T['tritons_by_cell']['mean'][2:]));assert abs(heat_sum_error)<.001 and abs(tri_sum_error)<1e-8
  safe_paths=[];max_time=0
  for path in paths['paths']:
   points=np.asarray(path['states']);assert points.shape[1]==5 and np.isfinite(points).all();assert np.all(np.diff(points[:,3])>=0) and np.all(points[:,3]>=0)
   assert np.all(points[:,:3]>=np.array([-2.3001,-.0001,-.0001])) and np.all(points[:,:3]<=np.array([dims['x']+.0001,dims['y']+.0001,dims['z']+.0001]))
   safe_paths.append({'primary':path['history'][2],'particle':path['particle'],'secondary_index':path['secondary_index'],'states':path['states']});max_time=max(max_time,float(points[-1,3]))
  h=heating/voxel;s=hs/voxel;scale=max(scale,float(h.max()));yieldv=T['total_tritons']['mean'][0];yse=T['total_tritons']['std_dev'][0]
  title=spec['source_law'].capitalize()+' incidence / '+spec['layout'].replace('headers_','')+' headers'
  c={'id':spec['id'],'title':title,'layout':spec['layout'],'source_law':spec['source_law'],'source_histories':r['histories'],'tritons_per_source':yieldv,'tritons_standard_error':yse,'heating_MeV_per_source':T['total_heating']['mean'][0]/1e6,'heating_standard_error_MeV':T['total_heating']['std_dev'][0]/1e6,'heating_density':h.tolist(),'heating_standard_error_density':s.tolist(),'tritons_by_voxel':tritons.tolist(),'tritons_by_voxel_standard_error':ts.tolist(),'paths':safe_paths,'max_track_time_s':max_time,'statepoint_sha256':r['statepoint_sha256'],'tracks_hdf5_sha256':r['tracks_hdf5_sha256'],'result_sha256':sha(folder/'RESULT.json'),'physical_validation':False}
  cases.append(c);summary[spec['id']]={k:v for k,v in c.items() if k not in ['paths','heating_density','heating_standard_error_density','tritons_by_voxel','tritons_by_voxel_standard_error']}
  good=(h>0)&(s<=.5*h);checks.append({'id':spec['id'],'heat_sum_error_eV_source':heat_sum_error,'triton_sum_error_source':tri_sum_error,'tracked_histories':16,'rendered_paths':len(safe_paths),'path_states':paths['state_count'],'mean_field_acceptable_voxels':int(good.sum()),'field_voxels':6144,'all_track_states_in_domain':True,'no_downsampling_or_synthetic_paths':True})
 contrasts={}
 for source in ['cosine','normal']:
  a=summary[source+'_front'];b=summary[source+'_rear'];d=contrast(a['tritons_per_source'],a['tritons_standard_error'],b['tritons_per_source'],b['tritons_standard_error']);d['percent_of_rear']=100*d['difference']/b['tritons_per_source'];contrasts[source]=d
 effect=contrast(contrasts['normal']['difference'],contrasts['normal']['standard_error'],contrasts['cosine']['difference'],contrasts['cosine']['standard_error'])
 conclusions={'source_direction_interaction':effect,'source_change_resolved_at99_MC':effect['interval99'][0]>0 or effect['interval99'][1]<0,'no_validated_source_law_selected':True,'full_reactor_TBR':False,'geometry_or_plant_output_updated':False}
 result={'schema':'fusion.source_direction_spatial_result.v1','date':'2026-09-10','cases':summary,'front_minus_rear':contrasts,'conclusions':conclusions,'projection_checks':checks,'admission_sha256':sha(HERE/'ADMISSION.json'),'physical_validation':False,'scope':'A source-law stress test of the inherited r838 local cell. Normal and diffuse incidence are contrasting hypotheses, not physical confidence limits.'};write(HERE/'KEY_RESULTS.json',result)
 packet={'schema':'fusion.transport-lab.v1','date':'2026-09-10','configuration':'r838 local module, not full reactor','dimensions_cm':[dims['x'],dims['y'],dims['z']],'header_outer_radius_cm':dims['ro'],'header_inner_radius_cm':dims['r'],'header_cap_cm':dims['t'],'mesh_dimension':[24,16,16],'common_heating_scale':scale,'field_units':'eV/cm^3 per incident neutron','mask_rule':'relative statistical standard error above0.5 or zero mean; no measurement uncertainty included','cases':cases,'physical_validation':False,'admission_sha256':result['admission_sha256'],'source_run_issues':'First cosine/rear tallies retained; tracks recovered in a one-batch companion with unchanged physics and seed after correcting the track API spelling.','visual_encodings':['Metres-to-centimetres already converted in solver geometry; coordinates are cm. Unreal flips Y to account for handedness.','Particle markers and brightness are illustrative; positions/time/energy are actual recorded histories.','Independent first16 histories share emission time for display; not a physical pulse or source intensity.','Time slider is logarithmic. Field colors use one common log(1+value) scale with actual displayed units.','Cutaway hides surfaces for inspection; it does not alter transport geometry.']};write(HERE/'transport_lab.json',packet)
 return result
if __name__=='__main__':print(json.dumps(run(),indent=2))
