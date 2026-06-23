# QXtrl L0 数据与信息存放规则

**版本**: v0.2（工作草案）  
**日期**: 2026-05-31  
**定位**: 定义 QXtrl L0 Core Contracts / 核心契约层中配置、快照、运行记录、实验数据、校准数据、日志、诊断包和敏感信息的存放、引用、权限、保留和交接规则。  
**关联文档**: [QXtrl L0 契约层命名与编码规则](QXtrl_L0契约层命名与编码规则.md)

## 0. 为什么 L0 要管数据存放

测控系统中最危险的混乱不一定出现在驱动代码里，也可能出现在数据和配置里：

1. 某次运行到底用了哪版线路、哪版安全策略、哪版校准参数，无法追溯。
2. 原始数据、分析结果、校准参数和日志分散在脚本目录里。
3. 真实芯片参数、站点地址、凭据和客户数据混在普通配置中。
4. 旧数据被覆盖，导致分析和校准无法复现。
5. AI 或自动化工具读取了未审核、过期或敏感数据。

因此 L0 不仅要定义芯片、线路和设备规则，也要定义数据与信息的存放规则。

## 1. 数据分类

| 类别 | 示例 | 敏感性 | 是否可变 | 默认存放 |
| --- | --- | --- | --- | --- |
| 配置草稿 | 未审核的 HardwareInventory、WiringGraph | 中 | 可变 | `config/drafts/` 或配置数据库 draft 表 |
| 已发布快照 | 已审核 L0 snapshot | 中/高 | 不可变 | `config/snapshots/` 或版本化对象存储 |
| 运行记录 | `RunManifest`、任务状态、操作者、输入快照引用 | 高 | 不可变 | `runs/<run_id>/manifest.*` |
| 原始实验数据 | ADC trace、IQ 点、波形采集 | 高 | 不可变 | `runs/<run_id>/raw/` |
| 处理数据 | averaged IQ、拟合输入、降采样曲线 | 中/高 | 可再生成 | `runs/<run_id>/processed/` |
| 分析结果 | 拟合参数、质量指标、图表 | 中 | 可版本更新 | `runs/<run_id>/analysis/<analysis_version>/` |
| 校准记录 | `CalibrationRecord`、active snapshot、回滚链 | 高 | 状态可变，历史不可变 | `calibration/records/`、`calibration/snapshots/` |
| 数字孪生模型 | `TwinModel`、训练数据引用、验证报告 | 高 | 版本化 | `twins/models/`、`twins/reports/` |
| 日志 | 系统日志、设备日志、审计日志 | 中/高 | 追加 | `logs/` 或日志系统 |
| 诊断包 | 支持导出、错误上下文、配置摘要 | 高 | 生成后不可变 | `diagnostics/<package_id>/` |
| 凭据和密钥 | token、密码、私钥、设备登录信息 | 极高 | 可轮换 | secret manager，不进入普通配置 |

## 2. 基本规则

| 编号 | 规则 | 说明 |
| --- | --- | --- |
| D-001 | 运行输入不可变 | 一次实机运行引用的 L0 快照、校准快照、软件版本和操作者必须写入 `RunManifest`。 |
| D-002 | 原始数据不可覆盖 | raw trace、IQ 原始点和设备返回原始 payload 只能追加或新建版本，不能原地覆盖。 |
| D-003 | 分析结果可重算但需版本化 | 同一 raw 数据可被多个分析版本处理，分析结果必须带算法版本和参数。 |
| D-004 | 校准状态可变，历史不可变 | active/rejected/retired 状态可变化，但每条 `CalibrationRecord` 的内容不可修改。 |
| D-005 | 凭据不得进入普通配置 | IP 可作为受控配置，密码、token、证书私钥必须进入 secret manager。 |
| D-006 | 草稿不能被运行时读取 | 编译器、调度器、AI 和实机执行只能读取已发布快照。 |
| D-007 | 数据路径不得硬编码在实验脚本中 | 运行时由 L5 的 ResultStore / DataSink 分配路径并返回引用。 |
| D-008 | 删除必须可审计 | 数据删除、归档、脱敏和导出都需要记录操作者、时间和原因。 |
| D-009 | 客户/芯片敏感信息默认不外发 | 诊断包和交接包必须支持脱敏导出。 |
| D-010 | AI 只读已授权数据视图 | AI 不直接读文件系统，只通过受控 API 获取最小必要上下文。 |

## 3. 推荐存放结构

本地或离线部署可先采用文件 + SQLite/PostgreSQL 索引的混合结构。对象存储或数据库部署时也应保留同样的逻辑分区。

```text
qxtrl_workspace/
├── config/
│   ├── drafts/
│   │   └── station.st_lab01/
│   └── snapshots/
│       └── station.st_lab01/
│           ├── hw_inv_20260529_001.yaml
│           ├── wiring_20260529_001.yaml
│           ├── chip_20260529_001.yaml
│           ├── safety_20260529_001.yaml
│           └── l0_bundle_20260529_001.yaml
├── calibration/
│   ├── records/
│   └── snapshots/
├── runs/
│   └── 2026/05/29/
│       └── run_20260529_153012_abc123/
│           ├── manifest.yaml
│           ├── raw/
│           ├── processed/
│           ├── analysis/
│           ├── figures/
│           └── logs/
├── twins/
│   ├── models/
│   ├── validation_reports/
│   └── replay_sets/
├── diagnostics/
├── exports/
└── logs/
```

真实生产部署可以把这些逻辑目录映射到：

1. 本地文件系统。
2. NAS / 实验站共享存储。
3. 对象存储。
4. 数据库。
5. 版本化配置仓库。

但逻辑命名和引用规则应保持一致。

## 4. RunManifest 必填引用

每次运行必须生成 `RunManifest`，并至少包含：

```yaml
run_id: run_20260529_153012_abc123
station_id: station.st_lab01
chip_id: chip.chip_001
operator:
  user_id: user.zhangsan
  role: calibration_engineer
started_at: 2026-05-29T15:30:12Z
software:
  qxtrl_version: 0.1.0
  git_commit: unknown
  environment_hash: unknown
input_snapshots:
  hardware_inventory_snapshot: hw_inv_20260529_001
  wiring_graph_snapshot: wiring_20260529_001
  chip_model_snapshot: chip_20260529_001
  safety_policy_snapshot: safety_20260529_001
  calibration_snapshot: cal_snap_20260529_001
execution:
  backend_id: backend.virtual_qpu_001
  compiled_bundle_hash: sha256:...
  run_mode: simulation | replay | physical | hil
data_refs:
  raw: runs/2026/05/29/run_20260529_153012_abc123/raw/
  processed: runs/2026/05/29/run_20260529_153012_abc123/processed/
  logs: runs/2026/05/29/run_20260529_153012_abc123/logs/
status:
  final_state: succeeded | failed | cancelled | rejected
  failure_reason: null
```

没有 `RunManifest` 的数据不能进入校准晋升，也不能作为数字孪生训练或 AI 评估依据。

## 5. 校准数据存放规则

校准数据分三层：

| 层 | 对象 | 说明 |
| --- | --- | --- |
| 参数记录 | `CalibrationRecord` | 单个参数的一次候选、激活、拒绝或退役记录。 |
| 参数快照 | `CalibrationSnapshot` | 某一时刻可用于运行的 active 参数集合。 |
| 校准谱系 | `CalibrationLineage` | 参数之间的依赖、失效传播、回滚关系。 |

规则：

1. `CalibrationRecord` 内容不可变。
2. active 状态变化必须生成审计事件。
3. `CalibrationSnapshot` 发布后不可修改。
4. 每个 active 参数必须能追溯到 `run_id`、分析版本和质量指标。
5. 人工录入参数必须记录录入人、审批人和原因。
6. 从厂商或历史系统导入的参数必须标注来源和可信度。

## 6. 敏感信息规则

### 6.1 禁止进入普通配置的内容

以下内容不得进入 `HardwareInventory`、`WiringGraph`、`ChipModel`、`RunManifest` 的普通明文导出：

1. 设备登录密码。
2. API token。
3. SSH 私钥。
4. 数据库密码。
5. 客户身份信息。
6. 未脱敏的客户站点地址。
7. 不允许外发的真实芯片设计文件。

普通配置中只能保存引用：

```yaml
connection:
  kind: tcpip
  address: 192.168.10.23
  credential_ref: secret://station.st_lab01/dev.awg.awg01/login
```

### 6.2 诊断包脱敏

导出诊断包时应提供脱敏级别：

| 级别 | 内容 |
| --- | --- |
| internal_full | 内部完整诊断，仍不含密钥明文 |
| vendor_support | 给设备厂商，移除芯片敏感参数和客户身份 |
| customer_handoff | 给客户，保留运行摘要和可交付证据 |
| public_example | 仅保留结构，不含真实数据 |

## 7. 保留、归档与删除

建议默认策略：

| 数据 | 默认保留 | 说明 |
| --- | --- | --- |
| L0 已发布快照 | 永久 | 运行可追溯所必需 |
| RunManifest | 永久 | 数据索引和审计核心 |
| CalibrationRecord | 永久 | 参数谱系和回滚所必需 |
| 原始 raw trace | 按项目策略，默认 6 至 24 个月 | 可根据容量与重分析价值分级 |
| 处理数据 | 可重算则短期，关键结果长期 | 保留生成脚本和版本 |
| 日志 | 3 至 12 个月 | 安全审计日志可更长 |
| 诊断包 | 按支持周期 | 到期归档或删除 |
| 数字孪生训练集 | 与模型生命周期绑定 | 删除训练集会影响模型可审计性 |

删除规则：

1. 不允许直接删除已被 active 校准或 TwinModel 引用的数据。
2. 删除前必须生成影响分析。
3. 删除、归档、脱敏均生成审计事件。

## 8. L5 数据接口原则

L0 只定义数据治理契约，不实现具体存储引擎。具体 `ConfigStore`、`ResultStore`、`DataSink` 属于 L5 数据与状态层；它们必须遵守 L0 中定义的命名、引用、权限、保留、脱敏和审计规则。

上层模块不直接拼文件路径，而通过 ResultStore / DataSink 写入和引用数据：

```python
run_ref = result_store.create_run(
    station_id="station.st_lab01",
    chip_id="chip.chip_001",
    input_snapshots={...},
)

raw_ref = data_sink.write_raw_dataset(
    run_id=run_ref.run_id,
    name="iq_points",
    data=iq_array,
    metadata={...},
)
```

ResultStore / DataSink 至少负责：

1. 分配 `run_id` 和路径。
2. 写入 `RunManifest`。
3. 记录数据 hash、shape、单位、坐标和来源。
4. 维护 raw、processed、analysis 的关联。
5. 检查权限和数据保留策略。
6. 提供查询和导出 API。

## 9. 数据集最小元数据

任何进入 ResultStore / DataSink 的实验数据集都必须带最小元数据。没有最小元数据的数据，不能进入校准晋升、数字孪生训练或 AI 评估。

```yaml
dataset_id: ds_run_20260529_153012_iq_points
run_id: run_20260529_153012_abc123
kind: raw_iq | raw_trace | processed_curve | analysis_result | figure | log
format: zarr | hdf5 | netcdf | parquet | numpy | json | png | text
schema_version: qxtrl.data.Dataset/v0.1
created_at: 2026-05-29T15:31:00Z
producer:
  module: qxtrl.backend.virtual/v0.1
  software_version: 0.1.0
content:
  shape: [101, 2]
  dtype: float64
  dims: [sweep_point, iq_component]
  coordinates:
    sweep_frequency:
      unit: Hz
      source: ExperimentSpec
    iq_component:
      values: [I, Q]
units:
  signal: V
hash:
  algorithm: sha256
  value: unknown_until_written
lineage:
  input_snapshots:
    calibration_snapshot: cal_snap_20260529_001
  parent_datasets: []
access:
  sensitivity: internal | sensitive_chip | customer_confidential | public_example
  export_policy: internal_full
```

最低规则：

1. 数据必须带 `run_id`。
2. 数值数据必须带单位、shape、dtype、维度名和坐标。
3. 处理数据必须引用父数据。
4. 分析结果必须记录分析模块版本和输入参数。
5. 数据 hash 应在写入完成后生成。
6. 脱敏数据必须保留与原始数据的受控谱系关系。

## 10. 对 L0 Onboarding 工具的要求

L0 信息录入与审核工具必须支持配置数据治理：

| 功能 | 说明 |
| --- | --- |
| 存储位置配置 | 为站点设置 config、runs、calibration、logs、diagnostics 的根位置 |
| 敏感字段识别 | 标记哪些字段不能导出 |
| 数据保留策略 | 为 raw、processed、logs、diagnostics 设置保留期限 |
| 快照发布 | 发布后写入不可变位置 |
| 诊断包导出 | 支持脱敏级别 |
| 交接包生成 | 导出站点 L0 状态、数据路径和权限说明 |

## 11. 待讨论问题

1. 首版采用纯文件存储、数据库存储，还是混合方式？
2. `RunManifest` 用 YAML、JSON，还是 Parquet/数据库记录？
3. 原始数据首选 HDF5、Zarr、NetCDF、Parquet，还是按实验类型选择？
4. 是否需要所有数据文件都有内容哈希和签名？
5. 客户现场是否允许集中对象存储，还是必须本地离线？
6. 数据保留策略由项目、站点还是客户配置决定？
7. AI 读取历史数据时需要怎样的最小权限视图？
