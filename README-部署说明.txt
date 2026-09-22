Hermes Agent 课程站（离线镜像）
=====================================================

这是什么
  一套可离线部署的 Hermes Agent 课程静态站点：
  · index.html            课程首页（六个学习阶段），所有文档链接已改为站内相对路径
  · docs/                 官方文档镜像，共 775 篇（中文 + 英文）
  · docs/index.html       文档总目录，支持关键词即时过滤
  · llms.txt              全部页面的一句话索引（每页标题 + 路径）
  · llms-full.txt         全部文档源码合集（纯文本，约 10 MB，可作离线 LLM 语料）
  · assets/style.css      全站样式（含代码高亮）
  · assets/img/           文档引用的图片
  · tools/                构建脚本，可重复生成

怎么用
  方式一（最简单）：双击 index.html 用浏览器打开，页面内链接在本地即可跳转。
  方式二（推荐，部署到服务器/内网）：
      cd C:\Users\79305\Desktop\hermes-course-site
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
      C:\Users\79305\AppData\Local\hermes\hermes-agent\website
  版本：Hermes Agent v0.21.3 (2026.9.14) · upstream b5251aa4
  构建日期：2026-09-20

已知的断链（都来自官方文档源码本身，共 20 处，不影响课程使用）
  · 3 处图片/视频：源码引用了 /docs/img/... 但这些素材在仓库里并不存在
  · 14 处技能目录链接 + 1 处 rl-training.md：指向的页面在源码树里根本没有
  · 1 处 /plugins：指向站点插件页（不属于文档源码）
  · 3 处锚点：中文页与英文页都没有对应小节
  其余 1282 处站外链接（GitHub、Discord 等）保持原样，标记 ↗，需要联网才能打开。

重新构建（按顺序执行）
  cd C:\Users\79305\Desktop\hermes-course-site\tools
  python build_site.py     # ① 渲染全部文档页（约 4-5 分钟）
  python fixup_links.py    # ② 修补站内绝对路径、中文页缺失锚点
  python package_site.py   # ③ 生成样式/目录/首页/llms 文件并打包 zip
  python check_links.py    # ④ 全站链接自检（应报出 20 处已知断链）
