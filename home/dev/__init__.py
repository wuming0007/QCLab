"""本模块存放所有设备的驱动
1、所有驱动继承自BaseDriver，类名统一为Driver，并要求实现open/close/read/write四个方法。样板见VirtualDevice
2、所有厂家提供的底层库，均放于driver/common内，各自新建文件夹分别放置


为避免IP地址冲突，采取以下IP段分配方案：
设备IP地址前两段为192.168
第三段分配如下（子网掩码均为255.255.255.0）：
101：示波器，如192.168.101.10，共254 # os
102：频谱仪，如192.168.102.10，共254 # sa
103：网分，如192.168.103.10，共254 # na
104-106：墨方，如192.168.105.10，共254*3 # mf
107-109：六合，如192.168.108.10，共254*3 # lh
110：泰克，如192.168.110.110，共254 # tk
111-115：耐数，如192.168.112.10，共254*5 # ns
116-120：芯跳(ChipQ)，如192.168.117.10，共254*5 # xt
121-125：中微达，如192.168.122.10，共254*5 # zw
126-127：微波源

199：其他设备 # ot

"""
# 重要提示：所有结尾.1的ip用于电脑设置，包括192.168.101.1，192.168.108.1
# 重要提示：所有结尾.1的ip用于电脑设置，包括192.168.101.1，192.168.108.1
# 重要提示：所有结尾.1的ip用于电脑设置，包括192.168.101.1，192.168.108.1

import json
import sys
import zipfile
from pathlib import Path

import requests

try:
    root = Path(__file__).parents[1]

    # with open(root/'etc/bootstrap.json') as f:
    #     ext = json.loads(f.read())['extentions']

    # for module, file in ext['modules'].items():
    #     driver = root / f'dev/zipped/{file}'
    #     driver.parent.mkdir(exist_ok=True, parents=True)

        # if not driver.exists():
        #     location = f"{ext['server']}/packages/dev/{file}"
        #     print(f'Trying to download driver from {location}')
        #     resp = requests.get(location)

        #     with open(driver, 'wb') as f:
        #         f.write(resp.content)
        #         print(f'{location} saved to {driver}')

            # with zipfile.ZipFile(driver) as f:
            #     for zf in f.filelist:
            #         if not zf.filename.startswith(('__MAC', 'dev/__init__')):
            #             # print(zf.filename)
            #             f.extract(zf, driver.parent)

            # if str(driver) not in sys.path:
            #     sys.path.append(str(driver))

    URL = "https://gitee.com/quarkstudio/iptable/edit/master/iptable.json"
except Exception as e:
    print('failed to init dev', e)
