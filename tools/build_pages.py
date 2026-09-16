"""Build the read-only Pages viewer from cleared application data. No network access."""
from pathlib import Path
import argparse,hashlib,json,re,shutil,base64
ROOT=Path(__file__).resolve().parents[1]
REPO='https://github.com/chriszavadil/fusion-workbench-open'
BRANCH='main'

def build(root=ROOT):
 from build_power_progress import build as build_power_progress
 build_power_progress(root)
 from build_progress_roadmap import build as build_progress_roadmap
 build_progress_roadmap(root)
 root=root.resolve();out=root/'docs';out.mkdir(exist_ok=True);web=root/'app/web';data=root/'app/data'
 for name in ['assets','vendor']:
  dst=out/name
  if dst.exists():shutil.rmtree(dst)
  shutil.copytree(web/name,dst)
 for name in ['catalog.json','neutronics.json','research_library.json','transport_lab.json','source_context.bin','lif_benchmark.json','prior_work.json']:
  dst=out/'data'/name;dst.parent.mkdir(exist_ok=True);shutil.copyfile(data/name,dst)
 for name in ['style.css','viewer.js','research.js','neutronics.js','transport-lab.js','benchmarks.js']:
  text=(web/name).read_text(encoding='utf-8')
  for a,b in [('/api/research','./data/research_library.json'),('/api/neutronics','./data/neutronics.json'),('/api/transportlab','./data/transport_lab.json')]:text=text.replace(a,b)
  text=text.replace("'/data/","'./data/")
  text=text.replace("'/assets/","'./assets/").replace('`/assets/','`./assets/')
  (out/name).write_text(text,encoding='utf-8')
 app=(web/'app.js').read_text(encoding='utf-8')
 begin=app.index('async function api(');end=app.index('function buildEvidence()',begin)
 app=app[:begin]+app[end:]
 begin=app.index(" $('verify').onclick=");end=app.index(" $('proposal').onsubmit=",begin)
 app=app[:begin]+" $('verify').disabled=true;$('rerun').disabled=true;$('cancel').classList.add('hidden');\n"+app[end:]
 app=app.replace("fetch('/data/catalog.json')","fetch('./data/catalog.json')")
 app=app.replace('await status();setInterval(status,1500);','')
 app=app.replace('Start the local workbench server.','Refresh this page; the published catalog could not be loaded.')
 app=app.replace("text('connection','Offline')","text('connection','Published dataset unavailable')")
 (out/'app-public.js').write_text(app,encoding='utf-8')
 html=(web/'index.html').read_text(encoding='utf-8')
 html=re.sub(r'((?:src|href)=\")/(?!/)',r'\1./',html).replace('"/vendor/','"./vendor/')
 html=html.replace('src="./app.js"','src="./app-public.js"')
 html=re.sub(r'(<span id="connection" class="connection">).*?(</span>)',r'\1Published snapshot - no hosted solver\2',html)
 html=re.sub(r'(<span id="footer-status">).*?(</span>)',r'\1OPEN RESEARCH - PUBLISHED RESULTS, NOT LIVE COMPUTE\2',html)
 html=html.replace('<button class="tab selected" data-tab="device">','<button class="tab selected" data-tab="overview">Start here</button><button class="tab" data-tab="device">')
 html=html.replace('id="device" class="view active"','id="device" class="view"')
 html=html.replace('<span id="connection" class="connection">Checking local workerâ€¦</span>','<span id="connection" class="connection">Published snapshot Â· no remote solver</span>')
 html=html.replace('<div class="eyebrow">LOCAL EXPERIMENTS</div>','<div class="eyebrow">DESKTOP EXPERIMENTS</div>')
 html=html.replace('Runs do not silently replace an accepted reference. No public code execution is enabled.','This hosted viewer is read-only. Run approved solvers with the separately configured desktop app; no requests are sent to the research computer.')
 html=html.replace('A fresh local execution is distinct from the playback timeline.','No solver is running on this site. The timeline replays recorded model outputs.')
 html=html.replace('NO ACTIVE EXPERIMENT','PUBLISHED RESULTS ONLY')
 html=html.replace('LOCAL PREVIEW Â· NO PUBLIC HOST CONNECTED','READ-ONLY PUBLICATION CANDIDATE Â· DATA AS OF 2026-09-13')
 html=html.replace('This prototype saves a local JSON brief; it does not submit or publish it.','This form downloads a proposal brief; it does not submit it. Attach the brief to a reviewed contribution through the repository when its public collaboration gate is open.')
 html=html.replace('Public contribution hosting and reviewed live result publication are not connected yet.','No public code-execution endpoint is exposed.')
 html=html.replace('<title>Fusion Workbench â€” open research</title>','<title>Fusion Workbench | Explore the research and evidence</title>')
 html=html.replace('>3D transport</button>','>Our particles</button>')
 html=html.replace('</head>','<meta name="description" content="Inspect fusion reactor concepts, recorded neutron transport, open research reports and the unresolved evidence gaps. Research preview, not a working reactor."><link rel="stylesheet" href="./pages.css"></head>')
 overview=(root/'tools/pages/overview.html').read_text(encoding='utf-8');html=html.replace('<main id="device"',overview+'\n<main id="device"',1)
 html=html.replace('</body>','<script type="module" src="./pages.js"></script><script type="module" src="./power-summary.js"></script><script type="module" src="./beginner.js"></script><script type="module" src="./progress-preview.js"></script></body>')
 importmap=re.search(r'<script type="importmap">(.*?)</script>',html,re.S).group(1)
 digest=base64.b64encode(hashlib.sha256(importmap.encode()).digest()).decode()
 csp="default-src 'self'; script-src 'self' 'sha256-"+digest+"'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'none'; worker-src 'none'"
 html=html.replace('<head>','<head><meta http-equiv="Content-Security-Policy" content="'+csp+'">',1)
 (out/'index.html').write_text(html,encoding='utf-8');(out/'.nojekyll').write_text('')
 for name in ['pages.css','pages.js','power-summary.js','beginner.js','progress-preview.js']:shutil.copyfile(root/'tools/pages'/name,out/name)
 for name in ['source-context.png','neutron-study.png']:
  p=root/'media'/name
  if p.exists():dst=out/'media'/name;dst.parent.mkdir(exist_ok=True);shutil.copyfile(p,dst)
 catalog=json.loads((data/'catalog.json').read_text());library=json.loads((data/'research_library.json').read_text());proof=json.loads((root/'project-status.json').read_text())
 published={'schema':'fusion.pages-publication.v1','viewer_version':'0.5.8-progress-roadmap','data_date':library['updated_date'],'research_records':len(library['records']),'data_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in data.iterdir() if p.is_file()},'repository':REPO,'source_branch':BRANCH,'solver_hosted':False,'snapshot_only':True,'public_collaboration_open':True,'release_gate':'Clean public repository; see public-deployment.json for independent hosting verification.','readiness':proof['readiness'],'milestones':proof['milestones']}
 published['plant_decision_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((out/'plant-decision').iterdir()) if p.is_file()}
 published['ec_equilibrium_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((out/'ec-wave').iterdir()) if p.is_file()}
 published['power_progress_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((out/'power-progress').iterdir()) if p.is_file()}
 published['progress_roadmap_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((out/'progress').iterdir()) if p.is_file()}
 published['revision_id']=hashlib.sha256(json.dumps(published,sort_keys=True).encode()).hexdigest()
 (out/'release-status.json').write_text(json.dumps(published,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 from xml.etree.ElementTree import Element,SubElement,tostring,register_namespace
 register_namespace('','http://www.w3.org/2005/Atom');ns='{http://www.w3.org/2005/Atom}';feed=Element(ns+'feed');SubElement(feed,ns+'title').text='Fusion Workbench research updates';SubElement(feed,ns+'id').text='urn:fusion-workbench:research-updates';SubElement(feed,ns+'updated').text=published['data_date']+'T00:00:00Z'
 author=SubElement(feed,ns+'author');SubElement(author,ns+'name').text='Fusion Workbench contributors'
 for item in proof['milestones']:
  e=SubElement(feed,ns+'entry');SubElement(e,ns+'title').text=item['title'];SubElement(e,ns+'id').text='urn:fusion-workbench:'+item['id'];SubElement(e,ns+'updated').text=item['date']+'T00:00:00Z';SubElement(e,ns+'summary').text=item['summary'];SubElement(e,ns+'link',{'href':'https://chriszavadil.github.io/fusion-workbench-open/#research='+item['search'].replace(' ','%20')})
 (out/'feed.xml').write_bytes(tostring(feed,encoding='utf-8',xml_declaration=True))
 # All scientific records are byte-identical copies; only the app shell is adapted.
 source_files=[p for p in out.rglob('*') if p.is_file() and p.name not in {'SITE_MANIFEST.json'} and not any(x.startswith('.') and x!='.nojekyll' for x in p.relative_to(out).parts)]
 (out/'SITE_MANIFEST.json').write_text(json.dumps({'schema':'fusion.static-site-manifest.v1','data_date':published['data_date'],'backend_required':False,'publication_verified':False,'files':{p.relative_to(out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(source_files)}},indent=2)+'\n')
 return {'files':len(source_files),'research_records':len(library['records']),'bytes':sum(p.stat().st_size for p in source_files),'backend_required':False,'publication_verified':False}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=ROOT);args=ap.parse_args();print(json.dumps(build(args.root)))
