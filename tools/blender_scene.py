"""Build auditable display envelopes, not engineering CAD or transport geometry.

Run with Blender --background --factory-startup --python this_file.py -- --root PATH
The source dimensions come from the reviewed catalog. Surfaces between native
build dimensions and TF-coil shapes are explicitly schematic. No stress, heat,
plasma dynamics, or neutron flux is inferred from mesh appearance.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import bpy
from mathutils import Vector

TAU=2*math.pi

def material(name,color,metallic=0.4,emission=0):
    mat=bpy.data.materials.new(name);mat.diffuse_color=(*color,1);mat.use_nodes=True
    bs=mat.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Metallic'].default_value=metallic
    bs.inputs['Roughness'].default_value=.3
    if emission:
        bs.inputs['Emission Color'].default_value=(*color,1);bs.inputs['Emission Strength'].default_value=emission
    return mat

def add_mesh(name,verts,faces,mat,cid,config,quadrant=-1):
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    for face in mesh.polygons:face.use_smooth=True
    obj['component_id']=cid;obj['configuration_id']=config['id']
    obj['evidence_level']='display_envelope_not_validated_CAD'
    obj['source_artifact_sha256']=config['provenance']['artifact_sha256']
    obj['cutaway_segment']=quadrant==3
    return obj

def contour(g,theta,inboard=0.,outboard=0.,vertical=0.):
    center=g['major_radius_m']+(outboard-inboard)/2
    a=g['minor_radius_m']+(inboard+outboard)/2
    b=g['minor_radius_m']*g['elongation']+vertical
    return center+a*math.cos(theta+math.asin(g['triangularity'])*math.sin(theta)), b*math.sin(theta)

def shell(name,g,inner,outer,mat,config):
    # Four quarter shells allow a cutaway without changing scientific geometry.
    for quadrant in range(4):
        verts=[];faces=[];ns=32;nt=96
        for layer in (inner,outer):
            for i in range(ns+1):
                phi=TAU*(quadrant/4+i/ns/4)
                for j in range(nt):
                    r,z=contour(g,TAU*j/nt,*layer)
                    verts.append((r*math.cos(phi),r*math.sin(phi),z))
        size=(ns+1)*nt
        for offset,flip in ((0,True),(size,False)):
            for i in range(ns):
                for j in range(nt):
                    f=(offset+i*nt+j,offset+i*nt+(j+1)%nt,offset+(i+1)*nt+(j+1)%nt,offset+(i+1)*nt+j)
                    faces.append(tuple(reversed(f)) if flip else f)
        for i in (0,ns):
            for j in range(nt):
                f=(i*nt+j,size+i*nt+j,size+i*nt+(j+1)%nt,i*nt+(j+1)%nt)
                faces.append(tuple(reversed(f)) if i==0 else f)
        add_mesh(f'{name}_Q{quadrant}',verts,faces,mat,name,config,quadrant)

def plasma(g,mat,config):
    verts=[];faces=[];ns=128;nt=64
    for i in range(ns):
        phi=TAU*i/ns
        for j in range(nt):
            r,z=contour(g,TAU*j/nt)
            verts.append((r*math.cos(phi),r*math.sin(phi),z))
    for i in range(ns):
        for j in range(nt):faces.append((i*nt+j,i*nt+(j+1)%nt,((i+1)%ns)*nt+(j+1)%nt,((i+1)%ns)*nt+j))
    add_mesh('plasma',verts,faces,mat,'plasma',config)

def solenoid(g,mat,config):
    r1=g['solenoid_inner_radius_m'];r2=r1+g['solenoid_radial_width_m'];h=g['solenoid_height_m']/2
    verts=[];faces=[];n=128
    for r,z in ((r1,-h),(r1,h),(r2,-h),(r2,h)):
        verts.extend((r*math.cos(TAU*i/n),r*math.sin(TAU*i/n),z) for i in range(n))
    for i in range(n):
        j=(i+1)%n
        faces.extend([(i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),
                      (i,2*n+i,2*n+j,j),(n+i,n+j,3*n+j,3*n+i)])
    add_mesh('solenoid',verts,faces,mat,'solenoid',config)

def coil(g,angle,mat,config,index):
    # Count is native; coil cross-section and path are schematic only.
    rmin=g['solenoid_inner_radius_m']+g['solenoid_radial_width_m']+.24
    rmax=g['major_radius_m']+g['minor_radius_m']+g['plasma_gap_outboard_m']+g['first_wall_outboard_m']+g['blanket_outboard_m']+g['shield_outboard_m']+g['vessel_outboard_m']+.75
    c=(rmin+rmax)/2;a=(rmax-rmin)/2;b=g['minor_radius_m']*g['elongation']+2.3
    verts=[];faces=[];n=96;m=8;radius=.18
    for i in range(n):
        t=TAU*i/n;r=c+a*math.cos(t);z=b*math.sin(t)
        norm=Vector((math.cos(t)/a,math.sin(t)/b));norm.normalize()
        for j in range(m):
            s=TAU*j/m;rr=r+radius*math.cos(s)*norm.x;zz=z+radius*math.cos(s)*norm.y;toro=radius*math.sin(s)
            verts.append((rr*math.cos(angle)-toro*math.sin(angle),rr*math.sin(angle)+toro*math.cos(angle),zz))
    for i in range(n):
        for j in range(m):faces.append((i*m+j,i*m+(j+1)%m,((i+1)%n)*m+(j+1)%m,((i+1)%n)*m+j))
    obj=add_mesh(f'coils_{index:02d}',verts,faces,mat,'coils',config,3 if angle>=1.5*math.pi else -1)
    obj['evidence_level']='schematic_coil_path_native_count_only'

def aim(obj,point):obj.rotation_euler=(Vector(point)-obj.location).to_track_quat('-Z','Y').to_euler()

def make(config,root):
    for old in list(bpy.data.objects):
        bpy.data.objects.remove(old,do_unlink=True)
    for old in list(bpy.data.meshes):
        if old.users==0:bpy.data.meshes.remove(old)
    for old in list(bpy.data.materials):
        if old.users==0:bpy.data.materials.remove(old)
    scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
    g=config['geometry']
    mats={'plasma':material('Plasma_display_glow',(0.06,.7,.66),0.1,.7),
          'solenoid':material('Solenoid_copper',(.56,.25,.1),.72),
          'first_wall':material('First_wall',(.12,.48,.56),.55),
          'blanket':material('Blanket',(.72,.55,.26),.45),
          'shield':material('Shield',(.19,.29,.37),.65),
          'vessel':material('Vessel',(.47,.59,.66),.65),
          'coils':material('TF_coils_schematic',(.31,.39,.43),.7)}
    plasma(g,mats['plasma'],config);solenoid(g,mats['solenoid'],config)
    current=(g['plasma_gap_inboard_m'],g['plasma_gap_outboard_m'],g['plasma_gap_upper_m'])
    for name,delta in (
        ('first_wall',(g['first_wall_inboard_m'],g['first_wall_outboard_m'],.018)),
        ('blanket',(g['blanket_inboard_m'],g['blanket_outboard_m'],g['blanket_upper_m'])),
        ('shield',(g['shield_inboard_m'],g['shield_outboard_m'],.5)),
        ('vessel',(g['vessel_inboard_m'],g['vessel_outboard_m'],.3))):
        nxt=tuple(a+b for a,b in zip(current,delta));shell(name,g,current,nxt,mats[name],config);current=nxt
    for i in range(int(g['toroidal_coil_count'])):coil(g,TAU*i/g['toroidal_coil_count'],mats['coils'],config,i)
    components=[obj for obj in scene.objects if obj.type=='MESH']
    assert len(components)==18+int(g['toroidal_coil_count']), 'Unexpected leftover geometry'
    assert all(obj.get('configuration_id')==config['id'] for obj in components), 'Cross-configuration mesh rejected'
    # All quadrants are exported; viewers can hide the explicitly tagged quadrant.
    glb=root/'app/web/assets'/f"{config['id']}.glb";glb.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',export_extras=True,export_cameras=False,export_lights=False)
    usd=root/'output'/f"{config['id']}.usda";usd.parent.mkdir(exist_ok=True)
    props=bpy.ops.wm.usd_export.get_rna_type().properties.keys()
    options={'filepath':str(usd),'export_materials':True,'export_custom_properties':True,'generate_preview_surface':True}
    bpy.ops.wm.usd_export(**{k:v for k,v in options.items() if k in props})
    for obj in components:
        if obj.get('cutaway_segment'):obj.hide_render=True;obj.hide_set(True)
    # Presentation only; not exported into the device's scientific mesh hierarchy.
    bpy.ops.object.camera_add(location=(30,-38,26));cam=bpy.context.object;aim(cam,(0,0,0));scene.camera=cam;cam.data.lens=48
    for pos,power,size in [((8,-16,25),70000,18),((-20,-8,14),55000,15),((6,18,22),90000,12)]:
        bpy.ops.object.light_add(type='AREA',location=pos);light=bpy.context.object;light.data.energy=power;light.data.shape='DISK';light.data.size=size;aim(light,(0,0,0))
    scene.world.color=(.05,.05,.05)
    scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=1400;scene.render.resolution_y=1050;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
    scene.view_settings.view_transform='AgX'
    for area in bpy.context.screen.areas if bpy.context.screen else []:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_distance=45
            area.spaces.active.clip_end=1000
    blend=root/'output'/f"{config['id']}.blend";bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    scene.render.filepath=str(root/'output'/f"{config['id']}_preview.png");bpy.ops.render.render(write_still=True)
    bound=[obj.matrix_world@Vector(corner) for obj in components for corner in obj.bound_box]
    return {'configuration_id':config['id'],'mesh_objects':len(components),'triangulated_mesh_source':False,
            'glb_sha256':hashlib.sha256(glb.read_bytes()).hexdigest(),'usd_sha256':hashlib.sha256(usd.read_bytes()).hexdigest(),
            'size_m':[max(v[k] for v in bound)-min(v[k] for v in bound) for k in range(3)],
            'geometry_status':'dimension_linked_display_envelope_not_engineering_CAD',
            'metadata_policy':'Only component ID, configuration ID, evidence class, cutaway tag and source artifact hash.'}

if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);parsed=ap.parse_args(args)
    catalog=json.loads((parsed.root/'app/data/catalog.json').read_text())
    summaries=[make(c,parsed.root) for c in catalog['configurations']]
    (parsed.root/'output/model-manifest.json').write_text(json.dumps({'models':summaries,'blender_version':bpy.app.version_string,'claim':'Visualization only'},indent=2)+'\n')
    print('WORKBENCH_MODELS_COMPLETE',json.dumps(summaries))
