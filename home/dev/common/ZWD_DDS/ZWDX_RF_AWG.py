import socket
import numpy as np
import struct
import pickle
import os
from matplotlib import pyplot as plt
import time

ack_type = {'down_ack': 1, 'start_ack': 2, 'stop_ack': 3}
g_ch_status = 0


class dev_init:
    head = 0x18EFDC01
    cmd_type = 0x01
    input_clk = 00
    yuliu = np.zeros(6, dtype=np.uint8)
    end = 0x01DCEF18

    def __init__(self):
        pass

    def build(self):
        format_str = '!IBB6sI'
        string = struct.pack(format_str, self.head, self.cmd_type, self.input_clk, self.yuliu.tobytes(), self.end)
        return string


class tcp_down_cmd:
    head = 0x18EFDC01
    cmd_type = 2
    ch = 1
    yuliu = np.zeros((6,), np.int8)
    wave_data = []
    end = 0x01DCEF18

    def __init__(self, ch, data):
        self.ch = ch
        if type(data[0]) == np.int8:
            self.length = len(data)
        elif type(data[0]) == np.int16:
            self.length = len(data) * 2
        else:
            print('error')
        self.wave_data = data

    def build(self):
        format_str = '!IBB6s' + str(self.length) + 's' + 'I'
        ss = struct.pack(format_str, self.head, self.cmd_type, self.ch,
                         self.yuliu.tobytes(), np.asarray(self.wave_data).tobytes(), self.end)

        return ss


class cai_yang_lv_switch:
    head = 0x18EFDC01
    cmd_type = 0x03
    cai_yang_lv = 0
    yuliu = np.zeros(6, dtype=np.uint8)
    end = 0x01DCEF18

    def build(self):
        return struct.pack('!IBB6sI', self.head, self.cmd_type, self.cai_yang_lv, self.yuliu.tobytes(), self.end)


class mo_shi_switch:
    head = 0x18EFDC01
    cmd_type = 0x04
    mode = 0
    yuliu = np.zeros(6, dtype=np.uint8)
    end = 0x01DCEF18

    def build(self):
        return struct.pack('!IBB6sI', self.head, self.cmd_type, self.mode, self.yuliu.tobytes(), self.end)


class tcp_open_cmd:
    head = 0x18EFDC01
    cmd_type = 5
    ch = 0x0FFF
    yuliu = np.zeros((5,), np.int8)
    end = 0x01DCEF18

    def __init__(self, ch_list, operation='open'):
        global g_ch_status
        if operation == 'open':
            for i in ch_list:
                g_ch_status |= (1 << (i - 1))
        else:
            for i in ch_list:
                g_ch_status &= ~(1 << (i - 1))
        self.ch = g_ch_status

    def build(self):
        format_str = '!IBH5sI'
        ss = struct.pack(format_str, self.head, self.cmd_type, self.ch, self.yuliu.tobytes(), self.end)
        return ss


class tcp_mai_chong_switch_cmd:
    head = 0x18EFDC01
    cmd_type = 6
    mode = 0
    yuliu = np.zeros((6,), np.int8)
    end = 0x01DCEF18

    def __init__(self, mode=0):
        self.mode = mode

    def build(self):
        format_str = '!IBB6sI'
        ss = struct.pack(format_str, self.head, self.cmd_type, self.mode, self.yuliu.tobytes(), self.end)
        return ss


class tcp_ip_switch_cmd:
    head = 0x18EFDC01
    cmd_type = 7
    ip = []
    yuliu = np.zeros((3,), np.int8)
    end = 0x01DCEF18

    def __init__(self, ip=''):
        self.ip.clear()
        list = ip.split('.')
        for i in list:
            self.ip.append(int(i))

    def build(self):
        format_str = '!IB4s3sI'
        ss = struct.pack(format_str, self.head, self.cmd_type, np.asarray(self.ip, np.uint8).tobytes(),
                         self.yuliu.tobytes(), self.end)
        return ss


class sleep_control:
    head = 0x18EFDC01
    cmd_type = 0x08
    ch = 1
    delay = 0x00000000
    yuliu = np.zeros(2, dtype=np.uint8)
    end = 0x01DCEF18

    def build(self):
        return struct.pack('!IBBI2sI', self.head, self.cmd_type, self.ch, self.delay, self.yuliu.tobytes(), self.end)


class tcp_ref_switch_cmd:
    head = 0x18EFDC01
    cmd_type = 5
    ref = 0x00
    yuliu = np.zeros((6,), np.int8)
    end = 0x01DCEF18

    def __init__(self, ref=''):
        if ref == 'ext_ref':
            self.ref = 0x01
        elif ref == 'in_ref':
            self.ref = 0x00
        else:
            print(f'input error')

    def build(self):
        format_str = '!IBB6sI'
        ss = struct.pack(format_str, self.head, self.cmd_type, self.ref,
                         self.yuliu.tobytes(), self.end)
        return ss


def sin_wave(pulse_width, frequency, after_init_phase, A):
    """
    y = Asin(wt + @)
    w = 2*pi*f
    T = 2*PI/W
    位宽16位
    采样率这里固定为5G
    :param A:
    :param pulse_width: 脉冲时宽，也叫采样时长,ns单位
    :param frequency: 基带频率Hz
    :param after_init_phase: 相位
    :return:
    """
    sf = 5 * pow(10, 9)
    # fs = 1 / (5 * pow(10, 9))
    # count = (pulse_width * pow(10, -9)) / fs

    # x = np.linspace(0, pinglv * shichang * 2 * np.pi, caiyangpinglv * shichang)
    x = np.linspace(0, frequency * pulse_width * 2 * np.pi + after_init_phase, int(sf * pulse_width))
    y = A * np.sin(x)
    # plt.plot(x, y)
    # plt.show()
    yy = np.asarray(y) * ((pow(2, 16) - 1) / 2)
    data = list(map(np.int16, yy))
    yyy = np.asarray(data).byteswap()
    return yyy


def square_wave():
    x = np.linspace(-10, 10, 100)
    y = []
    for i in x:
        if np.sin(i) > 0:
            y.append(-1)
        else:
            y.append(1)
    return np.array(y)


class RF_AWG(object):

    def __init__(self, ip, port):
        self.s = socket.socket()
        self.s.connect((ip, port))

    def __del__(self):
        self.s.close()

    def init_dev(self, clk):
        """
        初始化设备
        :param clk:10MHz 或 100MHz
        :return:返回指令响应状态
        """
        cmd = dev_init()
        if clk == 10:
            cmd.input_clk = 0
        elif clk == 100:
            cmd.input_clk = 1
        elif clk == 1000:
            cmd.input_clk = 2
        else:
            pass
        self.s.send(cmd.build())
        return self.get_ack_status()

    def set_cai_yang_lv(self, speed='5G'):
        """
        采样率切换
        :param speed:‘5G’ '4G'
        :return:返回指令响应状态
        """
        cmd = cai_yang_lv_switch()
        if speed == '5G':
            cmd.cai_yang_lv = 0
        elif speed == '4G':
            cmd.cai_yang_lv = 1
        else:
            pass
        self.s.send(cmd.build())
        return self.get_ack_status()

    def set_mode_switch(self, moshi='NRZ'):
        """
        模式切换
        :param moshi: 'NRZ' 或 'MIX'
        :return:
        """
        cmd = mo_shi_switch()
        if moshi == 'NRZ':
            cmd.mode = 0
        elif moshi == 'MIX':
            cmd.mode = 1
        else:
            pass
        self.s.send(cmd.build())
        return self.get_ack_status()

    def set_delay(self, ch=1, delay=0):
        """
        延时调节指令
        :param ch: 通道
        :param delay: 延时【0-15】
        :return:
        """
        cmd = sleep_control()
        cmd.ch = ch
        cmd.delay = delay
        self.s.send(cmd.build())
        return self.get_ack_status()

    def write_wave(self, data, ch=1):
        cmd = tcp_down_cmd(ch, data)
        self.s.send(cmd.build())

    def read_process(self):
        msg = self.s.recv(16)
        return msg

    def get_ack_status(self):
        msg = self.read_process()
        format_str = '!IBB6sI'
        head, type, ack, yuliu, end = struct.unpack(format_str, msg)
        if ack == 0xAA:
            return True
        else:
            return False

    def tcp_send_sin_wave(self, ch, pulse_width, frequency, after_init_phase, A):
        x = sin_wave(pulse_width, frequency, after_init_phase, A)
        self.write_wave(x, ch)
        return self.get_ack_status()

    def tcp_send_square_wave(self, ch=1):
        x = square_wave()
        self.write_wave(x, ch)
        return self.get_ack_status()

    # def tcp_send_sin_wave_file(self, path, ch=1):
    #     fd = open(path, 'rb')
    #     list = []
    #     size = os.path.getsize(path)
    #     for i in range(size):
    #         byte = fd.read(1)
    #         list.append(byte)
    #     self.write_wave(list, ch)
    #     return self.get_ack_status()

    def dac_point_update(self, path, ch=1):
        fd = open(path, 'rb')
        data = np.fromfile(fd, np.int16)
        self.write_wave(data, ch)
        return self.get_ack_status()

    def write_wave_form(self, data, ch=1):
        """
        写入波形数据
        :param data: 波形数据
        :param ch: 通道
        :return: 返回指令响应状态
        """
        yushu = len(data) % 16
        if yushu:
            cha = 16 - yushu
            a = np.zeros(cha, dtype=np.int8)
            data = np.append(data, a)
        array = np.asarray(data).clip(-1, 1)
        point = array * (2 ** 15 - 1)
        u16point = np.asarray(point, dtype=np.int16).byteswap()
        self.write_wave(u16point, ch)
        return self.get_ack_status()

    # def tcp_send_file(self, path):
    #     fd = open(path, 'rb')
    #     list = []
    #     size = os.path.getsize(path)
    #     # print(time.time())
    #     for i in range(size):
    #         byte = fd.read(1)
    #         list.append(byte)
    #     # print(time.time())
    #     x = np.asarray(list).tobytes()
    #     # print(time.time())
    #     self.s.send(x)
    #     return self.get_ack_status()

    def tcp_send_file(self, path):
        fd = open(path, 'rb')
        self.s.send(np.fromfile(fd, np.uint8))
        return self.get_ack_status()

    def open(self, ch_list):
        """
        打开通道【1-12】
        :param ch_list:需要打开的通道列表 example:[1,5,7]
        :return: 返回打开是否成功状态
        """
        cmd = tcp_open_cmd(ch_list)
        self.s.send(cmd.build())
        return self.get_ack_status()

    def close(self, ch_list):
        """
        关闭通道【1-12】
        :param ch_list:需要关闭的通道列表 example:[2,5,7,10]
        :return:返回关闭是否成功状态
        """
        cmd = tcp_open_cmd(ch_list, 'close')
        self.s.send(cmd.build())
        return self.get_ack_status()

    def set_mode(self, mode):
        """
        设置调制模式
        :param mode:0：脉冲模式 1：点频模式
        :return:返回设置是否成功状态
        """
        cmd = tcp_mai_chong_switch_cmd(mode)
        self.s.send(cmd.build())
        return self.get_ack_status()

    def set_ip(self, ip=''):
        """
        设置板卡IP重启后生效
        :param ip: IP地址
        :return:返回设置是否成功状态
        """
        cmd = tcp_ip_switch_cmd(ip)
        self.s.send(cmd.build())
        return self.get_ack_status()

    def set_ref(self, ref=''):
        """
        设置参考模式
        :param ref: 外参考：'ext_ref' 内外参：'in_ref'
        :return: 返回设置是否成功状态
        """
        cmd = tcp_ref_switch_cmd(ref)
        self.s.send(cmd.build())
        return self.get_ack_status()
