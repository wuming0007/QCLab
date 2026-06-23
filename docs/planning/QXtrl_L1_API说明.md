# QXtrl L1 Experiment Language API 说明

**版本**: v0.1  
**日期**: 2026-06-22  
**状态**: 当前实现说明，面向 L2+ 开发、校准逻辑和后续审查  
**代码范围**: `qxtrl/el/`  
**Schema 前缀**: `qxtrl.el.*`  
**关联文档**:
- [QXtrl_L1_Experiment_Language_设计.md](QXtrl_L1_Experiment_Language_设计.md)
- [QXtrl_L2_CPIR_Compiler_PulseIR_设计.md](QXtrl_L2_CPIR_Compiler_PulseIR_设计.md)
- [QXtrl_L0_API说明.md](QXtrl_L0_API说明.md)
- [QXtrl_MVP最薄垂直切片定义.md](QXtrl_MVP最薄垂直切片定义.md)

## 0. 文档目的与范围

本文档说明 QXtrl L1 / EL Experiment Language 当前 Python API 的用途、字段、方法、校验规则和典型用法。

L1 的职责是把实验意图结构化，形成可验证、可编译、可审计的 `ExperimentSpec`。当前 MVP 只支持 Rabi amplitude Atom。

L1 负责：

1. 描述实验目标、target、scan、acquisition、do/check/act、PDCA path。
2. 声明 L0 上下文和 L0 gate 依赖。
3. 约束高层实验意图不携带最终 waveform / samples。
4. 为 L2 / CPIR 提供可编译输入。
5. 为 L5 / RunManifest 和 L6 / Calibration 提供结构化谱系。

L1 不负责：

1. 生成 `PulseIR` 或 `CompiledBundle`。
2. 生成最终 waveform arrays。
3. 设备上传、执行、采集。
4. 拟合算法实现。
5. 参数写回 active config。
6. UI 或运行调度。

## 1. 导入方式与公开 API

推荐从 `qxtrl.el` 统一导入公开 API：

```python
from qxtrl.el import (
    ExperimentSpec,
    AtomSpec,
    PlanSpec,
    DoSpec,
    CheckSpec,
    ActSpec,
    TargetSpec,
    ScanSpec,
    ScanAxisSpec,
    AcquisitionSpec,
    L0ContextRef,
    PDCAPathItem,
    NodeIOContract,
    TypedRef,
    RegistryEntry,
    ParameterProposalTarget,
    create_rabi_experiment_spec,
    registry,
)
```

当前 `qxtrl.el.__all__` 导出的对象包括：

| 类别 | 名称 |
| --- | --- |
| 顶层实验 | `ExperimentSpec`, `AtomSpec` |
| PDCA | `PlanSpec`, `DoSpec`, `CheckSpec`, `ActSpec`, `PDCAPathItem` |
| target / scan / acquisition | `TargetSpec`, `ScanSpec`, `ScanAxisSpec`, `AcquisitionSpec` |
| L0 与 IO | `L0ContextRef`, `NodeIOContract`, `TypedRef` |
| registry | `RegistryEntry`, `registry` |
| 校准动作 | `ParameterProposalTarget` |
| 示例工厂 | `create_rabi_experiment_spec` |

## 2. 关键契约规则

### 2.1 schema version

当前唯一合法顶层 schema：

```text
qxtrl.el.ExperimentSpec/v0.1
```

`ExperimentSpec` validator 使用精确匹配。未来版本不能只靠 prefix 兼容。

### 2.2 MVP 只支持 Atom

当前实现拒绝：

1. `node_kind != "atom"`。
2. `children` 非空。
3. 缺失 `atom`。

Task / Session 递归结构保留在字段上，但当前不会通过 validator。

### 2.3 L0 gate

`L0ContextRef` 可以接收字符串 ref、`L0SnapshotRef` 或实际 L0 对象。

当传入实际 L0 对象，`ExperimentSpec` validator 会调用：

```python
ref.require_usable_for_control(context=f"l1.validate.{name}")
```

因此 physical/control path 下，未审批、撤销或不可用于控制的 L0 对象会被拒绝。

### 2.4 无 waveform 高层规则

`DoSpec.parameters` 和 `DoSpec.compile_hints` 递归拒绝以下高风险字段：

```text
waveform, waveforms, ndarray, samples, raw_iq_array, device_opcode
```

L1 只描述意图和参数，不承载最终采样数组或设备私有 opcode。

### 2.5 `parameter_ref` MVP 语法

当前支持两类：

```text
pulse.<role>.<name>
calibration.<element_id>.<logical_channel>.<param>
```

MVP 中 `pulse.<role>.<name>` 只允许 `role == "drive"`。

`calibration.*` 会校验 `<element_id>` 是否符合 L0 element id 规则，并在 `ExperimentSpec` 层检查 element 是否与 target 一致。

### 2.6 不可变和演化方式

主要 L1 Pydantic model 都配置：

```python
model_config = {"frozen": True}
```

集合字段使用 tuple，避免 validation 后原地清空或追加。生成派生 spec 时不要使用裸 `model_copy(update=...)`，应使用：

```python
new_spec = spec.validated_copy(...)
```

## 3. 核心对象 API

### 3.1 `L0ContextRef`

**目的**: 明确一次实验依赖的 L0 上下文。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `chip_model_ref` | `L0SnapshotRef | str | ChipModel` | 芯片模型 ref 或对象 |
| `wiring_graph_ref` | `L0SnapshotRef | str | WiringGraph` | 连线图 ref 或对象 |
| `hardware_inventory_ref` | `L0SnapshotRef | str | HardwareInventory` | 硬件清单 ref 或对象 |
| `safety_policy_ref` | `L0SnapshotRef | str | SafetyPolicy` | 安全策略 ref 或对象 |
| `calibration_ref` | `L0SnapshotRef | str | Any | None` | 校准快照 ref，占位 |

示例：

```python
from qxtrl.el import L0ContextRef

ctx = L0ContextRef(
    chip_model_ref="chip.demo_rabi_001",
    wiring_graph_ref="wiring.chip.demo_rabi_001",
    hardware_inventory_ref="hw.station.demo01",
    safety_policy_ref="safety.station.demo01",
)
```

### 3.2 `PDCAPathItem`

**目的**: 记录当前节点在递归 PDCA 路径中的位置，供 RunManifest 和审计使用。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `node_id` | `str` | 节点 ID，例如 `atom.rabi.q000` |
| `node_kind` | `atom | task | session` | 节点类型 |
| `pdca_phase` | `plan | do | check | act` | 所属 PDCA 阶段 |
| `iteration` | `int | None` | 迭代轮次 |
| `parent_node_id` | `str | None` | 父节点 ID，MVP 可为空 |

### 3.3 `TypedRef`

**目的**: 通用 typed reference，用于 IO contract 和跨层引用。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `kind` | `str` | 引用类别，例如 `qubit`、`line`、`observation` |
| `ref` | `str` | 引用 ID |
| `optional` | `bool` | 是否可选 |
| `unit` | `str | None` | 单位说明 |

### 3.4 `TargetSpec`

**目的**: 描述实验目标量子对象和相关逻辑 line。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `element_id` | `str` | L0 element id，例如 `q000` |
| `drive_line_id` | `str | None` | drive line，例如 `line.xy.q000` |
| `readout_line_id` | `str | None` | readout line，例如 `line.ro.rr_q000` |
| `coupler_id` | `str | None` | coupler element id |
| `logical_role` | `str | None` | 逻辑角色，占位 |

校验：

1. `element_id` 使用 L0 `validate_element_id()`。
2. line 字段使用 L0 `validate_line_id()`。
3. `coupler_id` 使用 L0 `validate_element_id()`。

### 3.5 `ScanAxisSpec`

**目的**: 描述一个扫描轴。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `axis_id` | `str` | 轴 ID，例如 `amp` |
| `parameter_ref` | `str` | 被扫描参数，例如 `pulse.drive.amplitude` |
| `unit` | `str` | 单位，必须在 L0 `KNOWN_UNITS` 中 |
| `values` | `tuple[float, ...]` | 扫描值，非空，不允许 bool/NaN/Inf |
| `description` | `str | None` | 说明 |

示例：

```python
from qxtrl.el import ScanAxisSpec

axis = ScanAxisSpec(
    axis_id="amp",
    parameter_ref="pulse.drive.amplitude",
    unit="a.u.",
    values=(0.0, 0.05, 0.10),
)
```

### 3.6 `ScanSpec`

**目的**: 描述扫描策略。

| 字段 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `axes` | `tuple[ScanAxisSpec, ...]` | 必填 | 扫描轴 |
| `order` | `cartesian | zipped` | `cartesian` | 多轴组合方式 |
| `randomization` | `none | shuffled` | `none` | 随机化策略 |

当前 Rabi MVP 由 L2 进一步限制为单轴 `pulse.drive.amplitude`。

### 3.7 `AcquisitionSpec`

**目的**: 描述采集 shots 和结果层级。

| 字段 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `shots` | `int` | 必填 | 必须 > 0 |
| `result_level` | `iq | classified | counts` | `iq` | 结果类型 |
| `averaging` | `single_shot | average` | `average` | 平均方式 |

### 3.8 `PlanSpec`

**目的**: 描述实验计划层面的目标、target、scan 和 acquisition。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `objective` | `str` | 实验目标，例如 `estimate_pi_amp` |
| `target` | `TargetSpec` | 目标对象 |
| `scan` | `ScanSpec` | 扫描设置 |
| `acquisition` | `AcquisitionSpec` | 采集设置 |
| `constraints` | `dict[str, Any]` | 约束，占位 |

### 3.9 `DoSpec`

**目的**: 描述如何执行 Atom，但不包含最终波形。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `atom_ref` | `str` | Atom 模板引用，例如 `qxtrl.atom.rabi_amplitude/v0.1` |
| `pulse_template_ref` | `str | None` | pulse 模板引用 |
| `parameters` | `dict[str, Any]` | 参数，可含 L0 `Quantity` |
| `compile_hints` | `dict[str, Any]` | 编译提示 |

示例：

```python
from qxtrl.cc import Quantity
from qxtrl.el import DoSpec

do = DoSpec(
    atom_ref="qxtrl.atom.rabi_amplitude/v0.1",
    pulse_template_ref="qxtrl.pulse.rabi_gaussian/v0.1",
    parameters={"pulse_duration": Quantity(value=40.0, unit="ns")},
    compile_hints={"frame_policy": "use_l0_defaults"},
)
```

### 3.10 `CheckSpec`

**目的**: 描述执行后如何分析和判断结果。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `analyzer_ref` | `str` | 分析器引用 |
| `expected_observation` | `str` | 期望 observation 类型 |
| `metrics` | `tuple[str, ...]` | 必须非空 |
| `acceptance` | `dict[str, Any]` | 接受标准，必须非空 |

### 3.11 `ParameterProposalTarget`

**目的**: 声明可被 `ActSpec` 生成候选 patch 的参数。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `parameter_ref` | `str` | 目标参数，例如 `calibration.q000.xy.pi_amp` |
| `source_metric` | `str` | 来源 metric，例如 `pi_amp` |

### 3.12 `ActSpec`

**目的**: 描述分析后的动作。当前只生成候选，不直接写 active config。

| 字段 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `mode` | `none | propose_patch | request_review` | `propose_patch` | 动作类型 |
| `proposal_targets` | `tuple[ParameterProposalTarget, ...]` | 空 tuple | 候选目标 |
| `requires_review` | `bool` | `False` | 是否需要人工 review |

校验：

```text
mode == "propose_patch" 时 proposal_targets 必须非空。
```

### 3.13 `NodeIOContract`

**目的**: SCP-001 typed edge，声明节点输入、输出、失效和依赖。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `consumes` | `tuple[TypedRef, ...]` | 消费对象 |
| `produces` | `tuple[TypedRef, ...]` | 产出对象 |
| `invalidates` | `tuple[TypedRef, ...]` | 失效对象 |
| `depends_on` | `tuple[TypedRef, ...]` | 依赖对象 |

MVP `ExperimentSpec` 要求 `consumes` 和 `produces` 均非空。

### 3.14 `AtomSpec`

**目的**: 叶子实验节点。MVP 中只有 Atom 能进入 L2/L3 执行链。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `atom_id` | `str` | Atom ID，例如 `atom.rabi.q000` |
| `atom_kind` | `str` | Atom 类型，例如 `rabi.amplitude` |
| `atom_version` | `str` | Atom 版本 |
| `target` | `TargetSpec` | 目标 |
| `scan` | `ScanSpec` | 扫描 |
| `acquisition` | `AcquisitionSpec` | 采集 |
| `capability_requirements` | `tuple[str, ...]` | 后端能力要求 |

### 3.15 `ExperimentSpec`

**目的**: L1 顶层实验规格，是 L2 编译入口的正式输入。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `schema_version` | `str` | 必须为 `qxtrl.el.ExperimentSpec/v0.1` |
| `spec_id` | `str` | 实验 ID |
| `display_name` | `str | None` | 展示名称 |
| `node_kind` | `atom | task | session` | MVP 只允许 `atom` |
| `atom` | `AtomSpec | None` | MVP 必填 |
| `children` | `tuple[ExperimentSpec, ...]` | MVP 必须为空 |
| `pdca_path` | `tuple[PDCAPathItem, ...]` | PDCA 谱系 |
| `l0_context` | `L0ContextRef` | L0 上下文 |
| `plan` | `PlanSpec` | Plan |
| `do` | `DoSpec` | Do |
| `check` | `CheckSpec` | Check |
| `act` | `ActSpec` | Act |
| `io` | `NodeIOContract` | IO contract |
| `metadata` | `dict[str, Any]` | 非核心补充信息 |

主要校验：

1. MVP 只允许 Atom。
2. schema version 精确匹配。
3. L0 object ref 自动 gate。
4. `plan/do/check/act` 均存在。
5. `io.consumes` / `io.produces` 均非空。
6. `atom.target.element_id == plan.target.element_id`。
7. `calibration.*` parameter_ref 的 element 与 target 一致。

主要方法：

| 方法 | 目的 |
| --- | --- |
| `validated_copy(**updates)` | 生成重新验证后的派生 `ExperimentSpec` |

示例：

```python
from qxtrl.el import create_rabi_experiment_spec

spec = create_rabi_experiment_spec(qubit_id="q000")
updated = spec.validated_copy(display_name="Rabi q000 - review copy")
```

不要这样做：

```python
# 不推荐：Pydantic model_copy(update=...) 默认不重新运行全部 validator。
unsafe = spec.model_copy(update={"node_kind": "task"})
```

## 4. Registry API

### 4.1 `RegistryEntry`

**目的**: 描述 Atom、Analyzer、Optimizer、Backend、Storage 等插件或模板。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `entry_id` | `str` | 注册 ID |
| `entry_kind` | `atom | analyzer | optimizer | backend | storage` | 注册类别 |
| `version` | `str` | 版本 |
| `display_name` | `str | None` | 展示名称 |
| `input_schema` | `str` | 输入 schema |
| `output_schema` | `str` | 输出 schema |
| `capabilities` | `tuple[str, ...]` | 能力声明 |
| `compatible_l1_versions` | `tuple[str, ...]` | 兼容的 L1 schema |
| `io_contract_template` | `NodeIOContract | None` | IO 模板，占位 |

### 4.2 `registry`

当前实现提供一个全局内存 registry，类型为内部 `_SimpleRegistry`。

| 方法 | 参数 | 返回 | 说明 |
| --- | --- | --- | --- |
| `register(entry)` | `RegistryEntry` | `None` | 注册或覆盖 entry |
| `resolve(entry_id, l1_version)` | `str, str` | `RegistryEntry` | 按 ID 和 L1 版本解析 |

默认注册：

1. `qxtrl.atom.rabi_amplitude/v0.1`
2. `qxtrl.check.rabi_fit/v0.1`

示例：

```python
from qxtrl.el import registry

entry = registry.resolve(
    "qxtrl.atom.rabi_amplitude/v0.1",
    "qxtrl.el.ExperimentSpec/v0.1",
)
print(entry.capabilities)
```

## 5. 示例工厂

### 5.1 `create_rabi_experiment_spec()`

**目的**: 创建符合 MVP 规则的 Rabi amplitude scan `ExperimentSpec`。

签名：

```python
def create_rabi_experiment_spec(
    qubit_id: str = "q000",
    drive_line_id: str = "line.xy.q000",
    readout_line_id: str = "line.ro.rr_q000",
    amplitudes: list[float] = None,
    shots: int = 1024,
    pulse_duration_ns: float = 40.0,
    l0_chip_model_ref: str = "chip.demo_rabi_001",
    l0_wiring_ref: str = "wiring.chip.demo_rabi_001",
    l0_hw_ref: str = "hw.station.demo01",
    l0_safety_ref: str = "safety.station.demo01",
) -> ExperimentSpec:
    ...
```

返回对象具有：

1. `atom.atom_kind == "rabi.amplitude"`。
2. 单 scan axis：`pulse.drive.amplitude`。
3. 默认 amplitudes：`[0.0, 0.05, 0.10, 0.15, 0.20]`。
4. 默认 `DoSpec.atom_ref == "qxtrl.atom.rabi_amplitude/v0.1"`。
5. 默认 `ActSpec` 只生成 `calibration.<qubit>.xy.pi_amp` 候选。

示例：

```python
from qxtrl.cc import minimal_rabi_lab
from qxtrl.el import create_rabi_experiment_spec

lab = minimal_rabi_lab()
spec = create_rabi_experiment_spec(
    qubit_id="q000",
    l0_chip_model_ref=lab["chip"],
    l0_wiring_ref=lab["wiring"],
    l0_hw_ref=lab["hardware"],
    l0_safety_ref=lab["safety"],
)

print(spec.spec_id)
print(spec.plan.scan.axes[0].values)
```

## 6. L1 到 L2 的推荐用法

```python
from qxtrl.el import create_rabi_experiment_spec
from qxtrl.cpir import compile_to_bundle

spec = create_rabi_experiment_spec()
bundle = compile_to_bundle(spec)
```

L2 会在边界重新验证 L1：

```python
ExperimentSpec.model_validate(spec.model_dump(mode="python"))
```

因此 L1 开发者应保持：

1. 所有实验意图都进入 `ExperimentSpec`。
2. 不要用 ad hoc dict 旁路 validator。
3. 需要派生 spec 时使用 `validated_copy()`。

## 7. 常见错误示例

### 7.1 waveform 被拒绝

```python
from qxtrl.el import DoSpec

DoSpec(
    atom_ref="qxtrl.atom.rabi_amplitude/v0.1",
    parameters={"waveform": [0.0, 1.0]},
)
# raises QXtrlValidationError
```

### 7.2 非法 scan value 被拒绝

```python
from qxtrl.el import ScanAxisSpec

ScanAxisSpec(
    axis_id="amp",
    parameter_ref="pulse.drive.amplitude",
    unit="a.u.",
    values=(True,),
)
# raises QXtrlValidationError
```

### 7.3 target 与 calibration ref 不一致被拒绝

```python
# target 是 q000，但 proposal target 指向 q001 时，
# ExperimentSpec validator 会拒绝。
```

## 8. 测试与验收

推荐命令：

```bash
PYTHONPATH=. python3 -m pytest qxtrl/el/tests/ -q
PYTHONPATH=. python3 -m pytest qxtrl -q
python3 -m ruff check qxtrl/el
```

当前 L1 测试覆盖重点：

1. 合法 Rabi spec 构造。
2. schema version 精确绑定。
3. no-waveform guard。
4. `children` / 非 Atom 拒绝。
5. L0 gate。
6. scan unit / bool / NaN / Inf。
7. parameter_ref 语法和 target 一致性。
8. 不可变与 mutation 抵抗。
9. `validated_copy()`。

## 9. 当前边界和后续增强

当前边界：

1. 只支持 Rabi amplitude Atom。
2. Task / Session 字段存在但被 MVP validator 拒绝。
3. Registry 为内存实现，不是插件发现系统。
4. `metadata` / `parameters` 等 dict 字段仍需在跨层边界重新 validate。
5. 完整优化器、黑板、checkpoint 和回滚策略不在 L1 MVP。

后续建议：

1. 新增第二个 Atom 后，抽象 Atom-specific validator。
2. Task/Session 开放前，先定义递归 PDCA schema 和 path 规则。
3. Registry 替换为可版本化、可发现的插件注册表。
4. 与 L6 calibration graph 对齐 `NodeIOContract` typed edge。
