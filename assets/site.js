/* ============================================================================
   Hermes Agent 课程站 · 交互层  v2
   一份脚本，四类页面通用：枢纽页、学习路径页、步骤详情页、文档镜像页。
   纯原生 JS，无模块、无外部依赖；file:// 双击直开也能用（不使用 fetch）。
   ========================================================================== */
(function () {
  'use strict';

  /* ------------------------------------------------ 站点根路径（相对自适应） */
  var SELF = document.currentScript;
  if (!SELF) {
    var all = document.querySelectorAll('script[src]');
    for (var i = all.length - 1; i >= 0; i--) {
      if (/assets\/site\.js(\?|$)/.test(all[i].getAttribute('src') || '')) { SELF = all[i]; break; }
    }
  }
  var ROOT = SELF ? String(SELF.src).replace(/assets\/site\.js.*$/, '') : '';
  var IDX = window.COURSE_INDEX || null;

  function abs(u) { return ROOT + String(u || '').replace(/^\//, ''); }
  function $(s, r) { return (r || document).querySelector(s); }
  function $$(s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); }
  function ls(key, fallback) {
    try { var v = localStorage.getItem(key); return v == null ? fallback : v; }
    catch (e) { return fallback; }
  }
  function lsSet(key, val) { try { localStorage.setItem(key, val); } catch (e) {} }

  /* ------------------------------------------------------------------ 主题 */
  var THEME_KEY = 'hg-theme';
  function applyTheme(t) {
    if (t === 'light') { document.documentElement.setAttribute('data-theme', 'light'); }
    else { document.documentElement.removeAttribute('data-theme'); }
    var btn = $('[data-theme-toggle]');
    if (btn) {
      btn.setAttribute('aria-label', t === 'light' ? '切换到深色主题' : '切换到浅色主题');
      btn.title = t === 'light' ? '深色' : '浅色';
      var g = $('.tg', btn);
      if (g) { g.textContent = t === 'light' ? '◐' : '◑'; }
    }
  }
  function initTheme() {
    applyTheme(ls(THEME_KEY, 'dark'));
    $$('[data-theme-toggle]').forEach(function (b) {
      b.addEventListener('click', function () {
        var next = ls(THEME_KEY, 'dark') === 'light' ? 'dark' : 'light';
        lsSet(THEME_KEY, next);
        applyTheme(next);
      });
    });
  }

  /* ---------------------------------------------------------------- 进度存储 */
  var PKEY = 'hg-progress-v1';
  var store = {};
  try { store = JSON.parse(ls(PKEY, '{}')) || {}; } catch (e) { store = {}; }
  function doneOf(id) {
    var a = store[id];
    if (!a) { return []; }
    if (Object.prototype.toString.call(a) !== '[object Array]') { return []; }
    return a.map(Number).filter(function (n) { return !isNaN(n); });
  }
  function save() { lsSet(PKEY, JSON.stringify(store)); }
  function toggle(id, i) {
    var a = doneOf(id), p = a.indexOf(i);
    if (p === -1) { a.push(i); } else { a.splice(p, 1); }
    store[id] = a;
    save();
    paint();
  }
  function stepTotal(id) {
    if (!IDX) { return 0; }
    for (var i = 0; i < IDX.steps.length; i++) { if (IDX.steps[i].id === id) { return IDX.steps[i].total || 0; } }
    return 0;
  }
  function countsFor(id) {
    var total = stepTotal(id), done = 0;
    if (total) {
      done = doneOf(id).filter(function (i) { return i >= 0 && i < total; }).length;
    } else {
      var box = $('.checklist[data-step="' + id + '"]');
      total = box ? $$('.check', box).length : 0;
      done = Math.min(doneOf(id).length, total);
    }
    return { done: done, total: total };
  }
  function isStepDone(id) { var c = countsFor(id); return c.total > 0 && c.done >= c.total; }
  function totals() {
    var ids = IDX ? IDX.steps.map(function (s) { return s.id; }) : Object.keys(store);
    var done = 0, total = 0;
    ids.forEach(function (id) { var c = countsFor(id); done += c.done; total += c.total; });
    return { done: done, total: total, stepsDone: ids.filter(isStepDone).length, steps: ids.length };
  }

  /* 把进度画到当前页上所有相关组件 */
  function paint() {
    var t = totals();

    /* 1) 当前页的验收清单 */
    $$('.checklist').forEach(function (box) {
      var id = box.getAttribute('data-step') || '';
      var items = $$('.check', box);
      var done = 0;
      items.forEach(function (b) {
        var i = Number(b.getAttribute('data-i'));
        var on = doneOf(id).indexOf(i) !== -1;
        b.setAttribute('aria-pressed', on ? 'true' : 'false');
        if (on) { done++; }
      });
      var cnt = $('.cnt', box);
      if (cnt) { cnt.textContent = done + ' / ' + items.length; }
      box.classList.toggle('done', items.length > 0 && done === items.length);
    });

    /* 2) 顶栏分段进度 */
    $$('.tprog').forEach(function (w) {
      var segs = $$('.seg i', w);
      if (IDX) {
        IDX.steps.forEach(function (s, k) {
          if (segs[k]) { segs[k].classList.toggle('on', isStepDone(s.id)); }
        });
      }
      var b = $('b', w);
      if (b) { b.textContent = t.stepsDone + '/' + t.steps; }
      w.setAttribute('title', '已完成 ' + t.stepsDone + ' / ' + t.steps + ' 个阶段，共勾选 ' +
        t.done + ' / ' + t.total + ' 个验收项');
    });

    /* 3) 左栏六步导航 + 枢纽页右侧竖排 */
    $$('.rail li, .hs-list li').forEach(function (li) {
      var id = li.getAttribute('data-step') || '';
      li.setAttribute('data-state', isStepDone(id) ? 'done' : '');
    });
    $$('.hero-side .chip').forEach(function (el) {
      el.textContent = t.done + ' / ' + t.total + ' 项';
    });
    $$('.railbar').forEach(function (w) {
      var b = $('b', w), bar = $('.bar i', w);
      var c = w.getAttribute('data-step') ? countsFor(w.getAttribute('data-step')) : t;
      if (b) { b.textContent = c.done + '/' + c.total; }
      if (bar) { bar.style.width = (c.total ? (c.done / c.total * 100) : 0) + '%'; }
    });

    /* 4) 学习路径页：进度环 + 步骤卡 */
    $$('.ring').forEach(function (r) {
      var c = r.querySelector('.bar'), lbl = $('.lbl b', r), st = $('.lbl span', r);
      var pct = t.total ? (t.done / t.total) : 0;
      if (c) {
        var len = c.getTotalLength ? c.getTotalLength() : (2 * Math.PI * 64);
        c.style.strokeDasharray = len;
        c.style.strokeDashoffset = len * (1 - pct);
      }
      if (lbl) { lbl.textContent = Math.round(pct * 100) + '%'; }
      if (st) { st.textContent = t.done + ' / ' + t.total + ' 项'; }
    });
    $$('.stepcard').forEach(function (card) {
      var id = card.getAttribute('data-step') || '';
      var c = countsFor(id);
      var pct = c.total ? (c.done / c.total * 100) : 0;
      card.setAttribute('data-state', (c.total && c.done === c.total) ? 'done' : '');
      var bar = $('.bar i', card); if (bar) { bar.style.width = pct + '%'; }
      var d = $('.ft .done', card);
      if (d) { d.textContent = c.done === c.total && c.total ? '✓ 已全部验收' : (c.done ? '✓ ' + c.done + '/' + c.total : '未开始'); }
    });
    $$('[data-total-count]').forEach(function (el) { el.textContent = t.done; });
  }

  function initChecklist() {
    $$('.checklist').forEach(function (box) {
      var id = box.getAttribute('data-step') || '';
      $$('.check', box).forEach(function (b) {
        b.addEventListener('click', function () { toggle(id, Number(b.getAttribute('data-i'))); });
      });
      var r = $('.reset', box);
      if (r) {
        r.addEventListener('click', function () {
          store[id] = []; save(); paint();
          r.textContent = '已重置';
          setTimeout(function () { r.textContent = '重置本步'; }, 1400);
        });
      }
    });
  }

  /* -------------------------------------------------------------- 代码块复制 */
  function copyBtn(text) {
    var b = document.createElement('button');
    b.type = 'button'; b.className = 'copy'; b.textContent = '复制';
    b.addEventListener('click', function () {
      var done = function () {
        b.textContent = '已复制'; b.classList.add('ok');
        setTimeout(function () { b.textContent = '复制'; b.classList.remove('ok'); }, 1500);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, function () { legacy(); });
      } else { legacy(); }
      function legacy() {
        try {
          var ta = document.createElement('textarea');
          ta.value = text; ta.style.position = 'fixed'; ta.style.top = '-1000px';
          document.body.appendChild(ta); ta.select();
          document.execCommand('copy'); document.body.removeChild(ta); done();
        } catch (e) { b.textContent = '复制失败'; }
      }
    });
    return b;
  }
  function initCopy() {
    /* 步骤页的代码块：头部已有容器 */
    $$('.codeblock').forEach(function (cb) {
      var head = $('.cb-head', cb), pre = $('pre', cb);
      if (!head || !pre || $('.copy', head)) { return; }
      var sp = document.createElement('span'); sp.className = 'spacer';
      head.appendChild(sp);
      head.appendChild(copyBtn(pre.innerText));
    });
    /* 文档镜像页的 Pygments 代码块：自己撑一个头部 */
    $$('.doccontent .highlight').forEach(function (hl) {
      var pre = $('pre', hl);
      if (!pre || $('.docs-cb-head', hl.parentNode)) { return; }
      var head = document.createElement('div');
      head.className = 'cb-head docs-cb-head';
      var lang = document.createElement('span'); lang.className = 'lang'; lang.textContent = 'code';
      var cap = document.createElement('span'); cap.className = 'cap';
      var prev = hl.previousElementSibling;
      cap.textContent = (prev && prev.classList && prev.classList.contains('codetitle'))
        ? prev.textContent : '';
      var sp = document.createElement('span'); sp.className = 'spacer';
      head.appendChild(lang); head.appendChild(cap); head.appendChild(sp);
      head.appendChild(copyBtn(pre.innerText));
      hl.style.borderTopLeftRadius = hl.style.borderTopRightRadius = '0';
      hl.parentNode.insertBefore(head, hl);
      head.style.cssText += ';border:1px solid var(--code-line);border-bottom:0;' +
        'border-radius:var(--radius) var(--radius) 0 0;background:var(--code-bg);' +
        'display:flex;align-items:center;gap:10px;padding:8px 12px 8px 14px;' +
        'font-family:var(--mono);font-size:.72rem;color:var(--muted)';
    });
  }

  /* ------------------------------------------------------ 目录高亮 / 阅读进度 */
  function initToc() {
    var links = $$('.railtoc a, .doctoc a');
    if (!links.length) { return; }
    var map = {};
    links.forEach(function (a) {
      var id = (a.getAttribute('href') || '').replace(/^#/, '');
      if (id) { map[id] = a; }
    });
    var targets = Object.keys(map)
      .map(function (id) { return document.getElementById(id); })
      .filter(Boolean);
    if (!targets.length) { return; }
    function mark(el) {
      links.forEach(function (a) { a.classList.remove('on'); });
      var a = map[el.id];
      if (a) {
        a.classList.add('on');
        var box = a.closest ? a.closest('.railtoc, .doctoc') : null;
        if (box && a.offsetTop > box.scrollTop + box.clientHeight - 60) {
          box.scrollTop = a.offsetTop - box.clientHeight + 80;
        }
      }
    }
    if ('IntersectionObserver' in window) {
      var seen = [];
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (en.isIntersecting) {
            seen = seen.filter(function (x) { return x !== en.target; });
            seen.push(en.target);
          } else { seen = seen.filter(function (x) { return x !== en.target; }); }
        });
        if (seen.length) {
          seen.sort(function (a, b) { return a.getBoundingClientRect().top - b.getBoundingClientRect().top; });
          mark(seen[0]);
        }
      }, { rootMargin: '-90px 0px -68% 0px', threshold: [0, 1] });
      targets.forEach(function (t) { io.observe(t); });
    }
  }
  function initReadbar() {
    var bar = $('.readbar');
    if (!bar) { return; }
    function upd() {
      var h = document.documentElement.scrollHeight - window.innerHeight;
      var p = h > 0 ? Math.min(1, Math.max(0, window.pageYOffset / h)) : 0;
      bar.style.width = (p * 100).toFixed(2) + '%';
    }
    window.addEventListener('scroll', upd, { passive: true });
    window.addEventListener('resize', upd);
    upd();
  }

  /* ------------------------------------------------------------- 命令面板 */
  function initPalette() {
    if (!IDX) { return; }
    var host = document.createElement('div');
    host.className = 'palette'; host.setAttribute('role', 'dialog');
    host.setAttribute('aria-modal', 'true'); host.setAttribute('aria-label', '搜索课程内容');
    host.innerHTML =
      '<div class="veil" data-close="1"></div>' +
      '<div class="box">' +
      '  <div class="ptop"><span class="ic">&gt;</span>' +
      '    <input type="text" placeholder="搜索阶段、小节、关键词…" aria-label="搜索" autocomplete="off" spellcheck="false">' +
      '    <span class="kbd">ESC</span></div>' +
      '  <div class="plist" role="listbox"></div>' +
      '  <div class="pfoot"><span>↑↓ 选择</span><span>Enter 打开</span>' +
      '    <span class="spacer" style="margin-left:auto"></span><span>' +
      IDX.steps.length + ' 个阶段 · ' +
      IDX.steps.reduce(function (n, s) { return n + (s.sections ? s.sections.length : 0); }, 0) +
      ' 个小节</span></div>' +
      '</div>';
    document.body.appendChild(host);

    var input = $('input', host), list = $('.plist', host);
    var items = [], sel = 0;

    function build() {
      items = [];
      IDX.steps.forEach(function (s) {
        items.push({ t: s.num + '. ' + s.title, s: s.titleEn || '', u: s.url, k: '阶段', n: String(s.num) });
        (s.sections || []).forEach(function (sec) {
          items.push({ t: sec.h, s: s.title, u: s.url + '#' + sec.id, k: '小节', n: s.num + '.' });
        });
      });
    }
    function render(q) {
      q = (q || '').trim().toLowerCase();
      var hit = items.filter(function (it) {
        if (!q) { return true; }
        return (it.t + ' ' + it.s + ' ' + it.k).toLowerCase().indexOf(q) !== -1;
      }).slice(0, 60);
      sel = 0;
      list.innerHTML = '';
      if (!hit.length) {
        list.innerHTML = '<div class="empty">没有匹配的内容。试试「安装」「模型」「工具」。</div>';
        return;
      }
      hit.forEach(function (it, i) {
        var a = document.createElement('a');
        a.className = 'pitem'; a.href = abs(it.u);
        a.setAttribute('role', 'option');
        a.setAttribute('aria-selected', i === 0 ? 'true' : 'false');
        a.innerHTML = '<span class="no"></span><span class="tx"></span><span class="knd"></span>';
        $('.no', a).textContent = it.n;
        $('.tx', a).textContent = it.t;
        $('.knd', a).textContent = it.k;
        a.addEventListener('mouseenter', function () { pick(i); });
        list.appendChild(a);
      });
      items.hit = hit;
    }
    function pick(i) {
      sel = i;
      $$('.pitem', list).forEach(function (a, k) {
        a.setAttribute('aria-selected', k === i ? 'true' : 'false');
      });
    }
    build();   /* 先把索引建好，否则面板永远是空的 */
    function open() {
      host.setAttribute('data-open', '1');
      input.value = ''; render('');
      setTimeout(function () { input.focus(); }, 20);
    }
    function close() { host.setAttribute('data-open', '0'); }
    function isOpen() { return host.getAttribute('data-open') === '1'; }

    input.addEventListener('input', function () { render(input.value); });
    host.addEventListener('click', function (e) {
      if (e.target.getAttribute && e.target.getAttribute('data-close')) { close(); }
    });
    document.addEventListener('keydown', function (e) {
      var k = e.key;
      if ((e.ctrlKey || e.metaKey) && (k === 'k' || k === 'K')) { e.preventDefault(); isOpen() ? close() : open(); return; }
      if (k === 'Escape' && isOpen()) { close(); return; }
      if (!isOpen()) {
        if (k === '/' && !/^(INPUT|TEXTAREA)$/.test(document.activeElement.tagName)) { e.preventDefault(); open(); }
        return;
      }
      var hit = items.hit || [];
      if (k === 'ArrowDown') { e.preventDefault(); if (hit.length) { pick((sel + 1) % hit.length); } }
      else if (k === 'ArrowUp') { e.preventDefault(); if (hit.length) { pick((sel - 1 + hit.length) % hit.length); } }
      else if (k === 'Enter') {
        if (hit[sel]) { e.preventDefault(); window.location.href = abs(hit[sel].u); }
      }
    });

    $$('[data-palette-open]').forEach(function (b) {
      b.addEventListener('click', function (e) { e.preventDefault(); open(); });
    });
  }

  /* -------------------------------------------- 文档镜像页：补齐顶栏与脚本 */
  function enhanceDocPages() {
    var bar = $('.topbar');
    if (!bar) { return; }
    if (!$('.topnav', bar)) {
      var nav = document.createElement('nav');
      nav.className = 'topnav';
      nav.setAttribute('aria-label', '站点导航');
      nav.innerHTML =
        '<a href="' + abs('index.html') + '">首页</a>' +
        '<a href="' + abs('path.html') + '">学习路径</a>' +
        '<a href="' + abs('docs/index.html') + '">文档目录</a>';
      var anchor = $('.langtag', bar);
      if (anchor) { bar.insertBefore(nav, anchor); } else { bar.appendChild(nav); }
    }
    if (!$('.tprog', bar) && IDX) {
      var w = document.createElement('span');
      w.className = 'tprog';
      w.innerHTML = '<span class="seg">' + IDX.steps.map(function () { return '<i></i>'; }).join('') +
        '</span><span>已完成 <b>0/6</b></span>';
      var lt = $('.langtag', bar);
      if (lt) { bar.insertBefore(w, lt); } else { bar.appendChild(w); }
    }
    if (!$('[data-palette-open]', bar)) {
      var b2 = document.createElement('button');
      b2.type = 'button'; b2.className = 'btn iconbtn';
      b2.setAttribute('data-palette-open', '1');
      b2.title = '搜索课程（Ctrl/⌘ + K）';
      b2.setAttribute('aria-label', '搜索课程');
      b2.innerHTML = '<span aria-hidden="true">⌕</span>';
      bar.appendChild(b2);
    }
  }
  function initPaletteTrigger() {
    if ($('[data-palette-open]')) { return; }
    var bar = $('.topbar');
    if (!bar || !IDX) { return; }
    var b = document.createElement('button');
    b.type = 'button'; b.className = 'btn iconbtn';
    b.setAttribute('data-palette-open', '1');
    b.title = '搜索课程（Ctrl/⌘ + K）';
    b.setAttribute('aria-label', '搜索课程');
    b.innerHTML = '<span aria-hidden="true">⌕</span>';
    bar.appendChild(b);
  }
  function initThemeToggleMount() {
    if ($('[data-theme-toggle]')) { return; }
    var bar = $('.topbar');
    if (!bar) { return; }
    var b = document.createElement('button');
    b.type = 'button'; b.className = 'btn iconbtn';
    b.setAttribute('data-theme-toggle', '1');
    b.innerHTML = '<span class="tg" aria-hidden="true">◑</span>';
    bar.appendChild(b);
  }

  /* --------------------------------------------- 浏览量（不蒜子计数器 2.3）--
     数据来源：向 busuanzi.ibruce.info 发一次 JSONP（只在 http/https 下请求）。
     · 按域名汇总：site_pv / site_uv 是整个 fuk-wang.github.io 的累计值（与同域名的
       lmapi 站共享），page_pv 才是当前页面自己的浏览量。
     · 断网或 file:// 直接打开时：不请求、不显示，页面其余功能不受影响——
       统计行默认隐藏，只有计数返回后才由 busuanzi 摘掉内层的 display:none。
     · 想撤掉统计：删掉本函数和 boot() 里的 initPv() 调用即可，不动任何 HTML。   */
  function initPv() {
    if (!/^https?:$/.test(location.protocol)) { return; }
    var foot = $('.sitefoot .in');
    var docfoot = $('.docfoot');
    if (!foot && !docfoot) { return; }

    /* 计数回来（busuanzi 把内层容器设成 inline）时，再把外层统计行露出来 */
    function reveal(outer, inner) {
      if (!outer || !inner) { return; }
      var mo = new MutationObserver(function () {
        if (inner.style.display !== 'none' && inner.style.display !== '') {
          outer.style.display = ''; mo.disconnect();
        }
      });
      mo.observe(inner, { attributes: true, childList: true, subtree: true });
      setTimeout(function () { mo.disconnect(); }, 20000);
    }

    if (foot) {
      var fw = document.createElement('span');
      fw.className = 'pvline mono';
      fw.style.display = 'none';
      fw.title = '不蒜子计数：site_pv / site_uv 按域名 fuk-wang.github.io 汇总，与同域名的 lmapi 站共享';
      fw.innerHTML =
        '<span id="busuanzi_container_page_pv" style="display:none">本页 <b id="busuanzi_value_page_pv">–</b> 次</span>' +
        '<span id="busuanzi_container_site_pv" style="display:none">全站累计 <b id="busuanzi_value_site_pv">–</b> 次 / <b id="busuanzi_value_site_uv">–</b> 人</span>';
      foot.appendChild(fw);
      reveal(fw, $('#busuanzi_container_page_pv', fw));
      reveal(fw, $('#busuanzi_container_site_pv', fw));
    }

    if (docfoot) {
      var dw = document.createElement('span');
      dw.className = 'pvline';
      dw.style.display = 'none';
      dw.title = '不蒜子计数：本页浏览量（按 URL 逐页统计）';
      dw.innerHTML = '<span id="busuanzi_container_page_pv" style="display:none">本页浏览 <b id="busuanzi_value_page_pv">–</b> 次</span>';
      docfoot.appendChild(dw);
      reveal(dw, $('#busuanzi_container_page_pv', dw));
    }

    var s = document.createElement('script');
    s.async = true;
    s.defer = true;
    s.src = 'https://busuanzi.ibruce.info/busuanzi/2.3/busuanzi.pure.mini.js';
    s.referrerPolicy = 'no-referrer-when-downgrade';
    document.head.appendChild(s);
  }

  /* ------------------------------------------------------------------- 启动 */
  function boot() {
    enhanceDocPages();
    initThemeToggleMount();
    initPaletteTrigger();
    initTheme();
    initChecklist();
    paint();
    initCopy();
    initToc();
    initReadbar();
    initPalette();
    initPv();
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else { boot(); }
})();
