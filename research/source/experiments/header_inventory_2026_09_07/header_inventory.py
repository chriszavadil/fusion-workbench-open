"""One declared header-envelope comparison; NOT a manufactured manifold design.
Reuses existing PROCESS hydraulics and the previously tested branch model.
The source papers establish topology/methods, not these chosen envelope dimensions.
"""
from __future__ import annotations
import os,sys,json,math,hashlib,copy
from pathlib import Path
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','NUMBA_NUM_THREADS'):os.environ[k]='1'
HERE=Path(__file__).resolve().parent; ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'flow-balance-20260907'))
from branch_balance import Network,load,sha,save
from process.models.engineering.pumping import darcy_friction_haaland
from CoolProp.CoolProp import PropsSI
from scipy.optimize import minimize_scalar
PIN='c0ae5b28649f2b20fb7efc7904628b6defe4151c'
class HeaderStudy:
    def __init__(self,state):
        self.state=state;self.net=Network(state);self.old=Network(state)
        self.old.lengths['outboard']=4.;self.old.nfw['outboard']/=2
        self.count={s:int(state['fwbs']['n_blkt_'+s+'_modules_toroidal']*state['fwbs']['n_blkt_'+s+'_modules_poloidal']) for s in self.net.lengths}
        self.length={s:state['blanket']['len_blkt_'+s+'_segment_poloidal'] for s in self.net.lengths}
    def geometry(self,side,radius):
        if side not in self.count or not math.isfinite(radius) or radius<=0:raise ValueError('Invalid header geometry')
        n=3*self.count[side];L=self.length[side];ri=radius;t=ri/6;ro=ri+t
        void=n*math.pi*ri**2*L
        shell=n*math.pi*(ro**2-ri**2)*L
        caps=n*2*math.pi*ro**2*t
        vc=self.state['fwbs']['vfcblkt']*self.state['fwbs']['vol_blkt_'+side]
        vs=self.state['fwbs']['f_vol_blkt_steel']*self.state['fwbs']['vol_blkt_'+side]
        if void>=vc or shell+caps>=vs:raise ValueError('Header envelope exhausts native inventory')
        p=self.net.pin;A=p*ri**2/(ro**2-ri**2);hoop=p*(ro**2+ri**2)/(ro**2-ri**2)
        vm=math.sqrt(.5*((hoop+p)**2+(-p-A)**2+(A-hoop)**2))
        return {'module_count':self.count[side],'header_count':n,'length_each_m':L,'inner_radius_m':ri,'wall_m':t,'outer_radius_m':ro,'header_coolant_m3':void,'shell_steel_m3':shell,'cap_volume_allowance_m3':caps,'native_coolant_m3':vc,'native_steel_m3':vs,'remaining_channel_coolant_m3':vc-void,'remaining_nonheader_steel_m3':vs-shell-caps,'coolant_reservation_fraction':void/vc,'steel_reservation_fraction':(shell+caps)/vs,'ideal_closed_barrel_hoop_Pa':hoop,'ideal_closed_barrel_von_Mises_Pa':vm,'caps_nozzles_and_remaining_structure_qualified':False}
    def evaluate(self,side,radius,split=True,choice='mean',flow=None):
        geom=self.geometry(side,radius);net=self.net if split else self.old
        m=net.nominal[side] if flow is None else flow
        branch=net.branch(side,m,choice,geom['coolant_reservation_fraction'])
        moduleflow=m/self.count[side]
        temps=[net.tin,branch['FW_outlet_K'],branch['BZ_outlet_K']]
        headers=[]
        for name,temp in zip(['supply','intermediate','return'],temps):
            prop=net.props(temp);area=math.pi*radius**2;velocity=moduleflow/(prop.density*area)
            reynolds=2*radius*moduleflow/(area*prop.viscosity)
            friction=float(darcy_friction_haaland(reynolds,net.f['roughness_fw_channel'],radius))
            dynamic=.5*prop.density*velocity**2
            dp=friction*self.length[side]/(2*radius)*dynamic
            sound=PropsSI('A','T',temp,'P',net.pin,'Helium')
            headers.append({'stage':name,'T_K':temp,'full_flow_friction_Pa':dp,'dynamic_head_Pa':dynamic,'velocity_m_s':velocity,'Mach':velocity/sound,'Re':reynolds})
        known=branch['channel_drop_Pa']+sum(h['full_flow_friction_Pa'] for h in headers)
        rem=net.allowance-known;weight=sum(h['dynamic_head_Pa'] for h in headers)
        return {'side':side,'split_outboard':split,'property_approximation':choice,'geometry':geom,'branch':branch,'headers':headers,'known_branch_pressure_Pa':known,'residual_to_full_loop_allowance_Pa':rem,'equal_per_header_unknown_K_allowance_if_no_external_loss':rem/weight,'dynamic_head_sum_Pa':weight,'native_temperature_margin_K':branch['temperature_margin_K'],'maximum_header_Mach':max(h['Mach'] for h in headers),'not_a_validated_hardware_result':True}
    def best(self,side,split,choice):
        vc=self.net.f['vfcblkt']*self.net.f['vol_blkt_'+side]
        rmax=math.sqrt(.85*vc/(3*self.count[side]*math.pi*self.length[side]))
        lo=.005
        opt=minimize_scalar(lambda r:self.evaluate(side,float(r),split,choice)['known_branch_pressure_Pa'],bounds=(lo,rmax),method='bounded',options={'xatol':1e-10,'maxiter':100})
        if not opt.success:raise RuntimeError(opt.message)
        r=float(opt.x);result=self.evaluate(side,r,split,choice)
        result['optimization']={'bounds_m':[lo,rmax],'objective':'known branch pressure only, unknown fittings and all steel adequacy excluded','evaluations':opt.nfev,'neighbor_pressure_differences_Pa':[self.evaluate(side,r*f,split,choice)['known_branch_pressure_Pa']-result['known_branch_pressure_Pa'] for f in [.99,1.01]],'global_plant_optimum_claim':False}
        return result
def run():
    s=load();study=HeaderStudy(s);frozen=json.loads((HERE/'ADMISSION.json').read_text())
    frozen.update({'driver_sha256':sha(Path(__file__)),'upstream_PROCESS':PIN,'branch_model_sha256':sha(ROOT/'flow-balance-20260907/branch_balance.py'),'thermal_model_sha256':sha(ROOT/'evaluate_frozen_fw_final.py'),'radius_search_domain':'0.005m to radius consuming85%of each native coolant inventory; minima must be interior; not a physically validated domain.','steel_allowable_stress_adopted':None,'hydraulic_feasibility_not_adoption':True})
    save(HERE/'FROZEN_INPUT.json',frozen)
    rows=[]
    for choice in ['mean','outlet']:
        ib=study.best('inboard',True,choice)
        for split in [False,True]:
            ob=study.best('outboard',split,choice)
            branches={'inboard':ib,'outboard':ob};common=max(x['known_branch_pressure_Pa'] for x in branches.values())
            extra={side:common-x['known_branch_pressure_Pa'] for side,x in branches.items()}
            row={'configuration':'outboard_split' if split else 'unsplit','choice':choice,'branches':branches,'known_common_pressure_Pa_after_nominal_balancing':common,'additional_balancing_drop_Pa':extra,'remaining_common_external_pressure_Pa':study.net.allowance-common,'total_header_coolant_m3':sum(x['geometry']['header_coolant_m3'] for x in branches.values()),'total_header_shell_cap_steel_m3':sum(x['geometry']['shell_steel_m3']+x['geometry']['cap_volume_allowance_m3'] for x in branches.values()),'envelope_known_loss_within_allowance':common<study.net.allowance,'all_nominal_FW_temperatures_below_native_limit':all(x['native_temperature_margin_K']>=0 for x in branches.values()),'unknown_loss_contract':'max_s(known_branch_drop_s + K_s*sum_header_dynamic_heads_s) + common_external_drop <=550000Pa; balances must be recalculated, not counted twice.','physical_manifold_or_plant_validated':False}
            rows.append(row)
    out={'schema':'fusion.header-inventory-comparison.v1','frozen_input_sha256':sha(HERE/'FROZEN_INPUT.json'),'results':rows,'scope':frozen['claim_boundary']+['Three circular envelopes per native module are a chosen topology, not an actual HCPB CAD reproduction.','Known friction charges full module flow over each full header length; it is NOT a bound on omitted junction/distribution losses.','Reallocating steel from the remaining blanket may compromise its support; no structural or breeding benefit is assumed.','Caps have volume only; local cap/nozzle/weld stresses, irradiated allowable values and thermal stress are not evaluated.','The repeated branch temperature calculation assumes prescribed nominal flow maintained by unspecified balancing.','No power-output update or tritium breeding tally was made.']}
    save(HERE/'RESULT.json',out)
    print(json.dumps([{'configuration':r['configuration'],'properties':r['choice'],'known_drop_kPa':r['known_common_pressure_Pa_after_nominal_balancing']/1000,'remaining_kPa':r['remaining_common_external_pressure_Pa']/1000,'header_void_m3':r['total_header_coolant_m3'],'header_steel_m3':r['total_header_shell_cap_steel_m3'],'radii_mm':{k:1000*v['geometry']['inner_radius_m'] for k,v in r['branches'].items()},'K_allowance':{k:v['equal_per_header_unknown_K_allowance_if_no_external_loss'] for k,v in r['branches'].items()}} for r in rows],indent=2),flush=True)
    return out
if __name__=='__main__':run()
