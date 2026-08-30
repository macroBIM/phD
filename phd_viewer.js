/*
    phd_viewer.js — 논문 뷰어 (macroBIM/phD)
    · 서버의 index_phd.html 은 이 파일 하나만 불러온다. 목차·본문·스타일은 모두 저장소가 갖는다.
      → 원고를 고치거나 레이아웃을 바꿔도 서버 파일은 그대로 둔다.
    · 읽는 순서: toc.json → 각 장의 .md 를 병렬로 → marked 로 조판 → KaTeX 로 수식.
    · 화면은 한 번에 한 장(章). 목차에서 장을 고르면 그 장이 열리고, 절을 고르면 그 절로 간다.
      '전체 보기' 로 아홉 장을 이어서 읽을 수 있고, 인쇄는 언제나 전체를 낸다.
    · 브랜치: ?br=<branch> > window.PHD_BRANCH(부트스트랩이 실제로 찾아낸 것) > main.
      (raw 는 text/plain + nosniff 라 <script src>/<link> 가 막힌다. 그래서 전부 fetch 후 주입한다.)
*/
(function () {
  var params  = new URLSearchParams(location.search);
  var BRANCH  = params.get('br') || window.PHD_BRANCH || 'main';
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
  function cssOnce(href) {                    // 스타일시트는 404·차단 시 onerror 가 뜬다
    return new Promise(function (res, rej) {
      var l = el('link', { rel: 'stylesheet', href: href });
      l.onload = res; l.onerror = function () { rej(new Error('css fail: ' + href)); };
      head(l);
    });
  }
  function first(urls, load) {                // 앞의 것이 실패하면 다음 것으로
    return urls.reduce(function (p, u) {
      return p.catch(function () { return load(u); });
    }, Promise.reject(new Error('empty')));
  }

  /* ── 바깥 자원 ─────────────────────────────────────────────────────────
     한 CDN 이 막힌 망(사내망·학교망·차단 확장)에서도 수식이 살아 있도록
     jsdelivr → cdnjs 순으로 시도한다. 경로 규칙이 서로 다르므로 둘 다 적는다. */
  var LIB = {
    marked: ['https://cdn.jsdelivr.net/npm/marked@12.0.2/marked.min.js',
             CDN + 'marked/12.0.2/marked.min.js'],
    katex:  ['https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js',
             CDN + 'KaTeX/0.16.9/katex.min.js'],
    auto:   ['https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js',
             CDN + 'KaTeX/0.16.9/contrib/auto-render.min.js'],
    css:    ['https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css',
             CDN + 'KaTeX/0.16.9/katex.min.css']
  };
  var mathNote = null, mdNote = null;         // 자원이 안 붙었을 때 화면에 띄울 사유

  //  marked 가 없으면 제목만이라도 살려 조판한다 — 목차와 장 넘김이 계속 동작하도록.
  function toHtml(md) {
    if (window.marked) return marked.parse(md);
    return md.split('\n').map(function (l) {
      var e = l.replace(/&/g, '&amp;').replace(/</g, '&lt;');
      var m;
      if ((m = e.match(/^###\s+(.*)/)))  return '<h3>' + m[1] + '</h3>';
      if ((m = e.match(/^##\s+(.*)/)))   return '<h2>' + m[1] + '</h2>';
      if ((m = e.match(/^#\s+(.*)/)))    return '<h1>' + m[1] + '</h1>';
      return e.trim() ? '<p>' + e + '</p>' : '';
    }).join('\n');
  }
  css('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');

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
  function chapterOf(id) {                       // sec-4-3 → ch-4
    var m = String(id).match(/^sec-(\d+)-/);
    return m ? 'ch-' + m[1] : id;
  }

  //  수식 자원이 다 실패해도 본문은 나와야 한다 — 사유만 적어두고 계속 간다.
  var mathReady = Promise.all([
    first(LIB.css, cssOnce).catch(function () { mathNote = 'KaTeX 스타일시트'; }),
    first(LIB.katex, script).then(function () { return first(LIB.auto, script); })
      .catch(function () { mathNote = 'KaTeX 스크립트'; })
  ]);

  Promise.all([
    first(LIB.marked, script).catch(function () { mdNote = 'marked(마크다운 조판기)'; }),
    mathReady,
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
    var box  = [];
    var md   = bodies.map(function (b) { return protect(b, box); }).join('\n\n');
    var html = restore(toHtml(md), box);

    var paper = el('div', { class: 'paper' });
    var cover = el('header', { class: 'cover' },
      '<h1>' + (meta.title || '') + '</h1>' +
      (meta.subtitle ? '<div class="sub">' + meta.subtitle + '</div>' : '') +
      '<div class="by">' + [meta.author, meta.updated ? '최종 수정 ' + meta.updated : '']
        .filter(Boolean).join(' · ') + '</div>' +
      (meta.note ? '<div class="note">' + meta.note + '</div>' : ''));
    var body = el('div', { class: 'body' }); body.innerHTML = html;
    paper.appendChild(cover); paper.appendChild(body);
    doc.innerHTML = ''; doc.appendChild(paper);

    if (!window.renderMathInElement) mathNote = mathNote || 'KaTeX 스크립트';
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

    /* ── 수식이 실제로 조판됐는지 확인 ──
       스크립트만 붙고 CSS 가 빠지면 KaTeX 는 HTML·MathML 두 층을 겹쳐 그려서
       글자가 깨진 것처럼 보인다. 폰트가 KaTeX 것인지로 그 상태를 잡아낸다. */
    var probe = body.querySelector('.katex .mord, .katex');
    if (probe && !/katex/i.test(getComputedStyle(probe).fontFamily || '')) mathNote = 'KaTeX 스타일시트';
    if (mathNote || mdNote) {
      var 증상 = mathNote === 'KaTeX 스타일시트'
        ? '수식이 글자가 겹친 모양으로 깨져 보입니다'          // 스크립트만 붙어 두 층이 겹친 상태
        : '수식이 $…$ 원문 그대로 보입니다';
      paper.insertBefore(el('div', { class: 'warn' },
        '<b>' + [mdNote, mathNote].filter(Boolean).join(', ') + '</b> 를 불러오지 못해 ' + 증상 + '. ' +
        (mdNote ? '표와 강조도 빠지고 제목·문단만 보입니다. ' : '') +
        '망에서 cdn.jsdelivr.net · cdnjs.cloudflare.com 이 막혀 있는지 확인해 주세요. ' +
        '본문 내용 자체는 모두 읽으실 수 있습니다.'), paper.firstChild);
    }

    /* ── 장별로 묶는다: h1 이 나올 때마다 새 <section> 을 열고 다음 h1 전까지 담는다 ── */
    var nodes = Array.prototype.slice.call(body.childNodes), secs = [], cur = null;
    nodes.forEach(function (n) {
      if (n.nodeType === 1 && n.tagName === 'H1') {
        cur = el('section', { class: 'chap' });
        cur.setAttribute('data-ch', anchorOf(n.textContent));
        secs.push(cur); body.appendChild(cur);
      }
      if (cur) cur.appendChild(n);
    });

    /* ── 목차: 본문 헤딩에서 만든다(장 상태만 toc.json 에서 가져온다) ── */
    var statusOf = {};
    chapters.forEach(function (c) { statusOf[anchorOf(c.title)] = c.status || ''; });

    var nav = el('nav'), links = [];
    secs.forEach(function (sec) {
      Array.prototype.forEach.call(sec.querySelectorAll('h1, h2'), function (h) {
        var id = anchorOf(h.textContent); h.id = id;
        var isCh = h.tagName === 'H1';
        var a = el('a', { href: '#' + id, class: isCh ? 'ch' : 'sec' },
          '<span>' + h.textContent + '</span>' +
          (isCh && statusOf[id] ? '<span class="st">' + statusOf[id] + '</span>' : ''));
        nav.appendChild(a); links.push({ a: a, h: h, id: id, sec: sec });
      });
    });

    /* ── 장 이동 ── */
    var all = false, active = secs.length ? secs[0].getAttribute('data-ch') : null;

    function show(id, scrollTo) {
      var chId = chapterOf(id);
      if (secs.some(function (s) { return s.getAttribute('data-ch') === chId; })) active = chId;
      secs.forEach(function (s) { s.hidden = !all && s.getAttribute('data-ch') !== active; });
      cover.hidden = !all && !!active && active !== secs[0].getAttribute('data-ch') ? true : false;
      document.body.classList.remove('toc-open');
      var t = scrollTo && document.getElementById(scrollTo);
      if (t && !t.closest('.chap[hidden]')) t.scrollIntoView({ block: 'start' });
      else window.scrollTo(0, 0);
      spy();
    }

    nav.addEventListener('click', function (e) {
      var a = e.target.closest && e.target.closest('a'); if (!a) return;
      e.preventDefault();
      var id = a.getAttribute('href').slice(1);
      if (history.replaceState) history.replaceState(null, '', '#' + id); else location.hash = id;
      show(id, id);
    });
    window.addEventListener('hashchange', function () {
      var id = location.hash.slice(1); if (id) show(id, id);
    });

    /* ── 장 끝의 이전/다음 ── */
    secs.forEach(function (sec, i) {
      var pager = el('div', { class: 'pager' });
      function btn(j, label) {
        if (j < 0 || j >= secs.length) return el('span', {});
        var id = secs[j].getAttribute('data-ch');
        var t  = secs[j].querySelector('h1').textContent;
        var b  = el('button', { type: 'button' }, label + ' ' + t);
        b.onclick = function () {
          if (history.replaceState) history.replaceState(null, '', '#' + id);
          show(id, null);
        };
        return b;
      }
      pager.appendChild(btn(i - 1, '←')); pager.appendChild(btn(i + 1, '→'));
      sec.appendChild(pager);
    });

    /* ── 사이드바 머리·발 ── */
    toc.innerHTML = '';
    toc.appendChild(el('div', { class: 'toc-head' },
      '<div class="toc-title">' + (meta.title || '논문') + '</div>' +
      '<div class="toc-sub">' + (meta.subtitle || '목차') + '</div>' +
      '<div class="toc-meta"><span class="pill">' + chapters.length + '개 장</span>' +
      (meta.updated ? '<span class="pill">' + meta.updated + '</span>' : '') +
      (BRANCH !== 'main' ? '<span class="pill branch">br: ' + BRANCH + '</span>' : '') + '</div>'));
    toc.appendChild(nav);
    var foot = el('div', { class: 'toc-foot' });
    var bAll = el('button', { type: 'button', class: 'ghost' }, '전체 보기');
    bAll.onclick = function () {
      all = !all; bAll.textContent = all ? '한 장씩 보기' : '전체 보기';
      bAll.classList.toggle('on', all);
      show(active, all ? null : active);
    };
    var bPrint = el('button', { type: 'button' }, '인쇄 / PDF');
    bPrint.onclick = function () { window.print(); };
    foot.appendChild(bAll); foot.appendChild(bPrint); toc.appendChild(foot);

    /* ── 스크롤에 따라 현재 절 표시(보이는 장 안에서만) ── */
    var ticking = false;
    function spy() {
      var vis = links.filter(function (l) { return !l.sec.hidden; });
      if (!vis.length) { ticking = false; return; }
      var cur2 = vis[0], y = window.scrollY + 90;
      vis.forEach(function (l) { if (l.h.getBoundingClientRect().top + window.scrollY <= y) cur2 = l; });
      links.forEach(function (l) { l.a.classList.toggle('active', l === cur2); });
      if (cur2.a.offsetTop < nav.scrollTop) nav.scrollTop = cur2.a.offsetTop - 40;
      else if (cur2.a.offsetTop > nav.scrollTop + nav.clientHeight - 60)
        nav.scrollTop = cur2.a.offsetTop - nav.clientHeight + 80;
      ticking = false;
    }
    window.addEventListener('scroll', function () {
      if (!ticking) { ticking = true; requestAnimationFrame(spy); }
    });

    show(location.hash.slice(1) || active, location.hash.slice(1) || null);
  }
})();
