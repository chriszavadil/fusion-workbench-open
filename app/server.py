"""Loopback-only evidence workbench. Not an Internet deployment server.

Only approved local input reproduction and numeric verification can be run.
No client-supplied command, script, path, URL, or environment is accepted.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
from pathlib import Path
import secrets
import subprocess
import sys
import threading
import time
from urllib.parse import urlsplit, unquote
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from evidence import verify_configuration, write_json

class JobManager:
    def __init__(self,root:Path):
        self.root=root;self.jobs={};self.processes={};self.lock=threading.RLock()
        self.pool=ThreadPoolExecutor(max_workers=1)
    def public(self,job):
        allowed=('id','kind','configuration_id','state','started_at','finished_at','message','result')
        return {k:job[k] for k in allowed if k in job}
    def create(self,kind,configuration_id):
        if kind not in ('verify_recorded_energy','rerun_process') or configuration_id not in ('r838','r900'):
            raise ValueError('Unsupported experiment')
        if kind=='rerun_process' and not (self.root/'.local/execution.json').is_file():
            raise RuntimeError('Full solver is not configured on this machine')
        with self.lock:
            if any(j['state'] in ('queued','running','cancelling') for j in self.jobs.values()):
                raise RuntimeError('A local experiment is already active')
            ident=secrets.token_hex(12)
            job={'id':ident,'kind':kind,'configuration_id':configuration_id,'state':'queued','message':'Waiting for the local worker.'}
            self.jobs[ident]=job
            self.pool.submit(self.execute,ident)
            return self.public(job)
    def execute(self,ident):
        with self.lock:
            job=self.jobs[ident]
            if job['state']=='cancelled':return
            job.update(state='running',started_at=time.time(),message='Executing a real local check; no simulated progress percentage.')
        try:
            folder=self.root/'.local/jobs'/ident;folder.mkdir(parents=True,exist_ok=False)
            if job['kind']=='verify_recorded_energy':
                catalog=json.loads((self.root/'app/data/catalog.json').read_text())
                config=next(x for x in catalog['configurations'] if x['id']==job['configuration_id'])
                result=verify_configuration(config)
                write_json(folder/'safe-result.json',result)
            else:
                adapter=json.loads((self.root/'.local/execution.json').read_text())
                command=[adapter['python'],'-u',str(self.root/'tools/process_worker.py'),'--workbench',str(self.root),
                         '--configuration',job['configuration_id'],'--job-dir',str(folder)]
                with (folder/'private-worker.log').open('w',encoding='utf-8') as logfile:
                    child=subprocess.Popen(command,cwd=folder,stdin=subprocess.DEVNULL,stdout=logfile,stderr=subprocess.STDOUT,shell=False,close_fds=True)
                    with self.lock:
                        self.processes[ident]=child
                        if job['state']=='cancelling':child.terminate()
                    try:code=child.wait(timeout=600)
                    except subprocess.TimeoutExpired:
                        child.terminate()
                        try:child.wait(timeout=10)
                        except subprocess.TimeoutExpired:child.kill();child.wait()
                        with self.lock:job.update(state='timed_out',message='The 600-second local run limit was reached.')
                        return
                with self.lock:
                    if job['state']=='cancelling':
                        job.update(state='cancelled',message='Local execution cancelled.');return
                if code!=0:raise RuntimeError('Private worker failed')
                result=json.loads((folder/'safe-result.json').read_text())
            with self.lock:
                if job['state']=='cancelling':job.update(state='cancelled',message='Cancelled; result not promoted.');return
                job.update(state='completed' if result['passed'] else 'failed',result=result,
                           message='Completed. Numerical evidence only; the accepted reference was not changed.')
        except Exception:
            with self.lock:job.update(state='failed',message='Local execution failed. Details remain in the private worker log.')
        finally:
            with self.lock:
                job['finished_at']=time.time();self.processes.pop(ident,None)
    def cancel(self,ident):
        with self.lock:
            if ident not in self.jobs:raise KeyError(ident)
            job=self.jobs[ident]
            if job['state']=='queued':job.update(state='cancelled',finished_at=time.time(),message='Cancelled before execution.')
            elif job['state']=='running':
                job.update(state='cancelling',message='Cancellation requested.')
                child=self.processes.get(ident)
                if child and child.poll() is None:child.terminate()
            return self.public(job)
    def close(self):
        for ident in list(self.jobs):self.cancel(ident)
        self.pool.shutdown(wait=True,cancel_futures=True)

class WorkbenchServer(ThreadingHTTPServer):
    daemon_threads=True
    allow_reuse_address=False
    def server_bind(self):
        import socket
        if os.name=='nt':self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1)
        super().server_bind()
    def __init__(self,address,root=ROOT):
        super().__init__(address,Handler);self.root=root;self.manager=JobManager(root)
        self.started_at=time.time()

class Handler(BaseHTTPRequestHandler):
    server_version='FusionWorkbench';sys_version=''
    def log_message(self,*args):pass
    def respond(self,status,obj,ctype='application/json; charset=utf-8'):
        data=json.dumps(obj,allow_nan=False).encode() if not isinstance(obj,bytes) else obj
        self.send_response(status);self.send_header('Content-Type',ctype);self.send_header('Content-Length',str(len(data)))
        self.send_header('X-Content-Type-Options','nosniff');self.send_header('Referrer-Policy','no-referrer')
        self.send_header('Cache-Control','no-store')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'")
        self.end_headers();self.wfile.write(data)
    def host_ok(self):
        port=self.server.server_address[1]
        return self.headers.get('Host') in (f'127.0.0.1:{port}',f'localhost:{port}')
    def do_GET(self):
        if not self.host_ok():return self.respond(403,{'error':'Invalid local host'})
        route=unquote(urlsplit(self.path).path)
        if route in ('/api/catalog','/data/catalog.json'):
            return self.respond(200,(self.server.root/'app/data/catalog.json').read_bytes())
        if route in ('/api/transportlab','/data/transport_lab.json'):
            return self.respond(200,(self.server.root/'app/data/transport_lab.json').read_bytes())
        if route in ('/api/neutronics','/data/neutronics.json'):
            return self.respond(200,(self.server.root/'app/data/neutronics.json').read_bytes())
        if route in ('/api/research','/data/research_library.json'):
            return self.respond(200,(self.server.root/'app/data/research_library.json').read_bytes())
        if route=='/api/status':
            with self.server.manager.lock:
                jobs=[self.server.manager.public(j) for j in self.server.manager.jobs.values()]
            return self.respond(200,{'mode':'local','worker':'available','full_solver_configured':(self.server.root/'.local/execution.json').is_file(),
                                     'checked_at':time.time(),'jobs':jobs,'public_hosting_enabled':False})
        if route.startswith('/api/jobs/'):
            with self.server.manager.lock:
                job=self.server.manager.jobs.get(route.split('/')[-1])
                return self.respond(200,self.server.manager.public(job)) if job else self.respond(404,{'error':'Unknown experiment'})
        if route=='/':route='/index.html'
        if route not in ('/index.html','/style.css','/app.js','/viewer.js','/research.js','/neutronics.js','/transport-lab.js') and not route.startswith(('/assets/','/vendor/')):
            return self.respond(404,{'error':'Not a public resource'})
        base=self.server.root/'app/web';target=(base/route.lstrip('/')).resolve()
        try:target.relative_to(base.resolve())
        except ValueError:return self.respond(404,{'error':'Not a public resource'})
        if not target.is_file() or target.is_symlink() or target.suffix.lower() not in ('.html','.js','.css','.glb','.json','.png','.svg','.txt'):
            return self.respond(404,{'error':'Not a public resource'})
        return self.respond(200,target.read_bytes(),mimetypes.guess_type(target.name)[0] or 'application/octet-stream')
    def reject_post(self,status,message):
        # Drain only a bounded declared body before rejecting, avoiding TCP reset races.
        try:
            n=int(self.headers.get("Content-Length","0"))
            if 0<n<=2048:
                self.connection.settimeout(2.0);self.rfile.read(n)
        except (ValueError,OSError):pass
        self.close_connection=True
        return self.respond(status,{"error":message})

    def do_POST(self):
        if not self.host_ok():return self.reject_post(403,'Invalid local host')
        origin=self.headers.get('Origin');port=self.server.server_address[1]
        if origin not in (f'http://127.0.0.1:{port}',f'http://localhost:{port}') or self.headers.get('X-Workbench-Request')!='local-ui-v1':
            return self.reject_post(403,'Same-origin local UI request required')
        if self.headers.get('Content-Type','').split(';')[0]!='application/json':
            return self.reject_post(415,'JSON required')
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=2048:raise ValueError()
            data=json.loads(self.rfile.read(length))
            if not isinstance(data,dict):raise ValueError()
            route=urlsplit(self.path).path
            if route=='/api/jobs':
                if set(data)!= {'kind','configuration_id'}:raise ValueError()
                if not all(isinstance(x,str) for x in data.values()):raise ValueError()
                result=self.server.manager.create(**data);return self.respond(202,result)
            if route.startswith('/api/jobs/') and route.endswith('/cancel') and data=={}:
                return self.respond(200,self.server.manager.cancel(route.split('/')[3]))
            return self.respond(404,{'error':'Unknown operation'})
        except (ValueError,TypeError,KeyError):return self.respond(400,{'error':'Invalid allowlisted operation'})
        except RuntimeError as exc:return self.respond(409,{'error':str(exc)})

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=18765);parser.add_argument('--open',action='store_true');args=parser.parse_args()
    if not 1024<=args.port<=65535:raise SystemExit('Use an unprivileged local port')
    server=WorkbenchServer(('127.0.0.1',args.port))
    print(f'Fusion Workbench: http://127.0.0.1:{args.port} (local only)',flush=True)
    if args.open:
        import webbrowser;webbrowser.open(f'http://127.0.0.1:{args.port}')
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.shutdown();server.manager.close();server.server_close()
