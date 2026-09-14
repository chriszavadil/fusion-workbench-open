"""Candidate-linked direct-view source; established point-kernel physics. MIT."""
from pathlib import Path
import json,math,hashlib
import numpy as np
from scipy.stats import qmc
HERE=Path(__file__).resolve().parent
A=json.loads((HERE/'ADMISSION.json').read_text());P=json.loads((HERE/'PLASMA_SOURCE.json').read_text());F=json.loads((HERE/'LOCAL_INPUT.json').read_text())
G=P['geometry'];R0=G['rmajor'];a=G['rminor'];kap=G['kappa'];delta=G['triang'];b=a+.25
h=F['header'];Z=h['length_each_m']+2*h['wall_m'];Y=F['module_volume_m3']/F['blanket_depth_m']/Z
RW=R0+b;area=Y*Z

def wall(z):
 theta=np.arcsin(np.clip(z/(kap*b),-1,1));out=R0+b*np.cos(theta+delta*np.sin(theta));ins=R0+b*np.cos(np.pi-theta+delta*np.sin(theta))
 slope=-np.sin(theta+delta*np.sin(theta))*(1+delta*np.cos(theta))/(kap*np.cos(theta))
 return ins,out,slope

def visible(source,target,nseg):
 good=np.ones(len(source),bool);d=target-source
 for t in np.linspace(0,1,nseg+1)[:-1]:
  p=source+t*d;r=np.hypot(p[:,0],p[:,1]);lo,hi,_=wall(p[:,2]);good &= (abs(p[:,2])<kap*b)&(r>lo-1e-9)&(r<hi+1e-9)
 return good

def sample(seed,power,refine=False):
 U=qmc.Sobol(5,scramble=True,seed=seed).random_base2(power);rho=np.sqrt(U[:,0]);th=2*np.pi*U[:,1];phi=2*np.pi*U[:,2];ang=th+delta*np.sin(th)
 radius=R0+a*rho*np.cos(ang);zz=kap*a*rho*np.sin(th);src=np.column_stack((radius*np.cos(phi),radius*np.sin(phi),zz))
 jac=radius*(np.cos(ang)*np.cos(th)+np.sin(ang)*(1+delta*np.cos(th))*np.sin(th));assert np.all(jac>0)
 emission=np.interp(rho,P['rho'],P['DT_emission_m3_s']);weight=emission*jac
 y=(U[:,3]-.5)*Y;z=(U[:,4]-.5)*Z;_,rt,slope=wall(z);ph=y/RW;c=np.cos(ph);s=np.sin(ph);norm=np.sqrt(1+slope*slope);target=np.column_stack((rt*c,rt*s,z))
 d=target-src;distance=np.linalg.norm(d,axis=1);direction=d/distance[:,None];mu=(direction[:,0]*c+direction[:,1]*s-direction[:,2]*slope)/norm
 cross=area*(rt/RW)*norm*np.maximum(mu,0)/(4*np.pi*distance**2);vis=visible(src,target,A['sampling']['visibility_segments']);w=weight*cross*vis
 localdir=np.column_stack((mu,-direction[:,0]*s+direction[:,1]*c,(slope*(direction[:,0]*c+direction[:,1]*s)+direction[:,2])/norm))
 assert np.allclose(np.linalg.norm(localdir,axis=1),1,atol=1e-12)
 localpos=np.column_stack((np.full(len(y),-100*(F['armour_m']+F['first_wall_m'])+1e-7),100*(y+Y/2),100*(z+Z/2)))
 info={'seed':seed,'pairs':len(w),'patch_fraction':float(w.sum()/weight.sum()),'unoccluded_patch_fraction':float(np.sum(weight*cross)/weight.sum()),'effective_pairs':float(w.sum()**2/np.sum(w*w)),'mean_mu':float(np.sum(w*mu)/w.sum()),'shape_volume_m3':float(2*np.pi**2*a*a*kap*jac.mean()),'shape_DT_rate_s':float(2*np.pi**2*a*a*kap*weight.mean())}
 if refine:
  fine=visible(src,target,2*A['sampling']['visibility_segments']);info['visibility_refinement_fraction']=float(np.sum(weight*cross*fine)/weight.sum());info['visibility_changed_pairs']=int(np.sum(fine!=vis))
 return {'w':w/weight.sum(),'r':localpos,'u':localdir,'birth':src*100,'target':target*100},info

def run():
 records=[];allsets=[]
 for i in range(A['sampling']['scrambles']):
  arrays,row=sample(A['sampling']['seed_base']+i,A['sampling']['sobol_power'],refine=i<2);records.append(row);allsets.append(arrays);print(json.dumps(row),flush=True)
 output=HERE/'source_banks';output.mkdir(exist_ok=False);rays=[];summaries=[]
 for group in range(2):
  batches=allsets[group*4:(group+1)*4];merged={k:np.concatenate([x[k] for x in batches]) for k in batches[0]};weights=merged['w'];cdf=np.cumsum(weights);cdf/=cdf[-1];count=A['sampling']['bank_particles_each'];rng=np.random.default_rng(A['sampling']['seed_base']+100+group)
  ids=np.searchsorted(cdf,(np.arange(count)+rng.random())/count);ids=ids[rng.permutation(count)];bank={k:merged[k][ids] for k in ['r','u','birth','target']}
  assert np.all(bank['u'][:,0]>0);np.savez_compressed(output/f'bank{group}.npz',**bank)
  hist,edges=np.histogram(bank['u'][:,0],bins=np.linspace(0,1,21));summaries.append({'bank':group,'count':count,'mean_mu':float(bank['u'][:,0].mean()),'mu_bin_edges':edges.tolist(),'mu_counts':hist.tolist(),'unique_resampled_pairs':int(len(np.unique(ids)))})
  if group==0:rays=[{'birth_cm':b.tolist(),'target_cm':t.tolist(),'direction_local':u.tolist()} for b,t,u in zip(bank['birth'][:64],bank['target'][:64],bank['u'][:64])]
 fractions=np.array([r['patch_fraction'] for r in records]);mean=float(fractions.mean());se=float(fractions.std(ddof=1)/math.sqrt(len(fractions)))
 result={'schema':'fusion.direct-surface-source-result.v1','configuration':'r838 parameterized direct-view proxy','admission_sha256':hashlib.sha256((HERE/'ADMISSION.json').read_bytes()).hexdigest(),'plasma_profile_sha256':hashlib.sha256((HERE/'PLASMA_SOURCE.json').read_bytes()).hexdigest(),'replicates':records,'banks':summaries,'patch_fraction':mean,'patch_fraction_scramble_se':se,'normalization_DT_rate_s':P['DT_neutrons_per_second'],'normalized_patch_neutrons_s':mean*P['DT_neutrons_per_second'],'planar_patch_area_m2':area,'parameterized_volume_difference_percent':100*(np.mean([r['shape_volume_m3'] for r in records])/G['vol_plasma']-1),'source_shape_total_rate_ratio_to_PROCESS':float(np.mean([r['shape_DT_rate_s'] for r in records])/P['DT_neutrons_per_second']),'source_rays':rays,'geometry':G,'local_size_cm':[100*F['blanket_depth_m'],100*Y,100*Z],'first_wall_major_outboard_m':RW,'limits':A['limits'],'full_reactor_TBR':False,'physical_validation':False}
 (HERE/'SOURCE_RESULT.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');return result
if __name__=='__main__':run()
