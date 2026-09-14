#!/usr/bin/env python3
"""Material-matched HCPB *slab* breeding screen for the PR42 PROCESS baseline.

This deliberately does NOT claim whole-plant geometry matching. It answers a narrower
question first: does the exact PROCESS blanket volume recipe have enough intrinsic
breeding headroom in an infinite transverse slab to justify a detailed tokamak model?
"""
from __future__ import annotations
import argparse, json, math, os
from pathlib import Path
import numpy as np
import openmc

# Frozen from the hash-verified PR42 baseline MFILE / PROCESS HCPB relation.
VOL = {"li4sio4":0.375, "tibe12":0.375, "eurofer":0.09705, "helium_coolant":0.05295, "purge_gas":0.10}
THICKNESS_CM = (70.0, 85.0, 100.0)  # PROCESS inboard, mean, outboard blanket build
ENRICHMENT = (40.0, 50.0, 60.0, 70.0, 80.0, 90.0)
FIRST_WALL_CM = 1.8


def materials(enrichment: float):
    f=enrichment/100
    ceramic=openmc.Material(name='Li4SiO4'); ceramic.add_nuclide('Li6',4*f,'ao'); ceramic.add_nuclide('Li7',4*(1-f),'ao'); ceramic.add_element('Si',1,'ao'); ceramic.add_element('O',4,'ao'); ceramic.set_density('g/cm3',2.4)
    mult=openmc.Material(name='TiBe12'); mult.add_element('Ti',1,'ao'); mult.add_element('Be',12,'ao'); mult.set_density('g/cm3',2.26)
    # Transparent, documented reduced EUROFER proxy for this screening gate only.
    steel=openmc.Material(name='reduced_EUROFER_proxy'); steel.add_element('Fe',0.89,'wo'); steel.add_element('Cr',0.09,'wo'); steel.add_element('W',0.01,'wo'); steel.add_element('Mn',0.009,'wo'); steel.add_element('Ta',0.001,'wo'); steel.set_density('g/cm3',7.8)
    he=openmc.Material(name='He'); he.add_element('He',1); he.set_density('g/cm3',0.005)
    blanket=openmc.Material.mix_materials([ceramic,mult,steel,he],[VOL['li4sio4'],VOL['tibe12'],VOL['eurofer'],VOL['helium_coolant']+VOL['purge_gas']],percent_type='vo',name='PROCESS_HCPB_homogenized')
    return steel, blanket


def run_case(root:Path, thickness:float, enrichment:float, particles:int, batches:int, seed:int):
    steel, blanket=materials(enrichment)
    x0=openmc.XPlane(x0=0,boundary_type='vacuum'); x1=openmc.XPlane(x0=FIRST_WALL_CM); x2=openmc.XPlane(x0=FIRST_WALL_CM+thickness,boundary_type='vacuum')
    fw=openmc.Cell(fill=steel,region=+x0 & -x1); bl=openmc.Cell(fill=blanket,region=+x1 & -x2)
    geom=openmc.Geometry([fw,bl])
    src=openmc.IndependentSource(space=openmc.stats.Point((1e-6,0,0)), angle=openmc.stats.Monodirectional((1,0,0)), energy=openmc.stats.Discrete([14.1e6],[1]))
    settings=openmc.Settings(); settings.run_mode='fixed source'; settings.source=src; settings.particles=particles; settings.batches=batches; settings.inactive=0; settings.seed=seed; settings.output={'summary':False,'tallies':False}
    t=openmc.Tally(name='tbr'); t.filters=[openmc.CellFilter(bl)]; t.scores=['(n,Xt)']
    model=openmc.Model(geom,openmc.Materials([steel,blanket]),settings,openmc.Tallies([t]))
    d=root/f't{int(thickness)}_e{int(enrichment)}'; d.mkdir(parents=True,exist_ok=True)
    spath=model.run(cwd=d,threads=1,output=False)
    with openmc.StatePoint(spath) as sp:
        tally=sp.get_tally(name='tbr'); mean=float(np.sum(tally.mean)); sd=float(math.sqrt(np.sum(tally.std_dev**2)))
    Path(spath).unlink(missing_ok=True)
    return {'thickness_cm':thickness,'li6_enrichment_pct':enrichment,'tbr_mean':mean,'tbr_std_dev':sd,'mean_minus_2se':mean-2*sd,'histories':particles*batches}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',type=Path,required=True); ap.add_argument('--particles',type=int,default=30000); ap.add_argument('--batches',type=int,default=8); a=ap.parse_args()
    if not math.isclose(sum(VOL.values()),1.0,abs_tol=1e-12): raise SystemExit('volume fractions do not close')
    if not os.environ.get('OPENMC_CROSS_SECTIONS'): raise SystemExit('OPENMC_CROSS_SECTIONS required')
    a.output.mkdir(parents=True,exist_ok=True); rows=[]
    for i,(th,en) in enumerate((x,y) for x in THICKNESS_CM for y in ENRICHMENT): rows.append(run_case(a.output,th,en,a.particles,a.batches,20260907+7919*i))
    payload={'schema':'fusion-solution-set.hcpb-material-gate.v1','process_baseline':{'blanket_volume_fractions':VOL,'first_wall_cm':FIRST_WALL_CM,'blanket_thickness_cm':list(THICKNESS_CM)},'results':rows,'claim_boundary':['Homogenized infinite-transverse slab; not a tokamak geometry or whole-plant TBR.','Normal-incidence 14.1 MeV source and omitted ports/divertor make this a material-physics screen, not certification.','EUROFER is a reduced elemental proxy; exact qualified composition remains a later gate.','Passing only justifies detailed source-matched HCPB geometry; failure is evidence to redirect composition/enrichment before that expense.']}
    (a.output/'HCPB_MATERIAL_GATE.json').write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'cases':len(rows),'best':max(rows,key=lambda r:r['mean_minus_2se']),'at_60pct':[r for r in rows if r['li6_enrichment_pct']==60]}))
if __name__=='__main__': main()
