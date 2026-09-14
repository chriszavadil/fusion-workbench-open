#!/usr/bin/env python3
"""Quantify pulsed duty-cycle and HCD efficiency impact on a PROCESS plant.

This uses the same generic large-tokamak optimization target (>=400 MWe flat-top
net) while varying only explicit engineering assumptions. The result reports
flat-top power, net energy per pulse, cycle-average power and availability-
adjusted annual average, preventing flat-top MWe from being confused with
continuous delivered power.
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
    {"id": "baseline", "dwell_s": 1800.0, "hcd_wallplug": 0.50, "availability": 0.80},
    {"id": "dwell900", "dwell_s": 900.0, "hcd_wallplug": 0.50, "availability": 0.80},
    {"id": "dwell300", "dwell_s": 300.0, "hcd_wallplug": 0.50, "availability": 0.80},
    {"id": "hcd60", "dwell_s": 1800.0, "hcd_wallplug": 0.60, "availability": 0.80},
    {"id": "hcd70", "dwell_s": 1800.0, "hcd_wallplug": 0.70, "availability": 0.80},
    {"id": "dwell900_hcd60", "dwell_s": 900.0, "hcd_wallplug": 0.60, "availability": 0.80},
    {"id": "dwell300_hcd70", "dwell_s": 300.0, "hcd_wallplug": 0.70, "availability": 0.80},
    {"id": "dwell300_hcd70_avail90", "dwell_s": 300.0, "hcd_wallplug": 0.70, "availability": 0.90},
]

KEYS = (
    "ifail", "rmajor", "p_fusion_total_mw", "p_plant_electric_gross_mw",
    "p_plant_electric_recirc_mw", "f_p_plant_electric_recirc",
    "p_plant_electric_net_mw", "p_hcd_electric_total_mw",
    "p_coolant_pump_elec_total_mw", "p_cryo_plant_electric_mw",
    "e_plant_net_electric_pulse_kwh", "t_plant_pulse_total",
    "t_plant_pulse_burn", "t_plant_pulse_dwell",
)


def get(mfile: MFile, key: str) -> float | None:
    try:
        v = float(mfile.get(key, scan=-1))
        return v if math.isfinite(v) else None
    except Exception:
        return None


def overrides(text: str, case: dict[str, float | str]) -> str:
    return text.rstrip() + "\n\n* Fusion Solution Set pulse-power sensitivity overrides *\n" + "\n".join([
        "p_plant_electric_net_required_mw = 400.0",
        f"t_plant_pulse_dwell = {case['dwell_s']}",
        f"eta_ecrh_injector_wall_plug = {case['hcd_wallplug']}",
        f"f_t_plant_available = {case['availability']}",
    ]) + "\n"


def run_case(process_root: Path, out: Path, case: dict[str, Any]) -> dict[str, Any]:
    d = out / "cases" / str(case["id"])
    d.mkdir(parents=True, exist_ok=True)
    source = process_root / "examples" / "data" / "large_tokamak_IN.DAT"
    inp = d / f"{case['id']}_IN.DAT"
    inp.write_text(overrides(source.read_text(), case))
    exception = None
    try:
        run = SingleRun(inp.as_posix())
        run.run()
        mf_path = Path(run.mfile_path)
    except Exception as exc:
        exception = {"type": type(exc).__name__, "message": str(exc)}
        found = list(d.glob("*MFILE.DAT"))
        mf_path = found[0] if found else d / "MFILE.DAT"
    values = {}
    if mf_path.is_file():
        mf = MFile(filename=mf_path)
        values = {k: get(mf, k) for k in KEYS}
    ifail = values.get("ifail")
    feasible = ifail is not None and int(round(ifail)) == 1 and exception is None
    energy = values.get("e_plant_net_electric_pulse_kwh")
    cycle = values.get("t_plant_pulse_total")
    cycle_avg = None
    if energy is not None and cycle is not None and cycle > 0:
        cycle_avg = energy / (cycle / 3600.0) / 1000.0
    avail = float(case["availability"])
    annual_avg = None if cycle_avg is None else cycle_avg * avail
    annual_mwh = None if annual_avg is None else annual_avg * 8766.0
    result = {
        "case": case,
        "feasible": feasible,
        "exception": exception,
        "values": values,
        "cycle_average_net_mw": cycle_avg,
        "availability_adjusted_average_net_mw": annual_avg,
        "annual_net_electricity_mwh": annual_mwh,
    }
    (d / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--process-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    results = [run_case(args.process_root.resolve(), args.output.resolve(), c) for c in CASES]
    payload = {
        "schema": "fusion-solution-set.process-power-cycle-sensitivity.v1",
        "source": {"PROCESS": "v3.4.2", "input": "large_tokamak_IN.DAT"},
        "results": results,
        "claim_boundary": [
            "Conceptual systems-model sensitivity only.",
            "Availability is assumed, not demonstrated.",
            "HCD wall-plug efficiency cases are technology targets, not achieved component performance.",
            "Tritium self-sufficiency is not closed by PROCESS v3.4.2 and is being evaluated independently with OpenMC.",
        ],
    }
    (args.output / "PROCESS_POWER_CYCLE_SENSITIVITY.json").write_text(json.dumps(payload, indent=2, sort_keys=True)+"\n")
    fields = ["case","feasible","dwell_s","hcd_wallplug","availability","rmajor_m","fusion_mw","gross_mw","flat_top_net_mw","recirc_mw","recirc_fraction","hcd_electric_mw","coolant_pump_mw","burn_s","cycle_s","pulse_net_kwh","cycle_average_net_mw","availability_adjusted_average_net_mw","annual_net_mwh"]
    with (args.output / "PROCESS_POWER_CYCLE_SENSITIVITY.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields); w.writeheader()
        for r in results:
            c=r["case"]; v=r["values"]
            w.writerow({
                "case":c["id"],"feasible":r["feasible"],"dwell_s":c["dwell_s"],"hcd_wallplug":c["hcd_wallplug"],"availability":c["availability"],
                "rmajor_m":v.get("rmajor"),"fusion_mw":v.get("p_fusion_total_mw"),"gross_mw":v.get("p_plant_electric_gross_mw"),"flat_top_net_mw":v.get("p_plant_electric_net_mw"),"recirc_mw":v.get("p_plant_electric_recirc_mw"),"recirc_fraction":v.get("f_p_plant_electric_recirc"),"hcd_electric_mw":v.get("p_hcd_electric_total_mw"),"coolant_pump_mw":v.get("p_coolant_pump_elec_total_mw"),"burn_s":v.get("t_plant_pulse_burn"),"cycle_s":v.get("t_plant_pulse_total"),"pulse_net_kwh":v.get("e_plant_net_electric_pulse_kwh"),"cycle_average_net_mw":r["cycle_average_net_mw"],"availability_adjusted_average_net_mw":r["availability_adjusted_average_net_mw"],"annual_net_mwh":r["annual_net_electricity_mwh"],
            })
    md=["# PROCESS pulse/HCD sensitivity","","All cases retain the >=400 MWe flat-top net constraint. The key metric is availability-adjusted cycle-average net power, not the flat-top headline.","","| Case | Feasible | R0 m | Recirc % gross | HCD MWe | Cycle avg MWe | Availability-adjusted MWe |","|---|---:|---:|---:|---:|---:|---:|"]
    for r in results:
        v=r["values"]
        f=lambda x,d=1:"—" if x is None else f"{float(x):.{d}f}"
        rf=v.get("f_p_plant_electric_recirc")
        md.append(f"| {r['case']['id']} | {r['feasible']} | {f(v.get('rmajor'),2)} | {f(None if rf is None else 100*rf,1)} | {f(v.get('p_hcd_electric_total_mw'))} | {f(r['cycle_average_net_mw'])} | {f(r['availability_adjusted_average_net_mw'])} |")
    (args.output / "PROCESS_POWER_CYCLE_SENSITIVITY.md").write_text("\n".join(md)+"\n")
    if not any(r["feasible"] for r in results):
        return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
