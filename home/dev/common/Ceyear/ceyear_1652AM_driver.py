
import ctypes
import os
import sys
import time
from pathlib import Path

import numpy as np

dll_PCIE_file = Path(__file__).parent/'CyPcieDmaDll.dll'
dll_ModuTimer_file = Path(__file__).parent/'DrvModuTimer.dll'

dll_PCIE = ctypes.cdll.LoadLibrary(str(dll_PCIE_file))
dll_ModuTimer = ctypes.cdll.LoadLibrary(str(dll_ModuTimer_file))


class Ceyear_1652AM_Driver():
    
    #def __init__(self,name,value_ex,board,channel=0):

    def openAWG(self):
        # 打开设备，执行初始化操作        
        
        # int        TimingBoard_Init (int *pNumBoard, DWORD *pdwBufErr, int *psDlyDSTARA); 
        # int        AWGBoard_Init (int *pNumBoard,      DWORD *pdwBufErr, int *psDlyDACCLK);
        # void       TimingBoard_SyncPulse          (int indexDev);
        # int        AWGBoard_Deinit        (int numOfBoardTimer, DWORD *pdwBufErr)
        # =============================== 初始化 ==================================== #
        # =============================== 初始化 ==================================== #
        # =============================== 初始化 ==================================== #

        # -----------各槽位延时数据导入-------------- #  
        file = open('C:\\7110B\\Slot_Dly_Config.bin','rb')
        temp_AllSlotStatus = file.read()   # 读出的为bytes类型
        file.close()

        slotHaveBad_add = 0;  idHaveBad_add = 4;  psClkDly_add = 8;  
        psTrigDly_add = 12;  trigsel_add = 16 # 每个int 4字节

        psDlyDSTARA = np.zeros((1,17))
        psDly7110B = np.zeros((1,17))
        oneSlotLen = 5*4 # bytes

        AllSlotStatus = np.zeros((5,16),dtype = int)    # slot0 (slotHaveBad,idHaveBad, psClkDly,psTrigDly,trigsel)
                                            # slot1 (slotHaveBad,idHaveBad, psClkDly,psTrigDly,trigsel)
                                            # ...   
        for k in np.arange(16):  
            slotHaveBad_x = temp_AllSlotStatus[oneSlotLen*k+slotHaveBad_add:oneSlotLen*k+slotHaveBad_add+4]
            idHaveBad_x = temp_AllSlotStatus[oneSlotLen*k+idHaveBad_add:oneSlotLen*k+idHaveBad_add+4] 
            psClkDly_x = temp_AllSlotStatus[oneSlotLen*k+psClkDly_add:oneSlotLen*k+psClkDly_add+4]       #（-360——360）
            psTrigDly_x = temp_AllSlotStatus[oneSlotLen*k+psTrigDly_add:oneSlotLen*k+psTrigDly_add+4]    #（-360——360）
            trigsel_x = temp_AllSlotStatus[oneSlotLen*k+trigsel_add:oneSlotLen*k+trigsel_add+4]          #(0——7，9——16)

            AllSlotStatus[0][k] = int.from_bytes(slotHaveBad_x, byteorder = "little",signed=True)
            AllSlotStatus[1][k] = int.from_bytes(idHaveBad_x, byteorder = "little",signed=True)
            AllSlotStatus[2][k] = int.from_bytes(psClkDly_x, byteorder = "little",signed=True)
            AllSlotStatus[3][k] = int.from_bytes(psTrigDly_x, byteorder = "little",signed=True)
            AllSlotStatus[4][k] = int.from_bytes(trigsel_x, byteorder = "little",signed=True)

            m = AllSlotStatus[4][k]
            if m >=0 & m <=16:      
                psDlyDSTARA[0,m] = AllSlotStatus[3][k] 

            n = AllSlotStatus[0][k]
            if n == 1 :     
                idHaveBad_x_x = AllSlotStatus[1][k]
                psDly7110B[0,idHaveBad_x_x] = AllSlotStatus[3][k]
        
        # -----------初始化定时器-------------- #  

        g_numOfBoardTimer = ctypes.c_int(0)
        dwBufErr_timer = ctypes.c_ulong(100)
        psDlyDSTARA_ptr = psDlyDSTARA.ctypes.data_as(ctypes.c_char_p)
        init_Timmer = dll_ModuTimer.TimingBoard_Init(ctypes.byref(g_numOfBoardTimer),ctypes.byref(dwBufErr_timer),psDlyDSTARA_ptr)

        # -----------初始化AWG -------------- #
        # init_AWG 为返回的错误ID
        g_numOfBoardAWG = ctypes.c_int(0)
        dwBufErr_7110B = ctypes.c_ulong(100)
        psDly7110B_ptr = psDly7110B.ctypes.data_as(ctypes.c_char_p)
        init_AWG = dll_ModuTimer.AWGBoard_Init(ctypes.byref(g_numOfBoardAWG),ctypes.byref(dwBufErr_7110B),psDly7110B_ptr)


        
        # -----------同步所有AWG-------------- #
        time.sleep(0.5)
        dll_ModuTimer.TimingBoard_SyncPulse(0)
        time.sleep(0.8)

        # -----------deinit AWG-------------- #
        # deinit_AWG 返回的错误ID
        deinit_AWG = dll_ModuTimer.AWGBoard_Deinit (g_numOfBoardAWG, ctypes.byref(dwBufErr_7110B))
        

    def closeAWG(self):
        # 关闭设备
        dll_ModuTimer.AWGBoard_CloseApp()

    def setAWG(self,name,value_ex,board=0,channel=1,pretreat='NULL',downTimes=1,triggerTimes=0):
        # 设置设备参数，对设备进行控制
        # name：设备属性名
        #       "Waveform" | "Amplitude" | "Offset" | "Output" |"TriggerType" | "WaveTypeSel"
        #       "TriggerTime" | "Impedence" |"CoupleType"
        # value_ex: 设备属性值
        #       "Waveform"  -->     tuple    (data,pretreat,times)  1D np.ndarray  in (-1,1)
        #       "Amplitude" -->     float
        #       "Offset"    -->     float
        #       "Output"    -->     bool   
        #       TriggerType  -->     "NULL" | "TIMING" | "SINGLE" | "SINGLE_OR_USER" 
        #       "WaveTypeSel"   -->  "Arb" | "Func"
        #       "TriggerTime"    --> list(doulbe)  value_ex[0] 触发间隔(s)   value_ex[1] 循环次数
        #       "Impedence"     --> int 0 50Ω | 1  1MΩ
        #       "CoupleType"    --> "DC"  |"AC" |"DAC"
        # board:板卡号      0|1|2|3...
        # channel:通道号    1|2|3|4
        

        if (name == "Waveform"):    
            # value_ex : tuple    (data,pretreat,downTimes)  
            #                   data-->1 D np.ndarray  in (-1,1)
            #                   pretreat: "NULL" | "HEAD" | "LAST" | "HEADLAST"| "ALL" | 
            #                   downTimes ：int
            # self.ArbStartSet(board,channel)       
            self.DownloadWaveOneSeqStart(pretreat,board)
            self.downSeqence_double(value_ex,downTimes,board)  # 下载波形
            # dll_ModuTimer.AWGBoard_DownloadEnd(board,channel)
            # dll_ModuTimer.AWGBoard_ArbChlRunCE(board, channel, 1)
            # dll_ModuTimer.AWGBoard_ArbGlobalRunCE (board,1)   # 开启全局触发
            


        elif(name == "Amplitude"):
            #   幅度设置 value_ex 
            dll_ModuTimer.AWGBoard_SetFourAmpl(board,ctypes.c_double(value_ex))
            return 1

        elif(name == "Offset"): 
            # 偏置设置，value_ex 单位 V  
            channel = 1<<(channel -1)# 右移操作
            dll_ModuTimer.AWGBoard_SetAmplDCOFT(board, channel,ctypes.c_double(value_ex))

        elif(name == "Output"):
            # 通道打开或者关闭         

            channel = 1<<(channel -1)# 右移操作
            dll_ModuTimer.AWGBoard_ArbChlRunCE(board,channel,value_ex)   # 任意波模式使能开关
            dll_ModuTimer.AWGBoard_EnableChlOutput(board,channel,value_ex)
            return 1
        elif(name == "WaveTypeSel"):
            # AWG模式选择，value_ex：Arb--> 任意波模式    Func --> 函数模式

            channel = 1<<(channel -1)# 右移操作
            if (value_ex == "Arb"):        # 任意波模式
                dll_ModuTimer.AWGBoard_WaveTypeSel(board,channel,0) 
            elif(value_ex == "Func"):      # 函数模式
                dll_ModuTimer.AWGBoard_WaveTypeSel(board,channel,1) 

        elif(name == "FuncWave"):
            channel = 1<<(channel -1)# 右移操作
            # 函数波形
            # AWGBoard_FuncFreq   (int indexDev, int multi_chl, double freq);
            # AWGBoard_FuncFirstPhase (int indexDev, int multi_chl, double firstphase);
            # AWGBoard_FuncTypeSel                     (int indexDev, int multi_chl, int sel)
            dll_ModuTimer.AWGBoard_WaveTypeSel(board,channel,1)
            dll_ModuTimer.AWGBoard_FuncTypeSel(board,channel,1)
            dll_ModuTimer.AWGBoard_FuncFreq(board,channel,10000000)
            dll_ModuTimer.AWGBoard_FuncFirstPhase(board,channel,0)    
            dll_ModuTimer.AWGBoard_FuncCE(board,channel,1)

        elif(name == "ArbGlobalRunCE"):    
            # 全局出发打开  value_ex 0 关闭，  1 打开
             dll_ModuTimer.AWGBoard_ArbGlobalRunCE (board,value_ex) 

        elif(name == "TriggerType"):
            # 触发类型选择
            # TriggerType : NULL             触发关闭  
            #              TIMING           等间隔触发
            #              SINGLE           单次触发
            #              SINGLE_OR_USER   用户触发   
            if (value_ex == "NULL"):   
                dll_ModuTimer.TimingBoard_SelTrig_NULL(board)
            elif (value_ex == "TIMING"):
                dll_ModuTimer.TimingBoard_SelTrig_TIMING(board)         # 循环触发
            elif (value_ex == "SINGLE"):
                dll_ModuTimer.TimingBoard_SelTrig_SINGLE(board)
            elif (value_ex == "SINGLE_OR_USER"):
                dll_ModuTimer.TimingBoard_SelTrig_SINGLE_OR_USER(board)
            else:
                print("所设置的触发类型不存在")

        elif(name == "TriggerTime"):
            # TriggerType 为 TIMING 情况下设置触发间隔和触发次数
            # value_ex[0]：单位s;      value_ex[1]:次数
            dll_ModuTimer.TimingBoard_ConfigTrig_TIMING  (ctypes.c_double(value_ex), board)               # 触发间隔
            dll_ModuTimer.TimingBoard_ConfigTrig_LOOP_N_TIMES(int(triggerTimes),board)            # 触发次数
        
        elif(name == "Impedence"):
            # 输出阻抗控制value_ex: 0-->50Ω，1-->1MΩ
            dll_ModuTimer.AWGBoard_SelFourOhm (board,value_ex)

        elif(name == "CoupleType"):  
            # 耦合方式选择 
            if value_ex =="DC":
                dll_ModuTimer.AWGBoard_SelFourCoupleType (board,0)
            elif value_ex =="AC":
                dll_ModuTimer.AWGBoard_SelFourCoupleType (board,1)
            elif value_ex =="DAC":
                dll_ModuTimer.AWGBoard_SelFourCoupleType (board,2)
            else:
                print("所选择的耦合方式不存在")

        elif(name == "ArbDelay"):
            # 通道延时控制，value_ex ：s    in 303ns~3us 
            channel = 1<<(channel -1)# 右移操作
            dll_ModuTimer.AWGBoard_ArbDelay(board,channel, ctypes.c_double(value_ex))

        else:
            print(name+"不是该设备属性")

    def getAWG(self):
        pass
    

    def ArbStartSet(self,board,channel):    
        channel = 1<<(channel -1)# 右移操作
       # dll_ModuTimer.AWGBoard_WaveTypeSel(board,channel,0)                     # 设置为任意波输出模式
       # dll_ModuTimer.AWGBoard_ArbGlobalRunCE (board,0)                         # 关闭全局触发
       # dll_ModuTimer.AWGBoard_SelArbSampleRate (board,channel,1200000000)      # 配置采样率
        dll_ModuTimer.AWGBoard_DownloadStart(board,channel)


    def DownloadWaveOneSeqStart(self,pretreat,board):
        # pretreat: "NULL" | "HEAD" | "LAST" | "HEADLAST"| "ALL" | 
        if pretreat == "NULL":
            dll_ModuTimer.AWGBoard_DownloadWaveOneSeqStart(board,0)  # 不进行预处理
        elif pretreat == "HEAD":
            dll_ModuTimer.AWGBoard_DownloadWaveOneSeqStart(board,1)  # 波形起始位置处理
        elif pretreat == "LAST":
            dll_ModuTimer.AWGBoard_DownloadWaveOneSeqStart(board,2)  # 波形起始结尾位置处理
        elif pretreat == "HEADLAST":
            dll_ModuTimer.AWGBoard_DownloadWaveOneSeqStart(board,3)  # 收尾均进行处理
        elif pretreat == "ALL":
            dll_ModuTimer.AWGBoard_DownloadWaveOneSeqStart(board,4)  # 所有数据点处理（针对脉冲）
    def downSeqence_double(self,data,count,board):
        # ******************************************************************** #
        # 函数功能：装载波形数据
        #       data            :   数据序列 -1<= data <=1, 1维numpy矩阵
        #       count           ：   播放次数。
        # data_list = list(data)
        numOneseg = 20000                # 每段波形采样点
        len_data = len(data)
        segNum = len_data // numOneseg          # 采样点数据分的段数
        segMod = len_data % numOneseg           # 分段后剩余的采样点数
        if len_data % 2 != 0:       # 是否为偶数个元素，如果不是补1个0
            np.append(data,0)
            len_data = len_data +1

        #  --------------整数段波形下载----------------------
        if segNum !=0:
            for k in range(segNum):
                temp = data[numOneseg*k : numOneseg*k + numOneseg]
                temp_ptr = temp.ctypes.data_as(ctypes.c_char_p)
                dll_ModuTimer.AWGBoard_DownloadWaveOneSeqNormal_double (board, temp_ptr,numOneseg)        # 装载该段数据
                # print(k)
        # ------------------ 剩余数据段下载 ------------------
        if segMod != 0:
            temp = data[numOneseg*(segNum) : numOneseg*(segNum) + segMod]
            temp_ptr = temp.ctypes.data_as(ctypes.c_char_p)
            
            dll_ModuTimer.AWGBoard_DownloadWaveOneSeqNormal_double (board,temp_ptr,segMod) 

        #import time
        #time.sleep(0.001)
        dll_ModuTimer.AWGBoard_DownloadWaveOneSeqEnd(board,count)             # 该段数据装载完成


    def ArbEndSet(sef,board,channel):
        channel = 1<<(channel -1)# 右移操作

        dll_ModuTimer.AWGBoard_DownloadEnd(board,channel)
        dll_ModuTimer.AWGBoard_ArbChlRunCE(board, channel, 1)
        dll_ModuTimer.AWGBoard_ArbGlobalRunCE (board,1)   # 开启全局触发
    

    def light_shining(self,board):  
        # 控制板卡闪灯
        dll_ModuTimer.AWGBoard_LED_Light(board,ctypes.c_int(1))
        time.sleep(0.5)
        dll_ModuTimer.AWGBoard_LED_Light(board,ctypes.c_int(0))
        time.sleep(0.5)
        dll_ModuTimer.AWGBoard_LED_Light(board,ctypes.c_int(1))
        time.sleep(0.5)
        dll_ModuTimer.AWGBoard_LED_Light(board,ctypes.c_int(0))
        time.sleep(0.5)
        dll_ModuTimer.AWGBoard_LED_Light(board,ctypes.c_int(1))
        time.sleep(0.5)
        dll_ModuTimer.AWGBoard_LED_Light(board,ctypes.c_int(0))

# %%
