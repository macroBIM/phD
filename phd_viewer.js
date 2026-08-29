/*
    phd_viewer.js — 논문 뷰어 (macroBIM/phD)
    · 서버의 index_phd.html 은 이 파일 하나만 불러온다. 목차·본문·스타일은 모두 저장소가 갖는다.
      → 논문을 고치거나 레이아웃을 바꿔도 서버 파일은 그대로 둔다.
    · 읽는 순서: toc.json → 각 장의 .md 를 병렬로 → marked 로 조판 → KaTeX 로 수식.
    · 브랜치 미리보기: index_phd.html?br=<branch> — 기본값 main.
      (raw 는 text/plain + nosniff 라 <script src>/<link> 가 막힌다. 그래서 전부 fetch 후 주입한다.)
*/
(function () {
  var params  = new URLSearchParams(location.search);
  var BRANCH  = params.get('br') || 'main';
  var RAW     = 'https://raw.githubusercontent.com/macroBIM/phD/' + BRANCH + '/';
  var BUST    = '?v=' + Date.now();
  var CDN     = 'https://cdnjs.cloudflare.com/ajax/libs/';
  var root    = document.getElementById('phd-root') || document.body;

  function el(tag, attrs, html) {
    var n = document.createElement(tag);
    for (var k in attrs) n.setAttribute(k, attrs[k]);
    if (html != null) n.innerHTML = html;
    return n;
  }
  function head(node) { document.head.appendChild(node); }
  function css(href)  { head(el('link', { rel: 'stylesheet', href: href })); }
  function text(url)  {
    return fetch(url).then(function (r) {
      if (!r.ok) throw new Error(url.split('/').pop().split('?')[0] + ' HTTP ' + r.status);
      return r.text();
    });
  }
  function script(src) {
    return new Promise(function (res, rej) {
      var s = document.createElement('script');
      s.src = src; s.onload = res; s.onerror = function () { rej(new Error('load fail: ' + src)); };
      head(s);
    });
  }

  /* ── 바깥 자원: 폰트, KaTeX(CSS+JS), marked ── */
  css('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');
  css(CDN + 'KaTeX/0.16.9/katex.min.css');

  /* ── 뼈대 DOM ── */
  //  부르는 쪽(index_phd.html)이 로딩 문구에 준 인라인 스타일이 본문으로 새지 않게 지운다.
  root.innerHTML = ''; root.removeAttribute('style'); root.removeAttribute('class');
  var burger = el('button', { id: 'phd-burger', type: 'button' }, '☰ 목차');
  var toc    = el('aside', { id: 'phd-toc' });
  var doc    = el('main',  { id: 'phd-doc' }, '<div class="paper"><div class="boot">논문을 불러오는 중…</div></div>');
  root.appendChild(burger); root.appendChild(toc); root.appendChild(doc);
  burger.onclick = function () { document.body.classList.toggle('toc-open'); };

  function fail(msg) {
    doc.querySelector('.paper').innerHTML =
      '<div class="err"><b>불러오지 못했습니다.</b><br>' + msg +
      '<br><br>브랜치 <code>' + BRANCH + '</code> 에 해당 파일이 있는지 확인하세요.</div>';
  }

  /* ── 수식 보호: marked 가 $…$ 안의 _ 나 \ 를 건드리지 못하게 잠시 빼둔다 ── */
  function protect(src, box) {
    function keep(m) { box.push(m); return '@@PHDMATH' + (box.length - 1) + '@@'; }
    return src
      .replace(/```[\s\S]*?```/g, keep)          // 코드블록 먼저
      .replace(/\$\$[\s\S]+?\$\$/g, keep)        // 디스플레이 수식
      .replace(/\$(?!\s)[^$\n]+?\$/g, keep);     // 인라인 수식
  }
  function restore(html, box) {
    return html.replace(/@@PHDMATH(\d+)@@/g, function (_, i) {
      // KaTeX 는 textContent 를 읽으므로, 되돌릴 때 HTML 특수문자를 이스케이프해 둔다.
      return box[+i].replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    });
  }

  /* ── 헤딩 → 앵커 id (번호에서 뽑으므로 목차와 본문이 어긋나지 않는다) ── */
  function anchorOf(t) {
    var ch = t.match(/제\s*(\d+)\s*장/);         if (ch)  return 'ch-' + ch[1];
    var se = t.match(/^\s*(\d+)\.(\d+)/);        if (se)  return 'sec-' + se[1] + '-' + se[2];
    return t.trim().replace(/\s+/g, '-');
  }

  Promise.all([
    script(CDN + 'marked/12.0.2/marked.min.js'),
    script(CDN + 'KaTeX/0.16.9/katex.min.js').then(function () {
      return script(CDN + 'KaTeX/0.16.9/contrib/auto-render.min.js');
    }),
    text(RAW + 'phd_style.css' + BUST).then(function (c) { head(el('style', {}, c)); })
      .catch(function (e) { console.error('[phd] style:', e); }),
    text(RAW + 'toc.json' + BUST).then(JSON.parse)
  ]).then(function (r) {
    var toc_ = r[3], meta = toc_.meta || {}, chapters = toc_.chapters || [];
    document.title = (meta.title || '논문') + ' — macroBIM';
    return Promise.all(chapters.map(function (c) { return text(RAW + c.file + BUST); }))
      .then(function (bodies) { render(meta, chapters, bodies); });
  }).catch(function (e) { fail(e.message); console.error('[phd]', e); });

  function render(meta, chapters, bodies) {
    var box = [];
    var md   = bodies.map(function (b) { return protect(b, box); }).join('\n\n');
    var html = restore(marked.parse(md), box);

    var paper = el('div', { class: 'paper' });
    paper.appendChild(el('header', { class: 'cover' },
      '<h1>' + (meta.title || '') + '</h1>' +
      (meta.subtitle ? '<div class="sub">' + meta.subtitle + '</div>' : '') +
      '<div class="by">' + [meta.author, meta.updated ? '최종 수정 ' + meta.updated : '']
        .filter(Boolean).join(' · ') + '</div>' +
      (meta.note ? '<div class="note">' + meta.note + '</div>' : '')));
    var body = el('div', { class: 'body' }); body.innerHTML = html;
    paper.appendChild(body);
    doc.innerHTML = ''; doc.appendChild(paper);

    if (window.renderMathInElement) {
      renderMathInElement(body, {
        delimiters: [
          { left: '$$', right: '$$', display: true },
          { left: '\\[', right: '\\]', display: true },
          { left: '$', right: '$', display: false },
          { left: '\\(', right: '\\)', display: false }
        ],
        throwOnError: false
      });
    }

    /* ── 목차: 본문 헤딩에서 만든다(장 상태만 toc.json 에서 가져온다) ── */
    var statusOf = {};
    chapters.forEach(function (c) { statusOf[anchorOf(c.title)] = c.status || ''; });

    var nav = el('nav'), heads = body.querySelectorAll('h1, h2'), links = [];
    Array.prototype.forEach.call(heads, function (h) {
      var id = anchorOf(h.textContent); h.id = id;
      var isCh = h.tagName === 'H1';
      var a = el('a', { href: '#' + id, class: isCh ? 'ch' : 'sec' },
        '<span>' + h.textContent + '</span>' +
        (isCh && statusOf[id] ? '<span class="st">' + statusOf[id] + '</span>' : ''));
      a.onclick = function () { document.body.classList.remove('toc-open'); };
      nav.appendChild(a); links.push({ a: a, h: h });
    });

    toc.innerHTML = '';
    toc.appendChild(el('div', { class: 'toc-head' },
      '<div class="toc-title">' + (meta.title || '논문') + '</div>' +
      '<div class="toc-sub">목차</div>' +
      '<div class="toc-meta"><span class="pill">' + chapters.length + '개 장</span>' +
      (meta.updated ? '<span class="pill">' + meta.updated + '</span>' : '') +
      (BRANCH !== 'main' ? '<span class="pill branch">br: ' + BRANCH + '</span>' : '') + '</div>'));
    toc.appendChild(nav);
    var foot = el('div', { class: 'toc-foot' });
    var pr = el('button', { type: 'button' }, '인쇄 / PDF'); pr.onclick = function () { window.print(); };
    var rl = el('button', { type: 'button', class: 'ghost' }, '새로고침');
    rl.onclick = function () { location.reload(); };
    foot.appendChild(pr); foot.appendChild(rl); toc.appendChild(foot);

    /* ── 스크롤에 따라 현재 절 표시 ── */
    var ticking = false;
    function spy() {
      var cur = links[0], y = window.scrollY + 90;
      links.forEach(function (l) { if (l.h.offsetTop <= y) cur = l; });
      links.forEach(function (l) { l.a.classList.toggle('active', l === cur); });
      if (cur && cur.a.offsetTop < nav.scrollTop) nav.scrollTop = cur.a.offsetTop - 40;
      else if (cur && cur.a.offsetTop > nav.scrollTop + nav.clientHeight - 60)
        nav.scrollTop = cur.a.offsetTop - nav.clientHeight + 80;
      ticking = false;
    }
    window.addEventListener('scroll', function () {
      if (!ticking) { ticking = true; requestAnimationFrame(spy); }
    });
    spy();
    if (location.hash) { var t = document.getElementById(location.hash.slice(1)); if (t) t.scrollIntoView(); }
  }
})();
