"""Lossless canonical source-site export. Renderer selection is separate. MIT."""
from pathlib import Path
import hashlib,json,struct
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
EXP=ROOT/'research/source/experiments/plasma_source_coupling_2026_09_11'
RECORD=struct.Struct('<QII14d');HEADER=struct.Struct('<IIQ');MAGIC=0x53574331

def load_bank(path):
 with np.load(path) as src:return {key:src[key] for key in src.files}

def export():
 packet=json.loads((ROOT/'app/data/transport_lab.json').read_text(encoding='utf-8'))
 S=json.loads((EXP/'SOURCE_RESULT.json').read_text());P=json.loads((EXP/'PLASMA_SOURCE.json').read_text());F=json.loads((EXP/'LOCAL_INPUT.json').read_text());R=json.loads((EXP/'KEY_RESULTS.json').read_text())
 banks=[load_bank(EXP/'source_banks'/f'bank{i}.npz') for i in range(len(S['banks']))];count=sum(len(b['r']) for b in banks)
 raw=bytearray(HEADER.pack(MAGIC,1,count));manifest=[]
 for bank_index,b in enumerate(banks):
  size=len(b['r']);probability=1/len(banks)/size
  for i in range(size):
   raw.extend(RECORD.pack((bank_index<<32)|i,bank_index,i,1.,probability,*b['birth'][i],*b['target'][i],*b['r'][i],*b['u'][i]))
  manifest.append({'bank_id':bank_index,'particles':size,'statistical_weight_per_particle':1.,'joint_selection_probability_per_particle':probability,'npz_sha256':hashlib.sha256((EXP/'source_banks'/f'bank{bank_index}.npz').read_bytes()).hexdigest()})
 context=packet['source_context'];context.pop('rays',None)
 context.update(authoritative_source_result=S,authoritative_plasma_profiles=P,authoritative_local_input=F,authoritative_coupled_result=R,bank_manifest=manifest,source_bank_file='source_context.bin',source_bank_sha256=hashlib.sha256(raw).hexdigest(),source_particle_count=count,source_record_format='<QII14d',source_record_fields=['stable_id','bank_id','particle_id','statistical_weight','joint_selection_probability','birth_xyz_cm','target_xyz_cm','local_position_xyz_cm','local_direction_xyz'],visualization={'default_source_site_budget':64,'max_source_site_budget':4096,'selection':'Display-only evenly spaced indices across the complete equal-weight source banks. Full particles, weights and source observations remain stored. No analysis uses the display subset.'})
 for case in packet['cases']:
  if not case['id'].startswith('profile_'):continue
  case['authoritative_track_banks']=[];case['authoritative_run_records']=[]
  for bank in range(len(banks)):
   folder=EXP/'runs'/f"{case['layout']}_bank{bank}";case['authoritative_run_records'].append({'bank_id':bank,'result':json.loads((folder/'RESULT.json').read_text()),'geometry':json.loads((folder/'GEOMETRY.json').read_text())});tracks=json.loads((folder/'TRACKS.json').read_text());case['authoritative_track_banks'].append({'bank_id':bank,'source_path':folder.relative_to(ROOT).as_posix()+'/TRACKS.json','sha256':hashlib.sha256((folder/'TRACKS.json').read_bytes()).hexdigest(),'data':tracks})
 data=(json.dumps(packet,indent=2,allow_nan=False)+'\n').encode('utf-8')
 for directory in [ROOT/'app/data',ROOT/'native/Content/WorkbenchData']:
  (directory/'source_context.bin').write_bytes(raw);(directory/'transport_lab.json').write_bytes(data)
 return {'source_particles':count,'source_banks':len(banks),'canonical_binary_bytes':len(raw),'visualization_packet_bytes':len(data),'source_bank_sha256':hashlib.sha256(raw).hexdigest(),'export_truncated':False}
if __name__=='__main__':print(json.dumps(export()))
