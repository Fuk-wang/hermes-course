Hermes 学习站（赛博风 · 离线自包含）
=====================================================

这是什么
  一套可以离线打开、也可以直接部署的 Hermes Agent 学习站，深色赛博风，可交互：

  index.html              枢纽页 —— 这个站是什么、主题卡、进入学习路径
  path.html               学习路径总览 —— 进度环 + 六个阶段卡片 + 本机进度
  steps/1..6-*.html       六个阶段的详情页（每页 6-7 节讲解，共 35 项验收）
  docs/index.html         文档总目录，776 篇，支持关键词即时过滤
  docs/                   官方文档镜像（中文 314 篇 + 英文 462 篇）
  assets/style.css        全站唯一样式表（枢纽页 + 详情页 + 文档镜像共用）
  assets/site.js          交互层（进度、搜索面板、目录高亮、复制、主题切换）
  assets/course-index.js  搜索面板的内容索引（由构建脚本生成）
  assets/img/             文档引用的图片
  llms.txt / llms-full.txt 页面索引与全部文档源码合集（纯文本，可作离线语料）
  tools/                  构建与自检脚本，可重复生成
  _content/               六步教程的内容源（构建输入，不参与部署）

六个阶段
  1 安装 Hermes Agent        装好它，并确认它能启动
  2 第一次对话与基本操作      启动后屏幕上有什么、怎么读、怎么退出
  3 给 Hermes 接上模型        配置文件、API Key、模型 id 到底填在哪
  4 把命令行用起来            CLI 与 TUI、斜杠命令、非交互用法
  5 把配置理清楚              ~/.hermes/ 里每个文件各管什么
  6 让 Hermes 真的动手干活    工具与工具集、它怎么一步步做事、怎么扩

  每个阶段页都包含：学习目标、逐节讲解、可直接复制的命令、常见坑，
  以及一份可以打勾的验收清单。进度存在浏览器 localStorage，关掉页面不丢。

怎么用
  方式一（最简单）：双击 index.html，用浏览器打开，页面内链接本地即可跳转。
  方式二（推荐，部署到服务器/内网）：
      cd C:\Users\79305\Desktop\hermes-course-site
      python -m http.server 8000
      浏览器访问 http://localhost:8000/
  部署到 Nginx / IIS / 校园服务器：把本目录整体上传到网站根目录即可，
  全部为静态文件，无需数据库、无需 Node、无需联网。

三个入口
  index.html          首页（枢纽）
  path.html           学习路径总览
  docs/index.html     文档总目录（也可以从任意页顶栏进入）

快捷键与交互
  Ctrl + K / ⌘ + K    打开搜索面板，可搜阶段、小节、关键词
  /                   同样可以唤起搜索面板（光标不在输入框里时）
  ↑ ↓ / Enter         在面板里选择与跳转，Esc 关闭
  右上角两个按钮       搜索与深浅主题切换（选择会记住）
  验收清单            点一下打勾，再点取消；「重置本步」清空本步
  代码块              点「复制」一键复制命令

链接说明
  1. 六个阶段页里的「官方文档」链接指向站内镜像（docs/**.html），离线可跳；
     鼠标悬停能看到对应的官网原文地址。
  2. 文档页之间的交叉链接同样已本地化，点击在站内跳转。
  3. 文档里指向 GitHub、Discord 等站外链接保持原样，标记为 ↗，需要联网才能打开
     —— 这部分无法离线镜像，属于第三方资源。

内容来源与版本
  文档内容来自本机 Hermes Agent 安装目录中的官方文档源码：
      C:\Users\79305\AppData\Local\hermes\hermes-agent\website
  版本：Hermes Agent v0.21.3 (2026.9.14) · upstream b5251aa4
  站点 v2（赛博风重做）构建日期：2026-09-22

已知的断链（都来自官方文档源码本身，不影响课程使用）
  · 14 处指向技能页/源码文件的链接：目标页面在文档源码树里根本没有对应文件
    （13 个技能目录链接 + 1 处 rl-training.md）
  · 3 处锚点：中文页与英文页都没有对应小节
  · 1282 处站外链接（GitHub、Discord 等）保持原样，标记 ↗，需要联网
  （原先 3 处 /docs/img 素材断链已修：素材拷进 assets/img，链接改写为相对路径；
    另有 7 处根绝对路径链接已由 fixup_deep_links.py 修好。
    六个阶段页与枢纽/路径页本身：0 断链）

重新构建
  # v2 学习站（枢纽 + 路径 + 六个阶段页 + 注入文档页脚本），几秒钟
  python tools/build_course.py            # 生成；--check 只校验不写文件
  python tools/fixup_deep_links.py        # 修补文档镜像里残留的根绝对路径链接
  python tools/package_course.py          # 打包 -> 桌面 hermes-course-site.zip
  python tools/check_links.py             # 全站链接与锚点自检

  # 文档镜像本身若要重渲染（约 4-5 分钟，正常情况不需要跑）
  cd tools
  python build_site.py                    # 由官网文档源码重渲染 776 篇
  python fixup_links.py                   # 修补站内绝对路径与缺失锚点
  # 注意：旧版 package_site.py 会覆盖 index.html 并重建旧样式，v2 已不再使用；
  #      它现在会检测到 v2 首页并拒绝运行，避免误覆盖。

  想改教程文字：只改 _content/step-*.json 里对应字段，然后重跑 build_course.py。
  想改外观：只改 assets/style.css —— 文档镜像引用的就是它，换掉即整站换肤。
