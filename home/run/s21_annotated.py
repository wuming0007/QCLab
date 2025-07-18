# 导入必要的库
import time  # 用于在 update 函数中打印带时间戳的日志
import numpy as np  # 科学计算库，这里主要用于生成扫描参数数组
from quark.app import Recipe, s  # 从核心应用 'quark.app' 中导入 Recipe 类和 s 对象
                                # Recipe: 用于构建一个完整实验流程的“配方”对象
                                # s: 一个全局单例对象，是用户与后端QuarkServer交互的主要接口，负责登录、提交任务、查询/更新参数等

# ------------------- 步骤 1: 连接到后端服务器 -------------------
# 通过 s 对象登录到 QuarkServer。
# 这一步会建立与硬件控制服务器的连接，后续所有操作都通过 s 对象进行。
s.login()


# ------------------- 步骤 2: 定义量子线路 (Circuit) -------------------
# 这个函数定义了实验中要执行的量子线路。
# 对于 S21 测量，线路非常简单，只包含对每个比特进行测量操作。
def circuit(qubits: list[str], ctx=None) -> list:
    """
    定义一个测量线路。
    
    Args:
        qubits (list[str]): 要操作的量子比特列表，例如 ['Q0', 'Q1']。
        ctx: 上下文参数，可选，此处未使用。

    Returns:
        list: 一个描述量子线路的列表。
              列表中的每个元素是一个元组 (operation, target_qubit)，
              例如 [(('Measure', 0, ), 'Q0'), (('Measure', 1, ), 'Q1')]
              其中 ('Measure', i, ) 定义了操作类型和可能的参数，q 是操作的目标比特。
    """
    # 使用列表推导式为每个传入的量子比特生成一个测量操作。
    # 'Measure' 是操作的名称。
    # i 是一个索引，可以用于区分不同的测量操作或为其分配参数。
    # q 是目标量子比特的名称。
    cc = [(('Measure', i, ), q) for i, q in enumerate(qubits)]
    return cc


# ------------------- 步骤 3: 定义并执行校准实验 (Calibrate) -------------------
# 这是执行 S21 测量的核心函数。
def calibrate(qubits: list[str]) -> list:
    """
    执行 S21 扫描实验。

    Args:
        qubits (list[str]): 希望进行测量的量子比特列表。

    Returns:
        tuple: 返回一个元组，包含实验结果的字典和本次任务的ID。
    """
    # !!! 注意: 下面这行代码将输入的 qubits 列表强制覆盖为 ['Q999']。
    # 这通常是为了进行快速测试或调试，确保实验只在一个虚拟或测试比特上运行。
    # 在实际使用中，应该注释掉这行，使用函数传入的 qubits 列表。
    qubits = [f'Q{i}' for i in [999]]

    # 创建一个 Recipe 实例，命名为 's21'。
    # signal='iq_avg' 指定了我们关心的数据是经过平均的 IQ 值。
    rcp = Recipe('s21', signal='iq_avg')

    # 指定 Recipe 使用的门库和硬件架构。
    # 这告诉编译器去哪里寻找 'Measure' 操作的具体物理实现（即脉冲定义）。
    rcp.lib = 'lib.gates.u3rcp'  # 使用 u3rcp 库
    rcp.arch = 'rcp'             # 使用 rcp 架构

    # 将上面定义的 circuit 函数赋给 Recipe 的 circuit 属性。
    rcp.circuit = circuit

    # --- 设置 Recipe 的参数 ---
    # 将要操作的比特列表传递给 Recipe。
    rcp['qubits'] = tuple(qubits)
    
    # 定义扫描参数：频率。
    # np.linspace(-10, 10, 101) * 1e6 创建了一个从 -10MHz 到 +10MHz，总共 101 个点的频率扫描范围。
    # 这个范围是相对值，将与比特当前的中心频率相加。
    rcp['freq'] = np.linspace(-10, 10, 101) * 1e6
    
    # 下面是其他可能扫描参数的示例，当前被注释掉了。
    # rcp['amp'] = np.linspace(0, 0.05, 21)  # 幅度扫描
    # rcp['state'] = ['0', '1']             # 在不同初态下进行扫描

    # --- 将扫描参数应用到具体的比特和操作上 ---
    for q in qubits:
        # 这是最关键的一步：将频率扫描应用到测量操作上。
        # rcp[f'{q}.Measure.frequency'] 设置了比特 q 的测量频率。
        # s.query(f'{q}.Measure.frequency') 从服务器获取比特 q 当前存储的测量频率（中心频率）。
        # 两者相加，实现了在中心频率附近进行扫描。
        rcp[f'{q}.Measure.frequency'] = rcp['freq'] + s.query(f'{q}.Measure.frequency')
        
        # 其他可能的参数设置，例如幅度
        # rcp[f'gate.Measure.{q}.params.amp'] = rcp['amp']
        # rcp[f'gate.Measure.{q}.default_type'] = 'default'

    # --- 提交任务并等待结果 ---
    # s.submit() 将构建好的 Recipe（通过 rcp.export() 导出为字典格式）提交给服务器执行。
    # block=True: 表示程序会在此处阻塞，直到实验执行完成。
    # preview=['3M1']: 可能用于指定一个实时数据显示的模式或通道。
    # plot=False: 不在服务器端生成静态图。
    s21 = s.submit(rcp.export(), block=True, preview=['3M1'], plot=False)
    
    # 在控制台显示一个进度条，interval=1 表示每秒更新一次。
    s21.bar(interval=1)
    
    # 返回实验结果 (s21.result()) 和任务ID (s21.tid)。
    return s21.result(), s21.tid


# ------------------- 步骤 4: 分析数据 (Analyze) -------------------
# 这个函数用于处理从 calibrate 函数获取的原始数据。
# 在一个真实的 S21 实验中，这里应该包含拟合算法，用于从 IQ 数据中提取谐振腔的中心频率。
def analyze(result: dict, level: str = 'check') -> dict:
    """
    分析实验结果。
    
    Args:
        result (dict): calibrate 函数返回的原始数据。
        level (str): 分析的级别，此处未使用。

    Returns:
        dict: 返回一个包含拟合参数的字典。
    """
    # !!! 注意: 当前这是一个占位符实现。
    # 它没有进行任何实际的拟合，只是返回了一个硬编码的字典。
    # 理想情况下，这里应该调用一个拟合函数，例如洛伦兹拟合，来找到频率最小值点。
    # fitted = fit_lorentzian(result['freq'], result['iq_avg'])
    fitted = {'Q0.param.frequency': 5e9}
    return fitted


# ------------------- 步骤 5: 诊断系统状态 (Diagnose) -------------------
# 这个函数在 analyze 的基础上，对系统状态给出一个更高层次的评估。
def diagnose(result: dict, level: str = 'check', history: list = []) -> dict:
    """
    根据分析结果诊断量子比特的状态。

    Returns:
        dict: 返回一个摘要字典，包含每个比特的状态（好/坏）和测量值。
    """
    # 一个辅助函数，用于生成一个带随机噪声的模拟频率值。
    def f(): return float((4.4 + np.random.randn(1)) * 1e9)

    # !!! 注意: 当前这是一个占位符实现。
    # 它返回一个硬编码的字典，模拟了对多个比特的状态评估。
    # 'red' 可能表示状态异常（例如，拟合失败或参数偏离过远），'green' 表示状态正常。
    # 在自动化流程中，这个摘要将决定下一步的操作（例如，重新校准红色比特，或继续下一个实验）。
    summary = {'Q0': ('red', f()), 'Q1': ('green', f()),
               'Q5': ('green', f()), 'Q8': ('red', f())}
    
    # 其他可能包含在摘要中的信息（当前被注释）:
    # 'adaptive_args': {'Q0': [], 'Q1': []}  # 为下一次自适应扫描提供建议参数
    # 'group': ('Q0', 'Q1', 'Q5', 'Q8')      # 动态分组信息
    return summary


# ------------------- 步骤 6: 更新系统参数 (Update) -------------------
# 这个函数接收 diagnose 的摘要，并将校准后的“好”参数写回到服务器数据库中。
def update(summary: dict):
    """
    根据诊断摘要更新系统参数。
    这是一个占位符函数，目前只打印信息，不执行实际的更新操作。
    """
    # 在一个真实的流程中，这里会遍历 summary 字典。
    # 如果比特的状态是 'green'（正常），则调用 s.update() 将新的、校准后的参数值写回数据库。
    # for t, (status, value) in summary.items():
    #     if status == 'green':
    #         s.update({f'{t}.param.frequency': value})
    
    # 打印一条日志，表示函数被调用，并显示摘要内容。
    print(f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] updated!', summary)
