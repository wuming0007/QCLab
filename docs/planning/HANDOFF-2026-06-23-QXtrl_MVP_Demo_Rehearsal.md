# HANDOFF: QXtrl MVP Demo Rehearsal - Tutorial, Dashboard and Time-Rabi Support

**版本**: v0.1  
**日期**: 2026-06-23  
**状态**: MVP demo rehearsal 准备就绪  
**关联 Session**: 当前长交互会话（L7 实现审查修复、时间 Rabi 支持、简易看板、Tutorial 开发）  
**Worktree**: 主仓库 (当前活跃)  
**Model**: grok-build  
**Context 使用**: 已通过多轮 subagent 规划、审查、漏洞深挖完成关键交付

## 1. 当前总体目标与阶段

**一句话目标**：将 QXtrl 推进到可进行 MVP demo 彩排的阶段。核心是让操作者能够完成“新芯片录入 L0 设置 → 定义 time-rabi 实验（q001 固定幅度扫描 duration） → 提交任务 → 查看任务流与结果可视化 → 回放审查”的完整闭环。产出可直接运行的 Tutorial 和简易看板作为演示入口。

**当前阶段**：
- MVP 薄垂直切片实现阶段（Rabi 必做，virtual backend）。
- 已完成 L7 TRH 核心（typed deterministic VirtualQPU、replay inspect with hash/ownership checks、16/64 support）。
- 新增 L1 time-rabi 支持 + L2 compiler 适配 + L7 虚拟仿真泛化。
- 产出 L9 简易文本看板（显示 L0 设置、任务进度、数据可视化、replay）。
- 产出完整 TUTORIAL.md，面向新手 10 分钟内跑通。
- L0-L9 主干已可支撑 rehearsal（无真实硬件、无 full analysis）。

参考：`QXtrl_MVP最薄垂直切片定义.md`、`QXtrl_第一次讨论会决策清单.md`

## 2. 必须先读的权威文件（新 agent 第一件事）

1. `AGENTS.md`（项目宪法、工作规则、已知命令、gotchas）
2. 本 handoff 文件
3. `docs/planning/QXtrl_架构层号与文档索引.md`（权威 L0-L9 层号与文档归属）
4. `docs/planning/QXtrl_MVP最薄垂直切片定义.md`（MVP 范围、必做链路、验收标准、OUT 清单）
5. `docs/planning/QXtrl模块拆解与接口责任矩阵.md`（模块责任）
6. `docs/planning/QXtrl_L0_API说明.md`（L0 当前 API）
7. `docs/planning/QXtrl_L7_TRH_TwinReplayHIL_设计.md` + 最近四轮审查意见与答复（L7 当前状态）
8. `docs/planning/QXtrl_L9_OI_OperatorInterfaces_设计.md`（L9 设计）
9. `TUTORIAL.md`（新手快速上手主入口）
10. `docs/planning/QXtrl_项目上下文工作流.md` + `HANDOFF_TEMPLATE.md`

**可选但推荐**：
- `docs/planning/QXtrl_L1_Experiment_Language_设计.md`
- `docs/planning/QXtrl_L2_CPIR_Compiler_PulseIR_设计.md`
- `docs/planning/QXtrl_第一次讨论会决策清单.md`
- `CHANGELOG.md`（最近变更历史）

## 3. 已完成工作与关键产物

**核心交付物**：
- **Tutorial**：`TUTORIAL.md`（根目录）—— 新手 5-10 分钟跑通全流程，包括 `simple_dashboard` 一键演示。
- **简易看板**：`qxtrl/examples/simple_dashboard.py` —— 文本看板展示 L0 设置（拓扑/连线/硬件/qubit 参数）、任务流进度、数据表格 + ASCII 振荡图、L7 replay。
- **时间 Rabi 支持**：
  - L0: `make_rabi_lab(qubit_id="q001")`（泛化，支持任意 qubit + 正确线路命名）。
  - L1: `create_time_rabi_experiment_spec(...)`（固定 amplitude + duration scan，明确 drive/readout line）。
  - L2: compiler 泛化支持 `pulse.drive.duration` + sweep bindings。
  - L7: TRH virtual 泛化 `_extract_sweep_values` + deterministic sim，支持 duration 产生衰减振荡。
- L7 TRH 实现已通过四轮审查（cross-run ref、malformed hash、core_refs_present、source_manifest_ref、64-bit hash 支持、duplicate diags 等全部闭合）。
- 代码可执行验证：`python -m qxtrl.examples.simple_dashboard` / `rehearse_time_rabi_q001.py` 可完整跑通并展示 proofs + 负向路径。
- 其他：更新 AGENTS.md、CHANGELOG.md；L0-L9 集成验证通过。

**关键文件变更（本次工作）**：
- qxtrl/cc/examples.py, el/models.py, cpir/compiler.py, cpir/pulse_ir.py, trh/virtual.py
- qxtrl/examples/{simple_dashboard.py, rehearse_time_rabi_q001.py}
- TUTORIAL.md (new)
- 多个 planning 审查答复文档

## 4. 开放项目 / 待决策 / 风险

**MVP 相关开放（来自 MVP 定义）**：
- 真实硬件后端（当前仅 virtual）。
- 完整分析拟合（当前 analyzer 兼容为主，proposal 为 candidate only）。
- L9 更丰富的 CLI / 可视化（当前 dashboard 是薄文本版）。
- 持久化 L0 配置（当前 in-memory + JSON 辅助）。

**开放项（本次）**：
- 将更多 planning 文档（L0/L7/L9 设计 + 审查答复 + MVP 定义等）补入 PR，便于未来 agent 理解上下文。
- 彩排脚本进一步打磨（可视化增强、交互菜单）。
- 确认是否需要 console script entrypoint（`python -m` 当前足够）。

**风险**：
- 工作树仍较脏（legacy 文件多），commit 时需精确 add。
- 中文文件名多，务必用精确路径。
- 64-bit vs 16-bit hash 契约已在 L7 修复，但 store 仍主产 16-bit（MVP 接受）。

## 5. 当前结构化任务状态

使用 todo 跟踪关键项（建议恢复后 sync）：
- MVP demo rehearsal 脚本与 dashboard 已可用。
- L7 四审所有 P1 已修复 + 测试。
- TUTORIAL.md 覆盖用户 envision 的完整故事。

## 6. 最近修改的关键文件

- qxtrl/ 各层实现（见上面）
- TUTORIAL.md
- docs/planning/ 新 HANDOFF + 关键设计文档（本次补录）

## 7. 恢复专用 Prompt 模板

```
你是 QXtrl 项目的新 agent。
严格遵守仓库根部的 AGENTS.md 和 docs/planning/ 下的所有权威文档。

请立即阅读：
- docs/planning/HANDOFF-2026-06-23-QXtrl_MVP_Demo_Rehearsal.md （本 handoff）
- docs/planning/QXtrl_架构层号与文档索引.md
- docs/planning/QXtrl_MVP最薄垂直切片定义.md
- docs/planning/QXtrl_L0_API说明.md
- TUTORIAL.md

当前工作在主仓库。
上次完成到：MVP demo rehearsal 准备就绪（time-rabi + dashboard + tutorial）。
接下来要继续做：根据用户确认的文档清单补 commit/push，或继续打磨彩排脚本 / 真实硬件适配。

请先用一句话确认你已理解当前阶段与约束，然后给出下一步具体行动计划。
```

## 8. 其他上下文备注

- 最近常用命令：`PYTHONPATH=. python -m qxtrl.examples.simple_dashboard`
- 所有变更使用 temp dir 隔离，避免污染 runs/。
- L7 已支持 require_hash_check + cross-run + malformed + 64-bit exact match。
- 推荐新 agent 先跑 dashboard 确认环境。

## 9. 下一步建议行动

1. 读取本 handoff + 列出的核心文档。
2. 运行 `python -m qxtrl.examples.simple_dashboard` 验证 rehearsal 流程。
3. 根据用户确认的文档清单，精确 git add 相关 planning docs + 新 HANDOFF。
4. commit + push feature branch。
5. 准备 PR description（聚焦 MVP demo + tutorial）。

**建议恢复后立刻做的三件事**：
1. 读取本 handoff + MVP 定义 + 架构索引 + L0 API + L7 设计。
2. 运行 dashboard 确认可执行。
3. 用 `todo_write` 同步剩余开放项。

---

**生成者**: Grok (主 agent)  
**生成时间**: 2026-06-23  
**下次更新触发条件**: 用户确认文档清单后 commit 前，或进入下一阶段（真实硬件 / S21）时。

相关链接：
- [AGENTS.md](../../AGENTS.md)
- [TUTORIAL.md](../../TUTORIAL.md)
- [CHANGELOG.md](../../CHANGELOG.md)
- 模板: [HANDOFF_TEMPLATE.md](HANDOFF_TEMPLATE.md)
```