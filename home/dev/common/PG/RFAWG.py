#   FileName:mf_rf_awg.py
#   Author:
#   E-mail:
#   All right reserved.
#   Modified: 2021.04.29
#   Description:The class of RF AWG
# import os
# import socket
# import time

# import numpy as np

from typing import no_type_check
from . import AWGboard
# import matplotlib.pyplot as plt
import struct
# from itertools import repeat


class RFAWG(AWGboard.AWGBoard):
    """
    RF AWG工作在混频模式，本振频率最高能到6GHz
    中频频率采样率为2.5GHz，用户根据自身需求进行频率规划。

    """
    def __init__(self):
        super().__init__(dev_type='RF_AWG')
        # Initialize core AWG parameters
        self.awg_mode = 0  # 0 IQ MIXER mode, 1 DAC mode(do not suport)
        self.channel_count = 4
        self.frequency = 2.5e9
        self.sample_per_clock = 8
        self.isTrigSource = 0
        self.wave_is_unsigned = False
        self.mark_is_in_wave = False

    def Write_Reg(self, bank, addr, data):
        """
        :param bank: 寄存器对象所属的BANK（设备或模块），4字节
        :param addr: 偏移地址，4字节
        :param data: 待写入数据，4字节
        :return: 4字节，写入是否成功，此处的成功是指TCP/IP协议的成功，也可以等效为数据写入成功

        :notes::

            这条命令下，AWG对象返回8字节数据，4字节表示状态，4字节表示数据

        """
        # if bank == 0: ## write cpu
        #    self.write_regs(0, [[data,addr]])
        #    return 0
        assert bank in [1, 2, 4, 5]
        if bank == 1:  # write dac 1 spi
            self.write_spi_reg(0, addr, data)
            return 0

        if bank == 2:  # write dac 2 spi
            self.write_spi_reg(2, addr, data)
            return 0

        if bank == 4:  # write awg 1 reg
            self.write_regs([[self.reg_id1, addr, data]])
            return 0

        if bank == 5:  # write awg 2 reg
            self.write_regs([[self.reg_id2, addr, data]])
            return 0

    def Read_Reg(self, bank, addr, data=0):
        """
        :param bank: 寄存器对象所属的BANK（设备或模块），4字节
        :param addr: 偏移地址，4字节
        :param data: 待写入数据，4字节
        :return: 4字节，读取是否成功，如果成功，返回读取的数据，否则，返回错误状态

        """
        # if bank == 0: ## write cpu
        #    return self.read_regs(0, [[data,addr]])[0]
        assert bank in [1, 2, 4, 5]
        if bank == 1:  # write dac 1 spi
            return self.read_spi_reg(0, addr, data)

        if bank == 2:  # write dac 2 spi
            return self.read_spi_reg(2, addr, data)

        if bank == 4:  # write awg 1 reg
            _ret = self.read_regs([[self.reg_id1, addr, 0]])
            return _ret[-1]

        if bank == 5:  # write awg 2 reg
            _ret = self.read_regs([[self.reg_id2, addr, 0]])
            return _ret[-1]

    def SetMarkMode(self, mark_is_in_wave=None):
        """
        :param self: AWG对象
        :param mark_is_in_wave: mark输出模式，不支持
        """

        self.mark_is_in_wave = False
        for channel in range(1, 5):
            self._commit_para(channel)

    def Start(self, channel):
        """
        :param self: AWG对象
        :param channel: 通道输出使能[12, 34] 12时同时使能1、2通道，34时同时使能3、4通道
        :return: None，网络通信失败表示命令设置失败
        :notes::
        """

        assert channel in [1, 2, 3, 4, 12, 34]
        _channel = 0x03
        _bank = self.bank_dic['awg'][0] if channel in [1, 2, 12] else self.bank_dic['awg'][2]
        self.Write_Reg(_bank, self.board_def.REG_CTRL_REG, _channel)

    def Stop(self, channel):
        """
        :param self: AWG对象
        :param channel: 通道输出禁止[1,2,3,4]
        :return: None，网络通信失败表示命令设置失败
        :notes::
        """
        assert channel in [1, 2, 3, 4, 12, 34]
        _channel = 0x30
        _bank = self.bank_dic['awg'][0] if channel in [1, 2, 12] else self.bank_dic['awg'][2]
        self.Write_Reg(_bank, self.board_def.REG_CTRL_REG, _channel)

    @staticmethod
    def _channel_check(channel):
        """
        :param channel: channel to be checked
        :return:
        """
        assert channel in [1, 2, 3, 4]

    def _SetDACMaxVolt(self, channel, volt):
        """

        该函数用于设置芯片的最大输出电压

        :param channel: AWG 通道（1，2，3，4）
        :param volt: 最大电压值
        :return:
        :notes::
            满电流值计算公式：
            IOUTFS = 32 mA × (ANA_FULL_SCALE_CURRENT[9:0]/1023) + 8 mA
        """
        assert volt <= 1.99
        assert volt >= 0.41
        cur = volt / 0.05
        code = (cur - 8) * 1023 / 32
        code = int(code) & 0x3FF
        self._SetDACFullScale(channel, code)

    def _SetDACFullScale(self, channel, data):
        """

        该函数根据输入的码值写入芯片

        :param self: AWG对象
        :param channel: AWG 通道 [1,2,3,4]
        :param data: 增益值，该值是10位无符号的增益数据
        :return:

        """
        data = 1023
        
        self._channel_check(channel)
        _bank = self.bank_dic['dac'][channel - 1]
        print(f'bank {_bank} set dac gain: ch {channel}, gain {data}')
        self.Write_Reg(_bank, 0x42, data & 0xFF)  # 写入满电流值低字节
        self.Write_Reg(_bank, 0x41, (data >> 8) & 0x03)  # 写入满电流值高字节

    def SetOffsetVolt(self, channel, offset_volt):
        """

        设置某个通道的偏置电压，该功能对当前通道的波形做偏置设置
        由于是通过DA码值来实现的，因此会消耗DA的有效码值范围

        :param self: AWG对象
        :param channel: 通道值（1，2，3，4）
        :param offset_volt: 对应的偏置电压值
        :return: None，网络通信失败表示命令设置失败
        """
        self.log.warning('RF AWG do not support offset volt setting')
        return 0

    def _SetCalibratedOffsetCode(self, channel, offset_code):
        """

        该函数设置的偏置值用于校准仪器在默认连接时的0电平码值

        :param channel: AWG通道[1，2，3，4]
        :param offset_code: 偏置码值
        :return:
        """
        self.log.warning('RF AWG do not support offset volt setting')
        return 0

    def _SetDacOffset(self, channel, offset_code):
        """

        :param self: AWG对象
        :param channel: 通道值（1，2，3，4）
        :param offset_code: 对应的DA通道的offset值，精度到1个LSB
        :return: None，网络通信失败表示命令设置失败
        """
        self.log.warning('RF AWG do not support offset volt setting')
        return 0

    @staticmethod
    def _get_volt(value):
        """
        返回满电流码值对应的电压值
        :param value: 满电流码值
        :return: 电压值
        """
        code = value & 0x3FF
        volts = (32*(code/1023)+8) * 0.05
        return volts

    def check_awg_status(self):
        """[check if dac bring up correctly]
        """
        d = self.read_spi_reg(0, 0x473)
        one_cnt = 0
        for i in range(8):
            one_cnt += (d >> i) & 0x01
        assert one_cnt >= 6, 'dac 1 status check failed'
        d = self.read_spi_reg(2, 0x473)
        one_cnt = 0
        for i in range(8):
            one_cnt += (d >> i) & 0x01
        assert one_cnt >= 6, 'dac 2 status check failed'

    def InitBoard(self):
        """
        初始化AWG，该命令在AWG状态异常时使用,使AWG回到初始状态，并停止输出

        :param self:
        :return:
        """

        self.check_awg_status()
        self._load_init_para()
        self.Stop(12)
        self.Stop(34)
        for channel in range(self.channel_count):
            self._commit_para(channel + 1)
            self._SetDACMaxVolt(channel + 1, self.voltrange[channel] * self.diffampgain[channel])

    def set_mode(self, chip, decode_mode=0, band_sel=0, nco_only=False):
        """[RF AWG工作模式设置]

        Args:
            decode_mode (int, optional): [0:直接输出, 1:混频输出]. Defaults to 0.
            band_sel (int, optional): [0:选择混频后的正边带，1:选择混频后的负边带]. Defaults to 1.
            nco_only (bool, optional): [前提decode_mode=1]
                     [True:仅使能NCO, False:数据接口与NCO一起]. Defaults to False.
        """        
        assert chip in [1, 2]
        if nco_only:
            self.Write_Reg(chip, 0x14E, 0x7F)  # DC test data.
            self.Write_Reg(chip, 0x14F, 0xFF)  # DC test data.
            self.Write_Reg(chip, 0x150, 0x02)  # DC test mode enable.
        else:
            self.Write_Reg(chip, 0x14E, 0x00)  # DC test data.
            self.Write_Reg(chip, 0x14F, 0x00)  # DC test data.
            self.Write_Reg(chip, 0x150, 0x00)  # DC test mode enable.
        
        if decode_mode == 1:
            self.Write_Reg(chip, 0x152, 1)  # Mix-Mode (second Nyquist).
            reg = 0x44 if band_sel == 0 else 0x46
            self.Write_Reg(chip, 0x111, reg)
        else:
            self.Write_Reg(chip, 0x152, 0)  # Mix-Mode (second Nyquist).
            self.Write_Reg(chip, 0x111, 0)

    def gen_modulus_reg(self, int_in):
        b_data = struct.pack('Q', int_in)
        # print(b_data)
        regs = struct.unpack('6B', b_data[0:6])
        # print(regs)
        return regs

    def gen_modulus(self, freq):
        '''频率计算
        freq：频率， 单位Hz
        '''
        f_carrier = freq
        f_dac = 5e9
        X = int(f_carrier/f_dac*(1 << 48))
        A_B = f_carrier/f_dac*(1 << 48) - X
        B = int(10**(len(str(A_B))-2))
        A = int(A_B*B)
        # print(hex(X), A_B, A, B)

        ftw = self.gen_modulus_reg(X)
        ACC_MODULUS = self.gen_modulus_reg(B)
        ACC_DELTA = self.gen_modulus_reg(A)
        reg_list = []
        for i in range(6):
            reg_list.append([0x114+i, ftw[i]])
        for i in range(6):
            reg_list.append([0x124+i, ACC_MODULUS[i]])
        for i in range(6):
            reg_list.append([0x12A+i, ACC_DELTA[i]])
        return reg_list

    def set_nco_freq(self, chip, freq):
        """[设置DAC芯片的NCO频率]

        Args:
            chip ([int]): [1:芯片1， 2:芯片2]
            freq ([float]): [NCO频率，单位：Hz]
        """
        reg_list = self.gen_modulus(freq)
        for reg in reg_list:
            self.Write_Reg(chip, reg[0], reg[1])
        self.Write_Reg(chip, 0x113, 0x00)
        self.Write_Reg(chip, 0x113, 0x01)

    def sideband_select(self, chip, high_low):
        """[混频后的边带选择]

        Args:
            chip ([int]): [1:芯片1， 2:芯片2]
            high_low ([int]): [边带选择，0:正边带，1：负边带]]
        """
        reg = self.Read_Reg(chip, 0x111) & 0xFD
        self.Write_Reg(chip, 0x111, reg | (high_low << 1))

    def convert_one2two(self, wave):
        """[将一个波形数据映射到两个通道]
        直接输出模式，NCO禁止，通道波形需要分配到两个通道
        I: 0, 1, 4, 5, ...
        Q: 2, 3, 6, 7, ...

        注意此时的DAC需要处于NRZ，无NCO的直接输出模式

        Args:
            wave ([np.arrary]): [待转换波形数据]

        Returns:
            [np.arrary]: [转换后的通道1，通道2数据]
        """        
        w1 = wave.reshape((len(wave) >> 1, 2))
        w2 = w1[::2]
        w3 = w1[1::2]
        return w2.reshape((1, len(w2)*2))[0], w3.reshape((1, len(w3)*2))[0]

    def conv_int(self, d_in):
        d_in.extend([0, 0])
        # print(d_in)
        s = struct.pack('8B', *d_in)
        s1 = struct.unpack('Q', s)
        return s1[0]

    def _get_nco_freq(self, chip):
        X_list = []
        B_list = []
        A_list = []
        for i in range(6):
            X_list.append(self.Read_Reg(chip, 0x114+i))
        for i in range(6):
            B_list.append(self.Read_Reg(chip, 0x124+i))
        for i in range(6):
            A_list.append(self.Read_Reg(chip, 0x12A+i))
        X = self.conv_int(X_list)
        A = self.conv_int(A_list)
        B = self.conv_int(B_list)
        freq = round((X+(A/B))*5e9/(1 << 48), 3)
        print(f'NCO frequency is {freq:,} Hz')

    def _get_work_mode(self, chip):
        reg = self.Read_Reg(chip, 0x150) & 0x02
        print(f'chip:{chip}, 仅使能NCO') if reg == 0x02 else None
        if reg == 0:
            reg = self.Read_Reg(chip, 0x152) & 0x03
            dec_mode = f'chip:{chip}, NRZ-Mode' if reg == 0 else f'chip:{chip}, Mix-Mode'
            print(dec_mode)
            if reg != 0:
                self._get_nco_freq(chip)
                reg = self.Read_Reg(chip, 0x111) & 0x46
                data_path_cfg = '边带选择：正边带' if reg == 0x44 else '边带选择：负边带'
                print(data_path_cfg)
        else:
            self._get_nco_freq(chip)

    def get_rf_awg_info(self):
        '''
        查询AWG工作模式
        '''
        self._get_work_mode(1)
        self._get_work_mode(2)

    def wave_compile(self, channel, waves_list, is_continue=False, false_data=False, pipeline=False):
        self.Stop(12) if channel in [1,2] else self.Stop(34)
        super().wave_compile(channel, waves_list, is_continue, false_data, pipeline)
        self.Stop(12) if channel in [1,2] else self.Stop(34)