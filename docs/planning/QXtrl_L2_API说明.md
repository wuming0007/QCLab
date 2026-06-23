# QXtrl L2 CPIR Compiler / Pulse IR API 说明

**版本**: v0.1  
**日期**: 2026-06-22  
**状态**: 当前实现说明，面向 L3 / L4 / L5 / L7 开发和后续审查  
**代码范围**: `qxtrl/cpir/`  
**Schema 前缀**: `qxtrl.cpir.*`  
**关联文档**:
- [QXtrl_L2_CPIR_Compiler_PulseIR_设计.md](QXtrl_L2_CPIR_Compiler_PulseIR_设计.md)
- [QXtrl_L3_EB_ExecutionBackend_设计.md](QXtrl_L3_EB_ExecutionBackend_设计.md)
- [QXtrl_L1_API说明.md](QXtrl_L1_API说明.md)
- [QXtrl_MVP最薄垂直切片定义.md](QXtrl_MVP最薄垂直切片定义.md)

## 0. 文档目的与范围

本文档说明 QXtrl L2 / CPIR 当前 Python API 的用途、字段、方法、编译入口、校验规则和典型用法。

L2 的职责是把 L1 / EL `ExperimentSpec` 编译成后端可消费、可审查、可哈希、可回放的硬件无关中间表示：

```text
ExperimentSpec -> PulseIR -> CompiledBundle
```

当前 MVP 只支持 Rabi amplitude Atom。

L2 负责：

1. 在编译边界重新验证 L1 输入。
2. 生成结构化 `SweepSpec`。
3. 生成模板化 `PulseMoment`、`FrameEvent`、`AcquireWindow`。
4. 维护 Rabi MVP frame consistency。
5. 生成 `PulseIR.content_hash` 和 `CompiledBundle.bundle_hash`。
6. 提供 `verify_compiled_bundle()` 给 L3/L4/L5 使用。

L2 不负责：

1. 后端执行、设备上传、采集。
2. 最终 waveform arrays 的长期保存。
3. 调度和资源锁。
4. Rabi 拟合和参数候选。
5. 真实硬件能力查询。

## 1. 导入方式与公开 API

推荐从 `qxtrl.cpir` 统一导入公开 API：

```python
from qxtrl.cpir import (
    compile_experiment_spec,
    compile_to_bundle,
    verify_compiled_bundle,
    PulseIR,
    PulseMoment,
    FrameEvent,
    SweepSpec,
    SweepAxis,
    AcquireWindow,
    ResourceUsage,
    CompileDiagnostic,
    CompiledBundle,
)
```

当前 `qxtrl.cpir.__all__` 导出的对象包括：

| 类别 | 名称 |
| --- | --- |
| 编译入口 | `compile_experiment_spec`, `compile_to_bundle`, `verify_compiled_bundle` |
| IR 核心 | `PulseIR`, `PulseMoment`, `FrameEvent`, `AcquireWindow` |
| 扫描与资源 | `SweepSpec`, `SweepAxis`, `ResourceUsage` |
| bundle 与诊断 | `CompileDiagnostic`, `CompiledBundle` |

## 2. 关键契约规则

### 2.1 schema version

当前 schema：

```text
qxtrl.cpir.PulseIR/v0.1
qxtrl.cpir.CompileDiagnostic/v0.1
qxtrl.cpir.CompiledBundle/v0.1
```

### 2.2 Rabi MVP 限制

当前编译器只支持：

1. `ExperimentSpec.node_kind == "atom"`。
2. `atom.atom_kind == "rabi.amplitude"`。
3. `do.atom_ref == "qxtrl.atom.rabi_amplitude/v0.1"`。
4. exactly one `plan.scan.axes`。
5. `parameter_ref == "pulse.drive.amplitude"`。
6. `plan.scan` 与 `atom.scan` axis 数量、parameter_ref 和 values 一致。

### 2.3 不携带最终 waveform

`PulseMoment.parameters`、`PulseMoment.sweep_bindings`、`PulseIR.target`、`PulseIR.metadata` 递归拒绝：

```text
waveform, waveforms, samples, iq_array, dac_samples, adc_samples, ndarray, raw_data
```

### 2.4 Frame consistency

当前 `PulseIR` validator 对 Rabi MVP 执行：

1. `drive` / `readout` 这类 coherent `PulseMoment` 必须有 `frame_id`。
2. `frame_id` 必须存在于 `PulseIR.frames`。
3. moment line 与 frame line 必须一致。
4. frame event 时间不能晚于 moment 开始时间。
5. 每条 line 上 frame events 的 `t0_ns` 单调。
6. moment / acquisition window 不得超过 `total_duration_ns`。

说明：当前 frame 模型足以支持 Rabi MVP 的单 drive frame。Ramsey / echo / virtual-Z 需要后续扩展 `FrameDefinition / FrameUpdate / FrameState`。

### 2.5 安全演化方式

主要 CPIR model 配置 `frozen=True`，并提供部分 `validated_copy()` 方法。

推荐：

```python
new_ir = ir.validated_copy(content_hash="...")
```

不推荐：

```python
unsafe = ir.model_copy(update={"total_duration_ns": -1})
```

说明：Pydantic 裸 `model_copy(update=...)` 默认不重新运行 validator。跨层入口必须调用 `verify_compiled_bundle()` 或重新 `model_validate(model_dump())`。

## 3. IR 对象 API

### 3.1 `SweepAxis`

**目的**: 描述一个 CPIR 扫描轴。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `axis_id` | `str` | 轴 ID，例如 `amp` |
| `parameter_ref` | `str` | 被扫参数，例如 `pulse.drive.amplitude` |
| `unit` | `str` | 单位，例如 `a.u.` |
| `values` | `tuple[float, ...]` | 扫描值，非空，不允许 bool/NaN/Inf |

示例：

```python
from qxtrl.cpir import SweepAxis

axis = SweepAxis(
    axis_id="amp",
    parameter_ref="pulse.drive.amplitude",
    unit="a.u.",
    values=(0.0, 0.05, 0.10),
)
```

### 3.2 `SweepSpec`

**目的**: 作为 `PulseIR` 中 scan 的权威字段。

| 字段 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `axes` | `tuple[SweepAxis, ...]` | 必填 | 扫描轴，MVP 至少一个 |
| `mode` | `grid | zip` | `grid` | 组合模式 |
| `order` | `as_declared | randomized` | `as_declared` | 执行顺序 |
| `seed` | `int | None` | `None` | 随机种子 |

MVP 中 `order="randomized"` 会被拒绝。

### 3.3 `PulseMoment`

**目的**: 描述模板化 pulse / acquire / wait / barrier moment，不展开最终采样数组。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `moment_id` | `str` | moment ID |
| `kind` | `drive | readout | wait | barrier | acquire` | moment 类型 |
| `line_id` | `str` | 逻辑 line |
| `t0_ns` | `float` | 起始时间，非负，不允许 bool/NaN/Inf |
| `duration_ns` | `float` | 持续时间，必须 > 0 |
| `template_ref` | `str | None` | 模板引用 |
| `parameters` | `dict[str, Any]` | 参数，不能含 waveform/samples |
| `sweep_bindings` | `dict[str, str]` | 参数到 sweep axis 的绑定 |
| `frame_id` | `str | None` | coherent `drive/readout` 必填 |

主要方法：

| 方法 | 目的 |
| --- | --- |
| `validated_copy(**updates)` | 生成重新验证的派生 `PulseMoment` |

示例：

```python
from qxtrl.cpir import PulseMoment

drive = PulseMoment(
    moment_id="moment.drive.atom.rabi.q000",
    kind="drive",
    line_id="line.xy.q000",
    t0_ns=0.0,
    duration_ns=40.0,
    template_ref="qxtrl.pulse.rabi_gaussian/v0.1",
    parameters={"sigma_ns": 8.0},
    sweep_bindings={"amplitude": "sweep.axis.amp"},
    frame_id="frame.drive.atom.rabi.q000",
)
```

### 3.4 `FrameEvent`

**目的**: 定义 Rabi MVP 中的 frame 初始状态事件。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `frame_id` | `str` | frame ID |
| `line_id` | `str` | 对应 line |
| `t0_ns` | `float` | 起始时间，非负，不允许 bool |
| `phase_rad` | `float` | 相位，默认 0 |
| `frequency_hz` | `float | None` | 频率，占位 |

当前不是完整 frame update log。后续支持 virtual-Z 时需要增加 operation 语义。

### 3.5 `AcquireWindow`

**目的**: 描述采集窗口。

| 字段 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `window_id` | `str` | 必填 | 采集窗口 ID |
| `line_id` | `str` | 必填 | readout line |
| `t0_ns` | `float` | 必填 | 起始时间，非负 |
| `duration_ns` | `float` | 必填 | 持续时间，必须 > 0 |
| `result_level` | `raw_iq | integrated_iq | classified` | `integrated_iq` | 结果层级 |
| `integration_kernel_ref` | `str | None` | `None` | 积分核引用 |

### 3.6 `ResourceUsage`

**目的**: 估算执行资源，供 L3/L4/L5 使用。

| 字段 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `line_ids` | `tuple[str, ...]` | `()` | 涉及 line |
| `estimated_points` | `int` | `0` | 估计扫描点数，非负 |
| `estimated_shots` | `int` | `0` | 估计 shots，非负 |
| `estimated_duration_ns_per_point` | `float` | `0.0` | 每点估计耗时，非负 |

### 3.7 `PulseIR`

**目的**: L2 的硬件无关 pulse 中间表示。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `schema_version` | `Literal["qxtrl.cpir.PulseIR/v0.1"]` | schema version |
| `ir_id` | `str` | IR ID |
| `source_spec_id` | `str` | 来源 L1 spec ID |
| `atom_id` | `str` | Atom ID |
| `target` | `dict[str, Any]` | target 镜像 |
| `sweep` | `SweepSpec` | 权威 sweep |
| `moments` | `tuple[PulseMoment, ...]` | pulse/acquire moments |
| `frames` | `tuple[FrameEvent, ...]` | frame events |
| `acquisition_windows` | `tuple[AcquireWindow, ...]` | 采集窗口 |
| `resources` | `ResourceUsage` | 资源估算 |
| `total_duration_ns` | `float` | 总时长 |
| `content_hash` | `str | None` | IR 内容 hash |
| `metadata` | `dict[str, Any]` | 过渡/诊断信息，不是权威 scan |

主要方法：

| 方法 | 目的 |
| --- | --- |
| `validated_copy(**updates)` | 生成重新验证的派生 `PulseIR` |

主要校验：

1. MVP exactly one sweep axis。
2. `parameter_ref == "pulse.drive.amplitude"`。
3. no-waveform guard。
4. `total_duration_ns` 覆盖 moment 和 acquisition window。
5. frame consistency。

## 4. Bundle 与诊断 API

### 4.1 `CompileDiagnostic`

**目的**: 编译诊断。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `schema_version` | `Literal["qxtrl.cpir.CompileDiagnostic/v0.1"]` | schema version |
| `severity` | `info | warning | error` | 严重程度 |
| `code` | `str` | 机器可读 code |
| `message` | `str` | 人可读信息 |
| `path` | `str | None` | 相关路径 |
| `hint` | `str | None` | 修复建议 |

### 4.2 `CompiledBundle`

**目的**: L2 提交给 L3/L4/L5/L7 的正式编译产物包装。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `schema_version` | `Literal["qxtrl.cpir.CompiledBundle/v0.1"]` | schema version |
| `bundle_id` | `str` | bundle ID |
| `pulse_ir` | `PulseIR` | 编译后的 IR |
| `diagnostics` | `tuple[CompileDiagnostic, ...]` | 编译诊断 |
| `l0_refs` | `tuple[str, ...]` | L0 ref / snapshot id，MVP 为字符串 |
| `source_spec_id` | `str` | L1 source spec ID |
| `source_spec_hash` | `str` | L1 source hash |
| `compiler_version` | `str` | 编译器版本，默认 `0.2-mvp` |
| `bundle_hash` | `str | None` | bundle 内容 hash |

主要方法：

| 方法 | 目的 |
| --- | --- |
| `validated_copy(**updates)` | 生成重新验证的派生 `CompiledBundle` |

## 5. 编译函数 API

### 5.1 `canonicalize_l1_spec()`

**位置**: `qxtrl.cpir.compiler`  
**公开程度**: 边界 helper，未从 `qxtrl.cpir.__all__` 导出。  
**目的**: 在 L2 边界重新验证 L1 输入。

签名：

```python
def canonicalize_l1_spec(spec: ExperimentSpec | dict[str, Any]) -> ExperimentSpec:
    ...
```

逻辑：

1. 如果输入是 `ExperimentSpec`，执行 `model_dump(mode="python")` 后 `ExperimentSpec.model_validate(...)`。
2. 如果输入是 dict，直接 `ExperimentSpec.model_validate(...)`。

### 5.2 `compile_experiment_spec()`

**目的**: 将 L1 `ExperimentSpec` 编译为 `PulseIR`。保留该函数主要为了 demo 兼容；稳定链路推荐 `compile_to_bundle()`。

签名：

```python
def compile_experiment_spec(spec: ExperimentSpec) -> PulseIR:
    ...
```

输入要求：

1. Rabi amplitude Atom。
2. 单 scan axis。
3. `do.atom_ref == "qxtrl.atom.rabi_amplitude/v0.1"`。

输出：

1. `PulseIR`。
2. drive moment + acquire moment。
3. drive frame event。
4. acquisition window。
5. structured `SweepSpec`。
6. `content_hash`。

示例：

```python
from qxtrl.el import create_rabi_experiment_spec
from qxtrl.cpir import compile_experiment_spec

spec = create_rabi_experiment_spec()
ir = compile_experiment_spec(spec)

print(ir.sweep.axes[0].values)
print(ir.content_hash)
```

### 5.3 `compile_to_bundle()`

**目的**: 官方稳定编译入口，返回 `CompiledBundle`。

签名：

```python
def compile_to_bundle(input: ExperimentSpec | dict[str, Any]) -> CompiledBundle:
    ...
```

输出包括：

1. `pulse_ir`。
2. `CompileDiagnostic(code="L2-COMPILE-OK")`。
3. `l0_refs`。
4. `source_spec_hash`。
5. `bundle_hash`。

示例：

```python
from qxtrl.el import create_rabi_experiment_spec
from qxtrl.cpir import compile_to_bundle

spec = create_rabi_experiment_spec()
bundle = compile_to_bundle(spec)

print(bundle.bundle_id)
print(bundle.bundle_hash)
```

### 5.4 `verify_compiled_bundle()`

**目的**: 为 L3 / L4 / L5 提供统一入口校验。下游层应优先调用它，而不是直接信任 Python 对象引用。

签名：

```python
def verify_compiled_bundle(bundle: CompiledBundle | dict[str, Any]) -> CompiledBundle:
    ...
```

执行检查：

1. schema / Pydantic re-validation。
2. `pulse_ir.content_hash` 校验。
3. `bundle.bundle_hash` 校验。
4. `diagnostics` 中不得有 `severity == "error"`。
5. `pulse_ir.sweep` 必须存在。
6. 返回重新验证后的 `CompiledBundle`。

注意：当前实现对空 `l0_refs` 不做硬拒绝，L3 MVP 设计建议在 L3 入口进一步要求核心 L0 refs 存在。

示例：

```python
from qxtrl.cpir import compile_to_bundle, verify_compiled_bundle
from qxtrl.el import create_rabi_experiment_spec

bundle = compile_to_bundle(create_rabi_experiment_spec())
verified = verify_compiled_bundle(bundle)
assert verified.bundle_hash == bundle.bundle_hash
```

hash 被篡改时：

```python
bad = bundle.model_copy(update={"bundle_hash": "deadbeef"})
verify_compiled_bundle(bad)
# raises QXtrlValidationError
```

## 6. 推荐 L2 -> L3 用法

```python
from qxtrl.el import create_rabi_experiment_spec
from qxtrl.cpir import compile_to_bundle, verify_compiled_bundle

spec = create_rabi_experiment_spec()
bundle = compile_to_bundle(spec)

# L3 entry should do this again at boundary.
bundle = verify_compiled_bundle(bundle)
```

L3 不应接受：

1. raw `ExperimentSpec`。
2. raw `PulseIR`。
3. 未校验 hash 的 `CompiledBundle`。

## 7. 常见错误示例

### 7.1 非 Rabi Atom 被拒绝

```python
bad = spec.model_copy(update={"atom": spec.atom.model_copy(update={"atom_kind": "not.rabi"})})
compile_to_bundle(bad)
# raises ValueError
```

### 7.2 多 scan axis 被拒绝

```python
# Rabi MVP 只允许 exactly one plan.scan axis。
```

### 7.3 缺失 frame 被拒绝

```python
from qxtrl.cpir import PulseMoment

PulseMoment(
    moment_id="bad",
    kind="drive",
    line_id="line.xy.q000",
    t0_ns=0,
    duration_ns=40,
)
# raises ValidationError: coherent moment must have frame_id
```

### 7.4 waveform 被拒绝

```python
from qxtrl.cpir import PulseMoment

PulseMoment(
    moment_id="bad",
    kind="drive",
    line_id="line.xy.q000",
    t0_ns=0,
    duration_ns=40,
    frame_id="frame.drive.q000",
    parameters={"waveform": [0.0, 1.0]},
)
# raises ValidationError
```

## 8. 测试与验收

推荐命令：

```bash
PYTHONPATH=. python3 -m pytest qxtrl/cpir/tests/ -q
PYTHONPATH=. python3 -m pytest qxtrl -q
python3 -m ruff check qxtrl/cpir
```

当前 L2 测试覆盖重点：

1. Rabi spec 编译为结构化 `PulseIR`。
2. `CompiledBundle` 生成和 hash。
3. frame consistency。
4. scan bool/NaN/Inf/empty 拒绝。
5. no-waveform guard。
6. `validated_copy()` 拒绝非法 update。
7. 多 scan axis 拒绝。
8. `verify_compiled_bundle()` 成功和 hash mismatch 拒绝。

## 9. 当前边界和后续增强

当前边界：

1. 只支持 Rabi amplitude Atom。
2. 只支持单 scan axis。
3. `SweepSpec.order="randomized"` 当前拒绝。
4. `FrameEvent` 只是 Rabi MVP 初始 frame 事件，不是完整 frame update log。
5. `l0_refs` 当前为字符串 ref，后续应升级为结构化 `L0SnapshotRef` / hash。
6. 内部 dict 仍需在跨层边界通过 `verify_compiled_bundle()` 防护。

后续建议：

1. 实现完整 `FrameDefinition / FrameUpdate / FrameState`。
2. 新增第二个 Atom 后抽象 atom-specific compiler。
3. 将 metadata 从 contract hash 策略中进一步明确为非契约或纳入受控诊断。
4. 为 L3 / EB 提供稳定 `verify_compiled_bundle()` 使用示例和 contract tests。
