import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js';
import { animate, type JSAnimation } from 'animejs';
import type { FlameState } from '@/entities/saffire/mission';

// Stylised, not-to-scale mission scene. The experiment is enlarged inside the cargo module so it can
// be inspected; positions are schematic. Only the flame state, sensor response and heat inputs come
// from the SAFFIRE-II evidence (passed in through `update`).

export type ScenePart = 'cargo' | 'service' | 'array' | 'duct' | 'sample' | 'igniter' | 'tc' | 'co2' | 'earth' | 'fan';
export type Preset = 'orbit' | 'craft' | 'inside' | 'flame';
export type SceneInput = { flame: FlameState; sensed: number; heat: number; intensity: number };
export type SampleSpec = { material: string; opposed: boolean; leadInCm: number | null };
export type LabelSpec = { part: ScenePart | 'duct-in'; text: string; inside: boolean };

const CM = 1.45 / 29; // sample units per cm (schematic enlargement)
const SAMPLE_X0 = -1.325, SAMPLE_X1 = 0.125, SAMPLE_Y = -0.2, SENSOR_X = 0.5;
const ORBIT_R = 66, EARTH_R = 40, SMOKE_N = 320, STREAKS = 26;
const MATERIAL_COLORS: Record<string, number> = { Silicone: 0x6f7b86, SIBAL: 0xb9a57e, PMMA: 0x7fb6cf, PMMA_Nomex: 0x7fb6cf };

function canvasTexture(w: number, h: number, draw: (c: CanvasRenderingContext2D) => void) {
  const cv = document.createElement('canvas'); cv.width = w; cv.height = h; draw(cv.getContext('2d')!);
  const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace; return tex;
}
const glowTexture = (inner: string, mid: string) => canvasTexture(128, 128, c => {
  const g = c.createRadialGradient(64, 64, 0, 64, 64, 64); g.addColorStop(0, inner); g.addColorStop(.35, mid); g.addColorStop(1, 'rgba(0,0,0,0)'); c.fillStyle = g; c.fillRect(0, 0, 128, 128);
});
function seeded(seed: number) { return () => { seed = (seed * 16807) % 2147483647; return (seed - 1) / 2147483646; }; }

export function createMissionScene(canvas: HTMLCanvasElement, labelLayer: HTMLElement, labels: LabelSpec[]) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = .85;
  const scene = new THREE.Scene(); scene.background = new THREE.Color(0x020305);
  const camera = new THREE.PerspectiveCamera(42, 1, 0.01, 4000);
  const controls = new OrbitControls(camera, canvas);
  controls.enableDamping = true; controls.dampingFactor = .06; controls.minDistance = .4; controls.maxDistance = 260; controls.zoomSpeed = .9;

  // Lights: sun, Earthshine and a faint fill.
  const sunDir = new THREE.Vector3(1, .45, .6).normalize();
  const sun = new THREE.DirectionalLight(0xfff2dc, 2.1); sun.position.copy(sunDir.clone().multiplyScalar(300)); scene.add(sun);
  scene.add(new THREE.HemisphereLight(0x77c3ed, 0x050a12, .55)); scene.add(new THREE.AmbientLight(0x223344, .35));

  // Stars
  const rnd = seeded(42), starPos = new Float32Array(3600 * 3);
  for (let i = 0; i < 3600; i++) { const v = new THREE.Vector3(rnd() - .5, rnd() - .5, rnd() - .5).normalize().multiplyScalar(1500 + rnd() * 400); starPos.set([v.x, v.y, v.z], i * 3); }
  const starGeo = new THREE.BufferGeometry(); starGeo.setAttribute('position', new THREE.BufferAttribute(starPos, 3));
  scene.add(new THREE.Points(starGeo, new THREE.PointsMaterial({ color: 0xd9f1ff, size: 1.4, sizeAttenuation: false })));
  const sunSprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTexture('rgba(255,250,235,1)', 'rgba(255,210,122,.35)'), blending: THREE.AdditiveBlending, depthWrite: false }));
  sunSprite.position.copy(sunDir.clone().multiplyScalar(1200)); sunSprite.scale.setScalar(120); (sunSprite.material as THREE.SpriteMaterial).opacity = .75; scene.add(sunSprite);

  // Earth (stylised procedural surface + clouds + atmosphere rim)
  const earthTex = canvasTexture(1024, 512, c => {
    const g = c.createLinearGradient(0, 0, 0, 512); g.addColorStop(0, '#0b2a4a'); g.addColorStop(.5, '#1d5f9a'); g.addColorStop(1, '#0b2a4a'); c.fillStyle = g; c.fillRect(0, 0, 1024, 512);
    const r = seeded(7);
    for (let k = 0; k < 22; k++) { const cx = r() * 1024, cy = 90 + r() * 330, n = 40 + r() * 70; for (let i = 0; i < n; i++) { c.fillStyle = `rgba(${60 + r() * 50},${90 + r() * 50},${50 + r() * 30},${.35 + r() * .4})`; c.beginPath(); c.arc(cx + (r() - .5) * 140, cy + (r() - .5) * 70, 4 + r() * 18, 0, Math.PI * 2); c.fill(); } }
    c.fillStyle = 'rgba(220,232,245,.55)'; c.fillRect(0, 0, 1024, 20); c.fillRect(0, 492, 1024, 20);
  });
  const cloudTex = canvasTexture(1024, 512, c => { const r = seeded(11); for (let i = 0; i < 520; i++) { c.fillStyle = `rgba(255,255,255,${r() * .09})`; c.beginPath(); c.ellipse(r() * 1024, r() * 512, 10 + r() * 50, 3 + r() * 10, 0, 0, Math.PI * 2); c.fill(); } });
  const earth = new THREE.Group(); scene.add(earth);
  const earthMesh = new THREE.Mesh(new THREE.SphereGeometry(EARTH_R, 96, 96), new THREE.MeshStandardMaterial({ map: earthTex, roughness: .95, metalness: 0, color: 0x8fa4b8 }));
  earthMesh.userData.part = 'earth'; earth.add(earthMesh);
  const clouds = new THREE.Mesh(new THREE.SphereGeometry(EARTH_R * 1.012, 96, 96), new THREE.MeshStandardMaterial({ map: cloudTex, transparent: true, depthWrite: false })); earth.add(clouds);
  const atmo = new THREE.Mesh(new THREE.SphereGeometry(EARTH_R * 1.09, 64, 64), new THREE.ShaderMaterial({
    side: THREE.BackSide, blending: THREE.AdditiveBlending, transparent: true, depthWrite: false,
    vertexShader: 'varying vec3 vN; void main(){ vN = normalize(normalMatrix * normal); gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
    fragmentShader: 'varying vec3 vN; void main(){ float i = pow(0.72 - dot(vN, vec3(0.0,0.0,1.0)), 3.0); gl_FragColor = vec4(0.3,0.6,1.0,1.0) * i * 0.9; }',
  })); earth.add(atmo);

  // Orbit path
  const orbitTilt = new THREE.Euler(.42, 0, .1);
  const orbitPts = Array.from({ length: 256 }, (_, i) => new THREE.Vector3(Math.cos(i / 256 * Math.PI * 2) * ORBIT_R, 0, Math.sin(i / 256 * Math.PI * 2) * ORBIT_R).applyEuler(orbitTilt));
  const orbitLine = new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints(orbitPts), new THREE.LineDashedMaterial({ color: 0x77c3ed, dashSize: 1.2, gapSize: 1.6, transparent: true, opacity: .35 }));
  orbitLine.computeLineDistances(); scene.add(orbitLine);

  // ---------- Spacecraft ----------
  const craft = new THREE.Group(); scene.add(craft);
  const hullMat = new THREE.MeshStandardMaterial({ color: 0xd7dde3, metalness: .6, roughness: .38, side: THREE.DoubleSide });
  const darkMetal = new THREE.MeshStandardMaterial({ color: 0x5f6b78, metalness: .7, roughness: .38 });
  const gold = new THREE.MeshStandardMaterial({ color: 0xc9a24f, metalness: .95, roughness: .28, emissive: 0x2a1c05 });
  const tag = <T extends THREE.Object3D>(o: T, part: ScenePart) => { o.traverse(c => { c.userData.part = part; }); return o; };
  const alongX = (m: THREE.Mesh) => { m.rotation.z = Math.PI / 2; return m; };

  const cargo = new THREE.Group(); craft.add(tag(cargo, 'cargo'));
  cargo.add(alongX(new THREE.Mesh(new THREE.CylinderGeometry(1.1, 1.1, 3.6, 64, 1, true), hullMat))).position.set(-.6, 0, 0);
  const capF = new THREE.Mesh(new THREE.SphereGeometry(1.1, 48, 16, 0, Math.PI * 2, 0, Math.PI / 2), hullMat); capF.rotation.z = Math.PI / 2; capF.scale.set(.35, 1, 1); capF.position.x = -2.4; cargo.add(capF);
  for (const x of [-2.1, -1.5, -.9, -.3, .3, .9]) { const ring = new THREE.Mesh(new THREE.TorusGeometry(1.105, .018, 8, 64), darkMetal); ring.rotation.y = Math.PI / 2; ring.position.x = x; cargo.add(ring); }
  const cbm = new THREE.Mesh(new THREE.TorusGeometry(.75, .09, 16, 64), darkMetal); cbm.rotation.y = Math.PI / 2; cbm.position.x = -2.78; cargo.add(cbm);
  const iface = alongX(new THREE.Mesh(new THREE.CylinderGeometry(1.16, 1.16, .16, 64), darkMetal)); iface.position.x = 1.28; cargo.add(iface);

  const service = new THREE.Group(); craft.add(tag(service, 'service'));
  service.add(alongX(new THREE.Mesh(new THREE.CylinderGeometry(1.02, 1.02, 1.4, 8), darkMetal))).position.set(2.05, 0, 0);
  service.add(alongX(new THREE.Mesh(new THREE.CylinderGeometry(1.045, 1.045, .78, 8), gold))).position.set(2.05, 0, 0);
  const nozzle = alongX(new THREE.Mesh(new THREE.CylinderGeometry(.22, .55, .7, 32, 1, true), new THREE.MeshStandardMaterial({ color: 0x2d3742, metalness: .8, roughness: .45, side: THREE.DoubleSide })));
  nozzle.rotation.z = -Math.PI / 2; nozzle.position.x = 3.1; service.add(nozzle);
  for (const [y, z] of [[1, 1], [1, -1], [-1, 1], [-1, -1]]) { const t = new THREE.Mesh(new THREE.BoxGeometry(.18, .14, .14), darkMetal); t.position.set(2.6, y * .78, z * .78); service.add(t); }
  const dish = new THREE.Mesh(new THREE.SphereGeometry(.42, 32, 12, 0, Math.PI * 2, 0, Math.PI / 3.2), new THREE.MeshStandardMaterial({ color: 0xdfe5ea, metalness: .3, roughness: .4, side: THREE.DoubleSide }));
  dish.position.set(2.1, 1.45, 0); dish.rotation.x = Math.PI; service.add(dish);
  const mast = new THREE.Mesh(new THREE.CylinderGeometry(.03, .03, .45), darkMetal); mast.position.set(2.1, 1.15, 0); service.add(mast);

  // Fan-type solar arrays with a procedural cell texture
  const cellTex = canvasTexture(512, 512, c => {
    c.fillStyle = '#0f3561'; c.fillRect(0, 0, 512, 512); c.strokeStyle = '#2f6fb2'; c.lineWidth = 2;
    for (let i = 0; i <= 512; i += 16) { c.beginPath(); c.moveTo(i, 0); c.lineTo(i, 512); c.moveTo(0, i); c.lineTo(512, i); c.stroke(); }
    c.strokeStyle = '#e8c97a'; c.lineWidth = 5; for (let k = 0; k < 10; k++) { const a = k * Math.PI / 5; c.beginPath(); c.moveTo(256, 256); c.lineTo(256 + Math.cos(a) * 256, 256 + Math.sin(a) * 256); c.stroke(); }
  });
  const arrayMat = new THREE.MeshStandardMaterial({ map: cellTex, metalness: .6, roughness: .25, side: THREE.DoubleSide, emissive: 0x05162a });
  const arrays: THREE.Group[] = [];
  for (const s of [-1, 1]) {
    const boom = new THREE.Mesh(new THREE.CylinderGeometry(.05, .05, 1.5), darkMetal); boom.rotation.x = Math.PI / 2; boom.position.set(2.05, 0, s * 1.75); craft.add(tag(boom, 'array'));
    const g = new THREE.Group(); g.position.set(2.05, 0, s * 4.1);
    const disk = new THREE.Mesh(new THREE.CircleGeometry(1.75, 64), arrayMat); disk.rotation.x = -Math.PI / 2; g.add(disk);
    const rim = new THREE.Mesh(new THREE.TorusGeometry(1.75, .025, 8, 80), gold); rim.rotation.x = Math.PI / 2; g.add(rim);
    const hub = new THREE.Mesh(new THREE.CylinderGeometry(.14, .14, .12, 24), darkMetal); g.add(hub);
    craft.add(tag(g, 'array')); arrays.push(g);
  }
  const navRed = new THREE.Mesh(new THREE.SphereGeometry(.05, 12, 12), new THREE.MeshBasicMaterial({ color: 0xff3b4e })); navRed.position.set(-1.9, 1.12, 0); craft.add(navRed);
  const navGreen = new THREE.Mesh(new THREE.SphereGeometry(.05, 12, 12), new THREE.MeshBasicMaterial({ color: 0x3dff9a })); navGreen.position.set(-1.9, -1.12, 0); craft.add(navGreen);
  const strobe = new THREE.Mesh(new THREE.SphereGeometry(.05, 12, 12), new THREE.MeshBasicMaterial({ color: 0xffffff })); strobe.position.set(-2.9, 0, 0); craft.add(strobe);

  // ---------- Experiment inside the cargo module ----------
  const exp = new THREE.Group(); craft.add(exp);
  const ductMat = new THREE.MeshStandardMaterial({ color: 0x0b1119, metalness: .4, roughness: .6, transparent: true, opacity: .55, side: THREE.DoubleSide, depthWrite: false });
  const duct = new THREE.Mesh(new THREE.BoxGeometry(2.5, .55, .55), ductMat); duct.position.set(-.6, -.15, 0); exp.add(tag(duct, 'duct'));
  const ductEdges = new THREE.LineSegments(new THREE.EdgesGeometry(duct.geometry), new THREE.LineBasicMaterial({ color: 0x77c3ed, transparent: true, opacity: .7 })); ductEdges.position.copy(duct.position); exp.add(ductEdges);
  const fan = new THREE.Group(); fan.position.set(-1.78, -.15, 0); exp.add(tag(fan, 'fan'));
  const bladeMat = new THREE.MeshStandardMaterial({ color: 0x1f2832, metalness: .5, roughness: .6 });
  for (let i = 0; i < 4; i++) { const blade = new THREE.Mesh(new THREE.BoxGeometry(.01, .2, .05), bladeMat); blade.rotation.x = i * Math.PI / 2; blade.position.set(0, Math.cos(i * Math.PI / 2) * .1, Math.sin(i * Math.PI / 2) * .1); fan.add(blade); }
  const sampleMat = new THREE.MeshStandardMaterial({ color: 0xb9a57e, roughness: .8, side: THREE.DoubleSide });
  const sample = new THREE.Mesh(new THREE.PlaneGeometry(SAMPLE_X1 - SAMPLE_X0, .25), sampleMat); sample.rotation.x = -Math.PI / 2; sample.position.set((SAMPLE_X0 + SAMPLE_X1) / 2, SAMPLE_Y, 0); exp.add(tag(sample, 'sample'));
  const nomex = new THREE.Mesh(new THREE.PlaneGeometry(1, .25), new THREE.MeshStandardMaterial({ color: 0xc9a24f, roughness: .7, side: THREE.DoubleSide })); nomex.rotation.x = -Math.PI / 2; nomex.visible = false; exp.add(tag(nomex, 'sample'));
  const burnt = new THREE.Mesh(new THREE.PlaneGeometry(1, .25), new THREE.MeshStandardMaterial({ color: 0x0d0607, roughness: 1, side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: -2 })); burnt.rotation.x = -Math.PI / 2; burnt.position.y = SAMPLE_Y + .002; exp.add(burnt);
  const regress = new THREE.Mesh(new THREE.PlaneGeometry(1, .25), new THREE.MeshBasicMaterial({ color: 0x2a0a10, transparent: true, opacity: 0, side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: -3 })); regress.rotation.x = -Math.PI / 2; regress.position.y = SAMPLE_Y + .003; exp.add(regress);
  const igniterMat = new THREE.MeshStandardMaterial({ color: 0x8c5a2b, emissive: 0xff5a1f, emissiveIntensity: 0, metalness: .5, roughness: .4 });
  const igniter = new THREE.Mesh(new THREE.TorusGeometry(.05, .012, 8, 24), igniterMat); igniter.rotation.y = Math.PI / 2; igniter.position.set(SAMPLE_X0 - .03, SAMPLE_Y + .02, 0); exp.add(tag(igniter, 'igniter'));
  const beads: THREE.Mesh[] = [];
  for (let i = 0; i < 6; i++) {
    const x = SAMPLE_X0 + .12 + i * .24;
    const wire = new THREE.Mesh(new THREE.CylinderGeometry(.006, .006, .14), darkMetal); wire.position.set(x, .02, .06); exp.add(tag(wire, 'tc'));
    const bead = new THREE.Mesh(new THREE.SphereGeometry(.018, 12, 12), new THREE.MeshStandardMaterial({ color: 0x3c5064, emissive: 0x000000 })); bead.position.set(x, -.05, .06); bead.userData.x = x; exp.add(tag(bead, 'tc')); beads.push(bead);
  }
  const co2Mat = new THREE.MeshStandardMaterial({ color: 0x0b1119, emissive: 0xffb347, emissiveIntensity: 0, metalness: .3, roughness: .5 });
  const co2 = new THREE.Mesh(new THREE.BoxGeometry(.14, .14, .14), co2Mat); co2.position.set(SENSOR_X, -.15, 0); exp.add(tag(co2, 'co2'));

  // Flame: layered additive sprites and a point light that lights the duct.
  const flame = new THREE.Group(); exp.add(flame);
  const outer = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTexture('rgba(255,214,150,1)', 'rgba(255,90,61,.55)'), blending: THREE.AdditiveBlending, depthWrite: false, transparent: true }));
  const inner = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTexture('rgba(255,250,235,1)', 'rgba(255,179,71,.6)'), blending: THREE.AdditiveBlending, depthWrite: false, transparent: true }));
  const edge = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTexture('rgba(190,230,255,1)', 'rgba(34,139,223,.5)'), blending: THREE.AdditiveBlending, depthWrite: false, transparent: true }));
  flame.add(outer, inner, edge);
  const flameLight = new THREE.PointLight(0xff8a3d, 0, 3, 1.6); flame.add(flameLight);

  // Smoke particles and flow streaks
  const smokePos = new Float32Array(SMOKE_N * 3).fill(-999), smokeLife = new Float32Array(SMOKE_N), smokeVel = new Float32Array(SMOKE_N * 2);
  const smokeGeo = new THREE.BufferGeometry(); smokeGeo.setAttribute('position', new THREE.BufferAttribute(smokePos, 3));
  const smoke = new THREE.Points(smokeGeo, new THREE.PointsMaterial({ map: glowTexture('rgba(200,210,220,.9)', 'rgba(160,170,180,.35)'), size: .07, transparent: true, depthWrite: false, opacity: .8, color: 0xb8c4cf }));
  exp.add(smoke);
  const streakPos = new Float32Array(STREAKS * 6), streakX = new Float32Array(STREAKS);
  const streakGeo = new THREE.BufferGeometry(); streakGeo.setAttribute('position', new THREE.BufferAttribute(streakPos, 3));
  const streaks = new THREE.LineSegments(streakGeo, new THREE.LineBasicMaterial({ color: 0x77c3ed, transparent: true, opacity: .55 })); exp.add(streaks);
  for (let i = 0; i < STREAKS; i++) streakX[i] = -1.8 + rnd() * 2.4;

  // ---------- Composer (bloom) ----------
  const composer = new EffectComposer(renderer);
  composer.addPass(new RenderPass(scene, camera));
  const bloom = new UnrealBloomPass(new THREE.Vector2(1, 1), .6, .45, .92); composer.addPass(bloom);
  composer.addPass(new OutputPass());

  // ---------- Labels ----------
  const labelPos: Record<string, THREE.Vector3> = {
    cargo: new THREE.Vector3(-1.4, 1.3, 0), service: new THREE.Vector3(2.4, 1.2, 0), array: new THREE.Vector3(2.05, .2, 5.9), earth: new THREE.Vector3(),
    duct: new THREE.Vector3(-1.6, .2, 0), 'duct-in': new THREE.Vector3(-1.6, .2, 0), sample: new THREE.Vector3(-.6, -.2, .2), igniter: new THREE.Vector3(SAMPLE_X0, -.15, .1), tc: new THREE.Vector3(-.2, .1, .06), co2: new THREE.Vector3(SENSOR_X, 0, 0), fan: new THREE.Vector3(-1.78, .05, 0),
  };
  const labelEls = labels.map(l => { const el = document.createElement('span'); el.className = `ms-label${l.inside ? ' ms-label-in' : ''}`; el.textContent = l.text; labelLayer.appendChild(el); return { ...l, el }; });

  // ---------- State ----------
  let cutaway = false, showLabels = true, orbitOn = true, flowOn = true, theta = .6, disposed = false, raf = 0;
  let input: SceneInput = { flame: { x: 0, alive: 0, burnt: 0, regress: 0, pulse: 0 }, sensed: 0, heat: 0, intensity: .5 };
  let spec: SampleSpec = { material: 'SIBAL', opposed: false, leadInCm: null };
  let flying: { local: { x: number; y: number; z: number; tx: number; ty: number; tz: number }; anim: JSAnimation } | null = null;
  let pickCb: ((p: ScenePart | null) => void) | null = null;
  const prevCraft = new THREE.Vector3();
  const tmp = new THREE.Vector3(), basis = new THREE.Matrix4();

  function placeCraft(dt: number) {
    if (orbitOn) theta += dt * .012;
    const pos = new THREE.Vector3(Math.cos(theta) * ORBIT_R, 0, Math.sin(theta) * ORBIT_R).applyEuler(orbitTilt);
    const tangent = new THREE.Vector3(-Math.sin(theta), 0, Math.cos(theta)).applyEuler(orbitTilt).normalize();
    const radial = pos.clone().normalize(), side = new THREE.Vector3().crossVectors(tangent, radial).normalize();
    basis.makeBasis(tangent, radial, side); craft.quaternion.setFromRotationMatrix(basis); craft.position.copy(pos);
  }

  const presets: Record<Preset, () => [THREE.Vector3, THREE.Vector3]> = {
    orbit: () => [new THREE.Vector3(-34, 26, 52), new THREE.Vector3(0, 0, 0)],
    craft: () => [new THREE.Vector3(7.5, 4.2, 9), new THREE.Vector3(.3, 0, 0)],
    inside: () => [new THREE.Vector3(-.6, 1.25, 2.6), new THREE.Vector3(-.6, -.18, 0)],
    flame: () => { const fx = flameX(); return [new THREE.Vector3(fx + .55, .45, 1.35), new THREE.Vector3(fx + .1, SAMPLE_Y, 0)]; },
  };
  const flameX = () => (spec.opposed ? SAMPLE_X1 - input.flame.x * CM : SAMPLE_X0 + input.flame.x * CM);

  function fly(p: Preset, duration = 1600) {
    flying?.anim.pause();
    const camLocal = craft.worldToLocal(camera.position.clone()), tgtLocal = craft.worldToLocal(controls.target.clone());
    const [c, t] = presets[p]();
    const local = { x: camLocal.x, y: camLocal.y, z: camLocal.z, tx: tgtLocal.x, ty: tgtLocal.y, tz: tgtLocal.z };
    controls.enabled = false;
    const anim = animate(local, { x: c.x, y: c.y, z: c.z, tx: t.x, ty: t.y, tz: t.z, duration, ease: 'inOut(3)', onComplete: () => { flying = null; controls.enabled = true; } });
    flying = { local, anim };
    if (p === 'inside' || p === 'flame') setCutaway(true);
  }

  function setCutaway(on: boolean) {
    cutaway = on; hullMat.transparent = on; hullMat.opacity = on ? .1 : 1; hullMat.depthWrite = !on; hullMat.wireframe = on;
    hullMat.color.setHex(on ? 0x77c3ed : 0xd7dde3); hullMat.emissive.setHex(on ? 0x0a2033 : 0x000000); hullMat.needsUpdate = true;
  }

  function setSample(s: SampleSpec) {
    spec = s; sampleMat.color.setHex(MATERIAL_COLORS[s.material] ?? 0x8c9eae);
    const len = SAMPLE_X1 - SAMPLE_X0;
    if (s.leadInCm) { const lead = s.leadInCm * CM; nomex.visible = true; nomex.scale.x = len - lead; nomex.position.set(SAMPLE_X0 + lead + (len - lead) / 2, SAMPLE_Y + .001, 0); } else nomex.visible = false;
    igniter.position.x = s.opposed ? SAMPLE_X1 + .03 : SAMPLE_X0 - .03;
    smokePos.fill(-999); smokeLife.fill(0); smokeGeo.attributes.position.needsUpdate = true;
  }

  function resize() {
    const w = canvas.clientWidth, h = canvas.clientHeight; if (!w || !h) return;
    renderer.setSize(w, h, false); composer.setSize(w, h); bloom.setSize(w, h); camera.aspect = w / h; camera.updateProjectionMatrix();
  }
  const ro = new ResizeObserver(resize); ro.observe(canvas);

  // Picking (click without drag)
  const ray = new THREE.Raycaster(), ndc = new THREE.Vector2(); let down = { x: 0, y: 0 };
  const onDown = (e: PointerEvent) => { down = { x: e.clientX, y: e.clientY }; };
  const onUp = (e: PointerEvent) => {
    if (Math.hypot(e.clientX - down.x, e.clientY - down.y) > 5 || !pickCb) return;
    const r = canvas.getBoundingClientRect(); ndc.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
    ray.setFromCamera(ndc, camera);
    const hits = ray.intersectObjects(scene.children, true).filter(h => h.object.userData.part && h.object.visible && !(h.object.userData.part === 'cargo' && cutaway));
    pickCb(hits.length ? hits[0].object.userData.part as ScenePart : null);
  };
  canvas.addEventListener('pointerdown', onDown); canvas.addEventListener('pointerup', onUp);

  // Initial placement
  placeCraft(0); prevCraft.copy(craft.position);
  camera.position.copy(craft.localToWorld(new THREE.Vector3(7.5, 4.2, 9))); controls.target.copy(craft.position);
  resize();

  const clock = new THREE.Clock();
  function frame() {
    if (disposed) return;
    const dt = Math.min(clock.getDelta(), .05), T = clock.elapsedTime;
    placeCraft(dt);
    earth.rotation.y += dt * .01; clouds.rotation.y += dt * .004;
    if (flying) {
      const l = flying.local;
      camera.position.copy(craft.localToWorld(tmp.set(l.x, l.y, l.z)));
      controls.target.copy(craft.localToWorld(new THREE.Vector3(l.tx, l.ty, l.tz)));
    } else {
      const delta = craft.position.clone().sub(prevCraft); camera.position.add(delta); controls.target.add(delta);
    }
    prevCraft.copy(craft.position);
    controls.update();

    // Spacecraft life
    navRed.visible = Math.sin(T * 3.2) > 0; navGreen.visible = Math.sin(T * 3.2 + 1.6) > 0; strobe.visible = (T % 2) < .08;
    arrays.forEach((a, i) => { a.rotation.y = Math.sin(T * .05 + i) * .02; });
    fan.rotation.x += dt * 14;

    // Experiment
    const f = input.flame, fx = flameX(), dir = spec.opposed ? -1 : 1;
    flame.position.set(fx, SAMPLE_Y + .06, 0);
    const flick = 1 + Math.sin(T * 23) * .06 + Math.sin(T * 37) * .04, a = f.alive;
    outer.scale.set(.62 * flick * a + .001, .34 * flick * a + .001, 1); outer.position.x = dir * .12;
    inner.scale.set(.26 * flick * a + .001, .16 * a + .001, 1); inner.position.x = dir * .04;
    edge.scale.set(.1 * a + .001, .22 * a + .001, 1); edge.position.x = -dir * .03;
    (outer.material as THREE.SpriteMaterial).opacity = a; (inner.material as THREE.SpriteMaterial).opacity = a; (edge.material as THREE.SpriteMaterial).opacity = a;
    flameLight.intensity = a * 3.2 * flick;
    const bw = Math.max(.0001, f.burnt * CM); burnt.scale.x = bw; burnt.position.x = spec.opposed ? SAMPLE_X1 - bw / 2 : SAMPLE_X0 + bw / 2;
    const rw = Math.max(.0001, (spec.leadInCm ? 0 : 10) * CM * f.regress); regress.scale.x = rw; regress.position.x = spec.opposed ? SAMPLE_X1 - rw / 2 : SAMPLE_X0 + rw / 2; (regress.material as THREE.MeshBasicMaterial).opacity = f.regress * .8;
    igniterMat.emissiveIntensity = f.pulse * 2.5;
    beads.forEach(b => { const d = Math.abs(b.userData.x - fx), heat = a * input.heat * Math.max(0, 1 - d * 1.8); (b.material as THREE.MeshStandardMaterial).emissive.setRGB(heat * 1.2, heat * .45, heat * .1); });
    co2Mat.emissiveIntensity = input.sensed * 1.6;

    // Smoke: emitted at the flame, carried downstream (+x) by the duct flow toward the CO₂ sensor.
    const emit = a * input.intensity;
    for (let i = 0; i < SMOKE_N; i++) {
      const k = i * 3;
      if (smokeLife[i] <= 0) {
        if (emit > 0 && Math.random() < emit * .08) { smokeLife[i] = 1; smokePos[k] = fx + dir * .05; smokePos[k + 1] = SAMPLE_Y + .05 + Math.random() * .04; smokePos[k + 2] = (Math.random() - .5) * .1; smokeVel[i * 2] = (Math.random() - .5) * .06; smokeVel[i * 2 + 1] = (Math.random() - .5) * .06; }
        else smokePos[k + 1] = -999;
        continue;
      }
      smokePos[k] += dt * .55; smokePos[k + 1] += smokeVel[i * 2] * dt; smokePos[k + 2] += smokeVel[i * 2 + 1] * dt;
      smokeLife[i] -= dt * .35;
      if (smokePos[k] > SENSOR_X + .05) smokeLife[i] = 0;
    }
    smokeGeo.attributes.position.needsUpdate = true;
    streaks.visible = flowOn && cutaway;
    for (let i = 0; i < STREAKS; i++) {
      streakX[i] += dt * .9; if (streakX[i] > .6) streakX[i] = -1.8;
      const y = -.38 + (i % 5) * .045 + (i % 2 ? .3 : 0), z = -.2 + ((i * 7) % 9) * .05, k = i * 6;
      streakPos.set([streakX[i], y, z, streakX[i] + .1, y, z], k);
    }
    streakGeo.attributes.position.needsUpdate = true;
    exp.visible = cutaway || camera.position.distanceTo(craft.position) < 2.5;
    sunSprite.visible = !cutaway;

    // Labels
    const w = canvas.clientWidth, h = canvas.clientHeight, dist = camera.position.distanceTo(craft.position);
    for (const l of labelEls) {
      const show = showLabels && (l.inside ? cutaway && dist < 9 : l.part === 'earth' ? dist > 30 : dist < 40);
      if (!show) { l.el.style.opacity = '0'; continue; }
      const p = l.part === 'earth' ? new THREE.Vector3(0, EARTH_R * 1.1, 0) : craft.localToWorld(labelPos[l.part].clone());
      const v = p.project(camera);
      if (v.z > 1) { l.el.style.opacity = '0'; continue; }
      l.el.style.opacity = '1'; l.el.style.transform = `translate(${((v.x + 1) / 2) * w}px, ${((1 - v.y) / 2) * h}px)`;
    }
    composer.render();
    raf = requestAnimationFrame(frame);
  }
  raf = requestAnimationFrame(frame);

  return {
    update(i: SceneInput) { input = i; },
    setSample, setCutaway, fly,
    setLabels(on: boolean) { showLabels = on; },
    setOrbit(on: boolean) { orbitOn = on; },
    setFlowVectors(on: boolean) { flowOn = on; },
    zoom(f: number) { const d = camera.position.clone().sub(controls.target); camera.position.copy(controls.target).add(d.multiplyScalar(f)); },
    onPick(cb: (p: ScenePart | null) => void) { pickCb = cb; },
    isCutaway: () => cutaway,
    dispose() {
      disposed = true; cancelAnimationFrame(raf); ro.disconnect(); flying?.anim.pause();
      canvas.removeEventListener('pointerdown', onDown); canvas.removeEventListener('pointerup', onUp);
      labelEls.forEach(l => l.el.remove()); controls.dispose(); composer.dispose();
      scene.traverse(o => { const m = o as THREE.Mesh; m.geometry?.dispose?.(); const mat = m.material as THREE.Material | THREE.Material[] | undefined; (Array.isArray(mat) ? mat : mat ? [mat] : []).forEach(x => { (x as THREE.MeshStandardMaterial).map?.dispose(); x.dispose(); }); });
      renderer.dispose();
    },
  };
}
export type MissionScene = ReturnType<typeof createMissionScene>;
