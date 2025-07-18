from copy import deepcopy

import numpy as np


class Quantity(object):

    def __init__(self, name: str, value=None, ch: int = 0, unit: str = ''):
        self.name = name
        self.isglobal, _ch = (True, 'global') if not ch else (False, ch)
        self.default = dict(value=value, unit=unit, ch=_ch)

    def __repr__(self):
        return f'Quantity({self.name})'


class VisaQuantity(Quantity):
    def __init__(self, name, value=None, unit='', ch=None,
                 get_cmd='', set_cmd='', type=None,):
        super().__init__(name, value, ch, unit)
        self.set_cmd = set_cmd
        self.get_cmd = get_cmd
        self.type = type

    def _process(self, value):
        '''process the value query from Instrument before final return'''
        return value

    def _formatGetCmd(self, **kw):
        '''format the get_cmd'''
        _kw = deepcopy(self.default)
        _kw.update(**kw)
        return self.get_cmd % dict(**_kw)

    def _pre_formatSetCmd(self, **kw):
        '''process the dict before formatSetCmd'''
        return kw

    def _formatSetCmd(self, value, **kw):
        '''format the set_cmd'''
        _kw = deepcopy(self.default)
        _kw.update(value=value, **kw)
        _kw = self._pre_formatSetCmd(**_kw)
        return self.set_cmd % dict(**_kw)


class QReal(VisaQuantity):
    def __init__(self, name, value=None, unit='', ch=None,
                 get_cmd='', set_cmd='',):
        super().__init__(name, value, unit, ch,
                         get_cmd=get_cmd, set_cmd=set_cmd, type='Real',)

    def _process(self, value):
        return float(value)


class QInteger(VisaQuantity):
    def __init__(self, name, value=None, unit='', ch=None,
                 get_cmd='', set_cmd='',):
        super().__init__(name, value, unit, ch,
                         get_cmd=get_cmd, set_cmd=set_cmd, type='Integer',)

    def _process(self, value):
        return int(value)

    def _pre_formatSetCmd(self, **kw):
        kw['value'] = int(kw['value'])
        return kw


class QBool(VisaQuantity):
    def __init__(self, name, value=None, unit='', ch=None,
                 get_cmd='', set_cmd='',):
        super().__init__(name, value, unit, ch,
                         get_cmd=get_cmd, set_cmd=set_cmd, type='Bool',)

    def _process(self, value):
        return bool(value)

    def _pre_formatSetCmd(self, **kw):
        kw['value'] = bool(kw['value'])
        return kw


class QString(VisaQuantity):
    def __init__(self, name, value=None, unit='', ch=None,
                 get_cmd='', set_cmd='',):
        super().__init__(name, value, unit, ch,
                         get_cmd=get_cmd, set_cmd=set_cmd, type='String',)

    def _process(self, value):
        return value.strip("\n\"' \r")


class QOption(VisaQuantity):
    def __init__(self, name, value=None, unit='', ch=None, options=[],
                 get_cmd='', set_cmd='',):
        super().__init__(name, value, unit, ch,
                         get_cmd=get_cmd, set_cmd=set_cmd, type='Option',)
        self.options = dict(options)
        _opts = {}
        for k, v in self.options.items():
            _opts[v] = k
        self._opts = _opts

    def _process(self, value):
        _value = value.strip("\n\"' \r")
        value = self._opts[_value]
        return value

    def _pre_formatSetCmd(self, **kw):
        assert kw['value'] in self.options.keys(), 'Not Find option: %s !' % kw['value']
        kw['option'] = self.options.get(kw['value'])
        return kw


class QVector(VisaQuantity):
    def __init__(self, name, value=None, unit='', ch=None,
                 get_cmd='', set_cmd='',):
        super().__init__(name, value, unit, ch,
                         get_cmd=get_cmd, set_cmd=set_cmd, type='Vector',)

    def _process(self, value):
        value = np.asarray(value)
        return value


class QList(VisaQuantity):
    def __init__(self, name, value=None, unit='', ch=None,
                 get_cmd='', set_cmd='',):
        super().__init__(name, value, unit, ch,
                         get_cmd=get_cmd, set_cmd=set_cmd, type='List',)


def newcfg(quantlist=[], CHs=[]):
    '''generate a new config'''
    config = {}
    for q in deepcopy(quantlist):
        _cfg = {}
        _default = dict(value=q.default['value'], unit=q.default['unit'])
        for i in CHs:
            _cfg.update({i: deepcopy(_default)})
        if q.isglobal:
            _cfg.update({'global': deepcopy(_default)})
        config.update({q.name: _cfg})
    return config
