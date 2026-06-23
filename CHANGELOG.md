# QCLab 项目日志

## [2026-06-22] - MVP Demo Rehearsal 推进 (L7 四审后 + 子代理规划/审查/漏洞汇总)

### MVP 彩排就绪进展
- 更新 `qxtrl/demo_rabi_l1.py` 为完整 rehearsal 脚本：使用隔离 /tmp 目录、无 cwd 'runs/' 污染；显式打印 4 大 PROOF（L1 spec + L0 gate、L2 compile boundary、L3/L7 virtual + L6 candidate proposal "CANDIDATE ONLY" 注释、L5 RunManifest + L7 replay inspect）；包含 require_hash_check 切换 + 删除数据集负向路径（TRH-DATASET-NOT-FOUND rejected）；输出结构化、可供非开发者直接运行验证。
- 在 `qxtrl/oi/sdk.py` 新增薄层 `replay_inspect`（委托 L7 TRH `replay_manifest` inspect 模式，支持 require_hash_check）。
- L5 `FileResultStore.get_manifest` 现验证 manifest.sha256 sidecar（防篡改，回应漏洞深挖）。
- TRH replay 错误消息清理（移除 full_path 泄漏）。
- 全量验证：`pytest qxtrl/ -q` 146 passed，ruff clean；rehearsal 脚本端到端绿路径 + 负向可见。
- 按 6 个子代理（2规划 + 2审查 + 2漏洞）汇总意见驱动：采纳推荐 hash 支持 + L9 暴露 + demo 可见性 + 关键漏洞修复（sidecar verify、路径消毒、legacy 导出、L3 信任、L9 bypass 等）。
- 目标达成：可进行 MVP demo 彩排（Rabi 薄切片，证明 4 大事项 + manifest/replay + 候选提案 + 负向诊断）。

## [2026-06-22] - 新增 L7 / TRH 实现四审意见-jed

### L7 / TRH 实现四审
- 新增 `docs/planning/QXtrl_L7实现四审意见-jed.md`，复核 grok 对 L7 三审意见的修复结果。
- 确认三审问题基本关闭：跨 run dataset ref、畸形短 hash、`core_refs_present` summary 和非法路径回显均已有实质修复。
- 记录冻结前剩余契约不一致：L5 `DatasetRef` validator 允许 64 位 sha256，但 L7 replay 只计算 16 位截断 hash，导致合法 64 位 hash 会被误判 `TRH-HASH-MISMATCH`；另记录 compile hash 缺失时可能重复 diagnostic 的清理项。
- 更新 `docs/planning/QXtrl_架构层号与文档索引.md`，登记 L7 三审答复与本次四审文档。

## [2026-06-22] - 新增 L7 / TRH 实现三审意见-jed

### L7 / TRH 实现三审
- 新增 `docs/planning/QXtrl_L7实现三审意见-jed.md`，复核 grok 对 L7 复审意见的修复结果。
- 确认复审三项 P1 主路径已基本关闭：dataset 缺失/篡改可 rejected，未实现 replay modes 统一 rejected，真实 L5 manifest 的 `pulse_ir_hash` 已落盘。
- 记录冻结前剩余风险：dataset ref 可跨 run 指向其他 run 并通过 hash check；`content_hash="sha256:"` 等畸形短 hash 可被前缀匹配放行；`require_hash_check=False` 下缺少 output refs 时 summary 仍报告 `core_refs_present=True`；非法 path 仍会回显到 `source_manifest_ref`。
- 更新 `docs/planning/QXtrl_架构层号与文档索引.md`，登记 L7 复审答复与本次三审文档。

## [2026-06-22] - 新增 L7 / TRH 实现复审意见-jed

### L7 / TRH 实现复审
- 新增 `docs/planning/QXtrl_L7实现复审意见-jed.md`，复核 grok 对 L7 综合审查意见的修复结果。
- 确认上一轮 P0 已关闭：VirtualQPU 数值契约、VirtualRunResult data 有限性、manifest 字段读取、非法 ref hygiene、`replay_virtual` rejected 语义和 L3 TRH lineage 均已有实质改进。
- 记录冻结前剩余风险：`require_hash_check=True` 未检查 dataset/hash、`replay_recorded`/`compare` 未实现却可能返回 succeeded、真实 manifest 的 `pulse_ir_hash` 为空但 replay inspect 不报错。
- 更新 `docs/planning/QXtrl_架构层号与文档索引.md`，登记 L7 综合审查答复与本次复审文档。

## [2026-06-22] - 新增 L7 / TRH 实现综合审查意见-jed

### L7 / TRH 实现审查
- 新增 `docs/planning/QXtrl_L7实现综合审查意见-jed.md`，综合审查 grok 对 L7/TRH typed virtual、deterministic RNG、replay inspect 以及 L3/L9/L4 联动的实现。
- 验证记录：`qxtrl/trh/tests` 4 项通过，`qxtrl/eb/tests` 7 项通过，`qxtrl/oi/tests` 15 项通过，`qxtrl` 全量 129 项通过，`ruff check qxtrl/trh qxtrl/eb qxtrl/oi` 通过。
- 记录 P0：`VirtualQPUConfig` 仍接受 bool/NaN/Inf/负噪声并可生成 NaN/Inf data；`build_replay_plan()` 未按当前 L5 `RunManifest` 结构读取 experiment/compile/output refs，导致有效 manifest 也生成空 refs 且 replay inspect 返回 succeeded。
- 记录 P1/P2：非法 manifest ref 的 source_run_id/path hygiene、L3 丢失 TRH model lineage、`replay_virtual` 占位却返回 succeeded、测试仍缺数值负向/有效 replay inspect/lineage 覆盖。
- 更新 `docs/planning/QXtrl_架构层号与文档索引.md` 登记该审查文档。

## [2026-06-22] - 新增 L7 / TRH Twin Replay HIL 开发文档

### L7 / TRH 规划启动
- 新增 `docs/planning/QXtrl_L7_TRH_TwinReplayHIL_设计.md`，作为当前 L7 / TRH Twin / Replay / HIL 的权威开发入口。
- 明确 L7 v0.1 MVP 聚焦 deterministic Rabi VirtualQPU、typed `VirtualRunResult`、显式 `TwinModelRef` / `VirtualQPUConfig` 和 manifest replay inspect。
- 记录当前 `qxtrl/trh/virtual.py` 差距：返回 dict、`seed` 未真正控制随机源、使用 Python `hash()` 导致跨进程不可复现、输入过宽、Replay 模型缺失、测试偏正向。
- 定义 `TRHDiagnostic`、`TwinModelRef`、`VirtualQPUConfig`、`VirtualRunRequest`、`VirtualRunResult`、`ReplayRequest`、`ReplayPlan`、`ReplayResult`、错误码、测试清单和 TRH-D-001 至 TRH-D-007 决策项。
- 更新 `docs/planning/QXtrl_架构层号与文档索引.md` 与 `AGENTS.md`，登记 L7 设计文档、`qxtrl/trh/` 目录和 TRH 测试命令。

## [2026-06-22] - 新增 L9 / OI 第一轮实现审查意见-jed

### L9 / OI 实现审查
- 新增 `docs/planning/QXtrl_L9实现审查意见-jed.md`，对 grok 的 `qxtrl/oi/` 小切片实现进行 Jed 侧首轮代码审查。
- 验证记录：`qxtrl/oi/tests` 8 项通过，`qxtrl` 全量 119 项通过，`ruff check qxtrl/oi` 通过。
- 记录 P0：OI 允许运行不在当前 L0 demo lab context 中的 qubit；`result_dir` 未真正控制 L5 manifest 写入位置。
- 记录 P1/P2：CLI 参数错误被映射为 runtime failure；manifest ref parser 接受过宽且 CLI/helper 实现不一致；CLI/SDK 测试断言过宽；formatter / manifest view 逻辑重复。
- 更新 `docs/planning/QXtrl_架构层号与文档索引.md` 登记该审查文档。

## [2026-06-22] - 新增 L9 / OI Operator Interfaces 开发文档

### L9 / OI 规划启动
- 新增 `docs/planning/QXtrl_L9_OI_OperatorInterfaces_设计.md`，作为当前 L9 / OI 操作员接口的权威开发入口。
- 明确 L9 MVP 优先推进薄 Python SDK + CLI，先收口 Rabi virtual 一键运行、`RunSummary`、manifest 查询、JSON/text 输出和 Markdown 报告导出。
- 固化 L9 边界：OI 只调用 L1/L4/L5 公开 API，不复制编译、执行、拟合、持久化或参数晋升逻辑；Web Console、实时 DataSink UI、参数 review 和 AI assistant 后置。
- 定义 `RunRabiOptions`、`RunSummary`、`OperatorDiagnostic`、`ManifestView`、CLI 退出码、错误码、测试清单和 OI-D-001 至 OI-D-008 决策项。
- 更新 `docs/planning/QXtrl_架构层号与文档索引.md` 与 `AGENTS.md`，登记 L9 设计文档。

## [2026-06-22] - 补强 L5 / DS Data & State 开发文档

### L5 / DS 设计补强
- 将 `docs/planning/QXtrl_L5_DS_DataState_设计.md` 从 v0.1 升级为 v0.2 补强稿。
- 明确在线运行 `run_id` 由 L4 分配，L5 负责唯一性校验、ResultStore 索引和引用生成；离线导入场景才允许 L5 分配。
- 补强 `RuntimeRunResult -> RunManifest` 字段映射、failure/partial manifest 语义、`DatasetRef`/`DatasetMetadata` hash 与 logical URI 规则、DS 结构化错误模型。
- 扩展 MVP API：`record_runtime_result()`、`FileResultStore`、`MemoryDataSink`，并明确旧 `record_run()` 的兼容迁移路径。
- 扩展 contract tests：DataSink 断连/overload、raw 不可覆盖、duplicate run_id、early failure 入库、manifest 禁止绝对路径、candidate calibration 不污染 active ConfigStore。
- 更新 `docs/planning/QXtrl_架构层号与文档索引.md`、`AGENTS.md`，登记 L5 v0.2 状态、`qxtrl/ds/` 目录和 DS 测试命令。

## [2026-06-22] - 新增 L4 / RS 实现复审意见-jed

### L4 / RS 实现复审（Jed）
- 新增 `docs/planning/QXtrl_L4实现复审意见-jed.md`，复核 grok 对 Jed + cursor L4 一审意见的答复与当前 `qxtrl/rs/` 实现。
- 确认一审 P0 基本关闭：15 项 RS tests、100 项全量测试通过；hardware/replay 已早拒绝；L3 rejected/failed 已映射；schema failure 返回事件；submit/get_state/list_events/cancel 已有 MVP 骨架。
- 记录仍需收口的 P1：early-return 失败路径缺 `total` timing、`RS-FAILED` 终端事件、`metrics.total_duration_ms` 和 RunState 终态；RS model validator 仍接受 bool 数值、非 JSON-like options、NaN duration；部分测试断言偏宽。
- 结论：当前 L4 可继续支撑 L5/L9 薄联调，但 L4 v0.1 定版前应补统一 finalizer、状态写入和 stricter validators。

## [2026-06-22] - 新增 L4 / RS 实现复审意见-cursor

### L4 / RS 实现复审（Cursor）
- 新增 `docs/planning/QXtrl_L4实现复审意见-cursor.md`，独立复验 grok 答复与当前 `qxtrl/rs/` 实现。
- 结论：一审 P0 基本关闭（15 RS tests、100 全量通过）；L4 virtual MVP 可冻结；L5 正式联调仍暂缓。
- 记录 v0.1.1 小修项：early-return 缺 total/RS-FAILED、分析失败测试断言偏松、并发锁未测。

## [2026-06-22] - 新增 L4 / RS 第一轮实现审查意见-kim

### L4 / RS 一审（kim）
- 新增 `docs/planning/QXtrl_L4实现一审意见.md`，由 kim 对 L4/RS Runtime & Scheduler v0.1 第一轮实现进行审查。
- 确认正向链路通畅：`RunRequest -> validate -> L2 compile -> resource lock -> L3 backend -> L6 analyze -> L5 persist -> RuntimeRunResult`，分层正确，无跨层绕过。
- 确认 9 个设计文档定义的模型均已实现（RunRequest, RunReceipt, RunState, RunEvent, RuntimeDiagnostic, StageTiming, ResourceLease, RetryPolicy, RuntimeRunResult）。
- 记录 P0 阻塞项：**零测试**（`qxtrl/rs/` 无 tests 目录），设计文档要求的 13 项 contract tests 全部未实现。
- 记录 6 项 P1：NaN/Inf timeout 绕过、model_copy 绕过（缺 validated_copy）、hardware mode 未在 L4 早拒、BackendSubmitRequest 未传 timeout_s、资源锁 TOCTOU 并发不安全、admission 失败路径 events 为空。
- 记录 7 项 P2：RunEvent stage 覆盖不足（7/16）、StageTiming 覆盖不足（缺 execute_backend 和 total）、cancel() 占位、字段校验不足、StageTiming/RetryPolicy 缺校验。
- 记录 5 项 P3 观察项：无长度限制、submit/run_once 不一致、无 demo、type: ignore、event store 隔离。
- 对照设计文档评定 7 项 MVP 验收清单（L4-AC-001 至 007）：3 通过、3 部分通过、1 不通过。
- 更新 `CHANGELOG.md`。

## [2026-06-22] - 新增 L4 / RS 实现审查意见-cursor

### L4 / RS 实现审查（Cursor）
- 新增 `docs/planning/QXtrl_L4实现审查意见-cursor.md`，基于当前 `qxtrl/rs/` 与运行时探针，相对 Jed 首轮审查给出增量结论。
- 已关闭：hardware/replay admission gate、4 条 RS 测试、submit/get_state/list_events/cancel 骨架。
- 仍开放 P0：L3 diagnostic 未上浮、early-return 路径 events 为空、契约测试远未覆盖设计 §12.1。
- 更新 `docs/planning/QXtrl_架构层号与文档索引.md` 登记审查文档。

## [2026-06-22] - 新增 L3 / EB 答复复审意见-jed

### L3 / EB 实现复审
- 新增 `docs/planning/QXtrl_L3实现复审意见-jed.md`，复核 grok 对 `QXtrl_L3实现审查意见-jed.md` 的逐条答复与当前 `qxtrl/eb/` 实现。
- 确认一审 P0 在 `submit()` 路径上基本关闭：backend_id、result_level、l0_refs、dry_run、L7 runtime failure 和 EB tests 均有实质修复。
- 接受 grok 对 `EB-BUNDLE-SCHEMA`、dict report、非全 model `validated_copy()`、hash-valid low-l0 测试策略的主要不同意见，但要求澄清 `validate_bundle()` 不是完整 L3 admission。
- 记录剩余问题：EB model validator 仍接受 bool 数值和非 JSON-like options，`submit(object())` 仍会抛裸异常，部分测试断言需要收紧并补 hash/model 负向测试。
- 验证记录：`pytest qxtrl/eb/tests/ -q` 7 项通过，`pytest qxtrl -q` 85 项通过，ruff 通过，L4 demo 通过；补充探针确认 L3 submit gate 已拒绝 hash-valid missing-l0 与 raw_iq bundle。

## [2026-06-22] - 新增 L4 / RS 第一轮实现审查意见-jed

### L4 / RS 实现一审
- 新增 `docs/planning/QXtrl_L4实现审查意见-jed.md`，对 grok 的 L4 / RS v0.1 第一轮实现进行 Jed 侧审查。
- 确认正向 Rabi virtual path 已经接入 `RuntimeService.run_once()`，demo 可执行，并开始形成 `RunRequest -> L2 compile -> L3 backend -> L6 analysis -> L5 manifest -> RuntimeRunResult` 链路。
- 记录阻塞项：`qxtrl/rs` 暂无自动化测试、`hardware/replay` 未在 L4 admission 阶段拒绝、L3 rejected/failed 未映射为 Runtime diagnostic、request schema failure 丢失返回事件、RS 模型 validator 偏薄。
- 验证记录：`pytest qxtrl -q` 85 项通过，ruff 通过，demo 通过；`pytest qxtrl/rs -q` 显示 no tests ran；补充负向探针用于 grok 下一轮复现和修复。
- 更新 `AGENTS.md` 高价值文件图，登记 `qxtrl/rs/` 为 L4 / RS 实现原型目录。

## [2026-06-22] - 新增 L5 / DS Data & State 开发文档

### L5 / DS 规划启动
- 新增 `docs/planning/QXtrl_L5_DS_DataState_设计.md`，作为当前 L5 / DS 的权威开发入口。
- 明确三类 store 强制分离：`ConfigStore`、`ResultStore`、`DataSink`；RunManifest 最小字段对齐 SCP-009/010。
- 给出 `qxtrl/ds/` 包结构、L4→L5 持久化序列、MVP 验收与 demo `record_run()` 迁移路径。
- 更新 `docs/planning/QXtrl_架构层号与文档索引.md` 登记 L5 设计文档。

## [2026-06-22] - 新增 L3 / EB API 说明文档

### L3 / EB API 文档
- 新增 `docs/planning/QXtrl_L3_API说明.md`，说明当前 `qxtrl/eb/` 公开 API、核心模型、`VirtualExecutionBackend`、输入信任边界、capability / L0 refs gate、dry-run 语义和结构化失败返回。
- 文档覆盖 `BackendSubmitRequest`、`BackendCapability`、`BackendDiagnostic`、`BackendEvent`、`BackendRunResult`、`ExecutionBackend`、`VirtualExecutionBackend` 以及 `verify_compiled_bundle` 重导出。
- 更新 `docs/planning/QXtrl_架构层号与文档索引.md` 与 `AGENTS.md`，登记 L3 API 文档为当前实现说明，并补充 `qxtrl/eb/` 实现位置。

## [2026-06-22] - 新增 L4 / RS Runtime & Scheduler 开发文档

### L4 / RS 规划启动
- 新增 `docs/planning/QXtrl_L4_RS_RuntimeScheduler_设计.md`，作为当前 L4 / RS Runtime & Scheduler 的权威开发入口。
- 明确 L4 v0.1 聚焦单进程同步 `run_once()`：`RunRequest -> L2 compile -> resource lease -> L3 backend -> L6 analysis -> L5 manifest -> RuntimeRunResult`。
- 定义 `RunRequest`、`RunReceipt`、`RunState`、`RunEvent`、`RuntimeDiagnostic`、`StageTiming`、`ResourceLease`、`RetryPolicy` 和 `RuntimeRunResult` 的建议契约。
- 明确 MVP 只支持 `dry_run` / `virtual`，默认全局资源锁、FIFO/同步执行、失败可见和分段计时；多队列、自动并行图着色、真实硬件、完整 Run Factory 均列为 OUT。
- 单列 L4-D-001 至 L4-D-012 决策表，覆盖同步/异步、run_id 归属、raw bundle 入口、资源锁粒度、retry、取消、事件 sink、Run Factory 和硬件模式等待拍板问题。
- 更新 `docs/planning/QXtrl_架构层号与文档索引.md` 与 `AGENTS.md`，登记 L4 设计文档。

## [2026-06-22] - 新增 L3 / EB 第一轮实现审查意见-jed

### L3 / EB 实现一审
- 新增 `docs/planning/QXtrl_L3实现审查意见-jed.md`，对 grok 的 L3 / EB 第一轮实现进行 Jed 侧审查，便于与 kim 的审查意见区分。
- 确认正向链路已跑通：`L1 -> L2 -> L3/EB -> L6 -> L5` demo 可执行，`VirtualExecutionBackend` 已开始消费 L2 `CompiledBundle` 并返回 `BackendRunResult`。
- 记录阻塞项：`backend_id` 未校验、capability/result level gate 缺失、`l0_refs` 缺失仍可执行、非验证阶段抛裸异常、`dry_run` 实际执行 L7、缺少 `qxtrl/eb/tests/` contract tests、EB model validator 不足。
- 验证记录：`pytest qxtrl -q` 78 项通过，ruff 通过，demo 通过；补充负向探针用于 grok 下一轮复现和修复。

## [2026-06-22] - 新增 L1 / L2 API 说明文档

### L1 / EL 与 L2 / CPIR API 文档
- 新增 `docs/planning/QXtrl_L1_API说明.md`，说明当前 `qxtrl/el/` 公开 API、核心模型、校验规则、`validated_copy()`、Registry 和 Rabi spec 示例工厂。
- 新增 `docs/planning/QXtrl_L2_API说明.md`，说明当前 `qxtrl/cpir/` 公开 API、`PulseIR`/`CompiledBundle` 模型、编译函数、`verify_compiled_bundle()`、frame consistency、hash 校验和 L3 推荐入口。
- 更新 `docs/planning/QXtrl_架构层号与文档索引.md` 与 `AGENTS.md`，登记 L1/L2 API 文档为当前实现说明。

## [2026-06-22] - 新增 L2 / CPIR 二审答复终审意见

### L2 二审答复终审
- 新增 `docs/planning/QXtrl_L2二审答复_终审意见.md`，对 grok 二审答复和当前 `qxtrl/cpir/` 实现进行终审。
- 确认二审三项 P1 问题中 **P1-009（组件级 validator）和 P1-010（多轴静默截断）已关闭**。P1-008（model_copy/dict mutation 绕过）的**内部路径已通过 validated_copy() 保护**，但裸 model_copy() 和原地 dict mutation（metadata 侧信道）问题仍然存在。
- 终审结论：**L2 已具备启动 L3/EB 开发的契约条件**，前提是 L3 入口必须执行 CompiledBundle 再验证（L3 设计文档已要求）。建议 L3 开发期间同步完成 L2 的剩余加固项（FrameEvent NaN phase、dict 深度冻结）。
- 确认 L0 refs 已迁移为稳定 identity.id（如 `chip.demo_rabi_001`），不再是全量 repr。
- 详细判定矩阵见 `docs/planning/QXtrl_L2二审答复_终审意见.md`。

## [2026-06-22] - 新增当前权威 L3 / EB Execution Backend 设计文档

### L3 / EB 设计启动
- 新增 `docs/planning/QXtrl_L3_EB_ExecutionBackend_设计.md`，作为当前权威 L3 / EB Execution Backend 设计入口。
- 明确 L3 MVP 只推进 Rabi `CompiledBundle -> VirtualExecutionBackend -> BackendRunResult`，真实硬件、Edge Agent、Replay/HIL、async event stream 暂不进入第一版。
- 固化 L3 输入信任模型：只消费 `CompiledBundle`，入口必须重新 validate + 校验 `bundle_hash` / `pulse_ir.content_hash`，拒绝 raw `ExperimentSpec` 和 raw `PulseIR`。
- 定义 `BackendSubmitRequest`、`BackendCapability`、`BackendDiagnostic`、`BackendEvent`、`BackendRunResult`、`ExecutionBackend` 等最小契约和 L3 MVP 测试清单。
- 更新 `docs/planning/QXtrl_架构层号与文档索引.md` 与 `AGENTS.md`，将该文档登记为当前 L3/EB 设计入口，优先于历史 L2 后端执行文档。

## [2026-06-22] - 新增 L2 / CPIR 实现二审意见

### L2 实现二审
- 新增 `docs/planning/QXtrl_L2实现二审意见.md`，对 grok 复审答复与当前 `qxtrl/cpir/` 实现进行二审。
- 确认正向进展：一审 P0（frame consistency）在 Rabi MVP 范围内已关闭；构造期契约保护（frame 引用一致性、基础数值校验、no-waveform guard、atom 白名单、bundle 谱系记录）均已正确实现。
- 确认复审三项 P1 问题仍未关闭：
  - **P1-008**: `model_copy(update=...)` 和内部 dict mutation 仍可绕过所有契约校验（10/10 探针 ACCEPTED），包括 sweep 变空、metadata 注入 waveform、duration 变负、hash 被绕过。L1 已验证 `validated_copy()` + deep-freeze 模式有效，L2 需复用。
  - **P1-009**: `SweepAxis`/`SweepSpec`/`FrameEvent` 缺少独立 validator，bool 被 Pydantic 吞成 1.0、NaN/Inf/空值/bad parameter_ref 均可直接构造（7/7 探针 ACCEPTED）。`FrameEvent.phase_rad` 无校验。
  - **P1-010**: 编译器仍未检查 `len(plan.scan.axes) == 1`，多轴 plan + 单轴 atom 时静默截断（探针 ACCEPTED）。
- 本轮新发现：
  - **P1-NEW-013**: `_simple_content_hash()` 排除 `metadata` 字段，使其成为不可审计的注入侧信道。
  - **P1-NEW-014**: `FrameEvent.phase_rad` 无 NaN/Inf 校验。
  - **P1-NEW-015**: `PulseIR` 接受 `order='randomized'`，违反设计文档 MVP 规则。
  - **P2-NEW-016**: `l0_refs` 使用全量 Python repr，体积膨胀且含时间戳。
- 验证记录：`qxtrl/cpir` 测试 10 项通过、`qxtrl` 全量测试 67 项通过、ruff 通过、Rabi demo 正常。补充 30+ 负向探针用于验证和下一轮修复。
- 建议修复顺序：validated_copy + deep-freeze → 组件级 validator → 编译器多轴检查 → randomized order 拒绝 → 扩展测试。

## [2026-06-22] - 新增 L2 / CPIR 实现复审意见

### L2 实现复审
- 新增 `docs/planning/QXtrl_L2实现复审意见.md`，复核 grok 对 `QXtrl_L2实现审查意见.md` 的逐条答复与当前 `qxtrl/cpir/` 实现。
- 确认正向进展：Rabi MVP frame 引用一致性基本关闭，基础数值校验、no-waveform 构造期 guard、atom kind 检查、bundle l0_refs/hash 和测试覆盖均有明显增强。
- 记录仍需修复的问题：`model_copy(update=...)` 与内部 dict mutation 仍可绕过 L2 契约并破坏 hash 语义；bool 可被 Pydantic coercion 吞成 `1.0`；`plan.scan` 多轴在 atom 单轴时仍会静默截断；完整 frame update / rotating frame state 语义仍需后续设计。
- 验证记录：`qxtrl/cpir` 测试 10 项通过、`qxtrl` 全量测试 67 项通过、ruff 通过、Rabi demo 正常；补充负向探针用于下一轮修复。

## [2026-06-22] - 新增 L2 / CPIR 实现一审意见

### L2 实现审查
- 新增 `docs/planning/QXtrl_L2实现审查意见.md`，审查 grok 当前 `qxtrl/cpir/` 初步实现。
- 确认正向进展：L2 已迁移到 Pydantic schema、结构化 `SweepSpec`、`CompiledBundle` 和边界再验证，正向 MVP 链路可运行。
- 记录需优先修复的问题：frame consistency 尚未形成契约，无法保证统一旋转坐标系；CPIR 数值/结构校验不足；no-waveform guard 缺失；frozen model 内部 dict 仍可变并破坏 hash 语义；编译器未拒绝未知 atom/multi-axis；bundle 未记录 L0 refs。
- 验证记录：`qxtrl/cpir` 测试 3 项通过、`qxtrl` 全量测试 60 项通过、ruff 通过；补充负向探针用于 grok 复现。

## [2026-06-22] - 完善 L2 / CPIR Compiler & PulseIR 设计

### L2 / CPIR 规划增强
- 将 `docs/planning/QXtrl_L2_CPIR_Compiler_PulseIR_设计.md` 升级为 v0.2 规划增强稿。
- 明确 `qxtrl.cpir.*` schema 前缀、`PulseIR` / `SweepSpec` / `CompiledBundle` / `CompileDiagnostic` / `ResourceUsage` 等核心对象。
- 将 scan 从临时 `metadata.scan` 提升为结构化 `SweepSpec` 权威字段，并要求 metadata 仅作为审查镜像或非契约补充。
- 增加 L2 编译边界的 L1 输入再验证、no-waveform 递归防线、canonical dump/content hash、bundle 谱系记录和 RunManifest 对齐要求。
- 区分当前 `qxtrl/cpir` dataclass demo prototype 与稳定 CPIR 契约目标，补充 MVP 测试清单和开发推进顺序。
- 更新 `docs/planning/QXtrl_架构层号与文档索引.md`、`AGENTS.md`，登记 L2 设计入口、`qxtrl/cpir/` 原型位置和 L2 测试命令。

## [2026-06-22] - 新增 L1 / EL 实现复审意见

### L1 实现复审
- 新增 `docs/planning/QXtrl_L1实现复审意见.md`，复核 grok 对 `QXtrl_L1实现审查意见.md` 的逐条答复与实现修改。
- 确认正向结果：L1 测试 21 项通过、`qxtrl` 全量测试 50 项通过、ruff 通过、Rabi demo 继续跑通。
- 复审结论：一审多数问题已关闭，但 P1-002（已验证 spec 的 mutation / copy 绕过）仍为部分关闭；新增复审 findings 覆盖嵌套可变对象、`model_copy(update=...)` 不重新校验、`parameter_ref` element_id 语义校验和测试误触发风险。

## [2026-06-22] - 新增 L1 / EL 实现一审意见

### L1 实现审查
- 新增 `docs/planning/QXtrl_L1实现审查意见.md`，对 grok 当前 `qxtrl/el/` MVP 实现进行一审。
- 记录正向结果：L1 测试 10 项通过、`qxtrl` 全量测试 39 项通过、ruff 通过、Rabi demo 跑通 L1 -> L2 -> L7 -> L6 -> L5。
- 记录需修复 findings：schema version 精确绑定、failed assignment 污染对象、`parameter_ref` MVP 语法、`coupler_id` 校验、嵌套 waveform 绕过、Registry 历史前缀、README 残留、公开导出缺口等。

## [2026-06-22] - L1 复审修复完成 + L2/CPIR 开发文档启动

### L1 / EL 复审闭环（针对 Jed 复审意见）
- P1-010：所有 L1 模型统一 frozen，所有关键集合改为 tuple（pdca_path、axes、values、metrics、proposal_targets、capability_requirements、children 等）。
- P1-011：新增 `ExperimentSpec.validated_copy(**updates)` 强制 re-validate；更新文档，不再推荐裸 model_copy。
- P2-012：parameter_ref 校验增强 —— calibration element 调用 L0 `validate_element_id()`；Rabi MVP pulse role 白名单（仅 drive）。
- P3-013：清理测试过时注释；修复 scan unit 测试使用合法 parameter_ref，避免误触发。
- 新增全部复审要求的 mutation 抵抗测试和 param_ref 负向测试。
- 所有复审探针现在正确 REJECTED；全量 59 测试 + ruff + demo 通过。
- L1 对 MVP Rabi 薄切片已足够坚实（不可变契约 + 完整负向覆盖 + L0 集成）。

### L2 / CPIR 规划启动
- 按权威架构索引（L2 = CPIR）创建 `docs/planning/QXtrl_L2_CPIR_Compiler_PulseIR_设计.md`。
- 文档遵循 template，定义 PulseIR v1、编译器职责、与 L1 的契约、MVP Rabi 范围、扩展点。
- 后续将基于此文档继续实现/强化 qxtrl/cpir。

## [2026-06-22] - L1/L2/L7/L6/L5 MVP 垂直切片打磨与测试扩展

### 改进内容
- L1: 扩展测试至 10 项，完整覆盖设计文档建议的 contract tests（bad unit/NaN/Inf/bool/empty scan、bad target ID、L0 gate 审批拒绝与通过、io consumes/produces 必填、pdca/io 记录等）。修复 scan values validator 对 bool 入参的严格捕获（mode=before）。
- L2 (CPIR): 编译器忠实传递 L1 scan 定义到 PulseIR.metadata，代表性 moments + sweep 参数；支持从 spec 提取 duration/amps。
- L7 (TRH): virtual 严格消费 metadata 中的 scan 值，生成 5 点真实 Rabi 振荡 IQ 数据（基于隐藏 pi_amp ~0.175 + 可控噪声）。
- L6 (CO): 分析器实现简单最小二乘网格搜索拟合，可从仿真数据可靠恢复 pi_amp（~0.175），fit_quality 高。
- L5 (DS): RunManifest 记录更丰富的结果（contrast/fit/proposal_value/points + 完整 l0_refs）。
- Demo: 打印更清晰（points、L0 gates 显式通过、recovered pi_amp 接近 truth）；端到端展示 proposal。
- 各层新增基础测试（cpir/trh/co/ds/tests），全量 pytest 39 通过。
- Ruff 全清零，lint 干净。

### 验证
- 所有测试通过；demo 成功跑通并展示有意义的拟合结果（非硬编码）。
- 继续忠实于 L1 设计文档 MVP 范围（仅 Atom，Rabi 路径，L0 gate 集成，无 waveform 落 L1）。

## [2026-06-22] - L1/EL 开发继续 + L2/CPIR + L7/TRH + L6/CO MVP 链路

### L1 Experiment Language (EL)
- 完善 `qxtrl/el/models.py` validator：完整 L0 gate 调用（当 context 为 L0 模型实例时自动 `require_usable_for_control`），覆盖设计文档中更多负向规则（schema version、children、io、target 一致性、Act/Do/Check 缺失等）。
- 新增 `create_rabi_experiment_spec()` 工厂函数 + 默认 Registry 注册，可直接生成符合设计文档的 Rabi Atom spec。
- 添加 `qxtrl/el/tests/test_el_mvp.py`，覆盖设计文档建议的 contract tests（Rabi 合法、拒绝 waveform、children、Registry 等）。
- 导出并测试通过。

### L2 Compiler / Pulse IR (CPIR)
- 新建 `qxtrl/cpir/` 包（短码 CPIR）。
- 最小 `PulseIR`、`PulseMoment`、`FrameEvent`。
- 简单 `compile_experiment_spec`：将 L1 Rabi AtomSpec 转为可被 virtual 执行的 IR 描述（含 metadata 中的 scan）。

### L7 Virtual (TRH)
- 新建 `qxtrl/trh/` 包（短码 TRH）。
- `run_rabi_virtual`：基于 scan amplitudes 用简单 sin^2 模型模拟 IQ 数据，返回 pi_amp_estimate 等。

### L6 Analyzer (CO)
- 新建 `qxtrl/co/` 包（短码 CO）。
- `analyze_rabi` + 简单拟合：从 virtual result 产生 metrics + proposal（pi_amp）。

### 集成 Demo
- `qxtrl/demo_rabi_l1.py`：端到端 L1 -> L2 -> L7 -> L6 链路，使用 L1 spec 创建 Rabi，编译，虚拟运行，分析出 proposal。
- 演示完整 thin slice，输出 proposal。

### 其他
- 更新 AGENTS.md、CHANGELOG 等。
- 所有测试通过，ruff clean。

## [2026-06-22] - 修正 L0 API 说明短码命名

### L0 API 文档
- 更新 `docs/planning/QXtrl_L0_API说明.md` 至 v0.2，将公开导入示例、schema version 示例、验证器示例和 quickstart 从 `qxtrl.l0` 迁移为 `qxtrl.cc`。
- 将 `L0SnapshotRef.kind` 示例中的 `l0_bundle` 对齐为当前实现使用的 `cc_bundle`。
- 保留 L0/CC 作为层语义名称，代码范围明确为 `qxtrl/cc/`。

## [2026-06-22] - 对齐 L1/EL 设计文档命名与实现约定

### L1 Experiment Language 设计审查修订
- 更新 `docs/planning/QXtrl_L1_Experiment_Language_设计.md`：将 L1 schema version 前缀从 `qxtrl.l1.*` 对齐为 `qxtrl.el.*`，并明确 L0/Core Contracts 当前实现包和 schema 前缀为 `qxtrl.cc.*`。
- 补充全局约定：schema version 使用层级短码；跨层数据 `kind` 可保留 `l0_snapshot` 等层语义标识，不等同于 Python 包名。
- 补充 Pydantic 递归结构实现提示、Rabi MVP `parameter_ref` 最小解析规则、Registry `output_schema` 对 L2/CPIR 的临时引用说明，以及 physical/control path 下 L0 gate 的明确要求。
- 扩展 L1 MVP contract tests 清单，新增 Atom 不允许 children、`parameter_ref` MVP path 规则等测试项。

## [2026-06-21] - 启动 L0 Core Contracts 实现 + HANDOFF_TEMPLATE.md

### L1 Experiment Language 设计
- 新增 `docs/planning/QXtrl_L1_Experiment_Language_设计.md`，定义 L1 / EL 的边界、MVP schema、Atom/PDCA path、Registry 最小设计、SCP-001 Node typed edge、Rabi Atom 示例和验收测试计划。
- 明确 MVP 只实现 `ExperimentSpec` + `AtomSpec` + Rabi Atom；Task/Session、黑板、checkpoint、回滚和完整优化器后置。
- 在 `docs/planning/QXtrl_架构层号与文档索引.md` 中登记该 L1 设计文档。

### L0 API 文档
- 新增 `docs/planning/QXtrl_L0_API说明.md`，面向 L1+ 开发说明当前 L0 Core Contracts 的公开导入、类、方法、验证器、错误模型、示例工厂、测试验收和当前边界。
- 文档覆盖 `DataQuality` 审批/撤销 gate、`Quantity` 数值规则、`ChipModel`/`WiringGraph`/`HardwareInventory`/`SafetyPolicy` 等核心对象，并明确后续增强项。

### L0 实现复审
- 新增 `docs/planning/QXtrl_L0实现复审意见.md`，记录开发 agent 按首轮审查修改后的复审结果。
- 确认首轮 P0/P1 主问题已基本修复：schema_version 类型绑定、SafetyPolicy missing=>deny、WiringEndpoint/channel 校验、Identity ID 校验、HardwareInventory channels 要求、README quickstart。
- 记录剩余需修复项：DataQuality assignment/gate 绕过、ChipModel 拓扑一致性、WiringEdge role/channel 语义、Quantity bool/NaN/Inf 输入收紧、提交前生成文件清理。

### L0 Core Contracts (新)
- 新建 `qxtrl/l0/` 包（后重命名为 `qxtrl/cc/` 以遵循 CC 短码命名）作为 QXtrl 独立产品主干的契约基础（按 AGENTS.md 及规划要求，与 legacy home/ 隔离）。
- 实现内容（MVP-01 范围）：
  - `Quantity`（value/unit/uncertainty，支持 "unknown"）。
  - ID 验证器：严格实现命名规则（qNNN、line.*、dev.*、chan.*、rg.*、coupler 端点排序等）。
  - `L0Base` + `Identity` + `DataQuality`（强制 `usable_for_control` + approved + 来源字段）。
  - `ChipModel`、`WiringGraph`、`HardwareInventory`、`SafetyPolicy`、`L0SnapshotRef` 等核心领域对象（schema_version、治理规则）。
  - 错误模型：`QXtrlValidationError`、`SafetyViolation`、`SchemaVersionError`。
  - 示例：public Willow 占位 + 最小可运行 Rabi lab 配置。
  - 单元测试全通过（ID 规则、数量、usable 拒绝、快照引用等）。
- 依赖：pydantic>=2.7（已加入 pyproject）。
- 对齐文档：遵循 `QXtrl_L0契约层命名与编码规则.md`、MVP 最薄切片、`QXtrl模块拆解与接口责任矩阵`、设计使用 `template.md` 形态创建了 `docs/planning/QXtrl_L0_Core_Contracts_设计.md`。

### 其他
- 新增 `docs/planning/HANDOFF_TEMPLATE.md`（内置完整使用指南），用于因 token 配额、上下文污染在多个 agent / session 之间切换时实现低摩擦恢复。

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
