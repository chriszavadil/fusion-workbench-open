"""Bounded source-boundary test and true OpenMC tracks/field export. Original MIT."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time
import numpy as np,openmc
from local_model import make
HERE=Path(__file__).resolve().parent
A=json.loads((HERE/'ADMISSION.json').read_text());F=json.loads((HERE/'FROZEN_INPUT.json').read_text())
def plain(o):
 if isinstance(o,dict):return {str(k):plain(v) for k,v in o.items()}
 if isinstance(o,(list,tuple)):return [plain(v) for v in o]
 if isinstance(o,np.generic):return o.item()
 return o
def save(p,o):p.write_text(json.dumps(plain(o),sort_keys=True,allow_nan=False)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def track_export(folder):
 result=[];primary=0;states_count=0
 for track in openmc.Tracks(folder/'tracks.h5'):
  primary+=1
  for j,(ptype,states) in enumerate(track.particle_tracks):
   if str(ptype).lower() not in ('neutron','photon'):continue
   pts=[]
   for s in states:
    r=s['r'];pts.append([float(r['x']),float(r['y']),float(r['z']),float(s['time']),float(s['E'])])
   if len(pts)>1:
    if not np.isfinite(pts).all() or np.any(np.diff(np.asarray(pts)[:,3])<0):raise ValueError('Invalid track states')
    states_count+=len(pts);result.append({'history':list(track.identifier),'particle':str(ptype).lower(),'secondary_index':j,'states':pts})
 return {'source_histories_recorded':primary,'state_count':states_count,'paths':result,'selection':'first16 primary histories in first batch, all neutron/photon descendants; not chosen after viewing','fields':['x_cm','y_cm','z_cm','time_s','energy_eV'],'statistical_histories_not_a_physical_source_pulse':True}
def execute(row):
 folder=HERE/'runs'/row['id'];folder.mkdir(parents=True);start=time.monotonic();model,meta=make(row['layout'],row['seed'])
 s=model.settings;s.batches=A['batches'];s.particles=A['particles'];s.tracks=A['track_ids']
 if row['source_law']=='normal':s.source[0].angle=openmc.stats.Monodirectional((1,0,0))
 mesh=openmc.RegularMesh();mesh.lower_left=[0,0,0];mesh.upper_right=[meta['dimensions_cm'][k] for k in ['x','y','z']];mesh.dimension=A['mesh_dimension']
 for name,score in [('volume_heating','heating'),('volume_tritons','H3-production')]:
  tally=openmc.Tally(name=name);tally.filters=[openmc.MeshFilter(mesh)];tally.scores=[score]
  if score=='H3-production':tally.filters.append(openmc.ParticleFilter(['neutron']))
  model.tallies.append(tally)
 save(folder/'GEOMETRY.json',meta);model.export_to_xml(directory=folder)
 xs=Path((HERE/'local_cross_sections_path.txt').read_text().strip());env=os.environ.copy();env['OPENMC_CROSS_SECTIONS']=str(xs);env['OMP_NUM_THREADS']=str(A['threads'])
 with (folder/'private-execution.log').open('w') as log:
  done=subprocess.run([str(Path(sys.executable).with_name('openmc')),'-s',str(A['threads'])],cwd=folder,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,timeout=A['timeout_each_seconds'])
 if done.returncode:raise RuntimeError('OpenMC failed; retain private log')
 state=folder/f"statepoint.{A['batches']}.h5"
 with openmc.StatePoint(state) as sp:
  tallies={}
  for name in ['total_tritons','total_heating','heat_by_cell','tritons_by_cell','volume_heating','volume_tritons']:
   t=sp.get_tally(name=name);tallies[name]={'mean':t.mean.ravel().tolist(),'std_dev':t.std_dev.ravel().tolist()}
  indices=[list(i) for i in mesh.indices];volume=float(np.prod(np.asarray(mesh.width)))
  if len(indices)!=len(tallies['volume_heating']['mean']):raise ValueError('Mesh shape mismatch')
 tracks=track_export(folder);save(folder/'TRACKS.json',tracks)
 out={'case':row,'histories':s.particles*s.batches,'completed':True,'seconds':time.monotonic()-start,'tallies':tallies,'mesh':{'dimension':A['mesh_dimension'],'lower_left_cm':list(mesh.lower_left),'upper_right_cm':list(mesh.upper_right),'indices_1based':indices,'voxel_cm3':volume},'statepoint_sha256':sha(state),'tracks_hdf5_sha256':sha(folder/'tracks.h5'),'tracks_json_sha256':sha(folder/'TRACKS.json'),'geometry_sha256':sha(folder/'GEOMETRY.json'),'primary_histories_recorded':tracks['source_histories_recorded'],'physical_validation':False}
 save(folder/'RESULT.json',out);return out
if __name__=='__main__':
 if (HERE/'runs').exists():raise RuntimeError('Refuse overwrite of existing runs')
 if sha(HERE/'local_model.py')!=A['prior_model_sha256'] or sha(HERE/'FROZEN_INPUT.json')!=A['prior_frozen_sha256']:raise ValueError('Inherited model changed')
 if not json.loads((HERE/'REFERENCE_RESULT.json').read_text())['computational_replay_passed']:raise ValueError('Reference not passed')
 openmc.config['cross_sections']=Path((HERE/'local_cross_sections_path.txt').read_text().strip())
 save(HERE/'RUN_MANIFEST.json',{'admission_sha256':sha(HERE/'ADMISSION.json'),'driver_sha256':sha(Path(__file__)),'material_sha256':sha(HERE/'materials_and_reference.py'),'openmc':openmc.__version__,'before_execution':True})
 status=[]
 for case in A['cases']:
  try:
   r=execute(case);status.append({'id':case['id'],'completed':True,'seconds':r['seconds']});print(json.dumps(status[-1]),flush=True)
  except Exception as e:
   import traceback;traceback.print_exc();status.append({'id':case['id'],'completed':False,'error_class':type(e).__name__});break
 save(HERE/'STATUS.json',{'cases':status,'all_completed':len(status)==4 and all(x['completed'] for x in status)})
