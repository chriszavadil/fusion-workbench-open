// Original MIT research reader: textContent only, no remote HTML or commands.
const $=id=>document.getElementById(id);
let packet=null,selected=null;
const words=q=>q.toLowerCase().trim().split(/\s+/).filter(Boolean);
function matches(r){const scope=$('research-scope').checked,config=$('configuration').value;
 if(scope&&!r.configuration_scope.split(/\s+/).includes(config))return false;
 const hay=[r.title,r.body,r.date,r.track,r.status].join(' ').toLowerCase();return words($('research-query').value).every(x=>hay.includes(x));}
function choose(r){selected=r;$('research-title').textContent=r.title;
 $('research-meta').textContent=`${r.date} | ${r.track} | ${r.status} | Scope: ${r.configuration_scope}`;
 $('research-warning').textContent=r.scope_notice;
 $('research-body').textContent=r.body;
 $('research-provenance').textContent=`Content SHA-256: ${r.content_sha256}\nSource: ${r.source_path}\nOriginal source SHA-256: ${r.source_sha256}\nPrivacy-transformed: ${r.privacy_transformed ? 'yes' : 'no'}`;
 $('research-sources').replaceChildren();for(const value of r.external_sources||[]){try{const u=new URL(value);if(u.protocol!=='https:'||u.username||u.password)continue;const a=document.createElement('a');a.href=u.href;a.target='_blank';a.rel='noopener noreferrer';a.textContent=u.hostname+' — '+u.pathname;$('research-sources').append(a);}catch{}}
 $('research-body').scrollTop=0;document.querySelectorAll('.research-card').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.record===r.id)));}
function filter(){if(!packet)return;const rows=packet.records.filter(matches);$('research-results').replaceChildren();
 $('research-count').textContent=`${rows.length} of ${packet.records.length} readable records | Updated ${packet.updated_date}`;
 for(const r of rows){const b=document.createElement('button');b.className='research-card';b.dataset.record=r.id;b.setAttribute('aria-pressed',String(selected?.id===r.id));
 const h=document.createElement('strong');h.textContent=r.title;const detail=document.createElement('span');detail.textContent=`${r.date} | ${r.track} | ${r.status}`;
 b.append(h,detail);b.onclick=()=>choose(r);$('research-results').append(b);}
 if(!rows.length)$('research-results').textContent='No matching records. Change the search or filter.';}
async function load(){try{const response=await fetch('/api/research');if(!response.ok)throw new Error();packet=await response.json();
 if(packet.schema!=='fusion.research-library.v1'||!Array.isArray(packet.records))throw new Error();filter();if(packet.records.length)choose(packet.records[0]);
 }catch{$('research-count').textContent='Research library unavailable. The device data has not changed.';}}
$('research-query').addEventListener('input',filter);$('research-scope').addEventListener('change',filter);$('configuration').addEventListener('change',filter);
$('research-save').onclick=()=>{if(!selected)return;const url=URL.createObjectURL(new Blob([selected.body],{type:'text/markdown;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download=selected.id+'.md';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
load();
