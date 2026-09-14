"""Export original Blender display meshes, not CAD or physical fields.
This little-endian format contains only allowlisted labels and numeric geometry.
"""
import bpy,sys,struct,json,hashlib,argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--workbench',type=Path,required=True);p.add_argument('--target',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);a.target.mkdir(parents=True,exist_ok=True)
rows=[]
for ident in ('r838','r900'):
 bpy.ops.wm.open_mainfile(filepath=str(a.workbench/'output'/f'{ident}.blend'))
 objects=sorted([o for o in bpy.context.scene.objects if o.type=='MESH' and o.get('component_id')],key=lambda o:o.name)
 assert len(objects)==34 and all(o.get('configuration_id')==ident for o in objects)
 data=bytearray(b'FWB1')+struct.pack('<I',len(objects));mins=[1e30]*3;maxs=[-1e30]*3
 def text(s):
  raw=s.encode('utf-8');assert len(raw)<256;data.extend(struct.pack('<I',len(raw)));data.extend(raw)
 for ob in objects:
  evaluated=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());m=evaluated.to_mesh();m.calc_loop_triangles()
  text(ob.name);text(ob['component_id']);data.extend(struct.pack('<BII',int(bool(ob.get('cutaway_segment'))),len(m.vertices),len(m.loop_triangles)*3))
  color=ob.active_material.diffuse_color if ob.active_material else (.7,.7,.7,1)
  data.extend(struct.pack('<4f',*color));normal_matrix=ob.matrix_world.to_3x3().inverted().transposed()
  for v in m.vertices:
   q=ob.matrix_world@v.co;xyz=(q.x*100,-q.y*100,q.z*100);data.extend(struct.pack('<3f',*xyz))
   for k in range(3):mins[k]=min(mins[k],xyz[k]);maxs[k]=max(maxs[k],xyz[k])
  for v in m.vertices:
   q=(normal_matrix@v.normal).normalized();data.extend(struct.pack('<3f',q.x,-q.y,q.z))
  for tri in m.loop_triangles:data.extend(struct.pack('<3I',tri.vertices[0],tri.vertices[2],tri.vertices[1]))
  evaluated.to_mesh_clear()
 dest=a.target/f'{ident}.fwm';dest.write_bytes(data);rows.append({'id':ident,'objects':len(objects),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'size_cm':[maxs[k]-mins[k] for k in range(3)],'scope':'display envelope; not engineering or physical validation'})
(a.target/'mesh_manifest.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows))
