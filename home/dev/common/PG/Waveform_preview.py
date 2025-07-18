import csv
import os
import numpy as np
# import matplotlib.pyplot as plt
# from matplotlib.pyplot import savefig

# plt.rcParams['font.sans-serif'] = ['SimHei']  # 步骤一（替换sans-serif字体）
# plt.rcParams['axes.unicode_minus'] = False  # 步骤二（解决坐标轴负数的负号显示问题）

mode = (
    u'direct output', u'', u'', u'', u'', u'', u'', u'', u'', 'trig output', u'delay output',
    u'', u'')


def print_wave(x_list, unit, listv, listv1, listv2, note, filename, outdir, user_set_xlabel=True):
    """
    :param x_list: x轴标签数据
    :param unit: 单位
    :param listv: 波形曲线
    :param listv1: 触发曲线
    :param listv2: 模式曲线
    :param note: 图片标题
    :param filename: 文件名，不需要后缀
    :param outdir: 输出目录
    :param user_set_xlabel: 是否需要显示含单位的x轴标签，设为true时，以x_list等间隔取10个数，此时的图像放大时不会显示细节的x轴的值
                             设为false时matplotlib自动控制显示，此时显示图像的放大缩小均会显示细节的x轴的值
    :return: None

    :notes::

        :param x_list: x轴标签数据
        :param listv: 波形曲线
        :param listv1: 触发曲线
        :param listv2: 模式曲线
        上面4个列表要等长
    """
    global mode
    y_pos = np.arange(len(mode))  # 模式是枚举型的
    x_pos = np.arange(len(x_list))  # x轴大小由列表长度决定
    plt.rc('figure', figsize=(9, 4))  # 设定图片大小

    fig, host = plt.subplots()

    par1 = host.twinx()
    par1.grid()
    # print(f'len listv:{len(listv)},len listv1:{len(listv1)},len listv2:{len(listv2)}')
    l1, = host.plot(range(0, len(listv2)), listv2, 'r*', label=u'trigger flag')
    p1, = host.plot(range(0, len(listv)), listv, color='blueviolet', label=u'waveform')
    p2, = par1.plot(range(0, len(listv1)), listv1, 'k.', label=u'output mode')

    host.set_xlim(0, len(listv) )
    host.set_ylim(-1.1, 1.8)
    # 设定Y轴离上下边框的范围
    # if min(listv) != max(listv):
    #     host.set_ylim((min(listv) - 0.2*abs(min(listv))) * 1.0, max(listv) + 0.6*abs(max(listv)))
    plt.yticks(y_pos, mode, rotation=0, fontsize='small')
    nn = x_pos[::int(len(x_list) / 10)]
    xx = []
    for ii in nn:
        xx.append(str(round(x_list[ii],2)) + unit)
    tt = list(nn)
    if (x_pos[-1] - nn[-1]) / nn[1] > 0.49:  # 最后一个标识不能太近
        xx.append(str(round(x_list[-1])) + unit)
        tt.append(x_pos[-1])
    if user_set_xlabel:
        plt.xticks(tt, xx, rotation=60)

    ss = filename
    _title = ss
    if ss.find('-') > -1:
        # host.set_xlabel(ss[:ss.find('-')])
        _title = ss[:ss.find('-')]
    # else:
        # host.set_xlabel(ss)
    host.set_ylabel(u'trigger flag')
    par1.set_ylabel(u'output mode')

    host.yaxis.label.set_color(p1.get_color())
    par1.yaxis.label.set_color(p2.get_color())

    tkw = dict(size=4, width=1.5)
    host.tick_params(axis='y', colors=p1.get_color(), **tkw)
    par1.tick_params(axis='y', colors=p2.get_color(), **tkw)
    host.tick_params(axis='x', **tkw)
    first_legend = host.legend(handles=[l1], loc='upper center')
    host.add_artist(first_legend)
    second_legend = host.legend(handles=[p1], loc='upper left')
    host.add_artist(second_legend)
    host.legend(handles=[p2], loc='upper right')
    # fig.legend(loc='center right', bbox_to_anchor=(1,1), bbox_transform=par1.transAxes)

    # plt.title(note)
    plt.title(_title)
    if filename.find('/') > 0:
        tt = filename.split('/')  # [filename.index('/')]='_'
        filename = tt[0] + tt[1]
    filename = filename.strip() + '.png'
    pathname = os.path.join(outdir, filename)

    savefig(pathname)
    plt.show()


class Waveform_preview:
    """
    波形基础类，用于简单测试
    包含正弦，方波，直流，脉冲，三角波等几种类型
    每种类型可以设置频率，最大值，最小值，长度
    """

    def __init__(self):
        self.amplitude = 1
        self.defaultvolt = 0
        self.max_wave_length = 200000  # 最大200K个采样点
        self.frequency = 2e9
        self.commands = None
        self.wave = None

    def get_loop_mode(self, cmd=None):
        """
        获取命令数据的执行模式

        :return: 
        """
        commands = self.commands
        if cmd:
            commands = cmd
        loop_mode = ''
        func_dic = {0: 'S', 1: 'L', 2: 'J', 8: 'T', 12: 'C', 4: 'D'}
        loop_dic = {0: '(', 1: '[', 2: '{', 3: '<'}
        jump_dic = {0: ')', 1: ']', 2: '}', 3: '>'}
        start_addr = [[], [], [], []]
        for commands_idx in range(len(commands) >> 2):
            idx = commands_idx << 2
            func = (commands[idx + 3] >> 11) & 0x000F
            level = (commands[idx + 3] >> 8) & 0x03
            count = commands[idx + 2]
            stop = (commands[idx + 3] >> 15) & 0x0001
            label = func_dic[func]
            if label == 'L':
                label = str(count) + loop_dic[level]
                start_addr[level].append(commands_idx)
                print('{}level begin: address is:{}'.format(level, commands_idx))
            if label == 'J':
                label = jump_dic[level]
                if len(start_addr[level]) == 0:
                    print('error: cycle level unmatch: address{}'.format(idx))
                commands[idx + 2] = start_addr[level][-1]
                start_addr[level].pop()
                print('{}level end: jump to：{}'.format(level, commands[idx + 2]))
            loop_mode += label
            if stop == 1:
                break
        if len(loop_mode) > 30:
            loop_mode = loop_mode[:30] + '...'
        return loop_mode

    @staticmethod
    def get_commands_level_order(commands):
        """
        :param commands: 待解析命令集
        :return:

        :notes::

            获取 commands中的嵌套关系
        """
        max_cnt_dic = {0: 0, 1: 0, 2: 0, 3: 0}
        loop_level = 0
        for commands_idx in range(len(commands) >> 2):
            idx = commands_idx << 2
            stop = (commands[idx + 3] >> 15) & 0x00001
            func = (commands[idx + 3] >> 11) & 0x000F
            level = (commands[idx + 3] >> 8) & 0x03

            if func == 1:  # loop start
                loop_level += 1
                max_cnt_dic[level] = max(max_cnt_dic[level], loop_level)
            if func == 2:  # loop end or jump
                loop_level -= 1
            if stop == 1:
                break
        list1 = sorted(max_cnt_dic.items(), key=lambda x: x[1], reverse=True)
        return [item[0] for item in list1]

    @staticmethod
    def commands_extend(commands, pro_level):
        """
        :param commands: 待展开命令集
        :param pro_level: 展开级别
        :return:
        """
        extended_commands = []
        loop_start_addr = 0
        loop_end_addr = 0
        loop_cnt = 0
        loop_level = 0
        find_start = 0
        has_level = 0
        for commands_idx in range(len(commands) >> 2):
            idx = commands_idx << 2
            stop = (commands[idx + 3] >> 15) & 0x00001
            func = (commands[idx + 3] >> 11) & 0x000F
            level = (commands[idx + 3] >> 8) & 0x03
            count = commands[idx + 2]
            # jump_addr = commands[idx + 2] << 2

            if func == 1:  # loop start
                # has_loops = 1
                if find_start == 0 and pro_level == level:
                    has_level = 1
                    loop_start_addr = idx
                    loop_cnt = count
                    loop_level = level
                    find_start = 1
                    extended_commands += commands[loop_end_addr:idx]

            if func == 2:  # loop end or jump
                if pro_level == level:
                    find_start = 0
                    if level != pro_level:
                        print('warnning: end level:{} is differrent from begin level:{}'.format(level, loop_level))
                    else:
                        loop_end_addr = idx + 4
                        extended_commands += commands[loop_start_addr:loop_end_addr] * loop_cnt
            if stop == 1:
                break
        if find_start > 0:
            print('warnning: matched end level is not found, begin level is:{}, recorded level is: {}'.format(loop_level, find_start))

        extended_commands += commands[loop_end_addr:]
        return extended_commands, has_level

    def get_wave_trig_pos(self, trig_delay, wave_length, count):
        """
        :param trig_delay: 触发延时
        :param wave_length: 波形长度
        :param count: 触发位置计数
        :return: 返回命令集输出的触发的位置
        """

        if trig_delay < 0 or trig_delay > 255:
            print('delay time is out of bound:{}'.format(trig_delay))
            os.error('delay time is out of bound:{}'.format(trig_delay))
        # trig_pos = (count + trig_delay - 45) * 8
        # 老版本
        trig_pos = (count + trig_delay) * self.sample_per_clock
        return wave_length + trig_pos

    def wave_preview(self, awg=None, ch=1, test_note='', is_volt=True, user_set_xlabel=True, max_wave_show_len=10000):
        """
        :param user_set_xlabel: 该值为True时，生成的波形横轴是ns时间单位，\
                                图像交互放大时不会显示放大的x坐标细节，\
                                Flase时，生成x轴是自动生成的计数，可以随波形放大而显示细节
        :param is_volt: 该值为True时，显示的波形y轴是实际AWG输出的volte，False时显示AWG电压对应的code
        :param awg: AWG对象, 该值为None时，预览波形对象的wave和command预期生成的波形
        :param ch: AWG通道（1，2，3，4）
        :param test_note: 预览图像的标题
        :return: 预览命令集对象生成的波形
        """
        self.frequency = awg.frequency
        self.sample_per_clock = awg.sample_per_clock
        self.ns_per_sample = 1e9/self.frequency
        self.ns_per_clock = self.ns_per_sample*self.sample_per_clock
        addr_step = int(np.log2(self.sample_per_clock))
        wave = []
        trig_pos_list = []
        commands_mode = []
        coe = 1.1
        default_volt = self.defaultvolt
        temp_commands = self.commands
        temp_wave = self.wave

        if awg:
            awg._channel_check(ch)
            coe = awg.coe[ch-1]
            # 默认输出值是默认code+用户设置的偏置值/0电平code
            default_volt = awg.offset_volt[ch-1]
            temp_commands = awg.commands[ch - 1]
            # 用户设置的波形在波形编译时没有加任何偏置数据，所以在还原成volte时再加上默认volte，就是最终的波形输出
            temp_wave = list((np.asarray(awg.waves[ch - 1]) - awg.zerocode[ch-1]) * coe / 32767.5 + default_volt)
            # coe = awg.voltrange[ch - 1][1] - awg.voltrange[ch - 1][0]
            if test_note == '':
                test_note = ',{0},channel: {1}'.format(awg.dev_id,ch)

        has_trig = False
        extended_commands = None

        #  将命令集展开
        #  获取嵌套关系
        loop_order = self.get_commands_level_order(temp_commands)
        for pro_level in loop_order:
            extended_commands, has_level = self.commands_extend(temp_commands, pro_level)
            temp_commands = extended_commands
        # 对展开后的命令集生成对应的波形，模式，触发命令集
        trig_cnt = 0
        for commands_idx in range(len(extended_commands) >> 2):
            idx = commands_idx << 2  # 命令集索引
            stop = extended_commands[idx + 3] >> 15  # 命令集停止标识
            func = (extended_commands[idx + 3] >> 11) & 0x000F  # 命令集类型
            start_addr = extended_commands[idx] << addr_step  # 波形区起始地址
            wave_len = extended_commands[idx + 1] << addr_step  # 波形采样点数
            end_addr = start_addr + wave_len  # 波形区结束地址
            count = extended_commands[idx + 2]  # 多功能计数区
            istrig_commands = (extended_commands[idx + 3] >> 10) & 0x0001  # 命令集trig output标识
            trig_delay = (extended_commands[idx + 3]) & 0x00FF  # 触发命令集的延时计数
            level = 0
            level_label_loop = ['0']
            level_label_jump = ['0']
            func_dic = {0: ['direct output'], 8: ['trig output'], 4: ['delay output'], 12: ['select output'], 1: level_label_loop, 2: level_label_jump}
            if func_dic[func][0] == 'select output':
                start_addr = (count & 0x00FF) << 9  # 低5位地址为0 #0态的地址 # 取0态的地址
                end_addr = start_addr + wave_len  # 波形区结束地址

            # 如果是命令集有触发标识，添加触发信号的位置
            if istrig_commands == 1 or func_dic[func][0] == 'trig output':
                has_trig = True
                trig_cnt += 1
                pos_cnt = 0
                if func_dic[func][0] == 'delay output':
                    pos_cnt = count
                trig_pos_list.append(self.get_wave_trig_pos(trig_delay, len(wave), pos_cnt))
            unit = []
            if func_dic[func][0] == 'delay output' or func_dic[func][0] == 'trig output':  # 计数类型延时
                unit = [default_volt] * (count << addr_step)  # 延时
            unit += temp_wave[start_addr:end_addr]
            wave += unit
            commands_mode += [mode.index(func_dic[func][level])] * len(unit)

            if end_addr > len(temp_wave):
                print('end addr:{0}, wave length:{1}'.format(end_addr, len(temp_wave)))
                print('waveform is out of bound, output will have unwanted waveform:{}'.format(extended_commands[idx:idx + 4]))

            if wave_len < (5 << addr_step):
                os.error('error: waveform length less than {0}ns, this is not surpported'.format((5 << addr_step)*self.sample_per_clock))

            if stop == 1:
                break
            if len(wave) > 100000:
                print('Warning：generated wave length is to long, some wave is not displayed. be easy, the output is not infected')
                break
            if trig_cnt >= 5:
                print('Warning：trigger count is two much, display first 5 triggered wave. be easy, the output is not infected')
                break
        # 根据触发位置list生成触发命令集
        # wave_trig = [min(wave)] * len(wave)
        wave_trig = [-1.1] * len(wave)
        trig_time = []
        note = 'Continuous waveform output'
        if len(trig_pos_list) > 0:
            pre_time = trig_pos_list[0]
            for idx in trig_pos_list:
                if idx < 0:
                    print('Warning, trigger position out of waveform boundary:{}ns'.format(idx * self.ns_per_sample))
                    idx = 0
                elif idx > len(wave):
                    print('Warning, trigger position out of waveform boundary:{}ns'.format(idx * self.ns_per_sample))
                    idx = -1
                print('trigger time:{}ns'.format(idx * self.ns_per_sample))
                tmp_pre = idx
                if idx - pre_time < -41:
                    print('Note: previous trigger time greater than the current trigger time')
                    tmp = trig_time[-1]
                    trig_time[-1] = idx * self.ns_per_sample
                    trig_time.append(tmp)
                    tmp_pre = tmp
                elif idx - pre_time < 0:
                    trig_time[-1] = idx * self.ns_per_sample
                    tmp_pre = idx * self.ns_per_sample
                    print('Note: previous trigger time overlap with current trigger time')
                elif idx - pre_time < 41 and idx != pre_time:
                    # 触发脉冲宽度为20ns，当两个触发位置间隔小于41时，存在重叠现象
                    print('warnning: trigger time is overlaped')
                else:
                    trig_time.append(idx * self.ns_per_sample)
                pre_time = tmp_pre
                wave_trig[idx] = max(wave)*coe
            note = self.get_loop_mode(temp_commands)
        # else:
        #     commands_mode = '连续波形'
        xlist = np.arange(0, len(wave))*self.ns_per_clock
        xlist = xlist.repeat(2)
        xlist.sort()
        file_dir = os.getcwd() + '\\test_data'
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)
        filename = 'waveform preview (displayed with volte)' + test_note  # +'-'+time.strftime('%Y_%m_%d_%H_%M_%S', time.localtime(time.time()))

        # print(len(xlist), len(wave))
        if not has_trig and len(wave) > max_wave_show_len:
            wave_trig = wave_trig[:max_wave_show_len]
            wave = wave[:max_wave_show_len]
            xlist = xlist[:max_wave_show_len]
        assert max(wave) <= 1.1  # 电压输出异常，大于上限
        assert min(wave) >= -1.1  # 电压输出异常，小于下限
        if not is_volt:
            print('convert to code')
            wave_trig = (np.asarray(wave_trig)/coe + 1) * 32767.5
            wave = (np.asarray(wave)/coe+1) * 32767.5
            filename = 'waveform preview (displayed with code)' + test_note
            # +'-'+time.strftime('%Y_%m_%d_%H_%M_%S', time.localtime(time.time()))
        xlist = np.arange(0, len(wave))*self.ns_per_sample
        print_wave(xlist, 'ns', wave, commands_mode, wave_trig, note, filename, file_dir,
                  user_set_xlabel=user_set_xlabel)
        
        # return len(wave), wave, trig_time

    def load_wave_file(self, filename):
        """
        波形数据文件，要求文件内的数据是-1与1之间的值

        :return: 如果文件中有超范围的值，返回-1， 正常返回0
        """
        self.wave = []
        with open(filename, 'r') as csvfile:
            reader = csv.reader(csvfile)
            for item in reader:
                self.wave.append(item[0])
        assert len(self.wave) <= self.max_wave_length  # 波形长度越界
        for volt in self.wave:
            if abs(float(volt)) > 1:
                os.error('value is out of bound([-1,1])：{0}'.format(volt))
                return -1
        return

    def write_wave_file(self, filename):
        """
        写波形数据文件，要求文件内的数据是（-1，1）之间的值
        :return:
        """
        with open(filename, 'w', newline="") as f:
            csvwriter = csv.writer(f)
            for item in self.wave:
                csvwriter.writerow([item])
        return 0


if __name__ == '__main__':
    wave_ctrl = Waveform_preview()
    # wave_ctrl.generate_sin(period=100e-9, amp=0.1)  # 生成周期为100ns的正弦信号
    wave_ctrl.wave_preview(is_volt=True)
