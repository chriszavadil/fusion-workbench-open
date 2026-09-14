"""Create only original minimal material/map assets for the packaged runtime."""
import unreal,json
from pathlib import Path
root=Path(unreal.Paths.project_dir()).resolve();assets=unreal.AssetToolsHelpers.get_asset_tools();edit=unreal.MaterialEditingLibrary
path='/Game/Workbench/M_Surface'
mat=unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else assets.create_asset('M_Surface','/Game/Workbench',unreal.Material,unreal.MaterialFactoryNew())
edit.delete_all_material_expressions(mat)
mat.set_editor_property('two_sided',True)
color=edit.create_material_expression(mat,unreal.MaterialExpressionVectorParameter,-450,-50);color.set_editor_property('parameter_name','Color');color.set_editor_property('default_value',unreal.LinearColor(.6,.7,.75,1))
glow=edit.create_material_expression(mat,unreal.MaterialExpressionScalarParameter,-450,180);glow.set_editor_property('parameter_name','Glow');glow.set_editor_property('default_value',.03)
mult=edit.create_material_expression(mat,unreal.MaterialExpressionMultiply,-150,180)
edit.connect_material_expressions(color,'',mult,'A');edit.connect_material_expressions(glow,'',mult,'B')
edit.connect_material_property(color,'',unreal.MaterialProperty.MP_BASE_COLOR);edit.connect_material_property(mult,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
rough=edit.create_material_expression(mat,unreal.MaterialExpressionConstant,-150,340);rough.set_editor_property('r',.42);edit.connect_material_property(rough,'',unreal.MaterialProperty.MP_ROUGHNESS)
metal=edit.create_material_expression(mat,unreal.MaterialExpressionConstant,-150,450);metal.set_editor_property('r',.22);edit.connect_material_property(metal,'',unreal.MaterialProperty.MP_METALLIC)
edit.recompile_material(mat);unreal.EditorAssetLibrary.save_loaded_asset(mat)
level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if unreal.EditorAssetLibrary.does_asset_exist('/Game/Boot'):assert level.load_level('/Game/Boot')
else:assert level.new_level('/Game/Boot')
assert level.save_current_level()
(root/'native-assets-result.json').write_text(json.dumps({'material':path,'map':'/Game/Boot','created':True,'physical_validation':False},indent=2)+'\n')
unreal.log('FUSION_NATIVE_ASSETS_READY')
