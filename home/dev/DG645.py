import time

from dev.common import QInteger, QOption, QReal, VisaDriver


class QRealDelay(QReal):
    def _process_query(self, value):
        '''process the value query from Instrument before final return'''
        _, v = value.split(',')
        return float(v)


class Driver(VisaDriver):

    error_command = 'LERR?'
    support_models = ['DG645']

    CHs = ['T0', 'AB', 'CD', 'EF', 'GH']

    _output_BNC_b = {
        'T0': 0,
        'AB': 1,
        'CD': 2,
        'EF': 3,
        'GH': 4
    }

    _output_BNC_cd = {
        'T0': (0, 1),
        'AB': (2, 3),
        'CD': (4, 5),
        'EF': (6, 7),
        'GH': (8, 9)
    }

    _delay_channel = dict(
        zip(['T0', 'T1', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'], range(10)))

    quants = [
        QReal('Amplitude',
              ch='AB',
              unit='V',
              set_cmd='LAMP %(para_b)d,%(value).2f',
              get_cmd='LAMP?%(para_b)d'),
        QReal('Offset',
              ch='AB',
              unit='V',
              set_cmd='LOFF %(para_b)d,%(value).2f',
              get_cmd='LOFF?%(para_b)d'),
        # QReal('Delay',
        #     ch='AB',
        #     unit='s',
        #     set_cmd='DLAY %(para_c)d,0,%(value).6E',
        #     get_cmd='DLAY?%(para_c)d'),
        # QReal('Length',
        #     ch='AB',
        #     unit='s',
        #     set_cmd='DLAY %(para_d)d,%(para_c)d,%(value).6E',
        #     get_cmd='DLAY?%(para_d)d'),
        QRealDelay('Delay',
                   ch='AB',
                   unit='s',
                   set_cmd='DLAY %(para_c)d,0,%(value).6E',
                   get_cmd='DLAY?%(para_c)d'),
        QRealDelay('Length',
                   ch='AB',
                   unit='s',
                   set_cmd='DLAY %(para_d)d,%(para_c)d,%(value).6E',
                   get_cmd='DLAY?%(para_d)d'),
        QOption('Polarity',
                ch='AB',
                set_cmd='LPOL %(para_b)d,%(option)s',
                get_cmd='LPOL?%(para_b)d',
                options=[('pos', '1'), ('neg', '0')]),


        # global
        QReal('TriggerRate',
              unit='Hz',
              set_cmd='TRAT %(value).6E',
              get_cmd='TRAT?'),
        QReal('TriggerLevel',
              unit='V',
              set_cmd='TLVL %(value).2f',
              get_cmd='TLVL?'),
        QOption('TriggerSource',
                set_cmd='TSRC %(option)s',
                get_cmd='TSRC?',
                options=[
                    ('Internal', '0'),
                    ('External rising edges', '1'),
                    ('External falling edges', '2'),
                    ('Single shot external rising edges', '3'),
                    ('Single shot external falling edges', '4'),
                    ('Single shot', '5'),
                    ('Line', '6'),
                ]),

        QInteger('BurstCount',
                 unit='num',
                 set_cmd='BURC %(value)d',
                 get_cmd='BURC?'),
        QReal('BurstDelay',
              unit='s',
              set_cmd='BURD %(value).6E',
              get_cmd='BURD?'),
        QInteger('BurstMode',  # 是否打开Burst模式，0关闭，1打开
                 set_cmd='BURM %(value)d',
                 get_cmd='BURM?'),
        QReal('BurstPeriod',
              unit='s',
              set_cmd='BURP %(value).6E',
              get_cmd='BURP?'),
        # QInteger('Burst T0 Configuration',
        #     set_cmd='BURT %(value)d',
        #     get_cmd='BURT?'),
        QInteger('SingleTrigger',
                 set_cmd='',
                 get_cmd=''),
        QInteger('TRIG'),
        QInteger('TriggerMode'),  # burst or continuous
    ]

    segment = ('ot', '199')

    def __init__(self, addr, **kw):
        super().__init__(addr, **kw)

    def open(self, **kw):
        self.addr = f"TCPIP::{self.addr}"
        return super().open(**kw)

    def close(self, **kw):
        return super().close(**kw)

    def read(self, name: str, **kw):
        kw = self._preprocess_kw(kw)
        return super().read(name, **kw)
        # if name in ['Delay','Length']:
        #     cmd = quant._formatGetCmd(**kw)
        #     _,value = self.query_ascii_values(cmd)
        #     value = quant._process_query(value)
        #     return value
        # else:
        #     return super().read(quant, **kw)

    def write(self, name: str, value, **kw):
        if name in ['SingleTrigger', 'TRIG']:
            time.sleep(0.1)
            self.startGun()
        elif name == 'TriggerMode':
            if value == 'Burst':
                self.BurstMode_init(**kw)
            else:
                self.Convention_init(**kw)
        else:
            kw = self._preprocess_kw(kw)
            super().write(name, value, **kw)

        return value

    # *#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*# user defined #*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#
    def _preprocess_kw(self, kw):
        '''添加para_b/c/d三个关键词'''
        ch = kw.get('ch', 'AB')
        para_b = self._output_BNC_b.get(ch, None)
        para_c, para_d = self._output_BNC_cd.get(ch, (None, None))
        kw.update({
            'para_b': para_b,
            'para_c': para_c,
            'para_d': para_d,
        })
        return kw

    def Trigger_singleshot(self):
        self.handle.write('*TRG')

    def Convention_init(self, rate=5000, **kwds):
        self.setValue('TriggerSource', 'Internal', **kwds)
        self.setValue('BurstMode', 0, **kwds)  # 关闭
        self.setValue('TriggerRate', rate, **kwds)

    def BurstMode_init(self, count=2048, delay=200e-6, period=200e-6, **kwds):
        self.setValue('TriggerSource', 'Single shot', **kwds)
        self.setValue('BurstMode', 1, **kwds)  # 打开
        self.setValue('BurstCount', count, **kwds)
        self.setValue('BurstDelay', delay, **kwds)
        self.setValue('BurstPeriod', period, **kwds)

    def startGun(self):
        self.Trigger_singleshot()
