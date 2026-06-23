# QXtrl L0 / CC (Core Contracts) 契约层命名与编码规则（短码 CC，包 `qxtrl/cc`）

**版本**: v0.2（工作草案）  
**日期**: 2026-05-31  
**定位**: 定义 QXtrl L0 Core Contracts / 核心契约层中芯片元素、硬件设备、硬件通道、逻辑线路、资源组、校准参数和快照对象的命名与编码规则。  
**关联文档**: [QXtrl 模块拆解与接口责任矩阵](QXtrl模块拆解与接口责任矩阵.md)

**落地工具**: [QXtrl L0 信息录入与审核工具需求](QXtrl_L0信息录入与审核工具需求.md)

**数据治理**: [QXtrl L0 数据与信息存放规则](QXtrl_L0数据与信息存放规则.md)

## 0. 为什么先定义 rules

L0 契约层不是单纯的数据结构集合，而是测控系统的治理规则。没有统一的命名和编码规则，后续 L1 实验语言、L2 IR/编译、调度器、校准 DAG、数据系统和 AI 接口都会出现隐式约定，最终变成脚本和配置里到处写死的“黑话”。

在新的模块拆解中，L0 对应 `Core Contracts` / 核心契约层；L1 已调整为 `Experiment Language` / 实验语言层。

本文件先定义 rules，再派生 schema。目标是让每个对象都能回答：

1. 它代表什么物理或逻辑对象。
2. 它的 ID 是否稳定、唯一、可追溯。
3. 它是否能被编译器、调度器和数据系统安全引用。
4. 它的来源、版本、可用性和安全状态是什么。

## 1. 总原则

| 编号 | 规则 | 说明 |
| --- | --- | --- |
| R-001 | ID 必须稳定 | ID 一旦进入运行记录、校准记录或数据文件，不得因显示名称变化而改变。 |
| R-002 | ID 不编码可变物理量 | 频率、幅度、功率、偏置、T1、误差率等会变化的信息不得写进 ID。 |
| R-003 | 内部 ID 与显示名分离 | 内部使用 `q003`，界面可显示 `Q4`、`Qubit 4` 或厂商原名。 |
| R-004 | 真实对象与占位对象分离 | 示例、导入中、未确认对象必须带 `status` 和 `usable_for_control: false`。 |
| R-005 | 缺失即拒绝 | 缺少线路映射、安全阈值、能力声明或校准快照时，默认拒绝实机执行。 |
| R-006 | 逻辑对象不直接引用厂商裸通道 | 实验和 Pulse IR 引用逻辑线路，编译/执行时再解析到硬件通道。 |
| R-007 | 硬件资源冲突显式建模 | LO、ADC、AWG、触发、复用读出链、共享 flux 线等必须进入资源组。 |
| R-008 | 快照不可变 | 每次实验运行引用的 L0 清单、校准快照和安全策略必须有不可变版本或哈希。 |
| R-009 | 所有对象带来源 | `source_kind`、`source_refs`、`confidence`、`approved_by` 是治理字段，不是可选装饰。 |
| R-010 | AI 只能读已声明能力 | AI/优化器不得根据字符串猜测设备或通道能力，必须读取 capability schema。 |
| R-011 | 能力、安全、校准三层边界分离 | `HardwareInventory` 描述设备能做到什么，`SafetyPolicy` 描述站点准许什么，`CalibrationSnapshot` 描述当前验证过什么。 |
| R-012 | 实机运行取最严格边界 | 同一参数同时受能力上限、安全上限和校准有效范围约束时，运行时必须取最严格范围。 |
| R-013 | 时间与时钟基准显式声明 | 所有快照、运行、校准和日志使用 UTC 时间戳；硬件时钟、采样率、触发基准必须记录来源。 |
| R-014 | 物理资产与安装位分离 | 设备物理资产、站点安装位和逻辑线路不是同一个 ID，换设备时必须生成新快照并触发影响分析。 |
| R-015 | schema 版本可迁移 | L0 对象必须带 `schema_version`，破坏性变更需要迁移规则和兼容性说明。 |
| R-016 | L0 定义治理契约，不实现存储引擎 | L0 规定数据和快照如何命名、引用和准入；具体 `ConfigStore`、`ResultStore`、`DataSink` 由 L5 数据与状态层实现。 |

## 2. ID 字符集与基本格式

### 2.1 字符集

内部 canonical ID 只允许：

```text
小写英文字母 a-z
数字 0-9
下划线 _
点号 .
```

禁止在 canonical ID 中使用：

```text
空格、中文、斜杠、反斜杠、冒号、逗号、括号、百分号、单位、厂商 GUI 显示名
```

原因是 ID 会进入文件路径、数据库键、API、日志、缓存哈希和运行记录。显示名可以使用中文和厂商原名，但 canonical ID 必须机器稳定。

### 2.2 通用 ID 结构

推荐使用点号表达层级：

```text
<domain>.<kind>.<name>
```

示例：

```text
station.st_lab01
chip.chip_001
dev.awg.awg01
chan.awg.awg01.out01
line.xy.q003
rg.lo.lo01
snap.calibration.20260529_001
```

对象局部字段中可以使用短 ID，例如 `q003`、`rr_q003`、`tc_q003_q004`。跨对象引用时应使用完整路径或结构化引用，避免歧义。

## 3. 芯片元素编码规则

### 3.1 元素类型

| 元素 | canonical ID 规则 | 示例 | 说明 |
| --- | --- | --- | --- |
| Qubit | `qNNN` | `q000`, `q127` | 内部默认从 0 开始编号，界面可映射为 Q1、Q128。 |
| Readout resonator | `rr_qNNN` | `rr_q000` | 若一个 qubit 对应一个 readout resonator，优先绑定 qubit ID。 |
| Coupler | `tc_qAAA_qBBB` 或 `fc_qAAA_qBBB` | `tc_q003_q004` | `tc` 表示 tunable coupler，`fc` 表示 fixed coupling edge。 |
| Bus / shared mode | `busNNN` | `bus000` | 多元素共享模式，不强行绑定单个 qubit。 |
| Control electrode / bias node | `bias_<target>` | `bias_tc_q003_q004` | 用于需要单独建模的偏置或 flux 控制对象。 |
| Logical qubit | `lqNNN` | `lq000` | QEC 或逻辑层对象，不等同于物理 qubit。 |
| QEC stabilizer | `stab_<type>_NNN` | `stab_x_000`, `stab_z_000` | 只在 QEC 工作流需要时引入。 |

### 3.2 编号规则

1. `NNN` 默认三位补零，支持 `q000` 至 `q999`。
2. 如果系统未来超过 999 个物理 qubit，应在新 schema 版本中扩展到四位，不在同一芯片内混用。
3. qubit 编号是 QXtrl 内部编号，不要求等同厂商编号或版图坐标。
4. 厂商编号、版图坐标、封装坐标应放在属性中：

```yaml
element_id: q003
display_name: Q4
vendor_label: Qubit_12
layout_coord:
  row: 2
  col: 5
package_coord:
  x_mm: unknown
  y_mm: unknown
```

### 3.3 Coupler 端点排序

Coupler ID 必须按端点 ID 字典序排序：

```text
tc_q003_q004  正确
tc_q004_q003  错误
```

原因是同一物理 coupler 不能因为书写顺序不同产生两个 ID。若 coupler 具有方向性，方向性写入属性：

```yaml
element_id: tc_q003_q004
endpoints: [q003, q004]
directionality:
  preferred_control: q003_to_q004
```

## 4. 设备与硬件通道编码规则

### 4.1 设备 ID

设备 ID 推荐格式：

```text
dev.<device_type>.<device_name>
```

常见 `device_type`：

| 类型 | 含义 | 示例 |
| --- | --- | --- |
| `awg` | 任意波形发生器 | `dev.awg.awg01` |
| `adc` | 采集卡或 digitizer | `dev.adc.adc01` |
| `mw` | 微波源 | `dev.mw.mw01` |
| `lo` | 本振源 | `dev.lo.lo01` |
| `mixer` | IQ mixer 或频率变换器 | `dev.mixer.mix01` |
| `dc` | 直流源 | `dev.dc.dc01` |
| `trig` | 触发/同步设备 | `dev.trig.trig01` |
| `fpga` | FPGA 或 sequencer | `dev.fpga.seq01` |
| `switch` | 微波/直流开关矩阵 | `dev.switch.sw01` |
| `attenuator` | 衰减器 | `dev.attenuator.att01` |
| `filter` | 滤波器 | `dev.filter.flt01` |
| `amp` | 放大器 | `dev.amp.amp01` |
| `crate` | 机箱或板卡框 | `dev.crate.crate01` |

设备属性必须至少包含：

```yaml
device_id: dev.awg.awg01
asset_id: asset.awg.awg01_serial_unknown
vendor: unknown
model: unknown
serial_number: unknown
firmware_version: unknown
driver_plugin: qxtrl_driver_unknown
connection:
  kind: tcpip | usb | pxi | pci | grpc | provider_api | unknown
  address_ref: secret_or_station_config_ref
status: draft | approved | deprecated | retired
```

### 4.1.1 物理资产与安装位

`device_id` 表示站点中的安装位或功能位，例如“第一台 AWG”。`asset_id` 表示一台具体物理设备，例如某个序列号的 AWG。两者必须分离：

```yaml
device_id: dev.awg.awg01
asset_id: asset.awg.keysight_m8195a_sn123456
installation:
  station_id: station.st_lab01
  slot: rack03_u12
  installed_at: 2026-05-29T10:00:00Z
  installed_by: user.device_engineer
```

如果同一安装位更换了物理设备，可以保留 `device_id`，但必须更新 `asset_id`、固件、能力声明和快照哈希，并触发以下影响分析：

1. 依赖该设备的线路是否仍然有效。
2. 设备能力上限是否变化。
3. SafetyPolicy 是否需要重新审批。
4. 相关 CalibrationSnapshot 是否失效。
5. 最近运行记录是否需要标记硬件变更。

### 4.2 硬件通道 ID

硬件通道 ID 推荐格式：

```text
chan.<device_type>.<device_name>.<channel_kind><NN>
```

示例：

```text
chan.awg.awg01.out01
chan.awg.awg01.marker01
chan.adc.adc01.in01
chan.mw.mw01.out01
chan.dc.dc01.out08
chan.trig.trig01.out01
```

通道只描述硬件端口，不描述它当前接到哪个 qubit。通道到芯片元素的关系由 `WiringGraph` 表达。

### 4.3 通道能力声明

每个硬件通道必须声明能力，而不是靠名字猜测：

```yaml
channel_id: chan.awg.awg01.out01
capabilities:
  signal_kind: analog_iq | analog_real | marker | trigger | dc | adc_input
  sample_rate:
    value: unknown
    unit: Sa/s
  amplitude_range:
    min: unknown
    max: unknown
    unit: V
  timing_resolution:
    value: unknown
    unit: s
  supports_waveform_upload: true
  supports_streaming: unknown
  safety_limits_ref: policy.channel.chan.awg.awg01.out01
```

### 4.4 能力上限、安全上限与校准有效范围

同一个运行参数可能同时受到三层限制：

| 层 | 所属对象 | 回答的问题 | 示例 |
| --- | --- | --- | --- |
| 能力上限 | `HardwareInventory` | 设备和固件能不能做到 | AWG 最高 `10 GSa/s` |
| 安全上限 | `SafetyPolicy` | 站点和芯片准不准这样做 | 当前线路最高允许 `4 GSa/s` |
| 校准有效范围 | `CalibrationSnapshot` | 当前参数是否验证过 | 当前校准只验证到 `2 GSa/s` |

运行时必须取最严格范围。若 AWG 能力为 `10 GSa/s`，安全策略允许 `4 GSa/s`，当前校准只覆盖 `2 GSa/s`，自动执行时有效上限就是 `2 GSa/s`。超过能力上限必须拒绝；超过安全上限必须拒绝或审批；超过校准有效范围必须拒绝、重新校准或进入明确审批流程。

```yaml
resolved_runtime_limit:
  parameter: sample_rate
  requested:
    value: 5.0e9
    unit: Sa/s
  hardware_capability_limit:
    max: 10.0e9
    source: hw_inv_20260529_001
  safety_limit:
    max: 4.0e9
    source: safety_20260529_001
  calibrated_valid_range:
    max: 2.0e9
    source: cal_snap_20260529_001
  decision: reject
  reason: requested_value_exceeds_safety_limit_and_calibrated_range
```

## 5. 逻辑线路编码规则

### 5.1 为什么需要逻辑线路

实验、Pulse IR 和校准节点不应直接写：

```text
chan.awg.awg01.out03
```

而应写：

```text
line.xy.q003
```

这样更换 AWG、换线、重接读出链时，不需要改实验定义，只需要更新 `WiringGraph`。

### 5.2 线路类型

| 线路类型 | ID 规则 | 示例 | 用途 |
| --- | --- | --- | --- |
| XY drive | `line.xy.qNNN` | `line.xy.q003` | 单 qubit 微波驱动。 |
| Readout | `line.ro.rr_qNNN` | `line.ro.rr_q003` | 读出 resonator 激励和采集链。 |
| Flux / Z | `line.z.qNNN` | `line.z.q003` | qubit flux 或 Z 控制。 |
| Coupler flux | `line.z.tc_qAAA_qBBB` | `line.z.tc_q003_q004` | tunable coupler 偏置或 flux 控制。 |
| Pump | `line.pump.<target>` | `line.pump.rr_q003` | 参数放大器或特殊泵浦链。 |
| Trigger | `line.trig.<group>` | `line.trig.main` | 触发和同步。 |
| LO | `line.lo.<group>` | `line.lo.xy_group01` | 本振分发链。 |
| Marker | `line.marker.<target>` | `line.marker.ro_group01` | 门控、开关、采集窗口。 |

### 5.3 线路到硬件通道的映射

`WiringGraph` 中应使用结构化映射，而不是字符串拼接：

```yaml
wiring_edges:
  - line_id: line.xy.q003
    role: drive_iq
    endpoints:
      chip_element: q003
      hardware_channels:
        i: chan.awg.awg01.out01
        q: chan.awg.awg01.out02
        lo: chan.lo.lo01.out01
    signal_chain:
      - dev.awg.awg01
      - dev.mw.mixer01
      - dev.lo.lo01
      - cryostat.input.xy_q003
    status: approved
```

### 5.4 线路状态

每条线路必须带状态：

```yaml
status: draft | approved | disabled | retired | unknown
usable_for_control: true | false
approved_by: person_or_role
approved_at: YYYY-MM-DDTHH:MM:SSZ
```

只有 `status: approved` 且 `usable_for_control: true` 的线路可以进入实机编译。

## 6. 资源组编码规则

资源组用于表达冲突和共享约束。它不是 UI 分组，而是调度器必须理解的安全约束。

### 6.1 资源组 ID

```text
rg.<resource_type>.<name>
```

示例：

```text
rg.lo.xy_lo01
rg.readout_mux.ro_mux00
rg.adc.adc01
rg.awg.awg01
rg.trigger.main
rg.cryostat.input_bundle01
rg.crosstalk.zone00
```

### 6.2 资源组规则

```yaml
resource_group_id: rg.readout_mux.ro_mux00
resource_type: readout_multiplex_group
members:
  - line.ro.rr_q000
  - line.ro.rr_q001
  - line.ro.rr_q002
conflict_policy:
  mode: shared_with_constraints
  max_simultaneous_measurements: 3
  requires_distinct_frequencies: true
  requires_common_lo: true
scheduler_behavior:
  missing_policy: deny_parallelization
```

调度器不得根据 qubit 距离或编号自动猜测并行性。并行执行必须由资源组和安全策略共同允许。

## 7. 校准参数编码规则

### 7.1 参数 key 与记录 ID 分离

`CalibrationRecord` 的记录 ID 可以是 UUID 或内容哈希，但参数 key 必须稳定、可读：

```text
<element_id>.<domain>.<parameter_name>
```

示例：

```text
q003.xy.f01
q003.xy.pi_amp
q003.xy.pi_duration
rr_q003.ro.freq
rr_q003.ro.iq_classifier
tc_q003_q004.cz.amp
tc_q003_q004.cz.duration
line.xy.q003.skew
line.ro.rr_q003.delay
```

### 7.2 参数记录示例

```yaml
parameter_key: q003.xy.pi_amp
record_id: calrec_20260529_000123
value:
  nominal: 0.182
  unit: a.u.
  uncertainty: 0.004
source:
  run_id: run_20260529_153012_abc123
  analysis_version: qxtrl.analysis.rabi/v0.1
state: candidate | active | rejected | retired
validity:
  valid_from: 2026-05-29T15:31:00Z
  expires_at: 2026-05-30T15:31:00Z
  invalidated_by:
    - q003.xy.f01
quality:
  score: 0.97
  metrics:
    fit_r2: 0.994
```

## 8. 快照与版本规则

任何实机运行必须引用不可变快照：

```yaml
run_inputs:
  hardware_inventory_snapshot: hw_inv_20260529_001
  wiring_graph_snapshot: wiring_20260529_001
  chip_model_snapshot: chip_20260529_001
  safety_policy_snapshot: safety_20260529_001
  calibration_snapshot: cal_snap_20260529_001
```

规则：

1. 快照生成后不可修改，只能生成新快照。
2. 快照必须包含内容哈希。
3. 快照必须记录来源、审批人、生成时间和适用范围。
4. `RunManifest` 必须保存全部快照引用。
5. 快照过期时，运行时必须拒绝或降级为模拟/回放。

### 8.1 Schema 版本与迁移

每个 L0 / CC 对象必须包含 `schema_version`，格式为（对应模块短码 cc）：

```text
qxtrl.cc.<ObjectName>/v<major>.<minor>
```

规则：

1. `minor` 版本可以添加向后兼容字段。
2. `major` 版本表示存在破坏性变更。
3. 发布新 `major` 版本时必须提供迁移规则或明确不能迁移的原因。
4. 快照必须记录生成它所用的 schema 版本和 validator 版本。
5. 运行时不得混用互不兼容的 L0 快照。

### 8.2 时间、时区与硬件时钟

所有治理时间戳使用 UTC ISO 8601 格式：

```text
2026-05-29T15:30:12Z
```

本地时区只用于界面显示，不能进入 canonical snapshot。硬件相关时间必须额外声明时钟来源：

```yaml
timing_reference:
  wall_clock: utc
  station_clock: station_clock_001
  hardware_clock:
    source: dev.clock.clk01
    frequency:
      value: 10.0e6
      unit: Hz
    locked_to_external_reference: true
  trigger_reference: line.trig.main
```

任何涉及采样率、dt、触发延迟、采集窗口、波形对齐的规则，都必须可追溯到 `HardwareInventory` 和 `WiringGraph` 中的时钟/触发声明。

## 9. Station / QPU Onboarding 清单

每台量子计算机进入测试校准前，必须完成以下 L0 清单：

| 清单 | 必填内容 | 未完成时行为 |
| --- | --- | --- |
| Station registry | 实验站 ID、位置、权限、部署模式 | 不允许创建实机任务 |
| HardwareInventory | 设备、通道、固件、驱动、能力声明 | 不允许编译到真实后端 |
| ChipModel | qubit、readout、coupler、拓扑、设计元数据 | 不允许引用芯片元素 |
| WiringGraph | 逻辑线路到硬件通道映射、资源组、线路状态 | 不允许下发真实脉冲 |
| SafetyPolicy | 通道边界、操作权限、审批规则、禁止动作 | 不允许任何实机执行 |
| InitialCalibrationSnapshot | 初始频率、读出、基础脉冲、有效状态 | 只允许发现型低风险流程或模拟 |
| Data governance | 数据路径、保留策略、脱敏规则、访问权限 | 不允许保存真实客户/芯片数据 |
| Clock and timing | 站点时钟、参考源、触发链、采样率基准 | 不允许执行需要精确定时的实机任务 |

这些清单不应主要依靠手写 YAML 完成。实际落地时，应通过 L0 信息录入与审核工具提供表单、导入、拓扑编辑、线路映射、校验中心、审批和快照发布能力，确保规则在交互层和后端 validator 中一致执行。

数据治理本身也是 L0 准入的一部分。每个站点必须明确配置草稿、已发布快照、运行记录、原始数据、处理数据、校准记录、日志、诊断包和敏感信息的存放规则。没有数据治理配置的站点，不应进入正式实机运行。

## 10. 禁止事项

以下做法在 L0 契约层中禁止：

1. 在实验脚本中直接写硬件通道号。
2. 在 qubit ID 中编码频率、位置、角色或当前状态。
3. 用 `Q1`、`Q2` 等显示名作为唯一内部 ID。
4. 复用已退役设备或芯片元素的 ID 表示新物理对象。
5. 在没有资源组约束时自动并行执行。
6. 在没有安全阈值时允许 AI 或自动校准提交实机动作。
7. 把厂商 SDK 返回的临时名称直接当作 QXtrl canonical ID。
8. 修改历史快照而不是创建新快照。

## 11. 最小示例

```yaml
station_id: station.st_lab01
chip_id: chip.chip_001

chip_elements:
  qubits:
    - element_id: q000
      display_name: Q1
    - element_id: q001
      display_name: Q2
  resonators:
    - element_id: rr_q000
      attached_to: q000
    - element_id: rr_q001
      attached_to: q001
  couplers:
    - element_id: tc_q000_q001
      endpoints: [q000, q001]

hardware:
  devices:
    - device_id: dev.awg.awg01
      device_type: awg
    - device_id: dev.adc.adc01
      device_type: adc
    - device_id: dev.lo.lo01
      device_type: lo
  channels:
    - channel_id: chan.awg.awg01.out01
      signal_kind: analog_iq_i
    - channel_id: chan.awg.awg01.out02
      signal_kind: analog_iq_q
    - channel_id: chan.adc.adc01.in01
      signal_kind: adc_input

wiring:
  - line_id: line.xy.q000
    maps_to:
      i: chan.awg.awg01.out01
      q: chan.awg.awg01.out02
      lo: chan.lo.lo01.out01
    status: approved
  - line_id: line.ro.rr_q000
    maps_to:
      adc: chan.adc.adc01.in01
    status: approved

resource_groups:
  - resource_group_id: rg.lo.xy_lo01
    members:
      - line.xy.q000
      - line.xy.q001
    conflict_policy:
      mode: shared_lo
      scheduler_behavior: require_frequency_separation_check
```

## 12. 待讨论问题

1. qubit 内部编号是否统一采用 0-based，还是允许站点选择 1-based 但必须声明？
2. 三位补零是否足够，是否一开始就采用四位编号？
3. tunable coupler 是否统一用 `tc_`，fixed coupling edge 是否统一用 `fc_`？
4. readout resonator 是否始终绑定 qubit，还是允许独立编号 `rr000`？
5. 线路 ID 是否需要区分输入、输出和双向链路？
6. 是否需要把 cryostat feedline、attenuator、filter、amplifier 作为 L0 可选对象建模？
7. 安全策略中的通道阈值应由硬件团队、测控团队还是站点管理员审批？
