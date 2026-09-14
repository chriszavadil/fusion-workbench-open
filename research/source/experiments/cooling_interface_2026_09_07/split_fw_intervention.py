"""One declared local design intervention: split each 4m FW path into two 2m paths.
Reuse existing correlations; do not claim parallel cooling is new or manifold cost-free.
"""
from pathlib import Path
import json,copy,hashlib,math
from evaluate_frozen_fw_final import peak
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'blanket-interface-20260907'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,obj):(OUT/name).write_text(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')
def main():
    s=json.loads((OUT/'SOLVED_STATE.json').read_text());t=json.loads((OUT/'FW_MAPPING_FINAL_RESULT.json').read_text());hyd=json.loads((OUT/'COOLANT_VOLUME_RESULT.json').read_text())
    admission={'question':'Can one two-way split of the existing FW paths leave a usable pressure budget without failing native FW temperature or silently increasing the in-wall coolant volume?','classification':'adaptive follow-on component-design comparison, not independent discovery','nearest_prior_art':['10.1016/j.fusengdes.2017.02.072 parallel HCPB FW channels and measured unequal channel/connection losses','10.3389/fnuen.2025.1694684 combined neutron/hydraulic optimization','Pinned PROCESS FirstWall and BlanketLibrary native methods'],'intervention':{'split_factor':2,'old_length_m':s['fwbs']['len_fw_channel'],'new_length_m':s['fwbs']['len_fw_channel']/2,'channel_radius_unchanged':True,'effective_total_FW_channel_count_multiplier':2},'unchanged':['FW area, pitch, channel radius, wall thickness, native surface/nuclear heat, branch mass flow and helium endpoints','Blanket inventory-matched channels and their pressure model','550kPa overall loop pressure allowance; no reduction credited to power'],'unresolved_costs':['Additional feed/return connections and manifold volumes, flow imbalance, local stress, neutron/structural penalties, external piping and heat exchanger losses.'],'stop_rule':'Evaluate this one split at two property approximations for IB and OB; no further sweep or optimistic net-power update.','state_sha256':sha(OUT/'SOLVED_STATE.json'),'code_sha256':sha(Path(__file__))}
    save('SPLIT_FW_ADMISSION.json',admission)
    alt=copy.deepcopy(s);alt['fwbs']['len_fw_channel']=s['fwbs']['len_fw_channel']/2
    rows=[]
    for side in ('inboard','outboard'):
        base=next(r for r in t['rows'] if r['side']==side and r['layout']=='FW_then_blanket_shared_branch')
        bb=next(r for r in hyd['rows'] if r['side']==side and r['mapping']=='inventory_matched_diagnostic')
        new=peak(alt,side,base['coolant_outlet_K'],s['primary_pumping']['p_he'])
        n=s['blanket']['n_fw_'+side+'_channels'];a=math.pi*s['fwbs']['radius_fw_channel']**2
        oldvol=n*a*s['fwbs']['len_fw_channel'];newvol=2*n*a*alt['fwbs']['len_fw_channel']
        oldmass=n*base['massflow_per_channel_kg_s'];newmass=2*n*new['massflow_per_channel_kg_s']
        assert abs(oldvol-newvol)<1e-10 and abs(oldmass-newmass)<1e-8
        estimates={}
        for label in ('mean_properties','outlet_properties'):
            fw_dp=new['native_FW_dp_'+label+'_two_bends_Pa'];bz_dp=bb['estimates'][label]['blanket_channel_dp_Pa'];budget=s['primary_pumping']['dp_he']
            estimates[label]={'FW_dp_Pa':fw_dp,'blanket_dp_Pa':bz_dp,'combined_channel_dp_Pa':fw_dp+bz_dp,'remaining_manifold_HX_piping_budget_Pa':budget-fw_dp-bz_dp,'baseline_combined_channel_dp_Pa':bb['estimates'][label]['combined_FW_BZ_dp_Pa']}
        rows.append({'side':side,'baseline_peak_K':base['peak_K'],'split_FW':new,'baseline_channel_count':n,'split_channel_count':2*n,'unchanged_FW_channel_void_volume_m3':oldvol,'channel_void_volume_difference_m3':newvol-oldvol,'branch_mass_flow_difference_kg_s':newmass-oldmass,'estimates':estimates})
    result={'schema':'fusion.split-fw-local-intervention.v1','input':admission,'rows':rows,'net_power_recalculated':False,'matched_neutronics_performed':False,'physical_cooling_validated':False,'interpretation':'Local channel temperature/pressure screen only. Extra manifold volume and loss must fit the resulting budget AND the neutron/material contract before adopting the intervention.'}
    save('SPLIT_FW_RESULT.json',result);print(json.dumps(result,allow_nan=False),flush=True)
if __name__=='__main__':main()
