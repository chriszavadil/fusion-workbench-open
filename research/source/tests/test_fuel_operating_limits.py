"""Check every inverse root against either side of the periodic boundary."""
from dataclasses import replace
from pathlib import Path
import json
import os
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_periodic_fuel import FuelConfig, Schedule, periodic_assessment
import audit_fuel_operating_limits as inverse_module
from audit_coupled_candidate import load_baseline
from scipy.constants import electron_volt, physical_constants

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture(scope='module')
def inputs(tmp_path_factory):
    path=os.environ.get('FUSION_POWER_ARCHIVE')
    if not path:pytest.skip('Set FUSION_POWER_ARCHIVE to the original ZIP')
    archive=Path(path);result=inverse_module.run(archive,tmp_path_factory.mktemp('inverse'))
    v,_=load_baseline(archive)
    burn=v['p_plasma_dt_mw']*1e6/(17.6e6*electron_volt)*physical_constants['triton mass'][0]
    return result,{'burn_rate_kg_s':burn}

@pytest.mark.parametrize('row_index',range(12))
def test_inverse_roots_are_actual_boundaries(inputs,row_index):
    inverse,first=inputs;row=inverse['results'][row_index]
    c=FuelConfig(**row['base_config']);s=Schedule(**inverse['input']['schedule']);B=first['burn_rate_kg_s']
    value=row['value'];name=row['variable']
    def adjusted(v):
        if name=='maximum_tritium_puff_to_core_ratio':return replace(c,puff_tritium_core_ratio=v)
        if name=='maximum_unrecovered_fraction_per_exhaust_pass':return replace(c,recycle_yield=1-v)
        if name=='minimum_effective_core_burn_fraction':return replace(c,burn_fraction=v)
        raise AssertionError(name)
    def margin(v):return periodic_assessment(adjusted(v),s,B,.5)['reserve_margin_kg']
    assert abs(margin(value))<1e-6
    smaller,larger=margin(value*(1-1e-4)),margin(value*(1+1e-4))
    if name.startswith('minimum'):
        assert smaller<0<larger
    else:
        assert smaller>0>larger
