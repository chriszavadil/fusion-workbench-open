"""Candidate-linked local representative CSG, not whole-reactor CAD/TBR. MIT."""
from pathlib import Path
import math,json
import numpy as np,openmc
from materials_and_reference import HERE,F,substances

def dimensions():
 h=F['header'];r=h['inner_radius_m'];ro=h['outer_radius_m'];t=h['wall_m'];L=h['length_each_m'];z=L+2*t;x=F['blanket_depth_m'];V=F['module_volume_m3'];y=V/(x*z)
 return {'x':x*100,'y':y*100,'z':z*100,'r':r*100,'ro':ro*100,'t':t*100,'L':L*100,'V':V*1e6,'cool':3*math.pi*r*r*L*1e6,'steel':3*(math.pi*(ro*ro-r*r)*L+2*math.pi*ro*ro*t)*1e6}

def make(layout,seed,particles=None):
 if layout not in F['layouts']:raise ValueError('Unadmitted layout')
 openmc.reset_auto_ids();a=dimensions();g=F['fractions'];fractions=np.array([g['f_vol_blkt_li4sio4'],g['f_vol_blkt_tibe12'],g['f_vol_blkt_steel'],g['vfcblkt'],g['vfpblkt']]);assert abs(sum(fractions)-1)<1e-12
 mats=substances();breeder,multiplier,steel,cool,purge,tungsten=mats;temperature=F['temperature_K']
 homogeneous=openmc.Material.mix_materials(mats[:5],fractions.tolist(),percent_type='vo',name='blanket_homogeneous');homogeneous.temperature=temperature
 fwfrac=F['first_wall_coolant_fraction'];fwmat=openmc.Material.mix_materials([steel,cool],[1-fwfrac,fwfrac],percent_type='vo',name='first_wall_mixed');fwmat.temperature=temperature
 residual_vol=a['V']-a['cool']-a['steel'];vols=fractions*a['V'];vols[2]-=a['steel'];vols[3]-=a['cool'];assert np.all(vols>=0)
 residual=openmc.Material.mix_materials(mats[:5],(vols/residual_vol).tolist(),percent_type='vo',name='blanket_residual');residual.temperature=temperature
 xa=-100*(F['armour_m']+F['first_wall_m']);xf=-100*F['first_wall_m'];x0=openmc.XPlane(x0=0);xb=openmc.XPlane(x0=a['x'],boundary_type='vacuum');front=openmc.XPlane(x0=xa,boundary_type='vacuum');wall=openmc.XPlane(x0=xf)
 y0=openmc.YPlane(y0=0,boundary_type='reflective');y1=openmc.YPlane(y0=a['y'],boundary_type='reflective');z0=openmc.ZPlane(z0=0,boundary_type='reflective');z1=openmc.ZPlane(z0=a['z'],boundary_type='reflective');span=+y0&-y1&+z0&-z1
 cells=[openmc.Cell(name='armour',fill=tungsten,region=+front&-wall&span),openmc.Cell(name='first_wall',fill=fwmat,region=+wall&-x0&span)];cells[0].volume=(xf-xa)*a['y']*a['z'];cells[1].volume=-xf*a['y']*a['z']
 region=+x0&-xb&span;headercells=[]
 if layout=='homogeneous':c=openmc.Cell(name='blanket',fill=homogeneous,region=region);c.volume=a['V'];cells.append(c)
 else:
  inside=openmc.ZPlane(z0=a['t']);top=openmc.ZPlane(z0=a['z']-a['t']);xc=a['ro']+1e-6 if layout=='headers_front' else a['x']-a['ro']-1e-6
  for i,yy in enumerate([a['y']/6,a['y']/2,5*a['y']/6]):
   outer=openmc.ZCylinder(x0=xc,y0=yy,r=a['ro']);inner=openmc.ZCylinder(x0=xc,y0=yy,r=a['r']);whole=-outer&span&+x0&-xb;fluid=-inner&+inside&-top&whole;shell=whole&~fluid
   cf=openmc.Cell(name=f'header_{i}_coolant',fill=cool,region=fluid);cf.volume=a['cool']/3
   cs=openmc.Cell(name=f'header_{i}_steel_caps',fill=steel,region=shell);cs.volume=a['steel']/3
   cells.extend([cf,cs]);headercells.extend([cf,cs]);region=region&~whole
  c=openmc.Cell(name='blanket_residual',fill=residual,region=region);c.volume=residual_vol;cells.append(c)
 model=openmc.Model(geometry=openmc.Geometry(cells));model.materials=openmc.Materials(list(model.geometry.get_all_materials().values()))
 source=openmc.IndependentSource(space=openmc.stats.CartesianIndependent(openmc.stats.Discrete([xa+1e-7],[1]),openmc.stats.Uniform(0,a['y']),openmc.stats.Uniform(0,a['z'])),angle=openmc.stats.PolarAzimuthal(mu=openmc.stats.PowerLaw(0,1,1),phi=openmc.stats.Uniform(0,2*math.pi),reference_uvw=(1,0,0)),energy=openmc.stats.Discrete([F['source_energy_eV']],[1]))
 settings=openmc.Settings();settings.run_mode='fixed source';settings.photon_transport=True;settings.source=source;settings.seed=seed;settings.batches=F['batches'];settings.particles=particles or F['particles_per_batch'];settings.temperature={'method':'interpolation'};settings.output={'tallies':False};model.settings=settings
 allcells=openmc.CellFilter(cells)
 tallies=[]
 for name,score,filters in [('heat_by_cell','heating',[allcells]),('tritons_by_cell','H3-production',[allcells,openmc.ParticleFilter(['neutron'])])]:
  t=openmc.Tally(name=name);t.filters=filters;t.scores=[score];tallies.append(t)
 li=openmc.Tally(name='lithium_tritons');li.scores=['H3-production'];li.nuclides=['Li6','Li7'];li.filters=[openmc.ParticleFilter(['neutron'])];tallies.append(li)
 for name,surface in [('front_leakage',front),('back_leakage',xb)]:
  t=openmc.Tally(name=name);t.filters=[openmc.SurfaceFilter(surface),openmc.ParticleFilter(['neutron','photon'])];t.scores=['current'];tallies.append(t)
 mesh=openmc.RegularMesh();mesh.lower_left=[0,0,0];mesh.upper_right=[a['x'],a['y'],a['z']];mesh.dimension=[40,1,1]
 mt=openmc.Tally(name='depth');mt.filters=[openmc.MeshFilter(mesh),openmc.ParticleFilter(['neutron'])];mt.scores=['flux','H3-production'];tallies.append(mt)
 gh=openmc.Tally(name='total_heating');gh.scores=['heating'];tallies.append(gh)
 gt=openmc.Tally(name='total_tritons');gt.scores=['H3-production'];gt.filters=[openmc.ParticleFilter(['neutron'])];tallies.append(gt)
 model.tallies=openmc.Tallies(tallies)
 inventory={}
 for cell in cells:
  for nu,density in cell.fill.get_nuclide_atom_densities().items():inventory[nu]=inventory.get(nu,0)+density*cell.volume
 meta={'layout':layout,'seed':seed,'dimensions_cm':a,'cells':[{'id':c.id,'name':c.name,'volume_cm3':c.volume,'material':c.fill.name} for c in cells],'atom_inventory_barn_cm':inventory,'cold_geometric_envelope_not_full_reactor':True,'neutron_source':F['source_angular_law'],'source_histories':settings.batches*settings.particles,'physical_validation':False}
 return model,meta
