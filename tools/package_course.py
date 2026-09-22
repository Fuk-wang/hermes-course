#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
打包 v2 站点为可分发 zip（赛博风电音学习站）。

包含：index.html、path.html、steps/、assets/（含 img）、docs/ 全部镜像、
      llms.txt、llms-full.txt、README-部署说明.txt
排除：_content/（构建输入）、_shots/（验证截图）、tools/__pycache__、.git

用法：  python tools/package_course.py
"""

import os, sys, zipfile, datetime

HOME = os.path.expanduser("~")
SITE = os.path.join(HOME, "Desktop", "hermes-course-site")
OUT = os.path.join(HOME, "Desktop", "hermes-course-site.zip")
SKIP_DIRS = {"_content", "_shots", ".git", "__pycache__"}
SKIP_FILES = {"build.log"}


def main():
    n = 0
    if os.path.exists(OUT):
        os.remove(OUT)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for dp, dns, fns in os.walk(SITE):
            dns[:] = [d for d in dns if d not in SKIP_DIRS]
            for f in fns:
                if f in SKIP_FILES:
                    continue
                full = os.path.join(dp, f)
                rel = os.path.relpath(full, SITE).replace("\\", "/")
                z.write(full, "hermes-course-site/" + rel)
                n += 1
    print("已打包 %d 个文件 -> %s (%.1f MB)"
          % (n, OUT, os.path.getsize(OUT) / 1048576.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
