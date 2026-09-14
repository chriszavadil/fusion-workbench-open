"""Project completed scoped neutron tallies into native/browser displays. MIT."""
from pathlib import Path
import hashlib,json,math
ROOT=Path(__file__).resolve().parents[1]
EXPERIMENT=ROOT/'research/source/experiments/header_neutron_placement_2026_09_10'

def build():
 raw=(EXPERIMENT/'KEY_RESULTS.json').read_bytes();r=json.loads(raw);f=json.loads((EXPERIMENT/'FROZEN_INPUT.json').read_text())
 if r['physical_validation'] or r['global_TBR_computed'] or r['new_plant_electrical_output_computed']:raise ValueError('Unexpected claim scope')
 rows=[];titles=['Uniform material inventory','Headers at rear','Headers near front — stress case']
 for layout,title in zip(f['layouts'],titles,strict=True):
  c=r['cases'][layout];fields=['tritons_per_incident_neutron','tritons_standard_error','heating_MeV_per_incident_neutron','heating_standard_error_MeV','source_histories','depth_tritons_per_incident_neutron']
  if c['source_histories']!=2000000 or len(c['depth_tritons_per_incident_neutron'])!=40:raise ValueError('Incomplete completed tally projection')
  if not all(math.isfinite(x) and x>=0 for x in c['depth_tritons_per_incident_neutron']):raise ValueError('Invalid profile')
  rows.append({'layout':layout,'title':title,**{k:c[k] for k in fields}})
 parts=[]
 for c in r['comparisons']:
  label='Rear headers' if c['layout']=='headers_rear' else 'Front headers'
  parts.append(f"{label}: {c['relative_percent']:+.2f}% local triton yield versus uniform; "+('flags the predeclared 2% geometry-sensitivity test.' if c['admitted_geometry_sensitivity_flag'] else 'does not flag the predeclared 2% geometry-sensitivity test.'))
 decision=' '.join(parts)+' This is a local design screen, not a certified reactor breeding margin.'
 h=f['header'];packet={'schema':'fusion.neutronics-view.v1','date':'2026-09-10','configuration_scope':'r838 local representative cell only','physical_validation':False,'module_depth_m':f['blanket_depth_m'],'module_width_m':f['module_volume_m3']/(f['blanket_depth_m']*(h['length_each_m']+2*h['wall_m'])),'header_outer_radius_m':h['outer_radius_m'],'header_inner_radius_m':h['inner_radius_m'],'cases':rows,'decision':decision,'source_results_sha256':hashlib.sha256(raw).hexdigest()}
 encoded=(json.dumps(packet,indent=2,sort_keys=True,ensure_ascii=False,allow_nan=False)+'\n').encode('utf-8')
 for dest in [ROOT/'app/data/neutronics.json',ROOT/'native/Content/WorkbenchData/neutronics.json']:
  dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(encoded)
 return {'sha256':hashlib.sha256(encoded).hexdigest(),'bytes':len(encoded),'decision':decision}
if __name__=='__main__':print(json.dumps(build()))
