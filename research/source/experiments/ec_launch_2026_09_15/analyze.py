"""Reproducible local EC seed/dispersion screen; no ray tracing or driven-current solve.
Original implementation MIT. Established equations credited in SOURCES.md.
Run: python analyze.py. Only NumPy/SciPy are required. No network or workstation calls.
"""
from __future__ import annotations
import hashlib,json,math,platform
from pathlib import Path
import numpy as np
from scipy.constants import c,e,m_e,epsilon_0,pi
from scipy.integrate import quad
from scipy.optimize import brentq
HERE=Path(__file__).resolve().parent
REST_KEV=m_e*c*c/(1000*e)

def positive(*xs):
    if any(not math.isfinite(float(v)) or float(v)<=0 for v in xs):
        raise ValueError('Expected finite positive physical parameters')

def characteristic(n:float,B:float)->tuple[float,float]:
    positive(n,B)
    return math.sqrt(n*e*e/(epsilon_0*m_e)),e*B/m_e

def reconstructed_profile(case:dict,p:dict,rho):
    r=np.asarray(rho,dtype=float)
    if np.any(~np.isfinite(r)) or np.any((r<0)|(r>1)):raise ValueError('rho outside [0,1]')
    nbar=case['ne_volume_average_m3'];ped=p['rho_ped_n'];alpha=p['alpha_n']
    ngw=case['Ip_A']/(pi*case['a_m']**2)*1e14
    nped=p['greenwald_fraction_ped']*ngw;nsep=p['greenwald_fraction_sep']*ngw
    n0=(3*nbar*(1+alpha)+nsep*(1+alpha)*(-2+ped+ped**2)-nped*((1+alpha)*(1+ped)+(alpha-2)*ped**2))/(3*ped**2)
    n=np.where(r<=ped,nped+(n0-nped)*np.maximum(1-(r/ped)**2,0)**alpha,nsep+(nped-nsep)*(1-r)/(1-ped))
    tped=p['rho_ped_T'];T0=case['Te_axis_keV']
    T=np.where(r<=tped,p['Te_ped_keV']+(T0-p['Te_ped_keV'])*np.maximum(1-(r/tped)**p['beta_T'],0)**p['alpha_T'],p['Te_sep_keV']+(p['Te_ped_keV']-p['Te_sep_keV'])*(1-r)/(1-tped))
    if np.any(n<=0) or np.any(T<=0):raise ValueError('Invalid positive reconstructed profile')
    return n,T,{'greenwald_m3':ngw,'n_ped_m3':nped,'n_sep_m3':nsep,'n_axis_m3':n0}

def hare(n:float,T:float,B:float,R:float,width:float,cos_theta:float)->dict:
    positive(n,T,B,R,width)
    if not 0<cos_theta<=1:raise ValueError('cos(theta) must lie in (0,1]')
    wp,wc=characteristic(n,B)
    argument=wp**2*width/(wc*c)*math.sqrt(T/(2*pi*REST_KEV))
    if argument<=1:raise ValueError('HARE logarithm does not give positive resonant energy')
    energy=T*math.log(argument);gamma=1+energy/REST_KEV;u=math.sqrt(gamma*gamma-1)
    ratio_R=1/(1+width/R*cos_theta)
    ratio_f=gamma+u*math.sqrt(1-ratio_R**2)
    Npar=(gamma-1/ratio_f)/u
    second_N=math.sqrt(1-(ratio_R/ratio_f)**2)
    def fun(x):return gamma-u*math.sqrt(max(0,1-(ratio_R/x)**2))-1/x
    def polynomial(x):return x*x-2*gamma*x+1+u*u*ratio_R*ratio_R
    root=brentq(polynomial,gamma+1e-12,gamma+2*u+1,xtol=1e-13)
    return {'frequency_GHz':wc*ratio_f/(2*pi*1e9),'N_parallel_magnitude':Npar,'f_over_fc':ratio_f,'resonant_energy_keV':energy,'gamma':gamma,'u_parallel_magnitude':u,'onset_R_m':R+width*cos_theta,'R_dep_over_R_onset':ratio_R,'log_argument':argument,'angular_frequency_units_used':True,'resonance_error':abs(gamma-Npar*u-1/ratio_f),'onset_error':abs(ratio_R/ratio_f-math.sqrt(1-Npar*Npar)),'N_formula_disagreement':abs(Npar-second_N),'independent_root_error':abs(root-ratio_f),'unsquared_resonance_at_root_error':abs(fun(root))}

def resonance_crossings(fc_GHz:float, f_GHz:float, Npar:float)->dict:
    """Exact u_perp=0 relativistic resonance intersections, no absorption solver."""
    positive(fc_GHz,f_GHz)
    if not math.isfinite(Npar) or abs(Npar)>=1:raise ValueError('Requires |Nparallel|<1')
    x=fc_GHz/f_GHz
    discriminant=x*x-(1-Npar*Npar)
    if discriminant < -1e-12:return {'real_crossings':False,'energies_keV':[],'u_parallel':[]}
    us=sorted([(x*Npar-math.sqrt(max(0,discriminant)))/(1-Npar*Npar),(x*Npar+math.sqrt(max(0,discriminant)))/(1-Npar*Npar)])
    for u in us:
        if abs(math.sqrt(1+u*u)-Npar*u-x)>1e-9:raise ValueError('Spurious squared resonance root')
    return {'real_crossings':True,'energies_keV':[(math.sqrt(1+u*u)-1)*REST_KEV for u in us],'u_parallel':us,'smaller_energy_keV':min((math.sqrt(1+u*u)-1)*REST_KEV for u in us)}

def stix(n:float,B:float,f_GHz:float):
    wp,wc=characteristic(n,B);w=f_GHz*2*pi*1e9
    positive(w)
    if abs(w-wc)/wc<1e-12:raise ValueError('Cold cyclotron pole')
    X=(wp/w)**2;Y=wc/w
    R=1-X/(1-Y);L=1-X/(1+Y)
    return (R+L)/2,(R-L)/2,1-X

def perpendicular_roots(n:float,B:float,f_GHz:float,Npar:float):
    S,D,P=stix(n,B,f_GHz);q=Npar*Npar
    coeff=[S,-((S+P)*(S-q)-D*D),P*((S-q)**2-D*D)]
    return np.roots(coeff),coeff

def cold_o_target(n:float,B:float,f_GHz:float,Npar:float)->dict:
    """Select the branch continuous from perpendicular O at Npar=0.
    Local dispersion ONLY, not global wave accessibility or a ray trajectory.
    """
    S,D,P=stix(n,B,f_GHz)
    prev=complex(P);minsep=math.inf
    for x in np.linspace(0,abs(Npar),257):
        roots,_=perpendicular_roots(n,B,f_GHz,float(x))
        chosen=roots[np.argmin(np.abs(roots-prev))];prev=complex(chosen)
        minsep=min(minsep,abs(roots[1]-roots[0]))
        if abs(prev.imag)>1e-9:return {'locally_propagating':False,'reason':'Complex continued root','n_perp_squared':None}
    value=prev.real
    if value<=0:return {'locally_propagating':False,'reason':'Nonpositive O-like n_perp squared','n_perp_squared':value}
    v=math.sqrt(value);M=np.array([[S-Npar*Npar,-1j*D,v*Npar],[1j*D,S-value-Npar*Npar,0],[v*Npar,0,P-value]],complex)
    _,_,vh=np.linalg.svd(M);vec=vh.conj().T[:,-1]
    return {'locally_propagating':True,'reason':'Positive continuous O-like local cold root','n_perp_squared':value,'n_perp_magnitude':v,'total_index':math.sqrt(value+Npar*Npar),'local_wavevector_angle_to_B_deg':math.degrees(math.atan2(v,abs(Npar))),'normalized_matrix_determinant_abs':float(abs(np.linalg.det(M))/(max(1,np.linalg.norm(M))**3)),'polarization_matrix_residual':float(np.linalg.norm(M@vec)),'branch_min_separation':float(minsep),'global_accessibility_proven':False,'cold_electron_only':True}

def run():
    raw=(HERE/'INPUTS.json').read_bytes();inputs=json.loads(raw)
    admission=json.loads((HERE/'ADMISSION.json').read_bytes());p=inputs['profile_parameters']
    cases={};rows=[];profiles={}
    for name,case in inputs['candidate_parameters'].items():
        density=lambda r:float(reconstructed_profile(case,p,r)[0]);temp=lambda r:float(reconstructed_profile(case,p,r)[1])
        nmean=quad(lambda r:2*r*density(r),0,1,points=[p['rho_ped_n']],epsabs=1e8,epsrel=1e-12)[0]
        tmean=quad(lambda r:2*r*temp(r),0,1,points=[p['rho_ped_T']],epsabs=1e-11,epsrel=1e-12)[0]
        rr=np.linspace(0,1,201);nn,tt,info=reconstructed_profile(case,p,rr)
        profiles[name]={'rho_geometric':rr.tolist(),'ne_m3':nn.tolist(),'Te_keV':tt.tolist(),'construction':'Reconstructed from equations, not exported original solver arrays'}
        wp0,wc0=characteristic(info['n_axis_m3'],case['B0_T'])
        req=case['Ip_A']*case['auxiliary_current_fraction']/1e3/case['credited_drive_MW']
        cases[name]={**case,**info,'plasma_frequency_axis_GHz':wp0/(2*pi*1e9),'cold_cyclotron_axis_GHz':wc0/(2*pi*1e9),'required_effective_kA_per_MW':req,'profile_relative_density_mean_error':(nmean/case['ne_volume_average_m3']-1),'profile_temperature_mean_error_keV':tmean-case['Te_volume_average_keV'],'profile_array_roundtrip_with_original_not_available':True}
        for rho in admission['fixed_execution']['rho_values']:
            n,T,_=reconstructed_profile(case,p,rho);n,T=float(n),float(T)
            R=case['R0_m']-case['a_m']*rho;B=case['B0_T']*case['R0_m']/R
            for fraction in admission['fixed_execution']['absorption_width_fractions_a']:
                for cos_theta in admission['fixed_execution']['cos_inclinations']:
                    row={'case':name,'rho_geometric':rho,'R_HFS_target_m':R,'B_toroidal_proxy_T':B,'ne_local_m3':n,'Te_local_keV':T,'width_over_a':fraction,'cos_theta':cos_theta,'method':'HARE analytic seed plus local cold-electron dispersion; NOT ray tracing'}
                    try:
                        h=hare(n,T,B,R,case['a_m']*fraction,cos_theta);row.update(h)
                        row['local_cold_dispersion']=cold_o_target(n,B,h['frequency_GHz'],h['N_parallel_magnitude'])
                        row['seed_admitted_to_future_ray_test']=row['local_cold_dispersion']['locally_propagating']
                        row['required_local_zeta_if_entire_current_at_this_density_temperature']=.033*req*case['R0_m']*(n/1e20)/T
                        row['density_only_ordinary_cutoff_ceiling_passes']=h['frequency_GHz']>cases[name]['plasma_frequency_axis_GHz']
                    except ValueError as exc:
                        row.update(seed_admitted_to_future_ray_test=False,rejection_reason=str(exc))
                    row.update(achieved_current_MA=None,launch_location_m=None,launch_angles_deg=None,physical_validation=False)
                    rows.append(row)
        probes=[]
        for frequency in admission['fixed_execution']['fixed_frequency_checks_GHz']:
            cold_R=case['R0_m']*wc0/(frequency*2*pi*1e9)
            n,T,_=reconstructed_profile(case,p,0.0)
            h=hare(float(n),float(T),case['B0_T'],case['R0_m'],.2*case['a_m'],1)
            ratio=frequency/cases[name]['cold_cyclotron_axis_GHz']
            N=(h['gamma']-1/ratio)/h['u_parallel_magnitude']
            u=h['u_parallel_magnitude'];dF_du=u/h['gamma']-N
            probes.append({'frequency_GHz':frequency,'cold_fundamental_R_m':cold_R,'cold_fundamental_rho_HFS_proxy':(case['R0_m']-cold_R)/case['a_m'],'axis_resonance_N_parallel_for_nominal_tail':N,'nominal_tail_is_minimum_energy_crossing':dF_du<0,'resonance_crossings':resonance_crossings(cases[name]['cold_cyclotron_axis_GHz'],frequency,N),'nominal_tail_lower_crossing_threshold_GHz':h['gamma']*cases[name]['cold_cyclotron_axis_GHz'],'global_accessibility_proven':False})
        cases[name]['fixed_frequency_probes']=probes
    result={'schema':'fusion.ec-analytic-screen.v1','date':'2026-09-15','inputs_sha256':hashlib.sha256(raw).hexdigest(),'admission_sha256':hashlib.sha256((HERE/'ADMISSION.json').read_bytes()).hexdigest(),'cases':cases,'profiles':profiles,'all_local_evaluations':rows,'evaluation_count':len(rows),'ray_runs':0,'current_drive_solver_runs':0,'new_PROCESS_optimizations':0,'new_neutron_runs':0,'achieved_current_drive_validated':False,'live_site_updated':False,'upstream_method_attribution':'E. Poli et al. HARE2018; N.A. Lopez, A. Alieva, S.A.M. McNamara, X. Zhang2025 published / arXiv v2 2026; UKAEA PROCESS profiles; Stix cold dielectric as presented by Richard Fitzpatrick','limitations':['No solved magnetic equilibrium, Shafranov shift or poloidal field.','The radial coordinate is geometric r/a, not a mapped normalized poloidal flux.','No actual rays, absorption fraction, achieved driven current, profile stability or control allocation has been calculated.','HARE width/inclination choices are sensitivity scenarios, not confidence limits.','Cold-electron branch existence at a target does not establish a connecting ray, boundary accessibility or hot-wave behavior.','Original full profile arrays were inaccessible; reconstructed scalar moments are checked instead.','Current-drive requirements are retained, not certified by passing the frequency screen.'],'environment':{'python':platform.python_version(),'numpy':np.__version__}}
    (HERE/'RESULTS.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')
    return result
if __name__=='__main__':
    r=run()
    print(json.dumps({'counts':{'local_evaluations':r['evaluation_count'],'locally_allowed':sum(x['seed_admitted_to_future_ray_test'] for x in r['all_local_evaluations']),'ray_runs':0},'profiles':{k:{s:v[s] for s in ['n_axis_m3','plasma_frequency_axis_GHz','cold_cyclotron_axis_GHz','profile_temperature_mean_error_keV']} for k,v in r['cases'].items()}},indent=2))
