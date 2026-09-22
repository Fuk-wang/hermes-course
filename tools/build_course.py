#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
把 _content/step-*.json（六步教程内容）渲染成赛博风学习站：

  index.html                枢纽页（这是什么 / 主题卡 / 页脚）
  path.html                 学习路径总览（进度环 + 六步卡片）
  steps/<n>-<id>.html       每一步的详情页（讲解 + 代码 + 验收清单 + 常见坑）
  assets/course-index.js    命令面板（Ctrl/⌘+K）用的小节索引
  docs/**/*.html            文档镜像：注入主题引导与站点脚本（幂等，只改一次）

用法：  python tools/build_course.py            # 生成
        python tools/build_course.py --check    # 只做校验，不写文件
"""

import os, re, io, sys, json, html, glob, datetime

HOME = os.path.expanduser("~")
SITE = os.path.join(HOME, "Desktop", "hermes-course-site")
CONTENT = os.path.join(SITE, "_content")
STEPS_OUT = os.path.join(SITE, "steps")
DOCS = os.path.join(SITE, "docs")
ORIGIN = "https://hermes-agent.nousresearch.com"
BUILD = datetime.date.today().isoformat()
CHECK_ONLY = "--check" in sys.argv

SITE_NAME = "Hermes 学习站"
SITE_DESC = ("Hermes Agent 交互式学习路径：六个阶段，每步都有学习目标、可照做的命令、"
             "可勾选的验收清单，以及离线可读的官方文档。")


def esc(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def slug_anchor(step, n):
    return "s%d" % n


# ------------------------------------------------------------------ 读内容
def load_steps():
    steps = []
    for p in sorted(glob.glob(os.path.join(CONTENT, "step-*.json"))):
        with io.open(p, encoding="utf-8") as f:
            d = json.load(f)
        d["_file"] = p
        steps.append(d)
    steps.sort(key=lambda d: int(d.get("num", 99)))
    for d in steps:
        pass
    return steps


# --------------------------------------------------------------- 片段渲染
def r_paras(paras):
    return "".join("<p>%s</p>" % esc(p) for p in (paras or []))


def r_list(items, cls=""):
    if not items:
        return ""
    c = ' class="%s"' % cls if cls else ""
    return "<ul%s>%s</ul>" % (c, "".join("<li>%s</li>" % esc(i) for i in items))


def r_code(blocks):
    out = []
    for b in blocks or []:
        if not b:
            continue
        lang = esc(b.get("lang") or "text")
        cap = esc(b.get("caption") or "")
        body = esc(b.get("text") or "")
        out.append(
            '<div class="codeblock">'
            '<div class="cb-head"><span class="lang">%s</span>'
            '<span class="cap">%s</span></div>'
            '<pre><code>%s</code></pre></div>' % (lang, cap, body))
    return "".join(out)


NOTE_LABEL = {"tip": "提示", "warn": "注意", "info": "说明", "danger": "警告"}


def r_note(n):
    if not n or not n.get("text"):
        return ""
    t = n.get("type") if n.get("type") in NOTE_LABEL else "tip"
    title = n.get("title") or NOTE_LABEL[t]
    return '<div class="note %s"><span class="nt">%s</span><p>%s</p></div>' % (
        esc(t), esc(title), esc(n["text"]))


def r_table(t):
    if not t or not t.get("head"):
        return ""
    head = "".join("<th>%s</th>" % esc(h) for h in t["head"])
    rows = ""
    for row in t.get("rows") or []:
        rows += "<tr>" + "".join("<td>%s</td>" % esc(c) for c in row) + "</tr>"
    return ('<div class="tablewrap"><table><thead><tr>%s</tr></thead>'
            '<tbody>%s</tbody></table></div>' % (head, rows))


def r_prose(step):
    out = []
    n = 0
    why = step.get("why") or []
    if why:
        n += 1
        out.append(
            '<section id="%s"><h2><span class="hno">%02d</span>这一步在解决什么'
            '<a class="anchor" href="#%s" aria-label="本节链接">#</a></h2>%s</section>'
            % (slug_anchor(step, n), n, slug_anchor(step, n), r_paras(why)))
    for sec in step.get("sections") or []:
        n += 1
        aid = slug_anchor(step, n)
        body = r_paras(sec.get("paras"))
        body += r_code(sec.get("code"))
        body += r_list(sec.get("list"))
        body += r_table(sec.get("table"))
        body += r_note(sec.get("note"))
        out.append(
            '<section id="%s"><h2><span class="hno">%02d</span>%s'
            '<a class="anchor" href="#%s" aria-label="本节链接">#</a></h2>%s</section>'
            % (aid, n, esc(sec.get("h") or ""), aid, body))
    return "".join(out), n


def r_checklist(step):
    items = step.get("checklist") or []
    lis = "".join(
        '<li><button class="check" type="button" data-i="%d" aria-pressed="false">'
        '<span class="box" aria-hidden="true">'
        '<svg viewBox="0 0 16 16"><path d="M3 8.6l3.1 3.1L13 4.8" fill="none" '
        'stroke="#04201d" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"/></svg>'
        '</span><span class="tx">%s</span></button></li>' % (i, esc(t))
        for i, t in enumerate(items))
    return (
        '<section id="check" class="checklist" data-step="%s" data-total="%d">'
        '<div class="ch"><h3>验收清单</h3><span class="spacer"></span>'
        '<span class="cnt">0 / %d</span>'
        '<button class="reset" type="button">重置本步</button></div>'
        '<ul>%s</ul>'
        '<p class="allgood">✓ 这一步已全部验收通过</p></section>'
        % (esc(step.get("id")), len(items), len(items), lis))


def r_pitfalls(step):
    items = step.get("pitfalls") or []
    if not items:
        return ""
    blocks = ""
    for i, p in enumerate(items):
        blocks += ('<details><summary><span class="q">%02d</span><span>%s</span>'
                   '<span class="pm" aria-hidden="true">+</span></summary>'
                   '<div class="ans"><p>%s</p></div></details>'
                   % (i + 1, esc(p.get("q")), esc(p.get("a"))))
    return ('<section class="pitfalls" id="pitfalls"><h2 class="ph">常见坑</h2>%s</section>'
            % blocks)


def r_doclinks(step, rel):
    ds = step.get("docs") or []
    if not ds:
        return ""
    lis = ""
    for d in ds:
        href = d.get("href") or ""
        url = d.get("url") or (ORIGIN + "/docs/" + href.replace("docs/", "").replace(".html", ""))
        lis += ('<li><a href="%s%s" target="_self"><span class="ic">›</span>'
                '<span>%s</span><span class="lk">%s</span></a></li>'
                % (rel, esc(href), esc(d.get("label") or href), esc(url.replace(ORIGIN, ""))))
    return ('<div class="doclinks"><h3>官方文档（离线镜像）</h3><ul>%s</ul></div>' % lis)


def r_pager(steps, cur, rel):
    i = [s["id"] for s in steps].index(cur["id"])
    out = ""
    if i > 0:
        p = steps[i - 1]
        out += ('<a class="prev" href="%s">'
                '<span class="k">← 上一步</span><span class="t">%s</span>'
                '<span class="d">%s</span></a>'
                % (esc(p["file"]), esc(p.get("title")), esc(p.get("tagline") or "")))
    if i < len(steps) - 1:
        n = steps[i + 1]
        out += ('<a class="next" href="%s">'
                '<span class="k">下一步 →</span><span class="t">%s</span>'
                '<span class="d">%s</span></a>'
                % (esc(n["file"]), esc(n.get("title")), esc(n.get("tagline") or "")))
    if not out:
        return ""
    return '<nav class="pager" aria-label="步骤导航">%s</nav>' % out


# ------------------------------------------------------------------ 页面骨架
FX = ('<div class="fx" aria-hidden="true"><div class="fx-grid"></div>'
      '<div class="fx-aur a"></div><div class="fx-aur b"></div>'
      '<div class="fx-aur c"></div><div class="fx-scan"></div></div>')

BOOT = ("<script>try{var t=localStorage.getItem('hg-theme');"
        "if(t==='light')document.documentElement.setAttribute('data-theme','light');}catch(e){}</script>")


def head(title, desc, rel):
    return (
        '<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<title>%s</title>\n'
        '<meta name="description" content="%s">\n'
        '<meta name="theme-color" content="#05070c">\n'
        '%s\n'
        '<link rel="icon" href="%sassets/favicon.svg" type="image/svg+xml">\n'
        '<link rel="stylesheet" href="%sassets/style.css">\n'
        '</head>\n<body>\n' % (esc(title), esc(desc), BOOT, rel, rel))


def tail(rel):
    return (
        '\n<script src="%sassets/course-index.js"></script>\n'
        '<script src="%sassets/site.js" defer></script>\n</body>\n</html>\n' % (rel, rel))


def topbar(rel, current, steps, tprog=True):
    segs = "".join("<i></i>" for _ in steps)
    prog = ('<span class="tprog"><span class="seg">%s</span>'
            '<span>已完成 <b>0/%d</b></span></span>' % (segs, len(steps))) if tprog else ""
    nav = ('<nav class="topnav" aria-label="站点导航">'
           '<a href="%sindex.html"%s>首页</a>'
           '<a href="%spath.html"%s>学习路径</a>'
           '<a href="%sdocs/index.html">文档目录</a></nav>'
           % (rel, ' aria-current="page"' if current == "index" else "",
              rel, ' aria-current="page"' if current == "path" else "", rel))
    return (
        '<header class="topbar">\n'
        '  <a class="brand" href="%sindex.html"><span class="mark" aria-hidden="true"></span>%s</a>\n'
        '  <span class="crumb">%s</span>\n'
        '  <span class="spacer"></span>\n'
        '  %s\n  %s\n'
        '  <button class="btn iconbtn" type="button" data-palette-open="1" '
        'title="搜索课程（Ctrl/⌘ + K）" aria-label="搜索课程"><span aria-hidden="true">⌕</span></button>\n'
        '  <button class="btn iconbtn" type="button" data-theme-toggle="1" '
        'aria-label="切换主题"><span class="tg" aria-hidden="true">◑</span></button>\n'
        '</header>\n' % (rel, SITE_NAME, current, nav, prog))


def foot(rel, extra=""):
    return (
        '<footer class="sitefoot"><div class="in">\n'
        '  <span>%s · 离线自包含静态站</span>\n'
        '  <span class="mono">构建 %s</span>\n'
        '  <span class="spacer"></span>\n'
        '  <a href="%sindex.html">首页</a>\n'
        '  <a href="%spath.html">学习路径</a>\n'
        '  <a href="%sdocs/index.html">文档目录</a>\n'
        '  <span class="mono">Ctrl/⌘ + K 搜索</span>\n'
        '</div>%s</footer>\n' % (SITE_NAME, BUILD, rel, rel, rel, extra))


def hero_side(steps):
    """枢纽页英雄区右侧：六个阶段的纵向进度条（跟着本机勾选状态点亮）。"""
    rows = ""
    for i, s in enumerate(steps, 1):
        rows += ('<li data-step="%s"><span class="hex">%02d</span>'
                 '<span class="t">%s</span>'
                 '<span class="tick" aria-hidden="true">✓</span></li>'
                 % (esc(s["id"]), i, esc(s.get("title") or "")))
    n_items = sum(len(s.get("checklist") or []) for s in steps)
    return (
        '<aside class="hero-side" aria-label="六个阶段进度">\n'
        '  <div class="hs-head"><span class="eyebrow">Path 01</span>'
        '<span class="chip cyan">0 / %d 项</span></div>\n'
        '  <ol class="hs-list">%s</ol>\n'
        '  <a class="hs-go" href="path.html">展开完整路径 <span aria-hidden="true">→</span></a>\n'
        '</aside>' % (n_items, rows))


# ---------------------------------------------------------------------- 枢纽页
def build_hub(steps):
    rel = ""
    n_items = sum(len(s.get("checklist") or []) for s in steps)
    body = [head("Hermes 学习站 · 从装好到让 Agent 干活", SITE_DESC, rel), FX, topbar(rel, "index", steps)]
    body.append('<main class="wrap">')
    body.append(
        '<section class="hub-hero">\n'
        '  <div class="hero-main">\n'
        '  <span class="kicker">交互式学习路径 · 可勾选验收</span>\n'
        '  <h1>从装好 Hermes，<br>到让它<span class="grad">自己干完一件事</span></h1>\n'
        '  <p class="lede">这里不讲抽象概念。六个阶段，每一段都写清三件事：这一段要做成什么、'
        '具体敲哪些命令、以及<strong>怎么判断自己真的做到了</strong>。每步都附离线可读的官方文档，'
        '断网也能照着走完。</p>\n'
        '  <div class="cta">\n'
        '    <a class="btn btn-primary" href="steps/1-%s.html">开始第一步 <span aria-hidden="true">→</span></a>\n'
        '    <a class="btn" href="path.html">看学习路径总览</a>\n'
        '  </div>\n'
        '  </div>\n'
        '  %s\n'
        '  <div class="statline">\n'
        '    <span>%d 个阶段</span><span>%d 项验收</span>'
        '<span>776 篇离线文档</span><span>已勾选 <b data-total-count>0</b> 项</span>\n'
        '  </div>\n'
        '</section>' % (steps[0]["id"], hero_side(steps), len(steps), n_items))

    first = steps[0]
    body.append(
        '<section class="section">\n'
        '  <div class="section-head"><h2>学习路径</h2>'
        '<p class="headnote">共 %d 个阶段，按顺序走完即可上手</p></div>\n'
        '  <p class="section-sub">路上每一步都有一份可以打勾的验收清单，进度存在你自己的浏览器里，'
        '关闭页面也不会丢。</p>\n'
        '  <div class="topic-grid">\n'
        '    <a class="topic" href="path.html">\n'
        '      <div class="row"><span class="chip cyan">%d 个阶段</span>'
        '<span class="spacer"></span><span class="chip live">已上线</span></div>\n'
        '      <h3>Hermes Agent</h3>\n'
        '      <p class="sub">从一行安装命令到完成一次真实的工具调用</p>\n'
        '      <p>六个阶段依次是：安装、第一次对话、接上模型、命令行用法、配置系统、工具系统。'
        '每个阶段都给出学习目标、能直接复制的命令、常见坑，以及一份「做到什么算过」的验收清单。</p>\n'
        '      <div class="tags"><span class="chip">AI Agent</span><span class="chip">自托管</span>'
        '<span class="chip">CLI</span><span class="chip">Provider 配置</span>'
        '<span class="chip">Tool Calling</span></div>\n'
        '      <span class="go">进入学习路径 <span class="arw" aria-hidden="true">→</span></span>\n'
        '    </a>\n'
        '    <div class="topic soon">\n'
        '      <h3>下一个主题？</h3>\n'
        '      <p>这一站设计成多主题结构：每个主题是独立的一组页面，新增主题不会影响已有的内容。'
        '文档镜像里还有 %s 之外的大量内容，可以单独拆成主题。</p>\n'
        '      <p class="hint">/ 待续</p>\n'
        '    </div>\n'
        '  </div>\n'
        '</section>' % (len(steps), len(steps), SITE_NAME))

    n_items = sum(len(s.get("checklist") or []) for s in steps)
    body.append(
        '<section class="section"><div class="hub-foot">\n'
        '  <div><h4>这个站是什么</h4>'
        '<p>把 Hermes Agent 官方文档读成一条能走完的路：六个阶段的讲解 + 逐条验收清单 + 离线文档镜像。</p>'
        '<p>全部是静态文件，不需要数据库、不需要 Node，断网也能用。快捷键 <code>Ctrl/⌘ + K</code> 可以直接搜索任意小节。</p></div>\n'
        '  <div><h4>内容来源与许可</h4>'
        '<p>内容来源：Hermes Agent 官方文档（Nous Research）· 上游仓库 '
        '<a href="https://github.com/NousResearch/hermes-agent" target="_blank" rel="noopener">NousResearch/hermes-agent</a> · MIT 许可。</p>'
        '<p>文档镜像共 776 篇，本文档快照随站点一起离线分发；讲解文字为课程改写，命令与配置以官方文档为准。</p>'
        '<p>构建日期 %s · %d 个阶段 · %d 项验收。</p></div>\n'
        '</div></section>' % (BUILD, len(steps), n_items))
    body.append('</main>')
    body.append(foot(rel))
    return "".join(body) + tail(rel)


# ------------------------------------------------------------------ 学习路径页
def build_path(steps):
    rel = ""
    n_items = sum(len(s.get("checklist") or []) for s in steps)
    body = [head("学习路径总览 · " + SITE_NAME, SITE_DESC, rel), FX, topbar(rel, "path", steps)]
    body.append('<main class="wrap">')
    body.append(
        '<section class="path-head">\n'
        '  <div>\n'
        '    <span class="eyebrow">Learning Path · 6 Steps</span>\n'
        '    <h1>Hermes Agent 六个阶段</h1>\n'
        '    <p class="lede">按顺序走完这六步：装好它 → 说上话 → 接上模型 → 用顺命令行 → 理清配置 → '
        '让它调用工具真的干活。每一步都能单独打开，读完打勾，进度自动保存。</p>\n'
        '    <div class="meta"><span class="chip cyan">6 个阶段</span>'
        '<span class="chip">%d 项验收</span><span class="chip">776 篇离线文档</span>'
        '<span class="chip indigo">Ctrl/⌘ + K 搜索</span></div>\n'
        '  </div>\n'
        '  <div class="ring" role="img" aria-label="总体完成进度">\n'
        '    <svg width="148" height="148" viewBox="0 0 148 148">\n'
        '      <circle class="track" cx="74" cy="74" r="64"></circle>\n'
        '      <circle class="bar" cx="74" cy="74" r="64"></circle>\n'
        '    </svg>\n'
        '    <span class="lbl"><b>0%%</b><span>0 / %d 项</span></span>\n'
        '  </div>\n'
        '</section>' % (n_items, n_items))

    lis = ""
    for i, s in enumerate(steps, 1):
        n = len(s.get("checklist") or [])
        lis += (
            '<li><a class="stepcard" data-step="%s" href="steps/%s">\n'
            '  <span class="hd"><span class="hex">%02d</span>'
            '<span class="no">STEP %02d</span><span class="spacer"></span>'
            '<span class="chip">%d 项验收</span></span>\n'
            '  <h3>%s</h3>\n  <p class="en">%s</p>\n'
            '  <p>%s</p>\n'
            '  <span class="bar"><i></i></span>\n'
            '  <span class="ft"><span class="done">未开始</span>'
            '<span>%s</span></span>\n'
            '</a></li>'
            % (esc(s["id"]), esc(s["file"]), i, i, n,
               esc(s.get("title")), esc(s.get("titleEn") or ""),
               esc(s.get("tagline") or s.get("scenario") or ""),
               esc(s.get("titleEn") or "")))
    body.append('<ol class="steps-grid">%s</ol>' % lis)
    body.append(
        '<div class="path-note"><span class="ic">i</span><span>'
        '验收清单不是考试题，而是「怎么确认自己没走错」。每条都能在终端里当场验证：'
        '看到预期的输出就打勾。全勾完再进下一步，后面出问题时你会知道是哪一层的事。'
        '</span></div>')
    body.append('</main>')
    body.append(foot(rel))
    return "".join(body) + tail(rel)


# -------------------------------------------------------------------- 步骤页
def build_step(steps, step):
    rel = "../"
    prose, nsec = r_prose(step)
    anchors = []
    anchors.append(("s1", "这一步在解决什么"))
    k = 1
    for sec in step.get("sections") or []:
        k += 1
        anchors.append(("s%d" % k, sec.get("h") or ""))
    anchors.append(("check", "验收清单"))
    if step.get("pitfalls"):
        anchors.append(("pitfalls", "常见坑"))
    toc = "".join('<li><a href="#%s">%s</a></li>' % (a, esc(t)) for a, t in anchors if t)

    rail = ""
    for i, s in enumerate(steps, 1):
        cur = ' aria-current="page"' if s["id"] == step["id"] else ""
        rail += ('<li data-step="%s"><a href="%s"%s><span class="n">%02d</span>'
                 '<span>%s</span><span class="tick" aria-hidden="true">✓</span></a></li>'
                 % (esc(s["id"]), esc(s["file"]), cur, i, esc(s.get("title"))))

    goals = "".join("<li>%s</li>" % esc(g) for g in (step.get("goals") or []))
    n_chk = len(step.get("checklist") or [])

    body = [head("%s · %s" % (step.get("title"), SITE_NAME),
                 step.get("tagline") or SITE_DESC, rel), FX,
            topbar(rel, "", steps)]
    body.append('<div class="readbar" aria-hidden="true"></div>')
    body.append('<div class="stepwrap">')

    body.append(
        '<aside class="rail"><h2>六个阶段</h2><ol>%s</ol>'
        '<div class="railbar" data-step="%s"><span class="k">本步验收 <b>0/%d</b></span>'
        '<span class="bar"><i></i></span></div></aside>' % (rail, esc(step["id"]), n_chk))

    body.append('<main class="stepmain">')
    body.append(
        '<header class="stephead">\n'
        '  <div class="tags"><span class="chip cyan">STEP %02d / %02d</span>'
        '<span class="chip">%s</span><span class="chip">%d 项验收</span></div>\n'
        '  <h1>%s</h1>\n  <p class="en">%s</p>\n'
        '  <p class="tagline">%s</p>\n  <p class="scenario">%s</p>\n'
        '</header>'
        % (int(step.get("num", 0)), len(steps), esc(step.get("titleEn") or ""), n_chk,
           esc(step.get("title")), esc(step.get("titleEn") or ""),
           esc(step.get("tagline") or ""), esc(step.get("scenario") or "")))

    body.append(
        '<div class="blocks">\n'
        '  <div class="panel"><h3><span class="ic">◆</span>学习目标</h3><ul class="goals">%s</ul></div>\n'
        '  %s\n'
        '</div>' % (goals, r_doclinks(step, rel)))

    body.append('<article class="prose">%s</article>' % prose)
    body.append(r_checklist(step))
    body.append(r_pitfalls(step))
    body.append(r_pager(steps, step, ""))
    body.append('</main>')

    body.append('<aside class="railtoc"><h2>本页内容</h2><ol>%s</ol></aside>' % toc)
    body.append('</div>')
    body.append(foot(rel))
    return "".join(body) + tail(rel)


# ------------------------------------------------------- 命令面板索引（内嵌 JS）
def build_index_js(steps):
    data = {"version": 1, "built": BUILD, "steps": []}
    for s in steps:
        secs = [{"id": "s1", "h": "这一步在解决什么"}]
        for i, sec in enumerate(s.get("sections") or [], 2):
            secs.append({"id": "s%d" % i, "h": sec.get("h") or ""})
        secs.append({"id": "check", "h": "验收清单"})
        if s.get("pitfalls"):
            secs.append({"id": "pitfalls", "h": "常见坑"})
        data["steps"].append({
            "id": s["id"], "num": int(s.get("num", 0)),
            "title": s.get("title"), "titleEn": s.get("titleEn"),
            "tagline": s.get("tagline"), "url": "steps/" + s["file"],
            "total": len(s.get("checklist") or []), "sections": secs,
        })
    js = ("/* 由 tools/build_course.py 生成，请勿手改 */\n"
          "window.COURSE_INDEX = " +
          json.dumps(data, ensure_ascii=False, indent=1) + ";\n")
    return js


FAVICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
<stop offset="0" stop-color="#3fe0cf"/><stop offset="0.55" stop-color="#7d8cff"/>
<stop offset="1" stop-color="#b06cff"/></linearGradient></defs>
<rect width="64" height="64" rx="15" fill="#05070c"/>
<path d="M32 9l19 11v22L32 53 13 42V20z" fill="none" stroke="url(#g)" stroke-width="3.4" stroke-linejoin="round"/>
<path d="M24 25v14M40 25v14M24 32h16" stroke="url(#g)" stroke-width="3.4" stroke-linecap="round"/>
</svg>
"""


# --------------------------------------------------- 文档镜像：注入脚本（幂等）
def retrofit_docs(steps):
    changed, skipped = 0, 0
    for dp, _, files in os.walk(DOCS):
        for f in files:
            if not f.endswith(".html"):
                continue
            p = os.path.join(dp, f)
            with io.open(p, encoding="utf-8") as fh:
                s = fh.read()
            if "assets/site.js" in s:
                skipped += 1
                continue
            m = re.search(r'href="([^"]*?)assets/style\.css"', s)
            if not m:
                skipped += 1
                continue
            rel = m.group(1)                      # 例如 ../../../ 或 ""（根级）
            head_ins = BOOT + "\n"
            if BOOT not in s:
                s = s.replace('<link rel="stylesheet" href="%sassets/style.css">' % rel,
                              '<link rel="stylesheet" href="%sassets/style.css">\n%s' % (rel, head_ins), 1)
            tail_ins = ('<script src="%sassets/course-index.js"></script>\n'
                        '<script src="%sassets/site.js" defer></script>\n' % (rel, rel))
            if "</body>" in s:
                s = s.replace("</body>", tail_ins + "</body>", 1)
            else:
                s = s + tail_ins
            if not CHECK_ONLY:
                with io.open(p, "w", encoding="utf-8") as fh:
                    fh.write(s)
            changed += 1
    return changed, skipped


# ------------------------------------------------------------------ 校验
def verify(steps):
    problems = []
    for s in steps:
        for field in ("id", "num", "title", "tagline"):
            if not s.get(field):
                problems.append("%s 缺字段 %s" % (s.get("_file"), field))
        if len(s.get("sections") or []) < 4:
            problems.append("%s sections 只有 %d 节" % (s["id"], len(s.get("sections") or [])))
        if len(s.get("checklist") or []) < 3:
            problems.append("%s checklist 只有 %d 条" % (s["id"], len(s.get("checklist") or [])))
        for d in s.get("docs") or []:
            href = d.get("href") or ""
            if not os.path.isfile(os.path.join(SITE, href)):
                problems.append("%s 文档链接不存在：%s" % (s["id"], href))
    return problems


def main():
    steps = load_steps()
    if not steps:
        print("!! _content/ 里没有 step-*.json")
        return 1
    for i, s in enumerate(steps, 1):
        s["file"] = "%d-%s.html" % (int(s.get("num", i)), s["id"])

    probs = verify(steps)
    print("== 内容校验 ==")
    for s in steps:
        print("  step-%s  %s  小节 %d  目标 %d  坑 %d  验收 %d  文档 %d"
              % (s.get("num"), s.get("id"), len(s.get("sections") or []),
                 len(s.get("goals") or []), len(s.get("pitfalls") or []),
                 len(s.get("checklist") or []), len(s.get("docs") or [])))
    if probs:
        print("  问题 %d 条：" % len(probs))
        for p in probs:
            print("   -", p)
    else:
        print("  结构无问题；文档链接全部存在")

    if CHECK_ONLY:
        return 1 if probs else 0

    if not os.path.isdir(STEPS_OUT):
        os.makedirs(STEPS_OUT)
    io.open(os.path.join(SITE, "index.html"), "w", encoding="utf-8").write(build_hub(steps))
    io.open(os.path.join(SITE, "path.html"), "w", encoding="utf-8").write(build_path(steps))
    for s in steps:
        io.open(os.path.join(STEPS_OUT, s["file"]), "w", encoding="utf-8").write(build_step(steps, s))
    io.open(os.path.join(SITE, "assets", "course-index.js"), "w", encoding="utf-8").write(build_index_js(steps))
    io.open(os.path.join(SITE, "assets", "favicon.svg"), "w", encoding="utf-8").write(FAVICON)

    # 写完后自检：三个根页面与搜索索引里引用的 steps/ 文件必须真实存在
    missing = []
    for s in steps:
        p = os.path.join(STEPS_OUT, s["file"])
        if not (os.path.isfile(p) and os.path.getsize(p) > 2000):
            missing.append(p)
    idx_js = io.open(os.path.join(SITE, "assets", "course-index.js"), encoding="utf-8").read()
    for m in re.finditer(r'"url":\s*"([^"]+)"', idx_js):
        if not os.path.isfile(os.path.join(SITE, m.group(1).split("#")[0])):
            missing.append("course-index -> " + m.group(1))
    print("  产物自检：%s" % ("全部存在" if not missing else "缺失 " + "; ".join(missing)))

    changed, skipped = retrofit_docs(steps)
    print("== 输出 ==")
    print("  index.html / path.html / steps/*.html (%d 个) / assets/course-index.js" % len(steps))
    print("  文档镜像注入：改写 %d 篇，跳过 %d 篇" % (changed, skipped))
    return 1 if probs else 0


if __name__ == "__main__":
    sys.exit(main())
