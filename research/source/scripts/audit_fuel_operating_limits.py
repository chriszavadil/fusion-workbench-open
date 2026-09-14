#!/usr/bin/env python3
"""Inverse requirement calculations; all physical inputs remain assumptions.

This is an explicitly follow-on experiment selected after the periodic-orbit test.
It is not held-out confirmation. Frozen inputs are saved before evaluating roots.
"""
from dataclasses import asdict, replace
from pathlib import Path
import argparse
import json
import math
from scipy.constants import electron_volt, physical_constants
from scipy.optimize import brentq
from audit_periodic_fuel import (FuelConfig, inherited_schedule, load_baseline,
                                 periodic_assessment, write_json)


def run(archive:Path, output:Path)->dict:
    v,sha=load_baseline(archive);s=inherited_schedule(v)
    B=v['p_plasma_dt_mw']*1e6/(17.6e6*electron_volt)*physical_constants['triton mass'][0]
    frozen={'schema':'fusion-solution-set.inverse-fuel-input.v1','prior_stage':'PERIODIC_FUEL_RESULT_2026-09-07.json',
            'selection':'adaptive follow-on, not held-out verification', 'TBR_assumed':1.15,'reserve_assumed_kg':.5,
            'base_config':asdict(FuelConfig()),'schedule':asdict(s),'baseline_mfile_sha256':sha,
            'direct_recycling_fractions':[0.,.8,1.], 'losses_for_gas_bound':[.0001,.0005],
            'fixed_gas_ratio_for_loss_and_burn_bound':10.}
    output.mkdir(exist_ok=True,parents=True)
    h=write_json(output/'INVERSE_FUEL_FROZEN_INPUT_2026-09-07.json',frozen)
    rows=[]
    def margin(c):return periodic_assessment(c,s,B,.5)['reserve_margin_kg']
    for direct in frozen['direct_recycling_fractions']:
        c=FuelConfig(direct_recycling_fraction=direct)
        for loss in frozen['losses_for_gas_bound']:
            cfg=replace(c,recycle_yield=1-loss)
            g=brentq(lambda g:margin(replace(cfg,puff_tritium_core_ratio=g)),0.,100.,xtol=1e-10)
            rows.append({'variable':'maximum_tritium_puff_to_core_ratio','value':g,'base_config':asdict(cfg),
                         'residual_kg':margin(replace(cfg,puff_tritium_core_ratio=g))})
        cfg=replace(c,puff_tritium_core_ratio=10.)
        loss=brentq(lambda l:margin(replace(cfg,recycle_yield=1-l)),0.,.005,xtol=1e-14)
        rows.append({'variable':'maximum_unrecovered_fraction_per_exhaust_pass','value':loss,'base_config':asdict(cfg),
                     'residual_kg':margin(replace(cfg,recycle_yield=1-loss))})
        b=brentq(lambda b:margin(replace(cfg,burn_fraction=b)),.005,.20,xtol=1e-12)
        rows.append({'variable':'minimum_effective_core_burn_fraction','value':b,'base_config':asdict(cfg),
                     'residual_kg':margin(replace(cfg,burn_fraction=b))})
    result={'schema':'fusion-solution-set.inverse-fuel-result.v1','frozen_input_sha256':h,'input':frozen,'results':rows,
            'claim_boundary':'Inverse requirements in the four-state periodic ledger only; no achieved device or recovery performance, and no plasma-power coupling.'}
    write_json(output/'INVERSE_FUEL_RESULT_2026-09-07.json',result)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=run(a.archive,a.output);print(json.dumps(r['results'],indent=2))
