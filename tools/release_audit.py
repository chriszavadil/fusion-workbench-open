"""Read-only release integrity/privacy scan; not a guarantee of anonymity.
Pass private identifiers through a local deny-file, never hard-code them here.
Compiler layouts, engine source, credentials, private history and raw logs are excluded.
"""
import argparse,hashlib,io,json,re,struct,tokenize
from pathlib import Path
TEXT={'.py','.cpp','.h','.cs','.ini','.md','.txt','.json','.html','.js','.css','.cmd','.yml','.yaml','.toml','.uproject','.gitignore','.gitattributes'}
SECRET=re.compile(rb'gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|AKIA[A-Z0-9]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')
EMAIL=re.compile(r'(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b')
def inspect(root,terms):
 findings=[];records={}
 for p in sorted(root.rglob('*')):
  rel=p.relative_to(root)
  if any(x in {'.git','.local','__pycache__','.pytest_cache'} for x in rel.parts):continue
  if p.is_symlink():findings.append({'file':rel.as_posix(),'class':'symlink_not_released'});continue
  if not p.is_file():continue
  raw=p.read_bytes();records[rel.as_posix()]=hashlib.sha256(raw).hexdigest()
  if p.suffix.lower() in {'.pdb','.log','.pem','.key','.blend','.vsix'} or p.name in {'.env','execution.json'}:findings.append({'file':rel.as_posix(),'class':'private_or_unreviewed_file_type'})
  if SECRET.search(raw):findings.append({'file':rel.as_posix(),'class':'credential_pattern'})
  if re.search(rb'(?i)[?&](?:token|access_token|sig|signature|api_key|password)=[a-z0-9_%+/-]{12,}',raw):findings.append({'file':rel.as_posix(),'class':'signed_url_or_credential_parameter'})
  if re.search(rb'(?i)[a-z]:[\\/]+Users[\\/]+[a-z0-9_.-]+',raw):findings.append({'file':rel.as_posix(),'class':'personal_home_path'})
  for i,t in enumerate(terms):
   if len(t)>=3 and any(re.search(r'(?i)(?<![a-z0-9])'+re.escape(t)+r'(?![a-z0-9])',raw.decode(enc,errors='ignore')) for enc in ('utf-8','utf-16-le')):findings.append({'file':rel.as_posix(),'class':'private_identifier_'+str(i)})
  if p.suffix.lower() in TEXT or p.name in {'LICENSE','SECURITY.md','CONTRIBUTING.md'}:
   text=raw.decode('utf-8-sig');candidate=text
   if p.suffix.lower()=='.py':
    candidate='\n'.join(t.string for t in tokenize.generate_tokens(io.StringIO(text).readline) if t.type in {tokenize.STRING,tokenize.COMMENT})
   # Matrix-product expressions are code, not contact addresses.
   if any(not e.lower().endswith(('@example.com','.invalid')) for e in EMAIL.findall(candidate)):findings.append({'file':rel.as_posix(),'class':'email_requires_context_review'})
 return {'schema':'fusion.release-audit.v1','files':records,'findings':findings,'passed':not findings,'automated_scan_only':True}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--deny-file',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 terms=json.loads(a.deny_file.read_text()).get('terms',[]) if a.deny_file else []
 result=inspect(a.root,terms);a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'passed':result['passed'],'files_scanned':len(result['files']),'findings':result['findings']}));raise SystemExit(0 if result['passed'] else 2)
