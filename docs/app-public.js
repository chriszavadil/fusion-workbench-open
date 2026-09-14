import {DeviceViewer} from './viewer.js';
const $=id=>document.getElementById(id);
const fmt=(v,n=2)=>Number(v).toLocaleString(undefined,{maximumFractionDigits:n,minimumFractionDigits:n});
let catalog,config,viewer,selected='solenoid',playing=false,lastFrame=0,jobId=null,worker=false;
const colors={plasma:'#65dfce',solenoid:'#c98e5c',first_wall:'#4aabbc',blanket:'#d4b479',shield:'#758ea0',vessel:'#b2c8d3',coils:'#8fa1a8'};
function text(id,value){$(id).textContent=value;}
function valueList(pairs){const box=$('component-values');box.replaceChildren();for(const [label,value] of pairs){const row=document.createElement('div');row.className='value';const name=document.createElement('span');name.textContent=label;const val=document.createElement('b');val.textContent=value;row.append(name,val);box.append(row);}}
function inspect(id){selected=id;const c=config.components.find(x=>x.id===id);if(!c)return;text('component-title',c.title);text('component-status',c.evidence.replaceAll('_',' '));text('component-detail',c.detail);
 const m=config.metrics,g=config.geometry;
 const entries={
  plasma:[['Major / minor radius',`${fmt(g.major_radius_m)} / ${fmt(g.minor_radius_m)} m`],['Elongation',fmt(g.elongation)],['Triangularity',fmt(g.triangularity)],['Internal multiplier',fmt(m.internal_confinement_multiplier,3)]],
  solenoid:[['Inner radius',`${fmt(g.solenoid_inner_radius_m,3)} m`],['Radial width',`${fmt(g.solenoid_radial_width_m,3)} m`],['Height',`${fmt(g.solenoid_height_m,3)} m`],['Model hoop stress',`${fmt(m.solenoid_hoop_MPa)} MPa`],['Model cycle life',fmt(m.fatigue_cycles,0)],['Required cycles',fmt(m.required_fatigue_cycles,0)],['Uncertainty margin','Not qualified']],
  first_wall:[['Inboard thickness',`${fmt(g.first_wall_inboard_m*1000,1)} mm`],['Outboard thickness',`${fmt(g.first_wall_outboard_m*1000,1)} mm`],['Heat map','Not available']],
  blanket:[['Inboard thickness',`${fmt(g.blanket_inboard_m)} m`],['Outboard thickness',`${fmt(g.blanket_outboard_m)} m`],['Matched TBR','Not calculated']],
  shield:[['Inboard radial build',`${fmt(g.shield_inboard_m)} m`],['Outboard radial build',`${fmt(g.shield_outboard_m)} m`],['Dose / shielding validation','Not supplied']],
  vessel:[['Inboard thickness',`${fmt(g.vessel_inboard_m)} m`],['Outboard thickness',`${fmt(g.vessel_outboard_m)} m`],['Structural qualification','Not established']],
  coils:[['Native coil count',fmt(g.toroidal_coil_count,0)],['Displayed coil paths','Schematic'],['Spatial field','Not calculated']]
 };
 valueList(entries[id]||[]);viewer?.select(id);
}
async function changeConfiguration(id){config=catalog.configurations.find(c=>c.id===id);if(!config)return;
 text('config-title',config.title);text('major-radius',`${fmt(config.geometry.major_radius_m,2)} m`);text('flat-net',`${fmt(config.metrics.flat_top_net_MW,1)} MW`);text('average-net',`${fmt(config.metrics.conditional_average_net_MW,2)} MW`);text('h-factor',fmt(config.metrics.internal_confinement_multiplier,3));text('source-hash',config.provenance.artifact_sha256);
 $('limitations').replaceChildren(...config.scope.map(s=>{const p=document.createElement('p');p.textContent=s;return p;}));
 inspect(selected);drawChart();updateTime();
 $('model-loading').classList.remove('hidden');text('model-loading','Loading dimension-linked model…');
 try{await viewer.load(id);$('model-loading').classList.add('hidden');}catch(e){text('model-loading','Model asset unavailable. No substitute geometry is being shown.');console.error('Model load failed');}
}
function drawChart(){const p=config.pulse,max=Math.max(...p.series.gross_MW)*1.05,min=Math.min(...p.series.net_MW)-40;
 const x=t=>36+t/p.time_s.at(-1)*746,y=v=>86-(v-min)/(max-min)*72;
 let html=`<line x1="36" y1="${y(0)}" x2="782" y2="${y(0)}" stroke="#46565f" stroke-dasharray="3 4"/><text x="0" y="17" fill="#8b9aa5" font-size="9">MW</text>`;
 for(const [key,color,label] of [['gross_MW','#718da1','Gross'],['net_MW','#68ddca','Net']]){
  const points=p.time_s.map((t,i)=>`${x(t)},${y(p.series[key][i])}`).join(' ');
  html+=`<polyline points="${points}" fill="none" stroke="${color}" stroke-width="2"/>`;
 }
 html+=`<line id="cursor-line" x1="36" y1="8" x2="36" y2="93" stroke="#e3b773" stroke-width="1"/><text x="630" y="12" fill="#718da1" font-size="9">GROSS</text><text x="695" y="12" fill="#68ddca" font-size="9">NET</text>`;
 $('chart').innerHTML=html;
}
function interpolate(time,key){const p=config.pulse;let i=p.time_s.findIndex((t,j)=>j>0&&t>=time);if(i<0)i=p.time_s.length-1;let lo=i-1,dt=p.time_s[i]-p.time_s[lo];const f=dt?Math.min(1,Math.max(0,(time-p.time_s[lo])/dt)):1;return p.series[key][lo]*(1-f)+p.series[key][i]*f;}
function updateTime(){if(!config)return;const time=+$('time').value/1000*config.pulse.time_s.at(-1);let i=config.pulse.time_s.findIndex((t,j)=>j>0&&t>=time);if(i<0)i=6;text('phase',config.pulse.phase_names[i-1]);text('time-label',`${fmt(time,0)} / ${fmt(config.metrics.cycle_s,0)} s`);text('instant-power',`${fmt(interpolate(time,'net_MW'),1)} MW`);const line=$('cursor-line');if(line){line.setAttribute('x1',36+time/config.metrics.cycle_s*746);line.setAttribute('x2',36+time/config.metrics.cycle_s*746);}}
function animate(now){if(playing&&config){const delta=Math.min(now-lastFrame,100);$('time').value=(+$('time').value+delta/60)%1000;updateTime();}lastFrame=now;requestAnimationFrame(animate);}
function buildEvidence(){text('progress-summary',catalog.progress_summary);text('inventory',`${catalog.inventory.tracked_artifacts_catalogued} research artifacts catalogued · ${catalog.configurations.length} configurations linked · Historical raw-run integration incomplete`);
 const box=$('track-grid');for(const t of catalog.tracks){const card=document.createElement('article');card.className='track';const title=document.createElement('h3');title.textContent=t.title;const model=document.createElement('strong');model.textContent=t.model_status;const state=document.createElement('div');state.className='state';state.textContent=t.validation_status;const p=document.createElement('p');p.textContent=t.summary;const count=document.createElement('div');count.className='count';count.textContent=`${t.catalogued_artifacts} catalogued artifacts · ${t.integration.replaceAll('_',' ')}`;card.append(title,model,state,p,count);box.append(card);}
 for(const r of catalog.historical_rejections){const row=document.createElement('div');row.className='rejection';const title=document.createElement('strong');title.textContent=`${r.title} — ${r.status.replaceAll('_',' ')}`;const p=document.createElement('p');p.textContent=r.reason;row.append(title,p);$('rejections').append(row);}}
async function boot(){const response=await fetch('./data/catalog.json');if(!response.ok)throw new Error('Catalog unavailable');catalog=await response.json();window.workbenchCatalog=catalog;
 try{viewer=new DeviceViewer($('viewport'),inspect);}catch(e){text('model-loading','WebGL is unavailable in this browser. Evidence remains accessible.');viewer={load:async()=>{throw e;},setLayer:()=>{},setCutaway:()=>{},reset:()=>{},select:()=>{}};}
 for(const c of catalog.configurations){const o=document.createElement('option');o.value=c.id;o.textContent=c.title;$('configuration').append(o);}
 for(const c of catalog.configurations[0].components){const row=document.createElement('label');row.className='layer';const check=document.createElement('input');check.type='checkbox';check.checked=true;check.setAttribute('aria-label',`Show ${c.title}`);check.onchange=()=>viewer.setLayer(c.id,check.checked);const dot=document.createElement('span');dot.className='dot';dot.style.background=colors[c.id];const b=document.createElement('button');b.type='button';b.textContent=c.title.replace(' envelope','');b.onclick=e=>{e.preventDefault();inspect(c.id);};row.append(check,dot,b);$('layers').append(row);}
 $('configuration').onchange=()=>changeConfiguration($('configuration').value);$('time').oninput=updateTime;$('play').onclick=()=>{playing=!playing;text('play',playing?'Ⅱ':'▶');};let cut=true;$('cutaway').onclick=()=>{cut=!cut;viewer.setCutaway(cut);text('cutaway',`Cutaway ${cut?'on':'off'}`);$('cutaway').setAttribute('aria-pressed',cut);$('cutaway').classList.toggle('active',cut);};$('reset').onclick=()=>viewer.reset();$('presentation').onclick=()=>document.body.classList.toggle('presenting');document.addEventListener('keydown',e=>{if(e.key==='Escape')document.body.classList.remove('presenting');});
 for(const tab of document.querySelectorAll('.tab'))tab.onclick=()=>{document.querySelectorAll('.tab').forEach(t=>t.classList.toggle('selected',t===tab));document.querySelectorAll('.view').forEach(v=>v.classList.toggle('active',v.id===tab.dataset.tab));};
 $('verify').disabled=true;$('rerun').disabled=true;$('cancel').classList.add('hidden');
 $('proposal').onsubmit=e=>{e.preventDefault();const form=new FormData(e.target);const proposal={schema:'fusion-workbench.proposal.v1',configuration_id:config.id,question:form.get('question'),prior_art:form.get('prior_art'),acceptance_criterion:form.get('acceptance'),status:'local_draft_not_submitted'};const url=URL.createObjectURL(new Blob([JSON.stringify(proposal,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='fusion-research-proposal.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
 buildEvidence();await changeConfiguration(catalog.configurations[0].id);requestAnimationFrame(animate);window.workbenchReady=true;
}
boot().catch(()=>{text('model-loading','Evidence catalog could not be loaded. Refresh this page; the published catalog could not be loaded.');text('connection','Published dataset unavailable');});
