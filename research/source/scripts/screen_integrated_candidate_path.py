#!/usr/bin/env python3
"""Reproducible screening calculation for the current PR42 integrated candidate path.

This is deliberately NOT a reactor simulation. It combines authenticated PR42 power/CS
numbers with explicitly labelled external HCPB/EC design targets to test whether a
worthwhile same-design closure experiment exists.
"""
from __future__ import annotations
import json, math

NET=[-122.3116741938922,-125.47970455427273,400.0224919213392,400.0224919213392,400.0224919213392,-122.3116741938922,-122.3116741938922]
HCD=[0.,0.,-362.11023874037596,-362.11023874037596,-362.11023874037596,0.,0.]
DUR=[500.,191.34631513215254,10.,7403.586975520301,191.34631513215254,1800.]
ETA_EC_BASE=.5; FWBL_PUMP_ELEC=266.8510551050698; PUMP_ELEC_EFF=.87
FWBL_HEAT=2595.036370284008; AVAIL=.8
HCPB_REFERENCE_THERMAL=2400.; HCPB_HIGH_CIRC_MECH=90.
RI0=2.089379293807715; DR0=.5382769798192093; J0=18.5e6; B0=12.68509
FSTEEL0=.7150556917712795; POISSON=.3; JCRIT_BOP0=29.107769109155677e6
A_TURN=.002162162162162162; TURN_ASPECT=3.1818181818181817; CORNER=.003
RESID=240e6; A0=.00089; PARIS=6.5e-13; PARIS_M=3.5; WALKER=.436; KIC=200.; SFV=SFR=2.; SFF=1.5

def integrate(v,d): return math.fsum(.5*(a+b)*dt for a,b,dt in zip(v,v[1:],d))

def power_case(eta_ec,dwell_s,circ_mech_mw,availability=.8):
    if not (0<eta_ec<=1 and dwell_s>=0 and circ_mech_mw>=0 and 0<availability<=1): raise ValueError
    d=DUR.copy(); d[-1]=dwell_s
    pump_elec=circ_mech_mw/PUMP_ELEC_EFF; saving=FWBL_PUMP_ELEC-pump_elec
    n=[x+h*(ETA_EC_BASE/eta_ec-1) for x,h in zip(NET,HCD)]
    for i in (2,3,4): n[i]+=saving
    avg=integrate(n,d)/math.fsum(d)
    return {'eta_ec_wallplug_to_injector':eta_ec,'dwell_s':dwell_s,'circulating_mechanical_mw':circ_mech_mw,
            'circulating_electric_mw':pump_elec,'flat_top_net_mw':n[3],'cycle_average_net_mw':avg,
            'availability_adjusted_net_mw':availability*avg}

def eta_for_target(target_mw,dwell_s,circ_mech_mw,availability=.8):
    lo,hi=.3,.9
    if power_case(hi,dwell_s,circ_mech_mw,availability)['availability_adjusted_net_mw']<target_mw:return None
    for _ in range(80):
        mid=(lo+hi)/2
        if power_case(mid,dwell_s,circ_mech_mw,availability)['availability_adjusted_net_mw']>=target_mw:hi=mid
        else:lo=mid
    return hi

def hoop_stress(ri,dr,j,b,fsteel):
    ro=ri+dr; alpha=ro/ri; eps=1.
    K=j*ri*(alpha*b)/(alpha-1); M=j*ri*b/(alpha-1)
    s=(K*(2+POISSON)/(3*(alpha+1))*(alpha**2+alpha+1+alpha**2/eps**2-eps*(1+2*POISSON)*(alpha+1)/(2+POISSON))
       -M*(3+POISSON)/8*(alpha**2+1+alpha**2/eps**2-(1+3*POISSON)/(3+POISSON)*eps**2))
    return s/fsteel

def conduit_thickness(fsteel):
    dz=math.sqrt(A_TURN/TURN_ASPECT); dr=TURN_ASPECT*dz
    radius=-((dr-dz)/math.pi)+math.sqrt(((dr-dz)/math.pi)**2+(dr*dz-(4-math.pi)*CORNER**2-A_TURN*fsteel)/math.pi)
    return dz/2-radius

def sif_pair(stress_mpa,t,w,a,c):
    result=[]
    for phi in (math.pi/2,0.):
        at=a/t; at2=at*at; sp=math.sin(phi); cp2=math.cos(phi)**2
        if a<=c:
            ac=a/c; q=1+1.464*ac**1.65; m1=1.13-.09*ac; m2=-.54+.89/(.2+ac); m3=.5-1/(.65+ac)+14*(1-ac)**24
            g=1+(.1+.35*at2)*(1-sp)**2; ff=(ac*ac*cp2+sp*sp)**.25
        else:
            ca=c/a; q=1+1.464*ca**1.65; m1=math.sqrt(ca)*(1+.04*ca); m2=.2*ca**4; m3=-.11*ca**4
            g=1+(.1+.35*ca*at2)*(1-sp)**2; ff=(ca*ca*sp*sp+cp2)**.25
        result.append(stress_mpa*((m1+m2*at2+m3*at**4)*g*ff*math.sqrt(1/math.cos(math.sqrt(at)*math.pi*c/(2*w))))*math.sqrt(math.pi*a/q))
    return result

def cycles_to_fracture(stress_pa,t):
    stress=stress_pa/1e6; residual=RESID/1e6; r=residual/(stress+residual)
    exponent=-PARIS_M*(WALKER-1); cr=PARIS/(1-r)**exponent
    a=A0; c=3*A0; kmax=0.; pulses=0.; delta=1e-4
    while a<=t/SFV and c<=t/SFR and kmax<=KIC/SFF:
        ka,kc=sif_pair(stress,t,t,a,c); kmax=max(ka,kc); dn=delta/(cr*kmax**PARIS_M)
        a+=delta*(ka/kmax)**PARIS_M; c+=delta*(kc/kmax)**PARIS_M; pulses+=dn
    return pulses/2

def fsteel_max_from_bop(dr):
    j=J0*DR0/dr
    return min(.95,1-j*(1-FSTEEL0)/(.7*JCRIT_BOP0))

def fatigue_screen(dr):
    f=fsteel_max_from_bop(dr); j=J0*DR0/dr; ri=RI0-.5*(dr-DR0)
    stress=hoop_stress(ri,dr,j,B0,f); t=conduit_thickness(f)
    return {'dr_cs_m':dr,'fsteel':f,'j_overall_ma_m2':j/1e6,'hoop_stress_mpa':stress/1e6,
            'conduit_mm':t*1e3,'bop_current_density_ratio':j/(JCRIT_BOP0*(1-f)/(1-FSTEEL0)),
            'cycles':cycles_to_fracture(stress,t)}

def dr_for_cycles(target):
    lo,hi=DR0,1.5
    for _ in range(55):
        mid=(lo+hi)/2
        if fatigue_screen(mid)['cycles']>=target:hi=mid
        else:lo=mid
    return fatigue_screen(hi)

def build_result():
    assert abs(cycles_to_fracture(437993444.0663996,conduit_thickness(FSTEEL0))-5736.97861814937)<1e-6
    scaled_mech=HCPB_HIGH_CIRC_MECH*FWBL_HEAT/HCPB_REFERENCE_THERMAL
    return {'schema':'fusion-solution-set.integrated-candidate-screen.v1','scaled_hcpb_circulating_mechanical_mw':scaled_mech,
      'power':{'baseline':power_case(.5,1800,FWBL_PUMP_ELEC*PUMP_ELEC_EFF),
        'conservative_hcpb_50pct_ec_600s':power_case(.5,600,scaled_mech),
        'conservative_hcpb_55pct_ec_600s':power_case(.55,600,scaled_mech),
        'conservative_hcpb_60pct_ec_600s':power_case(.6,600,scaled_mech),
        'ec_efficiency_for_400mw_avg':eta_for_target(400,600,scaled_mech)},
      'cs':{'baseline_cycles':cycles_to_fracture(437993444.0663996,conduit_thickness(FSTEEL0)),
        'screen_20000':dr_for_cycles(20000),'screen_40000':dr_for_cycles(40000)},
      'boundaries':['Power screen holds PR42 gross generation, fusion power and non-pump/non-EC loads fixed.',
        '90 MW HCPB circulating power is external design evidence, scaled linearly with thermal load; it is not a source-matched PR42 calculation.',
        'EC efficiency is PROCESS wall-plug-to-injector efficiency; 60% remains a future-system target, not demonstrated plant performance.',
        'CS screen preserves first-order ampere-turns and B field, uses PROCESS hoop/turn/fatigue equations, but is not a full PF equilibrium or superconducting reoptimization.',
        'No tritium inventory, component reliability, remote maintenance, disruption tolerance, or economics closure is established.']}

def main(): print(json.dumps(build_result(),indent=2,sort_keys=True))
if __name__=='__main__': main()
