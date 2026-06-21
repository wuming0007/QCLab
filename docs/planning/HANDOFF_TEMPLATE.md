# QXtrl Agent / Session Handoff 模板与使用指南

**版本**: v0.1  
**日期**: 2026-06-21  
**状态**: 初始模板  
**目的**: 解决长周期复杂项目中因 token 配额、上下文污染需要跨多个 agent/session 切换时的无缝衔接问题。提供结构化、可机器/人工快速消费的状态快照。

---

## 使用指南

### 1. 这是什么？解决什么问题？

在大项目开发中（尤其是 QXtrl 这种架构先行、多层契约、需要反复 review 的工作），单个 Grok session 很容易因为上下文增长、自动 compact 或配额限制而被迫切换。

单纯依赖聊天历史恢复成本极高（要重复读 AGENTS.md + 大量规划文档）。

本模板的目标是：**让任何新 agent 在 30 秒内就能以正确姿态继续工作**。

### 2. 何时必须产出/更新 Handoff 文件？

- 一个重要阶段/里程碑即将结束（例如 P0 决策拍板后、MVP 某个切片完成前）
- 准备切换到新 session、fork、或新 worktree
- 上下文使用率已接近 70%+，准备主动 `/compact`
- 即将长时间中断（吃饭、睡觉、切换机器）
- 主 agent 把工作委托给子 agent（`spawn_subagent`）后，需要把主线状态同步出来
- 跨模型切换（例如从 grok-build 切换到其它模型）

**小任务**（单文件修改、简单 bug）不需要。

### 3. 如何生成与维护？

1. 在当前 session 里对 agent 说：
   > “基于 `docs/planning/HANDOFF_TEMPLATE.md` 生成一个新的 handoff 文件，文件名带今天日期和当前阶段简述。把当前状态完整填进去。”

2. 同时执行：
   - `/flush`（若 memory 已启用，把关键知识固化）
   - 让 agent 用 `todo_write` 更新任务状态
   - 如果在改代码，考虑是否需要切 worktree

3. 文件命名推荐：
   - `HANDOFF-2026-06-21-P0决策后.md`
   - `HANDOFF-2026-06-21-MVP-Rabi-第一轮.md`
   - `HANDOFF-2026-06-21-当前.md` （临时占位，重要节点再重命名存档）

4. 位置：全部放在 `docs/planning/` 下，便于被 AGENTS.md 索引和 agent 自动发现。

5. 提交：建议 git add/commit，或至少保留在工作区供下次恢复。

### 4. 恢复时的推荐做法（优先级从高到低）

1. **最佳**：使用原 session ID
   - TUI 内：`/resume`
   - CLI：`grok --resume <session-id>` 或 `grok -c`（最近）
   - 然后阅读最新 handoff 文件

2. **优秀**：从当前 session fork
   - `/fork --worktree "继续做 XXX"`
   - 新 session 会继承历史，同时获得独立上下文预算和隔离目录

3. **可接受**：全新 session + 显式 prompt
   - 启动后第一条消息直接粘贴 handoff 文件内容 + 下面提供的“恢复专用 Prompt 模板”
   - 或者：`grok --worktree=branch-name "根据 docs/planning/HANDOFF-xxx.md 继续..."`

4. 无论哪种方式，**第一件事**永远是让 agent 读取：
   - `AGENTS.md`
   - 本 handoff 文件
   - `docs/planning/` 下核心权威文档（见下方“必须先读”清单）

### 5. 与现有机制的配合关系

| 机制               | 在 Handoff 场景中的角色                              | 建议动作 |
|--------------------|-----------------------------------------------------|----------|
| `AGENTS.md`        | 项目宪法，永远先读                                 | Handoff 中明确列出 |
| `docs/planning/` 系列 | 单一事实源（架构、决策、MVP、模块矩阵等）         | Handoff 里列出具体要读哪些 |
| `todo_write` 工具  | 结构化行动项，跨会话持久                           | 每次 handoff 前更新 |
| `/compact`         | 压缩历史，减少 token                               | 产出 handoff 后再 compact |
| `/flush` + Memory  | 跨 session 隐式记忆                               | 产出 handoff 前执行 |
| `spawn_subagent`   | 并行工作（推荐优先用它而不是开新顶层 session）   | 子 agent 完成后，主线产出 handoff |
| Worktree (`/fork --worktree`, `grok -w`) | 物理文件隔离，避免冲突                            | 记录 worktree 名称 |
| `/session-info`    | 查看当前 session 元数据                            | Handoff 里记录 session-id、model、turn 数 |

### 6. 最佳实践

- **简洁但完整**：目标是让新 agent 读完 handoff + 2-3 个规划文档就能开工，不要把所有历史抄一遍。
- **链接优先**：多用相对链接指向 `docs/planning/xxx.md`，少重复内容。
- **决策与开放问题**：尽量引用 `QXtrl_第一次讨论会决策清单.md` 中的 D-xxx。
- **可执行下一步**：每个开放项都要有 Owner + 建议截止 + 预期输出。
- **定期演进**：当发现某个 handoff 缺少关键信息时，更新本模板并记录到 CHANGELOG。
- 配合 `/btw` 把临时想法发给当前 agent，而不污染主线程。

---

## Handoff 模板（可直接复制使用）

```markdown
# HANDOFF: <阶段简述> - <日期>

**版本**: v0.1  
**日期**: 2026-06-21  
**状态**: 进行中 / 已暂停 / 待恢复  
**关联 Session**: <session-id 或 "当前正在交互的 session">  
**Worktree**: <worktree 名称 或 "主仓库">  
**Model**: grok-build / <其他>  
**Context 使用**: <约 X% / 使用 /session-info 查看>  

## 1. 当前总体目标与阶段

一句话描述本次要达成的结果（例如：完成 P0 决策拍板所有行动项的分配与初步实施；或 Rabi 虚拟后端端到端跑通）。

当前所处阶段（参考 MVP 定义或 implementation_plan）：

## 2. 必须先读的权威文件（新 agent 第一件事）

1. `AGENTS.md`（项目入口与工作规则）
2. 本 handoff 文件
3. `docs/planning/QXtrl_架构层号与文档索引.md`
4. `docs/planning/QXtrl模块拆解与接口责任矩阵.md`
5. `docs/planning/QXtrl_第一次讨论会决策清单.md`（重点看未闭合的 D-xxx）
6. `docs/planning/QXtrl_MVP最薄垂直切片定义.md`
7. `docs/planning/<本次阶段最相关的 PRD 或设计文档>`

**可选但推荐**：`QXtrl_项目上下文工作流.md`、`template.md`

## 3. 已完成工作与关键产物

- [ ] 已拍板/已实现的内容（列 3-6 条最重要）
- 产出的文件（带路径）：
  - `docs/planning/QXtrl_P0_决策拍板会.pptx`（已更新行动项分配表）
  - ...
- 代码/实验状态：
  - Virtual backend 已支持 Rabi 基本流程
  - ...

## 4. 开放项目 / 待决策 / 风险

使用表格，优先引用已有决策 ID：

| ID / 类型 | 主题 | 当前状态 | 推荐方向 | Owner | 建议截止 | 备注 |
|-----------|------|----------|----------|-------|----------|------|
| D-004     | Demo 范围 | 讨论中 | Rabi 必做，S21 可选 | 产品负责人 | 会后 1 天 | ... |
| TODO-017  | ... | 阻塞 | ... | ... | ... | 依赖 D-008 |
| Q-??      | ... | ... | ... | ... | ... | ... |

**高风险项**：
- ...

## 5. 当前结构化任务状态（来自 todo_write）

（如果有活跃的 todo 列表，请在此粘贴或总结关键 open items）

## 6. 最近修改的关键文件

列出本次会话或阶段内真正改动过的文件（便于 review 与 rewind）：

- docs/planning/...
- ...

## 7. 恢复专用 Prompt 模板（直接复制给新 session 用）

```
你是 QXtrl 项目的新 agent。

严格遵守仓库根部的 AGENTS.md 和 docs/planning/ 下的所有权威文档。

请立即阅读：
- docs/planning/HANDOFF-2026-06-21-xxx.md （本 handoff）
- docs/planning/QXtrl_架构层号与文档索引.md
- docs/planning/QXtrl_第一次讨论会决策清单.md
- docs/planning/QXtrl_MVP最薄垂直切片定义.md

当前工作在 <worktree 或主目录>。

上次完成到：...
接下来要继续做：...

请先用一句话确认你已理解当前阶段与约束，然后给出下一步具体行动计划（不要重新介绍项目）。
```

## 8. 其他上下文备注

- 最近用过的命令/构建方式：`uv run ...`
- 特殊权限或注意事项：
- 关联的子 agent / fork session：
- Memory 已 flush：是 / 否
- 计划下次 compact 时间点：

## 9. 下一步建议行动

1. ...
2. ...
3. ...

**建议恢复后立刻做的三件事**：
1. 读取本 handoff + 上面列出的 3 个核心文档
2. 运行 `/context` 和 `/session-info` 确认环境
3. 用 `todo_write` 把开放项同步到工具状态

---
**生成者**: <当前 agent / 人>  
**生成时间**: 2026-06-21 xx:xx  
**下次更新触发条件**: <例如：完成 D-001~D-005 后，或下次重大 compact 前>
```

---

## 附录：轻量版单文件 Handoff（极简场景）

如果只是临时切换，不想新建文件，可把上面模板的核心表格 + “必须先读” + “恢复 Prompt” 三段直接贴到聊天里或 `/remember`，但**正式项目阶段推荐始终落盘**。

---

**维护说明**：本模板是“可演进上下文工作流”的一部分（见 `QXtrl_项目上下文工作流.md` §7）。当发现新切换摩擦时，更新本模板 + `AGENTS.md`（尤其是 Layers 表格和 workflow 规则）。

相关链接（相对本目录）：
- [AGENTS.md](../../AGENTS.md)（当前操作入口，必读）
- [QXtrl_项目上下文工作流.md](QXtrl_项目上下文工作流.md)（起源 rationale + 演进历史）
- [template.md](../../template.md)
- [CHANGELOG.md](../../CHANGELOG.md)
```