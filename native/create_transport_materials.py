"""Original runtime visualization materials. No fabricated physical fields."""
import unreal,json
from pathlib import Path
assets=unreal.AssetToolsHelpers.get_asset_tools();edit=unreal.MaterialEditingLibrary
for name,ghost,unlit in [('M_LabMetal',False,False),('M_LabData',False,True),('M_LabGhost',True,True)]:
 path='/Game/Workbench/'+name
 mat=unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else assets.create_asset(name,'/Game/Workbench',unreal.Material,unreal.MaterialFactoryNew())
 edit.delete_all_material_expressions(mat);mat.set_editor_property('two_sided',True)
 if unlit:mat.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT)
 if ghost:mat.set_editor_property('blend_mode',unreal.BlendMode.BLEND_TRANSLUCENT)
 col=edit.create_material_expression(mat,unreal.MaterialExpressionVertexColor,-500,0)
 param=edit.create_material_expression(mat,unreal.MaterialExpressionVectorParameter,-500,180);param.set_editor_property('parameter_name','Tint');param.set_editor_property('default_value',unreal.LinearColor(1,1,1,1))
 mult=edit.create_material_expression(mat,unreal.MaterialExpressionMultiply,-250,0);edit.connect_material_expressions(col,'',mult,'A');edit.connect_material_expressions(param,'',mult,'B')
 edit.connect_material_property(mult,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR if unlit else unreal.MaterialProperty.MP_BASE_COLOR)
 if not unlit:
  rough=edit.create_material_expression(mat,unreal.MaterialExpressionConstant,-250,220);rough.set_editor_property('r',.3);edit.connect_material_property(rough,'',unreal.MaterialProperty.MP_ROUGHNESS)
  metal=edit.create_material_expression(mat,unreal.MaterialExpressionConstant,-250,330);metal.set_editor_property('r',.65);edit.connect_material_property(metal,'',unreal.MaterialProperty.MP_METALLIC)
 if ghost:
  alpha=edit.create_material_expression(mat,unreal.MaterialExpressionScalarParameter,-250,330);alpha.set_editor_property('parameter_name','Opacity');alpha.set_editor_property('default_value',.12);edit.connect_material_property(alpha,'',unreal.MaterialProperty.MP_OPACITY)
 edit.recompile_material(mat);unreal.EditorAssetLibrary.save_loaded_asset(mat)
unreal.log('TRANSPORT_MATERIALS_READY')
