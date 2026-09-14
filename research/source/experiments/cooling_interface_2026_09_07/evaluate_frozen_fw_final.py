"""Candidate-specific reuse of PROCESS FW thermal model; no blanket optimization.
Uses the completed solved-state capture. No reactor optimization is rerun.
"""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','NUMBA_NUM_THREADS'):os.environ[k]='1'
from pathlib import Path
from types import SimpleNamespace as NS
import json,hashlib,math,copy
from scipy.optimize import brentq
from process.models.fw import FirstWall
from process.models.blankets.blanket_library import BlanketLibrary
from process.models.engineering.pumping import darcy_friction_haaland
from process.core.coolprop_interface import FluidProperties
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'blanket-interface-20260907'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,obj):(OUT/name).write_text(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')
def peak(state,side,tout,pressure):
    f=NS(**state['fwbs']);f.i_fw_coolant_type=1
    f.temp_fw_coolant_in=state['primary_pumping']['t_in_bb'];f.temp_fw_coolant_out=tout;f.pres_fw_coolant=pressure
    a=state['first_wall']['a_fw_'+side];an=state['first_wall']['a_fw_total']
    qn=f.p_fw_nuclear_heat_total_mw*a/an;qs=f.psurffwi if side=='inboard' else f.psurffwo
    history=[]
    for _ in range(30):
        ans=FirstWall.fw_temp(NS(data=NS(fwbs=f)),False,f.radius_fw_channel,state['build']['dr_fw_'+side],a,qs,qn,side)
        history.append(float(ans[0]));err=abs(ans[0]-f.temp_fw_peak);f.temp_fw_peak=float(ans[0])
        if err<1e-7:break
    else:raise RuntimeError('Thermal fixed point not converged')
    fluid=FluidProperties.of('Helium',temperature=tout,pressure=pressure)
    flux=float(ans[3])/(math.pi*f.radius_fw_channel**2);velocity=flux/fluid.density
    re=2*f.radius_fw_channel*flux/fluid.viscosity;pr=fluid.specific_heat_const_p*fluid.viscosity/fluid.thermal_conductivity
    friction=darcy_friction_haaland(re,f.roughness_fw_channel,f.radius_fw_channel)
    if not (3000<re<5e6 and .5<pr<2000):raise ValueError('Outside declared heat-transfer correlation domain')
    obj=NS(data=NS(fwbs=f),pipe_hydraulic_diameter=lambda _:2*f.radius_fw_channel,elbow_coeff=BlanketLibrary.elbow_coeff)
    meanfluid=FluidProperties.of('Helium',temperature=(f.temp_fw_coolant_in+tout)/2,pressure=pressure)
    def native_dp(props):
        return float(BlanketLibrary.coolant_friction_pressure_drop(obj,1,f.radius_fw_channel_90_bend,f.radius_fw_channel_180_bend,2,0,f.len_fw_channel,props.density,props.viscosity,flux/props.density,'frozen_FW',False))
    dp=friction*f.len_fw_channel/(2*f.radius_fw_channel)*flux**2/(2*fluid.density)
    return {'side':side,'area_m2':a,'surface_heat_MW':qs,'nuclear_heat_MW':qn,'coolant_outlet_K':tout,'pressure_Pa':pressure,'peak_K':float(ans[0]),'margin_to_native_limit_K':f.temp_fw_max-float(ans[0]),'native_limit_K':f.temp_fw_max,'massflow_per_channel_kg_s':float(ans[3]),'outlet_velocity_m_s':velocity,'Re_outlet':re,'Pr_outlet':pr,'Gnielinski_in_declared_range':3000<re<5e6 and .5<pr<2000,'straight_channel_dp_outlet_properties_Pa':dp,'iteration_history_K':history,'native_FW_dp_mean_properties_two_bends_Pa':native_dp(meanfluid),'native_FW_dp_outlet_properties_two_bends_Pa':native_dp(fluid)}
def main():
    state=json.loads((OUT/'SOLVED_STATE.json').read_text());p=state['primary_pumping'];f=state['fwbs']
    admission={'question':'Does FW temperature pass in either of the existing separate/shared loop interpretations for this solved point?','prior_art':'Reuse PROCESS FirstWall.fw_temp and existing shared-loop heat apportionment in BlanketLibrary; no new correlation or cooling concept.','state_sha256':sha(OUT/'SOLVED_STATE.json'),'code_sha256':sha(Path(__file__)),'layouts':['separate_FW_full_loop_rise','FW_then_blanket_shared_branch'],'pressure':'Uniform active mode3 pump outlet pressure; axial pressure/temperature profile not solved.','root_followon':'If separate layout fails, find FW-only maximum coolant outlet at native material temperature limit. This is a diagnostic requirement, not a free power-cycle improvement.','stop_rule':'four fixed-layout/side calculations and at most two outlet roots; no design sweep. Root bracket restricted to valid correlation regime; native two FW 90-degree bends added. Original attempt retained.'}
    save('FW_MAPPING_FINAL_ADMISSION.json',admission)
    rows=[]
    for layout in admission['layouts']:
        for side in ('inboard','outboard'):
            area=state['first_wall']['a_fw_'+side];qt=f['p_fw_nuclear_heat_total_mw']
            qfw=qt*area/state['first_wall']['a_fw_total']+f['psurffwi' if side=='inboard' else 'psurffwo']
            qbb=f['p_blkt_nuclear_heat_total_mw']*f['vol_blkt_'+side]/f['vol_blkt_total']
            fraction=1. if layout.startswith('separate') else qfw/(qfw+qbb)
            tout=p['t_in_bb']+fraction*(p['t_out_bb']-p['t_in_bb'])
            result=peak(state,side,tout,p['p_he']);result.update({'layout':layout,'FW_heat_fraction_of_branch':qfw/(qfw+qbb),'full_loop_dp_budget_Pa':p['dp_he'],'straight_channel_dp_to_loop_budget':result['straight_channel_dp_outlet_properties_Pa']/p['dp_he']});rows.append(result)
    requirements=[]
    for side in ('inboard','outboard'):
        fun=lambda t:peak(state,side,t,p['p_he'])['peak_K']-f['temp_fw_max']
        lo=p['t_in_bb']+.1*(p['t_out_bb']-p['t_in_bb']);hi=p['t_out_bb']
        if fun(lo)*fun(hi)<0:
            boundary=brentq(fun,lo,hi,xtol=1e-7);requirements.append({'side':side,'maximum_FW_only_outlet_K_with_other_inputs_frozen':boundary,'at_boundary':peak(state,side,boundary,p['p_he'])})
    result={'schema':'fusion.frozen-fw-mapping.v1','input':admission,'active_loop':p,'inactive_FW_fields':{k:f[k] for k in ['temp_fw_coolant_in','temp_fw_coolant_out','pres_fw_coolant','temp_fw_peak','temp_fw_max']},'rows':rows,'outlet_requirements':requirements,'native_li6_enrichment_percent':f['f_blkt_li6_enrichment'],'reactor_optimization_rerun':False,'physical_cooling_validated':False,'scope':['Mode3 does not call the detailed temperature evaluator in the pinned HCPB path; stored temperature is not a thermal result.','Both local circuit mappings are declared interpretations, not already-specified CAD; assumed area/volume nuclear heat partition is unchanged.','Pressure estimate is straight pipe at outlet properties, not complete compression work or a rigorous physical bound.','Two native FW 90-degree bends are included in explicit diagnostic fields; manifold/heat exchanger/blanket pressure loss, thermal stress, uncertainty and plasma transients remain unresolved.','No change is credited to electrical output; no neutron calculation or TBR was run.']}
    save('FW_MAPPING_FINAL_RESULT.json',result);print(json.dumps(result,allow_nan=False),flush=True)
if __name__=='__main__':main()
