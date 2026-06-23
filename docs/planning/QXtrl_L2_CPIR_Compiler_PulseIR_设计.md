# QXtrl L2 / CPIR Compiler & Pulse IR 设计

**版本**: v0.2  
**日期**: 2026-06-22  
**状态**: MVP 规划增强稿（供 `qxtrl/cpir` 实现、L1/L3/L7 对齐和后续审查使用）  
**层级命名**: L2 / CPIR / Compiler / Pulse IR（短码 CPIR，包 `qxtrl/cpir`）  
**Schema 前缀**: `qxtrl.cpir.*`  
**关联文档**:
- [QXtrl_L1_Experiment_Language_设计.md](QXtrl_L1_Experiment_Language_设计.md)
- [QXtrl_MVP最薄垂直切片定义.md](QXtrl_MVP最薄垂直切片定义.md)
- [QXtrl_架构层号与文档索引.md](QXtrl_架构层号与文档索引.md)（权威：L2 = CPIR）
- [QXtrl模块拆解与接口责任矩阵.md](QXtrl模块拆解与接口责任矩阵.md)
- 当前实现参考：`qxtrl/cpir/`（极简 PulseIR + `compile_experiment_spec`）

## 0. 本轮规划者修订说明

本文件在 grok 初稿基础上补强以下点：

1. 明确 L2/CPIR 的稳定 schema 前缀、边界对象和 MVP 必须锁定的契约字段。
2. 将 scan 从“只放 metadata”升级为结构化 `SweepSpec`，metadata 只允许作为审查镜像或非契约补充。
3. 增加 `CompiledBundle`、`CompileDiagnostic`、内容哈希、资源需求和 RunManifest 对齐要求。
4. 增加 L1 输入再验证要求，避免上游对象 mutation/copy 绕过影响编译可重复性。
5. 区分“当前 `qxtrl/cpir` 可跑薄切片实现”和“稳定 CPIR 契约目标”，避免实现过早冻结为临时 dataclass 形态。

## 1. 文档目的与范围

本文档定义 L2 / CPIR 的职责、核心对象、编译规则、MVP 验收标准和后续升版条件。

L2 的核心目标是把 L1/EL 的实验意图编译成后端可消费、可审查、可哈希、可回放的硬件无关中间表示：

```text
L1 ExperimentSpec
  -> L2 Compiler
  -> PulseIR
  -> CompiledBundle
  -> L3 ExecutionBackend 或 L7 Twin / Replay / HIL
```

**MVP 聚焦**：Rabi amplitude Atom 的编译，产生单一 typed `PulseIR v1`，可被虚拟后端消费，并能进入 `RunManifest` 做谱系记录。

**明确不包含**：

1. 完整 QX-WIS 双层 IR。
2. 真实硬件上传格式、厂商私有指令、驱动适配。
3. 完整 waveform cache 策略。
4. 多 Atom / Task / Session 编译。
5. 完整 frame tracking 算法库。
6. L4 调度、L5 持久化、L6 校准决策、L9 UI 展示。

## 2. 架构边界

| 项 | 内容 |
| --- | --- |
| 层号 | L2 |
| 短码 | CPIR |
| 稳定英文名 | Compiler / Pulse IR |
| 代码包 | `qxtrl/cpir` |
| 上游 | L1 / EL：`ExperimentSpec`、`AtomSpec`、`PlanSpec`、`DoSpec` |
| 下游 | L3 / EB、L7 / TRH、L4 / RS、L5 / DS |
| 核心产出 | `PulseIR`、`CompiledBundle`、`CompileDiagnostic` |
| 不负责 | 硬件会话、真实上传、排队、拟合、参数晋升、UI |

L2 是“编译契约层”，不是“执行层”。它可以为执行层准备资源需求、时间结构、采集窗口、参数绑定和能力要求，但不能直接调用设备。

## 3. 关键设计原则

### 3.1 CPIR 是后端无关契约

`PulseIR` 必须表达硬件无关的脉冲、帧、采集、扫描、时序和资源占用。它可以引用逻辑 line/channel、L0 snapshot、模板名和参数绑定，但不能把某个厂商私有上传格式作为唯一语义。

### 3.2 高层不携带最终 waveform，L2 也不提前固化大数组

L1 禁止携带最终 waveform ndarray。L2 输出的 `PulseIR` 同样不得在契约对象中携带最终采样数组。

允许：
- `template_ref`
- `shape`
- `duration`
- `amplitude` 或 sweep binding
- `phase` / `frequency`
- `kernel_ref`

禁止：
- `samples: [0.0, ...]`
- `waveform: np.ndarray`
- `iq_array`
- 任意大段 DAC/ADC 原始数组

最终 waveform 应在受控 render 边界生成，并由 L3 adapter 或 L2 内部 renderer 以非契约缓存形式处理。

### 3.3 Scan 必须结构化

Rabi MVP 不能只把 scan 放进 `metadata`。`SweepSpec` 是权威字段，`metadata.scan` 只能作为审查镜像或兼容临时实现。

原因：

1. L7 Twin 需要稳定读取扫描轴。
2. L5 RunManifest 需要记录可回放的扫描谱系。
3. 后续 L4 factory pipeline 需要根据扫描点估算工作量和资源。
4. AI/自动校准需要明确知道哪个参数被扫描，而不是解析松散字典。

### 3.4 L2 必须对 L1 输入做再验证/规范化

L2 不能只相信“传进来的对象曾经验证过”。进入编译边界时必须形成 canonical input。

推荐实现策略：

```python
def canonicalize_l1_spec(spec: ExperimentSpec | dict) -> ExperimentSpec:
    if isinstance(spec, ExperimentSpec):
        return ExperimentSpec.model_validate(spec.model_dump(mode="python"))
    return ExperimentSpec.model_validate(spec)
```

如果 L1 已实现 `validated_copy()` 并保证 deep validation，可以使用该 helper；但 L2 文档和测试仍应保留编译边界再验证要求。

### 3.5 编译结果必须可哈希、可审查、可回放

`PulseIR` 和 `CompiledBundle` 应支持 canonical dump，并由确定性 JSON 产生 `content_hash` / `bundle_hash`。

哈希至少覆盖：

1. L1 `spec_id` 与 canonical spec digest。
2. 相关 L0 snapshot ref/hash。
3. PulseIR 契约字段。
4. compile options。
5. compiler version / schema version。

非确定性字段（时间戳、机器路径、临时对象地址）不得进入内容哈希。

## 4. 核心对象

### 4.1 CompileInput

`CompileInput` 是 L2 编译入口的完整上下文。MVP 可以先不实现独立类，但接口设计应按此收敛。

```python
class CompileInput(BaseModel):
    schema_version: Literal["qxtrl.cpir.CompileInput/v0.1"]
    experiment_spec: ExperimentSpec
    l0_snapshot_refs: tuple[L0SnapshotRef, ...] = ()
    backend_capability_ref: str | None = None
    compile_options: dict[str, object] = {}
```

要求：

1. `experiment_spec` 必须经过 L2 边界再验证。
2. `l0_snapshot_refs` 用于后续 `CompiledBundle` 谱系记录。
3. `backend_capability_ref` 在 MVP 可为空，真实后端路径必须存在。
4. `compile_options` 必须可序列化、可哈希；不能放 Python callable 或对象实例。

### 4.2 SweepSpec

`SweepSpec` 是扫描契约，不应仅藏在 metadata。

```python
class SweepAxis(BaseModel):
    axis_id: str
    parameter_ref: str
    unit: str
    values: tuple[float, ...]

class SweepSpec(BaseModel):
    axes: tuple[SweepAxis, ...]
    mode: Literal["grid", "zip"] = "grid"
    order: Literal["as_declared", "randomized"] = "as_declared"
    seed: int | None = None
```

Rabi MVP 最小规则：

1. 只允许一个 axis。
2. `parameter_ref` 只允许 `pulse.drive.amplitude`。
3. `values` 必须非空，且不包含 bool/NaN/Inf。
4. `unit` 可为 `a.u.` 或后续统一的无量纲幅度单位。
5. `order=randomized` 可以先拒绝，待 L4/L5 有完整随机序记录后再开放。

### 4.3 PulseIR

`PulseIR` 是硬件无关的脉冲中间表示。

```python
class PulseIR(BaseModel):
    schema_version: Literal["qxtrl.cpir.PulseIR/v0.1"]
    ir_id: str
    source_spec_id: str
    atom_id: str
    target: dict[str, object]
    sweep: SweepSpec
    moments: tuple[PulseMoment, ...]
    frames: tuple[FrameEvent, ...]
    acquisition_windows: tuple[AcquireWindow, ...]
    resources: ResourceUsage
    total_duration_ns: float
    content_hash: str | None = None
    metadata: dict[str, object] = {}
```

MVP 允许当前实现继续使用 dataclass 作为过渡，但稳定边界建议改为 frozen Pydantic value object，或在 dataclass 外增加 Pydantic serialization wrapper。

### 4.4 PulseMoment

`PulseMoment` 描述单个模板化脉冲、等待、barrier 或 acquire 动作。

```python
class PulseMoment(BaseModel):
    moment_id: str
    kind: Literal["drive", "readout", "wait", "barrier", "acquire"]
    line_id: str
    t0_ns: float
    duration_ns: float
    template_ref: str | None = None
    parameters: dict[str, object] = {}
    sweep_bindings: dict[str, str] = {}
    frame_id: str | None = None
```

规则：

1. `t0_ns >= 0`，`duration_ns > 0`，除非 `kind="barrier"` 后续另行定义。
2. `line_id` 必须来自 L1 target / L0 wiring 的逻辑 line，不得只写厂商私有通道。
3. 被扫描参数必须放在 `sweep_bindings`，例如 `{"amplitude": "sweep.axis.amp"}`。
4. `parameters` 可以有默认值，但不得复制全量扫描点为多个 moment，除非后续引入展开策略。

### 4.5 FrameEvent

```python
class FrameEvent(BaseModel):
    frame_id: str
    line_id: str
    t0_ns: float
    phase_rad: float = 0.0
    frequency_hz: float | None = None
```

MVP 只要求支持 drive frame 的初始 phase/frequency 占位。完整 phase convention 后续可从历史 L3 phase 文档抽取为 L0/L2 共同约定。

### 4.6 AcquireWindow

```python
class AcquireWindow(BaseModel):
    window_id: str
    line_id: str
    t0_ns: float
    duration_ns: float
    result_level: Literal["raw_iq", "integrated_iq", "classified"]
    integration_kernel_ref: str | None = None
```

Rabi MVP 建议使用 `integrated_iq`，满足 L7 虚拟执行和 L6 Rabi 拟合。

### 4.7 ResourceUsage

```python
class ResourceUsage(BaseModel):
    line_ids: tuple[str, ...]
    estimated_points: int
    estimated_shots: int
    estimated_duration_ns_per_point: float
```

MVP 中资源估算用于 L4/L5 展示和后续 Run Factory 产线化，不作为真实硬件排队依据。

### 4.8 CompileDiagnostic

```python
class CompileDiagnostic(BaseModel):
    schema_version: Literal["qxtrl.cpir.CompileDiagnostic/v0.1"]
    severity: Literal["info", "warning", "error"]
    code: str
    message: str
    path: str | None = None
    hint: str | None = None
```

建议错误码：

| code | 含义 |
| --- | --- |
| `L2-COMPILE-ATOM-ONLY` | MVP 只支持 Atom |
| `L2-UNSUPPORTED-ATOM-KIND` | 不支持当前 atom_kind |
| `L2-SCAN-MISSING` | 缺失 scan |
| `L2-SCAN-AXIS-UNSUPPORTED` | scan axis 不符合 MVP 白名单 |
| `L2-WAVEFORM-FORBIDDEN` | 输入或输出出现最终 waveform 数组 |
| `L2-L0-REF-MISSING` | 物理路径缺少必要 L0 引用 |
| `L2-HASH-NONDETERMINISTIC` | canonical dump 存在不可哈希内容 |

### 4.9 CompiledBundle

`CompiledBundle` 是提交给 L3/L7/L4 的编译产物包装。

```python
class CompiledBundle(BaseModel):
    schema_version: Literal["qxtrl.cpir.CompiledBundle/v0.1"]
    bundle_id: str
    pulse_ir: PulseIR
    diagnostics: tuple[CompileDiagnostic, ...] = ()
    l0_refs: tuple[L0SnapshotRef, ...] = ()
    source_spec_id: str
    source_spec_hash: str
    compiler_version: str
    bundle_hash: str | None = None
```

MVP 可让 `compile_experiment_spec()` 暂时返回 `PulseIR` 以兼容现有 demo，但正式接口应新增：

```python
def compile_to_bundle(input: CompileInput | ExperimentSpec | dict) -> CompiledBundle:
    ...
```

## 5. MVP Rabi 编译规则

### 5.1 输入限制

MVP 只支持：

1. `schema_version == "qxtrl.el.ExperimentSpec/v0.1"`。
2. `node_kind == "atom"`。
3. `atom.atom_kind` 为 Rabi amplitude Atom 的注册名称。
4. `children` 为空。
5. `plan.scan.axes` 只有一个 axis。
6. `plan.scan.axes[0].parameter_ref == "pulse.drive.amplitude"`。
7. physical/control path 下所有非空 L0 引用已通过 L1/L0 gate。

### 5.2 编译输出

Rabi MVP 至少产生：

1. 一个 drive `PulseMoment`。
2. 一个 readout/acquire `PulseMoment` 或独立 `AcquireWindow`。
3. 一个 drive `FrameEvent` 占位。
4. 一个结构化 `SweepSpec`，完整保留 scan values。
5. `ResourceUsage`，包含 line ids、points、shots、duration estimate。
6. `CompileDiagnostic`，至少允许 info/warning 级别输出。
7. `content_hash` / `bundle_hash` 的实现计划；如果暂未实现，必须在诊断中说明。

### 5.3 参数绑定

Rabi drive moment 不应把每个 amplitude 展开成多个最终脉冲。建议：

```yaml
moments:
  - moment_id: moment.drive.000
    kind: drive
    line_id: line.q000.xy
    t0_ns: 0.0
    duration_ns: 40.0
    template_ref: pulse.rabi.gaussian/v0
    parameters:
      sigma_ns: 8.0
    sweep_bindings:
      amplitude: sweep.axis.amp
sweep:
  axes:
    - axis_id: amp
      parameter_ref: pulse.drive.amplitude
      unit: a.u.
      values: [0.0, 0.05, 0.10, 0.15, 0.20]
```

当前实现把代表性 amplitude 放在 `PulseMoment.amplitude`，同时把 scan 放在 metadata。该行为可作为 demo 过渡，但不应成为稳定 CPIR 契约。

## 6. 编译流程

```text
ExperimentSpec / dict
  -> L2 canonicalize_l1_spec()
  -> validate MVP atom + scan + no waveform
  -> extract target, do, plan, acquisition, L0 refs
  -> build SweepSpec
  -> build PulseMoment / FrameEvent / AcquireWindow
  -> build PulseIR
  -> canonical dump + content hash
  -> build CompiledBundle + diagnostics
```

失败规则：

1. 非 Atom 输入直接失败。
2. 未知 atom_kind 直接失败。
3. 缺失 scan 或 scan axis 不合法直接失败。
4. 输入或输出发现 waveform 数组直接失败。
5. physical path 缺少必要 L0 refs 或 L0 gate 未通过时直接失败。
6. canonical hash 无法生成时直接失败，除非明确处于 demo-only 模式。

## 7. 与 L1 / L3 / L7 / L5 的接口关系

### 7.1 与 L1 / EL

L2 消费 L1 的结构化意图，不重新解释用户脚本。L2 必须保留以下谱系：

1. `source_spec_id`
2. `source_spec_hash`
3. `atom_id`
4. `target`
5. `plan.scan`
6. `do.pulse_template_ref`
7. 必要 L0 refs

L2 不应修改 L1 spec，也不应把编译默认值写回 L1。

### 7.2 与 L3 / EB

L3 消费 `CompiledBundle`，负责后端能力检查、真实上传、运行状态和结果返回。L2 可以生成资源需求和能力约束，但不能管理硬件会话。

### 7.3 与 L7 / TRH

L7 Twin / Virtual / Replay 应优先消费 `PulseIR` 或 `CompiledBundle`，不应直接依赖 L1。这样虚拟路径和真实路径可以共享编译结果。

MVP 阶段若 L7 仍读取 `metadata.scan`，需要在 L7 TODO 中迁移到 `pulse_ir.sweep`。

### 7.4 与 L5 / DS

L5 的 `RunManifest` 至少应记录：

1. L1 spec ref/hash。
2. L0 snapshot refs/hash。
3. `PulseIR.content_hash`。
4. `CompiledBundle.bundle_hash`。
5. compiler version。
6. diagnostics。
7. compile duration。

## 8. 当前实现差距

当前 `qxtrl/cpir` 已能支撑 L1 -> L7 Rabi demo，但仍属于 prototype：

| 项 | 当前状态 | 稳定目标 |
| --- | --- | --- |
| `PulseIR` | dataclass，无 schema_version | frozen Pydantic/value object，`qxtrl.cpir.PulseIR/v0.1` |
| scan | `metadata.scan` | 结构化 `SweepSpec`，metadata 只镜像 |
| bundle | 暂无 | `CompiledBundle` |
| diagnostics | 暂无 | `CompileDiagnostic` |
| hash | 暂无 | canonical JSON + content hash |
| waveform 防线 | 依赖 L1 为主 | L2 递归检查输入与输出 |
| 输入再验证 | 暂未明确 | `canonicalize_l1_spec()` |
| 资源估算 | 暂无 | `ResourceUsage` |

这不阻塞 MVP demo，但在 L2 被 L4/L5/L7 正式依赖前应至少关闭：schema、sweep、diagnostic、hash、no-waveform guard。

## 9. 测试与验收标准

### 9.1 MVP 必须测试

| 测试 | 目的 |
| --- | --- |
| `test_compile_rabi_produces_pulseir_with_structured_sweep` | Rabi spec 编译出结构化 sweep |
| `test_compile_rejects_non_atom` | MVP 只支持 Atom |
| `test_compile_rejects_unknown_atom_kind` | 防止未注册实验隐式通过 |
| `test_compile_rejects_bad_scan_axis` | 只允许 `pulse.drive.amplitude` |
| `test_pulseir_no_waveform_arrays_recursive` | 输入/输出均不允许 waveform/samples/ndarray |
| `test_compile_revalidates_l1_input` | L2 边界重新验证 L1 spec |
| `test_compiled_bundle_has_source_hashes` | 谱系可追踪 |
| `test_compile_is_deterministic` | 相同输入产生相同 hash |
| `test_l7_consumes_pulseir_sweep_not_l1` | L7 不直接依赖 L1 scan |

### 9.2 集成验收

1. `create_rabi_experiment_spec()` 生成的 spec 可编译为 `CompiledBundle`。
2. bundle 可由 L7 virtual 跑出固定 seed 下可复现 Rabi 数据。
3. L6 能基于结果产生 `ParameterPatchProposal`。
4. L5 manifest 能记录 spec/hash、bundle/hash、diagnostics 和结果 ref。
5. 关闭实时 UI/DataSink 不影响编译和执行。

## 10. 决策表

| ID | 问题 | 建议结论 | 状态 |
| --- | --- | --- | --- |
| L2-D-001 | PulseIR 用 dataclass 还是 Pydantic？ | 稳定边界使用 frozen Pydantic/value object；当前 dataclass 只作为 demo 过渡 | 建议采纳 |
| L2-D-002 | scan 放 metadata 还是独立 Sweep？ | 独立 `SweepSpec` 为权威字段，metadata 只镜像 | 建议采纳 |
| L2-D-003 | `pulse_template_ref` 如何解析？ | MVP 白名单透传；真实解析后置到模板库/renderer | 待细化 |
| L2-D-004 | 单位系统如何处理？ | 时间统一 `ns`，频率 `Hz`，相位 `rad`；幅度 MVP 用 `a.u.` | 建议采纳 |
| L2-D-005 | 内容哈希如何生成？ | canonical JSON，排除非确定性字段 | 待实现 |
| L2-D-006 | `compile_experiment_spec()` 返回什么？ | 保留返回 `PulseIR` 兼容 demo，新增 `compile_to_bundle()` 作为正式接口 | 建议采纳 |
| L2-D-007 | L7 是否可直接读 L1？ | 不建议。L7 应消费 `PulseIR`/`CompiledBundle` | 建议采纳 |

## 11. 开发建议

推荐按以下顺序推进：

1. 把 `PulseIR`、`PulseMoment`、`FrameEvent`、`AcquireWindow`、`SweepSpec` 改成 frozen Pydantic model。
2. 保留当前 `compile_experiment_spec()`，但内部先调用 canonicalize，再输出新 `PulseIR`。
3. 新增 `compile_to_bundle()`，返回 `CompiledBundle`。
4. 补充 no-waveform recursive guard。
5. 补充 canonical dump/hash 工具。
6. 将 L7 virtual 从 `metadata.scan` 迁移到 `pulse_ir.sweep`。
7. 扩充负向测试和 roundtrip 集成测试。

## 12. 后续升版条件

满足以下任一条件时，启动 v0.3：

1. 支持第二个 Atom（如 S21 / qubit spectroscopy）。
2. L3 ExecutionBackend 需要正式消费 `CompiledBundle`。
3. L4 Runtime 需要根据 `ResourceUsage` 做排队或 factory pipeline。
4. L5 RunManifest 开始依赖 bundle/hash 做回放。
5. L1 开始支持有限 Task 递归。
6. 需要正式的模板解析、frame convention 或 pulse renderer。

## 13. 结论

L2/CPIR 的设计方向应比当前实现更严格：当前实现可以继续作为 Rabi demo 薄切片，但稳定契约必须尽早落到 typed schema、结构化 sweep、编译诊断、内容哈希和 bundle 谱系上。

这样后续 L3 真实后端、L7 数字孪生、L5 回放记录和 L6 自动校准才能消费同一个编译产物，而不是分别解释 L1 实验意图。
