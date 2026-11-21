// Prop: phone in the guy's L hand (arm 0 = the hand farther from Ko). Screen normal = hand +Z (palm normal).
// Plug-in contract: see ../README.md. Copy to code/props/phone.js and add `import './props/phone.js';` under the PROPS / INSERTS marker.
// Needs in cues.src.json: gestures show_phone / lower_phone (side "L"), optional look {at:"phone"}.
// Poses: hold_phone (the resting base of arm 0, automatic), show_phone (turn the screen to Ko / camera A), lower_phone (back to the lap).
(function () {
  window.KO_PROPS = window.KO_PROPS || {};
  let PH, PHC, HOLD_PN, SHOW_PN, c0;
  const posesFor = (c) => {
    const { V, KD, handRest } = c;
    return {
      hold_phone: s => ({ p: V(s * .2, .86, .40), fd: V(-s * .35, .12, 1), pn: HOLD_PN.clone(), curl: .1, idx: 0, pole: V(s * .6, -.9, -.2) }),
      show_phone: s => ({ p: V(KD.x * .55, .98, KD.z * .55 + .26), fd: V(KD.x * .15, 1, KD.z * .15), pn: SHOW_PN.clone(), curl: .1, idx: 0, pole: V(s * .6, -.5, .6) }),
      lower_phone: s => ({ p: handRest[0].clone().add(V(-.12, .08, 0)), fd: V(.15, .15, 1), pn: V(0, 1, .1), curl: .1, idx: 0, pole: V(s * .8, -.75, -.5) }),
    };
  };
  let POSES;
  window.KO_PROPS.phone = {
    build(c) {
      const { THREE, V, obj, RB, COMIC, arms, up, CAMS, KD } = c;
      c0 = c;
      // mesh + chat-like screen texture (generic bubbles; edit the canvas drawing for another look)
      PH = new THREE.Group(); arms[0].hand.add(PH); PH.position.set(0, .1, .035); PH.scale.setScalar(1.15);
      PH.add(obj(RB(.075, .155, .009, .012), '#1d1d28', .003));
      const cv = document.createElement('canvas'); cv.width = 132; cv.height = 286; const g = cv.getContext('2d');
      g.fillStyle = '#15141c'; g.fillRect(0, 0, 132, 286); g.fillStyle = '#1c1b27'; g.fillRect(0, 0, 132, 30);
      [[10, 44, 70, 0], [44, 76, 78, 1], [10, 108, 62, 0], [40, 140, 82, 1], [10, 172, 76, 0], [34, 204, 88, 1]].forEach(([x, y, w, k]) => { g.fillStyle = k ? '#C7E44B' : '#3a3850'; g.beginPath(); g.roundRect(x, y, w, 22, 8); g.fill(); });
      g.fillStyle = '#2a2838'; g.beginPath(); g.roundRect(8, 252, 116, 24, 12); g.fill();
      const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace;
      const scrn = new THREE.Mesh(new THREE.PlaneGeometry(.066, .143), new THREE.MeshBasicMaterial({ map: tex, color: new THREE.Color(3.2, 3.2, 3.2), fog: false })); scrn.position.z = .0047; PH.add(scrn);
      if (!COMIC) { const l = new THREE.PointLight(0xBFD4FF, .06, 1.4, 2); l.position.set(0, .05, .3); PH.add(l); }   // screen light on the face
      PHC = []; for (const sx of [-1, 1]) for (const sy of [-1, 1]) for (const sz of [-1, 1]) PHC.push(V(sx * .0375 * 1.15, .1 + sy * .0775 * 1.15, .035 + sz * .0045 * 1.15));
      // palm normal of the hold: as far toward the face as still readable from camera B (<= 62 deg); screen toward Ko/camera A for show_phone
      const p = V(-.2, .86, .40), face = V(0, 1.22, .03).sub(p).normalize(), cm = up.worldToLocal(V(...CAMS.B.p)).sub(p).normalize(), wu = V(0, 1, 0).transformDirection(new THREE.Matrix4().copy(up.matrixWorld).invert());
      let hi = 1; for (let m = 0; m <= 1.0001; m += .02) { const n = face.clone().multiplyScalar(1 - m).addScaledVector(wu, m).normalize(); if (n.dot(cm) >= Math.cos(62 * Math.PI / 180)) { hi = m; break; } }
      HOLD_PN = face.clone().multiplyScalar(1 - hi).addScaledVector(wu, hi).normalize();
      SHOW_PN = (() => { const q = V(KD.x * .55, .98, KD.z * .55 + .26); return KD.clone().add(up.worldToLocal(V(...CAMS.A.p)).sub(q).normalize()).normalize(); })();
      POSES = posesFor(c);
    },
    poses() { return POSES; },
    armBase(i) { return i === 0 ? POSES.hold_phone(-1) : null; },     // arm 0 holds the phone whenever no gesture overrides it
    lookTargets(c) {                                                    // cues look {at:"phone"}
      const { V, qFP, yawTo, up } = c, P = POSES.hold_phone(-1), qh = qFP(P.fd, P.pn);
      return { phone: { yaw: yawTo(up.localToWorld(P.p.clone().add(V(0, .1, .035).applyQuaternion(qh)))), pitch: .1 } };
    },
    handPoints(i) { return i === 0 ? PHC : null; },                     // 8 box corners (hand-local): arm clearance + gesture_frame.mjs framing
    update(t, shot, c) { if (c.keySpot) c.keySpot.intensity *= 1 - .35 * c.lookW(t, 'phone'); },   // key light dims while he looks at the phone
  };
})();
