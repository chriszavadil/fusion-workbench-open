"""Editor-only USD scene assembly. Runtime workbench UI is a separate milestone.

Run with UnrealEditor-Cmd PROJECT -run=pythonscript -script=THIS_SCRIPT
The root is inferred from the .uproject, never a baked-in personal directory.
"""
import json
from pathlib import Path
import unreal

PROJECT=Path(unreal.Paths.project_dir()).resolve()
ROOT=PROJECT.parent
CATALOG=json.loads((ROOT/'app/data/catalog.json').read_text())

def label(actors,message,location,size=50):
    obj=actors.spawn_actor_from_class(unreal.TextRenderActor,unreal.Vector(*location),unreal.Rotator(0,180,0))
    c=obj.get_component_by_class(unreal.TextRenderComponent)
    c.set_text(message);c.set_world_size(size)
    obj.tags=[unreal.Name('fusion_generated')]
    obj.set_actor_label('Evidence label')
    return obj

level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
rows=[]
for config in CATALOG['configurations']:
    name='R838' if config['id']=='r838' else 'R900'
    map_path='/Game/Generated/'+name
    if unreal.EditorAssetLibrary.does_asset_exist(map_path):
        if not level.load_level(map_path):raise RuntimeError('Could not load generated level')
        for old in actors.get_all_level_actors():
            if 'fusion_generated' in [str(x) for x in old.tags]:actors.destroy_actor(old)
    elif not level.new_level(map_path):raise RuntimeError('Could not create a new research level')
    stage=actors.spawn_actor_from_class(unreal.UsdStageActor,unreal.Vector(0,0,0),unreal.Rotator(0,0,0))
    stage.tags=[unreal.Name('fusion_generated')]
    stage.set_actor_label(config['title']+' | display envelope')
    stage.set_root_layer(str(ROOT/'output'/f"{config['id']}.usda"))
    stage.set_kinds_to_collapse(0)
    stage.set_collect_metadata(True)
    # Sidecar data remains separate from the USD display; scalar values are not fields.
    m=config['metrics']
    label(actors,'FUSION WORKBENCH',(-1700,0,1350),100)
    label(actors,config['title'],(-1700,0,1180),65)
    label(actors,'CONCEPTUAL MODEL - NOT A VALIDATED REACTOR',(-1700,0,1040),40)
    label(actors,f"Generating-phase net: {m['flat_top_net_MW']:.1f} MW\nConditional average: {m['conditional_average_net_MW']:.2f} MW\nRecorded evidence, not live plasma",(-1700,0,-1050),45)
    light=actors.spawn_actor_from_class(unreal.DirectionalLight,unreal.Vector(0,0,2000),unreal.Rotator(-40,-35,0))
    light.tags=[unreal.Name('fusion_generated')]
    light.get_component_by_class(unreal.DirectionalLightComponent).set_intensity(5)
    sky=actors.spawn_actor_from_class(unreal.SkyLight,unreal.Vector(0,0,0),unreal.Rotator(0,0,0))
    sky.tags=[unreal.Name('fusion_generated')]
    generated=[stage]+list(stage.get_attached_actors(True,True))
    mesh_actors=[a for a in generated if a.get_components_by_class(unreal.StaticMeshComponent)]
    boxes=[a.get_actor_bounds(False,True) for a in mesh_actors]
    if not boxes:raise RuntimeError('USD did not generate mesh actors')
    lo=[min(getattr(o,axis)-getattr(e,axis) for o,e in boxes) for axis in ('x','y','z')]
    hi=[max(getattr(o,axis)+getattr(e,axis) for o,e in boxes) for axis in ('x','y','z')]
    sizes=[b-a for a,b in zip(lo,hi)]
    expected=next(x['size_m'] for x in json.loads((ROOT/'output/model-manifest.json').read_text())['models'] if x['configuration_id']==config['id'])
    diagnostic={'bounds_cm':sizes,'expected_cm':[v*100 for v in expected],'mesh_actor_count':len(mesh_actors)}
    (ROOT/'.local'/f"unreal-bounds-{config['id']}.json").write_text(json.dumps(diagnostic,indent=2))
    if not all(abs(v-e*100)<1.0 for v,e in zip(sizes,expected)):
        raise RuntimeError('USD metric conversion verification failed: '+str(diagnostic))
    if not level.save_current_level():raise RuntimeError('Could not save the research map')
    rows.append({'configuration_id':config['id'],'map':'/Game/Generated/'+name,'bounds_cm':sizes,'USD_loaded':True,'runtime_UMG_app':False})
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(unreal.Vector(3600,3600,2500),unreal.Rotator(-25,-135,0))
    level.save_current_level()
result={'maps':rows,'scope':'Editor scene import and metric bounds verification, not physical validation','full_runtime_UI_complete':False}
(ROOT/'.local/unreal-build-result.json').write_text(json.dumps(result,indent=2)+'\n')
unreal.log('FUSION_WORKBENCH_UNREAL_COMPLETE '+json.dumps(result))
