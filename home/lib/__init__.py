"""说明
qcompile: 编译qlisp线路
sample_waveform: 波形采样/失真计算
stdlib: 门定义
arch: 以rcp为例, code模块对应编译生成的指令处理, data模块对应数据处理
"""


from qlispc import Signal, get_arch
from qlispc.kernel_utils import qcompile, sample_waveform
from qlispc.namespace import DictDriver

from .arch import baqis2, rcp
from .gates import stdlib
