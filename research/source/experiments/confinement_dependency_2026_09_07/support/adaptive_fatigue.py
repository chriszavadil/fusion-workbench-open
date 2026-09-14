"""Runtime-only, event-located integration of the existing PROCESS fatigue law.
No upstream source file is edited. This is a numerical implementation comparison,
not a new constitutive model, qualified fatigue life, or safety determination.
"""
import math
import numpy as np
from scipy.integrate import solve_ivp
from process.models.cs_fatigue import CsFatigue
NATIVE=CsFatigue.ncycle

def adaptive_ncycle(self,max_hoop_stress,residual_stress,t_crack_vertical,dz_cs_turn_conduit,dr_cs_turn_conduit):
    p=self.data.cs_fatigue
    stress=max_hoop_stress/1e6; residual=residual_stress/1e6
    a0=float(t_crack_vertical); c0=3*a0
    alim=dz_cs_turn_conduit/p.sf_vertical_crack
    clim=dr_cs_turn_conduit/p.sf_radial_crack
    limit=p.fracture_toughness/p.sf_fast_fracture
    vals=(stress,residual,a0,alim,clim,limit,p.paris_coefficient,p.paris_power_law)
    if not all(math.isfinite(x) for x in vals):raise ValueError('Nonfinite fatigue input')
    if min(stress,a0,alim,clim,limit,p.paris_coefficient)<=0:raise ValueError('Nonpositive fatigue input')
    if a0>=alim or c0>=clim:return 0.,c0
    def K(a,c):
        ans=self.surface_stress_intensity_factor(stress,dz_cs_turn_conduit,dr_cs_turn_conduit,a,c,np.array([np.pi/2,0.]))
        if not np.all(np.isfinite(ans)) or np.min(ans)<=0:raise ValueError('Invalid stress-intensity factor')
        return ans
    if max(K(a0,c0))>=limit:return 0.,c0
    ratio=residual/(stress+residual)
    coeff=p.paris_coefficient/(1-ratio)**(-p.paris_power_law*(p.walker_coefficient-1))
    def rhs(a,y):
        ka,kc=K(a,y[0])
        return [(kc/ka)**p.paris_power_law,1/(2*coeff*ka**p.paris_power_law)]
    def radial(a,y):return clim-y[0]
    def fracture(a,y):return limit-max(K(a,y[0]))
    radial.terminal=fracture.terminal=True
    radial.direction=fracture.direction=-1
    sol=solve_ivp(rhs,(a0,alim),[c0,0.],events=[radial,fracture],method='DOP853',rtol=1e-9,atol=[1e-12,1e-6])
    if not sol.success:raise RuntimeError(sol.message)
    cycles=float(sol.y[1,-1])
    if not math.isfinite(cycles) or cycles<0:raise ValueError('Invalid integrated cycles')
    return cycles,c0

def install():
    if CsFatigue.ncycle is not NATIVE:raise RuntimeError('Unexpected preexisting fatigue patch')
    CsFatigue.ncycle=adaptive_ncycle

def inspect_case(stress,conduit):
    from types import SimpleNamespace
    from process.data_structure.cs_fatigue_variables import CSFatigueData
    obj=SimpleNamespace(data=SimpleNamespace(cs_fatigue=CSFatigueData()),surface_stress_intensity_factor=CsFatigue.surface_stress_intensity_factor)
    args=(obj,stress,240e6,.00089,conduit,conduit)
    return {'native_cycles':NATIVE(*args)[0],'adaptive_cycles':adaptive_ncycle(*args)[0]}
if __name__=='__main__':
    import json
    print(json.dumps(inspect_case(659999225.25370133,.0063104538380405924)))
