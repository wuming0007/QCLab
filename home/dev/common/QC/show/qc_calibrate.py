import os
import sys
project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_path+r'\lib')
from logging_util import logger

project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_path+r'\calibrate_lib')
from da_calibrate import DACalibrate
from iqmixer_calibrate import IQMixerCalibrate


import json
ca = DACalibrate()
iqmixer = IQMixerCalibrate()


def calibrate(cal_json):
    ret = 0
    cal_dict = json.loads(cal_json)
    print(cal_dict)
    # try:
    for k, v in cal_dict.items():
        for session_id, params in v.items():
            logger.info(f'[{session_id}]|BEGAIN#{k}')
            func = getattr(ca, k, None)
            if func is None:
                func = getattr(iqmixer, k)
            ret = func(session_id=session_id, params=params)
            if ret != 0:
                logger.error(f'[{session_id}]|{k} failure, ret:[{ret}] .')
            else:
                logger.error(f'[{session_id}]|{k} success .')
            logger.info(f'[{session_id}]|END#{k}#{ret}')
    # except Exception as e:
    #     ret = -1
    #     logger.error(f'[{session_id}]|err_msg:[{e}]')
    #     logger.info(f'[{session_id}]|END#{k}#{ret}')
    return ret


def da_init(da_id, da_ip, channel_id, session_id):
    cal_dict = {}
    params1 = {}
    session_dict1 ={}
    params1['da_id'] = da_id
    params1['da_ip'] = da_ip
    params1['channel_id'] = channel_id
    session_dict1[session_id] = params1
    cal_dict['da_init'] = session_dict1
    cal_json = json.dumps(cal_dict)
    calibrate(cal_json)


def da_gain_calibrate(da_id, da_ip, channel_id, avo_id, avo_ip, session_id):
    cal_dict = {}
    target_voltage = 1.28
    params2 = {}
    session_dict2 ={}
    params2['da_id'] = da_id
    params2['da_ip'] = da_ip
    params2['channel_id'] = channel_id
    params2['target_voltage'] = target_voltage
    params2['avo_id'] = avo_id
    params2['avo_ip'] = avo_ip
    session_dict2[session_id] = params2
    cal_dict['gain_calibrate'] = session_dict2
    cal_json = json.dumps(cal_dict)
    calibrate(cal_json)


def da_offset_calibrate(da_id, da_ip, channel_id, avo_id, avo_ip, session_id):
    cal_dict = {}
    target_code = 0
    params3 = {}
    session_dict3 = {}
    params3['da_id'] = da_id
    params3['da_ip'] = da_ip
    params3['channel_id'] = channel_id
    params3['target_code'] = target_code
    params3['avo_id'] = avo_id
    params3['avo_ip'] = avo_ip
    session_dict3[session_id] = params3
    cal_dict['offset_calibrate'] = session_dict3
    cal_json = json.dumps(cal_dict)
    calibrate(cal_json)


def da_temperature_dependence(da_id, da_ip, channel_id, temp_sample_count, temp_sample_interval, avo_id, avo_ip, session_id):
    cal_dict = {}
    params4 = {}
    session_dict4 = {}
    params4['da_id'] = da_id
    params4['da_ip'] = da_ip
    params4['channel_id'] = channel_id
    params4['temp_sample_count'] = temp_sample_count
    params4['temp_sample_interval'] = temp_sample_interval
    params4['avo_id'] = avo_id
    params4['avo_ip'] = avo_ip
    session_dict4[session_id] = params4
    cal_dict['temperature_dependence'] = session_dict4
    cal_json = json.dumps(cal_dict)
    calibrate(cal_json)


def da_dnl_inl(da_id, da_ip, channel_id, dnl_inl_repeat_count, avo_id, avo_ip, session_id):
    cal_dict = {}
    params5 = {}
    session_dict5 = {}
    params5['da_id'] = da_id
    params5['da_ip'] = da_ip
    params5['channel_id'] = channel_id
    params5['dnl_inl_repeat_count'] = dnl_inl_repeat_count
    params5['avo_id'] = avo_id
    params5['avo_ip'] = avo_ip
    session_dict5[session_id] = params5
    cal_dict['dnl_inl'] = session_dict5
    cal_json = json.dumps(cal_dict)
    calibrate(cal_json)


def iqmixer_zero_calibrate(da_id, da_ip, channel_i, channel_q, lo_power, lo_freq, mws_id, mws_port, mws_address, spa_id, spa_address, bounds, simplex, session_id):
    cal_dict = {}
    params1 = {}
    session_dict6 = {}
    params1['da_id'] = da_id
    params1['da_ip'] = da_ip
    params1['channel_i'] = channel_i
    params1['channel_q'] = channel_q
    params1['lo_power'] = lo_power
    params1['lo_freq'] = lo_freq
    params1['mws_id'] = mws_id
    params1['mws_address'] = mws_address
    params1['mws_port'] = mws_port
    params1['spa_id'] = spa_id
    params1['bounds'] = bounds
    params1['simplex'] = simplex
    params1['spa_address'] = spa_address
    session_dict6[session_id] = params1
    cal_dict['zero_calibration'] = session_dict6
    cal_json = json.dumps(cal_dict)
    calibrate(cal_json)


def iqmixer_sideband_calibration(da_id, da_ip, channel_i, channel_q, lo_power, lo_freq, mws_id, mws_address, mws_port, spa_id, spa_address, spa_amp, spa_freq, bounds, simplex, session_id):
    cal_dict = {}
    params1 = {}
    session_dict7 ={}
    params1['da_id'] = da_id
    params1['da_ip'] = da_ip
    params1['channel_i'] = channel_i
    params1['channel_q'] = channel_q
    params1['lo_power'] = lo_power
    params1['lo_freq'] = lo_freq
    params1['mws_id'] = mws_id
    params1['mws_address'] = mws_address
    params1['mws_port'] = mws_port
    params1['spa_id'] = spa_id
    params1['spa_address'] = spa_address
    params1['spa_amp'] = spa_amp
    params1['spa_freq'] = spa_freq
    params1['bouns'] = bounds
    params1['simplex'] = simplex
    session_dict7[session_id] = params1
    cal_dict['sideband_calibration'] = session_dict7
    cal_json = json.dumps(cal_dict)
    calibrate(cal_json)


if __name__ == '__main__':

    da_id = 'QF10K4N0016'
    da_ip = '10.0.200.74'
    # da_id = 'F135'
    # da_ip = '10.0.5.135'
    channel_i = 3
    channel_q = 4
    lo_power = [22]
    # lo_freq = [4.5e9, 5.5e9, 6.5e9]
    lo_freq = [5.5e9]
    mws_id = 'MWS_Sinolink_009'
    mws_address = '10.0.1.245'
    mws_port = 2000
    spa_id = 'spa_001'
    spa_address = '10.0.0.101'
    session_id = '000001_USTCF215_1_da_init_202004141500398'
    spa_amp = [15000]
    spa_freq = [3e8]
    bounds = 4000
    simplex = -2000

    avo_id = 'avo001'
    avo_ip = '10.0.254.68'

    # 初始化DA
    da_init(da_id, da_ip, channel_i, session_id)

    # 增益校准
    # da_gain_calibrate(da_id, da_ip, channel_i, avo_id, avo_ip, session_id)

    # 偏置校准
    # da_offset_calibrate(da_id, da_ip, channel_i, avo_id, avo_ip, session_id)

    # 增益-温度关系测试
    # da_temperature_dependence(da_id, da_ip, channel_i, 30, 1, avo_id, avo_ip,
    #                           session_id)

    # dnl/inl测试
    # da_dnl_inl(da_id, da_ip, channel_i, 1, avo_id, avo_ip, session_id)

    # LO泄漏矫正
    # iqmixer_zero_calibrate(da_id, da_ip, channel_i, channel_q, lo_power, lo_freq, mws_id, mws_port, mws_address,
    #                        spa_id, spa_address, bounds, simplex, session_id)
    # #
    # time.sleep(60)
    # 镜像边带矫正
    # iqmixer_sideband_calibration(da_id, da_ip, channel_i, channel_q, lo_power, lo_freq, mws_id, mws_address,
    #                              mws_port, spa_id, spa_address, spa_amp, spa_freq, bounds, simplex, session_id)

