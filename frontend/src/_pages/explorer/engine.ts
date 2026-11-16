import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';
import { animate, type JSAnimation } from 'animejs';
import type { FlameState } from '@/entities/saffire/mission';

// SAFFIRE-II 3D explorer engine. Stylised vehicle and Earth (not to scale); the experiment is enlarged.
// Flame state, CO₂ reading and heat come from the evidence through `update`.

export type Part = 'cargo' | 'service' | 'array' | 'rack' | 'sample' | 'igniter' | 'tc' | 'co2' | 'earth';
export type View = 'orbit' | 'craft' | 'rack' | 'flame';
export type EngineInput = { flame: FlameState; sensed: number; heat: number; intensity: number; reading: number | null; burning: boolean };
export type SampleSpec = { material: string; opposed: boolean; leadInCm: number | null; regressCm: number };
type Opts = { canvas: HTMLCanvasElement; pip: HTMLCanvasElement; overlay: HTMLElement; beacons: Record<Part, string>; onPick: (p: Part) => void; onHover: (p: Part | null, x: number, y: number) => void; onCamera: (dist: number) => void };

const CM = 1.45 / 29, SX0 = -1.325, SX1 = 0.125, SY = -0.2, SENSOR_X = 0.5, EARTH_R = 40, ORBIT_R = 66;
const FLAME_N = 1100, SMOKE_N = 420, SPARK_N = 120;
const MAT_COLOR: Record<string, string> = { Silicone: '#7d8894', SIBAL: '#c4b089', PMMA: '#8cc2d8', PMMA_Nomex: '#8cc2d8' };

const tex = (w: number, h: number, draw: (c: CanvasRenderingContext2D) => void) => { const cv = document.createElement('canvas'); cv.width = w; cv.height = h; draw(cv.getContext('2d')!); const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace; return t; };
const glow = (a: string, b: string) => tex(128, 128, c => { const g = c.createRadialGradient(64, 64, 0, 64, 64, 64); g.addColorStop(0, a); g.addColorStop(.35, b); g.addColorStop(1, 'rgba(0,0,0,0)'); c.fillStyle = g; c.fillRect(0, 0, 128, 128); });
const rng = (s: number) => () => { s = (s * 16807) % 2147483647; return (s - 1) / 2147483646; };

const PARTICLE_VS = 'attribute float aSize; attribute float aAlpha; attribute vec3 aColor; varying float vA; varying vec3 vC; void main(){ vec4 mv = modelViewMatrix * vec4(position,1.0); gl_PointSize = aSize * (300.0 / -mv.z); gl_Position = projectionMatrix * mv; vA = aAlpha; vC = aColor; }';
const PARTICLE_FS = 'varying float vA; varying vec3 vC; void main(){ float d = length(gl_PointCoord - 0.5); if (d > 0.5) discard; float a = pow(1.0 - d * 2.0, 1.6); gl_FragColor = vec4(vC * a, a * vA); }';

function particles(n: number, blending: THREE.Blending) {
  const geo = new THREE.BufferGeometry();
  const pos = new Float32Array(n * 3).fill(-999), col = new Float32Array(n * 3), size = new Float32Array(n), alpha = new Float32Array(n);
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3)); geo.setAttribute('aColor', new THREE.BufferAttribute(col, 3));
  geo.setAttribute('aSize', new THREE.BufferAttribute(size, 1)); geo.setAttribute('aAlpha', new THREE.BufferAttribute(alpha, 1));
  const mat = new THREE.ShaderMaterial({ vertexShader: PARTICLE_VS, fragmentShader: PARTICLE_FS, transparent: true, depthWrite: false, blending });
  const pts = new THREE.Points(geo, mat); pts.frustumCulled = false;
  return { pts, geo, pos, col, size, alpha, vel: new Float32Array(n * 3), life: new Float32Array(n), max: new Float32Array(n) };
}

export function createExplorer(o: Opts) {
  const renderer = new THREE.WebGLRenderer({ canvas: o.canvas, antialias: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2)); renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = .95; renderer.localClippingEnabled = true;
  const pipRenderer = new THREE.WebGLRenderer({ canvas: o.pip, antialias: true });
  pipRenderer.setPixelRatio(Math.min(devicePixelRatio, 1.5)); pipRenderer.toneMapping = THREE.ACESFilmicToneMapping; pipRenderer.toneMappingExposure = 1.1; pipRenderer.localClippingEnabled = true;

  const scene = new THREE.Scene(); scene.background = new THREE.Color(0x01030a);
  // Soft studio reflections so metallic parts read clearly instead of reflecting black space.
  const pmrem = new THREE.PMREMGenerator(renderer); const envTex = pmrem.fromScene(new RoomEnvironment(), .04).texture; scene.environment = envTex; scene.environmentIntensity = .32; pmrem.dispose();
  const camera = new THREE.PerspectiveCamera(40, 1, .01, 5000), pipCam = new THREE.PerspectiveCamera(46, 16 / 9, .005, 50);
  const controls = new OrbitControls(camera, o.canvas);
  Object.assign(controls, { enableDamping: true, dampingFactor: .07, minDistance: .25, maxDistance: 320, zoomSpeed: 1.1, rotateSpeed: .8, autoRotateSpeed: .6 });

  // ---------- Lighting (sun direction is user-controlled) ----------
  const sun = new THREE.DirectionalLight(0xfff4e2, 2.1); scene.add(sun);
  const hemi = new THREE.HemisphereLight(0x6fa8d6, 0x05070c, .28); scene.add(hemi);
  scene.add(new THREE.AmbientLight(0x1a2633, .18));
  const sunDir = new THREE.Vector3();
  const sunSprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: glow('rgba(255,250,236,1)', 'rgba(255,214,140,.28)'), blending: THREE.AdditiveBlending, depthWrite: false, transparent: true, opacity: .6 })); sunSprite.scale.setScalar(55); scene.add(sunSprite);
  function setSun(deg: number) {
    const a = THREE.MathUtils.degToRad(deg); sunDir.set(Math.cos(a), .38, Math.sin(a)).normalize();
    sun.position.copy(sunDir).multiplyScalar(400); sunSprite.position.copy(sunDir).multiplyScalar(1600); atmoMat.uniforms.sunDir.value.copy(sunDir);
  }

  // Stars (two layers for depth)
  const r = rng(5);
  for (const [count, size, rad] of [[4200, 1.1, 2200], [700, 2.2, 2000]] as const) {
    const p = new Float32Array(count * 3); for (let i = 0; i < count; i++) { const v = new THREE.Vector3(r() - .5, r() - .5, r() - .5).normalize().multiplyScalar(rad + r() * 300); p.set([v.x, v.y, v.z], i * 3); }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(p, 3));
    scene.add(new THREE.Points(g, new THREE.PointsMaterial({ color: 0xdcecff, size, sizeAttenuation: false, transparent: true, opacity: size > 2 ? .9 : .65 })));
  }

  // ---------- Earth: day/night shading, thin day-side limb (no blown-out glow) ----------
  const earthMap = tex(2048, 1024, c => {
    const g = c.createLinearGradient(0, 0, 0, 1024); g.addColorStop(0, '#0a2236'); g.addColorStop(.5, '#14476f'); g.addColorStop(1, '#0a2236'); c.fillStyle = g; c.fillRect(0, 0, 2048, 1024);
    const q = rng(9);
    for (let k = 0; k < 30; k++) { const cx = q() * 2048, cy = 180 + q() * 660, n = 60 + q() * 90; for (let i = 0; i < n; i++) { c.fillStyle = `rgba(${52 + q() * 40},${78 + q() * 40},${46 + q() * 26},${.4 + q() * .4})`; c.beginPath(); c.arc(cx + (q() - .5) * 260, cy + (q() - .5) * 130, 6 + q() * 26, 0, Math.PI * 2); c.fill(); } }
    c.fillStyle = 'rgba(210,225,240,.5)'; c.fillRect(0, 0, 2048, 34); c.fillRect(0, 990, 2048, 34);
  });
  earthMap.anisotropy = 4;
  const cloudMap = tex(2048, 1024, c => { const q = rng(13); for (let i = 0; i < 1100; i++) { c.fillStyle = `rgba(255,255,255,${q() * .08})`; c.beginPath(); c.ellipse(q() * 2048, q() * 1024, 20 + q() * 90, 5 + q() * 18, 0, 0, Math.PI * 2); c.fill(); } });
  const earth = new THREE.Group(); scene.add(earth);
  const earthMesh = new THREE.Mesh(new THREE.SphereGeometry(EARTH_R, 128, 128), new THREE.MeshStandardMaterial({ map: earthMap, roughness: 1, metalness: 0, envMapIntensity: 0 }));
  earthMesh.userData.part = 'earth'; earth.add(earthMesh);
  const clouds = new THREE.Mesh(new THREE.SphereGeometry(EARTH_R * 1.008, 96, 96), new THREE.MeshStandardMaterial({ map: cloudMap, transparent: true, depthWrite: false, roughness: 1, envMapIntensity: 0 })); earth.add(clouds);
  const atmoMat = new THREE.ShaderMaterial({
    uniforms: { sunDir: { value: new THREE.Vector3(1, 0, 0) } }, transparent: true, depthWrite: false,
    vertexShader: 'varying vec3 vN; varying vec3 vP; void main(){ vN = normalize(mat3(modelMatrix) * normal); vec4 w = modelMatrix * vec4(position,1.0); vP = w.xyz; gl_Position = projectionMatrix * viewMatrix * w; }',
    fragmentShader: 'uniform vec3 sunDir; varying vec3 vN; varying vec3 vP; void main(){ vec3 V = normalize(cameraPosition - vP); float rim = pow(1.0 - max(dot(V, vN), 0.0), 5.0); float day = smoothstep(-0.2, 0.45, dot(vN, sunDir)); gl_FragColor = vec4(0.38, 0.66, 1.0, rim * day * 0.75); }',
  });
  earth.add(new THREE.Mesh(new THREE.SphereGeometry(EARTH_R * 1.035, 96, 96), atmoMat));

  const tilt = new THREE.Euler(.38, 0, .08);
  const orbitLine = new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints(Array.from({ length: 360 }, (_, i) => new THREE.Vector3(Math.cos(i / 360 * Math.PI * 2) * ORBIT_R, 0, Math.sin(i / 360 * Math.PI * 2) * ORBIT_R).applyEuler(tilt))), new THREE.LineDashedMaterial({ color: 0x77c3ed, dashSize: 1, gapSize: 1.4, transparent: true, opacity: .28 }));
  orbitLine.computeLineDistances(); scene.add(orbitLine);

  // ---------- Spacecraft ----------
  const craft = new THREE.Group(); scene.add(craft);
  const clipLocal = new THREE.Plane(new THREE.Vector3(0, 0, -1), 1.3), clipWorld = new THREE.Plane();
  const hullOut = new THREE.MeshStandardMaterial({ color: 0xd2d8de, metalness: .4, roughness: .42, clippingPlanes: [clipWorld], clipShadows: true });
  const hullIn = new THREE.MeshStandardMaterial({ color: 0x46525e, metalness: .2, roughness: .8, side: THREE.BackSide, clippingPlanes: [clipWorld] });
  const ringMat = new THREE.MeshStandardMaterial({ color: 0x5f6b78, metalness: .75, roughness: .35, clippingPlanes: [clipWorld] });
  const dark = new THREE.MeshStandardMaterial({ color: 0x55616d, metalness: .75, roughness: .4 });
  const gold = new THREE.MeshStandardMaterial({ color: 0xc9a24f, metalness: .95, roughness: .3, emissive: 0x1d1404 });
  const tagPart = <T extends THREE.Object3D>(obj: T, part: Part) => { obj.traverse(c => { c.userData.part = part; }); return obj; };
  const alongX = <T extends THREE.Mesh>(m: T) => { m.rotation.z = Math.PI / 2; return m; };

  const cargo = new THREE.Group(); craft.add(cargo);
  const hullGeo = new THREE.CylinderGeometry(1.1, 1.1, 3.6, 96, 1, true);
  const hull = alongX(new THREE.Mesh(hullGeo, hullOut)); hull.position.x = -.6; cargo.add(hull);
  const hullInner = alongX(new THREE.Mesh(hullGeo, hullIn)); hullInner.position.x = -.6; cargo.add(hullInner);
  for (const x of [-2.15, -1.6, -1.05, -.5, .05, .6, 1.1]) { const ring = new THREE.Mesh(new THREE.TorusGeometry(1.105, .02, 8, 96), ringMat); ring.rotation.y = Math.PI / 2; ring.position.x = x; cargo.add(ring); }
  const cabinLight = new THREE.PointLight(0xdfefff, 1.1, 4.5, 1.4); cabinLight.position.set(-.6, .7, -.2); cargo.add(cabinLight);
  tagPart(cargo, 'cargo');
  const front = new THREE.Group(); craft.add(front);
  const cap = new THREE.Mesh(new THREE.SphereGeometry(1.1, 64, 16, 0, Math.PI * 2, 0, Math.PI / 2), hullOut); cap.rotation.z = Math.PI / 2; cap.scale.set(.32, 1, 1); cap.position.x = -2.4; front.add(cap);
  const cbm = new THREE.Mesh(new THREE.TorusGeometry(.72, .09, 16, 64), dark); cbm.rotation.y = Math.PI / 2; cbm.position.x = -2.76; front.add(cbm);
  tagPart(front, 'cargo');

  const service = new THREE.Group(); craft.add(service);
  service.add(alongX(new THREE.Mesh(new THREE.CylinderGeometry(1.02, 1.02, 1.4, 8), dark))).position.x = 2.05;
  service.add(alongX(new THREE.Mesh(new THREE.CylinderGeometry(1.045, 1.045, .78, 8), gold))).position.x = 2.05;
  const iface = alongX(new THREE.Mesh(new THREE.CylinderGeometry(1.15, 1.15, .14, 64), dark)); iface.position.x = 1.28; service.add(iface);
  const bell = alongX(new THREE.Mesh(new THREE.CylinderGeometry(.22, .55, .7, 40, 1, true), new THREE.MeshStandardMaterial({ color: 0x2b333c, metalness: .85, roughness: .4, side: THREE.DoubleSide }))); bell.rotation.z = -Math.PI / 2; bell.position.x = 3.1; service.add(bell);
  for (const [y, z] of [[1, 1], [1, -1], [-1, 1], [-1, -1]]) { const t = new THREE.Mesh(new THREE.BoxGeometry(.18, .14, .14), dark); t.position.set(2.6, y * .78, z * .78); service.add(t); }
  const dish = new THREE.Mesh(new THREE.SphereGeometry(.42, 32, 12, 0, Math.PI * 2, 0, Math.PI / 3.2), new THREE.MeshStandardMaterial({ color: 0xe2e7ec, metalness: .3, roughness: .45, side: THREE.DoubleSide })); dish.position.set(2.1, 1.45, 0); dish.rotation.x = Math.PI; service.add(dish);
  const mast = new THREE.Mesh(new THREE.CylinderGeometry(.03, .03, .45), dark); mast.position.set(2.1, 1.15, 0); service.add(mast);
  tagPart(service, 'service');

  const cells = tex(1024, 1024, c => {
    c.fillStyle = '#0d2f56'; c.fillRect(0, 0, 1024, 1024); c.strokeStyle = '#2d6aa8'; c.lineWidth = 2;
    for (let i = 0; i <= 1024; i += 22) { c.beginPath(); c.moveTo(i, 0); c.lineTo(i, 1024); c.moveTo(0, i); c.lineTo(1024, i); c.stroke(); }
    c.strokeStyle = '#e3c375'; c.lineWidth = 9; for (let k = 0; k < 10; k++) { const a = k * Math.PI / 5; c.beginPath(); c.moveTo(512, 512); c.lineTo(512 + Math.cos(a) * 512, 512 + Math.sin(a) * 512); c.stroke(); }
  });
  const arrayMat = new THREE.MeshStandardMaterial({ map: cells, metalness: .55, roughness: .22, side: THREE.DoubleSide, emissive: 0x041224 });
  const arrays: THREE.Group[] = [];
  for (const s of [-1, 1]) {
    const g = new THREE.Group(); craft.add(g);
    const boom = new THREE.Mesh(new THREE.CylinderGeometry(.05, .05, 1.6), dark); boom.rotation.x = Math.PI / 2; boom.position.set(2.05, 0, s * 1.8); g.add(boom);
    const disk = new THREE.Mesh(new THREE.CircleGeometry(1.75, 80), arrayMat); disk.rotation.x = -Math.PI / 2; disk.position.set(2.05, 0, s * 4.2); g.add(disk);
    const rim = new THREE.Mesh(new THREE.TorusGeometry(1.75, .025, 8, 96), gold); rim.rotation.x = Math.PI / 2; rim.position.copy(disk.position); g.add(rim);
    tagPart(g, 'array'); g.userData.side = s; arrays.push(g);
  }
  const navs = [[0xff3b4e, -1.9, 1.12], [0x3dff9a, -1.9, -1.12], [0xffffff, -2.92, 0]].map(([c, x, y]) => { const m = new THREE.Mesh(new THREE.SphereGeometry(.045, 12, 12), new THREE.MeshBasicMaterial({ color: c })); m.position.set(x, y, 0); front.add(m); return m; });

  // ---------- Experiment rack (pull-out) ----------
  const rack = new THREE.Group(); craft.add(rack); tagPart(rack, 'rack');
  const duct = new THREE.Mesh(new THREE.BoxGeometry(2.5, .56, .56), new THREE.MeshStandardMaterial({ color: 0x9fd4f5, transparent: true, opacity: .1, metalness: .1, roughness: .1, depthWrite: false, side: THREE.DoubleSide }));
  duct.position.set(-.6, -.15, 0); rack.add(tagPart(duct, 'rack'));
  const ductEdges = new THREE.LineSegments(new THREE.EdgesGeometry(duct.geometry), new THREE.LineBasicMaterial({ color: 0x77c3ed })); ductEdges.position.copy(duct.position); rack.add(ductEdges);
  const base = new THREE.Mesh(new THREE.BoxGeometry(2.6, .06, .66), dark); base.position.set(-.6, -.46, 0); rack.add(tagPart(base, 'rack'));
  const fan = new THREE.Group(); fan.position.set(-1.8, -.15, 0); rack.add(tagPart(fan, 'rack'));
  const bladeMat = new THREE.MeshStandardMaterial({ color: 0x2a333d, metalness: .5, roughness: .6 });
  for (let i = 0; i < 5; i++) { const b = new THREE.Mesh(new THREE.BoxGeometry(.012, .22, .06), bladeMat); const a = i * Math.PI * 2 / 5; b.position.set(0, Math.cos(a) * .11, Math.sin(a) * .11); b.rotation.x = a; fan.add(b); }
  const fanRing = new THREE.Mesh(new THREE.TorusGeometry(.24, .015, 8, 48), dark); fanRing.rotation.y = Math.PI / 2; fan.add(fanRing);

  // Specimen with a live char texture
  const charCanvas = document.createElement('canvas'); charCanvas.width = 1024; charCanvas.height = 96;
  const charCtx = charCanvas.getContext('2d')!; const charTex = new THREE.CanvasTexture(charCanvas); charTex.colorSpace = THREE.SRGBColorSpace;
  const sample = new THREE.Mesh(new THREE.PlaneGeometry(SX1 - SX0, .25), new THREE.MeshStandardMaterial({ map: charTex, roughness: .85, side: THREE.DoubleSide, emissiveMap: charTex, emissive: 0x000000 }));
  sample.rotation.x = -Math.PI / 2; sample.position.set((SX0 + SX1) / 2, SY, 0); rack.add(tagPart(sample, 'sample'));
  const holder = new THREE.Mesh(new THREE.BoxGeometry(SX1 - SX0 + .08, .02, .31), dark); holder.position.set((SX0 + SX1) / 2, SY - .015, 0); rack.add(tagPart(holder, 'sample'));
  const ignMat = new THREE.MeshStandardMaterial({ color: 0x8c5a2b, emissive: 0xff5a1f, emissiveIntensity: 0, metalness: .5, roughness: .4 });
  const igniter = new THREE.Group(); rack.add(tagPart(igniter, 'igniter'));
  for (let k = 0; k < 4; k++) { const coil = new THREE.Mesh(new THREE.TorusGeometry(.03, .007, 8, 20), ignMat); coil.rotation.y = Math.PI / 2; coil.position.z = -.06 + k * .04; igniter.add(coil); }
  igniter.userData.part = 'igniter';
  const beads: THREE.Mesh[] = [];
  for (let i = 0; i < 6; i++) {
    const x = SX0 + .12 + i * .24, w = new THREE.Mesh(new THREE.CylinderGeometry(.005, .005, .18), dark); w.position.set(x, .0, .08); rack.add(tagPart(w, 'tc'));
    const b = new THREE.Mesh(new THREE.SphereGeometry(.017, 14, 14), new THREE.MeshStandardMaterial({ color: 0x3c5064, emissive: 0x000000 })); b.position.set(x, -.09, .08); b.userData.x = x; rack.add(tagPart(b, 'tc')); beads.push(b);
  }
  const co2Mat = new THREE.MeshStandardMaterial({ color: 0x0f1720, emissive: 0xffb347, emissiveIntensity: 0, metalness: .4, roughness: .45 });
  const co2 = new THREE.Mesh(new THREE.BoxGeometry(.15, .15, .15), co2Mat); co2.position.set(SENSOR_X, -.15, 0); rack.add(tagPart(co2, 'co2'));
  const co2Ring = new THREE.Mesh(new THREE.TorusGeometry(.13, .006, 8, 48), new THREE.MeshBasicMaterial({ color: 0xffb347, transparent: true, opacity: 0 })); co2Ring.rotation.y = Math.PI / 2; co2Ring.position.copy(co2.position); rack.add(co2Ring);

  // Flame: particles + glow sprites + light; sparks; smoke
  const flame = particles(FLAME_N, THREE.AdditiveBlending), sparks = particles(SPARK_N, THREE.AdditiveBlending), smoke = particles(SMOKE_N, THREE.NormalBlending);
  rack.add(flame.pts, sparks.pts, smoke.pts);
  const halo = new THREE.Sprite(new THREE.SpriteMaterial({ map: glow('rgba(255,200,130,1)', 'rgba(255,90,40,.35)'), blending: THREE.AdditiveBlending, depthWrite: false, transparent: true })); rack.add(halo);
  const flameLight = new THREE.PointLight(0xff8a3d, 0, 3.2, 1.5); rack.add(flameLight);
  const streakPos = new Float32Array(30 * 6), streakX = Float32Array.from({ length: 30 }, () => -1.8 + Math.random() * 2.4);
  const streakGeo = new THREE.BufferGeometry(); streakGeo.setAttribute('position', new THREE.BufferAttribute(streakPos, 3));
  const streaks = new THREE.LineSegments(streakGeo, new THREE.LineBasicMaterial({ color: 0x77c3ed, transparent: true, opacity: .45 })); rack.add(streaks);

  // ---------- Post-processing (only very bright pixels bloom: flame, sun, lights) ----------
  const composer = new EffectComposer(renderer); composer.addPass(new RenderPass(scene, camera));
  const bloom = new UnrealBloomPass(new THREE.Vector2(1, 1), .62, .4, .94); composer.addPass(bloom); composer.addPass(new OutputPass());

  // ---------- Hover box and beacons ----------
  const hoverBox = new THREE.BoxHelper(new THREE.Object3D(), 0x77c3ed); hoverBox.visible = false; scene.add(hoverBox);
  const anchors: Record<Part, () => THREE.Vector3> = {
    cargo: () => craft.localToWorld(new THREE.Vector3(-1.4, 1.25, 0)), service: () => craft.localToWorld(new THREE.Vector3(2.4, 1.15, .3)),
    array: () => craft.localToWorld(arrays[1].position.clone().add(new THREE.Vector3(2.05, .2, 4.2))), earth: () => new THREE.Vector3(0, EARTH_R * 1.05, 0),
    rack: () => rack.localToWorld(new THREE.Vector3(-1.75, .2, 0)), sample: () => rack.localToWorld(new THREE.Vector3(-.6, SY, .16)), igniter: () => igniter.localToWorld(new THREE.Vector3(0, .05, 0)),
    tc: () => rack.localToWorld(new THREE.Vector3(-.3, .09, .08)), co2: () => rack.localToWorld(new THREE.Vector3(SENSOR_X, .02, 0)),
  };
  const beaconEls = (Object.keys(o.beacons) as Part[]).map(part => {
    const b = document.createElement('button'); b.type = 'button'; b.className = `xp-beacon xp-beacon-${part}`; b.innerHTML = `<i></i><span>${o.beacons[part]}</span>`;
    b.addEventListener('click', () => { o.onPick(part); focus(part); }); o.overlay.appendChild(b); return { part, el: b };
  });
  const co2Tag = document.createElement('div'); co2Tag.className = 'xp-holo'; o.overlay.appendChild(co2Tag);

  // ---------- State ----------
  let input: EngineInput = { flame: { x: 0, alive: 0, burnt: 0, regress: 0, pulse: 0 }, sensed: 0, heat: 0, intensity: .5, reading: null, burning: false };
  let spec: SampleSpec = { material: 'SIBAL', opposed: false, leadInCm: null, regressCm: 0 };
  let cut = 0, explode = 0, beacons = true, orbitSpeed = 1, theta = .9, disposed = false, raf = 0, lastChar = 0, lastCam = 0, lastHover = 0;
  let followFlame = false;
  let flying: { l: { x: number; y: number; z: number; tx: number; ty: number; tz: number }; anim: JSAnimation } | null = null;
  const prevPos = new THREE.Vector3(), prevQ = new THREE.Quaternion(), basis = new THREE.Matrix4();

  function placeCraft(dt: number) {
    theta += dt * .01 * orbitSpeed;
    const pos = new THREE.Vector3(Math.cos(theta) * ORBIT_R, 0, Math.sin(theta) * ORBIT_R).applyEuler(tilt);
    const tangent = new THREE.Vector3(-Math.sin(theta), 0, Math.cos(theta)).applyEuler(tilt).normalize(), radial = pos.clone().normalize();
    basis.makeBasis(tangent, radial, new THREE.Vector3().crossVectors(tangent, radial).normalize()); craft.quaternion.setFromRotationMatrix(basis); craft.position.copy(pos);
  }
  const flameLocalX = () => (spec.opposed ? SX1 - input.flame.x * CM : SX0 + input.flame.x * CM);

  // Camera targets in craft-local space
  const rackLocal = (v: THREE.Vector3) => v.add(rack.position);
  const views: Record<View | Part, () => [THREE.Vector3, THREE.Vector3]> = {
    orbit: () => [new THREE.Vector3(-26, 9, 40), new THREE.Vector3(0, -6, 0)], craft: () => [new THREE.Vector3(7.2, 1.6, 9.2), new THREE.Vector3(.3, 0, 0)],
    rack: () => [rackLocal(new THREE.Vector3(.1, 1.0, 2.5)), rackLocal(new THREE.Vector3(-.6, -.2, 0))], flame: () => { const fx = flameLocalX(); return [rackLocal(new THREE.Vector3(fx + .55, .62, 1.55)), rackLocal(new THREE.Vector3(fx + .2, SY - .02, 0))]; },
    cargo: () => [new THREE.Vector3(-2.5, 1.6, 5.4), new THREE.Vector3(-.6, 0, 0)], service: () => [new THREE.Vector3(4.6, 1.3, 3.6), new THREE.Vector3(2.05, 0, 0)],
    array: () => [new THREE.Vector3(2.2, 4.2, 9.5), new THREE.Vector3(2.05, 0, 4.4 + explode * 2)], earth: () => [new THREE.Vector3(-26, 9, 40), new THREE.Vector3(0, -6, 0)],
    sample: () => [rackLocal(new THREE.Vector3(-.4, .55, 1.0)), rackLocal(new THREE.Vector3(-.6, SY, 0))], igniter: () => { const x = spec.opposed ? SX1 + .03 : SX0 - .03; return [rackLocal(new THREE.Vector3(x + .3, .2, .55)), rackLocal(new THREE.Vector3(x, SY, 0))]; },
    tc: () => [rackLocal(new THREE.Vector3(-.3, .3, .9)), rackLocal(new THREE.Vector3(-.3, -.05, .08))], co2: () => [rackLocal(new THREE.Vector3(.85, .25, .7)), rackLocal(new THREE.Vector3(SENSOR_X, -.15, 0))],
  };
  function focus(v: View | Part, duration = 1500) {
    flying?.anim.pause(); followFlame = v === 'flame';
    const cl = craft.worldToLocal(camera.position.clone()), tl = craft.worldToLocal(controls.target.clone()), [c, t] = views[v]();
    const l = { x: cl.x, y: cl.y, z: cl.z, tx: tl.x, ty: tl.y, tz: tl.z };
    controls.enabled = false;
    const anim = animate(l, { x: c.x, y: c.y, z: c.z, tx: t.x, ty: t.y, tz: t.z, duration, ease: 'inOut(3)', onComplete: () => { flying = null; controls.enabled = true; } });
    flying = { l, anim };
    if (['rack', 'flame', 'sample', 'igniter', 'tc', 'co2'].includes(v) && cut < .55 && explode < .3) { setCut(.75); cutListeners.forEach(f => f(.75)); }
  }
  const cutListeners: ((v: number) => void)[] = [];
  function setCut(v: number) { cut = v; clipLocal.constant = 1.3 - v * 1.55; }
  function setExplode(v: number) { explode = v; }

  // Specimen texture redraw
  function drawChar() {
    const W = 1024, H = 96, f = input.flame, base = MAT_COLOR[spec.material] ?? '#8c9eae', c = charCtx;
    c.fillStyle = base; c.fillRect(0, 0, W, H);
    for (let i = 0; i < 140; i++) { c.fillStyle = `rgba(255,255,255,${(i % 7) * .006})`; c.fillRect((i * 73) % W, 0, 2, H); }
    if (spec.leadInCm) { const lx = spec.leadInCm / 29 * W; c.fillStyle = '#c9a24f'; c.fillRect(spec.opposed ? 0 : lx, 0, spec.opposed ? W - lx : W - lx, H); }
    const bw = f.burnt / 29 * W, x0 = spec.opposed ? W - bw : 0;
    if (bw > 0) { const g = c.createLinearGradient(spec.opposed ? W : 0, 0, spec.opposed ? W - bw : bw, 0); g.addColorStop(0, '#0b0606'); g.addColorStop(.8, '#1b0d0a'); g.addColorStop(1, '#3a1a10'); c.fillStyle = g; c.fillRect(x0, 0, bw, H); }
    if (spec.regressCm && f.regress > 0) { const rw = spec.regressCm / 29 * W; const g = c.createLinearGradient(spec.opposed ? W : 0, 0, spec.opposed ? W - rw : rw, 0); g.addColorStop(0, `rgba(20,6,6,${.85 * f.regress})`); g.addColorStop(1, 'rgba(20,6,6,0)'); c.fillStyle = g; c.fillRect(spec.opposed ? W - rw : 0, 0, rw, H); }
    if (f.alive > .02) { const ex = spec.opposed ? W - bw : bw, g = c.createLinearGradient(ex - 26, 0, ex + 26, 0); g.addColorStop(0, 'rgba(255,90,30,0)'); g.addColorStop(.5, `rgba(255,170,70,${f.alive})`); g.addColorStop(1, 'rgba(255,90,30,0)'); c.fillStyle = g; c.fillRect(ex - 26, 0, 52, H); }
    charTex.needsUpdate = true;
  }

  function setSample(s: SampleSpec) {
    spec = s; igniter.position.set(s.opposed ? SX1 + .035 : SX0 - .035, SY + .03, 0);
    [flame, smoke, sparks].forEach(p => { p.life.fill(0); p.pos.fill(-999); p.geo.attributes.position.needsUpdate = true; });
    drawChar();
  }

  // Resize
  function resize() {
    const w = o.canvas.clientWidth, h = o.canvas.clientHeight; if (w && h) { renderer.setSize(w, h, false); composer.setSize(w, h); bloom.setSize(w, h); camera.aspect = w / h; camera.updateProjectionMatrix(); }
    const pw = o.pip.clientWidth, ph = o.pip.clientHeight; if (pw && ph) { pipRenderer.setSize(pw, ph, false); pipCam.aspect = pw / ph; pipCam.updateProjectionMatrix(); }
  }
  const ro = new ResizeObserver(resize); ro.observe(o.canvas); ro.observe(o.pip);

  // Pointer: hover, click (pick), double-click (focus)
  const ray = new THREE.Raycaster(), ndc = new THREE.Vector2(); let down = { x: 0, y: 0 };
  const hit = (e: PointerEvent | MouseEvent): Part | null => {
    const rc = o.canvas.getBoundingClientRect(); ndc.set(((e.clientX - rc.left) / rc.width) * 2 - 1, -((e.clientY - rc.top) / rc.height) * 2 + 1); ray.setFromCamera(ndc, camera);
    for (const h of ray.intersectObjects([craft, earth], true)) {
      const part = h.object.userData.part as Part | undefined; if (!part || !h.object.visible) continue;
      if ((part === 'cargo') && cut > .3 && clipWorld.distanceToPoint(h.point) < 0) continue;
      return part;
    }
    return null;
  };
  const groupOf = (p: Part): THREE.Object3D => ({ cargo, service, array: arrays[1], rack, sample, igniter, tc: beads[2], co2, earth } as Record<Part, THREE.Object3D>)[p];
  const onMove = (e: PointerEvent) => {
    const now = performance.now(); if (now - lastHover < 60) return; lastHover = now;
    const p = hit(e); hoverBox.visible = !!p && p !== 'earth'; if (p && p !== 'earth') hoverBox.setFromObject(groupOf(p));
    o.onHover(p, e.clientX, e.clientY); o.canvas.style.cursor = p ? 'pointer' : 'grab';
  };
  const onDown = (e: PointerEvent) => { down = { x: e.clientX, y: e.clientY }; };
  const onUp = (e: PointerEvent) => { if (Math.hypot(e.clientX - down.x, e.clientY - down.y) > 5) return; const p = hit(e); if (p) o.onPick(p); };
  const onDbl = (e: MouseEvent) => { const p = hit(e); if (p) { o.onPick(p); focus(p); } };
  const onLeave = () => { hoverBox.visible = false; o.onHover(null, 0, 0); };
  controls.addEventListener('start', () => { followFlame = false; });
  o.canvas.addEventListener('pointermove', onMove); o.canvas.addEventListener('pointerdown', onDown); o.canvas.addEventListener('pointerup', onUp); o.canvas.addEventListener('dblclick', onDbl); o.canvas.addEventListener('pointerleave', onLeave);

  // Keyboard orbit / zoom
  const sph = new THREE.Spherical();
  const onKey = (e: KeyboardEvent) => {
    const tag = (e.target as HTMLElement)?.tagName; if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
    const k = e.key.toLowerCase(), off = camera.position.clone().sub(controls.target);
    if ('wasdqe'.includes(k) && k.length === 1) {
      sph.setFromVector3(off);
      if (k === 'a') sph.theta -= .09; if (k === 'd') sph.theta += .09; if (k === 'w') sph.phi = Math.max(.1, sph.phi - .07); if (k === 's') sph.phi = Math.min(Math.PI - .1, sph.phi + .07);
      if (k === 'q') sph.radius *= .85; if (k === 'e') sph.radius *= 1.18;
      camera.position.copy(controls.target).add(new THREE.Vector3().setFromSpherical(sph)); e.preventDefault();
    }
    if (k === 'r') focus('craft');
  };
  window.addEventListener('keydown', onKey);

  // Initial frame
  placeCraft(0); craft.updateMatrixWorld(); prevPos.copy(craft.position); prevQ.copy(craft.quaternion);
  const [c0, t0] = views.craft(); camera.position.copy(craft.localToWorld(c0)); controls.target.copy(craft.localToWorld(t0));
  // Start with the sun behind the viewer so the vehicle is front-lit (no glare behind it).
  const viewDir = camera.position.clone().sub(craft.position).normalize();
  const initialSun = Math.round((THREE.MathUtils.radToDeg(Math.atan2(viewDir.z, viewDir.x)) + 25 + 360) % 360); setSun(initialSun);
  setCut(0); drawChar(); resize();

  const t0ms = performance.now(); let lastMs = t0ms; const tmpQ = new THREE.Quaternion(), v3 = new THREE.Vector3();
  function frame() {
    if (disposed) return;
    const nowMs = performance.now(), dt = Math.min((nowMs - lastMs) / 1000, .05), T = (nowMs - t0ms) / 1000; lastMs = nowMs;
    placeCraft(dt); craft.updateMatrixWorld();
    earth.rotation.y += dt * .006; clouds.rotation.y += dt * .003;
    // Keep the camera locked to the craft frame (translation + rotation) unless flying.
    tmpQ.copy(craft.quaternion).multiply(prevQ.clone().invert());
    if (flying) {
      const l = flying.l; camera.position.copy(craft.localToWorld(v3.set(l.x, l.y, l.z))); controls.target.copy(craft.localToWorld(new THREE.Vector3(l.tx, l.ty, l.tz)));
    } else {
      const co = camera.position.clone().sub(prevPos).applyQuaternion(tmpQ), to = controls.target.clone().sub(prevPos).applyQuaternion(tmpQ);
      camera.position.copy(craft.position).add(co); controls.target.copy(craft.position).add(to);
      // Track the advancing flame front until the user takes the camera.
      if (followFlame && input.flame.alive > .02) { const [fc, ft] = views.flame(); camera.position.lerp(craft.localToWorld(fc), .035); controls.target.lerp(craft.localToWorld(ft), .06); }
    }
    prevPos.copy(craft.position); prevQ.copy(craft.quaternion);
    controls.update();

    // Exploded view and cutaway plane
    const ex = explode;
    service.position.x = ex * 2.6; front.position.x = -ex * 1.6; rack.position.y = ex * 2.2;
    arrays.forEach(a => { a.position.z = a.userData.side * ex * 2.2; });
    clipWorld.copy(clipLocal).applyMatrix4(craft.matrixWorld);
    navs[0].visible = Math.sin(T * 3.1) > 0; navs[1].visible = Math.sin(T * 3.1 + 1.6) > 0; navs[2].visible = (T % 2) < .07;
    fan.rotation.x += dt * 16;

    // ---- Fire ----
    const f = input.flame, fx = flameLocalX(), dir = spec.opposed ? -1 : 1, a = f.alive, flick = 1 + Math.sin(T * 27) * .07 + Math.sin(T * 41) * .05;
    const silicone = spec.material === 'Silicone';
    halo.position.set(fx + .06, SY + .07, 0); halo.scale.set(.75 * a * flick + .001, .42 * a * flick + .001, 1); (halo.material as THREE.SpriteMaterial).opacity = a * .9;
    flameLight.position.set(fx + .05, SY + .12, 0); flameLight.intensity = a * 4.2 * flick;
    ignMat.emissiveIntensity = f.pulse * 3 + (f.pulse > 0 ? Math.sin(T * 30) * .4 : 0);
    // flame particles
    const emitF = a * (silicone ? 380 : 950) * dt;
    let spawn = emitF;
    for (let i = 0; i < FLAME_N; i++) {
      const k = i * 3;
      if (flame.life[i] <= 0) {
        if (spawn >= 1 || (spawn > 0 && Math.random() < spawn)) {
          spawn -= 1; flame.max[i] = flame.life[i] = .35 + Math.random() * .5;
          flame.pos[k] = fx - dir * Math.random() * .07; flame.pos[k + 1] = SY + .006 + Math.random() * .012; flame.pos[k + 2] = (Math.random() - .5) * .22;
          flame.vel[k] = .09 + Math.random() * .08; flame.vel[k + 1] = .025 + Math.random() * .08; flame.vel[k + 2] = (Math.random() - .5) * .04;
        } else { flame.alpha[i] = 0; continue; }
      }
      flame.life[i] -= dt; const age = 1 - flame.life[i] / flame.max[i];
      flame.pos[k] += flame.vel[k] * dt; flame.pos[k + 1] += flame.vel[k + 1] * dt * (1 - age * .6); flame.pos[k + 2] += flame.vel[k + 2] * dt;
      const [cr, cg, cb] = age < .18 ? [.35, .6, 1] : age < .4 ? (silicone ? [.55, .75, 1] : [1, .93, .7]) : age < .7 ? (silicone ? [.4, .5, .95] : [1, .52, .14]) : [.55, .1, .05];
      flame.col.set([cr, cg, cb], k); flame.size[i] = (.05 - age * .03) * (silicone ? .8 : 1); flame.alpha[i] = Math.sin(Math.PI * Math.min(1, age * 1.15)) * .9 * a;
    }
    // igniter sparks
    for (let i = 0; i < SPARK_N; i++) {
      const k = i * 3;
      if (sparks.life[i] <= 0) {
        if (f.pulse > .3 && Math.random() < .25) { sparks.max[i] = sparks.life[i] = .25 + Math.random() * .3; const ip = igniter.position; sparks.pos.set([ip.x, ip.y, ip.z + (Math.random() - .5) * .12], k); sparks.vel.set([(Math.random() - .3) * .5 * dir, Math.random() * .4, (Math.random() - .5) * .4], k); }
        else { sparks.alpha[i] = 0; continue; }
      }
      sparks.life[i] -= dt; const age = 1 - sparks.life[i] / sparks.max[i];
      sparks.pos[k] += sparks.vel[k] * dt; sparks.pos[k + 1] += sparks.vel[k + 1] * dt; sparks.pos[k + 2] += sparks.vel[k + 2] * dt;
      sparks.col.set([1, .85 - age * .4, .5 - age * .4], k); sparks.size[i] = .018; sparks.alpha[i] = 1 - age;
    }
    // smoke carried downstream (+x) to the CO₂ sensor and beyond
    const emitS = a * input.intensity * 160 * dt; let sp = emitS;
    for (let i = 0; i < SMOKE_N; i++) {
      const k = i * 3;
      if (smoke.life[i] <= 0) {
        if (sp >= 1 || (sp > 0 && Math.random() < sp)) { sp -= 1; smoke.max[i] = smoke.life[i] = 2.2 + Math.random() * 1.5; smoke.pos.set([fx + .05, SY + .06 + Math.random() * .05, (Math.random() - .5) * .15], k); smoke.vel.set([.42 + Math.random() * .12, (Math.random() - .5) * .05, (Math.random() - .5) * .05], k); }
        else { smoke.alpha[i] = 0; continue; }
      }
      smoke.life[i] -= dt; const age = 1 - smoke.life[i] / smoke.max[i];
      smoke.pos[k] += smoke.vel[k] * dt; smoke.pos[k + 1] += smoke.vel[k + 1] * dt; smoke.pos[k + 2] += smoke.vel[k + 2] * dt;
      if (smoke.pos[k] > .62) smoke.life[i] = 0;
      const g = .55 - age * .2; smoke.col.set([g, g * 1.02, g * 1.06], k); smoke.size[i] = .04 + age * .09; smoke.alpha[i] = Math.sin(Math.PI * age) * .38;
    }
    for (const p of [flame, sparks, smoke]) { const at = p.geo.attributes; at.position.needsUpdate = at.aColor.needsUpdate = at.aSize.needsUpdate = at.aAlpha.needsUpdate = true; }
    beads.forEach(b => { const heat = a * input.heat * Math.max(0, 1 - Math.abs(b.userData.x - fx) * 1.7); (b.material as THREE.MeshStandardMaterial).emissive.setRGB(heat * 1.4, heat * .5, heat * .12); });
    co2Mat.emissiveIntensity = input.sensed * 1.8; (co2Ring.material as THREE.MeshBasicMaterial).opacity = input.sensed * (.6 + Math.sin(T * 5) * .3); co2Ring.scale.setScalar(1 + input.sensed * .3 + Math.sin(T * 5) * .05);
    if (T - lastChar > .1) { lastChar = T; drawChar(); }
    streaks.visible = cut > .2 || explode > .2;
    for (let i = 0; i < 30; i++) { streakX[i] += dt * .9; if (streakX[i] > .62) streakX[i] = -1.78; const y = -.4 + (i % 6) * .05 + (i % 2 ? .3 : 0), z = -.22 + ((i * 7) % 10) * .048; streakPos.set([streakX[i], y, z, streakX[i] + .1, y, z], i * 6); }
    streakGeo.attributes.position.needsUpdate = true;
    if (hoverBox.visible) hoverBox.update();

    // Beacons + holographic CO₂ tag
    const W = o.canvas.clientWidth, H = o.canvas.clientHeight, dist = camera.position.distanceTo(craft.position), inside = cut > .3 || explode > .25;
    for (const b of beaconEls) {
      const show = beacons && (b.part === 'earth' ? dist > 25 : ['rack', 'sample', 'igniter', 'tc', 'co2'].includes(b.part) ? inside && dist < 10 : dist < 32);
      if (!show) { b.el.style.opacity = '0'; b.el.style.pointerEvents = 'none'; continue; }
      const v = anchors[b.part]().project(camera);
      if (v.z > 1 || Math.abs(v.x) > 1.1 || Math.abs(v.y) > 1.1) { b.el.style.opacity = '0'; b.el.style.pointerEvents = 'none'; continue; }
      b.el.style.opacity = '1'; b.el.style.pointerEvents = 'auto'; b.el.style.transform = `translate(${((v.x + 1) / 2) * W}px,${((1 - v.y) / 2) * H}px)`;
    }
    const hv = rack.localToWorld(new THREE.Vector3(SENSOR_X, .14, 0)).project(camera);
    const showHolo = inside && dist < 6 && input.reading !== null && hv.z < 1;
    co2Tag.style.opacity = showHolo ? '1' : '0';
    if (showHolo) { co2Tag.textContent = `CO₂ ${input.reading!.toFixed(1)} ppm`; co2Tag.style.transform = `translate(${((hv.x + 1) / 2) * W}px,${((1 - hv.y) / 2) * H}px)`; }
    if (T - lastCam > .25) { lastCam = T; o.onCamera(dist); }

    composer.render();
    // Experiment camera (picture-in-picture), locked to the rack
    const flameW = rack.localToWorld(new THREE.Vector3(Math.min(SX1 - .2, Math.max(SX0 + .25, fx + .12)), SY, 0));
    pipCam.position.copy(rack.localToWorld(new THREE.Vector3(Math.min(SX1, Math.max(SX0, fx)) + .45, .2, .62)));
    pipCam.up.copy(new THREE.Vector3(0, 1, 0).applyQuaternion(craft.quaternion)); pipCam.lookAt(flameW);
    pipRenderer.render(scene, pipCam);
    raf = requestAnimationFrame(frame);
  }
  raf = requestAnimationFrame(frame);

  return {
    update(i: EngineInput) { input = i; },
    setSample, setExplode, focus,
    setCut(v: number) { setCut(v); },
    onCutAuto(fn: (v: number) => void) { cutListeners.push(fn); },
    setSun, setOrbitSpeed(k: number) { orbitSpeed = k; }, setBeacons(on: boolean) { beacons = on; }, setAutoRotate(on: boolean) { controls.autoRotate = on; },
    theta: () => theta, initialSun,
    dispose() {
      disposed = true; cancelAnimationFrame(raf); ro.disconnect(); flying?.anim.pause(); window.removeEventListener('keydown', onKey);
      o.canvas.removeEventListener('pointermove', onMove); o.canvas.removeEventListener('pointerdown', onDown); o.canvas.removeEventListener('pointerup', onUp); o.canvas.removeEventListener('dblclick', onDbl); o.canvas.removeEventListener('pointerleave', onLeave);
      beaconEls.forEach(b => b.el.remove()); co2Tag.remove(); controls.dispose(); composer.dispose();
      scene.traverse(x => { const m = x as THREE.Mesh; m.geometry?.dispose?.(); const mat = m.material as THREE.Material | THREE.Material[] | undefined; (Array.isArray(mat) ? mat : mat ? [mat] : []).forEach(q => { (q as THREE.MeshStandardMaterial).map?.dispose(); q.dispose(); }); });
      envTex.dispose(); renderer.dispose(); pipRenderer.dispose();
    },
  };
}
export type Explorer = ReturnType<typeof createExplorer>;
