"""Candidate-specific common-pressure test; reuses pinned PROCESS hydraulics.
Not a new flow correlation or a completed/validated manifold design.
"""
from __future__ import annotations
import os,sys,json,math,hashlib,copy
from pathlib import Path
from types import SimpleNamespace as NS
from functools import lru_cache
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','NUMBA_NUM_THREADS'):os.environ[k]='1'
import numpy as np
from scipy.optimize import brentq, root
from CoolProp.CoolProp import PropsSI
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(ROOT))
import evaluate_frozen_fw_final as fw_model
from process.models.blankets.blanket_library import BlanketLibrary
from process.core.coolprop_interface import FluidProperties
STATE_SHA='cedcfa6d695fd45d4be17ea1ee77ae40d821064ea15eb1244822804f3001f9ea'
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p:Path,obj):p.write_text(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')
def load():
    p=ROOT/'blanket-interface-20260907/SOLVED_STATE.json'
    if sha(p)!=STATE_SHA:raise ValueError('Wrong solved state')
    if sha(ROOT/'evaluate_frozen_fw_final.py')!='773ab997cad8265708eab529d08723f807db168e0ec9fd5d2a26cd28fb684dae':raise ValueError('Wrong inherited evaluator')
    return json.loads(p.read_text())
class Network:
    def __init__(self,s):
        self.s=s;self.f=s['fwbs'];self.p=s['primary_pumping'];self.b=s['blanket']
        self.pin=self.p['p_he'];self.tin=self.p['t_in_bb'];self.tout=self.p['t_out_bb']
        self.limit=self.f['temp_fw_max'];self.allowance=self.p['dp_he']
        self.nominal={};self.heat={};self.nfw={};self.lengths={'inboard':4.,'outboard':2.}
        for side in self.lengths:
            area=s['first_wall']['a_fw_'+side]
            qfw=self.f['p_fw_nuclear_heat_total_mw']*area/s['first_wall']['a_fw_total']+self.f['psurffwi' if side=='inboard' else 'psurffwo']
            qbz=self.f['p_blkt_nuclear_heat_total_mw']*self.f['vol_blkt_'+side]/self.f['vol_blkt_total']
            self.heat[side]=(qfw*1e6,qbz*1e6)
            self.nfw[side]=area/(self.f['dx_fw_module']*self.lengths[side])
            tfw=self.tin+qfw/(qfw+qbz)*(self.tout-self.tin)
            self.nominal[side]=qfw*1e6/self.cp_integral(self.tin,tfw)
        self.total=sum(self.nominal.values())
    @lru_cache(maxsize=4096)
    def props(self,t):return FluidProperties.of('Helium',temperature=t,pressure=self.pin)
    def cp_integral(self,t0,t1):
        return .5*(self.props(t0).specific_heat_const_p+self.props(t1).specific_heat_const_p)*(t1-t0)
    def outlet(self,t0,q,m):
        if not math.isfinite(m) or m<=0:raise ValueError('Positive finite flow required')
        return brentq(lambda t:self.cp_integral(t0,t)-q/m,t0+1e-6,1400.,xtol=1e-9)
    def friction(self,flow_per_channel,t,length,n90,n180):
        f=self.f;props=self.props(t);r=f['radius_fw_channel'];v=flow_per_channel/(math.pi*r*r*props.density)
        obj=NS(data=NS(fwbs=NS(**f)),pipe_hydraulic_diameter=lambda _:2*r,elbow_coeff=BlanketLibrary.elbow_coeff)
        dp=float(BlanketLibrary.coolant_friction_pressure_drop(obj,1,f['radius_blkt_channel_90_bend'],f['radius_blkt_channel_180_bend'],n90,n180,length,props.density,props.viscosity,v,'network',False))
        return dp,v,2*r*flow_per_channel/(math.pi*r*r*props.viscosity)
    def branch(self,side,m,choice='mean',reserve_fraction=0.):
        if choice not in ('mean','outlet'):raise ValueError('Unknown property choice')
        if not 0<=reserve_fraction<1:raise ValueError('Invalid reserved coolant fraction')
        qfw,qbz=self.heat[side];tfw=self.outlet(self.tin,qfw,m);tbz=self.outlet(tfw,qbz,m)
        local=copy.deepcopy(self.s);local['fwbs']['len_fw_channel']=self.lengths[side]
        wall=fw_model.peak(local,side,tfw,self.pin)
        n=self.f['vfcblkt']*(1-reserve_fraction)*self.f['vol_blkt_'+side]/(math.pi*self.f['radius_fw_channel']**2*self.b['len_blkt_'+side+'_channel_total'])
        t_bz=.5*(tfw+tbz) if choice=='mean' else tbz
        dpbz,velbz,rebz=self.friction(m/n,t_bz,self.b['len_blkt_'+side+'_channel_total'],4,1)
        dpfw=wall['native_FW_dp_'+('mean_properties' if choice=='mean' else 'outlet_properties')+'_two_bends_Pa']
        h0=PropsSI('Hmass','T',self.tin,'P',self.pin,'Helium');h1=PropsSI('Hmass','T',tfw,'P',self.pin,'Helium');h2=PropsSI('Hmass','T',tbz,'P',self.pin,'Helium')
        return {'side':side,'flow_kg_s':m,'flow_relative_to_nominal':m/self.nominal[side],'FW_outlet_K':tfw,'BZ_outlet_K':tbz,'peak_K':wall['peak_K'],'temperature_margin_K':self.limit-wall['peak_K'],'channel_drop_Pa':dpfw+dpbz,'FW_drop_Pa':dpfw,'BZ_drop_Pa':dpbz,'effective_FW_channels':self.nfw[side],'effective_BZ_channels':n,'reserved_coolant_volume_m3':reserve_fraction*self.f['vfcblkt']*self.f['vol_blkt_'+side],'BZ_Re':rebz,'BZ_velocity_m_s':velbz,'native_massflow_identity_error_kg_s':wall['massflow_per_channel_kg_s']*self.nfw[side]-m,'exact_enthalpy_heat_error_relative':(m*(h2-h0)-(qfw+qbz))/(qfw+qbz),'FW_exact_enthalpy_error_relative':(m*(h1-h0)-qfw)/qfw}
    def balance(self,choice='mean',outboard_added_nominal_drop=0.):
        def pressure(i):
            mi=i;mo=self.total-mi
            a=self.branch('inboard',mi,choice);b=self.branch('outboard',mo,choice)
            extra=outboard_added_nominal_drop*(mo/self.nominal['outboard'])**2
            return a['channel_drop_Pa']-b['channel_drop_Pa']-extra
        mi=brentq(pressure,.45*self.nominal['inboard'],1.75*self.nominal['inboard'],xtol=1e-7)
        a=self.branch('inboard',mi,choice);b=self.branch('outboard',self.total-mi,choice)
        return {'IB':a,'OB':b,'total_flow_kg_s':self.total,'pressure_mismatch_Pa':pressure(mi),'added_outboard_loss_Pa':outboard_added_nominal_drop*(b['flow_kg_s']/self.nominal['outboard'])**2,'remaining_common_pressure_budget_Pa':self.allowance-a['channel_drop_Pa'],'both_below_temperature_limit':min(a['temperature_margin_K'],b['temperature_margin_K'])>=0}
    def minimum_flow(self,side):
        return brentq(lambda m:self.branch(side,m)['temperature_margin_K'],.4*self.nominal[side],self.nominal[side],xtol=1e-7)
def run():
    s=load();net=Network(s);old=Network(s)
    old.lengths['outboard']=4.;old.nfw['outboard']/=2
    admission=json.loads((HERE/'ADMISSION.json').read_text())
    admission.update({'code_sha256':sha(Path(__file__)),'original_unsplit_common_pressure_reference':True,'flow_normalization':'Continuum channel count=area/(length*pitch), avoiding rounded-count heat mismatch; compared with archived values.','energy_rule':'Native average-cp heat balance per stage, independently checked against CoolProp enthalpy; both branch outlet temperatures solved, not held fixed after flow redistribution.'})
    save(HERE/'FROZEN_INPUT.json',admission)
    minflows={side:net.minimum_flow(side) for side in net.lengths}
    results=[]
    for choice in ('mean','outlet'):
        nom={side:net.branch(side,net.nominal[side],choice) for side in net.lengths}
        extra=nom['inboard']['channel_drop_Pa']-nom['outboard']['channel_drop_Pa']
        if extra<=0:raise ValueError('Required balancing location differs from declared case')
        old_result=old.balance(choice);unbalanced=net.balance(choice);balanced=net.balance(choice,extra)
        mi=minflows['inboard'];mo=net.total-mi
        boundary_loss=(net.branch('inboard',mi,choice)['channel_drop_Pa']-net.branch('outboard',mo,choice)['channel_drop_Pa'])/(mo/net.nominal['outboard'])**2
        reserve_limits={}
        for side in net.lengths:
            fn=lambda f:net.branch(side,net.nominal[side],choice,f)['channel_drop_Pa']-net.allowance
            frac=brentq(fn,0.,.85,xtol=1e-10)
            reserve_limits[side]={'maximum_reservation_fraction_before_any_header_loss':frac,'maximum_reserved_coolant_m3':frac*net.f['vfcblkt']*net.f['vol_blkt_'+side]}
        results.append({'property_choice':choice,'nominal_prescribed_flows':nom,'original_unsplit_unbalanced':old_result,'selected_split_unbalanced':unbalanced,'nominal_added_OB_balancing_drop_Pa':extra,'balanced_split':balanced,'minimum_OB_nominal_balancing_drop_for_IB_thermal_limit_Pa':max(0.,boundary_loss),'inventory_reservation_upper_limits':reserve_limits})
    result={'schema':'fusion.parallel-branch-balance.v1','frozen_input_sha256':sha(HERE/'FROZEN_INPUT.json'),'nominal_flows_kg_s':net.nominal,'total_flow_kg_s':net.total,'minimum_thermal_flows_kg_s':minflows,'maximum_local_flow_shortfall_fraction':{k:1-minflows[k]/net.nominal[k] for k in minflows},'results':results,'power_output_recalculated':False,'validated_manifold_or_plant':False,'scope':admission['claim_boundary']+['Common-pressure aggregate topology is a diagnostic choice, not an already specified plant circuit.','Added loss is an inverse control/balancing requirement, not a manufactured valve/orifice or free hardware.','Reservation limits remove channel volume to make space but allocate no pressure drop, steel thickness or actual manifold geometry; they are necessary screening budgets only.','No header dimensions, branch-jet CFD, heat-map uncertainty, neutron transport or added power generation has been validated.']}
    save(HERE/'RESULT.json',result)
    print(json.dumps({'nominal_flows':net.nominal,'min_flows':minflows,'summaries':[{'choice':r['property_choice'],'old_pass':r['original_unsplit_unbalanced']['both_below_temperature_limit'],'split_pass':r['selected_split_unbalanced']['both_below_temperature_limit'],'unbalanced_split_IB_peak_K':r['selected_split_unbalanced']['IB']['peak_K'],'unbalanced_split_IB_fraction':r['selected_split_unbalanced']['IB']['flow_relative_to_nominal'],'balanced_pass':r['balanced_split']['both_below_temperature_limit'],'required_balancing_Pa':r['nominal_added_OB_balancing_drop_Pa'],'remaining_budget_Pa':r['balanced_split']['remaining_common_pressure_budget_Pa']} for r in results]},indent=2),flush=True)
    return result
if __name__=='__main__':run()
