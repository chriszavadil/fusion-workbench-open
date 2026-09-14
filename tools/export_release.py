"""Allowlisted public export; raw private history/binaries are never copied.

This scanner is a supplementary check, not a secrecy or licensing guarantee.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import zipfile

ROOT_FILES={'LICENSE','README.md','SECURITY.md','CONTRIBUTING.md','DATA_SCOPE.md','PROJECT_POLICY.json','THIRD_PARTY_NOTICES.md','Launch_Workbench.cmd'}
PATTERNS=[
    re.compile(r'(?i)(?:gh[pousr]_[a-z0-9]{20,}|github_pat_[a-z0-9_]{20,}|AKIA[A-Z0-9]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----)'),
    re.compile(r'(?i)https?://[^\s/]+:[^\s@]+@'),
    re.compile(r'(?i)[?&](?:access_token|token|sig|signature|password|api_key)=[^\s"\']+'),
    re.compile(r'(?i)[a-z]:[\\/](?:users|documents and settings)[\\/][^\s"\']+'),
    re.compile(r'/(?:home|Users)/[^\s/]+/'),
    re.compile(r'(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b'),
]

def allowed(path:Path,root:Path)->bool:
    rel=path.relative_to(root)
    if any(x.startswith('.') or x in ('Saved','Intermediate','DerivedDataCache','Generated','node_modules') for x in rel.parts):return False
    if len(rel.parts)==1:return rel.name in ROOT_FILES
    top=rel.parts[0];suffix=path.suffix.lower()
    if top in ('tools','tests'):return suffix=='.py'
    if top in ('docs','schema'):return suffix in ('.md','.json')
    if top=='app':return suffix in ('.py','.html','.css','.js','.json','.txt','.glb','.png','.svg')
    if top=='unreal':return rel.as_posix()=='unreal/FusionWorkbench.uproject' or (rel.parts[1]=='Config' and suffix=='.ini')
    return False

def glb_metadata(raw:bytes)->str:
    if len(raw)<20 or raw[:4]!=b'glTF' or struct.unpack_from('<I',raw,4)[0]!=2 or struct.unpack_from('<I',raw,8)[0]!=len(raw):
        raise ValueError('Invalid binary glTF')
    n,kind=struct.unpack_from('<II',raw,12)
    if kind!=0x4e4f534a or 20+n>len(raw):raise ValueError('Missing glTF JSON chunk')
    text=raw[20:20+n].decode('utf-8').rstrip(' \0');doc=json.loads(text)
    for group in ('buffers','images'):
        for item in doc.get(group,[]):
            if 'uri' in item:raise ValueError('External/embedded textual URI not admitted in release glTF')
    return text

def inspect_file(path:Path,deny:list[str])->list[str]:
    raw=path.read_bytes()
    if path.suffix.lower()=='.glb':text=glb_metadata(raw)
    elif path.suffix.lower()=='.png':
        # Preview PNGs are not part of the current public allowlist in practice.
        raise ValueError('PNG metadata requires separate review')
    else:text=raw.decode('utf-8-sig')
    findings=[]
    for i,p in enumerate(PATTERNS):
        if p.search(text):findings.append(f'sensitive-pattern-{i+1}')
    for i,term in enumerate(deny):
        if len(term)>=3 and re.search(r'(?i)(?<![a-z0-9])'+re.escape(term)+r'(?![a-z0-9])',text):findings.append(f'private-identifier-{i+1}')
    return findings

def export(root:Path,destination:Path,deny:list[str])->dict:
    files=[p for p in root.rglob('*') if p.is_file() and not p.is_symlink() and allowed(p,root)]
    findings=[];manifest={}
    for p in sorted(files):
        result=inspect_file(p,deny)
        if result:findings.append({'file':p.relative_to(root).as_posix(),'classes':result})
        manifest[p.relative_to(root).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
    if findings:
        # Classes/relative names only; matched private strings are never emitted.
        raise ValueError(json.dumps({'release_blocked':True,'findings':findings}))
    report={'schema':'fusion-workbench.release-review.v1','files_scanned':len(files),
            'automated_privacy_gate':'passed','git_history_included':False,'raw_solver_logs_included':False,
            'hosted_publicly':False,'human_release_review_required':True,'file_sha256':manifest}
    destination.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(files):z.write(p,'FusionWorkbench/'+p.relative_to(root).as_posix())
        z.writestr('FusionWorkbench/RELEASE_REVIEW.json',json.dumps(report,indent=2)+'\n')
    return {'release_bytes':destination.stat().st_size,'release_sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),
            'files_scanned':len(files),'automated_privacy_gate':'passed','hosted_publicly':False,'human_release_review_required':True}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--destination',type=Path,required=True);ap.add_argument('--deny-file',type=Path)
    a=ap.parse_args();deny=json.loads(a.deny_file.read_text())['terms'] if a.deny_file else []
    print(json.dumps(export(a.root,a.destination,deny)))
