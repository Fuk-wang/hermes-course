#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
构建后处理：修补两类链接问题（不改内容，只改 href）

1. 站内绝对路径链接（源码里的 /user-guide/xxx）——按 /docs/user-guide/xxx 解析成
   站内相对路径；上游站点上这类链接本就是断的，本地镜像顺手接上。
2. 中文页里指向“英文锚点”的链接——中文翻译没翻对应小节标题，导致 #fragment 落空。
   若英文原页存在该锚点，就把链接改指英文页对应小节，并加 class="enfallback" 标注。

用法：  python fixup_links.py      （在 build_site.py 之后、package_site.py 之前执行）
"""

import os, re, sys, glob, collections, importlib.util

HOME = os.path.expanduser("~")
SITE = os.path.join(HOME, "Desktop", "hermes-course-site")
HERE = os.path.dirname(os.path.abspath(__file__))

spec = importlib.util.spec_from_file_location("bs", os.path.join(HERE, "build_site.py"))
bs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bs)

ID_RE = re.compile(r'\sid="([^"]+)"')
A_RE = re.compile(r'<a\s+([^>]*?)href="([^"]*)"([^>]*?)>')

PAGES = sorted(glob.glob(os.path.join(SITE, "**", "*.html"), recursive=True))
_ids = {}

def ids_of(path):
    if path not in _ids:
        _ids[path] = set(ID_RE.findall(open(path, encoding="utf-8", errors="replace").read()))
    return _ids[path]

def rel_to(page, target):
    return os.path.relpath(target, os.path.dirname(page)).replace("\\", "/")

def en_counterpart(path):
    """docs/zh-Hans/a/b.html -> docs/a/b.html（若存在）"""
    marker = os.sep + "zh-Hans" + os.sep
    if marker in path:
        alt = path.replace(marker, os.sep, 1)
        return alt if os.path.exists(alt) else None
    return None

def main():
    stats = collections.Counter()
    examples = collections.defaultdict(list)

    for page in PAGES:
        text = open(page, encoding="utf-8", errors="replace").read()
        changed = False

        def sub(m):
            nonlocal changed
            pre, href, post = m.group(1), m.group(2), m.group(3)
            if href.startswith(("http://", "https://", "//", "mailto:", "tel:",
                                "javascript:", "data:", "hermes:")):
                return m.group(0)

            # ---- 问题 3：纯页内锚点在中文页不存在 -> 指向英文原页对应小节
            if href.startswith("#"):
                frag = href[1:]
                if frag in ids_of(page):
                    return m.group(0)
                alt = en_counterpart(page)
                if alt and frag in ids_of(alt):
                    stats["页内锚点回退到英文页"] += 1
                    if len(examples["页内锚点回退到英文页"]) < 4:
                        examples["页内锚点回退到英文页"].append("%s #%s -> %s" % (
                            os.path.relpath(page, SITE), frag, os.path.relpath(alt, SITE)))
                    changed = True
                    return ('<a %shref="%s#%s"%s class="enfallback" '
                            'title="中文页尚无此小节，指向英文原页对应位置">'
                            % (pre, rel_to(page, alt), frag, post.rstrip()))
                stats["页内锚点两处都缺（上游问题）"] += 1
                return m.group(0)
            path, _, frag = href.partition("#")
            target = page if not path else os.path.normpath(
                os.path.join(os.path.dirname(page), path.replace("/", os.sep)))

            # ---- 问题 1：站内绝对路径
            if href.startswith("/") and not os.path.exists(target):
                # 站点根目录下的文件（/llms.txt 等）
                rootfile = os.path.join(SITE, path.lstrip("/").replace("/", os.sep))
                if os.path.isfile(rootfile):
                    stats["根目录文件已接上"] += 1
                    changed = True
                    return '<a %shref="%s%s"%s>' % (pre, rel_to(page, rootfile),
                                                    ("#" + frag) if frag else "", post)
                cand = os.path.join(SITE, bs.route_to_out("/docs" + path.rstrip("/")).replace("/", os.sep))
                if not os.path.exists(cand):
                    cand = os.path.join(SITE, bs.route_to_out(path.rstrip("/")).replace("/", os.sep))
                if os.path.exists(cand):
                    stats["绝对路径已接上"] += 1
                    if len(examples["绝对路径已接上"]) < 4:
                        examples["绝对路径已接上"].append("%s -> %s" % (
                            os.path.relpath(page, SITE), rel_to(page, cand)))
                    changed = True
                    return '<a %shref="%s%s"%s>' % (pre, rel_to(page, cand),
                                                    ("#" + frag) if frag else "", post)
                stats["绝对路径仍缺失"] += 1
                return m.group(0)

            if not os.path.exists(target) or not frag or not target.endswith(".html"):
                return m.group(0)

            # ---- 问题 2：锚点在目标页不存在
            if frag in ids_of(target):
                return m.group(0)
            alt = en_counterpart(target)
            if alt and frag in ids_of(alt):
                stats["锚点回退到英文页"] += 1
                if len(examples["锚点回退到英文页"]) < 4:
                    examples["锚点回退到英文页"].append("%s -> %s#%s" % (
                        os.path.relpath(page, SITE), os.path.relpath(alt, SITE), frag))
                changed = True
                extra = ' class="enfallback" title="中文页尚无此小节，指向英文原页对应位置"'
                return '<a %shref="%s#%s"%s%s>' % (pre, rel_to(page, alt), frag,
                                                  post.rstrip(), extra)
            stats["锚点两处都缺（上游问题）"] += 1
            return m.group(0)

        new = A_RE.sub(sub, text)
        if changed and new != text:
            with open(page, "w", encoding="utf-8", newline="\n") as f:
                f.write(new)

    print("=== 链接修补结果 ===")
    for k in ("绝对路径已接上", "根目录文件已接上", "绝对路径仍缺失", "锚点回退到英文页",
              "页内锚点回退到英文页", "锚点两处都缺（上游问题）", "页内锚点两处都缺（上游问题）"):
        print("  %s: %d" % (k, stats[k]))
        for e in examples[k]:
            print("      " + e)
    return 0

if __name__ == "__main__":
    sys.exit(main())
