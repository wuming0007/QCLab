# QXtrl 快速上手教程（新手 10 分钟跑通实验）

**目标**  
让一个完全的新手在 5~10 分钟内完成以下完整流程：

1. “新芯片到场” —— 录入芯片拓扑、连线、硬件、比特参数（L0）
2. 定义一个真实实验（以 **Time Rabi** 为例：在 q001 上固定幅度 0.1，扫描脉冲宽度）
3. 提交任务并获得结果
4. 在看板上看到任务流、结果可视化，并进行回放审查

本教程使用 **虚拟后端**（无需真实硬件），完美适合彩排和学习。

---

## 1. 环境准备

### 1.1 先决条件
- Python 3.10+
- （推荐）`uv` 包管理器（速度快）

```bash
# 检查 uv（没有就安装）
uv --version
# 安装 uv（macOS / Linux）
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 1.2 克隆并安装项目

```bash
# 进入项目根目录（假设你已经 clone 了 QCLab）
cd /path/to/QCLab

# 使用 uv 创建并激活虚拟环境（推荐）
uv venv .venv --python 3.12
source .venv/bin/activate   # macOS/Linux
# Windows: .venv\Scripts\activate

# 安装项目（开发模式）
uv pip install -e .
# 或者传统方式
pip install -e .
```

> **最简单方式（无需安装）**：直接用 `PYTHONPATH=.`

---

## 2. 最快跑通方式（推荐新手）

直接运行我们准备好的**简易看板**，它会自动完成“录入 → 提交 Time Rabi → 展示结果 + 回放”的完整故事：

```bash
# 方式一：使用 PYTHONPATH（最稳）
PYTHONPATH=. python -m qxtrl.examples.simple_dashboard

# 方式二：如果你已经 pip install -e .
python -m qxtrl.examples.simple_dashboard
```

**你会看到什么？**

- **当前系统设置看板**（L0）：芯片拓扑、连线结构（q001 的 drive/readout 线）、硬件信息、比特参数
- **任务流进度**：L1 → L2 → L3 → L4 → L6 → L5 清晰阶段
- **结果可视化**：
  - 数据表格（duration_ns | I | Q）
  - ASCII 振荡曲线
- **回放审查**：L7 Replay Inspect（带 `require_hash_check` 验证）

运行结束后，你就完成了**一次完整的实验彩排**！

---

## 3. 理解发生了什么（高层流程）

```
新手视角（你关心的）：
录入芯片/连线/硬件  →  定义 Time Rabi 实验  →  提交运行  →  看结果 + 回放

对应 QXtrl 层级：
L0 (Core Contracts)   →  L1 (Experiment Language)  →  L4 (Runtime) + L3 (Backend) + L7 (Virtual)  →  L5 (Manifest) + L7 (Replay) + L9 (Dashboard)
```

整个过程**不写真实硬件**，全部走虚拟后端，100% 可复现。

---

## 4. 手动逐步方式（想深入理解时使用）

如果你想一步步手动控制（适合学习或写自己的脚本）：

```python
# 1. 录入 L0 设置（相当于“新芯片录入”）
from qxtrl.cc.examples import make_rabi_lab

lab = make_rabi_lab(qubit_id="q001", freq_hz=5.234e9)
print("已录入芯片:", lab["chip"].identity.id)
print("控制线:", lab["drive_line"])
print("读取线:", lab["readout_line"])

# 2. 定义 Time Rabi 实验（固定幅度 0.1，扫描脉冲宽度）
from qxtrl.el import create_time_rabi_experiment_spec

spec = create_time_rabi_experiment_spec(
    qubit_id="q001",
    drive_line_id=lab["drive_line"],
    readout_line_id=lab["readout_line"],
    durations=[10.0, 20.0, 30.0, 40.0, 50.0, 80.0, 120.0],  # ns
    fixed_amplitude=0.1,
    l0_chip_model_ref=lab["chip"],
    l0_wiring_ref=lab["wiring"],
    l0_hw_ref=lab["hardware"],
    l0_safety_ref=lab["safety"],
)
print("实验已定义:", spec.spec_id)

# 3. 提交运行（使用虚拟后端）
from qxtrl.rs import RuntimeService, RunRequest
import tempfile

tmp = tempfile.mkdtemp(prefix="qxtrl_run_")
runtime = RuntimeService(result_base_dir=tmp)

result = runtime.run_once(RunRequest(
    request_id="my-first-time-rabi",
    experiment_spec=spec,
    backend_id="backend.virtual.rabi_mvp",
    mode="virtual",
))

print("运行完成！")
print("final_state:", result.final_state)
print("manifest_ref:", result.manifest_ref)

# 4. 查看结果 + 回放（L5 + L7）
from qxtrl.ds import FileResultStore
from qxtrl.trh import replay_manifest, ReplayRequest

store = FileResultStore(base_dir=tmp)
manifest = store.get_manifest(result.run_id)
print("Manifest 输出组:", list(manifest.output_refs.keys()))

# 回放审查
for check in [True, False]:
    r = replay_manifest(ReplayRequest(
        replay_id=f"review-{check}",
        run_id_or_manifest_ref=result.manifest_ref,
        result_dir=tmp,
        mode="inspect",
        require_hash_check=check,
    ))
    print(f"Replay (require_hash_check={check}): {r.final_state}")
```

---

## 5. 使用简易看板进行交互式探索

```python
from qxtrl.examples.simple_dashboard import SimpleLabDashboard

db = SimpleLabDashboard()

# 录入新芯片
db.load_lab("q001")

# 提交实验
db.submit_time_rabi(qubit_id="q001", amp=0.1)

# 展示完整看板（拓扑 + 进度 + 可视化 + 回放）
db.show_results_board()
```

---

## 6. 常用命令速查

```bash
# 运行看板（最推荐）
PYTHONPATH=. python -m qxtrl.examples.simple_dashboard

# 运行完整彩排脚本（更详细的故事版）
PYTHONPATH=. python -m qxtrl.examples.rehearse_time_rabi_q001

# 运行旧的 amplitude Rabi demo
PYTHONPATH=. python -m qxtrl.demo_rabi_l1

# 查看某个 manifest
PYTHONPATH=. python -m qxtrl.oi.cli manifest show <run_id> --result-dir /tmp/xxx
```

---

## 7. 下一步建议

- 修改 `durations` 或 `fixed_amplitude` 自己实验
- 尝试用不同 `qubit_id`（看板会自动生成对应连线）
- 学习如何在真实硬件上替换 `backend.virtual.rabi_mvp`
- 阅读 `docs/planning/QXtrl_MVP最薄垂直切片定义.md` 了解整体架构
- 探索 `qxtrl/oi/` 下的 SDK 和 CLI

---

## 常见问题

**Q: 运行时报错 `No module named 'qxtrl'`**  
A: 确保你在项目根目录，并使用了 `PYTHONPATH=.`

**Q: 想保存结果到固定目录？**  
A: `result_dir="/tmp/my_chip_experiments"` 传给 `RuntimeService` 或 `SimpleLabDashboard`

**Q: 如何看到更详细的中间数据？**  
A: `FileResultStore` 可以直接读 `raw/iq.json`、`analysis/analysis.json` 等。

---

**恭喜！** 你已经成功跑通了一次完整的量子芯片表征实验流程（从录入到回放）。

有任何问题欢迎继续提问，我们可以继续完善看板、增加更多实验类型（S21、Ramsey 等），或者帮你把这个流程接入真实硬件。 

祝实验顺利！ 🚀