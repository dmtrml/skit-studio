// characters.js - parametric characters from a passport (see ../CHARACTERS.md).
//   buildGuy(ctx) -> the human (legs, torso, head, hair, face, sleeves/hands via buildArms(AL))
//   buildKo(ctx)  -> the device character (block with a screen face)
//   applyLook(ctx) -> after look3 upgrade(): skin glow for non-default skin, plaid texture
// Defaults reproduce the original guy and Ko exactly. The rig (poseGuy, arms, gestures, moods, mouth, focus) reads only what is returned here.
import * as THREE from 'three';

export const GUY_DEFAULT = {
  name: 'Guy', kind: 'human', height: 1, build: 'average',
  skin: '#E2B08A', hair: { style: 'messy', color: '#3B2A2E' }, beard: 'none', mustache: 'none', age: 'adult', glasses: 'none', headwear: 'none',
  top: { type: 'hoodie', color: '#4A5F8A', pattern: 'none', color2: '#1c1a1e', under: null, shirt: '#D9D4CA' },   // type: hoodie|tshirt|shirt|sweater|vest_over_shirt (color = vest, shirt = shirt under it)
  bottom: { color: '#2B3248' }, shoes: '#e9e6f2', accent: '#9C98B4', headphones: true,
  face: { brow_color: null, eye_color: '#1a1418', mouth_color: '#5a2a2a', freckles: false, head_size: 1, glasses_color: '#16141c', beard_color: null, headwear_color: '#2a2a38', eye_white: '#F4F0F4', eye_bag: '#B98269' },
};
export const KO_DEFAULT = { name: 'Ko', kind: 'device', body: { shape: 'block', color: '#C7E44B' }, screen_face: true, outline: 1 };

const ORIG = {
  skin: ['#E2B08A', '#C48E69', '#9F6C4C', '#F4D2B4'], top: ['#4A5F8A', '#394A6C', '#2A3752', '#7088B8'],
  lime: ['#C7E44B', '#A9C33A', '#7C9426', '#EAF6B4'], us: ['#9FB937', '#86A02C', '#62781E', '#C7E44B'],
};
const mixHex = (a, b, k) => '#' + new THREE.Color(a).lerp(new THREE.Color(b), k).getHexString();
const same = (a, b) => a.toLowerCase() === b.toLowerCase();
const fabric = h => same(h, ORIG.top[0]) ? ORIG.top.slice() : [h, mixHex(h, '#10101e', .22), mixHex(h, '#10101e', .45), mixHex(h, '#ffffff', .2)];
const skinPal = h => same(h, ORIG.skin[0]) ? ORIG.skin.slice() : [h, mixHex(h, '#3a1408', .19), mixHex(h, '#3a1408', .43), mixHex(h, '#ffffff', .4)];
const merge = (a, b) => { const o = Array.isArray(a) ? a.slice() : { ...a }; for (const k in (b || {})) o[k] = (b[k] && typeof b[k] === 'object' && !Array.isArray(b[k]) && a[k] && typeof a[k] === 'object') ? merge(a[k], b[k]) : b[k]; return o; };
export const withDefaults = (p, d) => merge(d, p || {});

const BUILD = { // torso width, depth, leg x, leg w, shoulder offset past torso, upper/fore radius
  slim: { tw: .54, td: .37, lx: .11, lw: .15, so: .10, ru: .055, rf: .048 },
  average: { tw: .62, td: .40, lx: .12, lw: .16, so: .10, ru: .062, rf: .054 },
  broad: { tw: .74, td: .44, lx: .14, lw: .19, so: .10, ru: .072, rf: .063 },
};
const HAIR = ['none', 'buzz', 'short', 'messy', 'side_part', 'long', 'curly', 'bun', 'curly_bun', 'ponytail', 'cap_covered'];
export const HAIR_STYLES = HAIR;

function plaidTexture(c1, c2) {   // buffalo check: base colour + 2 translucent dark bands (single overlap dark, crossing darkest)
  const cv = document.createElement('canvas'); cv.width = cv.height = 128; const g = cv.getContext('2d');
  g.fillStyle = c1; g.fillRect(0, 0, 128, 128);
  const rgb = [1, 3, 5].map(i => parseInt(c2.slice(i, i + 2), 16)).join(',');
  g.fillStyle = `rgba(${rgb},.7)`; g.fillRect(64, 0, 64, 128); g.fillRect(0, 64, 128, 64);
  for (let i = 0; i < 900; i++) { g.fillStyle = `rgba(${i % 2 ? '255,255,255' : '0,0,0'},.05)`; g.fillRect((i * 37) % 128, (i * 91) % 128, 2, 1); }   // deterministic fuzz
  const t = new THREE.CanvasTexture(cv); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(2, 2); t.colorSpace = THREE.SRGBColorSpace; return t;
}
function ribTexture(rx, ry) {   // knit ribs for beanies
  const cv = document.createElement('canvas'); cv.width = 8; cv.height = 8; const g = cv.getContext('2d');
  g.fillStyle = '#fff'; g.fillRect(0, 0, 8, 8); g.fillStyle = 'rgba(0,0,0,.28)'; g.fillRect(0, 0, 2, 8); g.fillStyle = 'rgba(0,0,0,.1)'; g.fillRect(2, 0, 1, 8);
  const t = new THREE.CanvasTexture(cv); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(rx, ry); t.colorSpace = THREE.SRGBColorSpace; return t;
}

// ctx: { PAL, obj, put, RB, BX, CY, SP, V, I, CU, COMIC, GUY, passport }
export function buildGuy(c) {
  const { PAL, obj, put, RB, BX, CY, SP, V, I, CU, GUY, COMIC } = c;
  const P = withDefaults(c.passport, GUY_DEFAULT), F = P.face, T = P.top, B = BUILD[P.build] || BUILD.average;
  const h = Math.min(1.1, Math.max(.9, P.height)), HY = .72 * (h - 1), Y = y => y - .5;
  const isVest = T.type === 'vest_over_shirt', isOld = P.age === 'old';
  const hairC = isOld ? mixHex(P.hair.color, '#D6D6DA', .8) : P.hair.color, browC = F.brow_color || hairC;   // age old: grey tint on hair, brows, beard, mustache
  PAL.skin = skinPal(P.skin); PAL.hoodie = fabric(isVest ? (T.shirt || '#D9D4CA') : T.color); PAL.hair = hairC; PAL.jeans = P.bottom.color;
  const topMats = [], reg = n => { if (n.userData.mat) topMats.push(n.userData.mat); return n; };
  const isHood = T.type === 'hoodie', isShirt = T.type === 'shirt' || isVest, isTee = T.type === 'tshirt', isSweater = T.type === 'sweater';

  // legs
  [-B.lx, B.lx].forEach(x => {
    put(obj(RB(B.lw, .16, .5, .05), PAL.jeans, I), x, .58, .25, GUY);
    put(obj(RB(B.lw - .02, .5, B.lw - .02, .04), PAL.jeans, I), x, .31, .5, GUY);
    put(obj(RB(B.lw, .08, .26, .035), P.shoes, .004), x, .05, .58, GUY);
  });
  const TW = .3;   // torso twist toward the laptop
  const up = new THREE.Group(); up.position.set(0, .5, 0); up.rotation.x = .22; up.rotation.y = TW; GUY.add(up);
  // torso
  reg(put(obj(RB(B.tw, .72 * h, B.td, .1), PAL.hoodie, I), 0, Y(.74 + .36 * h), 0, up));
  if (isHood) {
    reg(put(obj(RB(.44 * B.tw / .62, .2, .22, .07), PAL.hoodie, I), 0, Y(1.5 + HY), -.2 * B.td / .4, up));   // hood lump
    put(obj(RB(.36 * B.tw / .62, .1, .04, .02), PAL.hoodie[1], .003), 0, Y(.93 + .36 * (h - 1)), B.td / 2, up);   // pocket
    [-.08, .08].forEach(x => put(obj(RB(.025, .17, .025, .01), P.accent, .002), x, Y(1.28 + .58 * (h - 1)), B.td / 2 + .005, up));   // drawstrings
  }
  if (isSweater) {
    put(obj(RB(B.tw + .012, .07, B.td + .012, .03), PAL.hoodie[1], .004), 0, Y(.775), 0, up);          // hem band
    put(obj(CY(.105, .11, .05, 14), PAL.hoodie[1], .004), 0, Y(1.485 + HY), .02, up);                  // neck rib
  }
  if (isVest) {   // vest over the shirt: two front panels (V gap shows the shirt), shoulder straps
    const vc = fabric(T.color);
    [-1, 1].forEach(s => {
      put(obj(RB(B.tw * .4, .6 * h, .035, .012), vc, .004), s * B.tw * .27, Y(.74 + .31 * h), B.td / 2 + .012, up);
      put(obj(RB(B.tw * .17, .05, B.td + .03, .01), vc, .004), s * B.tw * .31, Y(.74 + .62 * h), 0, up);
    });
  }
  if (isShirt) {
    [-1, 1].forEach(s => { const co = obj(RB(.14, .05, .05, .015), PAL.hoodie[1], .003); co.rotation.z = -s * .55; reg(put(co, s * .075, Y(1.49 + HY), .105 * B.td / .4, up)); });
    if (T.under) put(obj(RB(.2 * B.tw / .62, .6 * h, .02, .008), T.under, .003), 0, Y(.74 + .31 * h), B.td / 2 + .003, up);   // undershirt strip (open shirt)
    else put(obj(RB(.03, .6 * h, .02, .008), PAL.hoodie[1], .003), 0, Y(.74 + .31 * h), B.td / 2 + .003, up);    // button placket
  }
  put(obj(CY(.075, .08, .1, 8), PAL.skin, .003), 0, Y(1.5 + HY), .02, up);                              // neck
  const head = new THREE.Group(); head.position.set(0, Y(1.72 + HY), .03); up.add(head);
  if (F.head_size && F.head_size !== 1) head.scale.setScalar(F.head_size);
  put(obj(RB(.42, .42, .42, .09), PAL.skin, .005), 0, 0, 0, head);
  [-1, 1].forEach(s => put(obj(RB(.04, .1, .07, .02), PAL.skin, .003), s * .225, -.01, 0, head));   // ears
  put(obj(RB(.055, .055, .06, .02), PAL.skin[1], .003), 0, -.04, .22, head);                        // nose
  if (F.freckles) [[-.14, -.04], [-.1, -.065], [-.06, -.045], [-.13, -.085], [.14, -.04], [.1, -.065], [.06, -.045], [.13, -.085]].forEach(([x, y]) => put(obj(BX(.014, .014, .006), PAL.skin[2], 0), x, y, .2115, head));

  // hair
  let hs = P.hair.style; if (!HAIR.includes(hs)) hs = 'messy';
  if (P.headwear !== 'none' && !['none', 'long', 'ponytail'].includes(hs)) hs = 'cap_covered';
  const HC = (geo, x, y, z, r, ink) => { const n = obj(geo, PAL.hair, ink ?? .004); if (r) n.rotation.z = r; return put(n, x, y, z, head); };
  const HC2 = (geo, x, y, z) => put(obj(geo, mixHex(hairC, '#ff9a50', .16), .003), x, y, z, head);
  const cap = () => HC(RB(.45, .12, .45, .05), 0, .19, -.01), back = () => HC(RB(.45, .3, .1, .05), 0, .06, -.2);
  const curls = (ring) => ring.forEach(([x, y, z, r], i) => (i % 3 ? HC : (g, a, b, d) => HC2(g, a, b, d))(SP(r), x, y, z));
  if (hs === 'messy') {
    cap(); back();
    [[-.16, .27, .08, .18], [-.08, .3, .14, .1], [0, .29, .12, -.05], [.09, .3, .1, -.1], [.17, .26, .04, -.25], [-.2, .2, .2, .4], [.2, .22, .18, -.4]]
      .forEach(([x, y, z, r]) => { const tf = obj(RB(.07, .13, .07, .02), PAL.hair, .003); tf.rotation.z = r; put(tf, x, y, z, head); });
  } else if (hs === 'buzz') { HC(RB(.435, .07, .435, .03), 0, .205, -.01); HC(RB(.435, .2, .05, .02), 0, .1, -.2); }
  else if (hs === 'short') { cap(); back(); HC(RB(.44, .05, .06, .02), 0, .15, .2); }
  else if (hs === 'side_part') { cap(); back(); HC(RB(.3, .07, .1, .03), .07, .25, .12, .12); HC(RB(.4, .05, .06, .02), 0, .15, .2); }
  else if (hs === 'long') { cap(); HC(RB(.46, .55, .1, .05), 0, -.1, -.2); [-1, 1].forEach(s => HC(RB(.05, .4, .26, .03), s * .225, .0, -.09)); HC(RB(.44, .05, .06, .02), 0, .15, .2); }
  else if (hs === 'curly' || hs === 'curly_bun') {
    cap(); back();
    curls([[-.16, .26, .06, .075], [-.05, .29, .1, .08], [.07, .29, .08, .075], [.17, .25, .03, .075], [-.2, .2, .17, .06], [.2, .21, .15, .06], [0, .28, -.1, .08], [-.14, .25, -.12, .075], [.14, .25, -.12, .075],
      [-.22, .1, -.1, .07], [.22, .1, -.1, .07], [-.2, .0, -.17, .07], [.2, .0, -.17, .07], [-.1, .06, -.24, .075], [.1, .06, -.24, .075], [0, -.04, -.25, .07]]);
    if (hs === 'curly') curls([[-.225, -.09, -.02, .06], [.225, -.09, -.02, .06], [-.1, .2, .2, .05], [.05, .22, .2, .05]]);
  } else if (hs === 'bun') { cap(); back(); HC(RB(.44, .05, .06, .02), 0, .15, .2); HC(SP(.11), 0, .33, -.12); put(obj(new THREE.TorusGeometry(.085, .012, 6, 16), P.accent, .002), 0, .24, -.1, head).rotation.x = 1.2; }
  else if (hs === 'ponytail') { cap(); back(); HC(RB(.44, .05, .06, .02), 0, .15, .2); const tl = HC(RB(.1, .36, .1, .04), 0, -.05, -.31); tl.rotation.x = -.3; put(obj(CY(.05, .05, .03, 10), P.accent, .002), 0, .1, -.26, head).rotation.x = 1.2; }
  else if (hs === 'cap_covered') { HC(RB(.44, .12, .08, .03), 0, .02, -.2); [-1, 1].forEach(s => HC(BX(.02, .12, .12), s * .222, .06, -.05, 0, 0)); }
  if (hs === 'curly_bun') {
    [[0, .39, -.1, .08], [-.07, .36, -.14, .075], [.07, .36, -.14, .075], [0, .34, -.18, .08], [-.05, .42, -.13, .07], [.06, .41, -.11, .06]].forEach(([x, y, z, r], i) => (i % 2 ? HC2 : HC)(SP(r), x, y, z));
    [[-.215, -.0, .07, .05], [-.225, -.08, .02, .05], [-.23, -.15, -.03, .045], [.215, -.0, .07, .05], [.225, -.08, .02, .05], [.23, -.15, -.03, .045]].forEach(([x, y, z, r]) => HC(SP(r), x, y, z));
    HC(RB(.42, .05, .06, .02), 0, .155, .2);
  }
  // headwear
  const dome = (spec, ky, cy, r, th, ink, rib) => {   // skull-hugging cap of a sphere (open at the bottom, cut just below the brow line)
    const g = new THREE.SphereGeometry(r, COMIC ? 20 : 40, COMIC ? 12 : 24, 0, Math.PI * 2, 0, th); g.scale(1, ky, 1);
    const n = obj(g, spec, ink), m = n.userData.mat; if (rib && m && m.isMeshPhysicalMaterial) { m.map = ribTexture(48, 6); m.roughness = .95; }
    return put(n, 0, cy, -.005, head);
  };
  if (P.headwear === 'cap') { dome(F.headwear_color, .5, .15, .285, Math.PI * .56, .004); put(obj(RB(.32, .025, .2, .01), P.accent, .003), 0, .15, .3, head); }
  else if (P.headwear === 'beanie') {
    const hc = F.headwear_color; dome(hc, .7, .17, .29, Math.PI * .56, .004, true);
    const cuff = put(obj(new THREE.TorusGeometry(.272, .042, 12, 40), mixHex(hc, '#ffffff', .08), .004), 0, .14, -.005, head); cuff.rotation.x = Math.PI / 2;
    const cm = cuff.userData.mat; if (cm && cm.isMeshPhysicalMaterial) cm.map = ribTexture(70, 1);
  }
  else if (P.headwear === 'hood') {
    reg(dome(PAL.hoodie, .6, .17, .3, Math.PI * .6, I)); reg(put(obj(RB(.5, .44, .2, .08), PAL.hoodie, I), 0, -.02, -.22, head));
    [-1, 1].forEach(s => reg(put(obj(RB(.06, .4, .3, .03), PAL.hoodie, I), s * .245, .0, -.07, head)));
  }

  // eyes, brows, mouth
  const gEye = [], gBrow = [], gLid = [];
  [-1, 1].forEach(s => {
    const e = new THREE.Group(); e.position.set(s * .1, .03, .214); head.add(e);
    put(obj(BX(.085, .07, .016), F.eye_white, 0), 0, 0, 0, e);
    const pu = put(obj(BX(.036, .045, .012), F.eye_color, 0), s * .004, -.004, .009, e); gEye.push(pu);
    const lg = new THREE.Group(); lg.position.set(0, .035, .012); e.add(lg);
    put(obj(BX(.095, .07, .014), PAL.skin[1], 0), 0, -.035, 0, lg); gLid.push(lg);
    put(obj(BX(.1, .022, .01), F.eye_bag, 0), s * .0, -.055, .212 - .214, e);   // eye bag patch
    const bg = new THREE.Group(); bg.position.set(s * .1, .115, .216); head.add(bg);
    put(obj(RB(.1, .024, .02, .008), browC, .002), 0, 0, 0, bg); gBrow.push(bg);
  });
  const mz = P.beard === 'full' ? .232 : P.beard === 'stubble' ? .219 : .214;
  const gmouth = put(obj(RB(.1, .04, .02, .012), F.mouth_color, 0), 0, -.12, mz, head);
  // beard, glasses
  const bc = F.beard_color || hairC;
  if (P.beard === 'stubble') put(obj(RB(.43, .15, .43, .07), mixHex(PAL.skin[0], bc, .42), .004), 0, -.135, 0, head);
  else if (P.beard === 'full') { put(obj(RB(.46, .25, .45, .09), bc, .004), 0, -.15, 0, head); put(obj(RB(.14, .035, .03, .012), bc, .003), 0, -.083, .232, head); }
  const MU = { thin: [.13, .018], full: [.17, .034], walrus: [.21, .05] }[P.mustache];
  if (MU) put(obj(RB(MU[0], MU[1], .03, .012), bc, .003), 0, P.mustache === 'walrus' ? -.092 : -.086, .228, head);
  if (P.glasses !== 'none') {
    const gc = F.glasses_color;
    [-1, 1].forEach(s => {
      if (P.glasses === 'round') put(obj(new THREE.TorusGeometry(.062, .009, 8, 26), gc, 0), s * .1, .03, .226, head);
      else { [[0, .05, .13, .01], [0, -.05, .13, .01]].forEach(([x, y, w, t]) => put(obj(BX(w, t, .012), gc, 0), s * .1 + x, .03 + y, .226, head)); [-1, 1].forEach(q => put(obj(BX(.01, .1, .012), gc, 0), s * .1 + q * .065, .03, .226, head)); }
      put(obj(BX(.012, .012, .22), gc, 0), s * .215, .045, .11, head);   // temple
    });
    put(obj(BX(.05, .012, .012), gc, 0), 0, .045, .228, head);   // bridge
  }
  // optional headphones around the neck
  const hp = put(new THREE.Group(), 0, Y(1.46 + HY), .02, up);
  put(obj(RB(.5, .04, .04, .015), '#2a2a38', .003), 0, 0, .14, hp); [-1, 1].forEach(s => put(obj(RB(.09, .12, .1, .03), '#2a2a38', .003), s * .25, -.02, .06, hp));
  hp.visible = P.headphones && CU.headphones !== false;   // cues.src.json "headphones": false removes them

  const SH0 = i => V((i ? 1 : -1) * (B.tw / 2 + B.so), Y(1.3 + .58 * (h - 1)), -.02);
  const R_UP = B.ru, R_FA = B.rf;
  const capsule = (r, len, spec, parent, ink) => put(obj(new THREE.CapsuleGeometry(r, Math.max(.01, len - r), 4, 12), spec, ink), 0, 0, 0, parent);
  // arms: two-bone chains solved every frame in poseGuy(); meshes move by position/quaternion only
  function buildArms(AL) {
    return [0, 1].map(i => {
      const tx = i ? -1 : 1;
      const A = { shoulder: put(obj(SP(R_UP + .008), isTee ? PAL.hoodie : PAL.hoodie, .004), 0, 0, 0, up), upper: capsule(R_UP, AL[i][0], PAL.hoodie, up, .004), fore: capsule(R_FA, AL[i][1], isTee ? PAL.skin : PAL.hoodie, up, .004) };
      reg(A.shoulder); reg(A.upper); if (!isTee) reg(A.fore);
      const hg = new THREE.Group(); up.add(hg); A.hand = hg;
      if (!isTee) put(obj(CY(R_FA + .004, R_FA + .008, .04, 14), PAL.hoodie[1], .004), 0, -.005, 0, hg);   // cuff ring
      put(obj(RB(.09, .075, .05, .022), PAL.skin, .003), 0, .045, 0, hg);   // palm
      A.fing = new THREE.Group(); A.fing.position.set(0, .082, -.004); hg.add(A.fing);
      put(obj(RB(.088, .072, .042, .018), PAL.skin, .003), 0, .036, 0, A.fing);   // 4-finger block
      const th = new THREE.Group(); th.position.set(tx * .05, .03, .004); th.rotation.z = -tx * .55; hg.add(th);
      put(obj(new THREE.CapsuleGeometry(.02, .035, 4, 8), PAL.skin, .003), 0, .035, 0, th);   // thumb
      A.idx = new THREE.Group(); A.idx.position.set(-tx * .022, .1, .004); hg.add(A.idx);
      put(obj(new THREE.CapsuleGeometry(.0185, .075, 4, 8), PAL.skin, .003), 0, .05, 0, A.idx);   // index finger (scale 0 <-> 1)
      A.idx.scale.setScalar(.001); A.idx.visible = false;
      return A;
    });
  }
  const hhs = Math.max(1, F.head_size || 1);
  return { P, up, head, TW, Y, gEye, gBrow, gLid, gmouth, hp, SH0, R_UP, R_FA, buildArms, topMats,
    HEADY: Y(1.72 + HY), TC: V(0, Y(.74 + .36 * h), 0), TH: V(B.tw / 2, .36 * h, B.td / 2), HH: V(.21 * hhs, .21 * hhs, .21 * hhs) };
}

// device character (Ko): rounded block + base plate; returns the two meshes. Mutates PAL.limeC / PAL.usC from the body colour.
export function koColors(passport) {
  const P = withDefaults(passport, KO_DEFAULT), col = P.body.color, d = same(col, ORIG.lime[0]);
  const lime = d ? ORIG.lime.slice() : [col, mixHex(col, '#1c2406', .16), mixHex(col, '#1c2406', .4), mixHex(col, '#ffffff', .62)];
  const us = d ? ORIG.us.slice() : [mixHex(col, '#1c2406', .2), mixHex(col, '#1c2406', .3), mixHex(col, '#1c2406', .5), col];
  let happy = '#B4F010'; if (!d) { const hsl = {}; new THREE.Color(col).getHSL(hsl); happy = '#' + new THREE.Color().setHSL(hsl.h, .9, .5).getHexString(); }
  return { P, lime, us, happy, hex: parseInt(col.slice(1), 16) };
}
const KO_SHAPES = { block: [.56, .08], round: [.56, .2], sharp: [.56, .02], wide: [.68, .1], slim: [.48, .08] };
export function buildKo(c) {
  const { PAL, obj, RB } = c, K = koColors(c.passport), P = K.P, [w, r] = KO_SHAPES[P.body.shape] || KO_SHAPES.block, o = P.outline ?? 1;
  PAL.limeC = K.lime; PAL.usC = K.us;
  const koN = obj(RB(w, .74, .40, r), PAL.limeC, .0070 * o, { inkSoft: .0040 * o, emi: 0x1a2408, rough: .5, clear: .12 }); koN.position.y = .52;
  const usN = obj(RB(.44 * w / .56, .06, .16, .025), PAL.usC, .0070 * o, { inkSoft: .0040 * o, emi: 0x000000, rough: .55 }); usN.position.y = .03;
  return { koN, usN, ...K };
}

// after look3 upgrade(): per-passport material fixes the generic upgrade cannot know
export function applyLook(c) {
  const { scene, PAL, guy, COMIC } = c; if (COMIC) return;
  if (!same(PAL.skin[0], ORIG.skin[0])) scene.traverse(o => { const m = o.isMesh && o.material; if (m && m.isMeshPhysicalMaterial && m.color.getHex() === new THREE.Color(PAL.skin[0]).getHex()) m.emissive.set(PAL.skin[0]).multiplyScalar(.07); });
  const T = guy.P.top;
  if (!same(T.color, ORIG.top[0])) guy.topMats.forEach(m => { m.sheen = .45; m.sheenColor.set(mixHex(T.color, '#ffffff', .25)); m.needsUpdate = true; });   // look3's fabric sheen is blue-white (right for the default hoodie)
  if (T.pattern === 'plaid') { const map = plaidTexture(T.color, T.color2); guy.topMats.forEach(m => { m.map = map; m.color.set(0xffffff); m.emissive.set(T.color).multiplyScalar(.06); m.needsUpdate = true; }); }
}
