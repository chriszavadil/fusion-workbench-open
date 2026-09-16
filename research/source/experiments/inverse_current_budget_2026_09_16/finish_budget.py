"""Read the restored in-memory fields; preserve signs and do not fit current budgets. MIT."""
from pathlib import Path
import json,time,hashlib
import numpy as np
from scipy.integrate import simpson
from scipy.constants import mu_0
from OpenFUSIONToolkit.TokaMaker.bootstrap import redl_bootstrap

def finish(s):
 gs=s['gs'];x=s['qn'];out=s['out'];record=s['record'];kin=s['kin'];F=s['F'];Pp=s['Pprime'];Fp=s['Fprime']
 # Installed Redl workflow uses increasing outward flux with positive psi_bounds span.
 # TokaMaker absolute flux decreases outward in psi_convention0. Convert derivatives, not output signs.
 d={k:-v for k,v in s['der'].items()};assert s['psirange']<0 and gs.psi_convention==0
 ne,ni,Te,Ti,Z=[s[k] for k in ['ne','ni','Te','Ti','Z']]
 jB,coeff=redl_bootstrap(psi_N=x,Te=Te,Ti=Ti,ne=ne,ni=ni,pe=s['arrays']['pe_Pa'],pi=s['arrays']['pi_Pa'],Zeff=Z,R=s['rg']['<R>'],q=np.abs(s['q']),eps=s['eps'],fT=1-s['fc'],I_psi=F,dT_e_dpsi=d['Te_eV'],dT_i_dpsi=d['Ti_eV'],dn_e_dpsi=d['ne_m3'],dn_i_dpsi=d['ni_m3'],dp_dpsi=d['pe_Pa']+d['pi_Pa'],ln_lambda_e=s['ln_e'],ln_lambda_ii=s['ln_i'],formula_form='jboot1',use_sign_q=False,nu_e_star_override=s['nue'],nu_i_star_override=s['nui'])
 if not np.isfinite(jB).all():raise ValueError('Bootstrap output is not finite; no replacement zeros')
 ev=gs.get_field_eval('B');curves=[gs.trace_surf(float(v),nresample=256) for v in x];mid=[(p+np.roll(p,-1,axis=0))/2 for p in curves];B=ev.eval(np.concatenate(mid)).reshape(len(x),256,3)
 total=[];boot=[];area=[];ampere=[];b2=[];legacy=[];shell_records=[]
 for i,(curve,field) in enumerate(zip(curves,B)):
  delta=np.roll(curve,-1,axis=0)-curve;r=mid[i][:,0];dl=np.linalg.norm(delta,axis=1);bp=np.linalg.norm(field[:,[0,2]],axis=1);weight=dl/(r*bp)
  if np.min(bp)<=0 or np.max(abs(field[:,1]*r/F[i]-1))>1e-5:raise ValueError('B-field component or unit convention mismatch')
  bsquare=np.sum((field**2).sum(axis=1)*dl/bp)/np.sum(dl/bp);b2.append(bsquare);area.append(np.sum(weight)*abs(s['psirange']))
  jtotal=F[i]*Fp[i]/(mu_0*r)+r*Pp[i];jbs=jB[i]/bsquare*F[i]/r
  total.append(np.sum(jtotal*weight)*abs(s['psirange']));boot.append(np.sum(jbs*weight)*abs(s['psirange']))
  legacy.append(jB[i]*s['rg']['<R>'][i]/F[i]*area[-1])
  ampere.append(-np.sum(field[:,0]*delta[:,0]+field[:,2]*delta[:,1])/mu_0)
  shell_records.append({'psi_norm':x[i],'jtotal_area_average_A_m2':total[-1]/area[-1],'jbootstrap_parallel_projection_area_average_A_m2':boot[-1]/area[-1]})
 total=np.asarray(total);boot=np.asarray(boot);area=np.asarray(area);residual=total-boot
 it=float(simpson(total,x=x));ib=float(simpson(boot,x=x));ig=float(ampere[-1]-ampere[0]);coarse=float(simpson(boot[::2],x=x[::2]));opposite=float(simpson(np.maximum(-residual,0),x=x))
 result={'total_current_in_tested_shell_A':it,'bootstrap_current_in_tested_shell_A':ib,'remaining_current_in_tested_shell_A':it-ib,'countercurrent_lower_bound_in_shell_A':opposite,'positive_remaining_current_in_shell_A':float(simpson(np.maximum(residual,0),x=x)),'same_shell_ampere_current_A':ig,'ampere_relative_error':it/ig-1,'bootstrap_201_vs_401_relative_change':coarse/ib-1,'native_approximate_projection_integral_A':float(simpson(legacy,x=x)),'tested_poloidal_flux_interval':[float(x[0]),float(x[-1])],'complete_reactor_bootstrap_integral':False,'uncomputed_axis_edge_current_A':float(gs.get_globals()[0]-ig),'bootstrap_rescale_used':False,'inductive_rescale_used':False}
 allowed=kin['reference_current'];result['original_inductive_total_A']=allowed['plasma_current']*allowed['f_c_plasma_inductive'];result['original_EC_total_A']=allowed['plasma_current']*allowed['f_c_plasma_auxiliary'];result['original_bootstrap_total_A']=allowed['plasma_current']*allowed['f_c_plasma_bootstrap']
 # Optimistic necessary drive: allow ALL original inductive current in the tested shell.
 result['EC_shell_lower_bound_with_original_inductive_total_A']=max(0,result['positive_remaining_current_in_shell_A']-result['original_inductive_total_A'])
 result['no_countercurrent_profile_possible_on_proxy']=opposite<1e-6
 record.update(result=result,completed=True,sign_convention='Redl outward-positive poloidal flux = -TokaMaker absolute flux for psi_convention0; physical toroidal current checked via minus ccw RZ Ampere circulation',runtime_s=time.monotonic()-s['start'])
 record['passed_numerical_checks']=abs(result['ampere_relative_error'])<.01 and abs(result['bootstrap_201_vs_401_relative_change'])<.01
 record['assumed_parallel_current_projection']=True;record['full_current_profile_or_equilibrium_self_consistency_solved']=False
 arrays={**s['arrays'],'psi_norm':x,'jB_Redl':jB,'jB_raw_unconverted_sign_diagnostic':s['jB'],'F':F,'Fprime':Fp,'Pprime':Pp,'q':s['q'],'trapped_fraction':1-s['fc'],'nu_e_star':s['nue'],'nu_i_star':s['nui'],'area_per_normalized_flux_m2':area,'total_A_per_normalized_flux':total,'bootstrap_A_per_normalized_flux':boot,'residual_A_per_normalized_flux':residual,'enclosed_current_ampere_A':np.array(ampere),'B2_contour_average':np.array(b2),'native_projection_A_per_normalized_flux':np.array(legacy)}
 np.savez_compressed(out/'CURRENT_FIELDS.npz',**arrays);(out/'PROFILES.json').write_text(json.dumps({'shells':shell_records,'coefficients':coeff},default=s['plain'] if 'plain' in s else lambda v:v.tolist() if isinstance(v,np.ndarray) else v.item(),indent=2)+'\n')
 record['fields_sha256']=hashlib.sha256((out/'CURRENT_FIELDS.npz').read_bytes()).hexdigest();(out/'RESULT.json').write_text(json.dumps(record,indent=2,default=lambda v:v.tolist() if isinstance(v,np.ndarray) else v.item())+'\n');print('CURRENT_BUDGET_RESULT',json.dumps(result),flush=True);return record
