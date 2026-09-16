// Pure Node DOM-contract test. No browser, navigation, HTTP or solver execution.
import fs from 'node:fs';import vm from 'node:vm';import assert from 'node:assert/strict';
const root=process.argv[2];const data=JSON.parse(fs.readFileSync(root+'/docs/ec-wave/data.json','utf8'));
class Element{constructor(tag='div'){this.tagName=tag;this.children=[];this.attributes={};this.value='0';this.textContent='';}append(...items){this.children.push(...items);}replaceChildren(...items){this.children=items;}setAttribute(k,v){this.attributes[k]=v;}}
const ids=new Map();const defaults={'analytic-case':'alternative30','width':'0.2','inclination':'1','equilibrium-select':'0','ray-progress':'0'};
function get(id){if(!ids.has(id)){const e=new Element();e.value=defaults[id]??'0';ids.set(id,e);}return ids.get(id);}
const errors=[];const context=vm.createContext({document:{getElementById:get,createElement:t=>new Element(t),createElementNS:(_n,t)=>new Element(t)},fetch:async url=>{assert.equal(url,'data.json');return {ok:true,json:async()=>data};},requestAnimationFrame:()=>0,console:{error:e=>errors.push(String(e))}});
vm.runInContext(fs.readFileSync(root+'/docs/ec-wave/view.js','utf8'),context,{timeout:10000});await new Promise(resolve=>setImmediate(resolve));await new Promise(resolve=>setImmediate(resolve));assert.deepEqual(errors,[]);
assert.equal(get('equilibrium-select').children.length,4);assert.match(get('q-range').textContent,/3\.83/);
function verifyFinite(e){for(const[k,v]of Object.entries(e.attributes)){if(['points','x','y','cx','cy','x1','y1','x2','y2'].includes(k))assert.ok(!/NaN|Infinity|undefined/.test(v),k+':'+v);}for(const ch of e.children)verifyFinite(ch);}
for(let i=0;i<4;i++){get('equilibrium-select').value=String(i);get('equilibrium-select').onchange();assert.match(get('eq-status').textContent,/NOT PASSED/);verifyFinite(get('flux-plot'));verifyFinite(get('q-plot'));}
for(const c of ['control75','alternative30'])for(const w of ['0.1','0.2'])for(const a of ['0.5','1']){get('analytic-case').value=c;get('width').value=w;get('inclination').value=a;get('width').onchange();assert.match(get('analytic-status').textContent,/7 of56/);verifyFinite(get('frequency-plot'));}
get('ray-progress').value='1000';get('ray-progress').oninput();assert.match(get('ray-inspect').textContent,/343\/343/);verifyFinite(get('ray-plot'));assert.deepEqual(errors,[]);
console.log(JSON.stringify({passed:true,scope:'Node DOM contract only; not browser rendering or interaction verification',equilibrium_selections:4,analytic_selections:8,all_reference_points_accessible:true,network_requests:0,browser_navigation:0,scientific_jobs:0}));
