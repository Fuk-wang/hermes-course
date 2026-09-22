#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
站点链接自检：遍历站点内所有 HTML，检查相对链接与图片是否指向真实存在的文件，
并顺带核对页面内锚点（#fragment）是否存在。

用法：  python check_links.py
"""

import os, re, sys, glob, html, collections

HOME = os.path.expanduser("~")
SITE = os.path.join(HOME, "Desktop", "hermes-course-site")
ATTR = re.compile(r'(?:href|src)="([^"]+)"')
CODE = re.compile(r"<pre\b.*?</pre>|<code\b.*?</code>", re.S)   # 代码示例里的 "链接" 不算链接
ID_RE = re.compile(r'\sid="([^"]+)"')

def main():
    pages = sorted(glob.glob(os.path.join(SITE, "**", "*.html"), recursive=True))
    print("扫描 %d 个 HTML 文件 ..." % len(pages))

    ids_cache = {}
    missing, bad_frag, external = [], collections.Counter(), 0
    ext_domains = collections.Counter()

    for page in pages:
        src = open(page, encoding="utf-8", errors="replace").read()
        base = os.path.dirname(page)
        for val in set(ATTR.findall(CODE.sub("", src))):
            if val.startswith(("http://", "https://")):
                external += 1
                ext_domains[re.sub(r"^https?://([^/]+).*", r"\1", val)] += 1
                continue
            if val.startswith(("mailto:", "javascript:", "tel:", "data:")):
                continue
            path, _, frag = val.partition("#")
            if not path:                      # 纯页内锚点
                target = page
            else:
                target = os.path.normpath(os.path.join(base, path.replace("/", os.sep)))
            if not os.path.exists(target):
                missing.append((os.path.relpath(page, SITE).replace("\\", "/"), val))
                continue
            if frag and target.endswith(".html"):
                if target not in ids_cache:
                    ids_cache[target] = set(ID_RE.findall(
                        open(target, encoding="utf-8", errors="replace").read()))
                if frag not in ids_cache[target]:
                    bad_frag[(os.path.relpath(page, SITE).replace("\\", "/"), val)] += 1

    print("\n=== 结果 ===")
    print("缺失的本地目标:", len(missing))
    for pg, val in missing[:20]:
        print("   %s  ->  %s" % (pg, val))
    print("锚点对不上的链接:", len(bad_frag))
    for (pg, val), _ in list(bad_frag.items())[:10]:
        print("   %s  ->  %s" % (pg, val))
    print("站外链接（需联网，不入镜像）:", external, "处")
    print("   top:", ", ".join("%s(%d)" % kv for kv in ext_domains.most_common(6)))
    return 0 if not missing else 1

if __name__ == "__main__":
    sys.exit(main())
