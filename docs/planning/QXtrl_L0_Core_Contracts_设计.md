# QXtrl L0 Core Contracts (核心契约层)

**版本**: v0.1 (MVP-01 最小实现)  
**日期**: 2026-06-21  
**状态**: 实现启动中，基于 v0.2 规则文档与 MVP 最薄切片  
**关联文档**: 
- [QXtrl_架构层号与文档索引.md](QXtrl_架构层号与文档索引.md)
- [QXtrl模块拆解与接口责任矩阵.md](QXtrl模块拆解与接口责任矩阵.md)
- [QXtrl_L0契约层命名与编码规则.md](QXtrl_L0契约层命名与编码规则.md)
- [QXtrl_L0数据与信息存放规则.md](QXtrl_L0数据与信息存放规则.md)
- [QXtrl_L0契约层_schema示例_Willow_Heron.md](QXtrl_L0契约层_schema示例_Willow_Heron.md)
- [QXtrl_MVP最薄垂直切片定义.md](QXtrl_MVP最薄垂直切片定义.md)
- [QXtrl量子测控软件开发需求.md](QXtrl量子测控软件开发需求.md) (v0.4)
- [template.md](../../template.md)

## 0. 文档目的与范围

定义并实现 L0 Core Contracts 的最小可交付 Python 契约集合，作为 QXtrl 所有上层模块 (L1-L9) 的强制基础。L0 不实现业务逻辑、存储引擎或执行，只提供：

- 领域对象 schema 与版本化
- ID 命名与编码规则的机器可验证实现
- 单位/数量模型
- 安全与可用性治理字段（missing => deny）
- 基础错误模型
- 快照引用与来源审计字段

MVP 范围严格对齐最薄垂直切片：仅支持 Rabi 在 Virtual 后端跑通所需的最小 L0 对象。后续按需扩展。

**明确边界**：
- 负责：schema 定义、验证器、公共类型、示例数据（占位与最小有效）。
- 不负责：ConfigStore 持久化（L5）、具体校准节点（L6）、真实驱动（L3）、UI 表单（L9）。

## 1. 背景与当前问题

历史 QuarkStudio / 脚本使用隐式路径、字符串 ID、无版本 schema、混杂配置与结果，导致不可追溯、无法安全并行、难以支持 AI/校准闭环。L0 通过显式治理规则 + typed contracts 解决根本。

P0 契约补丁与命名规则已冻结，需落地为可测试的代码。

## 2. 所属架构层与边界

- **层**：L0 / CC (Core Contracts / 核心契约)，横切所有层。
- **稳定英文名**：Core Contracts
- **短码 / 包名**：CC / `qxtrl/cc` (或 `qxtrl.core.contracts`)
- **上游**：无（基础）。
- **下游**：L1/EL ExperimentSpec、L2/CPIR PulseIR、L3/EB ExecutionBackend、L4/RS RunRequest、L5/DS Config/Result、L6/CO CalibrationRecord 等均必须消费 L0/CC (qxtrl/cc) 类型。
- **不变性**：已发布快照对象、RunManifest 输入引用、schema_version。
- **候选状态**：draft 配置、未审批 SafetyPolicy。

参考矩阵：L0 明确不负责业务逻辑实现。

## 3. 输入 / 输出 / 状态 / 错误模型

### 输入
- 手工/工具录入的 YAML/JSON 或 Python dict（经 L0 validator）。
- 配置快照引用。

### 输出
- 验证通过的 Pydantic 模型实例（可安全序列化）。
- Validation 错误携带精确字段 + 治理原因（e.g. "usable_for_control=false"）。
- Snapshot hash / 版本。

### 状态影响
L0 模型本身纯数据；`data_quality.usable_for_control` 影响上层是否允许 physical run，但 L0 不执行写操作。

### 错误模型
- `QXtrlValidationError`（字段、ID 格式、缺失必填）。
- `SafetyViolation`（违反 policy）。
- `SchemaVersionError`（不兼容）。
- 所有错误必须可机器解析 + 人可读消息 + 建议修复。

## 4. 核心对象或 API

按 MVP + 命名规则 + schema 示例，核心对象（最小字段优先）：

1. **Quantity**：带 unit、uncertainty、source 的物理量。支持 "unknown"。
2. **Identity** / **SourceInfo**：id、display_name、vendor、source_kind、source_refs、confidence。
3. **ChipModel**：qubits (element_id: qNNN)、resonators、couplers、topology 占位。支持 Rabi 需要的单 qubit。
4. **WiringGraph** / **WiringEdge**：line_id (line.xy.q000) → hardware channels 映射。status + usable_for_control。
5. **HardwareInventory**（最小）：devices、channels、capability 声明（sample_rate 等）。
6. **SafetyPolicy**：global_rules、channel_limits、policy_mode="deny_by_default"。
7. **L0SnapshotRef** / Bundle：用于 RunManifest 引用的不可变快照引用 + hash。
8. **Domain / QXtrlError** 基类。

公共 API 示例（Python）：
```python
from qxtrl.cc import (
    Quantity, ChipModel, WiringGraph, SafetyPolicy,
    validate_id, QXtrlValidationError
)

q = Quantity(value=5.2e9, unit="Hz", uncertainty=1e6)
chip = ChipModel(...)  # 验证通过
```

所有对象必须：
- 带 `schema_version: "qxtrl.cc.<Name>/v0.1"`
- 实现 `.model_dump()` / `.model_validate()` (pydantic)
- 通过 ID 格式、缺失策略和三层限制规则（cap / safety / calibrated）校验。

## 5. 生命周期或执行流程

L0 对象生命周期：
1. draft（录入工具） → validator（ID、必填、单位）
2. publish → 产生不可变 snapshot（含 hash、approved_by、generated_at）
3. 引用（ExperimentSpec、RunManifest、CalibrationRecord） → 运行时取最严格边界
4. 失效 → 新 snapshot 替换，旧记录保留（不可修改）

编译/执行边界只接受 `usable_for_control=true` + approved snapshot 的 L0 对象。

## 6. 安全、权限、IP、数据治理约束

- 严格遵守命名规则（R-001..R-016）：ID 稳定、小写、点分、不编码可变物理量、物理资产与安装位分离。
- missing_fields_policy = "deny_physical_execution"
- 凭据绝不进入 L0 模型（仅 credential_ref）。
- 所有 L0 对象支持脱敏导出级别。
- Schema 版本迁移：major 破坏需迁移规则。
- L0 代码本身必须洁净实现（不直接复制历史驱动逻辑）。

## 7. 测试与验收标准

### 必须测试（MVP）
- ID 格式：q000、line.xy.q003、dev.awg.awg01、chan...、rg... 合法与非法。
- Quantity：单位已知列表（Hz, s, V, Sa/s, ...）、unknown 处理、算术占位。
- 必填字段缺失 → 精确 ValidationError。
- usable_for_control=false + physical 尝试 → 拒绝。
- 三层边界解析示例（cap > safety > cal）。
- schema_version 一致性与不匹配拒绝。
- 快照引用不可变性（模型可 hash 用于缓存 key）。
- 序列化往返（to yaml/json + 回模型）。
- 公共示例（Willow/Heron 占位）验证为 unusable。

### 验收证据
- pytest 全部通过。
- 可从 Python 构造最小 Rabi 所需 L0 对象并通过验证。
- 错误消息包含规则编号（如 R-005）。
- 至少一个端到端小示例脚本（不依赖上层 L1+）。

## 8. MVP 范围与 OUT 清单

**IN (MVP-01)**:
- 最小 ChipModel (qubit + 基础属性)
- WiringGraph (单 qubit XY/RO 线路)
- HardwareInventory (1 AWG + ADC 占位)
- SafetyPolicy (deny_by_default + 基本 limit)
- Quantity + Identity + 通用基类
- ID 校验器 + schema_version 机制
- 公共占位示例 + 最小 lab 示例（可用于 virtual Rabi）
- 基础错误类型

**OUT (本阶段)**:
- 完整站点资产、批量设备、cryostat feedline 等高级建模
- 完整 SafetyPolicy（审批工作流细节留 L9 工具）
- 校准参数 key 具体（L6 负责，但 L0 定义编码规则）
- 持久化 / ConfigStore（L5）
- 资源组冲突完整建模（P1，SCP-004）
- 云后端 / provider 特殊字段（Heron 仅示例）

## 9. 待确认问题和决策表

| ID | 问题 | 影响 | 建议 / 状态 |
|----|------|------|-------------|
| L0-Q1 | qubit 编号 0-based 还是站点可声明 1-based？ | ID 规则 | 内部强制 0-based（q000），display_name 自由；已按命名规则实现 |
| L0-Q2 | 单位系统：pint vs 简单字符串 + 已知列表？ | 复杂度 | MVP 用简单 + 枚举已知单位；需要真实转换时再引入 pint（不污染 L0 契约） |
| L0-Q3 | snapshot hash 算法固定 sha256？ | 互操作 | 是，记录在模型中 |
| L0-Q4 | 是否现在就支持 resource_groups 最小形式？ | MVP | 包含占位字段，完整规则 P1 |

## 10. API 参考文档

详细的公共 API 说明（类、字段、方法、验证规则、使用示例）已生成：

→ **[docs/L0_API.md](../L0_API.md)**

该文档会随代码演进同步维护，推荐开发者优先查阅。

## 11. 后续升版条件

- L0 schema 破坏性变更必须更新本文件 + 迁移指南 + 所有下游契约测试 + L0_API.md。
- 当 L1 ExperimentSpec、L2 PulseIR 锁定后，L0 需审查是否需要补充字段（e.g. timing_reference 更丰富）。
- 真实硬件插件引入前，扩展 HardwareInventory capability 声明。

**Backlog 项**：
- ChipModel 拓扑一致性增强（当前仅基础引用存在性校验；完整规则如 resonator 绑定、coupler 无重复、与 Wiring 交叉校验等列入后续，见复审意见）。

---

**实施顺序建议**（与 MVP 工作包对齐）：
1. 基础模型 + Quantity + validators + errors
2. ChipModel + ID 规则
3. WiringGraph + 线路映射
4. HardwareInventory + SafetyPolicy
5. 示例数据 + 测试 + 文档示例
6. 与 L1 联调准备（本设计不包含 L1）

本设计文档本身也需在代码首次落地后更新为 "v0.1 实现完成" 并加入 CHANGELOG 条目。