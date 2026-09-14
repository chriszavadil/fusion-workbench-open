// MIT. Displays completed local transport tallies; no code execution or design edits.
const by=id=>document.getElementById(id),NS='http://www.w3.org/2000/svg';let data=null;
function svg(tag,attrs){const e=document.createElementNS(NS,tag);for(const [k,v]of Object.entries(attrs))e.setAttribute(k,String(v));return e;}
function label(svgroot,text,x,y){const e=svg('text',{x,y,fill:'#9eb6c4','font-size':14});e.textContent=text;svgroot.append(e);}
function show(index){if(!data)return;const r=data.cases[index];by('neutron-title').textContent=r.title;
 by('neutron-metrics').textContent=`Tritons produced / incident neutron: ${r.tritons_per_incident_neutron.toFixed(5)} ± ${r.tritons_standard_error.toFixed(5)}\nDeposited energy: ${r.heating_MeV_per_incident_neutron.toFixed(3)} ± ${r.heating_standard_error_MeV.toFixed(3)} MeV / incident neutron\n${r.source_histories.toLocaleString()} simulated source histories; uncertainty = 1 Monte Carlo standard error only.`;
 const geo=by('neutron-geometry');geo.replaceChildren();const scale=Math.min(360/data.module_depth_m,320/data.module_width_m),ox=75,oy=40;
 geo.append(svg('rect',{x:ox,y:oy,width:scale*data.module_depth_m,height:scale*data.module_width_m,fill:'none',stroke:'#38cfb7','stroke-width':2}));geo.append(svg('line',{x1:ox-7,y1:oy,x2:ox-7,y2:oy+scale*data.module_width_m,stroke:'#ecb358','stroke-width':5}));
 label(geo,'14.1 MeV source →',10,22);label(geo,'1 m depth; reflecting side boundaries',45,389);
 if(index){const x=index===1?data.module_depth_m-data.header_outer_radius_m:data.header_outer_radius_m;for(const y of [data.module_width_m/6,data.module_width_m/2,5*data.module_width_m/6])for(const [radius,color] of [[data.header_outer_radius_m,'#9eb6c4'],[data.header_inner_radius_m,'#ecb358']])geo.append(svg('circle',{cx:ox+x*scale,cy:oy+y*scale,r:radius*scale,fill:'none',stroke:color,'stroke-width':2}));}
 else label(geo,'Uniformly mixed inventory',ox+15,oy+120);
 const plot=by('neutron-profile');plot.replaceChildren();const base=data.cases[0].depth_tritons_per_incident_neutron,ys=r.depth_tritons_per_incident_neutron,max=Math.max(...base,...ys)*1.1;
 plot.append(svg('path',{d:'M 55 40 V 345 H 575',fill:'none',stroke:'#9eb6c4'}));for(const [values,color]of [[base,'#9eb6c4'],[ys,'#38cfb7']])plot.append(svg('polyline',{points:values.map((v,i)=>`${55+520*(i+.5)/40},${345-280*v/max}`).join(' '),fill:'none',stroke:color,'stroke-width':2}));
 label(plot,'Tritons / incident neutron in each 2.5 cm bin',55,22);label(plot,`${max.toFixed(4)}`,2,58);label(plot,'0 cm',55,376);label(plot,'Blanket depth',275,376);label(plot,'100 cm',525,376);
 by('neutron-decision').textContent=data.decision;document.querySelectorAll('[data-neutron-layout]').forEach(b=>b.setAttribute('aria-pressed',String(Number(b.dataset.neutronLayout)===index)));}
for(const b of document.querySelectorAll('[data-neutron-layout]'))b.onclick=()=>show(Number(b.dataset.neutronLayout));
fetch('./data/neutronics.json').then(r=>{if(!r.ok)throw Error();return r.json();}).then(d=>{if(d.schema!=='fusion.neutronics-view.v1'||d.cases.length!==3||d.physical_validation!==false)throw Error();data=d;show(0);}).catch(()=>{by('neutron-title').textContent='Completed neutron study unavailable';});
