#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
把 Hermes Agent 仓库内的文档源码（website/docs + i18n/zh-Hans）渲染成一套
可离线部署的静态站点，并把课程首页里的外部文档链接改成站内相对路径。

用法：  python build_site.py
输出：  <SITE>/index.html            课程首页（链接已本地化）
        <SITE>/docs/**/*.html       文档镜像（776 页）
        <SITE>/assets/**            样式与图片
        <SITE>/README-部署说明.txt
"""

import os, re, sys, json, html, shutil, zipfile, datetime, collections

# ---------------------------------------------------------------- 配置
HOME = os.path.expanduser("~")
REPO_WEB = os.path.join(HOME, "AppData", "Local", "hermes", "hermes-agent", "website")
SRC_EN = os.path.join(REPO_WEB, "docs")
SRC_ZH = os.path.join(REPO_WEB, "i18n", "zh-Hans", "docusaurus-plugin-content-docs", "current")
SRC_STATIC = os.path.join(REPO_WEB, "static")
REPO = os.path.dirname(REPO_WEB)

SITE = os.path.join(HOME, "Desktop", "hermes-course-site")
DOCS_OUT = os.path.join(SITE, "docs")
ASSETS_OUT = os.path.join(SITE, "assets")
IMG_OUT = os.path.join(ASSETS_OUT, "img")

VERSION = "Hermes Agent v0.21.3 (2026.9.14) · upstream b5251aa4"
ORIGIN = "https://hermes-agent.nousresearch.com"
BUILD_DATE = datetime.date.today().isoformat()

norm = lambda p: os.path.normpath(os.path.abspath(p)).replace("\\", "/")

# ---------------------------------------------------------------- 1. 路由表
def build_routes():
    routes, titles = {}, {}
    for root, prefix in ((SRC_EN, ""), (SRC_ZH, "zh-Hans")):
        for dp, _, fn in os.walk(root):
            for f in fn:
                if not f.endswith((".md", ".mdx")):
                    continue
                full = os.path.join(dp, f)
                stem = re.sub(r"\.mdx?$", "", os.path.relpath(full, root).replace("\\", "/"))
                stem = re.sub(r"(^|/)index$", "", stem).strip("/")
                route = ("/docs/" + (prefix + "/" if prefix else "") + stem).rstrip("/")
                routes[route] = norm(full)
    return routes

ROUTES = build_routes()
FILE2ROUTE = {v: k for k, v in ROUTES.items()}

def route_to_out(route):
    """路由 -> 站点内相对输出路径"""
    rel = route[len("/docs"):] or "/index"
    rel = rel.strip("/")
    return "docs/" + (rel + ".html" if rel else "index.html")

OUT2ROUTE = {route_to_out(r): r for r in ROUTES}

# ---------------------------------------------------------------- 2. Markdown 管线
import markdown
from markdown.extensions.toc import slugify as _default_slugify
from pygments.formatters import HtmlFormatter

def gh_slugify(value, separator):
    """贴近 GitHub / Docusaurus 的锚点规则：标点直接删掉，每个空格换成一个连字符（不合并连续连字符）"""
    s = value.strip().lower()
    s = re.sub(r"[^\w\u4e00-\u9fff\u3040-\u30ff\s-]", "", s, flags=re.UNICODE)
    return s.replace(" ", separator)

MD = markdown.Markdown(extensions=[
    "fenced_code", "tables", "attr_list", "def_list", "footnotes",
    "toc",
    "codehilite",
], extension_configs={
    "toc": {"slugify": gh_slugify, "permalink": False, "anchorlink": False, "toc_depth": "2-4"},
    "codehilite": {"guess_lang": False, "css_class": "highlight",
                   "pygments_style": "default", "linenums": False},
})

FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.S)
MDX_COMMENT = re.compile(r"\{/\*.*?\*/\}", re.S)
IMPORT_LINE = re.compile(r"^import\s.*?;?\s*$", re.M)

ADM_KINDS = {"note", "tip", "info", "warning", "caution", "danger", "important"}
ADM_LABEL = {
    "zh": {"note": "注意", "tip": "提示", "info": "说明", "warning": "警告",
           "caution": "小心", "danger": "危险", "important": "重要"},
    "en": {"note": "Note", "tip": "Tip", "info": "Info", "warning": "Warning",
           "caution": "Caution", "danger": "Danger", "important": "Important"},
}

def strip_frontmatter(text):
    meta = {}
    m = FRONTMATTER.match(text)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line and not line.startswith((" ", "\t", "-")):
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip().strip('"').strip("'")
        text = text[m.end():]
    return text, meta

def preprocess(text, store, lang="zh"):
    """把 ::: 提示框、<details>、<div> 里的 markdown 先渲染好，
    用占位符替换，避免 raw-HTML 解析边界问题。"""
    text = MDX_COMMENT.sub("", text)
    text = IMPORT_LINE.sub("", text)

    # ---- ::: 提示框（支持嵌套）
    lines = text.split("\n")
    out, stack = [], []          # stack: [kind, title, body_lines]
    for ln in lines:
        s = ln.strip()
        m = re.match(r"^:::([a-zA-Z]+)\s*(.*)$", s)
        if m and not s == ":::":
            kind = m.group(1).lower()
            rest = m.group(2).strip()
            title = ""
            if rest.startswith("[") and rest.endswith("]"):
                title = rest[1:-1].strip()
            else:
                title = rest
            stack.append({"kind": kind, "title": title, "body": []})
            continue
        if s == ":::" and stack:
            adm = stack.pop()
            if stack:
                stack[-1]["body"].append("\x00ADM%d\x00" % len(store))
            body_md = "\n".join(adm["body"])
            inner = render_md(body_md)
            kind = adm["kind"] if adm["kind"] in ADM_KINDS else "note"
            title = adm["title"] or ADM_LABEL[lang][kind]
            head = '<p class="adm-title">%s</p>' % html.escape(title)
            block = ('<div class="admonition adm-%s">%s\n%s\n</div>' % (kind, head, inner))
            store.append(block)
            if not stack:
                out.append("\x00ADM%d\x00" % (len(store) - 1))
            continue
        if stack:
            stack[-1]["body"].append(ln)
        else:
            out.append(ln)
    # 未闭合的提示框：原样吐出
    for adm in stack:
        out.append(":::" + adm["kind"])
        out.extend(adm["body"])
    text = "\n".join(out)

    # ---- <details> 内的 markdown
    def details_sub(m):
        attrs, inner = m.group(1), m.group(2)
        if "class=" not in attrs:
            attrs = attrs + ' class="details"'
        store.append('<details%s>\n%s\n</details>' % (attrs, render_md(inner)))
        return "\x00ADM%d\x00" % (len(store) - 1)
    text = re.sub(r"<details([^>]*)>\s*(.*?)</details>", details_sub, text, flags=re.S)

    # ---- 代码块 info string 里的 Docusaurus 元数据（title= / showLineNumbers）剥掉
    def fence_sub(m):
        return "```" + m.group(1)
    text = re.sub(r"^```([a-zA-Z0-9+#-]*)([^\n]*)$", fence_sub, text, flags=re.M)
    return text, store

def render_md(text):
    MD.reset()
    return MD.convert(text)

# ---------------------------------------------------------------- 3. 链接与资源重写
LINK_RE = re.compile(r'(href|src)="([^"]*)"')

class PageCtx(object):
    def __init__(self, route, src_path, assets):
        self.route = route
        self.src = src_path
        self.dir = os.path.dirname(src_path)
        self.out = route_to_out(route)
        self.assets = assets
        self.unresolved = []

    @property
    def rel_root(self):
        """从本页到站点根目录的相对前缀"""
        depth = self.out.count("/")
        return "../" * depth if depth else ""

def resolve_route(tgt, ctx):
    """把相对 / 绝对 md 链接（含 Docusaurus 风格的无扩展名目录链接）解析成路由"""
    tgt = tgt.split("#")[0].split("?")[0]
    if not tgt:
        return None
    if tgt.startswith("/docs/"):
        r = tgt.rstrip("/")
        return r if r in ROUTES else None
    cands = []
    if re.search(r"\.mdx?$", tgt):
        cands.append(tgt)
    elif not os.path.splitext(tgt.rstrip("/"))[1]:      # ./iron-proxy  -> iron-proxy.md / iron-proxy/index.md
        cands.append(tgt.rstrip("/") + ".md")
        cands.append(tgt.rstrip("/") + "/index.md")
    for c in cands:
        p = norm(os.path.join(ctx.dir, c))
        r = FILE2ROUTE.get(p)
        if r:
            return r
        # 中文缺翻译时回退到英文原页（Docusaurus 同款行为）
        if ctx.route.startswith("/docs/zh-Hans/"):
            alt = norm(os.path.join(SRC_EN, os.path.relpath(p, SRC_ZH)))
            r = FILE2ROUTE.get(alt)
            if r:
                return r
    return None

SKIP_SCHEMES = ("mailto:", "tel:", "javascript:", "data:", "hermes:", "blob:")
CODE_SPLIT = re.compile(r"(<pre\b.*?</pre>|<code\b.*?</code>)", re.S)

def rewrite_links(htmltext, ctx, external_counter):
    def sub(m):
        attr, val = m.group(1), m.group(2)
        if val.startswith(("http://", "https://", "//")):
            external_counter.append(val)
            if attr == "href":
                return '%s="%s" class="ext" target="_blank" rel="noopener"' % (attr, val)
            return m.group(0)
        if val.startswith("#") or val.startswith(SKIP_SCHEMES):
            return m.group(0)
        if val.startswith(("/img/", "/files/", "/api/", "/oauth/")):
            src = os.path.join(SRC_STATIC, val.lstrip("/").replace("/", os.sep))
            if os.path.exists(src):
                ctx.assets.add(val)
                return '%s="%sassets/%s"' % (attr, ctx.rel_root, val.lstrip("/"))
            return m.group(0)
        if val.startswith("/") and not val.startswith("/docs/"):
            return m.group(0)                       # 其它站内绝对路径，原样保留
        base, _, frag = val.partition("#")
        r = resolve_route(base, ctx)
        if r:
            rel = os.path.relpath(route_to_out(r), os.path.dirname(ctx.out) or ".")
            return '%s="%s%s"' % (attr, rel.replace("\\", "/"), ("#" + frag) if frag else "")
        ctx.unresolved.append(val)
        return m.group(0)

    # 代码片段（<pre>/<code>）里的内容原样保留，避免改写示例代码
    parts = CODE_SPLIT.split(htmltext)
    for i in range(0, len(parts), 2):
        parts[i] = LINK_RE.sub(sub, parts[i])
    return "".join(parts)

# ---------------------------------------------------------------- 4. 页面模板
PAGE_TMPL = u"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · Hermes Agent 文档</title>
<link rel="stylesheet" href="{rel_root}assets/style.css">
</head>
<body class="doc-body">
<header class="topbar">
  <a class="brand" href="{rel_root}index.html">Hermes Agent 课程</a>
  <span class="crumb">{crumb}</span>
  <span class="langtag">{langtag}</span>
</header>
<div class="docwrap">
  <main class="docmain">
    <article class="doccontent">
{body}
    </article>
    <footer class="docfoot">
      <p>本页为<b>本地离线镜像</b>，内容来自 Hermes Agent 官方文档源码（{version}）。</p>
      <p>原始地址：<code>{origin}</code></p>
    </footer>
  </main>
  <aside class="doctoc">
    <p class="tochead">本页目录</p>
{toc}
  </aside>
</div>
</body>
</html>
"""

def build_toc(tokens, depth=2):
    if not tokens:
        return "<p class=\"tocempty\">（本页无小节标题）</p>"
    out = ["<ul class=\"toclist\">"]
    for t in tokens:
        if t["level"] > depth + 1:
            continue
        out.append('<li class="lvl%d"><a href="#%s">%s</a></li>'
                   % (t["level"], t["id"], html.escape(re.sub(r"<[^>]+>", "", t["name"]))))
        if t["level"] <= depth and t.get("children"):
            for c in t["children"]:
                out.append('<li class="lvl%d"><a href="#%s">%s</a></li>'
                           % (c["level"], c["id"], html.escape(re.sub(r"<[^>]+>", "", c["name"]))))
    out.append("</ul>")
    return "\n".join(out)

def crumb_of(route):
    rel = route[len("/docs"):].strip("/")
    if rel.startswith("zh-Hans/"):
        return "中文文档 / " + rel[len("zh-Hans/"):]
    return "English Docs / " + (rel or "index")

# ---------------------------------------------------------------- 5. 构建
def slug_title(route, meta, body, src):
    if meta.get("title"):
        return meta["title"]
    m = re.search(r"<h1[^>]*>(.*?)</h1>", body, re.S)
    if m:
        return re.sub(r"<[^>]+>", "", m.group(1)).strip()
    return route.rsplit("/", 1)[-1].replace("-", " ").title()

def main():
    for d in (DOCS_OUT, ASSETS_OUT, IMG_OUT):
        os.makedirs(d, exist_ok=True)

    external = []
    unresolved = collections.Counter()
    titles = {}
    failures = []
    pages = sorted(ROUTES)
    only = [a for a in sys.argv[1:] if a.startswith("/docs")]
    if only:
        pages = only
    print("开始渲染 %d 页 ..." % len(pages))

    for i, route in enumerate(pages, 1):
        try:
            src = ROUTES[route]
            raw = open(src, encoding="utf-8", errors="replace").read()
            text, meta = strip_frontmatter(raw)
            assets = set()
            ctx = PageCtx(route, src, assets)
            store = []
            plang = "zh" if route.startswith("/docs/zh-Hans") else "en"
            text2, store = preprocess(text, store, plang)
            body = render_md(text2)
            toc_tokens = list(getattr(MD, "toc_tokens", []) or [])
            # 占位符回填（先处理被 markdown 包进 <p> 的块级占位符）
            body = re.sub(r"<p>\s*\x00ADM(\d+)\x00\s*</p>",
                          lambda m: store[int(m.group(1))], body)
            body = re.sub(r"\x00ADM(\d+)\x00",
                          lambda m: store[int(m.group(1))], body)
            body = rewrite_links(body, ctx, external)
            title = slug_title(route, meta, body, src)
            titles[route] = title
            if route.startswith("/docs/zh-Hans"): lang, langtag = "zh-CN", "中文"
            else: lang, langtag = "en", "English"

            page = PAGE_TMPL.format(
                lang=lang, title=html.escape(title), rel_root=ctx.rel_root,
                crumb=html.escape(crumb_of(route)), langtag=langtag,
                body=body, toc=build_toc(toc_tokens),
                version=VERSION, origin=ORIGIN + route)

            dest = os.path.join(SITE, ctx.out.replace("/", os.sep))
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "w", encoding="utf-8", newline="\n") as f:
                f.write(page)

            for a in assets:
                sp = os.path.join(SRC_STATIC, a.lstrip("/").replace("/", os.sep))
                dp = os.path.join(ASSETS_OUT, a.lstrip("/").replace("/", os.sep))
                if os.path.exists(sp) and not os.path.exists(dp):
                    os.makedirs(os.path.dirname(dp), exist_ok=True)
                    shutil.copy2(sp, dp)

            unresolved.update(ctx.unresolved)
            if i % 100 == 0:
                print("  ... %d/%d" % (i, len(pages)))
            if i % 100 == 0:
                print("  ... %d/%d" % (i, len(pages)))
        except Exception as e:
            failures.append((route, "%s: %s" % (type(e).__name__, e)))
            print("  [FAIL] %s -> %s" % (route, e))

    print("渲染完成：%d 页" % len(pages))
    json.dump({"titles": titles, "unresolved": dict(unresolved), "external": len(external),
               "failures": [list(f) for f in failures]},
              open(os.path.join(SITE, "build-report.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("未解析的内部链接：", sum(unresolved.values()), "处，", len(unresolved), "种")
    print("渲染失败页：", len(failures))
    for r, e in failures[:10]:
        print("   -", r, e)
    return titles, unresolved

if __name__ == "__main__":
    main()
