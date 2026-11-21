// v4 atmosphere: dust motes, light-shaft haze, screen-light flicker, handheld sway. Everything is a pure function of t (seek-safe, seeded).
export const ATMO = {
  dust: true, haze: true, flicker: true, sway: true,
  nMotes: 200, nBokeh: 7, nNear: 110, nearFloor: .38, moteMaxA: .5, bokehMaxA: .08, moteSize: [3, 6], lightGain: .95, lightFloor: .07,
  hazeOp: .045, neonOp: .035, flickAmt: .04,
  swayRot: .25 * Math.PI / 180, swayPos: .004,
};

function rng(seed) { let a = seed >>> 0; return () => { a = (a + 0x6D2B79F5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
const sstep = (a, b, x) => { const u = Math.max(0, Math.min(1, (x - a) / (b - a))); return u * u * (3 - 2 * u); };
const TAU = Math.PI * 2;

// 3-sine "noise" in -1..1, frequencies in 0.3..0.7 Hz (sway) or custom range
function mkNoise(seed, f0, f1) {
  const r = rng(seed), c = [0, 1, 2].map(() => ({ f: f0 + (f1 - f0) * r(), p: r() * TAU, w: .4 + .6 * r() }));
  const ws = c.reduce((s, k) => s + k.w, 0);
  return t => c.reduce((s, k) => s + k.w * Math.sin(TAU * k.f * t + k.p), 0) / ws;
}

const VS = `attribute float aSize; attribute float aA; varying float vA; uniform float uPx;
void main(){ vA = aA; vec4 mv = modelViewMatrix * vec4(position,1.); gl_Position = projectionMatrix * mv; gl_PointSize = aSize * uPx; }`;
const FS_DUST = `varying float vA; uniform vec3 uCol;
void main(){ float r = length(gl_PointCoord - .5) * 2.; float f = 1. - smoothstep(0., 1., r); f = 1. - smoothstep(.25, 1., r); if (f < .02) discard; gl_FragColor = vec4(uCol * 2.4, vA * f); }`;
const FS_DISC = `varying float vA; uniform vec3 uCol;
void main(){ float r = length(gl_PointCoord - .5) * 2.; float f = (1. - smoothstep(.82, 1., r)) * (.55 + .45 * smoothstep(.3, .9, r)); gl_FragColor = vec4(uCol, vA * f); }`;
const VS_BEAM = `varying vec3 vN; varying vec3 vV; varying vec2 vUv;
void main(){ vUv = uv; vec4 mv = modelViewMatrix * vec4(position,1.); vN = normalize(normalMatrix * normal); vV = -mv.xyz; gl_Position = projectionMatrix * mv; }`;
const FS_BEAM = `varying vec3 vN; varying vec3 vV; varying vec2 vUv; uniform vec3 uCol; uniform float uOp;
void main(){ float nv = clamp(abs(dot(normalize(vN), normalize(vV))), 0., 1.); float a = pow(nv, 2.2) * pow(vUv.y, 1.3) * (1. - smoothstep(.88, 1., vUv.y)) * uOp; gl_FragColor = vec4(uCol, clamp(a, 0., 1.)); }`;

let S = null;

function setup(ctx) {
  const { THREE, scene, renderer, GUY, lid, koG, LK, scr, keySpot, SHELF_X, SHELF_Y } = ctx;
  const r = rng(4242);
  scene.updateMatrixWorld(true);
  S = { THREE, group: new THREE.Group(), r };
  S.group.name = 'atmo'; scene.add(S.group);
  const V = (x, y, z) => new THREE.Vector3(x, y, z);
  S.lp = lid.localToWorld(V(0, .22, .1));
  const face = GUY.localToWorld(V(0, 1.5, .1));
  S.dir = face.clone().sub(S.lp).normalize();
  S.koP = V(koG.position.x, .95, -.05);
  S.neonY = SHELF_Y - .07; S.neonZ = -1.3; S.sx0 = SHELF_X - .85; S.sx1 = SHELF_X + .85;
  const px = renderer.getPixelRatio();

  // ---- dust ----
  S.box = { x0: -1.9, x1: 1.8, y0: .55, y1: 2.5, z0: -1.1, z1: 1.5 };
  const N = ATMO.nMotes;
  S.m = Array.from({ length: N }, () => ({
    b: V(S.box.x0 + r() * (S.box.x1 - S.box.x0), S.box.y0 + r() * (S.box.y1 - S.box.y0), S.box.z0 + r() * (S.box.z1 - S.box.z0)),
    n: [mkNoise(r() * 1e9, .08, .22), mkNoise(r() * 1e9, .08, .22), mkNoise(r() * 1e9, .08, .22)],
    amp: .05 + .08 * r(), up: .004 + .008 * r(), size: ATMO.moteSize[0] + (ATMO.moteSize[1] - ATMO.moteSize[0]) * r(), tw: r() * TAU, twf: .15 + .35 * r(),
  }));
  const mk = (n, fs, col) => {
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(n * 3), 3));
    g.setAttribute('aSize', new THREE.BufferAttribute(new Float32Array(n), 1));
    g.setAttribute('aA', new THREE.BufferAttribute(new Float32Array(n), 1));
    const mat = new THREE.ShaderMaterial({ vertexShader: VS, fragmentShader: fs, uniforms: { uPx: { value: px }, uCol: { value: new THREE.Color(col) } },
      transparent: true, depthWrite: fs === FS_DUST, depthTest: true, blending: THREE.AdditiveBlending });
    const p = new THREE.Points(g, mat); p.frustumCulled = false; p.renderOrder = 5; S.group.add(p); return p;
  };
  S.dust = mk(N, FS_DUST, 0xFFE9CC);
  S.bk = Array.from({ length: ATMO.nBokeh }, () => ({ x: r() * 2 - 1, y: r() * 2 - 1, d: .55 + .7 * r(), size: 50 + 60 * r(), n: [mkNoise(r() * 1e9, .04, .1), mkNoise(r() * 1e9, .04, .1)], k: .6 + .4 * r() }));
  S.nr = Array.from({ length: ATMO.nNear }, () => ({ u: r() * 2 - 1, v: r() * 2 - 1, d: .7 + 2.8 * r(), n: [mkNoise(r() * 1e9, .06, .16), mkNoise(r() * 1e9, .06, .16), mkNoise(r() * 1e9, .06, .16)], amp: .08 + .1 * r(), size: ATMO.moteSize[0] + (ATMO.moteSize[1] - ATMO.moteSize[0]) * r(), tw: r() * TAU, twf: .15 + .35 * r() }));
  S.near = mk(ATMO.nNear, FS_DUST, 0xFFE9CC);
  S.bokeh = mk(ATMO.nBokeh, FS_DISC, 0xFFDDBB);
  S.bokeh.geometry.attributes.aSize.array.forEach((_, i, a) => a[i] = S.bk[i].size);

  // ---- haze: soft open cones, edge-faded in the shader ----
  const beam = (rt, rb, h, col) => {
    const g = new THREE.CylinderGeometry(rt, rb, h, 32, 1, true); g.translate(0, -h / 2, 0);
    const m = new THREE.ShaderMaterial({ vertexShader: VS_BEAM, fragmentShader: FS_BEAM, uniforms: { uCol: { value: new THREE.Color(col) }, uOp: { value: 0 } },
      transparent: true, depthWrite: false, side: THREE.DoubleSide, blending: THREE.AdditiveBlending });
    const o = new THREE.Mesh(g, m); o.renderOrder = 4; o.frustumCulled = false; S.group.add(o); return o;
  };
  const L = face.distanceTo(S.lp) * .95;
  S.b1 = beam(.1, .42, L, 0xBFD4FF); S.b1.position.copy(S.lp);
  S.b1.quaternion.setFromUnitVectors(V(0, -1, 0), S.dir);
  S.b2 = beam(.5, .8, 1.1, 0xA27BFF); S.b2.position.set(SHELF_X, S.neonY, S.neonZ - .05); S.b2.scale.set(1.0, 1, .28);

  // ---- flicker bases ----
  S.fk = { key: keySpot.intensity, scrL: LK && LK.scrL ? LK.scrL.intensity : 0, col: scr.material.color.clone(), n: mkNoise(77, .2, .6), n2: mkNoise(78, .9, 1.7) };
  // ---- sway noises per shot ----
  S.sw = {};
  S.tmp = V(0, 0, 0);
}

function light(p) {
  const T = S.tmp;
  // laptop screen cone
  T.copy(p).sub(S.lp); const d = Math.max(T.length(), .05), c = T.dot(S.dir) / d;
  const bs = sstep(.78, .96, c) * (1 / (1 + (d / .8) * (d / .8))) * 1.6;
  // neon strip
  const nx = Math.max(S.sx0, Math.min(S.sx1, p.x)), dn = Math.hypot(p.x - nx, p.y - S.neonY, p.z - S.neonZ);
  const bn = Math.exp(-dn / .45) * .9 * sstep(.1, -.2, p.y - S.neonY);
  // Ko glow
  const dk = p.distanceTo(S.koP), bk = Math.exp(-(dk / .45) * (dk / .45)) * .7;
  return bs + bn + bk + ATMO.lightFloor;
}

// ctx: {THREE, scene, cam, renderer, keySpot, LK, GUY, lid, koG, scr, SHELF_X, SHELF_Y}; shot: {id, cam}
export function atmo(t, ctx, shot) {
  if (!S) setup(ctx);
  const { cam } = ctx, THREE = S.THREE;
  const on = shot.cam !== 'INSERT';
  S.group.visible = on;
  if (!on) return;

  // sway (after camAt): handheld breathing
  if (ATMO.sway) {
    const id = parseInt(String(shot.id).replace(/\D/g, '')) || 1;
    const k = S.sw[id] || (S.sw[id] = [0, 1, 2, 3, 4, 5].map(i => mkNoise(1000 + id * 31 + i * 7, .3, .7)));
    cam.position.x += ATMO.swayPos * k[0](t); cam.position.y += ATMO.swayPos * k[1](t); cam.position.z += ATMO.swayPos * k[2](t);
    cam.rotateX(ATMO.swayRot * k[3](t)); cam.rotateY(ATMO.swayRot * k[4](t)); cam.rotateZ(ATMO.swayRot * .5 * k[5](t));
  }
  cam.updateMatrixWorld(true);

  // flicker
  let fl = 1;
  if (ATMO.flicker) {
    fl = 1 + ATMO.flickAmt * (.7 * S.fk.n(t) + .3 * S.fk.n2(t));
    ctx.keySpot.intensity = S.fk.key * fl;
    if (ctx.LK && ctx.LK.scrL) ctx.LK.scrL.intensity = S.fk.scrL * fl;
    ctx.scr.material.color.copy(S.fk.col).multiplyScalar(fl);
  }

  // haze
  S.b1.visible = S.b2.visible = !!ATMO.haze;
  if (ATMO.haze) { S.b1.material.uniforms.uOp.value = ATMO.hazeOp * fl; S.b2.material.uniforms.uOp.value = ATMO.neonOp; }

  // dust
  S.dust.visible = S.bokeh.visible = S.near.visible = !!ATMO.dust;
  if (ATMO.dust) {
    const bx = S.box, pos = S.dust.geometry.attributes.position.array, sz = S.dust.geometry.attributes.aSize.array, al = S.dust.geometry.attributes.aA.array;
    const P = new THREE.Vector3(); S.vis = 0;
    S.m.forEach((m, i) => {
      const H = bx.y1 - bx.y0;
      let y = ((m.b.y - bx.y0 + m.up * t) % H + H) % H;
      P.set(m.b.x + m.amp * m.n[0](t), bx.y0 + y + m.amp * .6 * m.n[1](t), m.b.z + m.amp * m.n[2](t));
      const edge = sstep(0, .12, y / H) * sstep(1, .88, y / H);
      const a = Math.min(ATMO.moteMaxA, light(P) * ATMO.lightGain) * (.7 + .3 * Math.sin(TAU * m.twf * t + m.tw)) * edge;
      pos[i * 3] = P.x; pos[i * 3 + 1] = P.y; pos[i * 3 + 2] = P.z; sz[i] = m.size; al[i] = a;
      if (a > .08) S.vis++;
    });
    S.dust.geometry.attributes.position.needsUpdate = S.dust.geometry.attributes.aA.needsUpdate = S.dust.geometry.attributes.aSize.needsUpdate = true;

    // near layer: loosely camera-framed motes (close-ups have little world volume), drifting by noise
    const nA = S.near.geometry.attributes, npz = nA.position.array, nsz = nA.aSize.array, nal = nA.aA.array;
    const cs = shot.cam === 'B' || shot.cam === 'C';
    S.near.visible = cs;
    if (cs) {
      const f2 = new THREE.Vector3(0, 0, -1).applyQuaternion(cam.quaternion), r2 = new THREE.Vector3(1, 0, 0).applyQuaternion(cam.quaternion), u2 = new THREE.Vector3(0, 1, 0).applyQuaternion(cam.quaternion);
      const th2 = Math.tan(cam.fov * Math.PI / 360);
      const FZ = -ctx.FOCUS[shot.cam][0].clone().applyMatrix4(cam.matrixWorldInverse).z;
      S.nr.forEach((m, i) => {
        const d = FZ * (.62 + .6 * ((m.d - .7) / 2.8)) + m.amp * .5 * m.n[2](t), x = (m.u * .95 + .12 * m.n[0](t)) * d * th2 * (1080 / 1920), y = (m.v * .95 + .12 * m.n[1](t)) * d * th2;
        P.copy(cam.position).addScaledVector(f2, d).addScaledVector(r2, x).addScaledVector(u2, y);
        npz[i * 3] = P.x; npz[i * 3 + 1] = P.y; npz[i * 3 + 2] = P.z;
        nsz[i] = m.size * Math.min(1.5, 1.3 / Math.sqrt(d));
        nal[i] = Math.min(ATMO.moteMaxA, (light(P) * ATMO.lightGain + ATMO.nearFloor) * (.65 + .35 * Math.sin(TAU * m.twf * t + m.tw)));
      });
      nA.position.needsUpdate = nA.aA.needsUpdate = nA.aSize.needsUpdate = true;
    }

    // bokeh discs: glued loosely in front of the camera, drifting
    const bp = S.bokeh.geometry.attributes.position.array, ba = S.bokeh.geometry.attributes.aA.array;
    const camShot = shot.cam === 'B' || shot.cam === 'C';
    const fwd = new THREE.Vector3(0, 0, -1).applyQuaternion(cam.quaternion), rt = new THREE.Vector3(1, 0, 0).applyQuaternion(cam.quaternion), up = new THREE.Vector3(0, 1, 0).applyQuaternion(cam.quaternion);
    const th = Math.tan(cam.fov * Math.PI / 360);
    S.bk.forEach((b, i) => {
      const x = Math.max(-1, Math.min(1, b.x * .8 + .35 * b.n[0](t))), y = Math.max(-1, Math.min(1, b.y * .8 + .35 * b.n[1](t)));
      P.copy(cam.position).addScaledVector(fwd, b.d).addScaledVector(rt, x * b.d * th * (1080 / 1920)).addScaledVector(up, y * b.d * th);
      bp[i * 3] = P.x; bp[i * 3 + 1] = P.y; bp[i * 3 + 2] = P.z;
      ba[i] = camShot ? Math.min(ATMO.bokehMaxA, (.3 + light(P)) * .06) * b.k * (.75 + .25 * Math.sin(TAU * .12 * t + i)) : 0;
    });
    S.bokeh.geometry.attributes.position.needsUpdate = S.bokeh.geometry.attributes.aA.needsUpdate = true;
  }
}
export function atmoStats() { return S ? { vis: S.vis } : null; }
if (typeof window !== 'undefined') window.__atmoStats = atmoStats;
if (typeof window !== 'undefined') window.__ATMO = ATMO;
