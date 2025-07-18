import numpy as np


def step_function(x, width):
    # 阶跃函数
    y = x < width  # numpy数组中的每个元素都与width比较大小，得到一个布尔型numpy数组
    return y.astype(np.int)  # astype()方法将numpy数组的布尔型转换为int型

