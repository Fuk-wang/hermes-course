/* 由 tools/build_course.py 生成，请勿手改 */
window.COURSE_INDEX = {
 "version": 1,
 "built": "2026-09-22",
 "steps": [
  {
   "id": "installation",
   "num": 1,
   "title": "安装 Hermes Agent",
   "titleEn": "Installation",
   "tagline": "用一行命令把 Hermes 装到电脑或手机上",
   "url": "steps/1-installation.html",
   "total": 5,
   "sections": [
    {
     "id": "s1",
     "h": "这一步在解决什么"
    },
    {
     "id": "s2",
     "h": "先选一条安装路径"
    },
    {
     "id": "s3",
     "h": "Linux / macOS / WSL2：一行安装命令"
    },
    {
     "id": "s4",
     "h": "Windows 原生：在 PowerShell 里安装"
    },
    {
     "id": "s5",
     "h": "Android：在 Termux 里安装"
    },
    {
     "id": "s6",
     "h": "安装程序替你做了什么，东西装到了哪里"
    },
    {
     "id": "s7",
     "h": "装完之后：重载 shell、配好模型、开始聊天"
    },
    {
     "id": "s8",
     "h": "非 sudo / 系统服务用户怎么装"
    },
    {
     "id": "check",
     "h": "验收清单"
    },
    {
     "id": "pitfalls",
     "h": "常见坑"
    }
   ]
  },
  {
   "id": "quickstart",
   "num": 2,
   "title": "第一次对话与基本操作",
   "titleEn": "Quickstart",
   "tagline": "启动后屏幕上看到什么、怎么读、怎么聊",
   "url": "steps/2-quickstart.html",
   "total": 6,
   "sections": [
    {
     "id": "s1",
     "h": "这一步在解决什么"
    },
    {
     "id": "s2",
     "h": "1. 启动：hermes 与 hermes --tui 怎么选"
    },
    {
     "id": "s3",
     "h": "2. 启动横幅：屏幕最上方那几行读什么"
    },
    {
     "id": "s4",
     "h": "3. 状态栏：一行字符里的模型、上下文和费用"
    },
    {
     "id": "s5",
     "h": "4. 第一句 prompt 与运行中的画面"
    },
    {
     "id": "s6",
     "h": "5. 斜杠命令、多行输入与中断"
    },
    {
     "id": "s7",
     "h": "6. 会话保存与恢复"
    },
    {
     "id": "s8",
     "h": "7. 出问题时：六步恢复工具包"
    },
    {
     "id": "check",
     "h": "验收清单"
    },
    {
     "id": "pitfalls",
     "h": "常见坑"
    }
   ]
  },
  {
   "id": "providers",
   "num": 3,
   "title": "给 Hermes 接上模型",
   "titleEn": "Providers / Model Configuration",
   "tagline": "模型写在哪、密钥放哪、怎么验证",
   "url": "steps/3-providers.html",
   "total": 6,
   "sections": [
    {
     "id": "s1",
     "h": "这一步在解决什么"
    },
    {
     "id": "s2",
     "h": "1. 先认清两个文件：config.yaml 管模型，.env 管密钥"
    },
    {
     "id": "s3",
     "h": "2. provider 与 model 到底怎么填"
    },
    {
     "id": "s4",
     "h": "3. API Key 从哪来：控制台申请，写进 .env，变量名必须对"
    },
    {
     "id": "s5",
     "h": "4. 抄三段配置：OpenRouter、Google Gemini、国产直连"
    },
    {
     "id": "s6",
     "h": "5. 本地模型与自托管端点：provider: custom"
    },
    {
     "id": "s7",
     "h": "6. hermes model 与 /model：一个负责配置，一个负责切换"
    },
    {
     "id": "s8",
     "h": "7. 怎么确认换模型真的生效"
    },
    {
     "id": "check",
     "h": "验收清单"
    },
    {
     "id": "pitfalls",
     "h": "常见坑"
    }
   ]
  },
  {
   "id": "cli",
   "num": 4,
   "title": "把命令行用起来",
   "titleEn": "CLI",
   "tagline": "在终端里把 Hermes 用顺手",
   "url": "steps/4-cli.html",
   "total": 6,
   "sections": [
    {
     "id": "s1",
     "h": "这一步在解决什么"
    },
    {
     "id": "s2",
     "h": "两种界面：经典 CLI 与 TUI"
    },
    {
     "id": "s3",
     "h": "启动一个会话：常用参数"
    },
    {
     "id": "s4",
     "h": "界面上有什么：横幅与状态栏"
    },
    {
     "id": "s5",
     "h": "键盘操作：发送、换行、中断"
    },
    {
     "id": "s6",
     "h": "斜杠命令：在输入框里敲 /"
    },
    {
     "id": "s7",
     "h": "非交互用法：一次跑完与管道输入"
    },
    {
     "id": "s8",
     "h": "恢复会话：接着上次继续聊"
    },
    {
     "id": "check",
     "h": "验收清单"
    },
    {
     "id": "pitfalls",
     "h": "常见坑"
    }
   ]
  },
  {
   "id": "configuration",
   "num": 5,
   "title": "把配置理清楚",
   "titleEn": "Configuration",
   "tagline": "看懂 ~/.hermes/ 目录，再动手改配置",
   "url": "steps/5-configuration.html",
   "total": 6,
   "sections": [
    {
     "id": "s1",
     "h": "这一步在解决什么"
    },
    {
     "id": "s2",
     "h": "先认清 ~/.hermes/ 这个目录"
    },
    {
     "id": "s3",
     "h": "谁说了算：配置优先级（precedence）"
    },
    {
     "id": "s4",
     "h": "用 hermes config 查看和修改"
    },
    {
     "id": "s5",
     "h": "在 config.yaml 里引用环境变量"
    },
    {
     "id": "s6",
     "h": "SOUL.md：agent 的身份，以及其他上下文文件"
    },
    {
     "id": "s7",
     "h": "几个你很快会用到的设置键"
    },
    {
     "id": "s8",
     "h": "改完怎么生效"
    },
    {
     "id": "check",
     "h": "验收清单"
    },
    {
     "id": "pitfalls",
     "h": "常见坑"
    }
   ]
  },
  {
   "id": "tools",
   "num": 6,
   "title": "让 Hermes 真的动手干活",
   "titleEn": "Tools",
   "tagline": "工具是它的手，工具集是工具箱",
   "url": "steps/6-tools.html",
   "total": 6,
   "sections": [
    {
     "id": "s1",
     "h": "这一步在解决什么"
    },
    {
     "id": "s2",
     "h": "工具与工具集：一个管「能做什么」，一个管「给谁做」"
    },
    {
     "id": "s3",
     "h": "先看清：这个会话到底有哪些工具"
    },
    {
     "id": "s4",
     "h": "终端与代码执行：最能干，也最需要看住"
    },
    {
     "id": "s5",
     "h": "它是怎么自己一步步做完的：Agent 循环的直观版"
    },
    {
     "id": "s6",
     "h": "练手任务：一句话让它读 CSV 并汇总"
    },
    {
     "id": "s7",
     "h": "怎么扩：技能打底，MCP 接外"
    },
    {
     "id": "check",
     "h": "验收清单"
    },
    {
     "id": "pitfalls",
     "h": "常见坑"
    }
   ]
  }
 ]
};
