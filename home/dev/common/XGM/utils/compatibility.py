# -*- coding: utf-8 -*-
"""
向后兼容性工具
"""


class BackwardCompatibilityMixin:
    """向后兼容性混入类"""

    def opencard(self, slot):
        """向后兼容：打开指定槽位的板卡"""
        return self.open_card(slot)

    def closecard(self, slot):
        """向后兼容：关闭指定槽位的板卡"""
        return self.close_card(slot)

    def readReg(self, addr, slot):
        """向后兼容：读取指定地址和槽位的寄存器值"""
        return self.read_reg(addr, slot)

    def writeReg(self, addr, data, slot=''):
        """向后兼容：写入指定地址和槽位的寄存器值"""
        return self.write_reg(addr, data, slot)
