from dev.common import BaseDriver, QInteger, QBool, QReal, QString
try:
    from dev.common.DDS_LH import clk_fout_dev
except:
    print('Import clk_fout_dev of clk fout Error!')


class Driver(BaseDriver):

    CHs_num = 19

    CHs = list(range(1, CHs_num + 1, 1))

    _trigger_source = {
        'Internal': 0,
        'External rising edges': 1,
        'External falling edges': 2,
        'External follow rising edges': 3,
        'External follow falling edges': 4,
        'Single shot': 5,
        'Single shot external rising edges': 6,
        'Single shot external falling edges': 7,
        'Single shot follow external rising edges': 8,
        'Single shot follow external falling edges': 9,
    }  # 没什么用，就是来展示一下有哪些模式。

    quants = [
        QBool('Output', value=True, ch=1),  # True标记为不起作用，False将真是关闭。
        QBool('Enable', value=True, ch=1),  # 通道使能标记

        QString('TriggerSource', ch=1,
                value='Single shot external rising edges'),
        QInteger('TRIG', ch=1),  # 触发开始命令
        # 在触发设置的最后，其余变量都是缓存，当triggermode设置的时候会真正刷新机器的触发设置。
        QString('TriggerMode', ch=1, value='Burst'),

        QInteger('BurstCount', ch=1, value=1024),
        QReal('Delay', ch=1, value=0, unit='s'),
        QReal('Period', ch=1, value=200e-6, unit='s'),
    ]

    segment = ('lh', '107|108|109')

    def __init__(self, addr, **kw):
        super().__init__(addr, **kw)
        self.model = 'LH_TRIG'

    def open(self, **kw):
        self.handle = clk_fout_dev(self.addr)

    def close(self, **kw):
        pass

    def read(self, name: str, **kw):
        return super().read(name, **kw)

    def write(self, name: str, value, **kw):
        ch = kw.get('ch', 1)

        if name == 'TRIG':
            self.triggerOpen()
        elif name == 'TriggerMode':
            if value == 'Burst':
                self.BurstMode_init(ch=ch)
            elif value == 'Continuous':
                self.Convention_init(ch=ch)
            elif value == 'Fanout':
                self.FanoutMode_init(ch=ch)
            else:
                print('Invalid trigger mode.')
        if name == 'Output':
            if not value:
                self.triggerClose()
        else:
            super().write(name, value, **kw)

        return value

    # *#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*# user defined #*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#

    def FanoutMode_init(self, ch=1):
        self.triggerClose()
        trigger_parameter = {
            'trigger_source': 1,
            'trigger_continue': 1,
            'trigger_block_en': int(self.config['Enable'][ch]['value']),
            'trigger_ref': 0,
            'trigger_times': 1,
            'trigger_us': 10,
            'trigger_delay': 0
        }

        ret = self.handle.trigger_ctrl(ch, trigger_parameter)
        assert ret == 'ok', 'Error in `FanoutMode_init()`'

    def Convention_init(self, ch=1):
        self.triggerClose()
        TriggerSource = self.config['TriggerSource'][ch]['value']

        trigger_ref = 0
        if TriggerSource == 'Internal':
            trigger_ref = 0
        elif TriggerSource == 'External rising edges':
            trigger_ref = 1
        elif TriggerSource == 'External falling edges':
            trigger_ref = 5
        elif TriggerSource == 'External follow rising edges':
            trigger_ref = 3
        elif TriggerSource == 'External follow falling edges':
            trigger_ref = 7
        else:
            assert 0, 'Error in `Convention_init()`'

        trigger_parameter = {
            'trigger_source': 0,
            'trigger_continue': 1,
            'trigger_block_en': int(self.config['Enable'][ch]['value']),
            'trigger_ref': trigger_ref,
            'trigger_times': 1,
            'trigger_us': self.config['Period'][ch]['value'] * 1e6,
            'trigger_delay': self.config['Delay'][ch]['value'] * 1e6
        }

        ret = self.handle.trigger_ctrl(ch, trigger_parameter)
        assert ret == 'ok', 'Error in `Convention_init()`'

    def BurstMode_init(self, ch=1):
        self.triggerClose()
        TriggerSource = self.config['TriggerSource'][ch]['value']

        trigger_ref = 0
        if TriggerSource == 'Single shot':
            trigger_ref = 0
        elif TriggerSource == 'Single shot external rising edges':
            trigger_ref = 1
        elif TriggerSource == 'Single shot external falling edges':
            trigger_ref = 5
        elif TriggerSource == 'Single shot follow external rising edges':
            trigger_ref = 3
        elif TriggerSource == 'Single shot follow external falling edges':
            trigger_ref = 7
        else:
            assert 0, 'Error in `BurstMode_init()`'

        trigger_parameter = {
            'trigger_source': 0,
            'trigger_continue': 0,
            'trigger_block_en': int(self.config['Enable'][ch]['value']),
            'trigger_ref': trigger_ref,
            'trigger_times': self.config['BurstCount'][ch]['value'],
            'trigger_us': self.config['Period'][ch]['value'] * 1e6,
            'trigger_delay': self.config['Delay'][ch]['value'] * 1e6,
        }

        ret = self.handle.trigger_ctrl(ch, trigger_parameter)
        assert ret == 'ok', 'Error in `BurstMode_init()`'

    def triggerClose(self):
        '''
        该函数用于关闭触发器
        '''
        ret = self.handle.trigger_close()
        assert ret == 'ok', 'Error in `triggerClose()`'

    def triggerOpen(self):
        '''
        该函数用于关闭触发器
        '''
        ret = self.handle.trigger_open()
        assert ret == 'ok', 'Error in `triggerOpen()`'
