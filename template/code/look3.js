// look3: richer "rendered" look for the soft Three.js route. One entry point, soft look only.
import { GTAOPass } from 'three/addons/postprocessing/GTAOPass.js';
import { RectAreaLightUniformsLib } from 'three/addons/lights/RectAreaLightUniformsLib.js';

// ---- seeded procedural textures (no downloads) ----
function rng(seed) { let a = seed >>> 0; return () => { a = (a + 0x6D2B79F5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
// tileable value noise, returns Float32Array n*n in 0..1
function noiseField(n, seed, cells, octaves, gain = .5) {
  const out = new Float32Array(n * n);
  let amp = 1, tot = 0;
  for (let o = 0; o < octaves; o++) {
    const c = cells << o, r = rng(seed + o * 101), g = new Float32Array(c * c);
    for (let i = 0; i < g.length; i++) g[i] = r();
    for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) {
      const fx = x / n * c, fy = y / n * c, x0 = Math.floor(fx), y0 = Math.floor(fy), tx = fx - x0, ty = fy - y0;
      const sx = tx * tx * (3 - 2 * tx), sy = ty * ty * (3 - 2 * ty);
      const a = g[(y0 % c) * c + (x0 % c)], b = g[(y0 % c) * c + ((x0 + 1) % c)], cc = g[((y0 + 1) % c) * c + (x0 % c)], d = g[((y0 + 1) % c) * c + ((x0 + 1) % c)];
      out[y * n + x] += amp * ((a + (b - a) * sx) * (1 - sy) + (cc + (d - cc) * sx) * sy);
    }
    tot += amp; amp *= gain;
  }
  for (let i = 0; i < out.length; i++) out[i] /= tot;
  return out;
}
function canvasFrom(THREE, n, fn, srgb) {
  const c = document.createElement('canvas'); c.width = c.height = n; const g = c.getContext('2d'), im = g.createImageData(n, n);
  for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) { const v = fn(x, y), k = (y * n + x) * 4; im.data[k] = v[0]; im.data[k + 1] = v[1]; im.data[k + 2] = v[2]; im.data[k + 3] = 255; }
  g.putImageData(im, 0, 0);
  const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.anisotropy = 8; if (srgb) t.colorSpace = THREE.SRGBColorSpace; return t;
}
// height field -> tangent-space normal map
function normalFrom(THREE, n, h, strength) {
  return canvasFrom(THREE, n, (x, y) => {
    const L = h[y * n + (x + n - 1) % n], R = h[y * n + (x + 1) % n], U = h[((y + n - 1) % n) * n + x], D = h[((y + 1) % n) * n + x];
    let nx = (L - R) * strength, ny = (U - D) * strength, nz = 1; const l = Math.hypot(nx, ny, nz);
    return [(nx / l * .5 + .5) * 255, (ny / l * .5 + .5) * 255, (nz / l * .5 + .5) * 255];
  }, false);
}
const grey = v => { const g = Math.max(0, Math.min(255, v * 255)); return [g, g, g]; };

export function upgrade(ctx) {
  const { THREE, scene, renderer, composer, cam, rt, PAL, LAP, lid, GUY, koG, koMat, usMat, SHELF_X, SHELF_Y, W, H, dpr } = ctx;
  RectAreaLightUniformsLib.init();
  const N = 256;

  // ---- textures ----
  const plasterH = noiseField(N, 11, 6, 5, .55), plasterB = normalFrom(THREE, N, plasterH, 2.2);
  const plasterR = canvasFrom(THREE, N, (x, y) => grey(.78 + plasterH[y * N + x] * .22), false);
  const wallAlb = canvasFrom(THREE, N, (x, y) => grey(.86 + plasterH[y * N + x] * .14), true);
  for (const t of [plasterB, plasterR, wallAlb]) t.repeat.set(5, 2);

  // wood grain: streaks along U, plus rings
  const wn = noiseField(N, 23, 3, 3, .5), wn2 = noiseField(N, 29, 24, 2, .5);
  const woodH = new Float32Array(N * N);
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) { const w = wn[y * N + x]; const ring = .5 + .5 * Math.sin((y / N * 38 + w * 9) * 6.283 / 3); woodH[y * N + x] = ring * .3 + wn2[((y * 7) % N) * N + x] * .7; }
  const woodAlb = canvasFrom(THREE, N, (x, y) => grey(.86 + woodH[y * N + x] * .14), true);
  const woodRough = canvasFrom(THREE, N, (x, y) => grey(.55 + (1 - woodH[y * N + x]) * .35), false);
  const woodB = normalFrom(THREE, N, woodH, 1.2);
  for (const t of [woodAlb, woodRough, woodB]) t.repeat.set(1.4, 1);

  // knit weave for the hoodie (rows of V stitches)
  const weaveH = new Float32Array(N * N), fn = noiseField(N, 41, 32, 2, .5);
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
    const cx = (x / N * 24) % 1, cy = (y / N * 32) % 1, s = Math.abs(cx - .5) * 2, v = Math.max(0, 1 - Math.abs(cy - (.3 + s * .45)) * 4.5);
    weaveH[y * N + x] = v * .8 + fn[y * N + x] * .2;
  }
  const weaveB = normalFrom(THREE, N, weaveH, 3.2);
  const weaveAlb = canvasFrom(THREE, N, (x, y) => grey(.82 + weaveH[y * N + x] * .18), true);
  for (const t of [weaveB, weaveAlb]) t.repeat.set(2.2, 2.2);

  // denim twill: diagonal ribs
  const twH = new Float32Array(N * N), tn = noiseField(N, 53, 48, 2, .5);
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) twH[y * N + x] = (.5 + .5 * Math.sin((x + y) / N * 6.283 * 42)) * .75 + tn[y * N + x] * .25;
  const twillB = normalFrom(THREE, N, twH, 2.2);
  const twillAlb = canvasFrom(THREE, N, (x, y) => grey(.8 + twH[y * N + x] * .2), true);
  for (const t of [twillB, twillAlb]) t.repeat.set(2, 2);

  // skin: faint pores
  const skinH = noiseField(N, 67, 64, 2, .6), skinB = normalFrom(THREE, N, skinH, .7); skinB.repeat.set(2, 2);

  // ---- materials by palette colour ----
  const key = a => new THREE.Color(Array.isArray(a) ? a[0] : a).getHex();
  const K = { wall: key(PAL.wall), desk: key(PAL.desk), deskEdge: new THREE.Color(PAL.deskEdge).getHex(), hoodie: key(PAL.hoodie), skin: key(PAL.skin), jeans: key(PAL.jeans), mug: new THREE.Color('#E9E6F2').getHex(), chair: key(PAL.chair) };
  const seen = new Set();
  scene.traverse(o => {
    const m = o.isMesh && o.material; if (!m || !m.isMeshPhysicalMaterial || seen.has(m)) return; seen.add(m);
    const hx = m.color.getHex();
    if (hx === K.wall) { m.map = wallAlb; m.roughnessMap = plasterR; m.bumpMap = plasterB; m.bumpScale = 1.2; m.roughness = 1; m.color.multiplyScalar(1.1); }
    else if (hx === K.desk || hx === K.deskEdge) { m.map = woodAlb; m.roughnessMap = woodRough; m.normalMap = woodB; m.normalScale.set(.25, .25); m.roughness = 1; m.clearcoat = .08; m.clearcoatRoughness = .6; }
    else if (hx === K.hoodie) { m.map = weaveAlb; m.normalMap = weaveB; m.normalScale.set(.8, .8); m.sheen = 1; m.sheenRoughness = .5; m.sheenColor.set(0x9db4ff); }
    else if (hx === K.jeans) { m.map = twillAlb; m.normalMap = twillB; m.normalScale.set(.7, .7); m.roughness = .85; m.sheen = .6; m.sheenColor.set(0x6a7cc0); m.sheenRoughness = .6; }
    else if (hx === K.skin) { m.normalMap = skinB; m.normalScale.set(.25, .25); m.roughness = .5; m.sheen = .8; m.sheenRoughness = .4; m.sheenColor.set(0xff9a78); m.emissive.set(0xE2B08A).multiplyScalar(.07); m.clearcoat = .15; m.clearcoatRoughness = .5; }
    else if (hx === K.mug) { m.roughness = .22; m.clearcoat = 1; m.clearcoatRoughness = .06; }
    else if (hx === K.chair) { m.roughness = .7; m.sheen = .5; m.sheenColor.set(0x6a64a0); }
    m.needsUpdate = true;
  });
  for (const m of [koMat, usMat]) { m.roughness = .45; m.clearcoat = .25; m.clearcoatRoughness = .4; m.sheen = 0; m.sheenColor.set(0); m.sheenColor.set(0xffffff); m.needsUpdate = true; }

  // ---- softer shadows ----
  scene.traverse(o => { if (o.isSpotLight && o.castShadow) { o.shadow.radius = 14; o.shadow.blurSamples = 20; o.shadow.mapSize.set(2048, 2048); o.shadow.bias = -.0006; } });
  renderer.shadowMap.type = THREE.VSMShadowMap;

  // ---- indirect light ----
  // warm bounce from the desk top (faces up, lights chins, hands, Ko's underside)
  const bounce = new THREE.RectAreaLight(0xC8805A, .7, 3.0, 2.2); bounce.position.set(.9, .8, 1.1); bounce.lookAt(.9, 3, 1.1); scene.add(bounce);
  // laptop screen -> guy's face / hands / desk
  const lp = lid.localToWorld(new THREE.Vector3(0, .22, .1)), ln = lid.localToWorld(new THREE.Vector3(0, .22, 1.5));
  const scrL = new THREE.RectAreaLight(0xBFD4FF, 3.2, .6, .38); scrL.position.copy(lp); scrL.lookAt(ln); scene.add(scrL);
  // neon strip under the shelf -> wall + books
  const neon = new THREE.RectAreaLight(0xA27BFF, 9, 1.7, .12); neon.position.set(SHELF_X, SHELF_Y - .07, -1.3); neon.lookAt(SHELF_X, SHELF_Y - 1.0, -1.7); scene.add(neon);
  // cool sky fill from the open room side
  const fill = new THREE.RectAreaLight(0x6a7cc8, .7, 3, 2); fill.position.set(-2.2, 1.9, 1.8); fill.lookAt(0, 1.2, 0); scene.add(fill);

  // coloured rims / key (tasteful)
  const P = (x, y, z) => new THREE.Vector3(x, y, z);
  const kRim = new THREE.PointLight(0x9B6BFF, 7, 3, 2); kRim.position.set(.9, 1.5, -.85); scene.add(kRim);           // violet from behind Ko
  const gRim = new THREE.SpotLight(0x8F63FF, 22, 0, .55, 1, 2); gRim.position.set(-1.9, 2.3, -1.2); gRim.target.position.copy(GUY.localToWorld(P(0, 1.4, 0))); scene.add(gRim, gRim.target);
  const warm = new THREE.SpotLight(0xFFB57A, 4, 0, .5, 1, 2); warm.position.set(.2, 1.7, 1.2); warm.target.position.copy(GUY.localToWorld(P(0, 1.55, .1))); scene.add(warm, warm.target);   // warm laptop-side key on the face
  const spill = new THREE.PointLight(0xC7E44B, .45, 1.1, 2); spill.position.set(.55, .8, .5); scene.add(spill);    // Ko glow on the desk
  const bl = composer.passes.find(p => p.strength !== undefined && p.threshold !== undefined); if (bl) bl.strength = .22;
  // ---- ambient occlusion (before DoF) ----
  const ao = new GTAOPass(scene, cam, W * dpr, H * dpr);
  ao.updateGtaoMaterial({ radius: .32, distanceExponent: 1.4, thickness: 1.2, scale: 1.3, samples: 16, distanceFallOff: 1, screenSpaceRadius: false });
  ao.updatePdMaterial({ lumaPhi: 10, depthPhi: 2, normalPhi: 3, radius: 5, rings: 2, samples: 16 });
  ao.blendIntensity = 1.15;
  composer.insertPass(ao, 1);
  // AO adds one buffer swap per frame: keep the RenderPass on the same (depth-carrying) buffer every frame, DoF reads its depth
  // keep transparent quads (Ko face, glows) out of the AO normal/depth pass
  const aoRender = ao.render.bind(ao);
  ao.render = (...a) => { const hid = []; scene.traverse(o => { if (o.visible && ((o.isMesh && o.material && o.material.transparent) || o.isSprite || o.isPoints)) { o.visible = false; hid.push(o); } }); aoRender(...a); hid.forEach(o => o.visible = true); };
  const rb0 = composer.readBuffer, render0 = composer.render.bind(composer);
  composer.render = dt => { if (composer.readBuffer !== rb0) composer.swapBuffers(); ctx.dof.uniforms.tDepth.value = rb0.depthTexture; spill.color.copy(koMat.color); render0(dt); };
  return { ao, bounce, scrL, neon, fill };
}
