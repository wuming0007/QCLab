"""
简易看板 (Simple Dashboard / Kanban) for QXtrl MVP Rehearsal

展示：
- 当前系统设置 (L0: 芯片拓扑、连线、硬件、qubit 参数)
- 提交测试任务 (time rabi on q001)
- 任务流 / 进度 (stages)
- 返回数据可视化 (表格 + ASCII 图)
- 结果回看 (manifest + replay inspect)

运行方式：
  PYTHONPATH=. python -m qxtrl.examples.simple_dashboard

这是一个纯文本的 "看板"，适合在终端演练使用。
后续可替换为 web / PySide6 版本。
"""

import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from qxtrl.cc.examples import make_rabi_lab
from qxtrl.el import create_time_rabi_experiment_spec
from qxtrl.rs import RuntimeService, RunRequest
from qxtrl.ds import FileResultStore
from qxtrl.trh import replay_manifest, ReplayRequest


class SimpleLabDashboard:
    """简易看板类"""

    def __init__(self, result_dir: Optional[str] = None):
        self.result_dir = result_dir or tempfile.mkdtemp(prefix="qxtrl_dashboard_")
        self.current_lab: Optional[Dict[str, Any]] = None
        self.last_result: Optional[Any] = None
        self.last_manifest: Optional[Any] = None
        self.current_run_id: Optional[str] = None

    # ===================== L0 设置展示 =====================
    def show_lab_board(self):
        """展示当前系统设置看板"""
        print("\n" + "=" * 70)
        print("【当前系统设置看板 - L0 Core Contracts】")
        print("=" * 70)

        if not self.current_lab:
            print("  (尚未录入芯片信息，请先 '录入' 或 load_lab)")
            return

        lab = self.current_lab
        chip = lab["chip"]
        wiring = lab["wiring"]
        hw = lab["hardware"]

        print(f"\n[芯片拓扑]")
        print(f"  Chip ID : {chip.identity.id}")
        print(f"  Qubits  : {[q.element_id for q in chip.qubits]}")
        for q in chip.qubits:
            print(f"    - {q.element_id}: freq={q.frequency}")

        print(f"\n[连线结构]")
        for edge in wiring.edges:
            print(f"  {edge.line_id} ({edge.role})")
            ep = edge.endpoints
            if hasattr(ep, "chip_element"):
                print(f"    -> chip_element: {ep.chip_element}")
            if hasattr(ep, "hardware_channels"):
                print(f"    -> hardware_channels: {ep.hardware_channels}")

        print(f"\n[测控硬件信息]")
        print(f"  Station : {hw.identity.id}")
        print(f"  Devices : {[d.device_id for d in hw.devices]}")
        print(f"  Channels: {[c.channel_id for c in hw.channels]}")

        print(f"\n[Qubit / 读取基本参数 (示例)]")
        print(f"  目标比特: {lab.get('target_qubit')}")
        print(f"  Drive   : {lab.get('drive_line')}")
        print(f"  Readout : {lab.get('readout_line')}")

        print("\n(这些信息模拟了 '新芯片到场后' 的录入操作)")

    def load_lab(self, qubit_id: str = "q001"):
        """模拟 '录入' 操作"""
        print(f"\n>>> 正在录入芯片设置 for {qubit_id} ...")
        self.current_lab = make_rabi_lab(qubit_id=qubit_id, freq_hz=5.234e9)
        print("录入完成！")
        self.show_lab_board()

    # ===================== 任务提交 + 进度 =====================
    def submit_time_rabi(self, qubit_id: str = "q001", amp: float = 0.1, durations: Optional[List[float]] = None):
        """提交 time rabi 任务，并展示流程"""
        if not self.current_lab:
            print("请先 load_lab() 录入设置")
            return

        if durations is None:
            durations = [10.0, 20.0, 30.0, 40.0, 50.0, 80.0, 120.0]

        lab = self.current_lab
        print(f"\n>>> 提交任务: Time Rabi on {qubit_id} (amp={amp})")
        print(f"    扫描 durations (ns): {durations}")

        spec = create_time_rabi_experiment_spec(
            qubit_id=qubit_id,
            drive_line_id=lab["drive_line"],
            readout_line_id=lab["readout_line"],
            durations=durations,
            fixed_amplitude=amp,
            l0_chip_model_ref=lab["chip"],
            l0_wiring_ref=lab["wiring"],
            l0_hw_ref=lab["hardware"],
            l0_safety_ref=lab["safety"],
        )

        # 模拟任务流看板
        stages = [
            ("L1 ExperimentSpec", "定义实验意图 (time rabi + 固定幅度 + duration扫描)"),
            ("L2 Compile", "生成 PulseIR + CompiledBundle"),
            ("L3 Execution Backend", "调用 VirtualQPU (TRH)"),
            ("L4 Runtime Scheduler", "全生命周期调度 + 资源 + 事件"),
            ("L6 Analysis", "初步分析 (产生候选)"),
            ("L5 Data & State", "持久化 RunManifest + datasets"),
        ]

        print("\n【任务流 / 进度看板】")
        for i, (stage, desc) in enumerate(stages, 1):
            print(f"  [{i}/6] {stage:<25} ... {desc}")

        runtime = RuntimeService(result_base_dir=self.result_dir)
        req = RunRequest(
            request_id=f"dashboard.{spec.spec_id}",
            experiment_spec=spec,
            backend_id="backend.virtual.rabi_mvp",
            mode="virtual",
        )

        print("\n>>> 正在执行 ...")
        result = runtime.run_once(req)
        self.last_result = result
        self.current_run_id = result.run_id

        print(f"\n任务完成: final_state = {result.final_state}")
        print(f"manifest_ref = {result.manifest_ref}")

        # 加载 manifest 用于后续查看
        try:
            store = FileResultStore(base_dir=self.result_dir)
            self.last_manifest = store.get_manifest(result.run_id)
        except Exception as e:
            print(f"加载 manifest 时出错: {e}")

    # ===================== 结果可视化 =====================
    def show_results_board(self):
        """展示结果看板 + 可视化"""
        print("\n" + "=" * 70)
        print("【结果看板 + 数据可视化】")
        print("=" * 70)

        if not self.last_result:
            print("还没有提交任务")
            return

        res = self.last_result
        print(f"\nRun ID      : {res.run_id}")
        print(f"final_state : {res.final_state}")
        print(f"manifest    : {res.manifest_ref}")

        if self.last_manifest:
            m = self.last_manifest
            print(f"\n[RunManifest 摘要]")
            print(f"  experiment.spec_id : {m.experiment.spec_id}")
            print(f"  compile.bundle_id  : {m.compile.bundle_id if m.compile else None}")
            print(f"  output groups      : {list(m.output_refs.keys()) if m.output_refs else []}")

        # 尝试拿 raw 数据可视化
        try:
            store = FileResultStore(base_dir=self.result_dir)
            # 直接读 raw 数据集 (简化)
            # 实际应该通过 result refs，这里简化从运行结果拿
            data = getattr(res, "backend_result", None)
            if data and hasattr(data, "data"):
                iq_list = data.data.get("iq", [])
                self._visualize_iq_data(iq_list)
            else:
                # 尝试从 manifest 的 output_refs 找
                if self.last_manifest and "raw" in self.last_manifest.output_refs:
                    # 简化：直接从文件读
                    run_dir = Path(self.result_dir) / res.run_id
                    raw_file = run_dir / "raw" / "iq.json"
                    if raw_file.exists():
                        import json
                        iq_list = json.loads(raw_file.read_text())
                        self._visualize_iq_data(iq_list)
        except Exception as e:
            print(f"可视化数据时出错 (可忽略): {e}")

        # Replay 审查
        if res.manifest_ref:
            print("\n[回放审查 (L7 Replay Inspect)]")
            for require in [True, False]:
                try:
                    rres = replay_manifest(ReplayRequest(
                        replay_id=f"dash-{require}",
                        run_id_or_manifest_ref=res.manifest_ref,
                        result_dir=self.result_dir,
                        mode="inspect",
                        require_hash_check=require,
                    ))
                    print(f"  require_hash_check={require}: {rres.final_state} | {rres.output_summary}")
                except Exception as e:
                    print(f"  replay error: {e}")

    def _visualize_iq_data(self, iq_list: List[dict]):
        """简单的结果可视化"""
        if not iq_list:
            print("  (无 IQ 数据)")
            return

        print("\n[返回数据可视化 - Time Rabi (I vs Duration)]")

        # 取 x 和 I
        x_label = "duration_ns" if "duration_ns" in iq_list[0] else "amp"
        xs = [float(d.get(x_label, d.get("amp", 0))) for d in iq_list]
        is_ = [float(d.get("i", d.get("I", 0))) for d in iq_list]

        # 表格
        print(f"\n  {x_label:>12} | {'I':>8} | {'Q':>8}")
        print("  " + "-" * 34)
        for d in iq_list[:7]:  # 最多显示前7点
            x = d.get(x_label, d.get("amp", "?"))
            i = d.get("i", d.get("I", 0))
            q = d.get("q", d.get("Q", 0))
            print(f"  {float(x):>12.1f} | {float(i):>8.4f} | {float(q):>8.4f}")

        if len(iq_list) > 7:
            print("  ... (更多点)")

        # 极简 ASCII 图 (I 值)
        print("\n  ASCII 振荡图 (I 值, 归一化):")
        self._ascii_plot(is_)

    def _ascii_plot(self, values: List[float], width: int = 50, height: int = 8):
        """极简 ASCII 折线图"""
        if not values:
            return
        min_v = min(values)
        max_v = max(values)
        if max_v == min_v:
            print("  (数据平坦)")
            return

        def scale(v):
            return int((v - min_v) / (max_v - min_v) * (height - 1))

        canvas = [[" " for _ in range(width)] for _ in range(height)]

        n = len(values)
        for i in range(n - 1):
            x1 = int(i / (n - 1) * (width - 1))
            x2 = int((i + 1) / (n - 1) * (width - 1))
            y1 = height - 1 - scale(values[i])
            y2 = height - 1 - scale(values[i + 1])

            # 简单画点和线
            canvas[y1][x1] = "*"
            if x2 > x1:
                for x in range(x1 + 1, x2):
                    canvas[y1][x] = "-"
            canvas[y2][x2] = "*"

        for row in canvas:
            print("  " + "".join(row))

    # ===================== 交互入口 =====================
    def run_demo_rehearsal(self):
        """一键运行完整演练故事"""
        print("欢迎使用 QXtrl 简易看板 (MVP Rehearsal)")

        # 1. 录入
        self.load_lab("q001")

        # 2. 提交任务
        self.submit_time_rabi(qubit_id="q001", amp=0.1)

        # 3. 展示结果看板
        self.show_results_board()

        print("\n看板演示结束。")
        print("你可以继续调用 dashboard.load_lab(), submit_time_rabi(), show_results_board() 等方法。")


def main():
    dashboard = SimpleLabDashboard()
    dashboard.run_demo_rehearsal()


if __name__ == "__main__":
    main()
