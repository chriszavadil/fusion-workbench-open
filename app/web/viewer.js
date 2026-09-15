import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

export class DeviceViewer {
  constructor(container, onSelect) {
    this.container=container; this.onSelect=onSelect; this.model=null; this.cutaway=true;
    this.layers=new Map(); this.loading=0;
    this.scene=new THREE.Scene();
    this.camera=new THREE.PerspectiveCamera(42,1,.1,400);
    this.renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio,2));
    this.renderer.setClearColor(0x000000,0);
    this.renderer.outputColorSpace=THREE.SRGBColorSpace;
    this.renderer.toneMapping=THREE.ACESFilmicToneMapping;this.renderer.toneMappingExposure=1.35;
    container.appendChild(this.renderer.domElement);
    this.controls=new OrbitControls(this.camera,this.renderer.domElement);
    this.controls.enableDamping=true;this.controls.dampingFactor=.07;
    this.controls.minDistance=5;this.controls.maxDistance=140;
    this.scene.add(new THREE.HemisphereLight(0xc9e7f3,0x263340,3));
    for(const [pos,color,power] of [[[15,30,25],0xffeee0,4],[[-25,12,5],0x83cfe3,3],[[0,25,-30],0xffffff,4]]){
      const light=new THREE.DirectionalLight(color,power);light.position.set(...pos);this.scene.add(light);
    }
    const grid=new THREE.GridHelper(60,30,0x3b545e,0x243740);grid.position.y=-10.5;
    grid.material.transparent=true;grid.material.opacity=.38;this.scene.add(grid);
    this.ray=new THREE.Raycaster();this.pointer=new THREE.Vector2();this.pointerDown=null;
    this.renderer.domElement.addEventListener('pointerdown',e=>{this.pointerDown=[e.clientX,e.clientY];});
    this.renderer.domElement.addEventListener('pointerup',e=>{
      if(!this.model||!this.pointerDown||Math.hypot(e.clientX-this.pointerDown[0],e.clientY-this.pointerDown[1])>4)return;
      const rect=container.getBoundingClientRect();this.pointer.set((e.clientX-rect.left)/rect.width*2-1,-(e.clientY-rect.top)/rect.height*2+1);
      this.ray.setFromCamera(this.pointer,this.camera);
      const hits=this.ray.intersectObject(this.model,true).filter(h=>h.object.visible&&this.isVisible(h.object));
      if(hits.length){const id=this.component(hits[0].object);if(id){this.select(id);this.onSelect(id);}}
    });
    this.resizeObserver=new ResizeObserver(()=>this.resize());this.resizeObserver.observe(container);this.resize();this.reset();
    this.needsRender=true;this.controls.addEventListener('change',()=>{this.needsRender=true;});
    this.renderer.setAnimationLoop(()=>{if(document.hidden||!this.container.clientWidth||!this.container.clientHeight)return;this.controls.update();if(this.needsRender){this.renderer.render(this.scene,this.camera);this.needsRender=false;}});
  }
  isVisible(o){for(let p=o;p;p=p.parent)if(!p.visible)return false;return true;}
  component(o){for(let p=o;p;p=p.parent)if(p.userData.component_id)return p.userData.component_id;return null;}
  resize(){this.needsRender=true;const w=this.container.clientWidth,h=this.container.clientHeight;if(!w||!h)return;this.renderer.setSize(w,h,false);this.camera.aspect=w/h;this.camera.updateProjectionMatrix();}
  reset(){this.needsRender=true;this.camera.position.set(26,18,28);this.controls.target.set(0,0,0);this.controls.update();}
  async load(id){
    const ticket=++this.loading;
    const asset=await new GLTFLoader().loadAsync(`/assets/${id}.glb`);
    if(ticket!==this.loading)return;
    if(this.model){this.scene.remove(this.model);this.model.traverse(o=>{if(o.geometry)o.geometry.dispose();if(o.material){for(const m of Array.isArray(o.material)?o.material:[o.material])m.dispose();}});}
    this.model=asset.scene;
    this.model.traverse(o=>{if(o.isMesh){o.material=o.material.clone();o.userData.baseEmission=o.material.emissive?.clone();o.userData.baseIntensity=o.material.emissiveIntensity;}});
    this.scene.add(this.model);this.applyVisibility();this.reset();this.select('solenoid');
    window.workbenchModelReady=id;
  }
  applyVisibility(){this.needsRender=true;if(!this.model)return;this.model.traverse(o=>{
    const ownId=o.userData.component_id;
    if(ownId)o.visible=this.layers.get(ownId)!==false&&!(this.cutaway&&o.userData.cutaway_segment===true);
  });}
  setCutaway(value){this.cutaway=value;this.applyVisibility();}
  setLayer(id,value){this.layers.set(id,value);this.applyVisibility();}
  select(id){this.needsRender=true;if(!this.model)return;this.model.traverse(o=>{
    if(!o.isMesh||!o.material.emissive)return;
    if(o.userData.baseEmission)o.material.emissive.copy(o.userData.baseEmission);
    o.material.emissiveIntensity=o.userData.baseIntensity??1;
    if(this.component(o)===id&&id!=='plasma'){o.material.emissive.set(0x28695e);o.material.emissiveIntensity=.5;}
  });}
}
