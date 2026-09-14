"""Check the candidate's coolant inventory against native hydraulic pipe counting.
A targeted same-design consistency test, not a new hydraulics model or blanket search.
"""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','NUMBA_NUM_THREADS'):os.environ[k]='1'
from pathlib import Path
from types import SimpleNamespace as NS
import json,math,hashlib
from process.models.blankets.blanket_library import BlanketLibrary
from process.core.coolprop_interface import FluidProperties
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'blanket-interface-20260907'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,obj):(OUT/name).write_text(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')
def main():
    s=json.loads((OUT/'SOLVED_STATE.json').read_text());thermal=json.loads((OUT/'FW_MAPPING_FINAL_RESULT.json').read_text());f=s['fwbs'];p=s['primary_pumping'];b=s['blanket']
    admission={'question':'Does the inactive hydraulic default allocate the same coolant volume as the solved blanket inventory, and what loop-pressure margin remains under an explicitly matched allocation?','source':'Pinned BlanketLibrary.thermo_hydraulic_model_pressure_drop_calculations solid-breeder branch uses N = f_a_blkt_cooling_channels * V / (pi r^2 L).','state_sha256':sha(OUT/'SOLVED_STATE.json'),'thermal_result_sha256':sha(OUT/'FW_MAPPING_FINAL_RESULT.json'),'code_sha256':sha(Path(__file__)),'mappings':{'inactive_hydraulic_default':f['f_a_blkt_cooling_channels'],'inventory_matched_diagnostic':f['vfcblkt']},'stop_rule':'Two volume mappings for each existing inboard/outboard branch, no optimization.','scope':'Uses the same existing shared-loop heat allocation and fluid properties. Does not validate real manifold, parallel distribution or pressure profile.'}
    save('COOLANT_VOLUME_ADMISSION.json',admission)
    obj=NS(data=NS(fwbs=NS(**f)),pipe_hydraulic_diameter=lambda _:2*f['radius_fw_channel'],elbow_coeff=BlanketLibrary.elbow_coeff)
    rows=[]
    for mapping,frac in admission['mappings'].items():
        for side in ('inboard','outboard'):
            fw=next(r for r in thermal['rows'] if r['side']==side and r['layout']=='FW_then_blanket_shared_branch')
            nfw=b['n_fw_'+side+'_channels'];massflow=fw['massflow_per_channel_kg_s']*nfw
            length=b['len_blkt_'+side+'_channel_total'];volume=f['vol_blkt_'+side]
            n=frac*volume/(math.pi*f['radius_fw_channel']**2*length);pipe_mass=massflow/n
            estimates={}
            for label,temp in [('mean_properties',(fw['coolant_outlet_K']+p['t_out_bb'])/2),('outlet_properties',p['t_out_bb'])]:
                props=FluidProperties.of('Helium',temperature=temp,pressure=p['p_he']);velocity=pipe_mass/(math.pi*f['radius_fw_channel']**2*props.density)
                dp=float(BlanketLibrary.coolant_friction_pressure_drop(obj,1,f['radius_blkt_channel_90_bend'],f['radius_blkt_channel_180_bend'],4,1,length,props.density,props.viscosity,velocity,'frozen_BZ',False))
                fw_dp=fw['native_FW_dp_'+label+'_two_bends_Pa']
                estimates[label]={'blanket_channel_dp_Pa':dp,'FW_channel_dp_Pa':fw_dp,'combined_FW_BZ_dp_Pa':fw_dp+dp,'remaining_for_manifolds_HX_pipes_Pa':p['dp_he']-fw_dp-dp,'blanket_velocity_m_s':velocity,'blanket_Re':2*f['radius_fw_channel']*pipe_mass/(math.pi*f['radius_fw_channel']**2*props.viscosity)}
            rows.append({'mapping':mapping,'side':side,'coolant_fraction_in_channel_count':frac,'native_inventory_coolant_fraction':f['vfcblkt'],'counted_pipe_volume_m3':n*math.pi*f['radius_fw_channel']**2*length,'inventory_pressurized_coolant_volume_m3':f['vfcblkt']*volume,'effective_number_of_blanket_channels':n,'blanket_channel_length_m':length,'branch_massflow_kg_s':massflow,'blanket_massflow_per_channel_kg_s':pipe_mass,'estimates':estimates})
    result={'schema':'fusion.coolant-volume-interface.v1','input':admission,'native_default_to_inventory_fraction_ratio':f['f_a_blkt_cooling_channels']/f['vfcblkt'],'rows':rows,'scope':['The 25% channel-count default is inactive in the solved mode3 plant; it is NOT a measured inventory.','Equating hydraulic channel volume to the 5.295% inventory is an explicitly declared diagnostic mapping, not a proven CAD/circuit design.','Mean/outlet property estimates are alternative approximations, not confidence bounds or a full compressible pressure solution.','Four blanket 90-degree bends and one 180-degree bend follow the existing code; manifolds, heat exchanger and external piping losses are not included.','The first-wall and blanket branch heat allocations follow the existing heuristic model, not source-matched neutron transport.','No change is credited to net power and no physical cooling or breeding feasibility is established.']}
    save('COOLANT_VOLUME_RESULT.json',result)
    print(json.dumps(result,allow_nan=False),flush=True)
if __name__=='__main__':main()
