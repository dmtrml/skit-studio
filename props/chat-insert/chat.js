// Insert: dark dating-app chat. chat1 = the sent bubble pops, the chat scrolls, the reply pops; chat2 = zoom on the reply, a highlighter wipes over one word.
// Plug-in contract: see ../README.md. Copy to code/inserts/chat.js and add `import './inserts/chat.js';` under the PROPS / INSERTS marker.
// Needs: shots {cam:"INSERT", ins:"chat1"|"chat2"} and events chat1 {start, sent, reply}, chat2 {start, mark} in tools/prep.py (SHOTS / EVENTS).
// Edit ONLY CHAT_TEXT for a new skit. The last two bubbles are the sent one (green, "g") and the reply (grey, "h"); the reply's `hl` part gets the highlighter.
(function () {
  const CHAT_TEXT = {
    name: 'Алина', avatar: 'А', status: 'в сети', placeholder: 'Сообщение',
    history: [                                  // earlier bubbles: g = ours (green, right), h = hers (grey, left)
      ['g', 'Привет! Красивое фото у моря', '23:32'],
      ['h', 'Привет) спасибо', '23:33'],
      ['g', 'Это закат? Очень красиво', '23:35'],
      ['h', 'Да, обожаю закаты', '23:36'],
      ['g', 'А что ещё любишь?', '23:38'],
      ['h', 'Закаты и честных людей)', '23:39'],
    ],
    sent: ['Тоже обожаю закаты и честность', '23:41 ✓✓'],
    reply: { before: 'Как здорово ', hl: '—', after: ' честность сейчас такая редкость!', time: '23:41' },
  };
  const CSS = `
.kc-in{position:absolute;left:0;top:0;width:1080px;height:1920px;transform-origin:0 0;font-family:'Segoe UI',Arial,sans-serif}
.kc-head{position:absolute;left:0;top:0;width:1080px;height:190px;background:#1c1b27;z-index:3;box-shadow:0 4px 24px rgba(0,0,0,.5)}
.kc-head svg{position:absolute;left:34px;top:62px}
.kc-head .av{position:absolute;left:120px;top:49px;width:92px;height:92px;border-radius:50%;background:#8062E0;color:#fff;font:700 50px/92px 'Segoe UI',Arial,sans-serif;text-align:center}
.kc-head .nm{position:absolute;left:236px;top:36px;color:#fff;font:700 52px/64px 'Segoe UI',Arial,sans-serif}
.kc-head .on{position:absolute;left:236px;top:102px;color:#8fd9a8;font:400 34px/44px 'Segoe UI',Arial,sans-serif}
.kc-head .on i{display:inline-block;width:18px;height:18px;border-radius:50%;background:#3ddc84;margin-right:12px;vertical-align:1px}
.kc-cin{position:absolute;left:0;top:1740px;width:1080px;height:180px;background:#1c1b27;z-index:3}
.kc-cin .pill{position:absolute;left:36px;top:30px;width:830px;height:110px;border-radius:55px;background:#2a2838;color:#7d7a92;font:400 42px/110px 'Segoe UI',Arial,sans-serif;padding-left:44px}
.kc-cin .snd{position:absolute;left:896px;top:30px;width:110px;height:110px;border-radius:50%;background:#C7E44B}
.kc-msgs{position:absolute;left:0;top:190px;width:1080px;height:1360px;overflow:hidden}
.kc-col{position:absolute;left:0;top:0;width:1080px}
.kc-b{position:relative;max-width:800px;width:fit-content;margin:0 40px 22px;padding:20px 30px 14px;border-radius:38px;font:400 44px/58px 'Segoe UI',Arial,sans-serif;word-break:normal}
.kc-b.g{margin-left:auto;background:#C7E44B;color:#151714;border-bottom-right-radius:10px;transform-origin:100% 100%}
.kc-b.h{background:#2a2838;color:#fff;border-bottom-left-radius:10px;transform-origin:0 100%}
.kc-b small{display:block;text-align:right;font:400 28px/34px 'Segoe UI',Arial,sans-serif;opacity:.6;margin-top:2px}
.kc-b.reply{max-width:560px}
.kc-dash{position:relative;display:inline-block;padding:0 16px;margin:0 2px}
.kc-dash i{position:absolute;left:0;right:0;top:3px;bottom:3px;background:#C7E44B;opacity:.85;border-radius:14px;transform-origin:0 50%;transform:scaleX(0);z-index:0}
.kc-dash b{position:relative;z-index:1;font-weight:700}`;
  const MW = 1360, MPAD = 24;
  const X = CHAT_TEXT;
  // DOM is built with createElement on purpose: HTML tags written as text in a .js file are parsed by the HyperFrames compiler as page DOM.
  const mk = (tag, cls, txt, parent) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; if (parent) parent.appendChild(e); return e; };
  const bubble = (parent, k, text, time) => { const b = mk('div', 'kc-b ' + k, null, parent); b.appendChild(document.createTextNode(text)); mk('small', null, time, b); return b; };
  const build = el => {
    const root = mk('div', 'kc-in', null, el); root.setAttribute('data-layout-ignore', '');
    const col = mk('div', 'kc-col', null, mk('div', 'kc-msgs', null, root)); col.setAttribute('data-layout-ignore', '');
    X.history.forEach(([k, tx, tm]) => bubble(col, k, tx, tm));
    bubble(col, 'g sent', X.sent[0], X.sent[1]);
    const rp = X.reply, rb = mk('div', 'kc-b h reply', null, col);
    rb.appendChild(document.createTextNode(rp.before));
    const dash = mk('span', 'kc-dash', null, rb); mk('i', null, null, dash); mk('b', null, rp.hl, dash);
    rb.appendChild(document.createTextNode(rp.after)); mk('small', null, rp.time, rb);
    const head = mk('div', 'kc-head', null, root), NS = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(NS, 'svg'); svg.setAttribute('width', 44); svg.setAttribute('height', 68); svg.setAttribute('viewBox', '0 0 44 68');
    const path = document.createElementNS(NS, 'path'); [['d', 'M34 6 L8 34 L34 62'], ['fill', 'none'], ['stroke', '#fff'], ['stroke-width', 7], ['stroke-linecap', 'round'], ['stroke-linejoin', 'round']].forEach(([k, v]) => path.setAttribute(k, v));
    svg.appendChild(path); head.appendChild(svg);
    mk('div', 'av', X.avatar, head); mk('div', 'nm', X.name, head);
    const on = mk('div', 'on', null, head); mk('i', null, null, on); on.appendChild(document.createTextNode(X.status));
    const cin = mk('div', 'kc-cin', null, root); mk('div', 'pill', X.placeholder, cin); mk('div', 'snd', null, cin);
  };
  function make(final) {
    let R = null, CH = null;
    return {
      capTop: 1640,                                     // captions sit in the empty strip below the bubbles
      init(el) {
        if (!document.getElementById('kc-css')) { const st = document.createElement('style'); st.id = 'kc-css'; st.textContent = CSS; document.head.appendChild(st); }
        el.style.background = '#121119'; build(el);
        const q = s => el.querySelector(s), col = q('.kc-col'), bub = [...col.querySelectorAll('.kc-b')];
        R = { in: q('.kc-in'), col, bub, m7: bub[bub.length - 2], m8: bub[bub.length - 1], dash: q('.kc-dash'), dashI: q('.kc-dash i'), dashB: q('.kc-dash b'), head: q('.kc-head'), cin: q('.kc-cin') };
      },
      draw(t, shot, ev, c) {
        const { seg, out3, backOut, TL } = c;
        const n = R.bub.length, bot = i => R.bub[i].offsetTop + R.bub[i].offsetHeight, last = R.bub[n - 1];
        if (!CH) CH = { y0: MW - MPAD - bot(n - 3), y1: MW - MPAD - bot(n - 2), y2: MW - MPAD - bot(n - 1),
          cx: last.offsetLeft + last.offsetWidth / 2, cy: last.offsetTop + last.offsetHeight / 2, dashX: R.dash.offsetLeft + last.offsetLeft + R.dash.offsetWidth / 2 };
        const e1 = TL.events.find(e => e.type === 'chat1'), e2 = TL.events.find(e => e.type === 'chat2');
        const sentT = e1 ? e1.sent : 1e9, replyT = e1 ? e1.reply : 1e9, mk = e2 ? e2.mark : 1e9;
        const pop = (el, u0) => { const u = seg(t, u0, u0 + .15); el.style.opacity = t >= u0 ? 1 : 0; el.style.transform = `scale(${t >= u0 ? .9 + .1 * backOut(u) : .9})`; };
        const ty = final ? CH.y2 : CH.y0 + (CH.y1 - CH.y0) * out3(seg(t, sentT, sentT + .25)) + (CH.y2 - CH.y1) * out3(seg(t, replyT, replyT + .25));
        R.col.style.transform = `translateY(${ty}px)`;
        pop(R.m7, final ? -1 : sentT); pop(R.m8, final ? -1 : replyT);
        if (!final) {
          const p = seg(t, shot.start, shot.end); R.in.style.transform = `scale(${1 + .04 * p})`; R.in.style.transformOrigin = '50% 50%';
          R.dashI.style.transform = 'scaleX(0)'; R.dashB.style.color = ''; R.dash.style.transform = '';
        } else {
          const k = 1.3 + .5 * out3(seg(t, shot.start, shot.start + .4)), cx = CH.cx, cy = CH.cy + ty + 190;
          R.in.style.transformOrigin = '0 0'; R.in.style.transform = `translate(${540 - k * cx}px,${890 - k * cy}px) scale(${k})`;
          const dw = seg(t, mk, mk + .25); R.dashI.style.transform = `scaleX(${out3(dw)})`; R.dashB.style.color = dw > .5 ? '#151714' : '';
          R.dash.style.transform = `scale(${1 + .1 * Math.sin(Math.PI * seg(t, mk + .25, mk + .6))})`;
        }
        const op = final ? 1 - seg(t, shot.start, shot.start + .4) : 1; R.head.style.opacity = R.cin.style.opacity = op;
      },
    };
  }
  window.KO_INSERTS = window.KO_INSERTS || {};
  window.KO_INSERTS.chat1 = make(false);
  window.KO_INSERTS.chat2 = make(true);
})();
