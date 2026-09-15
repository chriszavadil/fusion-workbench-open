"""Reuse the pinned published LiF benchmark without changing its physics. MIT."""
from pathlib import Path
import hashlib,importlib.util,json,os,subprocess,sys,time
import openmc,openmc_data_downloader as odd
HERE=Path(__file__).resolve().parent
A=json.loads((HERE/'ADMISSION.json').read_text());V=HERE/'upstream';P=V/'ofb_openmc_model.py'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True,allow_nan=False)+'\n')
assert sha(P)==A['model_sha256'];cfg=A['runs'][0]
spec=importlib.util.spec_from_file_location('pinned_reference',P);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
original=openmc.Model.run;argv=sys.argv[:]
try:
 openmc.Model.run=lambda self,**kw:self;sys.argv=[str(P),'-b',str(cfg['batches']),'-p',str(cfg['particles_per_batch']),'-s',str(cfg['threads'])];model=module.main()
finally:openmc.Model.run=original;sys.argv=argv
assert model.geometry.get_all_surfaces()[6].r==30.5
model.settings.seed=cfg['seed'];materials=openmc.Materials(list(model.geometry.get_all_materials().values()))
root=Path('/root/FusionResearch-neutronics-20260910');oldxs=root/'data/cross_sections.xml';library=openmc.data.DataLibrary.from_xml(oldxs)
needed_n={n for m in materials for n in m.get_nuclides()};needed_p={''.join(c for c in n if c.isalpha()) for n in needed_n};present_n={n for e in library if e['type']=='neutron' for n in e['materials']};present_p={n for e in library if e['type']=='photon' for n in e['materials']}
missing_n=sorted(needed_n-present_n);missing_p=sorted(needed_p-present_p);newdir=root/'lif-reference-data-20260914';newdir.mkdir(exist_ok=True)
if missing_n or missing_p:
 m=openmc.Material();
 for n in set(missing_n)|{next(n for n in needed_n if ''.join(c for c in n if c.isalpha())==e) for e in missing_p}:m.add_nuclide(n,1)
 m.set_density('g/cm3',1);odd.download_cross_section_data(openmc.Materials([m]),libraries=['ENDFB-8.0-NNDC'],destination=newdir,particles=['neutron','photon'],set_OPENMC_CROSS_SECTIONS=False,overwrite=False)
 library.extend(openmc.data.DataLibrary.from_xml(newdir/'cross_sections.xml'))
combined=openmc.data.DataLibrary();keys=set();files=[]
for entry in library:
 if not ((entry['type']=='neutron' and set(entry['materials'])&needed_n) or (entry['type']=='photon' and set(entry['materials'])&needed_p)):continue
 key=(entry['type'],tuple(entry['materials']))
 if key in keys:continue
 keys.add(key);p=Path(entry['path']);assert p.is_absolute() and p.is_file();combined.append(entry);files.append({'type':entry['type'],'materials':entry['materials'],'sha256':sha(p),'bytes':p.stat().st_size,'file':p.name})
xs=newdir/'benchmark_cross_sections.xml';combined.export_to_xml(xs)
out=HERE/'run';out.mkdir(exist_ok=False);model.export_to_xml(directory=out)
save(HERE/'DATA_MANIFEST.json',{'library':'ENDFB-8.0-NNDC','files':files,'new_nuclides':missing_n,'new_photoatomic_elements':missing_p,'old_library_changed':False})
save(HERE/'FROZEN_RUN.json',{'model_sha256':sha(P),'admission_sha256':sha(HERE/'ADMISSION.json'),'openmc':openmc.__version__,'geometry_sha256':sha(out/'geometry.xml'),'materials_sha256':sha(out/'materials.xml'),'settings_sha256':sha(out/'settings.xml'),'tallies_sha256':sha(out/'tallies.xml'),'before_execution':True})
env=os.environ.copy();env['OPENMC_CROSS_SECTIONS']=str(xs);env['OMP_NUM_THREADS']=str(cfg['threads']);start=time.monotonic()
with (out/'execution-private.log').open('w') as log:
 p=subprocess.run([str(Path(sys.executable).with_name('openmc')),'-s',str(cfg['threads'])],cwd=out,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,timeout=cfg['timeout_seconds'])
if p.returncode:raise RuntimeError('Transport failed; preserve raw log')
state=out/f"statepoint.{cfg['batches']}.h5";spectra={}
with openmc.StatePoint(state) as sp:
 for name in ['nspectrum','gspectrum']:
  tally=sp.get_tally(name=name);edges=tally.find_filter(openmc.EnergyFilter).bins
  spectra[name]={'energy_low_eV':edges[:,0].tolist(),'energy_high_eV':edges[:,1].tolist(),'current_per_source':tally.mean.ravel().tolist(),'statistical_standard_error':tally.std_dev.ravel().tolist()}
result={'schema':'fusion.lif-reference-result.v1','completed':True,'histories':cfg['batches']*cfg['particles_per_batch'],'elapsed_seconds':time.monotonic()-start,'statepoint_sha256':sha(state),'spectra':spectra,'physical_validation':False,'experiment_comparison_completed':False,'reactor_TBR':False};save(HERE/'RESULT.json',result);print(json.dumps({k:v for k,v in result.items() if k!='spectra'}),flush=True)
