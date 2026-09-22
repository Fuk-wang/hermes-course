#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
打包阶段：生成站点样式、文档总目录、课程首页（链接本地化）、部署说明，并压缩成 zip。
必须在 build_site.py 跑完全量渲染之后执行。

用法：  python package_site.py
"""

import os, re, sys, json, html, glob, zipfile, datetime, collections

HOME = os.path.expanduser("~")
SITE = os.path.join(HOME, "Desktop", "hermes-course-site")
DOCS_OUT = os.path.join(SITE, "docs")
ASSETS_OUT = os.path.join(SITE, "assets")
COURSE_SRC = os.path.join(HOME, "Desktop", "hermes-agent-course.html")
VERSION = "Hermes Agent v0.21.3 (2026.9.14) · upstream b5251aa4"
ORIGIN = "https://hermes-agent.nousresearch.com"

SRC_OF = {}

LINK_MAP = [
    ("https://hermes-agent.nousresearch.com/docs/getting-started/installation",
     "docs/getting-started/installation.html"),
    ("https://hermes-agent.nousresearch.com/docs/zh-Hans/getting-started/quickstart",
     "docs/zh-Hans/getting-started/quickstart.html"),
    ("https://hermes-agent.nousresearch.com/docs/integrations/providers",
     "docs/integrations/providers.html"),
    ("https://hermes-agent.nousresearch.com/docs/zh-Hans/user-guide/cli",
     "docs/zh-Hans/user-guide/cli.html"),
    ("https://hermes-agent.nousresearch.com/docs/zh-Hans/user-guide/configuration",
     "docs/zh-Hans/user-guide/configuration.html"),
    ("https://hermes-agent.nousresearch.com/docs/zh-Hans/user-guide/features/tools",
     "docs/zh-Hans/user-guide/features/tools.html"),
    ("https://hermes-agent.nousresearch.com/docs/zh-Hans/getting-started/learning-path",
     "docs/zh-Hans/getting-started/learning-path.html"),
]

# ---------------------------------------------------------------- 样式
def build_css():
    from pygments.formatters import HtmlFormatter
    pyg = HtmlFormatter(style="default").get_style_defs(".highlight")
    return CSS_TMPL.replace("/*PYGMENTS*/", pyg)


CSS_TMPL = u"""/* Hermes Agent 课程站 · 统一样式（课程首页 + 文档镜像） */
:root{
  --bg:#f8f8f6; --surface:#fff; --surface-2:#fbfbfa;
  --ink:#191b19; --ink-2:#3f4440; --muted:#767b76;
  --line:#e4e5e1; --line-strong:#d0d2cd;
  --accent:#0e6e68; --accent-ink:#0a4f4a; --accent-soft:#eaf3f1;
  --sans:ui-sans-serif,system-ui,-apple-system,"Segoe UI","Microsoft YaHei","PingFang SC","Hiragino Sans GB","Noto Sans SC",sans-serif;
  --mono:ui-monospace,"SFMono-Regular",Consolas,"Liberation Mono",Menlo,monospace;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);
     font-size:16px;line-height:1.72;-webkit-font-smoothing:antialiased}

/* ---------- 顶部条 ---------- */
.topbar{
  position:sticky;top:0;z-index:20;
  display:flex;align-items:center;gap:14px;
  padding:11px 26px;background:rgba(248,248,246,.92);
  backdrop-filter:saturate(180%) blur(8px);
  border-bottom:1px solid var(--line);
  font-size:.84rem;
}
.topbar .brand{color:var(--accent-ink);text-decoration:none;font-weight:650;white-space:nowrap}
.topbar .brand:hover{text-decoration:underline}
.topbar .crumb{color:var(--muted);font-family:var(--mono);
  font-size:.76rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.topbar .langtag{margin-left:auto;flex:none;color:var(--accent-ink);background:var(--accent-soft);
  border-radius:999px;padding:2px 10px;font-size:.72rem}

/* ---------- 布局 ---------- */
.docwrap{max-width:1180px;margin:0 auto;padding:40px 26px 90px;
  display:grid;grid-template-columns:minmax(0,1fr) 248px;gap:52px;align-items:start}
.docmain{min-width:0}
.doccontent{max-width:760px}
.docfoot{max-width:760px;margin-top:64px;padding-top:18px;border-top:1px solid var(--line);
  font-size:.8rem;color:var(--muted);line-height:1.7}
.docfoot p{margin:0 0 4px}
.docfoot code{font-family:var(--mono);font-size:.92em;color:var(--ink-2)}

/* ---------- 正文排版 ---------- */
.doccontent h1{font-size:clamp(1.6rem,3vw,2.05rem);line-height:1.26;letter-spacing:-.02em;
  font-weight:660;margin:0 0 22px;text-wrap:pretty}
.doccontent h2{font-size:1.28rem;font-weight:650;letter-spacing:-.014em;
  margin:2.4em 0 .7em;padding-bottom:.35em;border-bottom:1px solid var(--line);text-wrap:pretty}
.doccontent h3{font-size:1.08rem;font-weight:650;margin:1.9em 0 .5em;text-wrap:pretty}
.doccontent h4{font-size:.98rem;font-weight:650;color:var(--ink-2);margin:1.6em 0 .4em}
.doccontent p{margin:0 0 1.05em;color:var(--ink-2);text-wrap:pretty}
.doccontent strong{color:var(--ink);font-weight:650}
.doccontent a{color:var(--accent);text-decoration:none;border-bottom:1px solid rgba(14,110,104,.3)}
.doccontent a:hover{color:var(--accent-ink);border-bottom-color:var(--accent-ink)}
.doccontent a:focus-visible{outline:2px solid var(--accent);outline-offset:2px;border-radius:2px}
.doccontent a.ext::after{content:"↗";font-size:.82em;margin-left:2px;opacity:.65}
.doccontent a.enfallback{border-bottom-style:dashed}
.doccontent a.enfallback::after{content:"EN";font-family:var(--mono);font-size:.6em;
  letter-spacing:.04em;color:var(--muted);margin-left:5px;vertical-align:.2em}
.doccontent ul,.doccontent ol{margin:0 0 1.05em;padding-left:1.35em;color:var(--ink-2)}
.doccontent li{margin:.28em 0}
.doccontent li>p{margin:.2em 0}
.doccontent hr{border:0;border-top:1px solid var(--line);margin:2.2em 0}
.doccontent blockquote{margin:0 0 1.1em;padding:2px 0 2px 16px;border-left:3px solid var(--line-strong);
  color:var(--muted)}
.doccontent blockquote p:last-child{margin-bottom:0}
.doccontent img{max-width:100%;height:auto;border:1px solid var(--line);border-radius:10px;
  margin:.4em 0 1.2em;background:#fff}

/* 行内代码 */
.doccontent code{font-family:var(--mono);font-size:.86em;background:var(--accent-soft);
  color:var(--accent-ink);padding:.12em .38em;border-radius:5px;overflow-wrap:anywhere}
/* 代码块 */
.doccontent .highlight{margin:0 0 1.2em;border:1px solid var(--line);border-radius:12px;
  background:var(--surface);overflow:hidden}
.doccontent .highlight pre{margin:0;padding:15px 18px;overflow-x:auto;font-size:.83rem;line-height:1.6}
.doccontent .highlight code{background:none;color:inherit;padding:0;font-size:1em;white-space:pre}
.doccontent .codetitle{margin:-1.2em 0 1.2em;font-family:var(--mono);font-size:.76rem;color:var(--muted)}

/* 表格 */
.doccontent table{border-collapse:collapse;width:100%;display:block;overflow-x:auto;
  margin:0 0 1.3em;font-size:.9rem}
.doccontent th,.doccontent td{border:1px solid var(--line);padding:8px 12px;text-align:left;
  vertical-align:top}
.doccontent th{background:var(--surface-2);font-weight:650;color:var(--ink);white-space:nowrap}
.doccontent td{color:var(--ink-2)}

/* 提示框 */
.admonition{margin:0 0 1.2em;padding:14px 18px;border-radius:12px;border:1px solid;
  background:var(--surface);border-left-width:4px}
.admonition .adm-title{margin:0 0 6px;font-weight:660;font-size:.94rem;color:inherit}
.admonition p:last-child,.admonition ul:last-child,.admonition ol:last-child{margin-bottom:0}
.admonition pre{background:rgba(255,255,255,.7)}
.adm-note,.adm-info{background:#eef4fb;border-color:#c8dcf3;color:#1d4e7d}
.adm-tip{background:#ecf7f0;border-color:#c5e6d1;color:#1c6140}
.adm-warning{background:#fdf5e7;border-color:#f0dcb0;color:#7d5311}
.adm-caution{background:#fdefe7;border-color:#f2cdb5;color:#8a4a1c}
.adm-danger{background:#fdeceb;border-color:#f3c2bf;color:#8f2b25}
.adm-important{background:#f1eefb;border-color:#d6cef0;color:#4a3a86}
.doccontent .admonition a{border-bottom-color:currentColor}

/* details */
.details{margin:0 0 1.2em;border:1px solid var(--line);border-radius:12px;padding:12px 18px;
  background:var(--surface)}
.details summary{cursor:pointer;font-weight:600}
.details[open] summary{margin-bottom:10px}

/* 脚注 */
.footnote{font-size:.85rem;color:var(--muted)}
.footnote-ref{font-size:.75em;vertical-align:super}

/* ---------- 侧栏目录 ---------- */
.doctoc{position:sticky;top:74px;font-size:.83rem;max-height:calc(100vh - 110px);overflow:auto}
.tochead{margin:0 0 10px;font-size:.72rem;letter-spacing:.1em;color:var(--muted)}
.toclist{list-style:none;margin:0;padding:0;border-left:1px solid var(--line)}
.toclist li{margin:0}
.toclist a{display:block;padding:4px 12px;color:var(--muted);text-decoration:none;
  border-left:2px solid transparent;margin-left:-1px;line-height:1.5}
.toclist a:hover{color:var(--accent-ink);border-left-color:var(--accent)}
.toclist .lvl2 a{color:var(--ink-2)}
.toclist .lvl4 a{padding-left:24px;font-size:.96em}
.tocempty{color:var(--muted);font-size:.8rem}

/* ---------- 文档总目录页 ---------- */
.indexwrap{max-width:960px;margin:0 auto;padding:44px 26px 90px}
.indexwrap h1{font-size:clamp(1.6rem,3vw,2rem);letter-spacing:-.02em;margin:0 0 10px}
.indexwrap .lede{color:var(--ink-2);margin:0 0 22px;max-width:62ch;font-size:.95rem}
.filterbar{display:flex;flex-wrap:wrap;gap:12px;align-items:center;margin:0 0 28px}
.filterbar input{flex:1 1 260px;min-width:0;padding:10px 14px;font:inherit;font-size:.9rem;
  border:1px solid var(--line-strong);border-radius:10px;background:var(--surface);color:var(--ink)}
.filterbar input:focus{outline:2px solid var(--accent);outline-offset:1px;border-color:var(--accent)}
.filterbar .count{font-family:var(--mono);font-size:.78rem;color:var(--muted)}
.group{margin:0 0 30px}
.group>h2{font-size:.78rem;letter-spacing:.1em;color:var(--muted);font-weight:600;
  margin:0 0 10px;padding-bottom:8px;border-bottom:1px solid var(--line)}
.doclist{list-style:none;margin:0;padding:0}
.doclist li{display:flex;gap:12px;align-items:baseline;padding:7px 0;border-bottom:1px dashed var(--line)}
.doclist a{color:var(--accent-ink);text-decoration:none;font-size:.94rem}
.doclist a:hover{text-decoration:underline}
.doclist .path{font-family:var(--mono);font-size:.72rem;color:var(--muted);margin-left:auto;
  text-align:right;overflow-wrap:anywhere}
.doclist li.hide{display:none}

/* ---------- 响应式 ---------- */
@media (max-width:1000px){
  .docwrap{grid-template-columns:minmax(0,1fr);gap:0;padding:28px 20px 70px}
  .doctoc{display:none}
  .doccontent{max-width:none}
  .topbar{padding:10px 16px}
}
@media (max-width:640px){
  .doccontent table{font-size:.84rem}
  .doclist li{flex-direction:column;gap:2px}
  .doclist .path{margin-left:0;text-align:left}
}
@media (prefers-reduced-motion:reduce){*{transition:none !important}}
/*PYGMENTS*/
"""

# ---------------------------------------------------------------- 文档总目录
def build_index(titles):
    pages = []
    for f in glob.glob(os.path.join(DOCS_OUT, "**", "*.html"), recursive=True):
        rel = os.path.relpath(f, DOCS_OUT).replace("\\", "/")
        if rel == "index.html":
            continue
        stem = re.sub(r"\.html$", "", rel)                       # 去掉 .html 后缀
        stem = re.sub(r"(^|/)index$", "", stem).strip("/")        # 目录索引页归到目录路由
        route = ("/docs/" + stem).rstrip("/") or "/docs"
        zh = route.startswith("/docs/zh-Hans")
        section = re.sub(r"^/docs/(zh-Hans/)?", "", route)
        section = section.split("/")[0] if "/" in section else "(顶层)"
        pages.append({"out": rel, "route": route, "title": titles.get(route, route.rsplit("/", 1)[-1]),
                      "zh": zh, "section": section})

    def render_group(name, items):
        if not items:
            return ""
        rows = "\n".join(
            '<li><a href="%s">%s</a><span class="path">%s</span></li>'
            % (p["out"], html.escape(p["title"]), html.escape(p["route"])) for p in items)
        return '<section class="group"><h2>%s（%d）</h2><ul class="doclist">%s</ul></section>' % (
            html.escape(name), len(items), rows)

    zh_pages = sorted([p for p in pages if p["zh"]], key=lambda p: p["route"])
    en_pages = sorted([p for p in pages if not p["zh"]], key=lambda p: p["route"])
    body = []
    for sec in sorted({p["section"] for p in zh_pages}):
        body.append(render_group("中文文档 / " + sec, [p for p in zh_pages if p["section"] == sec]))
    for sec in sorted({p["section"] for p in en_pages}):
        body.append(render_group("English Docs / " + sec, [p for p in en_pages if p["section"] == sec]))

    return INDEX_TMPL.format(total=len(pages), groups="\n".join(body),
                             version=VERSION, date=datetime.date.today().isoformat())

INDEX_TMPL = u"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>文档总目录 · Hermes Agent 课程</title>
<link rel="stylesheet" href="../assets/style.css">
</head>
<body>
<div class="indexwrap">
  <h1>Hermes Agent 文档总目录（本地镜像）</h1>
  <p class="lede">共 {total} 篇，全部为站内本地页面，离线可读。在下面的输入框里输入关键词可以即时过滤标题或路径。</p>
  <div class="filterbar">
    <input id="q" type="search" placeholder="过滤：例如 configuration / 工具 / tools" autocomplete="off">
    <span class="count" id="count">{total} / {total}</span>
    <a class="path" href="../index.html" style="font-family:var(--mono);font-size:.78rem">← 返回课程首页</a>
  </div>
{groups}
  <footer class="docfoot">
    <p>镜像内容来自 Hermes Agent 官方文档源码（{version}），构建日期 {date}。</p>
  </footer>
</div>
<script>
(function(){{
  var q = document.getElementById('q'), c = document.getElementById('count');
  var lis = Array.prototype.slice.call(document.querySelectorAll('.doclist li'));
  var groups = Array.prototype.slice.call(document.querySelectorAll('.group'));
  function apply(){{
    var k = q.value.trim().toLowerCase(), n = 0;
    lis.forEach(function(li){{
      var hit = !k || li.textContent.toLowerCase().indexOf(k) !== -1;
      li.classList.toggle('hide', !hit); if(hit) n++;
    }});
    groups.forEach(function(g){{
      var vis = g.querySelectorAll('.doclist li:not(.hide)').length;
      g.style.display = vis ? '' : 'none';
    }});
    c.textContent = n + ' / ' + lis.length;
  }}
  q.addEventListener('input', apply); apply();
}})();
</script>
</body>
</html>
"""

# ---------------------------------------------------------------- 课程首页
def build_course_page(total):
    src = open(COURSE_SRC, encoding="utf-8").read()
    out = src
    for url, local in LINK_MAP:
        pattern = re.compile(r'<a class="url" href="%s"[^>]*>%s</a>' % (re.escape(url), re.escape(url)))
        repl = '<a class="url" href="%s" title="原文地址：%s">%s</a>' % (local, url, local)
        out, n = pattern.subn(repl, out)
        assert n == 1, "链接未按预期匹配：%s (matched=%d)" % (url, n)

    old_meta = '<span>官方文档：hermes-agent.nousresearch.com</span>'
    new_meta = '<span>站内文档镜像 · %d 篇</span>' % total
    assert old_meta in out
    out = out.replace(old_meta, new_meta)

    old_sep = '<span class="sep">/</span>\n    <span class="progress">'
    new_sep = ('<span class="sep">/</span>\n'
               '    <a class="localindex" href="docs/index.html" '
               'style="color:var(--accent-ink);text-decoration:none;'
               'border-bottom:1px solid rgba(14,110,104,.3)">文档总目录</a>\n'
               '    <span class="sep">/</span>\n    <span class="progress">')
    assert old_sep in out
    out = out.replace(old_sep, new_sep, 1)

    old_foot = "所有链接均指向 Hermes Agent 官方文档站点。点击每个阶段右侧的方框可标记完成，"
    new_foot = ("页面内所有文档链接指向站内本地镜像（<code>docs/</code>），无需联网即可翻阅。" \
                "点击每个阶段右侧的方框可标记完成，")
    assert old_foot in out
    out = out.replace(old_foot, new_foot)

    old_tail = "主要配置文件位置：<code>~/.hermes/config.yaml</code>、<code>~/.hermes/.env</code>"
    new_tail = ("主要配置文件位置：<code>~/.hermes/config.yaml</code>、<code>~/.hermes/.env</code><br>\n"
                "镜像来源：Hermes Agent 官方文档源码（%s）· 构建日期 %s"
                % (VERSION, datetime.date.today().isoformat()))
    assert old_tail in out
    out = out.replace(old_tail, new_tail)

    # 链接文本是本地路径，去掉新窗口打开
    out = out.replace('<a class="url" href="docs/', '<a class="url" target="_self" href="docs/')
    return out

# ---------------------------------------------------------------- 说明与打包
README = u"""{name}
=====================================================

这是什么
  一套可离线部署的 Hermes Agent 课程静态站点：
  · index.html            课程首页（六个学习阶段），所有文档链接已改为站内相对路径
  · docs/                 官方文档镜像，共 {pages} 篇（中文 + 英文）
  · docs/index.html       文档总目录，支持关键词即时过滤
  · llms.txt              全部页面的一句话索引（每页标题 + 路径）
  · llms-full.txt         全部文档源码合集（纯文本，约 10 MB，可作离线 LLM 语料）
  · assets/style.css      全站样式（含代码高亮）
  · assets/img/           文档引用的图片
  · tools/                构建脚本，可重复生成

怎么用
  方式一（最简单）：双击 index.html 用浏览器打开，页面内链接在本地即可跳转。
  方式二（推荐，部署到服务器/内网）：
      cd {site}
      python -m http.server 8000
      浏览器访问 http://localhost:8000/
  部署到 Nginx / IIS / 校园服务器：把本目录整体上传到网站根目录即可，
  全部为静态文件，无需数据库、无需 Node、无需联网。

链接说明
  1. 首页 7 个「官方文档」链接已从 https://hermes-agent.nousresearch.com/...
     改为站内相对路径 docs/**.html；鼠标悬停仍能看到原始地址（title 属性）。
  2. 文档页之间的交叉链接同样已本地化，点击在站内跳转。
  3. 文档里指向 GitHub、Discord 等站外链接保持原样，标记为 ↗，需要联网才能打开
     ——这部分无法离线镜像，属于第三方资源。

内容来源与版本
  文档内容来自本机 Hermes Agent 安装目录中的官方文档源码：
      {repo}
  版本：{version}
  构建日期：{date}

已知的断链（都来自官方文档源码本身，共 20 处，不影响课程使用）
  · 3 处图片/视频：源码引用了 /docs/img/... 但这些素材在仓库里并不存在
  · 14 处技能目录链接 + 1 处 rl-training.md：指向的页面在源码树里根本没有
  · 1 处 /plugins：指向站点插件页（不属于文档源码）
  · 3 处锚点：中文页与英文页都没有对应小节
  其余 1282 处站外链接（GitHub、Discord 等）保持原样，标记 ↗，需要联网才能打开。

重新构建（按顺序执行）
  cd {site}\\tools
  python build_site.py     # ① 渲染全部文档页（约 4-5 分钟）
  python fixup_links.py    # ② 修补站内绝对路径、中文页缺失锚点
  python package_site.py   # ③ 生成样式/目录/首页/llms 文件并打包 zip
  python check_links.py    # ④ 全站链接自检（应报出 20 处已知断链）
"""

def load_src_map():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "bs", os.path.join(os.path.dirname(os.path.abspath(__file__)), "build_site.py"))
    bs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bs)
    return bs.ROUTES

def main():
    global SRC_OF
    SRC_OF = load_src_map()
    report = json.load(open(os.path.join(SITE, "build-report.json"), encoding="utf-8"))
    titles = report["titles"]
    total = len(glob.glob(os.path.join(DOCS_OUT, "**", "*.html"), recursive=True)) - 1

    os.makedirs(ASSETS_OUT, exist_ok=True)
    with open(os.path.join(ASSETS_OUT, "style.css"), "w", encoding="utf-8", newline="\n") as f:
        f.write(build_css())
    with open(os.path.join(DOCS_OUT, "index.html"), "w", encoding="utf-8", newline="\n") as f:
        f.write(build_index(titles))
    with open(os.path.join(SITE, "index.html"), "w", encoding="utf-8", newline="\n") as f:
        f.write(build_course_page(total))
    repo = os.path.join(HOME, "AppData", "Local", "hermes", "hermes-agent", "website")
    with open(os.path.join(SITE, "README-部署说明.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write(README.format(name="Hermes Agent 课程站（离线镜像）", pages=total, site=SITE,
                              repo=repo, version=VERSION, date=datetime.date.today().isoformat()))
    print("样式 / 总目录 / 首页 / 说明已生成，文档页 %d 篇" % total)

    # llms.txt：全部页面的一句话索引（离线可用，替代官网部署时生成的同名文件）
    lines = ["# Hermes Agent 文档（本地离线镜像）", ""]
    for lang, title in (("zh-Hans", "中文文档"), ("", "English Docs")):
        lines.append("## " + title)
        pref = "/docs/" + (lang + "/" if lang else "")
        for route in sorted(r for r in titles if r.startswith(pref) and
                           (lang or not r.startswith("/docs/zh-Hans"))):
            lines.append("- [%s](%s)" % (titles[route], route))
        lines.append("")
    with open(os.path.join(SITE, "llms.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    print("llms.txt 已生成（%d 条）" % (len(lines) - 5))

    # llms-full.txt：把全部文档源码拼成一份纯文本合集
    parts, size = ["# Hermes Agent 文档全集（本地离线镜像）\n"], 0
    for route in sorted(titles):
        src = SRC_OF.get(route)
        if not src or not os.path.exists(src):
            continue
        body = open(src, encoding="utf-8", errors="replace").read()
        parts.append("\n\n<!-- %s | %s -->\n\n%s\n" % (route, titles[route], body))
        size += len(body)
    with open(os.path.join(SITE, "llms-full.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("".join(parts))
    print("llms-full.txt 已生成（%.1f MB 文本）" % (size / 1048576.0))

    zip_path = os.path.join(os.path.dirname(SITE), os.path.basename(SITE) + ".zip")
    n = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for dp, dn, fn in os.walk(SITE):
            for f in fn:
                full = os.path.join(dp, f)
                z.write(full, os.path.relpath(full, os.path.dirname(SITE)))
                n += 1
    print("已打包 %d 个文件 -> %s (%.1f MB)" % (n, zip_path, os.path.getsize(zip_path) / 1048576.0))

if __name__ == "__main__":
    main()
