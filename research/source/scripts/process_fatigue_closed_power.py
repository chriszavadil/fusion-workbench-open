#!/usr/bin/env python3
"""Re-run the PR42 PROCESS plant with central-solenoid fatigue constraint 90 enabled.

This closes a missing engineering constraint discovered in the authenticated baseline:
PROCESS reported 5,736.98 allowable CS cycles versus a declared minimum of 20,000,
while the original optimization did not enable constraint 90.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

from process.main import SingleRun
try:
    from process.core.io.mfile import MFile
except ImportError:
    from process.core.io.mfile.base import MFile

CASES = [
    {"id":"fatigue_blanket_life","n_cycle_min":12105.712015290683,"dwell_s":1800.0,"hcd_wallplug":0.50,"availability":0.80},
    {"id":"fatigue_20k","n_cycle_min":20000.0,"dwell_s":1800.0,"hcd_wallplug":0.50,"availability":0.80},
    {"id":"fatigue_20k_hcd60_dwell300","n_cycle_min":20000.0,"dwell_s":300.0,"hcd_wallplug":0.60,"availability":0.80},
    {"id":"fatigue_20k_hcd70_dwell300","n_cycle_min":20000.0,"dwell_s":300.0,"hcd_wallplug":0.70,"availability":0.80},
]

KEYS = (
    "ifail","rmajor","dr_cs","f_a_cs_turn_steel","stress_hoop_cs_inner","stress_shear_cs_peak",
    "n_cycle","n_cycle_min","bktcycles","p_fusion_total_mw","p_plant_electric_gross_mw",
    "p_plant_electric_net_mw","p_plant_electric_recirc_mw","p_hcd_electric_total_mw",
    "p_coolant_pump_elec_total_mw","e_plant_net_electric_pulse_kwh","t_plant_pulse_total",
    "t_plant_pulse_burn","t_plant_pulse_dwell","cost_of_electricity"
)

def get(mfile:MFile,key:str)->float|None:
    try:
        value=float(mfile.get(key,scan=-1))
        return value if math.isfinite(value) else None
    except Exception:
        return None

def decorate(text:str,case:dict[str,Any])->str:
    lines=[
        "", "* Fusion Solution Set fatigue-closed plant audit *",
        "icc = 90 * CS achievable stress load cycles lower limit",
        f"n_cycle_min = {case['n_cycle_min']}",
        "p_plant_electric_net_required_mw = 400.0",
        f"t_plant_pulse_dwell = {case['dwell_s']}",
        f"eta_ecrh_injector_wall_plug = {case['hcd_wallplug']}",
        f"f_t_plant_available = {case['availability']}",
    ]
    return text.rstrip()+"\n"+"\n".join(lines)+"\n"

def run_case(process_root:Path,out:Path,case:dict[str,Any])->dict[str,Any]:
    directory=out/"cases"/case["id"]
    directory.mkdir(parents=True,exist_ok=True)
    source=process_root/"examples"/"data"/"large_tokamak_IN.DAT"
    input_path=directory/f"{case['id']}_IN.DAT"
    input_path.write_text(decorate(source.read_text(),case))
    exception=None
    try:
        run=SingleRun(input_path.as_posix()); run.run(); mfile_path=Path(run.mfile_path)
    except Exception as exc:
        exception={"type":type(exc).__name__,"message":str(exc)}
        found=sorted(directory.glob("*MFILE.DAT")); mfile_path=found[0] if found else directory/"MFILE.DAT"
    values={}
    if mfile_path.is_file():
        mf=MFile(filename=mfile_path); values={key:get(mf,key) for key in KEYS}
    ifail=values.get("ifail"); cycles=values.get("n_cycle")
    numerical=exception is None and ifail is not None and int(round(ifail))==1
    fatigue=cycles is not None and cycles+1e-9>=float(case["n_cycle_min"])
    energy=values.get("e_plant_net_electric_pulse_kwh"); cycle=values.get("t_plant_pulse_total")
    cycle_avg=None if energy is None or cycle is None or cycle<=0 else energy/(cycle/3600.0)/1000.0
    avg=None if cycle_avg is None else cycle_avg*float(case["availability"])
    result={"case":case,"exception":exception,"values":values,"numerically_converged":numerical,
            "fatigue_constraint_satisfied":fatigue,"fatigue_closed":numerical and fatigue,
            "cycle_average_net_mw":cycle_avg,"availability_adjusted_average_net_mw":avg}
    (directory/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    return result

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--process-root",type=Path,required=True); ap.add_argument("--output",type=Path,required=True); args=ap.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    rows=[run_case(args.process_root.resolve(),args.output.resolve(),case) for case in CASES]
    payload={"schema":"fusion-solution-set.process-fatigue-closed-power.v1",
             "source":{"PROCESS_commit":"c0ae5b28649f2b20fb7efc7904628b6defe4151c","baseline":"examples/data/large_tokamak_IN.DAT"},
             "cases":rows,
             "claim_boundary":["Conceptual PROCESS systems-model results only.","Constraint 90 is newly enforced; this is not experimental magnet lifetime validation.","HCD efficiency, dwell and availability cases are assumptions unless independently validated.","Tritium self-sufficiency remains external to tokamak PROCESS in this source revision."]}
    (args.output/"PROCESS_FATIGUE_CLOSED_POWER.json").write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
    fields=["case","fatigue_closed","n_cycle_min","n_cycle","hoop_stress_mpa","dr_cs_m","cs_steel_fraction","rmajor_m","fusion_mw","flat_top_net_mw","cycle_average_net_mw","availability_adjusted_average_net_mw","exception"]
    with (args.output/"PROCESS_FATIGUE_CLOSED_POWER.csv").open("w",newline="") as fh:
        writer=csv.DictWriter(fh,fieldnames=fields); writer.writeheader()
        for row in rows:
            v=row["values"]; writer.writerow({"case":row["case"]["id"],"fatigue_closed":row["fatigue_closed"],"n_cycle_min":row["case"]["n_cycle_min"],"n_cycle":v.get("n_cycle"),"hoop_stress_mpa":None if v.get("stress_hoop_cs_inner") is None else v["stress_hoop_cs_inner"]/1e6,"dr_cs_m":v.get("dr_cs"),"cs_steel_fraction":v.get("f_a_cs_turn_steel"),"rmajor_m":v.get("rmajor"),"fusion_mw":v.get("p_fusion_total_mw"),"flat_top_net_mw":v.get("p_plant_electric_net_mw"),"cycle_average_net_mw":row["cycle_average_net_mw"],"availability_adjusted_average_net_mw":row["availability_adjusted_average_net_mw"],"exception":None if row["exception"] is None else row["exception"]["message"]})
    return 0 if any(r["fatigue_closed"] for r in rows) else 2

if __name__=="__main__": raise SystemExit(main())
