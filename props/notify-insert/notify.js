// Insert: the guy's laptop screen at night — a browser with a search query in the bar, then a desktop notification
// pops in at the top (app icon = mini Ko, sender, text). Skit 3 «Как сын»: the mom's message after the punchline.
// Plug-in contract: ../README.md (props/README.md in the library). Copy to code/inserts/notify.js,
// `import './inserts/notify.js';` under the `// PROPS / INSERTS` marker.
// tools/prep.py: SHOTS row ("S15","INSERT",i1,{"ins":"notify"}); EVENTS row {"type":"notify","start":i1,"pop":i1+0.45}.
// Texts: NOTIFY below (edit text only). SFX: {"t":"notify.pop","src":"ding","db":-20}.
(function () {
  const NOTIFY = {
    query: 'как сварить пельмени, чтобы не слиплись',   // browser search bar (callback to the joke); '' = no browser window
    app: 'Ко', when: 'сейчас',
    from: 'Мама',
    text: 'Ко, скажи ему, пусть шапку наденет',
    capTop: 1640,
  };
  const CSS = `
.kn-in{position:absolute;inset:0;transform-origin:50% 30%;background:radial-gradient(ellipse 90% 60% at 50% 30%,#232a3d 0,#121622 60%,#0a0c12 100%)}
.kn-win{position:absolute;left:60px;right:60px;top:1000px;height:820px;border-radius:26px;background:#1a1e2a;border:2px solid #2b3142;overflow:hidden}
.kn-bar{position:absolute;left:0;right:0;top:0;height:110px;background:#222736}
.kn-dot{position:absolute;top:42px;width:26px;height:26px;border-radius:13px}
.kn-url{position:absolute;left:150px;right:40px;top:24px;height:62px;border-radius:31px;background:#141824;color:#c9cedb;font:400 34px/62px "Segoe UI",Arial,sans-serif;padding-left:70px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.kn-url b{position:absolute;left:26px;top:15px;width:22px;height:22px;border:4px solid #7d8496;border-radius:50%;box-sizing:border-box}
.kn-h{position:absolute;left:60px;right:60px;top:150px;color:#aab3ff;font:600 44px/56px "Segoe UI",Arial,sans-serif}
.kn-line{position:absolute;left:60px;height:30px;border-radius:15px;background:#262b3a}
.kn-toast{position:absolute;left:44px;right:44px;top:560px;height:330px;border-radius:40px;background:rgba(42,47,62,.97);border:2px solid rgba(255,255,255,.12);box-shadow:0 30px 80px rgba(0,0,0,.6),0 0 60px rgba(199,228,75,.18)}
.kn-ico{position:absolute;left:40px;top:70px;width:120px;height:140px;border-radius:24px;background:#C7E44B;border:4px solid #151714;box-shadow:0 0 40px 4px rgba(199,228,75,.35)}
.kn-ico i{position:absolute;top:38px;width:16px;height:38px;border-radius:8px;background:#151714}
.kn-ico i.l{left:26px}.kn-ico i.r{right:26px}
.kn-app{position:absolute;left:196px;top:34px;color:#9aa1b2;font:400 32px/40px "Segoe UI",Arial,sans-serif}
.kn-when{position:absolute;right:44px;top:34px;color:#9aa1b2;font:400 32px/40px "Segoe UI",Arial,sans-serif}
.kn-from{position:absolute;left:196px;top:86px;color:#fff;font:700 60px/70px "Segoe UI",Arial,sans-serif}
.kn-text{position:absolute;left:196px;right:40px;top:164px;color:#e8ebf2;font:400 52px/62px "Segoe UI",Arial,sans-serif}`;
  let R;
  window.KO_INSERTS = window.KO_INSERTS || {};
  window.KO_INSERTS.notify = {
    capTop: NOTIFY.capTop,
    init(el) {
      const st = document.createElement('style'); st.textContent = CSS; document.head.appendChild(st);
      const mk = (cls, txt, parent, tag) => { const e = document.createElement(tag || 'div'); e.className = cls; if (txt != null) e.textContent = txt; parent.appendChild(e); return e; };   // createElement only: HTML strings get parsed by the compiler
      el.style.background = '#0a0c12';
      const root = mk('kn-in', null, el); root.setAttribute('data-layout-ignore', '');
      if (NOTIFY.query) {
        const win = mk('kn-win', null, root), bar = mk('kn-bar', null, win);
        ['#ff5f57', '#febc2e', '#28c840'].forEach((c, k) => { const d = mk('kn-dot', null, bar); d.style.background = c; d.style.left = (30 + k * 38) + 'px'; d.style.opacity = .55; });
        const url = mk('kn-url', NOTIFY.query, bar); mk('', null, url, 'b');
        mk('kn-h', NOTIFY.query[0].toUpperCase() + NOTIFY.query.slice(1), win);
        [[300, 760], [360, 540], [460, 820], [520, 700], [580, 480], [680, 800], [740, 600]].forEach(([y, w]) => { const l = mk('kn-line', null, win); l.style.top = y + 'px'; l.style.width = w + 'px'; });
      }
      const toast = mk('kn-toast', null, root);
      const ico = mk('kn-ico', null, toast); mk('l', null, ico, 'i'); mk('r', null, ico, 'i');
      mk('kn-app', NOTIFY.app, toast); mk('kn-when', NOTIFY.when, toast);
      mk('kn-from', NOTIFY.from, toast); mk('kn-text', NOTIFY.text, toast);
      R = { in: root, toast, eyes: [...ico.querySelectorAll('i')] };
    },
    draw(t, shot, ev, c) {
      R.in.style.transform = `scale(${1 + .04 * c.seg(t, shot.start, shot.end)})`;
      const pop = ev && ev.pop != null ? ev.pop : shot.start + .45;
      const p = c.seg(t, pop, pop + .4);
      R.toast.style.opacity = c.seg(t, pop, pop + .15);
      R.toast.style.transform = `translateY(${(1 - c.backOut(p)) * -180}px)`;
      const bl = ((t - pop) % 2.2 + 2.2) % 2.2;               // mini Ko blinks once ~1 s after the pop, then every 2.2 s
      const k = bl > 1.0 && bl < 1.15 ? .12 : 1;
      R.eyes.forEach(e => e.style.transform = `scaleY(${k})`);
    },
  };
})();
