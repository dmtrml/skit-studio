// Insert: empty code editor ("1" in the gutter, blinking lime cursor) with a mini Ko in the corner whose eyes blink with the cursor.
// Ported from skit 1 (research/styles/ko-skit/code-v3, shot S14). Plug-in contract: ../README.md.
// Copy to code/inserts/editor.js, `import './inserts/editor.js';` under the `// PROPS / INSERTS` marker. Needs a shot {cam:"INSERT", ins:"editor"} in tools/prep.py SHOTS (no event needed).
// Edit EDITOR below for another first line / colours. The slow zoom runs over the shot (1.00 -> 1.04), blink period 1 s.
(function () {
  const EDITOR = { line: '1', capTop: 700 };       // capTop: caption y during the insert (the corner has the mini Ko, the top has the cursor)
  const CSS = `
.ke-in{position:absolute;inset:0;transform-origin:50% 50%;background:radial-gradient(ellipse 80% 60% at 40% 35%,#2a1f47 0,#150f24 60%,#0d0a16 100%)}
.ke-gutter{position:absolute;left:0;top:0;width:150px;height:100%;background:rgba(255,255,255,.04)}
.ke-ln{position:absolute;left:60px;top:260px;font:400 64px/90px Consolas,'Courier New',monospace;color:#6b6f80}
.ke-cur{position:absolute;left:190px;top:268px;width:34px;height:76px;background:#C7E44B;box-shadow:0 0 34px 6px rgba(199,228,75,.55)}
.ke-mini{position:absolute;right:70px;bottom:90px;width:150px;height:200px;background:#C7E44B;border-radius:28px;border:4px solid #151714;box-shadow:0 0 90px 10px rgba(199,228,75,.3)}
.ke-mini i{position:absolute;top:56px;width:22px;height:54px;background:#151714;border-radius:11px;transform-origin:50% 50%}
.ke-mini i.l{left:36px}.ke-mini i.r{right:36px}`;
  let R;
  window.KO_INSERTS = window.KO_INSERTS || {};
  window.KO_INSERTS.editor = {
    capTop: EDITOR.capTop,
    init(el) {
      const st = document.createElement('style'); st.textContent = CSS; document.head.appendChild(st);
      const mk = (cls, txt, parent, tag) => { const e = document.createElement(tag || 'div'); e.className = cls; if (txt != null) e.textContent = txt; parent.appendChild(e); return e; };   // createElement: HTML tags as text in .js are parsed as page DOM by the compiler
      const root = mk('ke-in', null, el); root.setAttribute('data-layout-ignore', '');
      mk('ke-gutter', null, root); mk('ke-ln', EDITOR.line, root); mk('ke-cur', null, root);
      const mini = mk('ke-mini', null, root); mk('l', null, mini, 'i'); mk('r', null, mini, 'i');
      R = { in: el.querySelector('.ke-in'), cur: el.querySelector('.ke-cur'), eyes: [...el.querySelectorAll('.ke-mini i')] };
    },
    draw(t, shot, ev, c) {
      R.in.style.transform = `scale(${1 + .04 * c.seg(t, shot.start, shot.end)})`;
      const on = ((t - shot.start) % 1) < .5; R.cur.style.opacity = on ? 1 : 0;
      R.eyes.forEach(e => e.style.transform = `scaleY(${on ? 1 : .12})`);
    },
  };
})();
