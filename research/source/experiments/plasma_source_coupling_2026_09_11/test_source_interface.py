"""Independent geometric/normalization checks, not experimental validation."""
from pathlib import Path
import importlib.util,json,math,hashlib
import numpy as np
from numpy.polynomial.legendre import leggauss
import pytest
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('surface',HERE/'make_surface_source.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
R=json.loads((HERE/'SOURCE_RESULT.json').read_text());P=json.loads((HERE/'PLASMA_SOURCE.json').read_text())
def test_point_kernel_against_exact_rectangular_solid_angle():
 a,b,d=1.3,.9,3.;x,w=leggauss(64);y=a*x[:,None];z=b*x[None,:]
 integral=np.sum(w[:,None]*w[None,:]*a*b*d/(4*np.pi*(d*d+y*y+z*z)**1.5))
 exact=math.atan(a*b/(d*math.sqrt(d*d+a*a+b*b)))/math.pi
 assert integral==pytest.approx(exact,rel=1e-12)
def test_Miller_volume_independent_quadrature():
 x,w=leggauss(128);rho=(x+1)/2;theta=np.pi*(x+1);ang=theta+m.delta*np.sin(theta);Rr=m.R0+m.a*rho[:,None]*np.cos(ang)
 J=(np.cos(ang)*np.cos(theta)+np.sin(ang)*(1+m.delta*np.cos(theta))*np.sin(theta));V=2*np.pi*m.a*m.a*m.kap*np.sum((w[:,None]/2)*(np.pi*w[None,:])*rho[:,None]*Rr*J)
 assert V==pytest.approx(np.mean([r['shape_volume_m3'] for r in R['replicates']]),rel=1e-6)
def test_first_wall_shadow_refinement_recorded():
 fine=[r for r in R['replicates'] if 'visibility_refinement_fraction' in r];assert len(fine)==2
 for r in fine:assert abs(r['visibility_refinement_fraction']/r['patch_fraction']-1)<.001
 assert all(r['patch_fraction']<r['unoccluded_patch_fraction'] for r in R['replicates'])
@pytest.mark.parametrize('bank',[0,1])
def test_bank_positions_directions_and_units(bank):
 b=np.load(HERE/'source_banks'/f'bank{bank}.npz');assert len(b['r'])==65536
 assert np.all(b['u'][:,0]>0) and np.allclose(np.linalg.norm(b['u'],axis=1),1,atol=1e-12)
 assert np.allclose(b['r'][:,0],-2.3+1e-7) and np.all(b['r'][:,1:]>=0)
 assert np.all(b['r'][:,1]<m.Y*100) and np.all(b['r'][:,2]<m.Z*100)
 assert abs(b['u'][:,0].mean()-np.mean([x['mean_mu'] for x in R['replicates']]))<.004
