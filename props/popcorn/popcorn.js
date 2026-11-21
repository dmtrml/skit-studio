// Prop: striped popcorn bucket slides in from the right to Ko (desk level); Ko squashes, hops and turns toward it, lands, leans back.
// Ported from skit 1 (research/styles/ko-skit/code-v3). Plug-in contract: ../README.md. Copy to code/props/popcorn.js, import line under the PROPS / INSERTS marker.
// Needs event in tools/prep.py EVENTS:  {"type":"popcorn","start":T,"slide":0.5,"turn_at":T+0.6,"turn":0.4}
//   start = bucket begins to slide, slide = slide duration (s), turn_at = Ko's turn cue (squash starts 0.15 s later), turn = unused spare.
// All Ko motion below is relative to turn_at: squash +0.15..0.23, hop +0.23..0.53 (turns Ko by -1.0 rad), landing squash +0.53..0.76, lean back +0.71..1.16.
// SFX (cues.src.json sfx): {"t":"popcorn.start","src":"swoosh-quick.mp3","db":-24}, {"t":"popcorn.start+0.36","src":"paper-crumple-quick.mp3","db":-21}.
(function () {
  window.KO_PROPS = window.KO_PROPS || {};
  let POP;
  const ev = c => c.TL.events.find(e => e.type === 'popcorn');
  window.KO_PROPS.popcorn = {
    build(c) {
      const { THREE, obj, CY, SP, scene } = c;
      POP = new THREE.Group(); POP.scale.setScalar(1.6); scene.add(POP);
      const n = 8;
      for (let i = 0; i < n; i++) {
        const g = new THREE.CylinderGeometry(.11, .08, .24, 3, 1, true, i * 2 * Math.PI / n, 2 * Math.PI / n);
        const w = obj(g, i % 2 ? ['#F2EEF6', '#CFC8DC', '#A59CBA', '#FFFFFF'] : ['#D84A4A', '#B03A3A', '#852C2C', '#F08A8A'], 0);
        if (w.userData.mat.side !== undefined) w.userData.mat.side = THREE.DoubleSide;
        w.position.y = .12; POP.add(w);
      }
      const bot = obj(CY(.08, .08, .01, 14), '#B03A3A', 0); bot.position.y = .005; POP.add(bot);
      for (let i = 0; i < 8; i++) { const m = obj(SP(.055), '#FFF1CF', .003); const a = i * 2.4; m.position.set(Math.cos(a) * .06 * (i % 3), .27 + (i % 3) * .035, Math.sin(a) * .06 * (i % 3)); POP.add(m); }
    },
    update(t, shot, c) {                      // bucket position: slide in from x = 3.3 to beside Ko
      const e = ev(c); POP.visible = !!e && t >= e.start;
      if (!e) return;
      const slide = c.backOut(c.seg(t, e.start, e.start + e.slide));
      POP.position.set(3.3 + ((c.KOX + .46) - 3.3) * slide, .75, .22);
    },
    koFx(t, ko, c) {                          // Ko's squash / hop / turn / lean (ko = { sx, sy, by, rotY, rotX }, applied by the base)
      const e = ev(c); if (!e) return;
      const T = e.turn_at, { seg, out3 } = c;
      let sqy = 1, hop = 0;
      if (t >= T + .15 && t < T + .23) sqy = 1 - .12 * seg(t, T + .15, T + .23);
      else if (t >= T + .23 && t < T + .53) { const u = seg(t, T + .23, T + .53); sqy = 1 + .05 * Math.sin(Math.PI * u); hop = .12 * 4 * u * (1 - u); }
      else if (t >= T + .53 && t < T + .76) sqy = 1 - .12 * Math.sin(Math.PI * seg(t, T + .53, T + .76));
      ko.sy *= sqy; ko.sx /= Math.sqrt(sqy); ko.by += hop;
      ko.rotX += -.08 * out3(seg(t, T + .71, T + 1.16));
      ko.rotY += -1.0 * out3(seg(t, T + .23, T + .53));
    },
  };
})();
