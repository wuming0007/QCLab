# QXtrl L3 Execution Backend API 说明

**版本**: v0.1  
**日期**: 2026-06-22  
**状态**: 当前实现说明，面向 L4 / RS、L5 / DS、L7 / TRH、后续真实后端开发和审查  
**代码范围**: `qxtrl/eb/`  
**Schema 前缀**: `qxtrl.eb.*`  
**关联文档**:
- [QXtrl_L3_EB_ExecutionBackend_设计.md](QXtrl_L3_EB_ExecutionBackend_设计.md)
- [QXtrl_L3实现审查意见-jed.md](QXtrl_L3实现审查意见-jed.md)
- [QXtrl_L3实现审查意见_答复.md](QXtrl_L3实现审查意见_答复.md)
- [QXtrl_L2_API说明.md](QXtrl_L2_API说明.md)
- [QXtrl_L4_RS_RuntimeScheduler_设计.md](QXtrl_L4_RS_RuntimeScheduler_设计.md)
- [QXtrl_MVP最薄垂直切片定义.md](QXtrl_MVP最薄垂直切片定义.md)

## 0. 文档目的与范围

本文档说明 QXtrl L3 / EB Execution Backend 当前 Python API 的用途、字段、方法、校验规则和典型用法。

L3 的职责是把 L2 / CPIR 产生的 `CompiledBundle` 交给统一执行后端，并返回结构化执行结果：

```text
CompiledBundle -> ExecutionBackend -> BackendRunResult
```

当前 MVP 只实现 `VirtualExecutionBackend`，用于 Rabi amplitude virtual run。该后端包装 L7 / TRH 的 `run_rabi_virtual()`，但对上层只暴露 L3 统一契约。

L3 负责：

1. 接收 `BackendSubmitRequest`。
2. 重新验证 L2 `CompiledBundle`，校验 hash 和 diagnostic。
3. 检查后端 identity、mode、capability、result level 和 L0 refs。
4. 调用虚拟后端执行或 dry-run。
5. 将 schema、capability、bundle、运行异常转成结构化 `BackendRunResult`。
6. 提供 `BackendEvent` 和 `BackendDiagnostic` 供 L4 / L5 / L9 消费。

L3 不负责：

1. 生成 `ExperimentSpec`、`PulseIR` 或 `CompiledBundle`。
2. 编排队列、资源锁、取消策略和重试策略。
3. Rabi 拟合、参数候选和参数晋升。
4. 长期数据持久化和 RunManifest 事实源。
5. UI、SDK、Web console。
6. AI 诊断或动作决策。

## 1. 导入方式与公开 API

推荐从 `qxtrl.eb` 统一导入公开 API：

```python
from qxtrl.eb import (
    BackendSubmitRequest,
    BackendCapability,
    BackendDiagnostic,
    BackendEvent,
    BackendRunResult,
    ExecutionBackend,
    VirtualExecutionBackend,
    verify_compiled_bundle,
)
```

当前 `qxtrl.eb.__all__` 导出的对象包括：

| 类别 | 名称 |
| --- | --- |
| 请求 / 结果 | `BackendSubmitRequest`, `BackendRunResult` |
| 能力 / 诊断 / 事件 | `BackendCapability`, `BackendDiagnostic`, `BackendEvent` |
| 后端接口 | `ExecutionBackend`, `VirtualExecutionBackend` |
| L2 验证工具重导出 | `verify_compiled_bundle` |

说明：`verify_compiled_bundle` 的权威实现仍属于 L2 / CPIR。L3 只是为了上层调用便利进行重导出。

## 2. 关键契约规则

### 2.1 schema version

当前 L3 schema：

```text
qxtrl.eb.BackendSubmitRequest/v0.1
qxtrl.eb.BackendCapability/v0.1
qxtrl.eb.BackendDiagnostic/v0.1
qxtrl.eb.BackendEvent/v0.1
qxtrl.eb.BackendRunResult/v0.1
```

这些 schema 目前通过 Pydantic `Literal[...]` 精确约束。

### 2.2 输入信任边界

L3 公共执行入口是 `VirtualExecutionBackend.submit()`，输入必须是：

```python
BackendSubmitRequest | dict[str, object]
```

其中 `bundle` 必须是 L2 `CompiledBundle` 或可验证为 `CompiledBundle` 的 dict。

L3 当前不允许：

1. raw `ExperimentSpec` 直接提交。
2. raw `PulseIR` 直接提交。
3. 跳过 bundle hash 验证。
4. 跳过 L0 refs gate。
5. backend_id 与实际后端不一致。

### 2.3 支持的 mode

`BackendSubmitRequest.mode` 类型层面允许：

```text
dry_run, virtual, replay, hardware
```

但当前 `VirtualExecutionBackend` 只支持：

```text
dry_run, virtual
```

`replay` 和 `hardware` 会返回：

```text
BackendRunResult(final_state="rejected")
diagnostic.code = "EB-UNSUPPORTED-BACKEND"
```

### 2.4 capability gate

`VirtualExecutionBackend.describe_capability()` 声明：

```yaml
backend_id: backend.virtual.rabi_mvp
backend_kind: virtual
supported_bundle_versions:
  - qxtrl.cpir.CompiledBundle/v0.1
supported_result_levels:
  - integrated_iq
supports_cancel: false
supports_fault_injection: true
```

`submit()` 会检查 `CompiledBundle.pulse_ir.acquisition_windows[*].result_level`。若 bundle 要求 `raw_iq` 等不支持 result level，会返回：

```text
final_state = "rejected"
diagnostic.code = "EB-UNSUPPORTED-RESULT-LEVEL"
```

### 2.5 L0 refs gate

当前 L3 MVP 要求 `CompiledBundle.l0_refs` 至少包含 4 个引用，用于 chip / wiring / hardware / safety 谱系。

若 `l0_refs` 缺失或数量不足，会返回：

```text
final_state = "rejected"
diagnostic.code = "EB-BUNDLE-SCHEMA"
```

说明：L2 `verify_compiled_bundle()` 对 `l0_refs` 保持相对宽松，L3 是执行边界，因此在 L3 做严格 gate。

### 2.6 dry-run 语义

`mode="dry_run"` 只做：

1. request validation。
2. bundle verify。
3. backend identity / capability / L0 refs gate。
4. 事件记录。

`dry_run` 不调用 L7 `run_rabi_virtual()`，不生成 IQ 数据。

成功 dry-run 返回：

```text
final_state = "succeeded"
data = {}
metrics = {"dry_run": True}
```

### 2.7 failure-visible

`submit()` 对普通运行错误返回结构化 `BackendRunResult`，而不是把异常直接抛给 L4 / L9。

典型映射：

| 场景 | final_state | diagnostic code |
| --- | --- | --- |
| request / bundle schema 不合法 | `rejected` | `EB-BUNDLE-SCHEMA` |
| bundle hash 或 pulse_ir hash mismatch | `rejected` | `EB-BUNDLE-HASH` |
| backend_id 或 mode 不支持 | `rejected` | `EB-UNSUPPORTED-BACKEND` |
| result level 不支持 | `rejected` | `EB-UNSUPPORTED-RESULT-LEVEL` |
| L7 virtual 执行异常 | `failed` | `EB-VIRTUAL-RUN-FAILED` |

`validate_bundle()` 仍会在验证失败时抛出异常；它是较低层验证工具，不是完整提交入口。

### 2.8 安全演化方式

当前 `BackendSubmitRequest`、`BackendEvent`、`BackendRunResult` 使用 `frozen=True`。关键对象提供 `validated_copy()`：

```python
new_request = request.validated_copy(timeout_s=120.0)
new_result = result.validated_copy(metrics={"points": 5})
```

不推荐跨层使用裸 `model_copy(update=...)` 构造新对象，因为 Pydantic 默认不重新运行全部 validator。

## 3. 核心对象 API

### 3.1 `BackendSubmitRequest`

**目的**: L3 后端提交请求。L4 / RS 后续应构造该对象并提交给 `ExecutionBackend.submit()`。

| 字段 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `schema_version` | `Literal["qxtrl.eb.BackendSubmitRequest/v0.1"]` | 自动 | schema version |
| `request_id` | `str` | 必填 | 上游请求 ID |
| `run_id` | `str` | 必填 | 本次 run ID，通常由 L4 生成 |
| `backend_id` | `str` | 必填 | 目标后端 ID |
| `bundle` | `CompiledBundle` | 必填 | L2 编译包 |
| `mode` | `dry_run | virtual | replay | hardware` | `virtual` | 请求执行模式 |
| `timeout_s` | `float` | `60.0` | 正有限数 |
| `options` | `dict[str, Any]` | `{}` | 后端选项，不允许 callable |

主要 validator：

| validator | 规则 |
| --- | --- |
| `_validate_timeout` | `timeout_s` 必须是 > 0 的有限数 |
| `_validate_options` | `options` 中不得递归包含 callable |

主要方法：

| 方法 | 目的 |
| --- | --- |
| `validated_copy(**updates)` | 生成重新验证的派生 request |

示例：

```python
from qxtrl.eb import BackendSubmitRequest

request = BackendSubmitRequest(
    request_id="req.rabi.q000.001",
    run_id="run.rabi.q000.001",
    backend_id="backend.virtual.rabi_mvp",
    bundle=bundle,
    mode="virtual",
    timeout_s=60.0,
)
```

非法示例：

```python
BackendSubmitRequest(
    request_id="req.bad",
    run_id="run.bad",
    backend_id="backend.virtual.rabi_mvp",
    bundle=bundle,
    timeout_s=-1,
)
```

上述会被拒绝，因为 `timeout_s` 必须为正有限数。

### 3.2 `BackendCapability`

**目的**: 描述一个执行后端的能力，供 L4 / L9 / 测试判断该后端是否能执行某类 bundle。

| 字段 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `schema_version` | `Literal["qxtrl.eb.BackendCapability/v0.1"]` | 自动 | schema version |
| `backend_id` | `str` | 必填 | 后端 ID |
| `backend_kind` | `virtual | real_hardware | replay | hil` | 必填 | 后端类型 |
| `supported_bundle_versions` | `tuple[str, ...]` | 必填 | 支持的 bundle schema |
| `supported_result_levels` | `tuple[str, ...]` | 必填 | 支持的采集结果级别 |
| `max_points` | `int | None` | `None` | 最大扫描点数，`None` 表示 MVP 暂不限制 |
| `supports_cancel` | `bool` | `False` | 是否支持取消 |
| `supports_fault_injection` | `bool` | `False` | 是否支持故障注入 |

示例：

```python
from qxtrl.eb import VirtualExecutionBackend

backend = VirtualExecutionBackend()
cap = backend.describe_capability()

assert cap.backend_id == "backend.virtual.rabi_mvp"
assert "integrated_iq" in cap.supported_result_levels
```

### 3.3 `BackendDiagnostic`

**目的**: 描述后端验证或执行阶段的结构化诊断。

| 字段 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `schema_version` | `Literal["qxtrl.eb.BackendDiagnostic/v0.1"]` | 自动 | schema version |
| `severity` | `info | warning | error` | 必填 | 严重程度 |
| `code` | `str` | 必填 | 机器可读错误码 |
| `message` | `str` | 必填 | 人类可读说明 |
| `stage` | `str | None` | `None` | 阶段，例如 `validating` / `running` |
| `path` | `str | None` | `None` | 可选字段路径 |
| `hint` | `str | None` | `None` | 可选修复建议 |

当前常见 code：

| code | 含义 |
| --- | --- |
| `EB-BUNDLE-SCHEMA` | request 或 bundle schema 不合法 |
| `EB-BUNDLE-HASH` | bundle hash 或 pulse_ir hash 不匹配 |
| `EB-BUNDLE-VERIFY` | bundle 验证失败但未细分 |
| `EB-UNSUPPORTED-BACKEND` | backend_id 或 mode 不支持 |
| `EB-UNSUPPORTED-RESULT-LEVEL` | result level 不被当前后端支持 |
| `EB-VIRTUAL-RUN-FAILED` | L7 virtual runner 执行失败 |
| `CANCELLED` | 当前 `cancel()` stub 使用的取消诊断 |
| `SAFE_STOP` | 当前 `safe_stop()` stub 使用的诊断 |

示例：

```python
from qxtrl.eb import BackendDiagnostic

diag = BackendDiagnostic(
    severity="error",
    code="EB-UNSUPPORTED-BACKEND",
    message="backend_id mismatch",
    stage="validating",
)
```

### 3.4 `BackendEvent`

**目的**: 描述 L3 后端执行生命周期事件。MVP 中事件内联保存在 `BackendRunResult.events`。

| 字段 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `schema_version` | `Literal["qxtrl.eb.BackendEvent/v0.1"]` | 自动 | schema version |
| `event_id` | `str` | 必填 | 事件 ID |
| `run_id` | `str` | 必填 | 所属 run |
| `backend_id` | `str` | 必填 | 后端 ID |
| `stage` | 见下表 | 必填 | 后端阶段 |
| `state` | `started | succeeded | failed | skipped` | 必填 | 阶段状态 |
| `t_rel_ms` | `float` | 必填 | 相对时间，非负有限数 |
| `details` | `dict[str, Any]` | `{}` | 结构化补充信息 |

当前 stage 枚举：

```text
created, validating, preparing, uploading, arming,
running, acquiring, completed, failed, cancelled, cleanup
```

主要 validator：

| validator | 规则 |
| --- | --- |
| `_validate_t_rel` | `t_rel_ms` 必须为非负有限数 |

示例：

```python
from qxtrl.eb import BackendEvent

evt = BackendEvent(
    event_id="evt.run1.validating",
    run_id="run1",
    backend_id="backend.virtual.rabi_mvp",
    stage="validating",
    state="succeeded",
    t_rel_ms=0.0,
)
```

### 3.5 `BackendRunResult`

**目的**: L3 后端提交入口的最终返回结果。L4 / L5 / L6 不应直接消费 L7 dict，而应消费该对象。

| 字段 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `schema_version` | `Literal["qxtrl.eb.BackendRunResult/v0.1"]` | 自动 | schema version |
| `run_id` | `str` | 必填 | run ID |
| `backend_id` | `str` | 必填 | 实际后端 ID |
| `final_state` | `succeeded | failed | cancelled | rejected` | 必填 | 终态 |
| `bundle_id` | `str` | 必填 | L2 bundle ID |
| `bundle_hash` | `str` | 必填 | L2 bundle hash |
| `pulse_ir_hash` | `str` | 必填 | L2 pulse_ir content hash |
| `result_level` | `str` | 必填 | 结果级别，当前为 `integrated_iq` |
| `data` | `dict[str, Any]` | `{}` | MVP 可内联 virtual IQ |
| `data_refs` | `tuple[str, ...]` | `()` | 后续 L5 data refs |
| `events` | `tuple[BackendEvent, ...]` | `()` | 后端事件 |
| `diagnostics` | `tuple[BackendDiagnostic, ...]` | `()` | 后端诊断 |
| `metrics` | `dict[str, float]` | `{}` | 轻量指标，例如点数 |

主要 validator：

| 条件 | 规则 |
| --- | --- |
| `final_state == "succeeded"` | `bundle_hash`、`pulse_ir_hash`、`result_level` 必须非空，且必须包含 `completed/succeeded` event |
| `final_state in ("rejected", "failed")` | 必须至少有一个 `severity="error"` diagnostic |

主要方法：

| 方法 | 目的 |
| --- | --- |
| `validated_copy(**updates)` | 生成重新验证的派生 result |

示例：

```python
result = backend.submit(request)

if result.final_state == "succeeded":
    iq_points = result.data.get("iq", [])
```

### 3.6 `ExecutionBackend`

**目的**: L3 后端协议。未来真实硬件、replay、HIL 后端都应实现相同接口。

当前 Protocol：

```python
class ExecutionBackend(Protocol):
    backend_id: str

    def describe_capability(self) -> BackendCapability:
        ...

    def validate_bundle(self, bundle: CompiledBundle | dict) -> dict[str, Any]:
        ...

    def submit(self, request: BackendSubmitRequest | dict) -> BackendRunResult:
        ...

    def cancel(self, run_id: str, reason: str) -> BackendRunResult:
        ...

    def safe_stop(self, reason: str) -> BackendDiagnostic:
        ...
```

方法说明：

| 方法 | 输入 | 输出 | 当前语义 |
| --- | --- | --- | --- |
| `describe_capability()` | 无 | `BackendCapability` | 返回后端能力 |
| `validate_bundle(bundle)` | `CompiledBundle | dict` | `dict[str, Any]` | 调用 L2 `verify_compiled_bundle()`；失败会抛异常 |
| `submit(request)` | `BackendSubmitRequest | dict` | `BackendRunResult` | 主要提交入口；失败结构化返回 |
| `cancel(run_id, reason)` | `str, str` | `BackendRunResult` | MVP stub，返回 `cancelled` |
| `safe_stop(reason)` | `str` | `BackendDiagnostic` | MVP stub，返回 info diagnostic |

## 4. `VirtualExecutionBackend` API

### 4.1 目的

`VirtualExecutionBackend` 是当前唯一 L3 实现，用于 Rabi MVP 的虚拟执行。

它的职责是：

1. 作为 `ExecutionBackend` 统一边界。
2. 消费 L2 `CompiledBundle`。
3. 执行 L3 gate。
4. 调用 L7 / TRH `run_rabi_virtual()`。
5. 返回 `BackendRunResult`。

当前固定：

```python
backend.backend_id == "backend.virtual.rabi_mvp"
```

### 4.2 `describe_capability()`

**目的**: 返回当前虚拟后端能力。

示例：

```python
from qxtrl.eb import VirtualExecutionBackend

backend = VirtualExecutionBackend()
cap = backend.describe_capability()

print(cap.backend_kind)              # virtual
print(cap.supported_result_levels)   # ("integrated_iq",)
```

### 4.3 `validate_bundle(bundle)`

**目的**: 验证 bundle 并返回最小 report。

输入：

```python
CompiledBundle | dict[str, Any]
```

输出示例：

```python
{
    "valid": True,
    "bundle_id": "...",
    "bundle_hash": "...",
    "pulse_ir_hash": "...",
    "l0_refs_count": 4,
}
```

注意：

1. 该方法失败时会抛异常。
2. 该方法只委托 L2 `verify_compiled_bundle()`。
3. 完整 L3 gate 和结构化失败返回在 `submit()` 中实现。

因此，L4 / L9 的运行入口应优先调用 `submit()`，不要把 `validate_bundle()` 当作完整执行准入。

### 4.4 `submit(request)`

**目的**: L3 主提交入口。

输入：

```python
BackendSubmitRequest | dict[str, Any]
```

执行顺序：

1. 若输入为 dict，先 `BackendSubmitRequest.model_validate()`。
2. 检查 `request.backend_id == self.backend_id`。
3. 检查 mode，只允许 `virtual` / `dry_run`。
4. 调用 L2 `verify_compiled_bundle()`。
5. 检查 result level 是否在 capability 中。
6. 检查 `len(l0_refs) >= 4`。
7. 若 `dry_run`，返回成功但不执行 L7。
8. 若 `virtual`，调用 `run_rabi_virtual(verified.pulse_ir, noise=0.015)`。
9. 返回 `BackendRunResult`。

成功 virtual run 的事件序列当前为：

```text
validating/succeeded
preparing/succeeded
uploading/skipped
arming/skipped
running/started
running/succeeded
acquiring/succeeded
completed/succeeded
```

成功 dry-run 的事件序列当前为：

```text
validating/succeeded
preparing/succeeded
uploading/skipped
arming/skipped
running/skipped
acquiring/skipped
completed/succeeded
```

### 4.5 `cancel(run_id, reason)`

**目的**: 取消接口占位。

当前实现是 MVP stub：

```python
result = backend.cancel("run1", "user request")

assert result.final_state == "cancelled"
```

注意：

1. 当前不追踪真实运行中的任务。
2. 当前不触发异步 cancellation token。
3. `supports_cancel=False`。
4. L4 v0.1 可将其作为占位接口，但不能假定执行中取消已完整实现。

### 4.6 `safe_stop(reason)`

**目的**: safe stop 接口占位。

当前返回：

```python
BackendDiagnostic(
    severity="info",
    code="SAFE_STOP",
    message=reason,
    stage="cleanup",
)
```

真实硬件后端必须重新实现该方法，并把设备恢复到定义安全状态。

## 5. 端到端示例

### 5.1 Rabi virtual run

```python
from qxtrl.cc import minimal_rabi_lab
from qxtrl.el import create_rabi_experiment_spec
from qxtrl.cpir import compile_to_bundle
from qxtrl.eb import BackendSubmitRequest, VirtualExecutionBackend

lab = minimal_rabi_lab()

spec = create_rabi_experiment_spec(
    qubit_id="q000",
    l0_chip_model_ref=lab["chip"],
    l0_wiring_ref=lab["wiring"],
    l0_hw_ref=lab["hardware"],
    l0_safety_ref=lab["safety"],
)

bundle = compile_to_bundle(spec)
backend = VirtualExecutionBackend()

request = BackendSubmitRequest(
    request_id="req.rabi.q000.001",
    run_id="run.rabi.q000.001",
    backend_id=backend.backend_id,
    bundle=bundle,
    mode="virtual",
)

result = backend.submit(request)

assert result.final_state == "succeeded"
assert result.result_level == "integrated_iq"
assert len(result.data["iq"]) == len(bundle.pulse_ir.sweep.axes[0].values)
```

### 5.2 dry-run

```python
request = BackendSubmitRequest(
    request_id="req.rabi.q000.dry",
    run_id="run.rabi.q000.dry",
    backend_id=backend.backend_id,
    bundle=bundle,
    mode="dry_run",
)

result = backend.submit(request)

assert result.final_state == "succeeded"
assert result.data == {}
assert result.metrics["dry_run"] is True
```

### 5.3 dict 输入

`submit()` 可接受 dict，并转为 `BackendSubmitRequest`。

```python
result = backend.submit({
    "schema_version": "qxtrl.eb.BackendSubmitRequest/v0.1",
    "request_id": "req.rabi.q000.dict",
    "run_id": "run.rabi.q000.dict",
    "backend_id": backend.backend_id,
    "bundle": bundle.model_dump(mode="python"),
    "mode": "virtual",
})
```

若 dict 中 `bundle` 是 raw `PulseIR` 而不是 `CompiledBundle`，当前会结构化拒绝：

```text
final_state = "rejected"
diagnostic.code = "EB-BUNDLE-SCHEMA"
```

## 6. 常见错误示例

### 6.1 backend_id 不匹配

```python
bad_request = request.validated_copy(backend_id="backend.wrong")
result = backend.submit(bad_request)

assert result.final_state == "rejected"
assert result.diagnostics[0].code == "EB-UNSUPPORTED-BACKEND"
```

### 6.2 unsupported mode

```python
bad_request = request.validated_copy(mode="hardware")
result = backend.submit(bad_request)

assert result.final_state == "rejected"
assert result.diagnostics[0].code == "EB-UNSUPPORTED-BACKEND"
```

说明：`hardware` 在 `BackendSubmitRequest` 类型中是合法枚举，但当前 `VirtualExecutionBackend` 不支持。

### 6.3 bundle hash mismatch

```python
bad_bundle = bundle.model_copy(update={"bundle_hash": "bad"})
bad_request = request.validated_copy(bundle=bad_bundle)
result = backend.submit(bad_request)

assert result.final_state == "rejected"
assert result.diagnostics[0].code == "EB-BUNDLE-HASH"
```

### 6.4 L0 refs 缺失

若 bundle 的 `l0_refs` 数量少于 4，即使 hash 被重新计算为合法，也会被 L3 拒绝：

```text
final_state = "rejected"
diagnostic.code = "EB-BUNDLE-SCHEMA"
```

### 6.5 unsupported result level

若 `pulse_ir.acquisition_windows[*].result_level == "raw_iq"`，当前 virtual backend 会拒绝：

```text
final_state = "rejected"
diagnostic.code = "EB-UNSUPPORTED-RESULT-LEVEL"
```

### 6.6 L7 runtime failure

若 L7 virtual runner 抛异常：

```text
final_state = "failed"
diagnostic.code = "EB-VIRTUAL-RUN-FAILED"
```

## 7. 与 L4 / L5 / L6 / L7 的推荐用法

### 7.1 L4 / RS

L4 应构造 `BackendSubmitRequest` 并调用 `submit()`：

```python
backend_result = backend.submit(BackendSubmitRequest(
    request_id=run_request.request_id,
    run_id=run_id,
    backend_id=run_request.backend_id,
    bundle=bundle,
    mode=run_request.mode,
    timeout_s=remaining_timeout_s,
))
```

L4 不应：

1. 直接调用 `run_rabi_virtual()`。
2. 直接消费 `PulseIR` 绕过 `CompiledBundle`。
3. 把 `validate_bundle()` 当作完整执行入口。

### 7.2 L5 / DS

L5 应记录 `BackendRunResult` 中的：

1. `run_id`
2. `backend_id`
3. `final_state`
4. `bundle_id`
5. `bundle_hash`
6. `pulse_ir_hash`
7. `events`
8. `diagnostics`
9. `data_refs` 或 MVP `data`

MVP 可内联 `data["iq"]`；正式 ResultStore 应迁移到 `data_refs`。

### 7.3 L6 / CO

L6 analyzer 应消费 L3 标准输出，而不是 L7 私有返回：

```python
iq_points = backend_result.data.get("iq", [])
```

L6 不应根据 backend 私有字段决定参数晋升。

### 7.4 L7 / TRH

L7 提供物理响应模型，例如 `run_rabi_virtual()`。L3 负责把 L7 的 dict 输出转换成 `BackendRunResult`。

后续 Twin / Replay / HIL 应尽量复用 L3 后端接口，而不是让上层直接调用 L7 内部函数。

## 8. 测试与验收

当前测试入口：

```bash
PYTHONPATH=. python3 -m pytest qxtrl/eb/tests -q
PYTHONPATH=. python3 -m pytest qxtrl -q
python3 -m ruff check qxtrl
PYTHONPATH=. python3 qxtrl/demo_rabi_l1.py
```

当前 L3 contract tests 覆盖：

| 测试 | 目的 |
| --- | --- |
| `test_virtual_backend_accepts_valid_rabi_bundle` | 合法 Rabi bundle 成功执行 |
| `test_backend_rejects_wrong_backend_id` | backend_id mismatch 被拒绝 |
| `test_backend_rejects_missing_l0_refs` | hash 合法但缺失 L0 refs 被拒绝 |
| `test_backend_rejects_unsupported_result_level` | hash 合法但 result level 不支持被拒绝 |
| `test_backend_rejects_raw_pulseir_input_as_result_not_exception` | raw PulseIR 请求被结构化拒绝 |
| `test_backend_runtime_failure_returns_failed_result` | L7 runtime failure 转为 failed result |
| `test_dry_run_does_not_execute_l7` | dry-run 不执行 L7、不生成 IQ |

建议后续补充：

1. `BackendSubmitRequest.options` 嵌套 callable 拒绝测试。
2. `BackendEvent.t_rel_ms` NaN / Inf / 负值拒绝测试。
3. `BackendRunResult` 成功/失败一致性 validator 测试。
4. `cancel()` 和 `safe_stop()` stub 行为测试。
5. `validate_bundle()` 抛错路径测试。

## 9. 当前边界和后续增强

当前边界：

1. 只实现 `VirtualExecutionBackend`。
2. 只支持 Rabi MVP 的 virtual / dry-run。
3. `cancel()` 和 `safe_stop()` 是占位实现。
4. `validate_bundle()` 返回 dict report，不是独立 Pydantic report model。
5. `data` 仍可内联 IQ 点，未切到 L5 `data_refs`。
6. 事件是内联 tuple，尚未接 L4 event stream。
7. `BackendCapability` / `BackendDiagnostic` 尚未全部 frozen，也未提供 `validated_copy()`。

后续增强：

1. L4 接入后，将 L3 events 映射为 L4 `RunEvent`。
2. L5 ResultStore 接入后，将 `data["iq"]` 迁移为 `data_refs`。
3. 真实硬件后端必须实现完整 `cancel()` / `safe_stop()`。
4. Replay / HIL 后端应复用 `ExecutionBackend` Protocol。
5. 引入更细的 diagnostic code，例如 `EB-L0-REFS-MISSING`。
6. 将 `validate_bundle()` 的返回值升级为结构化 `BackendValidationReport`。

