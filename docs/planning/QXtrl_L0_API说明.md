# QXtrl L0 Core Contracts API 说明

**版本**: v0.2  
**日期**: 2026-06-22  
**状态**: 当前实现说明，面向 L1+ 开发和后续审查  
**代码范围**: `qxtrl/cc/`  
**关联文档**:
- [QXtrl_L0_Core_Contracts_设计.md](QXtrl_L0_Core_Contracts_设计.md)
- [QXtrl_L0契约层命名与编码规则.md](QXtrl_L0契约层命名与编码规则.md)
- [QXtrl_L0数据与信息存放规则.md](QXtrl_L0数据与信息存放规则.md)
- [QXtrl_MVP最薄垂直切片定义.md](QXtrl_MVP最薄垂直切片定义.md)

## 0. 文档目的与范围

本文档说明 QXtrl L0 Core Contracts 当前 Python API 的用途、字段、方法、校验规则和典型用法。

L0 的职责是提供跨层共享的“契约纪律”：

1. 稳定 ID、命名规则和 schema version。
2. 物理量单位、未知值和基础数值合法性。
3. 芯片、连线、硬件、安全策略等核心对象的结构化模型。
4. `usable_for_control`、审批、撤销、missing => deny 等治理规则。
5. 上层可捕获、可机器解析的错误模型。

L0 不负责：

1. 实验语义编排。
2. Pulse 编译、波形生成、调度执行。
3. 真实设备 I/O。
4. 参数拟合、校准决策和 AI 决策。
5. 配置写回和结果存储。

## 1. 导入方式与公开 API

推荐从 `qxtrl.cc` 统一导入公开 API：

```python
from qxtrl.cc import (
    Quantity,
    DataQuality,
    Identity,
    ChipModel,
    QubitElement,
    WiringEdge,
    WiringGraph,
    HardwareInventory,
    SafetyPolicy,
    QXtrlValidationError,
    minimal_rabi_lab,
)
```

当前 `qxtrl.cc.__all__` 导出的对象包括：

| 类别 | 名称 |
| --- | --- |
| 错误类型 | `QXtrlError`, `QXtrlValidationError`, `SafetyViolation`, `SchemaVersionError` |
| 物理量 | `Quantity`, `QuantityField` |
| 验证器 | `validate_element_id`, `validate_identity_id`, `validate_line_id`, `validate_device_id`, `validate_channel_id`, `validate_resource_group_id`, `validate_schema_version`, `KNOWN_UNITS` |
| 治理与基础模型 | `L0Base`, `Identity`, `SourceRef`, `DataQuality` |
| 芯片模型 | `ChipModel`, `QubitElement`, `ResonatorElement`, `CouplerElement` |
| 连线模型 | `WiringGraph`, `WiringEdge`, `HardwareChannels`, `WiringEndpoint` |
| 硬件模型 | `HardwareInventory`, `Device`, `Channel`, `ChannelCapability` |
| 安全与快照 | `SafetyPolicy`, `L0SnapshotRef` |
| 示例工厂 | `minimal_rabi_lab`, `public_willow_chip_example` |

## 2. 关键治理规则

### 2.1 可控状态判断

L0 中“可以进入真实控制链路”的唯一语义是：

```text
usable_for_control == True
status == "approved"
approved_by 非空
approved_at 非空
未撤销: revoked_by / revoked_at 均为空
```

上层不得只读取 `.usable_for_control`。应使用：

1. `DataQuality.is_approved_for_control()`
2. `L0Base.require_usable_for_control()`
3. `validators.is_usable_for_control(...)`

示例：

```python
from qxtrl.cc import DataQuality

dq = DataQuality(
    confidence="measured",
    usable_for_control=True,
    status="approved",
    approved_by="lab-admin",
    approved_at="2026-06-21T00:00:00Z",
)

assert dq.is_approved_for_control()
```

撤销示例：

```python
revoked = dq.revoke(
    by="lab-admin",
    at="2026-06-22T00:00:00Z",
    reason="calibration drift",
)

assert revoked.is_revoked()
assert not revoked.is_approved_for_control()
```

### 2.2 missing => deny

缺失字段默认不允许真实控制。典型体现：

1. `SafetyPolicy.operation_classes` 默认为空，缺项即拒绝。
2. `DataQuality` 未审批时，`require_usable_for_control()` 拒绝。
3. `HardwareInventory.usable_for_control=True` 时，必须声明 `devices` 和 `channels`。
4. `WiringEdge` 根据 role 要求最小硬件通道。

### 2.3 schema version 类型绑定

核心 L0 对象使用精确 schema version，例如：

```python
ChipModel.schema_version == "qxtrl.cc.ChipModel/v0.1"
HardwareInventory.schema_version == "qxtrl.cc.HardwareInventory/v0.1"
```

对象类型与 schema version 名称不匹配时会被拒绝。

## 3. 错误模型

### 3.1 `QXtrlError`

**位置**: `qxtrl/cc/errors.py`  
**用途**: QXtrl L0+ 的基础异常类型。  
**核心字段**:

| 字段 | 说明 |
| --- | --- |
| `code` | 机器可读错误码，默认 `QXTRL_ERROR` |
| `details` | 结构化错误上下文，供日志、UI、诊断使用 |

**主要方法**:

| 方法 | 目的 |
| --- | --- |
| `__init__(message, code="QXTRL_ERROR", details=None)` | 创建带错误码和结构化详情的异常 |
| `__str__()` | 输出人可读 message，同时附带 code/details |

示例：

```python
from qxtrl.cc import QXtrlError

err = QXtrlError("something failed", code="DEMO", details={"field": "x"})
print(str(err))
```

### 3.2 `QXtrlValidationError`

**用途**: L0 schema、ID、单位、缺失字段、治理规则失败时使用。  
**继承**: `QXtrlError`。  
**错误码**: `L0_VALIDATION`。

构造参数：

| 参数 | 说明 |
| --- | --- |
| `message` | 人可读错误描述 |
| `field` | 相关字段路径 |
| `rule` | 对应规则编号或内部规则名 |
| `**kwargs` | 额外结构化信息 |

示例：

```python
from qxtrl.cc import Quantity, QXtrlValidationError

try:
    Quantity(value=1.0, unit="bad_unit")
except QXtrlValidationError as exc:
    print(exc.code)
    print(exc.details)
```

### 3.3 `SafetyViolation`

**用途**: 操作或物理值违反安全策略时使用。当前 L0 仅定义错误类型，实际触发通常由上层 Runtime / Backend / Safety gate 完成。  
**错误码**: `L0_SAFETY_VIOLATION`。

参数：

| 参数 | 说明 |
| --- | --- |
| `message` | 错误描述 |
| `policy_id` | 触发的安全策略 ID |
| `limit_kind` | 限制类型，例如 channel limit / global rule |

### 3.4 `SchemaVersionError`

**用途**: schema version 不兼容或未知时使用。当前大部分格式错误由 `QXtrlValidationError` 抛出，`SchemaVersionError` 保留给后续迁移/兼容层。  
**错误码**: `L0_SCHEMA_VERSION`。

## 4. 物理量 API

### 4.1 `Quantity`

**位置**: `qxtrl/cc/quantity.py`  
**目的**: 表达带单位的物理量，避免在 ID 或散乱 dict 中隐式编码物理值。  
**典型用途**:

1. qubit 频率、T1/T2、采样率、时序分辨率。
2. 安全阈值和硬件能力声明。
3. `unknown` 占位，表示该值缺失但显式知道缺失。

字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `value` | `float | "unknown"` | 数值或显式未知 |
| `unit` | `str` | 单位，必须属于 `KNOWN_UNITS` |
| `uncertainty` | `float | "unknown" | None` | 同单位不确定度 |
| `source` | `str | None` | 数据来源标签 |

校验规则：

1. `unit` 必须在 `KNOWN_UNITS` 中。
2. `value` / `uncertainty` 接受有限实数或 `"unknown"`。
3. 拒绝 `bool`，避免 `True -> 1.0`。
4. 拒绝 `NaN` 和 `Inf`。
5. 禁止额外字段，开启 assignment validation。

方法：

| 方法 | 目的 |
| --- | --- |
| `is_unknown()` | 判断 `value == "unknown"` |
| `__repr__()` | 给调试输出提供简洁物理量表示 |

示例：

```python
from qxtrl.cc import Quantity

freq = Quantity(value=5.0e9, unit="Hz", uncertainty=5e6, source="demo")
assert not freq.is_unknown()

unknown_amp = Quantity(value="unknown", unit="V")
assert unknown_amp.is_unknown()
```

非法示例：

```python
from qxtrl.cc import Quantity

Quantity(value=True, unit="V")        # 拒绝
Quantity(value=float("nan"), unit="V")  # 拒绝
Quantity(value=1.0, unit="bad_unit")  # 拒绝
```

## 5. 治理与基础模型

### 5.1 `SourceRef`

**目的**: 记录对象来源，支持审计和 IP 边界管理。  
**字段**:

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `label` | `str` | 来源名称 |
| `url` | `str | None` | 公开 URL 或来源链接 |
| `retrieved_date` | `str | None` | 获取日期，建议 `YYYY-MM-DD` |

示例：

```python
from qxtrl.cc import SourceRef

ref = SourceRef(
    label="public announcement",
    url="https://example.com/public-source",
    retrieved_date="2026-06-21",
)
```

### 5.2 `Identity`

**目的**: 给所有 L0 顶层对象提供稳定身份和来源说明。  
**字段**:

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `str` | 稳定 ID，必须符合 `validate_identity_id` |
| `display_name` | `str` | 人可读名称 |
| `vendor` | `str | None` | 厂商或来源方 |
| `source_kind` | `SourceKind` | 来源类别 |
| `source_refs` | `list[SourceRef]` | 来源引用列表 |

`SourceKind` 可选值：

```text
public_example, vendor_snapshot, lab_calibrated, simulated, draft, imported
```

校验：

1. `id` 长度至少 3。
2. 只允许 `a-z0-9_.`。
3. 禁止空格、大写、中文和其他非规范字符。

示例：

```python
from qxtrl.cc import Identity

identity = Identity(
    id="chip.demo_rabi_001",
    display_name="Demo single-qubit chip",
    source_kind="simulated",
)
```

### 5.3 `DataQuality`

**目的**: 统一描述 L0 对象是否可用于真实控制，以及该判断的审批和撤销状态。  
**核心原则**: `usable_for_control` 不是单独 gate，必须和审批字段一起判断。

字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `confidence` | `str` | 数据可信度标签，默认 `unknown` |
| `usable_for_control` | `bool` | 是否意图允许进入控制链路 |
| `missing_fields_policy` | `Literal` | 缺失字段策略，默认 `deny_physical_execution` |
| `status` | `Status` | `draft`, `approved`, `disabled`, `retired`, `unknown` |
| `approved_by` | `str | None` | 审批人或角色 |
| `approved_at` | `str | None` | 审批时间，建议 ISO8601 UTC |
| `revoked_by` | `str | None` | 撤销人或角色 |
| `revoked_at` | `str | None` | 撤销时间 |
| `revocation_reason` | `str | None` | 撤销原因 |

方法：

| 方法 | 目的 |
| --- | --- |
| `is_approved_for_control()` | 唯一权威 control gate，必须同时满足 `usable_for_control/status/approved_by/approved_at/未撤销` |
| `is_revoked()` | 判断是否存在撤销字段 |
| `revoke(by, at, reason=None)` | 返回一个撤销后的副本，不修改原对象 |

校验规则：

1. `usable_for_control=True` 要求 `status="approved"`、`approved_by`、`approved_at`。
2. `status="approved"` 要求 `approved_by`、`approved_at`。
3. 出现 `revoked_by` 或 `revoked_at` 时，`usable_for_control` 必须为 `False`。
4. 出现撤销字段时，`status` 应为 `disabled`、`retired` 或 `unknown`。
5. assignment validation 开启，但上层仍应使用 `is_approved_for_control()` 做最终 gate。

正常审批示例：

```python
from qxtrl.cc import DataQuality

dq = DataQuality(
    confidence="measured",
    usable_for_control=True,
    status="approved",
    approved_by="calibration-owner",
    approved_at="2026-06-21T00:00:00Z",
)

assert dq.is_approved_for_control()
```

撤销示例：

```python
revoked = dq.revoke(
    by="calibration-owner",
    at="2026-06-22T00:00:00Z",
    reason="drift detected",
)

assert revoked.is_revoked()
assert not revoked.is_approved_for_control()
```

非法示例：

```python
DataQuality(usable_for_control=True, status="draft")  # 拒绝
DataQuality(status="approved", approved_by="a")       # 缺 approved_at，拒绝
DataQuality(
    usable_for_control=True,
    status="approved",
    approved_by="a",
    approved_at="t",
    revoked_by="admin",
)  # 已撤销却可控，拒绝
```

### 5.4 `L0Base`

**目的**: 所有顶层 L0 对象的共同基类。统一 schema version、身份、治理状态和创建时间。  
**继承者**: `ChipModel`, `WiringGraph`, `HardwareInventory`, `SafetyPolicy`。

字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `schema_version` | `str` | `qxtrl.cc.<Name>/v<major>.<minor>` |
| `identity` | `Identity` | 稳定身份 |
| `data_quality` | `DataQuality` | 治理状态 |
| `created_at` | `str` | UTC ISO 时间，默认当前时间 |
| `updated_at` | `str | None` | 更新时间 |

重要方法：

| 方法 | 目的 |
| --- | --- |
| `require_usable_for_control(context="run")` | 若对象未通过 `data_quality.is_approved_for_control()`，抛出 `QXtrlValidationError` |

内置校验：

1. `schema_version` 格式合法。
2. `schema_version` 中的 `<Name>` 必须等于具体类名。
3. 直接替换 `data_quality` 时重新执行控制 gate 基本规则。
4. 禁止额外字段，开启 assignment validation。

示例：

```python
from qxtrl.cc import ChipModel, DataQuality, Identity

chip = ChipModel(
    identity=Identity(id="chip.demo01", display_name="demo"),
    data_quality=DataQuality(usable_for_control=False),
)

chip.require_usable_for_control()  # 抛出 QXtrlValidationError
```

## 6. 芯片模型 API

### 6.1 `QubitElement`

**目的**: 表达一个物理或逻辑 qubit 的静态属性。  
**字段**:

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `element_id` | `str` | qubit ID，例如 `q000` |
| `display_name` | `str | None` | 人可读名称 |
| `role` | `physical_qubit | logical` | qubit 角色 |
| `frequency` | `Quantity | None` | 频率 |
| `anharmonicity` | `Quantity | None` | 非谐性 |
| `t1` | `Quantity | None` | T1 |
| `t2` | `Quantity | None` | T2 |

校验：

1. `element_id` 必须通过 `validate_element_id`。
2. qubit ID 当前格式为 `qNNN`。

示例：

```python
from qxtrl.cc import QubitElement, Quantity

q0 = QubitElement(
    element_id="q000",
    frequency=Quantity(value=5.0e9, unit="Hz"),
)
```

### 6.2 `ResonatorElement`

**目的**: 表达读出谐振腔等芯片元素。  
**字段**:

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `element_id` | `str` | resonator ID，例如 `rr_q000` |
| `attached_to` | `str` | 关联 qubit ID |
| `frequency` | `Quantity | None` | 谐振腔频率 |

校验：

1. `element_id` 通过 `validate_element_id`。
2. 在 `ChipModel` 中，`attached_to` 必须存在于 `qubits`。

示例：

```python
from qxtrl.cc import ResonatorElement

rr0 = ResonatorElement(element_id="rr_q000", attached_to="q000")
```

### 6.3 `CouplerElement`

**目的**: 表达 tunable coupler / fixed coupler。  
**字段**:

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `element_id` | `str` | coupler ID，例如 `tc_q000_q001` |
| `endpoints` | `list[str]` | 两个 endpoint qubit |

校验：

1. `element_id` 通过 `validate_element_id`。
2. `endpoints` 必须恰好两个。
3. `endpoints` 必须按字典序排序。
4. 在 `ChipModel` 中，所有 endpoints 必须存在于 `qubits`。

当前边界：

1. 当前实现尚未强制 `element_id` 与 `endpoints` 完全一致，例如 `tc_q000_q001` 与 `["q002", "q003"]` 的一致性可后续增强。
2. resonator/coupler 的全局重复 ID 检查可后续增强。

示例：

```python
from qxtrl.cc import CouplerElement

tc01 = CouplerElement(element_id="tc_q000_q001", endpoints=["q000", "q001"])
```

### 6.4 `ChipModel`

**继承**: `L0Base`  
**目的**: 表达芯片静态拓扑和基础物理属性。  
**schema**: `qxtrl.cc.ChipModel/v0.1`

字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `qubits` | `list[QubitElement]` | qubit 列表 |
| `resonators` | `list[ResonatorElement]` | resonator 列表 |
| `couplers` | `list[CouplerElement]` | coupler 列表 |
| `modality` | `superconducting | other` | 芯片技术路线 |
| `physical_qubit_count` | `int` | 自动同步为 `len(qubits)` |

方法：

| 方法 | 目的 |
| --- | --- |
| `get_qubit(qid)` | 按 ID 获取 qubit，找不到时抛出 `KeyError` |

内置校验：

1. schema version 必须匹配 `ChipModel`。
2. qubit element ID 不可重复。
3. `physical_qubit_count` 自动设为 qubit 数量。
4. resonator `attached_to` 必须引用已知 qubit。
5. coupler endpoints 必须引用已知 qubit。

示例：

```python
from qxtrl.cc import ChipModel, DataQuality, Identity, QubitElement, ResonatorElement

chip = ChipModel(
    identity=Identity(id="chip.demo01", display_name="demo chip"),
    data_quality=DataQuality(usable_for_control=False),
    qubits=[QubitElement(element_id="q000")],
    resonators=[ResonatorElement(element_id="rr_q000", attached_to="q000")],
)

assert chip.physical_qubit_count == 1
assert chip.get_qubit("q000").element_id == "q000"
```

## 7. 连线模型 API

### 7.1 `HardwareChannels`

**目的**: 结构化描述一条 logical line 绑定的硬件通道。  
**字段**:

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `i` | `str | None` | IQ 驱动 I 分量通道 |
| `q` | `str | None` | IQ 驱动 Q 分量通道 |
| `adc` | `str | None` | 读出 ADC 通道 |
| `marker` | `str | None` | marker 通道 |
| `lo` | `str | None` | LO 通道 |
| `other` | `dict[str, str]` | 扩展通道 |

校验：

1. 所有非空 channel id 必须通过 `validate_channel_id`。
2. `other` 的值也会按 channel id 校验。

示例：

```python
from qxtrl.cc import HardwareChannels

channels = HardwareChannels(
    i="chan.awg.demo.out01",
    q="chan.awg.demo.out02",
)
```

### 7.2 `WiringEndpoint`

**目的**: 描述 logical line 的芯片端和硬件通道端。  
**字段**:

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `chip_element` | `str` | 芯片元素 ID，例如 `q000` 或 `rr_q000` |
| `hardware_channels` | `HardwareChannels` | 绑定的硬件通道 |

校验：

1. `chip_element` 必须通过 `validate_element_id`。
2. `hardware_channels` 内的 channel id 必须合法。

示例：

```python
from qxtrl.cc import WiringEndpoint, HardwareChannels

endpoint = WiringEndpoint(
    chip_element="q000",
    hardware_channels=HardwareChannels(
        i="chan.awg.demo.out01",
        q="chan.awg.demo.out02",
    ),
)
```

### 7.3 `WiringEdge`

**目的**: 将一条 logical line 映射到芯片元素和硬件通道。  
**字段**:

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `line_id` | `str` | logical line ID，例如 `line.xy.q000` |
| `role` | `str` | line 角色，例如 `drive_iq`, `readout`, `flux` |
| `endpoints` | `WiringEndpoint | dict` | endpoint，可传 dict，会自动转换 |
| `signal_chain` | `list[str]` | 设备链路顺序 |
| `status` | `Status` | 线路状态 |
| `usable_for_control` | `bool` | 线路是否可控 |

校验：

1. `line_id` 必须通过 `validate_line_id`。
2. dict 格式 `endpoints` 会自动转换为 `WiringEndpoint`。
3. `role="drive_iq"` 要求同时有 `i` 和 `q`。
4. `role="readout"` 要求有 `adc`。
5. `role in ("flux", "z", "marker", "lo", "pump", "trig")` 要求至少一个 channel。
6. 未知 role 暂允许，用于扩展，但无额外语义校验。

示例：

```python
from qxtrl.cc import WiringEdge

edge_xy = WiringEdge(
    line_id="line.xy.q000",
    role="drive_iq",
    endpoints={
        "chip_element": "q000",
        "hardware_channels": {
            "i": "chan.awg.demo.out01",
            "q": "chan.awg.demo.out02",
        },
    },
    status="approved",
    usable_for_control=True,
)
```

非法示例：

```python
WiringEdge(
    line_id="line.xy.q000",
    role="drive_iq",
    endpoints={
        "chip_element": "q000",
        "hardware_channels": {"i": "chan.awg.demo.out01"},
    },
)  # 缺 q，拒绝
```

### 7.4 `WiringGraph`

**继承**: `L0Base`  
**目的**: 管理 logical line 到硬件资源的映射集合。  
**schema**: `qxtrl.cc.WiringGraph/v0.1`

字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `edges` | `list[WiringEdge]` | 连线边列表 |
| `resource_groups` | `dict[str, Any]` | 资源组占位，用于后续调度冲突建模 |

方法：

| 方法 | 目的 |
| --- | --- |
| `get_edge(line_id)` | 按 line id 获取 edge，找不到时抛出 `KeyError` |

校验：

1. schema version 必须匹配 `WiringGraph`。
2. 若 edge `usable_for_control=True`，则 edge `status` 必须为 `approved`。

当前边界：

1. `chip_element` 是否存在于 `ChipModel` 的跨对象校验后续由 `L0Bundle` / snapshot validator 或上层资源绑定完成。
2. `hardware_channels` 是否存在于 `HardwareInventory.channels` 当前尚未在 `WiringGraph` 内做跨对象校验。

示例：

```python
from qxtrl.cc import DataQuality, Identity, WiringGraph

wiring = WiringGraph(
    identity=Identity(id="wiring.chip_demo01", display_name="demo wiring"),
    data_quality=DataQuality(usable_for_control=False),
    edges=[edge_xy],
)

edge = wiring.get_edge("line.xy.q000")
```

## 8. 硬件资产 API

### 8.1 `ChannelCapability`

**目的**: 描述硬件通道能力，不代表实时状态。  
**字段**:

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `signal_kind` | `Literal` | `analog_iq`, `analog_real`, `marker`, `trigger`, `dc`, `adc_input`, `unknown` |
| `sample_rate` | `Quantity | None` | 采样率 |
| `amplitude_range` | `dict[str, Any] | None` | 幅度范围，例如 `{min, max, unit}` |
| `timing_resolution` | `Quantity | None` | 时序分辨率 |
| `supports_waveform_upload` | `bool` | 是否支持波形上传 |

示例：

```python
from qxtrl.cc import ChannelCapability, Quantity

cap = ChannelCapability(
    signal_kind="analog_iq",
    sample_rate=Quantity(value=2.0e9, unit="Sa/s"),
    supports_waveform_upload=True,
)
```

### 8.2 `Channel`

**目的**: 声明硬件通道 ID 和能力。  
**字段**:

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `channel_id` | `str` | channel ID，例如 `chan.awg.demo.out01` |
| `capabilities` | `ChannelCapability` | 通道能力 |
| `safety_limits_ref` | `str | None` | 安全限制引用 |

校验：

1. `channel_id` 必须通过 `validate_channel_id`。

### 8.3 `Device`

**目的**: 声明安装位上的设备，不直接表达实时连接状态。  
**字段**:

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `device_id` | `str` | 设备安装位 ID，例如 `dev.awg.demo` |
| `device_type` | `str` | 设备类型 |
| `asset_id` | `str | None` | 资产/序列号引用 |
| `vendor` | `str | None` | 厂商 |
| `model` | `str | None` | 型号 |
| `firmware_version` | `str | None` | 固件版本 |
| `connection` | `dict[str, Any]` | 连接信息，不应包含凭据 |
| `status` | `Status` | 设备状态 |

校验：

1. `device_id` 必须通过 `validate_device_id`。

### 8.4 `HardwareInventory`

**继承**: `L0Base`  
**目的**: 声明设备、通道和能力。  
**schema**: `qxtrl.cc.HardwareInventory/v0.1`

字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `devices` | `list[Device]` | 设备声明 |
| `channels` | `list[Channel]` | 通道声明 |

校验：

1. schema version 必须匹配 `HardwareInventory`。
2. 当 `data_quality.usable_for_control=True` 时，必须至少有一个 `Device`。
3. 当 `data_quality.usable_for_control=True` 时，必须至少有一个 `Channel`。
4. virtual/demo 场景也应声明代表性 channel，便于 L2/L3 资源绑定。

示例：

```python
from qxtrl.cc import (
    Channel,
    ChannelCapability,
    DataQuality,
    Device,
    HardwareInventory,
    Identity,
)

hw = HardwareInventory(
    identity=Identity(id="hw.station_demo01", display_name="demo hw"),
    data_quality=DataQuality(
        usable_for_control=True,
        status="approved",
        approved_by="lab-admin",
        approved_at="2026-06-21T00:00:00Z",
    ),
    devices=[Device(device_id="dev.awg.demo", device_type="awg")],
    channels=[
        Channel(
            channel_id="chan.awg.demo.out01",
            capabilities=ChannelCapability(signal_kind="analog_iq"),
        )
    ],
)
```

## 9. 安全策略 API

### 9.1 `SafetyPolicy`

**继承**: `L0Base`  
**目的**: 描述站点/芯片/资源的安全边界和操作类别白名单。  
**schema**: `qxtrl.cc.SafetyPolicy/v0.1`

字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `policy_mode` | `deny_by_default | allow_list` | 策略模式，默认 `deny_by_default` |
| `applies_to` | `dict[str, str]` | 策略适用对象，如 station/chip |
| `global_rules` | `dict[str, Any]` | 全局安全规则 |
| `channel_limits` | `dict[str, Any]` | 通道限制 |
| `operation_classes` | `dict[str, Any]` | 操作类别授权 |

默认 `global_rules`：

```python
{
    "require_authenticated_operator": True,
    "require_approved_hardware_inventory": True,
    "require_approved_wiring_graph": True,
    "require_active_calibration_snapshot": True,
    "deny_when_any_required_limit_unknown": True,
    "allow_ai_to_execute_physical_actions": False,
}
```

方法：

| 方法 | 目的 |
| --- | --- |
| `is_operation_allowed(op_class)` | 判断操作类别是否显式允许，缺项返回 `False` |
| `allows_simulation()` | `is_operation_allowed("simulation")` |
| `allows_replay()` | `is_operation_allowed("replay")` |

示例：

```python
from qxtrl.cc import DataQuality, Identity, SafetyPolicy

policy = SafetyPolicy(
    identity=Identity(id="safety.station_demo01", display_name="demo safety"),
    data_quality=DataQuality(
        usable_for_control=True,
        status="approved",
        approved_by="lab-admin",
        approved_at="2026-06-21T00:00:00Z",
    ),
    operation_classes={
        "simulation": {"allowed": True, "requires_approval": False},
        "replay": {"allowed": True, "requires_approval": False},
        "physical_low_risk_calibration": {"allowed": False},
    },
)

assert policy.allows_simulation()
assert not policy.is_operation_allowed("physical_low_risk_calibration")
assert not policy.is_operation_allowed("missing_operation")
```

## 10. 快照引用 API

### 10.1 `L0SnapshotRef`

**目的**: 给 `RunManifest`、校准记录或上层任务引用已发布的 L0 快照。  
**当前实现**: 仅引用对象，不负责生成 hash 或发布快照。  
**字段**:

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `snapshot_id` | `str` | 快照 ID |
| `schema_version` | `str` | 被引用对象 schema version |
| `content_hash` | `str` | 内容 hash，建议 `sha256:...` |
| `generated_at` | `str` | 生成时间 |
| `kind` | `Literal` | `hardware_inventory`, `wiring_graph`, `chip_model`, `safety_policy`, `calibration`, `cc_bundle` |

校验：

1. `schema_version` 必须通过 `validate_schema_version`。

示例：

```python
from qxtrl.cc import L0SnapshotRef

ref = L0SnapshotRef(
    snapshot_id="hw_inv_demo_001",
    schema_version="qxtrl.cc.HardwareInventory/v0.1",
    content_hash="sha256:deadbeef",
    generated_at="2026-06-21T12:00:00Z",
    kind="hardware_inventory",
)
```

## 11. 验证器 API

### 11.1 `KNOWN_UNITS`

**目的**: MVP 阶段允许的单位集合。  
当前包含：

```text
Hz, kHz, MHz, GHz
s, ms, us, ns, ps
V, mV, uV
A, mA, uA
W, mW, dBm
Sa/s, GSa/s, MSa/s
a.u., fraction
K, mK
rad, deg
ohm
```

### 11.2 ID 验证器

| 函数 | 目的 | 合法示例 | 非法示例 |
| --- | --- | --- | --- |
| `validate_element_id(element_id)` | 验证芯片元素 ID | `q000`, `rr_q000`, `tc_q000_q001`, `bias_q000` | `Q000`, `tc_q001_q000` |
| `validate_line_id(line_id)` | 验证 logical line ID | `line.xy.q000`, `line.ro.rr_q000` | `chan.awg.demo.out01` |
| `validate_device_id(device_id)` | 验证设备安装位 ID | `dev.awg.demo` | `awg.demo` |
| `validate_channel_id(channel_id)` | 验证硬件通道 ID | `chan.awg.demo.out01` | `not_a_channel` |
| `validate_resource_group_id(rg_id)` | 验证资源组 ID | `rg.awg.demo` | `resource.awg.demo` |
| `validate_identity_id(identity_id)` | 验证顶层对象 identity | `chip.demo01`, `station.demo01` | `Bad ID`, `中文id` |

用法：

```python
from qxtrl.cc import validate_channel_id, QXtrlValidationError

try:
    validate_channel_id("not_a_channel")
except QXtrlValidationError as exc:
    print(exc.details["rule"])
```

### 11.3 `validate_schema_version`

**目的**: 校验 schema version 格式和可选精确匹配。  
格式：

```text
qxtrl.cc.<Name>/v<major>.<minor>
```

示例：

```python
from qxtrl.cc import validate_schema_version

validate_schema_version("qxtrl.cc.ChipModel/v0.1")
validate_schema_version(
    "qxtrl.cc.ChipModel/v0.1",
    expected="qxtrl.cc.ChipModel/v0.1",
)
```

### 11.4 `is_usable_for_control`

**目的**: 对 `DataQuality` 对象、dict 或兼容对象执行统一可控判断。  
判断条件：

1. `usable_for_control=True`
2. `status=="approved"`
3. `approved_by` 非空
4. `approved_at` 非空
5. 未设置 `revoked_by` / `revoked_at`

示例：

```python
from qxtrl.cc.validators import is_usable_for_control

assert not is_usable_for_control({"usable_for_control": True})
assert is_usable_for_control({
    "usable_for_control": True,
    "status": "approved",
    "approved_by": "tester",
    "approved_at": "2026-06-21T00:00:00Z",
})
assert not is_usable_for_control({
    "usable_for_control": True,
    "status": "approved",
    "approved_by": "tester",
    "approved_at": "2026-06-21T00:00:00Z",
    "revoked_by": "admin",
})
```

## 12. 示例工厂 API

### 12.1 `public_willow_chip_example()`

**目的**: 创建公开资料占位示例，用于 schema 展示和测试。  
**返回**: `ChipModel`。  
**关键语义**:

1. `source_kind="public_example"`。
2. `usable_for_control=False`。
3. 仅作为公开占位，不可用于真实控制。

示例：

```python
from qxtrl.cc import public_willow_chip_example

chip = public_willow_chip_example()
assert chip.physical_qubit_count == 105
assert not chip.data_quality.usable_for_control
```

### 12.2 `minimal_rabi_lab()`

**目的**: 创建 MVP Virtual Rabi 所需的最小 L0 对象集合。  
**返回**: `dict[str, object]`，包含：

| key | 对象 |
| --- | --- |
| `chip` | `ChipModel` |
| `wiring` | `WiringGraph` |
| `hardware` | `HardwareInventory` |
| `safety` | `SafetyPolicy` |
| `target_qubit` | `str` |

示例：

```python
from qxtrl.cc import minimal_rabi_lab

objs = minimal_rabi_lab()
chip = objs["chip"]
wiring = objs["wiring"]
hardware = objs["hardware"]
safety = objs["safety"]

chip.require_usable_for_control(context="mvp_demo")
wiring.require_usable_for_control(context="mvp_demo")
hardware.require_usable_for_control(context="mvp_demo")
safety.require_usable_for_control(context="mvp_demo")

assert safety.allows_simulation()
```

## 13. 常见构造模式

### 13.1 构造一个可控单 qubit chip

```python
from qxtrl.cc import ChipModel, DataQuality, Identity, QubitElement, Quantity

chip = ChipModel(
    identity=Identity(id="chip.single_q_demo", display_name="single q demo"),
    data_quality=DataQuality(
        confidence="measured",
        usable_for_control=True,
        status="approved",
        approved_by="calibration-owner",
        approved_at="2026-06-21T00:00:00Z",
    ),
    qubits=[
        QubitElement(
            element_id="q000",
            frequency=Quantity(value=5.0e9, unit="Hz"),
        )
    ],
)

chip.require_usable_for_control(context="physical_compile")
```

### 13.2 构造 drive/readout wiring

```python
from qxtrl.cc import DataQuality, Identity, WiringEdge, WiringGraph

edge_xy = WiringEdge(
    line_id="line.xy.q000",
    role="drive_iq",
    endpoints={
        "chip_element": "q000",
        "hardware_channels": {
            "i": "chan.awg.demo.out01",
            "q": "chan.awg.demo.out02",
        },
    },
    status="approved",
    usable_for_control=True,
)

edge_ro = WiringEdge(
    line_id="line.ro.rr_q000",
    role="readout",
    endpoints={
        "chip_element": "rr_q000",
        "hardware_channels": {"adc": "chan.adc.demo.in01"},
    },
    status="approved",
    usable_for_control=True,
)

wiring = WiringGraph(
    identity=Identity(id="wiring.single_q_demo", display_name="single q wiring"),
    data_quality=DataQuality(
        usable_for_control=True,
        status="approved",
        approved_by="wiring-owner",
        approved_at="2026-06-21T00:00:00Z",
    ),
    edges=[edge_xy, edge_ro],
)
```

### 13.3 拒绝不完整 safety policy

```python
from qxtrl.cc import DataQuality, Identity, SafetyPolicy

policy = SafetyPolicy(
    identity=Identity(id="safety.default_deny", display_name="default deny"),
    data_quality=DataQuality(usable_for_control=False),
)

assert not policy.allows_simulation()
assert not policy.allows_replay()
```

## 14. 测试与验收

当前 L0 验收命令：

```bash
PYTHONPATH=. python3 -m pytest qxtrl/cc/tests/ -q
PYTHONPATH=. python3 -c 'from qxtrl.cc import minimal_rabi_lab; print(minimal_rabi_lab()["chip"].identity.id)'
python3 -m ruff check qxtrl/cc
```

当前已验证结果：

```text
24 passed
chip.demo_rabi_001
All checks passed
```

建议所有 L1+ 代码至少覆盖以下 contract tests：

1. 不可控 L0 对象进入 physical/control path 时必须拒绝。
2. 缺失 operation class 的 SafetyPolicy 必须拒绝。
3. Wiring role/channel 不满足最小语义时必须拒绝。
4. Quantity bool/NaN/Inf 必须拒绝。
5. schema version 名称错配必须拒绝。

## 15. 当前边界与后续增强

当前 L0 API 已能支撑 MVP Virtual Rabi 的最小契约，但以下内容仍是后续增强：

1. `WiringGraph` 与 `ChipModel` / `HardwareInventory` 的跨对象引用一致性。
2. `ChipModel` 中 coupler `element_id` 与 `endpoints` 的完全一致性。
3. resonator/coupler 全局 element ID 唯一性。
4. `L0Bundle` / snapshot 发布、hash 生成和不可变快照治理。
5. `SafetyPolicy.channel_limits` 的结构化 schema。
6. `DataQuality.approved_at` / `revoked_at` 的严格 ISO8601 格式校验。
7. resource group 的结构化冲突模型。

这些增强不应阻塞 L1/L2 MVP 开发，但进入真实硬件交付前应逐步补齐。
