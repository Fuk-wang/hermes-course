#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修补文档镜像里残留的「站点根绝对路径」链接（原来指向 docusaurus 的线上路径）。

例如 docs/user-guide/cli.html 里的 href="/docs/img/docs/cli-layout.svg"：
镜像把图片放在 assets/img 下，这个链接在本地点不开。本脚本按下面的顺序找目标，
找到就改写成相对路径，找不到就原样留着并报告出来。

  1) /docs/img/xxx 或 /img/xxx      -> assets/img/xxx
  2) /llms*.txt、/favicon.svg 等根文件 -> 站点根同名文件
  3) 页面在 zh-Hans 下时优先 /zh-Hans 镜像路径，其次英文路径
     （candidate.html 与 candidate/index.html 两种都试）
  4) 兜底：同目录下的同名文件

用法：  python tools/fixup_deep_links.py [--dry]
"""

import os, re, io, sys

HOME = os.path.expanduser("~")
SITE = os.path.join(HOME, "Desktop", "hermes-course-site")
DOCS = os.path.join(SITE, "docs")
DRY = "--dry" in sys.argv

HREF = re.compile(r'(href|src)="(/[^"/][^"]*)"')
ROOT_FILES = {"llms.txt", "llms-full.txt", "favicon.svg", "index.html", "path.html"}


def rel_to(page_dir, target):
    r = os.path.relpath(target, page_dir).replace("\\", "/")
    return r


def candidates(path, page, page_dir):
    p = path.lstrip("/")
    zh = "zh-Hans/" if os.sep + "zh-Hans" + os.sep in page else ""
    out = []
    if p.startswith("docs/img/"):
        out.append(os.path.join(SITE, "assets", "img", p[len("docs/img/"):]))
    if p.startswith("img/"):
        out.append(os.path.join(SITE, "assets", "img", p[len("img/"):]))
    if p in ROOT_FILES:
        out.append(os.path.join(SITE, p))
    for prefix in (zh, ""):
        base = os.path.join(DOCS, prefix + p)
        out.append(base + ".html")
        out.append(os.path.join(base, "index.html"))
    out.append(os.path.join(page_dir, os.path.basename(p)))
    out.append(os.path.join(page_dir, os.path.basename(p) + ".html"))
    return out


def main():
    pages = []
    for dp, _, fs in os.walk(DOCS):
        for f in fs:
            if f.endswith(".html"):
                pages.append(os.path.join(dp, f))

    fixed = 0
    untouched = {}
    for page in pages:
        src = io.open(page, encoding="utf-8", errors="replace").read()
        page_dir = os.path.dirname(page)
        new = src

        def sub(m):
            nonlocal fixed
            attr, path = m.group(1), m.group(2)
            if path.startswith("//"):
                return m.group(0)
            for c in candidates(path, page, page_dir):
                if os.path.isfile(c):
                    fixed += 1
                    return '%s="%s"' % (attr, rel_to(page_dir, c))
            key = (path, os.path.relpath(page, SITE).replace("\\", "/"))
            untouched[key] = True
            return m.group(0)

        new = HREF.sub(sub, src)
        if new != src and not DRY:
            io.open(page, "w", encoding="utf-8").write(new)

    print("改写链接：%d 处%s" % (fixed, "（--dry 未写入）" if DRY else ""))
    print("仍无法解析：%d 处" % len(untouched))
    for (path, pg) in list(untouched.keys())[:20]:
        print("   %-52s <- %s" % (path, pg))
    return 0


if __name__ == "__main__":
    sys.exit(main())
