# QXtrl 架构层号与文档索引

**版本**: v0.1  
**日期**: 2026-06-02  
**状态**: 草案，供第一次规划讨论会拍板  
**目的**: 冻结 QXtrl 当前规划中的权威层号、稳定命名和文档归属，解决 L2/L3 历史漂移导致的协作歧义。  

## 1. 使用原则

1. **稳定名称优先，层号辅助**：研发沟通和代码包名优先使用稳定英文名（如 `Core Contracts`、`Experiment Language`）；短码（CC、EL 等）用于代码包/子模块名（`qxtrl/cc`、`qxtrl/el` 等小写）；`L0-L9` 用于文档索引和责任矩阵。
2. **本文件作为层号与文档归属的唯一事实源**：若旧文档标题或正文层号与本文件冲突，以本文件为准。
3. **旧文档先标注，再重命名**：正式开发前可以先在旧文档顶部增加“历史层号说明”；重命名文件需一次性完成并更新交叉引用。
4. **3+1 是产品架构视图，L0-L9 是研发责任矩阵**：两者不是竞争关系，而是给不同沟通场景使用的两张地图。

## 2. 3+1 产品架构视图

| 大层 | 稳定名称 | 吸收层级 | 核心职责 | 明确不负责 |
| --- | --- | --- | --- | --- |
| +1 | Contract Discipline / 契约纪律 (短码横切) | L0 横切所有层 | schema、命名、单位、版本、安全策略、错误模型、运行记录规范 | 具体执行、存储引擎、UI 展示 |
| 1 | Execution Backend / 执行底座 (EB) | 主要 L3，部分 L7 | 接收已验证 `CompiledBundle`，管理真实/虚拟/回放/HIL 后端，返回状态与采集结果 | 实验语义、校准决策、AI 决策、参数晋升 |
| 2 | Runtime & Middleware / 运行中台 (RS + EL + CPIR + DS + CO) | L1/L2/L4/L5/L6，部分 L7/L8 | 实验解析、编译、调度、数据状态、校准闭环、Twin/AI 安全入口 | 绕过契约直接操作硬件，或在 UI 内写核心状态 |
| 3 | Frontend Workbench / 交互工作台 (OI) | L9 | 任务编排、数据可视化、参数 review、波形 review、诊断与交付界面 | 拟合事实源、参数写回、硬件直接控制 |

## 3. 权威 L0-L9 层号表

| 层号 | 短码 | 稳定英文名 | 中文名 | 主要对象 / 接口 | 备注 |
| --- | --- | --- | --- | --- |
| L0 | CC | Core Contracts | 核心契约 | `HardwareInventory`、`ChipModel`、`WiringGraph`、`SafetyPolicy`、`DomainError` | 所有层必须遵守；不实现业务逻辑。代码包/模块：`qxtrl/cc` |
| L1 | EL | Experiment Language | 实验语言 | `ExperimentSpec`、`AtomSpec`、`TaskSpec`、`SessionSpec`、PDCA | 描述意图，不携带最终 waveform ndarray。代码包/模块：`qxtrl/el` |
| L2 | CPIR | Compiler / Pulse IR | 编译器与脉冲中间表示 | `PulseIR`、`FrameEvent`、`PulseMoment`、`CompiledBundle`、`CompileDiagnostic` | 当前权威含义：编译器、IR、延迟绑定。代码包/模块：`qxtrl/cpir` |
| L3 | EB | Execution Backend | 执行后端 | `ExecutionBackend`、`BackendCapability`、`BackendRunResult`、HAL、设备插件 | 当前权威含义：真实/虚拟/回放/HIL 执行。代码包/模块：`qxtrl/eb` |
| L4 | RS | Runtime & Scheduler | 运行时与调度器 | `RunRequest`、`RunState`、`RunEvent`、资源锁、取消、重试 | 不做拟合，不决定参数是否晋升。代码包/模块：`qxtrl/rs` |
| L5 | DS | Data & State | 数据与状态 | `ConfigStore`、`ResultStore`、`DataSink`、`RunManifest` | 三类数据边界必须由测试强制。代码包/模块：`qxtrl/ds` |
| L6 | CO | Calibration & Optimization | 校准与优化 | `CalibrationPlan`、`CalibrationRecord`、`Observation`、`ParameterPatchProposal`、Blackboard | 搜索期不得污染在线 `ConfigStore`。代码包/模块：`qxtrl/co` |
| L7 | TRH | Twin / Replay / HIL | 数字孪生、回放与硬件在环 | `VirtualQPU`、`VirtualInstrument`、`ReplayBackend`、`TwinModel` | 不能替代真实硬件发布验收。代码包/模块：`qxtrl/trh` |
| L8 | ADG | AI & Diagnostics Gateway | AI 与诊断网关 | `ActionProposal`、策略门、诊断知识库、证据链 | AI 不直接调用设备命令。代码包/模块：`qxtrl/adg` |
| L9 | OI | Operator Interfaces | 操作员接口 | CLI、Python SDK、Web Console、诊断包、交付工具 | 不绕过核心 API 操作硬件。代码包/模块：`qxtrl/oi` |

## 4. 包/模块与 Schema 版本命名约定

为避免层号漂移导致的协作问题，代码实现使用**短码小写**作为包/子模块名：

- L0 / CC → `qxtrl/cc`
- L1 / EL → `qxtrl/el`
- L2 / CPIR → `qxtrl/cpir`
- L3 / EB → `qxtrl/eb`
- L4 / RS → `qxtrl/rs`
- L5 / DS → `qxtrl/ds`
- L6 / CO → `qxtrl/co`
- L7 / TRH → `qxtrl/trh`
- L8 / ADG → `qxtrl/adg`
- L9 / OI → `qxtrl/oi`

Schema version 格式相应采用模块前缀，例如：
- `qxtrl.cc.<ObjectName>/v<major>.<minor>`
- `qxtrl.el.ExperimentSpec/v0.1`
- `qxtrl.cpir.PulseIR/v0.1`

文档中仍可使用稳定英文名 + 层号；代码包名优先用短码。

## 5. 历史层号迁移说明

早期 05-29 文档中曾使用：

- L2 = 后端执行与设备分发。
- L3 = 硬件无关波形/编译语义。

自 PRD v0.4 与模块矩阵 v0.2 起，权威含义调整为：

- **L2 = Compiler / Pulse IR**。
- **L3 = Execution Backend**。

因此，05-29 的 L2/L3 相关框架文档属于历史命名，需要迁移或标注。

## 6. 文档索引与当前归属

| 文档 | 当前用途 | 权威归属 | 状态 | 建议动作 |
| --- | --- | --- | --- | --- |
| [QXtrl量子测控软件开发需求.md](QXtrl量子测控软件开发需求.md) | 产品需求与长期路线 | PRD 主文档 | v0.4 可用 | 增补最薄垂直切片后再升版 |
| [QXtrl模块拆解与接口责任矩阵.md](QXtrl模块拆解与接口责任矩阵.md) | L0-L9 模块责任矩阵 | 层号权威来源之一 | v0.2 可用 | 后续对齐本文件中的稳定名称 |
| [QXtrl_L0契约层命名与编码规则.md](QXtrl_L0契约层命名与编码规则.md) | L0 / CC 命名与编码规则 | L0 (CC) | 可用 | 保持为 CC 规则源（包 `qxtrl/cc`） |
| [QXtrl_L0_API说明.md](QXtrl_L0_API说明.md) | L0 当前 Python API 说明 | L0 | v0.1 可用 | 随 `qxtrl/cc/` 实现变更同步更新（模块名 cc，对应 L0/Core Contracts 层） |
| [QXtrl_L1_Experiment_Language_设计.md](QXtrl_L1_Experiment_Language_设计.md) | L1 / EL 实验语言设计 | L1 (EL) | v0.1 草案 | 用于 L1 MVP schema 与 L2/L6 对齐审查（包 `qxtrl/el`） |
| [QXtrl_L1_API说明.md](QXtrl_L1_API说明.md) | L1 当前 Python API 说明 | L1 (EL) | v0.1 当前实现说明 | 随 `qxtrl/el/` 实现变更同步更新 |
| [QXtrl_L2_CPIR_Compiler_PulseIR_设计.md](QXtrl_L2_CPIR_Compiler_PulseIR_设计.md) | L2 / CPIR 编译器与 PulseIR 设计 | L2 (CPIR) | v0.2 规划增强稿 | 当前 L2/CPIR 设计入口；优先于历史 L3 波形/IR 文档（包 `qxtrl/cpir`） |
| [QXtrl_L2_API说明.md](QXtrl_L2_API说明.md) | L2 当前 Python API 说明 | L2 (CPIR) | v0.1 当前实现说明 | 随 `qxtrl/cpir/` 实现变更同步更新 |
| [QXtrl_L3_EB_ExecutionBackend_设计.md](QXtrl_L3_EB_ExecutionBackend_设计.md) | L3 / EB 执行后端设计 | L3 (EB) | v0.1 当前权威草案 | 当前 L3/EB 设计入口；优先于历史 L2 后端执行文档（建议包 `qxtrl/eb`） |
| [QXtrl_L3_API说明.md](QXtrl_L3_API说明.md) | L3 当前 Python API 说明 | L3 (EB) | v0.1 当前实现说明 | 随 `qxtrl/eb/` 实现变更同步更新 |
| [QXtrl_L4_RS_RuntimeScheduler_设计.md](QXtrl_L4_RS_RuntimeScheduler_设计.md) | L4 / RS 运行时与调度器设计 | L4 (RS) | v0.1 当前权威草案 | 当前 L4/RS 设计入口；用于 `qxtrl/rs` MVP 开发 |
| [QXtrl_L4实现审查意见-jed.md](QXtrl_L4实现审查意见-jed.md) | L4 / RS 第一轮实现审查 | L4 (RS) | v0.1 | Jed 首轮审查；部分 P0 已修复 |
| [QXtrl_L4实现审查意见-cursor.md](QXtrl_L4实现审查意见-cursor.md) | L4 / RS 实现审查（Cursor） | L4 (RS) | v0.1 | 相对 Jed 审查的增量状态与开放 findings |
| [QXtrl_L4实现审查意见_答复.md](QXtrl_L4实现审查意见_答复.md) | L4 / RS 对 Jed/Cursor 审查的答复 | L4 (RS) | v0.1 | grok 修复说明与验收记录 |
| [QXtrl_L4实现复审意见-cursor.md](QXtrl_L4实现复审意见-cursor.md) | L4 / RS 实现复审（Cursor） | L4 (RS) | v0.1 | 对 grok 答复与当前实现的独立复验结论 |
| [QXtrl_L5_DS_DataState_设计.md](QXtrl_L5_DS_DataState_设计.md) | L5 / DS 数据与状态设计 | L5 (DS) | v0.2 当前权威草案 | 当前 L5/DS 设计入口；ConfigStore/ResultStore/DataSink/RunManifest（包 `qxtrl/ds`）；已补强 L4 映射、failure manifest、DatasetRef 和验收测试 |
| [QXtrl_L7_TRH_TwinReplayHIL_设计.md](QXtrl_L7_TRH_TwinReplayHIL_设计.md) | L7 / TRH Twin / Replay / HIL 设计 | L7 (TRH) | v0.1 当前权威草案 | 当前 L7/TRH 设计入口；MVP 聚焦 deterministic Rabi VirtualQPU、typed virtual result、manifest replay inspect（包 `qxtrl/trh`） |
| [QXtrl_L7实现综合审查意见-jed.md](QXtrl_L7实现综合审查意见-jed.md) | L7 / TRH 实现综合审查 | L7 (TRH) | v0.1 | Jed 综合审查；记录 typed config 数值校验、manifest replay inspect、TRH lineage、replay_virtual 语义和测试覆盖问题 |
| [QXtrl_L7实现综合审查意见_答复.md](QXtrl_L7实现综合审查意见_答复.md) | L7 / TRH 综合审查答复 | L7 (TRH) | v0.1 | grok 对 Jed 综合审查意见的修复说明与验证记录 |
| [QXtrl_L7实现复审意见-jed.md](QXtrl_L7实现复审意见-jed.md) | L7 / TRH 实现复审 | L7 (TRH) | v0.1 冻结候选复审 | 确认上一轮 P0 已关闭；新增 replay hash/dataset check、未实现 mode、compile hash 完整性等冻结前风险 |
| [QXtrl_L7实现复审意见_答复.md](QXtrl_L7实现复审意见_答复.md) | L7 / TRH 复审答复 | L7 (TRH) | v0.1 | grok 对 Jed 复审意见的修复说明与验证记录 |
| [QXtrl_L7实现三审意见-jed.md](QXtrl_L7实现三审意见-jed.md) | L7 / TRH 实现三审 | L7 (TRH) | v0.1 冻结前审查 | 确认复审三项 P1 主路径关闭；新增跨 run dataset ref、畸形 hash、summary 语义和路径回显问题 |
| [QXtrl_L7实现三审意见_答复.md](QXtrl_L7实现三审意见_答复.md) | L7 / TRH 三审答复 | L7 (TRH) | v0.1 | grok 对 Jed 三审意见的修复说明与验证记录 |
| [QXtrl_L7实现四审意见-jed.md](QXtrl_L7实现四审意见-jed.md) | L7 / TRH 实现四审 | L7 (TRH) | v0.1 冻结前审查 | 确认三审问题基本关闭；指出 L5 允许 64 位 hash 但 L7 只校验 16 位截断 hash 的契约不一致 |
| [QXtrl_L9_OI_OperatorInterfaces_设计.md](QXtrl_L9_OI_OperatorInterfaces_设计.md) | L9 / OI 操作员接口设计 | L9 (OI) | v0.1 当前权威草案 | 当前 L9/OI 设计入口；MVP 聚焦薄 Python SDK + CLI、manifest view、JSON/text 输出和报告导出（建议包 `qxtrl/oi`） |
| [QXtrl_L9实现审查意见-jed.md](QXtrl_L9实现审查意见-jed.md) | L9 / OI 第一轮实现审查 | L9 (OI) | v0.1 | Jed 首轮审查；记录 target/L0 context、result_dir、CLI 错误码、manifest parser 和测试覆盖问题 |
| [QXtrl_L0数据与信息存放规则.md](QXtrl_L0数据与信息存放规则.md) | L0 / CC 数据治理规则 | L0 (CC) / L5 (DS) 边界 | 可用 | 后续补充 DataSink/ResultStore 强制测试 |
| [QXtrl_L0信息录入与审核工具需求.md](QXtrl_L0信息录入与审核工具需求.md) | L0 / CC 信息录入工具需求 | L0 (CC) / L9 (OI) | 可用 | 与 Frontend Workbench 视图对齐 |
| [QXtrl_L2开发框架.md](QXtrl_L2开发框架.md) | 历史“后端执行与设备分发”框架 | 当前 L3 / EB Execution Backend | 层号冲突 | 建议标注历史层号；后续重命名为 `QXtrl_L3_EB_ExecutionBackend开发框架.md` |
| [QXtrl_L2后端执行与设备分发层设计.md](QXtrl_L2后端执行与设备分发层设计.md) | 历史后端执行设计 | 当前 L3 / EB Execution Backend | 层号冲突 | 同上 |
| [QXtrl_L3开发框架.md](QXtrl_L3开发框架.md) | 历史“编译/QX-WIS/PulseIR”框架 | 当前 L2 / CPIR Compiler / Pulse IR | 层号冲突 | 建议标注历史层号；后续重命名为 `QXtrl_L2_CPIR_Compiler_PulseIR开发框架.md` |
| [QXtrl_L3量子测控波形指令集设计.md](QXtrl_L3量子测控波形指令集设计.md) | QX-WIS / PulseIR 设计 | 当前 L2 / CPIR Compiler / Pulse IR | 层号冲突且 MVP 过厚 | MVP 阶段降级 QX-WIS 为 PulseIR 审查视图 |
| [QXtrl_L3坐标系与相位跟踪算法框架.md](QXtrl_L3坐标系与相位跟踪算法框架.md) | frame tracking 与 phase convention | 当前 L2 / CPIR 编译约定，部分可上升为 L0 / CC convention | 层号冲突 | 抽出 `phase_convention` 决策 |
| [QXtrl规划审查意见.md](QXtrl规划审查意见.md) | 规划审查意见 | 审查输入 | 可用 | 已逐条回复 |
| [QXtrl规划审查意见逐条回复.md](QXtrl规划审查意见逐条回复.md) | 审查意见回复 | 决策输入 | 可用 | 本轮三份短文档来源 |
| [comments.md](comments.md) | 导师/专家短评 | 决策输入 | 可用 | 已转为 schema/契约补丁清单 |
| [QXtrl_测控软件开发规划讨论稿_v0.3.pptx](QXtrl_测控软件开发规划讨论稿_v0.3.pptx) | 第一次讨论会 PPT | 沟通材料 | 可用 | 不作为权威需求源 |

## 7. 新文档命名规则

从本文件确认后，新文档应遵守：

1. 新增文档标题中的层号必须符合本文件。
2. 若文档面对外部会议，标题优先使用稳定名称。
3. 若需保留历史文档，不直接删除，先在顶部标注：

```text
注意：本文档使用历史层号。当前权威层号见《QXtrl_架构层号与文档索引.md》。
本文档内容归属当前 L3 Execution Backend / 当前 L2 Compiler。
```

## 8. 第一次讨论会需拍板

| 决策 | 推荐结论 |
| --- | --- |
| 是否以本文件作为层号与文档归属唯一事实源 | 是 |
| 是否以 PRD v0.4 / 模块矩阵 v0.2 的 L0-L9 为权威层号 | 是 |
| 代码和新文档是否优先使用稳定英文名称 | 是 |
| 旧 L2/L3 文档是否先标注、后重命名 | 是 |

## 9. 后续维护

每次新增或升版规划文档时，必须检查本索引是否需要更新。若层号、稳定名称或文档权威性发生变化，应先更新本文件，再修改下游规划文档。
