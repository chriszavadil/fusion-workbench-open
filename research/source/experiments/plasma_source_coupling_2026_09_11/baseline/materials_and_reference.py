"""Pinned reference capture and declared material definitions. Original code MIT."""
from pathlib import Path
import hashlib,importlib.util,json,sys
import openmc
import neutronics_material_maker as nmm
HERE=Path(__file__).resolve().parent
F=json.loads((HERE/'FROZEN_INPUT.json').read_text())

def reference():
 path=HERE/'ofb/models/oktavian/oktavian_al/openmc_model.py'
 if hashlib.sha256(path.read_bytes()).hexdigest()!=F['benchmark_model_sha256']:raise ValueError('Reference code changed')
 spec=importlib.util.spec_from_file_location('published_reference',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 original=openmc.Model.run;argv=sys.argv[:]
 try:
  openmc.Model.run=lambda self,**kw:self
  sys.argv=[str(path),'-b','40','-p','25000','-s','2'];model=m.main()
 finally:openmc.Model.run=original;sys.argv=argv
 return model

def substances():
 d=F['densities_g_cm3'];t=F['temperature_K']
 steel=nmm.Material.from_library('eurofer').openmc_material;steel.name='eurofer_recipe';steel.set_density('g/cm3',d['steel']);steel.temperature=t
 breeder=openmc.Material(name='Li4SiO4');breeder.add_element('Li',4,enrichment=F['li6_atom_enrichment_percent'],enrichment_target='Li6',enrichment_type='ao');breeder.add_element('Si',1);breeder.add_element('O',4);breeder.set_density('g/cm3',d['Li4SiO4']);breeder.temperature=t
 multiplier=openmc.Material(name='TiBe12');multiplier.add_element('Ti',1);multiplier.add_nuclide('Be9',12);multiplier.set_density('g/cm3',d['TiBe12']);multiplier.temperature=t
 cool=openmc.Material(name='pressurized_He4');cool.add_nuclide('He4',1);cool.set_density('g/cm3',d['coolant_He4']);cool.temperature=t
 purge=openmc.Material(name='purge_He4');purge.add_nuclide('He4',1);purge.set_density('g/cm3',d['purge_He4']);purge.temperature=t
 tungsten=openmc.Material(name='armour_W');tungsten.add_element('W',1);tungsten.set_density('g/cm3',d['tungsten']);tungsten.temperature=t
 return [breeder,multiplier,steel,cool,purge,tungsten]
