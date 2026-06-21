# QCLab 项目日志

## [2026-06-21] - 新增 HANDOFF_TEMPLATE.md 支撑多 agent 无缝切换

### 新增内容
- 新增 `docs/planning/HANDOFF_TEMPLATE.md`（内置完整使用指南），用于因 token 配额、上下文污染在多个 agent / session 之间切换时实现低摩擦恢复。
- 模板包含：生成时机、恢复优先级（resume > fork --worktree > 新 session + prompt）、必须先读文件清单、结构化决策/待办表格、专用恢复 prompt 模板、与 `/compact`、`/flush`、worktree、subagent、todo_write 的配合方式。
- 在 `AGENTS.md` High-Value File Map 中登记该模板。

### 背景与价值
长周期复杂项目（如 QXtrl 规划与后续实现）经常需要跨多个 Grok session/agent 工作。纯聊天历史恢复成本高。本模板配合现有 `AGENTS.md` + `docs/planning/` 规划文档体系，让新 agent 能快速拿到正确约束和当前状态，最大化利用有限配额。

### 使用触发
重要阶段结束、准备 `/compact` 或切换 worktree / 模型 / session 前，主动让 agent 产出带日期的 handoff 文件。

## [2026-06-07] - 引入演化式项目上下文工作流

### 新增内容
- 新增 `AGENTS.md`，作为项目级 agent / 协作者入口上下文。
- 新增 `template.md`，沉淀 QXtrl 架构、API、模块设计的可复用写法。
- 新增 `docs/planning/QXtrl_项目上下文工作流.md`，记录工作流解读、采纳理由和本项目适配方式。

### 工作流约定（初始）
- 重要结构、架构权威、命令或协作规则变化时，更新 `AGENTS.md`。
- 形成可复用设计模式或检查清单时，更新 `template.md`。
- 重要项目变更继续记录在 `CHANGELOG.md`。
- 私有上下文放入 `AGENTS.private.md` 或 `.local-learnings/`，不进入版本控制。

> 后续演进见 2026-06-21 条目及 `docs/planning/QXtrl_项目上下文工作流.md` §7。日常操作规则已收敛到 `AGENTS.md`。

### 设计理由
- QXtrl 当前处于架构快速演进和多文档协作阶段，需要一个轻量、可持续更新的入口上下文，降低后续人员和 agent 的重复理解成本。

## [2024-12-19] - 初始环境配置

### 新增功能
- 创建Python 3.12.11虚拟环境 `venv-qc`
- 配置清华镜像源以加速包下载
- 安装quarkstudio[full]完整版量子计算开发环境

### 技术细节
- **虚拟环境**: 使用uv创建，命名为`venv-qc`
- **Python版本**: 3.12.11
- **包管理器**: uv
- **镜像源**: https://pypi.tuna.tsinghua.edu.cn/simple

### 安装的主要依赖包
- **quarkstudio==7.1.8** - 量子计算工作室主程序
- **qlisp==1.1.5** - 量子Lisp编程语言
- **qlispc==1.2.0** - 量子Lisp编译器
- **qwark==1.2.1** - 量子工作流框架
- **vios==3.4.5** - 虚拟仪器操作系统
- **waveforms==2.1.0** - 波形处理库
- **axion==4.4.2** - 量子计算框架
- **anyon==4.7.5** - 任意子模拟库

### 其他重要依赖
- numpy==2.3.1 - 数值计算
- scipy==1.16.0 - 科学计算
- matplotlib==3.10.3 - 数据可视化
- PySide6==6.9.1 - GUI框架
- vispy==0.15.2 - 高性能可视化
- h5py==3.14.0 - HDF5文件格式支持

### 安装命令
```bash
# 创建虚拟环境
uv venv venv-qc --python 3.12

# 激活虚拟环境并安装依赖
source venv-qc/bin/activate
uv pip install "quarkstudio[full]" --index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

### 环境状态
- ✅ 虚拟环境创建成功
- ✅ 清华镜像源配置完成
- ✅ quarkstudio[full]安装完成
- ✅ 所有依赖包安装成功 (共99个包)

### 下一步计划
- [ ] 创建示例量子计算项目
- [ ] 配置开发环境
- [ ] 编写使用文档

## [2024-12-19] - 文档下载

### 新增功能
- 下载 QuarkStudio 官方文档和教程
- 创建本地文档目录结构

### 下载内容
- **quarkstudio_docs/index.html** - 官方文档主页 (40.5KB)
- **quarkstudio_docs/quarkstudio_tutorial.html** - 教程页面 (67KB)
- **quarkstudio_docs/README.md** - 文档说明文件

### 原始链接
- 官方文档: https://quarkstudio.readthedocs.io/
- 教程页面: https://quarkstudio.readthedocs.io/en/latest/usage/tutorial/

### 文档状态
- ✅ 主页文档下载完成
- ✅ 教程页面下载完成
- ✅ 文档说明文件创建完成

## [2024-12-19] - HTML转Markdown

### 新增功能
- 安装html2text工具进行HTML到Markdown转换
- 创建自定义转换脚本 `convert_html_to_md.py`
- 将HTML文档转换为Markdown格式

### 转换内容
- **quarkstudio_docs/index.md** (7KB) - 主页文档的Markdown版本
- **quarkstudio_docs/tutorial.md** (8.5KB) - 教程文档的Markdown版本

### 技术细节
- **转换工具**: html2text==2025.4.15
- **转换脚本**: 自定义Python脚本，支持内容清理和格式优化
- **转换特性**: 
  - 自动提取主要内容区域
  - 清理HTML标签和脚本
  - 保持链接和图片引用
  - 优化Markdown格式

### 转换状态
- ✅ HTML到Markdown转换完成
- ✅ 文档格式优化完成
- ✅ README文件更新完成

## [2024-12-19] - QLisp语法分析

### 新增功能
- 深入分析QLisp量子线路语法规范
- 创建详细的语法指南文档
- 开发QLisp使用示例脚本

### 分析内容
- **qlisp_syntax_guide.md** - 完整的QLisp语法指南
- **qlisp_examples.py** - 实用的示例脚本

### 语法特性
- **量子门**: H, sigmaX, sigmaY, sigmaZ, S, Sdag, T, Tdag, CX, CZ, SWAP等
- **Bell态**: phiplus, phiminus, psiplus, psiminus等
- **预定义电路**: QPT, QST, XY4, XY8, XY16, Ramsey等
- **工具函数**: draw(), seq2mat(), kak_decomposition()等

### 语法规范
- 单比特门: `(gate, qubit)`
- 双比特门: `(gate, (qubit1, qubit2))`
- 测量操作: `(measure, qubit)`
- 电路表示: 列表形式 `[(gate1, qubit1), (gate2, qubit2), ...]`

### 分析状态
- ✅ QLisp库结构分析完成
- ✅ 语法指南编写完成
- ✅ 示例脚本开发完成
- ✅ 语法规范验证完成 
