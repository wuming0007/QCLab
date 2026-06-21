# QXtrl 项目上下文工作流

**版本**: v0.2  
**日期**: 2026-06-07（初始采纳）；2026-06-21（演进记录）  
**状态**: 已采纳的轻量可演进工作流  
**参考**: 用户提供链接 `https://neolithic.usay.dev/posts/evolving-workflow`（Tom Harada 的 "An Evolving Context Workflow"）。

> **当前操作规则请以 `AGENTS.md` §5 "Development And Documentation Workflow" 为准**。  
> 本文档主要记录**起源、决策理由、适配过程和后续演进历史**。日常使用规则已收敛到 AGENTS.md 以减少重复并保持其作为 agent 必读入口的简洁性。  

## 1. 工作流解读

该工作流的核心不是“多写几个文档”，而是把项目上下文分成不同作用域，让人和 agent 每次进入项目时都能快速定位：

| 层 | 文件 | 作用 |
| --- | --- | --- |
| 项目上下文 | `AGENTS.md` | 当前项目是什么、目录怎么走、有哪些约定、有哪些坑、应该如何维护上下文 |
| 可复用模板 | `template.md` | 当前项目里沉淀出的架构模式、接口写法、决策清单和验收套路 |
| 私有经验 | `~/learnings` 或本地私有文件 | 个人或内部经验，不进入公开仓库 |
| 变化记录 | `CHANGELOG.md` | 记录改了什么、为什么改，给后续人和 agent 一个压缩历史 |
| 自动提醒 | git hook | 在提交后提醒维护上下文和 changelog |

它解决的问题很直接：agent 没有可靠的跨会话长期记忆，团队成员也不可能每次都从头读完所有规划文档。`AGENTS.md` 相当于“进入项目的门口地图”；`template.md` 相当于“我们做这类设计时的固定手法”；`CHANGELOG.md` 则记录上下文为什么变成今天这样。

## 2. 对本项目的适配判断

我建议采纳，但不是原样照搬，而是轻量采纳。

适合的原因：

1. QXtrl 当前处于架构快速演进期，层号、模块边界、MVP 范围、接口命名都需要稳定传递。
2. 项目中已有大量历史代码、文档、PPT、配置、驱动和规划文件，新参与者很容易迷路。
3. 后续很可能多人和多个 agent 协作，缺少入口上下文会造成重复解释和风格漂移。
4. 本项目有 IP、数据、硬件安全和 AI 权限边界，必须有一个 public-safe 的约定入口。
5. 目前已经有 `CHANGELOG.md`，引入成本不高。

需要改造的地方：

1. 原文中的 `~/learnings` 更适合个人机器，不应强行进入仓库。
2. 本项目包含敏感实验室和潜在商业信息，必须明确 `AGENTS.md` 只放 public-safe 内容。
3. 自动 git hook 暂不强制安装，先用文档和人工/agent 习惯建立纪律。
4. QXtrl 已有大量规划文档，`AGENTS.md` 不应替代它们，只做入口索引和当前约定摘要。

## 3. 本项目采纳方式

初始（2026-06-07）已落地：

| 文件 | 状态 | 说明 |
| --- | --- | --- |
| `AGENTS.md` | 新增 | 项目入口上下文，供 agent 和新协作者快速定向 |
| `template.md` | 新增 | QXtrl 架构/API/模块设计的可复用模板 |
| `.gitignore` | 更新 | 增加 `AGENTS.private.md` 和 `.local-learnings/`，隔离私有上下文 |
| `CHANGELOG.md` | 更新 | 记录本次工作流引入 |
| `docs/planning/QXtrl_项目上下文工作流.md` | 新增 | 本说明文档（起源与 rationale） |

后续演进（见 §7）：

| 文件 | 状态 | 说明 |
| --- | --- | --- |
| `docs/planning/HANDOFF_TEMPLATE.md` | 新增 (2026-06-21) | 跨 session/agent 状态快照模板 + 使用指南，解决配额切换痛点 |
| `AGENTS.md` | 更新 | 收敛日常规则 + 新增 "Evolvable Context Maintenance Layers" 表格 |

暂不做的事项：

| 项目 | 原因 | 后续条件 |
| --- | --- | --- |
| 自动安装 `.git/hooks/post-commit` | 当前不宜悄悄改变提交行为，且 `.git` 不应纳入项目文件 | 团队确认后再安装或提供脚本 |
| 建立仓库内私有知识库 | 私有上下文不应进入可交付项目 | 可在个人目录或公司内部受控知识库维护 |
| 把所有规划文档重写为同一模板 | 会造成不必要 churn | 新文档先用，旧文档按需迁移 |

## 4. 历史版日常使用规则（2026-06-07 采纳时）

> **注意**：以下规则的**当前可操作版本**已收敛到 `AGENTS.md` 第 5 节（Development And Documentation Workflow + Evolvable Context Maintenance Layers）。  
> 保留此处是为了展示初始设计意图。

### 4.1 开始任务前（历史）

1. 先读 `AGENTS.md`，确认当前架构约定和文件地图。
2. 若任务涉及模块设计、接口定义、架构文档，参考 `template.md`。
3. 若任务涉及层号或文档归属，以 `docs/planning/QXtrl_架构层号与文档索引.md` 为准。

### 4.2 完成重要变更后（历史）

需要检查三件事：

1. `AGENTS.md` 是否需要更新...
2. `template.md` 是否需要更新...
3. `CHANGELOG.md` 是否需要记录...

### 4.3 私有信息处理（历史）

（内容同上，参见 `AGENTS.md` §5.4）

## 5. 进入正式研发后的增强建议（历史）

| 阶段 | 建议 |
| --- | --- |
| 架构讨论期 | 手工维护 `AGENTS.md`、`template.md`、`CHANGELOG.md` 即可 |
| MVP 开发期 | 增加轻量 post-commit 提醒脚本，提示更新上下文和 changelog |
| 多人协作期 | 在 PR 模板中加入“是否需要更新 AGENTS/template/changelog” |
| 商业交付期 | 将上下文维护纳入发布检查清单，避免交付包带入私有上下文 |

## 6. 我的意见（2026-06-07）

这套工作流值得接纳。它和 QXtrl 当前的“契约先行、边界清晰、可审查、可交接”思路相当吻合，而且成本很低。

但它不能替代正式设计文档、测试和审查。正确用法是：`AGENTS.md` 负责让人快速进场，`template.md` 负责让新文档不跑偏，`CHANGELOG.md` 负责记录演进脉络，真正的技术契约仍然落在 PRD、模块矩阵、L0 规则、API 文档和测试中。

## 7. 后续演进记录

### 2026-06-21：HANDOFF_TEMPLATE 作为跨 agent 连续性的演进

在实际使用长会话进行复杂规划（如 P0 决策会、PPT 生成、多轮讨论）后，暴露了新痛点：

- Token 配额经常迫使在多个 Grok session / agent 之间切换。
- 单纯依赖聊天历史或手动复制上下文效率低、容易污染或丢失关键约束。
- 即使有 AGENTS.md + planning 文档，新 agent 仍然需要“当前阶段快照”（做了什么、开放什么、推荐怎么恢复）。

**演进动作**：
- 新增 `docs/planning/HANDOFF_TEMPLATE.md`（同时包含使用指南和可实例化的模板）。
- 它成为“Evolvable Context Maintenance Layers”中的新层：**Cross-session Continuity**。
- 在 AGENTS.md 中新增 “5.5 Evolvable Context Maintenance Layers” 表格，显式把 AGENTS.md、项目上下文工作流文档、CHANGELOG、HANDOFF_TEMPLATE、template.md 串起来。
- 日常规则（开始前 / 变更后检查）已收敛到 AGENTS.md，避免两个文档长期漂移。
- HANDOFF 使用时机：重要阶段结束、准备 `/compact`、`/fork --worktree`、切换模型、长时间中断、主子 agent 同步等。

这正是“可演进工作流”的体现：当新的摩擦（跨 agent 切换）出现时，引入最小新机制（handoff 文件 + 模板），并更新入口文档（AGENTS）使其可见。

### 未来可能的演进方向

- 当多人或多 agent 并行开发更频繁时，考虑把 handoff 产出纳入变更检查清单。
- 如果需要，增加轻量自动化（例如 skills 或 hooks）来提示/生成 handoff。
- 继续把可操作内容往 AGENTS.md 收敛，把历史/rationale 留在本规划文档。

当前实践已经证明：分层（现时操作 vs 历史 rationale vs 日志 vs 状态传递）比把一切塞进一个文件更可持续。

