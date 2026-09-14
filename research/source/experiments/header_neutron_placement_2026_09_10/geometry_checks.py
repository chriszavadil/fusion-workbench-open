"""Pre-transport CSG, material inventory and data-temperature checks. MIT."""
from pathlib import Path
import json,math
import numpy as np,openmc,h5py
from materials_and_reference import HERE,F
from local_model import make,dimensions
xs=Path((HERE/'local_cross_sections_path.txt').read_text().strip());openmc.config['cross_sections']=xs
results=[];base=None
for layout in F['layouts']:
 model,m=make(layout,F['seeds'][0]);a=dimensions();inventory=m['atom_inventory_barn_cm']
 if base is None:base=inventory
 difference=max(abs(inventory[k]-base[k])/max(base[k],1e-30) for k in base)
 if difference>1e-12:raise ValueError('Nuclide inventory changed across layouts')
 rng=np.random.default_rng(99313);hits={c.id:0 for c in model.geometry.get_all_cells().values()}
 # Sampling deliberately tests bulk and known interfaces without claiming exact overlap proof.
 for point in rng.uniform([0,0,0],[a['x'],a['y'],a['z']],(10000,3)):
  found=model.geometry.find(point)
  if not found or not isinstance(found[-1],openmc.Cell):raise ValueError('Geometry void/unassigned point')
  hits[found[-1].id]+=1
 for cell in model.geometry.get_all_cells().values():
  if 'header' in cell.name and hits[cell.id]==0:raise ValueError('Explicit header not sampled')
 expected=F['header']['header_coolant_m3']/F['module_count']*1e6
 if abs(a['cool']-expected)>1e-6:raise ValueError('Header coolant volume differs from archived design')
 expected_steel=(F['header']['shell_steel_m3']+F['header']['cap_volume_allowance_m3'])/F['module_count']*1e6
 if abs(a['steel']-expected_steel)>1e-6:raise ValueError('Cap/shell volume differs from archived design')
 out=HERE/'geometry'/layout;out.mkdir(parents=True,exist_ok=True);model.export_to_xml(directory=out);(out/'MODEL.json').write_text(json.dumps(m,indent=2)+'\n')
 results.append({'layout':layout,'nuclide_inventory_max_relative_difference':difference,'points_checked':10000,'cell_hits':hits,'volume_sum_cm3':sum(c.volume for c in model.geometry.get_all_cells().values()),'passed':True})
temps={}
for row in openmc.data.DataLibrary.from_xml(xs):
 if row['type']!='neutron':continue
 with h5py.File(row['path'],'r') as h:
  for nu in row['materials']:
   ts=[float(v[()])/openmc.data.K_BOLTZMANN for v in h[nu]['kTs'].values()];temps[nu]=ts
   if min(ts)>F['temperature_K'] or max(ts)<F['temperature_K']:raise ValueError('Temperature not bracketed: '+nu)
result={'schema':'fusion.local-transport-preflight.v1','cases':results,'nuclear_temperatures_K':temps,'temperature_bracketed':True,'equal_inventory_verified':True,'physical_geometry_validated':False}
(HERE/'GEOMETRY_CHECKS.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'preflight_passed':True,'layouts':len(results),'data_temperatures_checked':len(temps)}),flush=True)
