import copy
import functools
import warnings
from itertools import permutations

from qlispc.config import (ABCCompileConfigMixin, ADChannel, AWGChannel,
                           ConfigProxy, GateConfig, MultADChannel,
                           MultAWGChannel, _flattenDictIter, _foldDict, _query,
                           _update)
from qlispc.namespace import DictDriver

_NO_DEFAULT = object()


def _getSharedCoupler(qubitsDict: list[dict]) -> set[str]:
    if qubitsDict:
        s = set(qubitsDict[0].get('couplers', []))
        for qubit in qubitsDict[1:]:
            s = s & set(qubit.get('couplers', []))
        return s
    else:
        return set()


def _makeAWGChannelInfo(section: str, cfgDict: dict, name: str) -> str | dict:
    ret = {}
    channel = cfgDict.get(name, {})
    if name == 'drive':
        if channel.get('address', None) is not None:
            return channel['address']  # channel = cfgDict.get('channel', {})
    elif name == 'RF':
        if channel.get('DDS', None) is not None:
            return f"{section}.waveform.DDS"
        if channel.get('I', None) is not None:
            ret['I'] = f"{section}.waveform.RF.I"
        if channel.get('Q', None) is not None:
            ret['Q'] = f"{section}.waveform.RF.Q"
        ret['lofreq'] = cfgDict.get('setting', {}).get('LO', 0)
        return ret
    elif name == 'AD.trigger':
        return f"{section}.waveform.TRIG"
    elif name == 'probe':
        return channel['address']  # f"{section}.waveform.{name}"


class CompileConfigMixin(ABCCompileConfigMixin):

    def _get_raw_AWG_channel(self, channel: str):
        elm, *_, chType = channel.split('.')
        return self.query(f"{elm}.channel.{chType}")

    def _map_repetitive_channel(self, channel: str):
        if not hasattr(self, 'dev_channels'):
            self.dev_channels = {
                # 'NS_XYZ.CH1': 'Q8.waveform.DDS'
            }

        raw_ch = channel  # self._get_raw_AWG_channel(channel)
        if raw_ch in self.dev_channels:
            channel = self.dev_channels[raw_ch]
        else:
            self.dev_channels[raw_ch] = channel
        return channel

    def _getAWGChannel(self, name, *qubits) -> AWGChannel | MultAWGChannel:

        # qubitsDict = [self.getQubit(q) for q in qubits]

        # if name.startswith('readoutLine.'):
        #     name = name.removeprefix('readoutLine.')
        #     section = qubitsDict[0]['Measure']
        #     cfgDict = self.getReadout(section)
        # elif name.startswith('coupler.'):
        #     name = name.removeprefix('coupler.')
        #     section = _getSharedCoupler(qubitsDict).pop()
        #     cfgDict = self.getCoupler(section)
        # else:
        # section = qubits[0]
        # cfgDict = qubitsDict[0]

        # _makeAWGChannelInfo(section, cfgDict, name)
        chInfo = f'{qubits[0]}.{name}'

        if isinstance(chInfo, str):
            return AWGChannel(self._map_repetitive_channel(chInfo), -1)
        else:
            info = {'lo_freq': chInfo['lofreq']}
            if 'I' in chInfo:
                info['I'] = AWGChannel(
                    self._map_repetitive_channel(chInfo['I']), -1)
            if 'Q' in chInfo:
                info['Q'] = AWGChannel(
                    self._map_repetitive_channel(chInfo['Q']), -1)
            return MultAWGChannel(**info)

    def _getADChannel(self, qubit) -> ADChannel | MultADChannel:
        rl = self.getQubit(qubit)  # ['probe']
        # rlDict = self.getReadout(rl)
        channel = rl.get('acquire', {})  # rl = self.getQubit(qubit)['probe']
        # rlDict = self.getReadout(rl)
        # channel = rlDict.get('channel', {})
        # setting = rlDict.get('setting', {})
        channel = rl.get('acquire', {})
        setting = rl.get('acquire', {})
        chInfo = {
            'IQ': channel.get('address', 'None').rsplit('.', 1)[0],
            'LO': channel.get('LO', None),
            'TRIG': channel.get('TRIG', None),
            'lofreq': setting.get('LO', 0),
            'trigger': '',
            # f'{rl}.waveform.TRIG' if channel.get('TRIG', None) else '',
            'sampleRate': rl.get('adcsr', 0),
            'triggerDelay': setting.get('TRIGD', 0),
            'triggerClockCycle': setting.get('triggerClockCycle', 8e-9),
            'triggerDelayAddress': channel.get('DATRIGD', '')
        }

        return MultADChannel(
            IQ=ADChannel(
                chInfo['IQ'], chInfo['sampleRate'], chInfo['trigger'],
                chInfo['triggerDelay'], chInfo['triggerClockCycle'],
                (('triggerDelayAddress', chInfo['triggerDelayAddress']), )),
            LO=chInfo['LO'],
            DA=self._getAWGChannel('probe', qubit),
            lo_freq=chInfo['lofreq'],
        )

    def _getGateConfig(self, name, *qubits, type=None) -> GateConfig:
        try:
            gate = self.getGate(name, *qubits)
            if not isinstance(gate, dict):
                return None
            qubits = gate['qubits']
            if type is None:
                type = gate.get('default_type', 'default')
            if type not in gate:
                params = gate  # ['params']
            else:
                params = gate[type]
        except:
            type = 'default'
            params = {}
        return GateConfig(name, qubits, type, params)

    def _getAllQubitLabels(self) -> list[str]:
        return self.keys('Q*')


class QuarkConfig(ConfigProxy, CompileConfigMixin):

    def __init__(self, host='127.0.0.1', port=2088):
        self.host = host
        self.port = port


class QuarkLocalConfig(ConfigProxy, CompileConfigMixin):

    def __init__(self, data) -> None:
        self._history = None
        self.__driver = DictDriver(copy.deepcopy(data))

    def test(self):
        return 'rcp config'

    def query(self, q):
        try:
            return self.__driver.query(q)
        except Exception as e:
            pass

    def get(self, key, default=_NO_DEFAULT):
        try:
            return self.__driver.query(key)
        except KeyError as e:
            if default is not _NO_DEFAULT:
                return default
            raise e

    def keys(self, pattern='*'):
        if isinstance(self.__driver, DictDriver):
            return self.__driver.keys(pattern)
        return self._keys

    def update(self, q, v, cache=False):
        if isinstance(self.__driver, DictDriver):
            self.__driver.update_many({q: v})
        else:
            self.__driver.update(q, v)

    def getQubit(self, name):
        return self.query(name)

    def getCoupler(self, name):
        return self.query(name)

    def getReadout(self, name):
        return self.query(name)

    def getGate(self, name, *qubits):
        order_senstive = self.query(f"gate.{name}.__order_senstive__")
        if order_senstive is None:
            order_senstive = True
        if len(qubits) == 1 or order_senstive:
            ret = self.query(f"{'_'.join(qubits)}.{name}")
            if isinstance(ret, dict):
                ret['qubits'] = tuple(qubits)
                return ret
            else:
                raise Exception(f"gate {name} of {qubits} not calibrated.")
        else:
            for qlist in permutations(qubits):
                try:
                    ret = self.query(f"gate.{name}.{'_'.join(qlist)}")
                    if isinstance(ret, dict):
                        ret['qubits'] = tuple(qlist)
                        return ret
                except:
                    break
            raise Exception(f"gate {name} of {qubits} not calibrated.")

    def export(self):
        return copy.deepcopy(self.__driver.dct)

    @functools.lru_cache(maxsize=1024)
    def _getGateConfig(self, name, *qubits, type=None) -> GateConfig:
        return super()._getGateConfig(name, *qubits, type=type)
