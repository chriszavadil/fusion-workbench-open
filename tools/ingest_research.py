"""Explicit private-source intake; only numeric allowlisted projections are public."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
from evidence import project_configuration, sha256, write_json

SOURCE_SPECS = [
    ('r838', 'Reference · 8.38 m', 'runs-20260907/adaptive30y_warm_fixed',
     '92b7e95564e4890b3f2f3860f70d5e5834c4f838dde4eff77fbf5d1f6b5ccb8c'),
    ('r900', 'Confinement comparator · 9.00 m', 'confinement-dependency-20260907/H103_native_validation',
     '2566fdf898d61e46c82cedcb2476cf77869cf940c5e0930f8f5b565cf2929f5a'),
]
TRACKS = [
    ('systems','Systems and net electricity','Numerical reference available','Needs integrated physical validation', 'Two geometry-specific full-solver references; pulse electricity replay is available.'),
    ('plasma','Plasma confinement','Empirical scaling only','Transport / stability validation open','Keep internal scaling definitions separate from experimental global confinement metrics.'),
    ('magnets','Magnets and lifetime','Numerical constraint checked','Material margin unqualified','Event-located fatigue integration is numerically checked, not experimental lifetime evidence.'),
    ('cooling','Cooling and distribution','Component comparisons','Complete loop unresolved','Independent regional circuits and header obligations remain specific to the smaller reference.'),
    ('neutronics','Breeding and neutron heating','Same-design result missing','Blocked by geometry / transport interface','Historical mismatched screens do not establish breeding for either displayed device.'),
    ('fuel','Fuel and material recovery','Conditional ledgers / references','Compatible measurements incomplete','Recovery delays, permanent losses and isotope definitions need physical calibration.'),
    ('control','Plasma control benchmarks','Historical reference work','Separate machine scenes pending','Machine-specific vertical-control and observer studies are not tests of the displayed reactor.'),
    ('evidence','Equipment and evidence intake','Source records inspected','Map transfer not accepted','Measured, rated and simulated equipment records must not be merged into one performance claim.'),
]

def run(root: Path, repo: Path, out: Path) -> dict:
    configs=[]; adapter={}; inventory=[]
    for ident,title,relative,expected in SOURCE_SPECS:
        path=root/relative/'case_MFILE.DAT'
        if sha256(path)!=expected: raise ValueError('Pinned source artifact mismatch')
        configs.append(project_configuration(path,ident,title))
        template=path.with_name('case_IN.DAT')
        adapter[ident]={'input':str(template.resolve()),'input_sha256':sha256(template)}
    tracked=subprocess.check_output(['git','-C',str(repo),'ls-files','-z']).decode().split('\0')
    categories={'systems':[],'plasma':[],'magnets':[],'cooling':[],'neutronics':[], 'fuel':[],'control':[],'evidence':[],'other':[]}
    rules=[('control',r'freegs|tokamaker|observer|vertical|mast|protection'),
           ('magnets',r'fatigue|solenoid|lifecycle'),('cooling',r'cool|header|circuit|flow.balance|manifold'),
           ('neutronics',r'openmc|neutron|tbr|p[b]?17li'),('fuel',r'fuel|material|surface|diffusion|periodic'),
           ('plasma',r'confinement|plasma'),('systems',r'power|reactor|plant|closure'),('evidence',r'evidence|access|data|reference|prior.art')]
    for name in tracked:
        path=repo/name
        if not name or path.suffix.lower() not in ('.md','.json','.csv','.zip','.py','.txt') or not path.is_file(): continue
        category=next((k for k,pattern in rules if re.search(pattern,name,re.I)),'other')
        categories[category].append(name)
        inventory.append({'private_relative_path':name,'category':category,'sha256':sha256(path)})
    public_tracks=[{'id':t[0],'title':t[1],'model_status':t[2],'validation_status':t[3],
                    'summary':t[4],'catalogued_artifacts':len(categories[t[0]]),
                    'integration':'summary_only' if t[0] not in ('systems','magnets') else 'selected_runs_linked'} for t in TRACKS]
    catalog={'schema':'fusion-workbench.catalog.v1','project':'Fusion Workbench',
             'attribution':'Fusion Workbench contributors','purpose':'Open research for humanity',
             'publication_mode':'reviewed_projection','configurations':configs,'tracks':public_tracks,
             'inventory':{'tracked_artifacts_catalogued':len(inventory),
                          'interactive_configurations':len(configs),
                          'historical_raw_runs_fully_integrated':False,
                          'note':'Repository inventory plus selected linked runs, not a claim that every historical dataset is already rendered.'},
             'progress_summary':'Conceptual systems models exist. An experimentally validated integrated fusion plant has not been demonstrated by this project.',
             'experiments':[
                 {'id':'verify_recorded_energy','title':'Verify recorded pulse electricity','kind':'numerical_verification','local_only':True},
                 {'id':'rerun_process','title':'Run pinned full-systems reproduction','kind':'new_solver_execution','local_only':True,
                  'scope':'Fresh execution of an approved, fixed input; not an arbitrary code runner and not a new scientific discovery.'}
             ],
             'historical_rejections':[
                 {'title':'Unmatched blanket evidence','status':'not_combined','reason':'Lead-lithium screening and ceramic-blanket power results represent different materials and geometries.'},
                 {'title':'Earlier optimistic average-output estimate','status':'superseded','reason':'Pump heat recovery and fatigue numerics required correction; no superseded output is added to either current configuration.'},
                 {'title':'Internal confinement 1.00 attempts','status':'not_converged','reason':'Unconverged final states are not accepted power predictions and do not prove global physical impossibility.'}
             ],
             'public_references':[
                 {'title':'UKAEA PROCESS','url':'https://github.com/ukaea/PROCESS','role':'Existing systems-model solver; upstream attribution retained.'},
                 {'title':'Paramak','url':'https://github.com/fusion-energy/paramak','role':'Existing engineering CAD route to evaluate; this preview does not replace it.'}
             ]}
    write_json(out/'app/data/catalog.json',catalog)
    write_json(out/'.local/private-source-inventory.json',{'items':inventory,'repository':str(repo.resolve())})
    runtime={name:{'path':str(root/name),'sha256':sha256(root/name)} for name in ('windows_output_fix.py','adaptive_fatigue.py','mission_constraint.py')}
    write_json(out/'.local/execution.json',{'research_root':str(root.resolve()),'python':str(Path(os.sys.executable).resolve()),
               'source':str(root/'PROCESS-v3.4.2'),'upstream':'c0ae5b28649f2b20fb7efc7904628b6defe4151c',
               'runtime_modules':runtime,'configurations':adapter})
    # Never print or distribute this local deny list. It complements generic scanning.
    origin=subprocess.check_output(['git','-C',str(repo),'remote','get-url','origin'],text=True).strip()
    account=re.search(r'github\.com[:/]([^/]+)/',origin)
    private_terms=[os.environ.get('USERNAME',''),os.environ.get('COMPUTERNAME','')]
    if account: private_terms.append(account.group(1))
    write_json(out/'.local/private-deny.json',{'terms':[t for t in private_terms if len(t)>=3]})
    return {'configurations':len(configs),'artifacts_catalogued':len(inventory),'public_projection_written':True,'credentials_exported':False}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--research-root',type=Path,required=True);ap.add_argument('--repo',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();print(json.dumps(run(a.research_root,a.repo,a.output)))
