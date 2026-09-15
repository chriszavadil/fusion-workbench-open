// Read-only publication status. No workstation connections, job POSTs, or analytics.
const $=id=>document.getElementById(id);let revision=null;
function openView(id,search){document.querySelector(`.tab[data-tab="${id}"]`)?.click();if(search){$('research-query').value=search;$('research-query').dispatchEvent(new Event('input'));}document.body.classList.remove('presenting');}
for(const b of document.querySelectorAll('[data-open]'))b.addEventListener('click',()=>openView(b.dataset.open,b.dataset.search));
function element(tag,text,cls){const el=document.createElement(tag);el.textContent=text;if(cls)el.className=cls;return el;}
async function update(first=false){try{const response=await fetch('./release-status.json',{cache:'no-store'});if(!response.ok)throw Error();const d=await response.json();if(d.schema!=='fusion.pages-publication.v1'||!d.snapshot_only)throw Error();
 if(revision&&revision!==d.revision_id){$('publication-check').textContent='A newer published snapshot is available. Reload to use it.';return;}revision=d.revision_id;
 $('pages-version').textContent=`${d.viewer_version} · evidence through ${d.data_date}`;$('pages-records').textContent=d.research_records;
 if(!first)$('publication-check').textContent=`Checked ${new Date().toLocaleTimeString()}: this published snapshot is current.`;
 if(first){const grid=$('pages-readiness');for(const row of d.readiness){const card=element('article','','readiness-card');card.append(element('span',row.status,'readiness-label '+row.level),element('h3',row.title),element('p',row.detail));grid.append(card);}
 const history=$('pages-history');for(const m of d.milestones){const card=element('article','','history-entry');const b=element('button','Read evidence','small');b.onclick=()=>openView('research',m.search);card.append(element('time',m.date),element('h3',m.title),element('p',m.summary),b);history.append(card);}
 const sub=element('a','Subscribe to the research update feed');sub.href='./feed.xml';sub.className='feed-link';history.after(sub);}
 $('collaboration-status').textContent=d.public_collaboration_open?'Contribution issues are public. Submitted code is reviewed before any experiment is run.':'The repository is currently private. Its source/issue links require access; the reviewed source archive and this site can be shared once Pages is enabled. No submission is automatically executed.';
 }catch{$('publication-check').textContent='Publication status unavailable; no live-run status is being inferred.';}}
$('check-publication').onclick=()=>update(false);update(true);setInterval(()=>{if(!document.hidden)update(false);},300000);
async function route(){if(location.hash==='#benchmarks'){for(let n=0;n<100&&!window.workbenchReady;n++)await new Promise(r=>setTimeout(r,100));openView('benchmarks');return;}const m=location.hash.match(/^#research=(.*)$/);if(!m)return;for(let n=0;n<100&&!window.workbenchReady;n++)await new Promise(r=>setTimeout(r,100));openView('research',decodeURIComponent(m[1]));}
window.addEventListener('hashchange',route);route();
