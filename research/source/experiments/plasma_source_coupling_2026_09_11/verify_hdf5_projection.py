"""Read-only independent extraction of source-coupled statepoint/track files."""
from pathlib import Path
import hashlib,json
import numpy as np
import openmc
HERE=Path(__file__).resolve().parent
checks=[]
for folder in sorted((HERE/'runs').iterdir()):
 r=json.loads((folder/'RESULT.json').read_text());p=json.loads((folder/'TRACKS.json').read_text())
 assert hashlib.sha256((folder/'statepoint.20.h5').read_bytes()).hexdigest()==r['statepoint_sha256']
 assert hashlib.sha256((folder/'tracks.h5').read_bytes()).hexdigest()==r['tracks_sha256']
 with openmc.StatePoint(folder/'statepoint.20.h5') as sp:
  for name,value in r['tallies'].items():
   t=sp.get_tally(name=name);assert np.array_equal(t.mean.ravel(),value['mean']);assert np.array_equal(t.std_dev.ravel(),value['std_dev'])
 paths=[];primary=0
 for record in openmc.Tracks(folder/'tracks.h5'):
  primary+=1
  for index,(particle,states) in enumerate(record.particle_tracks):
   if str(particle).lower() not in ('neutron','photon') or len(states)<2:continue
   q=[[float(s['r'][k]) for k in ('x','y','z')]+[float(s['time']),float(s['E'])] for s in states]
   paths.append({'primary':int(record.identifier[2]),'particle':str(particle).lower(),'secondary_index':index,'states':q})
 assert paths==p['paths'] and primary==p['source_histories_recorded']==16
 checks.append({'run':folder.name,'primary_histories':primary,'recorded_paths':len(paths),'tally_values_and_errors_exact':True,'recorded_states_exact':True,'passed':True})
report={'passed':all(c['passed'] for c in checks),'checks':checks,'fresh_transport_run':False,'physical_validation':False}
(HERE/'HDF5_PROJECTION_CHECK.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
