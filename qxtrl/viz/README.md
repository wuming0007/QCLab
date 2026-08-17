# 芯片二维拓扑图绘制说明

用同一套绘图函数画任意平面量子芯片：圆形是量子比特，方块是耦合器；填充色由**度量关键字**绑定。Google Willow 只是一个内置示例，换几何和数据表即可画自己的芯片。

代码入口：`qxtrl/viz/`。图注与 Willow 公开拓扑说明见 `WILLOW_CAPTION`。

依赖：`matplotlib`、`numpy`（`pip install '.[viz]'` 或使用已有科学计算环境）。仓库根目录下设置 `PYTHONPATH=.`。

---

## 1. 30 秒：复现 Willow 示例

```bash
PYTHONPATH=. python3 -m qxtrl.viz
PYTHONPATH=. python3 -m qxtrl.viz --qubit-metric t2 --coupler-metric cz_error
PYTHONPATH=. python3 -m qxtrl.viz --legend-zh --show-labels grid
```

默认写出 `figures/chip_topology/willow105.{pdf,svg,png}`。

Python 等价写法：

```python
from qxtrl.viz import plot_chip_topology, save_topology_figure, willow105_layout

layout = willow105_layout(seed=0)
fig = plot_chip_topology(layout, qubit_metric="t1", coupler_metric="cz_fidelity")
save_topology_figure(fig.fig, "figures/chip_topology/willow105")
```

Willow 的网格来自公开 Cirq `willow_pink` / Willow105。逐点颜色是按 Chip-1 QEC 公开均值生成的**示意样本**，不是 Google 实测地图，不能用于控制或性能声称。实验室数据请用下面第 3 节注入。

---

## 2. 定义拓扑：三种方式，选一种

绘图只认 `ChipLayout`：一组带平面坐标的比特，加上连接它们的耦合器。用下面三种构造器之一即可。

### 2.1 矩形方格（最快）

近邻方格，正交耦合，适合规则 2D lattice 或小规模演示。

```python
from qxtrl.viz import ChipLayout, plot_chip_topology, save_topology_figure

layout = ChipLayout.rectangular_grid(4, 5, name="lab-4x5")
fig = plot_chip_topology(layout, qubit_metric=None, coupler_metric=None)
save_topology_figure(fig.fig, "figures/chip_topology/lab_4x5")
```

比特 ID 按行优先编号：`q000`、`q001`、…。耦合器 ID 为 `tc_<id小>_<id大>`，例如 `tc_q000_q001`。

`qubit_metric=None` 且 `coupler_metric=None` 时只画几何，不着色。

### 2.2 ASCII 占位图（不规则方格、缺角、十字）

与 Cirq 设备图相同：字母或数字是比特，`-`、`.`、空格是空位。默认只连接上下左右近邻（`connect="4"`）；`connect="8"` 会额外连对角。

```python
layout = ChipLayout.from_ascii(
    """
    -X-
    XXX
    -X-
    """,
    name="plus-5",
)
```

再如缺角的近邻方格（Sycamore / Willow 一类）：

```python
layout = ChipLayout.from_ascii(
    """
    --XXXX--
    -XXXXXX-
    XXXXXXXX
    -XXXXXX-
    --XXXX--
    """,
    name="truncated-square",
)
```

约定：

| 规则 | 含义 |
| --- | --- |
| 第 0 行画在图的**上方**（`y = -row`） | 与 Cirq `GridQubit(row, col)` 一致 |
| 比特 ID | 行优先 `q000`、`q001`、… |
| 空位 | `-` `.` 空格，不占 ID |
| 耦合 | 默认四近邻；只在两个占位都存在时生成 |

画自己的芯片时，先用纸或表格画出 0/1 占位，再写成 ASCII，比手写坐标更快。

### 2.3 显式坐标（heavy-hex、环形、任意平面图）

不是方格、或耦合不是四近邻时，直接给每个比特的平面坐标 `(x, y)`，再列出真实存在的边。耦合器默认画在两端点中点。

**(x, y) 不是归一化到 [0, 1]。** 它们是绘图平面上的任意实数，单位自定（格子步长、微米、毫米都可以）。绘图函数只看**相对位置**：

- 近邻之间的距离决定圆和方块的大小（取耦合键长的中位数）。
- 坐标整体平移（例如全体 `+100`）或整体缩放（例如全体 `×1e-6`）不改变拓扑形状。
- 坐标轴范围由数据自动框定，不必预先压到 `[0, 1]`。
- 建议让**最近邻间距约为 1**（或某个固定常数），这样和 `from_ascii` / 矩形网格的约定一致，也最好调。

本仓库的方格约定（`from_ascii` 与内置 Willow 都用这一套）：

| 量 | 约定 |
| --- | --- |
| `x` | 列号 `col`，向右增大 |
| `y` | `-row`，第 0 行在图的**上方** |
| 最近邻 | 水平或竖直相距 **1** |
| 比特 ID | 行优先扫描占位格：`q000` … `q104`（105 个比特，**没有 `q105`**） |

用显式坐标复现 Willow 时，不要假设 `q000 = (0, 0)`。第一行是 `------XXX------`，第一个占位在 `col=6`，所以内置布局是：

| 比特 | `(x, y)` = `(col, -row)` | 含义 |
| --- | --- | --- |
| `q000` | `(6, 0)` | 第 0 行、第 6 列，图的顶部偏中 |
| `q104`（最后一个） | `(8, -12)` | 第 12 行、第 8 列，图的底部偏中 |

若你坚持把 `q000` 平移到原点，只需全体减去 `(6, 0)`，则 `q104` 变为 `(2, -12)`。形状不变，只是原点换了。

```python
from qxtrl.viz import ChipLayout, CouplerSite, QubitSite, plot_chip_topology, willow105_layout

# 查看内置 Willow 的真实坐标，而不是手猜：
w = willow105_layout(with_illustrative_metrics=False)
print(w.qubits[0].qubit_id, w.qubits[0].x, w.qubits[0].y)    # q000 6.0 0.0
print(w.qubits[-1].qubit_id, w.qubits[-1].x, w.qubits[-1].y)  # q104 8.0 -12.0

# 任意平面图：单位自定，这里用边长 1 的正三角形
qubits = [
    QubitSite("q000", x=0.0, y=0.0),
    QubitSite("q001", x=1.0, y=0.0),
    QubitSite("q002", x=0.5, y=0.87),
]
couplers = [
    CouplerSite("tc_q000_q001", "q000", "q001"),
    CouplerSite("tc_q000_q002", "q000", "q002"),
    CouplerSite("tc_q001_q002", "q001", "q002"),
]
layout = ChipLayout(name="triangle", qubits=qubits, couplers=couplers)
fig = plot_chip_topology(layout, qubit_metric=None, coupler_metric=None)
```

IBM heavy-hex 一类：每个比特给 `(x, y)`，耦合器只列入真实存在的边，不要用 `from_ascii(..., connect="8")` 去“猜”连接。

若耦合器在芯片上并不位于键中点，可在 `CouplerSite` 上显式设 `x`、`y`。


---

## 3. 写入实测（或仿真）数据

几何和颜色是分开的。先构造 `ChipLayout`，再按关键字写入字典。

```python
layout.set_qubit_metrics("t1", {
    "q000": 72.4,
    "q001": 65.1,
    "q002": 80.0,
})
layout.set_coupler_metrics("cz_fidelity", {
    "tc_q000_q001": 0.995,
    "q001__q002": 0.991,   # 也可用两端点，顺序无关
})

fig = plot_chip_topology(
    layout,
    qubit_metric="t1",
    coupler_metric="cz_fidelity",
)
```

从 CSV 读入时，列名用同一套关键字即可：

```python
import csv

t1 = {}
with open("qubit_metrics.csv", newline="") as f:
    for row in csv.DictReader(f):
        t1[row["qubit_id"]] = float(row["t1_us"])
layout.set_qubit_metrics("t1", t1)
```

缺测的比特或耦合器会画成浅灰，不进入 colorbar。关键字大小写不敏感（`T1` 与 `t1` 相同）。

Willow 若只要公开网格、不要示意颜色：

```python
layout = willow105_layout(with_illustrative_metrics=False)
layout.set_qubit_metrics("t1", measured_t1)
layout.set_coupler_metrics("cz_fidelity", measured_f)
```

---

## 4. 度量关键字

`plot_chip_topology(..., qubit_metric="...", coupler_metric="...")` 只是从每个位点的 `metrics` 字典里取同名键。下表是内置 colorbar 标签；未列出的键也可以用，标签会回退为键名。

| 关键字 | 通常画在 | Colorbar |
| --- | --- | --- |
| `t1` | 比特（圆） | \(T_1\) (µs) |
| `t2` / `t2_star` / `t2_echo` | 比特 | \(T_2\) / \(T_2^*\) / \(T_{2E}\) |
| `frequency` / `freq` | 比特 | \(f_{01}\) (GHz) |
| `anharmonicity` | 比特 | \(\alpha\) (MHz) |
| `readout_fidelity` / `readout_error` | 比特 | \(F_{\mathrm{RO}}\) / \(\varepsilon_{\mathrm{RO}}\) |
| `cz_fidelity` / `cz_error` | 耦合器（方） | \(F_{\mathrm{CZ}}\) / \(\varepsilon_{\mathrm{CZ}}\) |
| `iswap_fidelity` / `iswap_error` | 耦合器 | \(F_{\mathrm{iSWAP}}\) |
| `gate_fidelity` / `two_qubit_fidelity` / `gate_error` | 耦合器 | \(F_{\mathrm{2Q}}\) |

保真度（0–1）自动显示为百分数；误差关键字用小数。自定义标签：

```python
plot_chip_topology(
    layout,
    qubit_metric="t1",
    coupler_metric="my_edge_snr",
    qubit_label=r"$T_1$ ($\mu$s)",
    coupler_label="edge SNR",
    qubit_cmap="YlGnBu",
    coupler_cmap="YlOrRd",
    qubit_vmin=40,
    qubit_vmax=100,
)
```

---

## 5. 常用绘图选项

```python
fig = plot_chip_topology(
    layout,
    qubit_metric="t1",
    coupler_metric="cz_fidelity",
    preset="journal",          # 或 "slide"
    show_labels="none",        # "id" | "grid"
    legend_labels=("量子比特", "耦合器"),
    coupler_shape="square",    # "rect" 则沿键拉长
    show_bonds=True,
    show_substrate=True,
    title=None,                # 论文图题通常放图注，不画在图内
)
save_topology_figure(
    fig.fig,
    "figures/chip_topology/my_chip",
    formats=("pdf", "svg", "png"),
    dpi=600,
)
```

| 选项 | 作用 |
| --- | --- |
| `preset="journal"` | Nature 双栏宽（183 mm）、8 pt、PDF/SVG 可编辑字体 |
| `preset="slide"` | 更大字号与画幅 |
| `show_labels="id"` | 圆内写 `q000` |
| `show_labels="grid"` | 圆内写 `row,col`（ASCII/方格布局才有） |
| `coupler_shape="rect"` | 耦合器画成沿键的短矩形，更接近实物版图 |
| `legend_labels` | 左上角形例文字 |
| `qubit_radius` / `coupler_size` | 覆盖默认相对格子间距的尺寸 |

论文图注不要写进图内。Willow 示例可用：

```python
from qxtrl.viz import WILLOW_CAPTION
print(WILLOW_CAPTION)
```

---

## 6. 推荐工作流（新芯片）

1. 判断拓扑类型：规则方格 → `rectangular_grid`；有缺位的方格 → `from_ascii`；heavy-hex / 任意图 → 显式 `QubitSite` + `CouplerSite`。
2. 先 `qubit_metric=None, coupler_metric=None` 出一张纯几何图，核对比特数、耦合数、平均度。
3. 用实验室表 `set_qubit_metrics` / `set_coupler_metrics` 写入 `t1`、`cz_fidelity` 等。
4. `preset="journal"` 导出 PDF（投稿）和 SVG（后期改字）。PNG 仅作预览。
5. 图注写清数据来源；公开示例与实测不要混称。

检查几何是否合理：

```python
print(len(layout.qubits), len(layout.couplers), round(layout.average_degree(), 2))
```

---

## 7. 文件与命令

| 路径 | 内容 |
| --- | --- |
| `qxtrl/viz/topology.py` | `ChipLayout` 与 `plot_chip_topology` |
| `qxtrl/viz/willow.py` | 公开 Willow105 占位图 |
| `qxtrl/examples/plot_willow_topology.py` | 命令行示例 |
| `figures/chip_topology/` | 导出图 |
| `qxtrl/viz/tests/test_topology.py` | 几何与关键字测试 |

```bash
PYTHONPATH=. python3 -m pytest qxtrl/viz/tests/ -q
PYTHONPATH=. python3 -m qxtrl.viz --help
```

本模块只负责示意图，不写入 L0 `ChipModel`，也不把图上的示意颜色当作可执行校准数据。
