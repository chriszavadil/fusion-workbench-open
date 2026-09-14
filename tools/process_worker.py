"""Trusted local allowlisted PROCESS execution; never exposed as a code upload API."""
from __future__ import annotations
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','NUMBA_NUM_THREADS','MKL_NUM_THREADS'):
    os.environ[k]='1'
os.environ['MPLBACKEND']='Agg'
from evidence import project_configuration, sha256, write_json, read_mfile

def git_output(source: Path, *args: str) -> str:
    """Bounded shell-free metadata lookup; no physics changes."""
    result = subprocess.run(
        ['git', '-C', str(source), *args], shell=False,
        capture_output=True, text=True, check=True, timeout=15,
    )
    return result.stdout.strip()


def install_reporting_metadata(source: Path) -> dict:
    """Replace only the unbounded shell calls used by the upstream banner."""
    branch = git_output(source, 'rev-parse', '--abbrev-ref', 'HEAD')
    tag = git_output(source, 'describe', '--tags')
    import process.core.init as process_init
    process_init.get_git_summary = lambda: (branch, tag)
    return {'branch': branch, 'tag': tag,
            'adapter_scope': 'reporting-only shell-free Git lookup; equations unchanged'}


def main() -> int:
    ap=argparse.ArgumentParser();ap.add_argument('--workbench',type=Path,required=True);ap.add_argument('--configuration',choices=('r838','r900'),required=True);ap.add_argument('--job-dir',type=Path,required=True)
    args=ap.parse_args();root=args.workbench.resolve();dest=args.job_dir.resolve()
    dest.relative_to((root/'.local/jobs').resolve())
    cfg=json.loads((root/'.local/execution.json').read_text())
    source=Path(cfg['source'])
    pin=git_output(source,'rev-parse','HEAD')
    if pin!=cfg['upstream']:raise ValueError('Upstream revision changed')
    if git_output(source,'status','--porcelain'):
        raise ValueError('Upstream working tree modified')
    template=cfg['configurations'][args.configuration]
    raw=Path(template['input'])
    if sha256(raw)!=template['input_sha256']:raise ValueError('Approved input changed')
    for filename,module in cfg['runtime_modules'].items():
        path=Path(module['path'])
        if sha256(path)!=module['sha256']:raise ValueError('Approved runtime module changed')
        name=path.stem
        spec=importlib.util.spec_from_file_location(name,path)
        obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);obj.install()
    inp=dest/'case_IN.DAT';shutil.copyfile(raw,inp)
    write_json(dest/'input-provenance.json',{'input_sha256':sha256(inp),'upstream':pin,'configuration':args.configuration})
    print('FULL_SOLVER_STARTED',flush=True)
    from process.main import SingleRun
    metadata=install_reporting_metadata(source)
    write_json(dest/'reporting-adapter.json',metadata)
    SingleRun(inp.as_posix()).run()
    output=dest/'case_MFILE.DAT'
    values=read_mfile(output)
    if values.get('ifail')!=1:
        write_json(dest/'safe-result.json',{'passed':False,'kind':'full_solver_reproduction','classification':'solver_not_converged','physical_validation':False})
        return 0
    projected=project_configuration(output,args.configuration,'Fresh local reproduction')
    write_json(dest/'safe-result.json',{'passed':True,'kind':'full_solver_reproduction',
               'classification':'numerically_converged','configuration_id':args.configuration,
               'metrics':projected['metrics'],'verification':projected['verification'],
               'artifact_sha256':projected['provenance']['artifact_sha256'],
               'physical_validation':False,'accepted_reference_updated':False})
    print('FULL_SOLVER_FINISHED',flush=True)
    return 0

if __name__=='__main__':
    if os.environ.get('FUSION_WORKER_DIAGNOSTIC') == '1':
        import faulthandler
        faulthandler.dump_traceback_later(30, repeat=True)
    print('WORKER_STARTUP_ENTERED',flush=True)
    try:raise SystemExit(main())
    except Exception:
        # Private log contains traceback for local debugging; never return it over HTTP.
        import traceback;traceback.print_exc();raise SystemExit(2)
