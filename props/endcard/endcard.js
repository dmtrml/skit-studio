// Prop (overlay): closing end card over the last wide shot — the 3D scene keeps playing, goes soft (CSS blur on the
// canvas) and darker; a title pops in at the top and a CTA box at the bottom. Skit 3 «Как сын», author 10.11.
// Copy to code/props/endcard.js, `import './props/endcard.js';` under the `// PROPS / INSERTS` marker.
// tools/prep.py: EVENTS row {"type":"endcard","start":T,"cta":T+0.5}; make TAIL long enough (≈ 2.5 s after start).
// Texts: END below (edit text only). Uses hooks build + update (props/README.md). Pure function of t.
(function () {
  const END = {
    title: ['ЭТОТ СКЕТЧ', 'ЦЕЛИКОМ СДЕЛАН'], brand: 'В CLAUDE',
    cta: 'НАПИШИ «КО»', cta2: 'В КОММЕНТАХ —', cta3: 'ПОКАЖУ, КАК СДЕЛАТЬ ТАКОЙ',
    blur: 9, dark: .3,          // px of canvas blur and darkening at full strength
  };
  const CSS = `
@font-face{font-family:"KoImpact";src:local("Impact"),local("Impact Regular")}
.ec{position:absolute;inset:0;pointer-events:none;opacity:0;font-family:"KoImpact",Impact,sans-serif;color:#fff;text-align:center}
.ec-t{position:absolute;left:0;right:0;top:300px;transform-origin:50% 50%}
.ec-t div{font-size:96px;line-height:110px;-webkit-text-stroke:6px #0a0a0e;paint-order:stroke fill}
.ec-t .b{font-size:150px;line-height:170px;color:#C7E44B;-webkit-text-stroke:8px #0a0a0e}
.ec-c{position:absolute;left:70px;right:70px;top:1330px;height:370px;border-radius:44px;background:rgba(20,18,34,.85);border:5px solid #C7E44B;box-shadow:0 0 50px rgba(199,228,75,.25);transform-origin:50% 50%}
.ec-c .a{margin-top:30px;font-size:110px;line-height:120px;color:#C7E44B}
.ec-c .m{font-size:70px;line-height:86px}
.ec-c .s{font-size:62px;line-height:80px}`;
  let R;
  window.KO_PROPS = window.KO_PROPS || {};
  window.KO_PROPS.endcard = {
    build(c) {
      const st = document.createElement('style'); st.textContent = CSS; document.head.appendChild(st);
      const mk = (cls, txt, parent) => { const e = document.createElement('div'); e.className = cls; if (txt != null) e.textContent = txt; parent.appendChild(e); return e; };
      const host = document.getElementById('sk-clip');
      const root = mk('ec', null, host); root.setAttribute('data-layout-ignore', '');
      const t = mk('ec-t', null, root); END.title.forEach(s => mk('', s, t)); mk('b', END.brand, t);
      const box = mk('ec-c', null, root); mk('a', END.cta, box); mk('m', END.cta2, box); mk('s', END.cta3, box);
      R = { root, t, box, gl: document.getElementById('gl'), ev: (c.TL.events || []).find(e => e.type === 'endcard') };
    },
    update(t, shot, c) {
      const ev = R.ev;
      if (!ev) return;
      const k = c.seg(t, ev.start, ev.start + .6);
      const s = .5 - .5 * Math.cos(Math.PI * k);
      R.gl.style.filter = s > 0 ? `blur(${(END.blur * s).toFixed(2)}px) brightness(${(1 - END.dark * s).toFixed(3)})` : '';
      R.root.style.opacity = c.seg(t, ev.start + .15, ev.start + .3);
      const p1 = c.seg(t, ev.start + .15, ev.start + .55), cta = ev.cta != null ? ev.cta : ev.start + .5;
      const p2 = c.seg(t, cta, cta + .4);
      R.t.style.transform = `scale(${(.6 + .4 * c.backOut(p1)).toFixed(4)})`;
      R.box.style.opacity = c.seg(t, cta, cta + .12);
      R.box.style.transform = `scale(${(.7 + .3 * c.backOut(p2)).toFixed(4)})`;
    },
  };
})();
