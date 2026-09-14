#!/usr/bin/env python3
"""Separately declared follow-on to the external-material reference study.

Use Kulsartov et al. Eq.5 ONLY on that article's separate biphasic material.
Compute diffusion-only envelopes for an unknown cooling trace, not a fit to the
experiment. No transplantation of these parameters into the pure-Li4SiO4 case.
"""
from __future__ import annotations
from pathlib import Path
import argparse,json,math
import numpy as np
from scipy.constants import R
from scipy.integrate import quad
from material_release_reference import steady_shutdown_fraction_released,write

def D_kelvin(T:float)->float:
    if not math.isfinite(T) or T<=0:raise ValueError('positive absolute temperature required')
    return 5e-11*math.exp(-20000/(R*T))

def temperature_scenario(profile,t,duration,hot,cold):
    if profile=='held_hot':return hot
    if profile=='instant_cold':return cold
    if profile=='linear_cooling_sensitivity':return hot+(cold-hot)*t/duration
    raise ValueError('unknown profile')

def diffusion_clock(profile,duration,hot,cold):
    if not math.isfinite(duration) or duration<=0:raise ValueError('duration')
    if not all(math.isfinite(x) and x>0 for x in (hot,cold)) or hot<cold:raise ValueError('temperature interval')
    ref=D_kelvin(hot)
    if ref==0:raise ValueError('Diffusivity underflow')
    v,e=quad(lambda t:D_kelvin(temperature_scenario(profile,t,duration,hot,cold))/ref,0,duration,epsabs=1e-10,epsrel=1e-11)
    return v,e

def run(output:Path):
    output.mkdir(parents=True,exist_ok=True)
    frozen={'schema':'fusion.cooldown.inputs.v1','source_doi':'10.1016/j.nme.2023.101489',
      'source_pdf':'https://publikationen.bibliothek.kit.edu/1000161583/151216760',
      'source_inspected_pages_one_based':[1,3,4,5],
      'material':'Li4SiO4 with 35 mol% Li2TiO3; vacuum extraction; not pure-Li4SiO4 calibration',
      'diffusivity_D0_m2_s':5e-11,'activation_energy_J_mol':20000,
      'hot_K':665+273.15,'cold_K':100+273.15,'shutdown_s':1.5*3600,
      'diameters_um':[250.,750.,1250.],
      'profiles':['held_hot','instant_cold','linear_cooling_sensitivity'],
      'diameter_selection':'two reported range endpoints and a predeclared middle example; no experimental size weights assumed',
      'initial_condition':'hypothetical fully developed hot steady-state uniform-generation diffusion profile',
      'history_selection':'adaptive follow-on; these are not measured temperature histories',
      'scope':['Only diffusion with a spatially uniform temperature and zero surface concentration.',
               'Paper models surface desorption as well; it cautions that its effective diffusion coefficient is qualitative.',
               'No raw trace, fitted model uncertainty, HCPB delivery yield or industrial material qualification available.',
               'Upper/lower labels bound this restricted PDE only, not the actual experiment.']}
    h=write(output/'COOLDOWN_FROZEN_INPUT.json',frozen)
    hot,cold,duration=frozen['hot_K'],frozen['cold_K'],frozen['shutdown_s']
    rows=[]
    for size in frozen['diameters_um']:
        radius=size*1e-6/2;mean_hot=radius*radius/(15*D_kelvin(hot))
        for profile in frozen['profiles']:
            t,e=diffusion_clock(profile,duration,hot,cold)
            fraction=float(steady_shutdown_fraction_released(t,mean_hot,4096))
            rows.append({'diameter_um':size,'profile':profile,'hot_diffusion_mean_h':mean_hot/3600,
              'equivalent_hot_time_s':t,'quadrature_error_s':e,'fraction_released_during_shutdown':fraction,
              'fraction_remaining':1-fraction})
    r={'schema':'fusion.cooldown.result.v1','frozen_input_sha256':h,'D_hot_m2_s':D_kelvin(hot),'D_cold_m2_s':D_kelvin(cold),
       'D_hot_over_cold':D_kelvin(hot)/D_kelvin(cold),'cases':rows,'scope':frozen['scope']}
    write(output/'COOLDOWN_RESULT.json',r);return r
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(run(a.output),indent=2))
