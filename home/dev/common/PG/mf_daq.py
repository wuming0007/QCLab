# coding=utf-8
import time
import numpy as np
import os
# import mf_board as mf_board
from . import mf_board as mf_board

class mf_daq(mf_board.board):
    """[base adc hardware define, surport basic reg operate]
       reg define:
        0x40	SAMPLES_PER_FRAME	每次触发采集的采样点数，SAMPLE_MODE为1时有效	读写
        0x44	SAMPLE_MODE	采集模式：0连续，1触发	读写
        0x48	SAMPLE_FRAME_LIMIT 	预期采集的帧数	读写
        0x4C	SAMPLE_FALSE_DATA 	采集的数据用假数据替代	读写
        0x50	START_SAMPLE 	采集控制，上升沿使能采集，下降沿停止采集	读写
        0x54	FRAMES_GOT  	已采集帧数	只读
        0x58	SAMPLES_GOT	已采集采样点数	只读
        0x60	RAW_DATA_DDR_ADDR	原始数据在DDR的存储起始地址	读写
        0x64	ALG_DATA_DDR_ADDR	算法数据在DDR的存储起始地址	读写
        0x68	FLUSH_DATA	刷新数据，在采集结束时，已采集数据可能没有完全存入DDR，需要强制flush	只写
        自清零
        0x70	SAMPLE_DELAY0 	触发模块延时1	
        0x74	SAMPLE_DELAY1 	触发模块延时2	
        0x78	SAMPLE_DELAY2 	触发模块延时3	
        0x7C	SAMPLE_DELAY3 	触发模块延时4	
        0x80	JESD_STATUS	jesd模块状态	
    """    
    def __init__(self):
        super().__init__(dev_type = 'ADC')
        self.ad_module_idx = 0x60
        self.alg_module_idx = 0x90
        self.spi_module_idx = 0x11
        self.frame_cnt = 1000
        self.frame_size = 1024
        self.trig_mode = 1
        self.mode = 'raw'
        self.sample_false = False
        ## sample delay set for adc
        ## support upto 4 sample delay set
        self.frequency = 1e9
        self.samples_per_clk = 4
        self.adc_trig_delays = None
        self.soft_version = 1.1
        self.bytes_data = None
        self.mixerTable = None
        self.alg_num = 0  # 使能算法模块数
        self.triggerTable = None
        self.raw_data_ddr_addr = 0
        self.raw_data_space    = 0x40000000
        self.alg_data_ddr_addr = self.raw_data_space
        self.alg_data_space = 16<<20  # every alg data occupated space
        self.coef_data_ddr_addr = 0x60000000
        self.coef_data_space = 16<<20  # every coef data occupated space

    def connect(self, ip, client=None):
        super().connect(ip, client)
        self.set_adc_trig_delays([0,])
        self._get_alg_num()
        # self.setRawDataAddr()
        # self.setAlgDataAddr()

    def _get_alg_num(self):
        '''获取ADC中使能的算法模块个数，防止设备例化后，客户不想重复设置算法系数
        '''
        _reg = self.read_regs([[self.alg_module_idx, 0x2f<<2, 0]])[0] # 使能多少个算法通道
        alg_num = 0
        while _reg > 0:
            alg_num += 1
            _reg = _reg >> 1
        self.alg_num = alg_num >> 1
        
    def set_adc_trig_delays(self, delay):
        """[set upto 4 different adc trig dalay]
        when trig is comming, len(delay) of trig will output
        first trig1 is delay delay[0] ns from input trig
        second trig2 is delay delay[1] ns relative to trig1 (len(delay) >= 2)
        second trig3 is delay delay[2] ns relative to trig2 (len(delay) >= 3)
        second trig4 is delay delay[3] ns relative to trig3 (len(delay) == 4)

        Arguments:
            delay {[list]} -- [adc dalays to be set]
            
        """
        assert 1 <= len(delay) <= 4, 'len(delay):%s is not in 1,2,3,4'%len(delay)
        _delays = [0]*4
        for idx, _d in enumerate(delay):
            assert 0 <= _d < 250e-6, 'relative sapmle delay range is [0, 250000 ns]'
            val = round(_d*2.5e8) # clock frequency is 250MHz, int -> round
            _delays[idx] = val + 1 # add 4ns (1 clock)
            print('sample delay relative to trigger %s is set to :%s ns, command is set to %s ns'%(idx+1,val*4,round(_d*1e9)))
        for idx, _d  in enumerate(_delays): ## reg addr is 8,9,a,b
            self.set_sample_delay(_d, idx)
        self.adc_trig_delays = delay

    def set_adc_trig_delay_clocks(self, delay):
        """[set upto 4 different adc trig dalay]
        when trig is comming, len(delay) of trig will output
        first trig1 is delay delay[0] ns from input trig
        second trig2 is delay delay[1] ns relative to trig1 (len(delay) >= 2)
        second trig3 is delay delay[2] ns relative to trig2 (len(delay) >= 3)
        second trig4 is delay delay[3] ns relative to trig3 (len(delay) == 4)

        Arguments:
            delay {[list]} -- [adc dalays to be set]
            
        """
        assert 1 <= len(delay) <= 4, 'len(delay):%s is not in 1,2,3,4'%len(delay)
        for idx, _d in enumerate(delay):
            assert 0 <= _d < 62500, 'relative sapmle delay range is [0, 250000 ns]'
            val = round(_d) # int -> round
            self.set_sample_delay(val + 1, idx)
            print('sample delay relative to trigger %s is set to :%s ns'%(idx+1,val*4))
        self.adc_trig_delay_clocks = delay
        self.adc_trig_delays = [delayi*4.0/1e9 for delayi in delay]
    
    def set_sample_delay(self, delay, idx):
        '''delay set to 0 will disable correspond trig'''
        self.write_regs([[self.ad_module_idx, 0x70+idx*4, delay]])

    def flush_data(self):
        # print('stop sample')
        self.start_sample(0)
        return self.write_regs([[self.ad_module_idx,0x68, 0],[self.ad_module_idx,0x68, 1],[self.ad_module_idx,0x68, 0]])

    def start_sample(self, val):
        return self.write_regs([[self.ad_module_idx,0x50, val]])

    def setRecordLength(self, recordLength=1):
        '''frame length for every frame, unit is kB'''
        self.frame_size = recordLength << 10
        # if self.trig_mode == 0:
        #     recordLength = recordLength*self.frame_cnt
        return self.write_regs([[self.ad_module_idx,0x40, self.frame_size]])

    def setFrameNumber(self, frameNum=1000):
        self.frame_cnt = frameNum
        return self.write_regs([[self.ad_module_idx,0x48, frameNum]])

    def setTriggerType(self, frame_mode=1):
        self.trig_mode = frame_mode
        return self.write_regs([[self.ad_module_idx,0x44, frame_mode]])

    def setRawDataAddr(self, addr=0):
        self.raw_data_ddr_addr = addr
    
    def setAlgDataAddr(self, addr=0x40000000):
        self.alg_data_ddr_addr = addr

    def sample_with_false_data(self, is_false_data=True):
        self.sample_false = is_false_data
        _val = 1 if is_false_data else 0
        return self.write_regs([[self.ad_module_idx,0x4c, _val]])

    def _start_alg(self):
        self.write_regs([[self.alg_module_idx,0x30<<2, 0],[self.alg_module_idx,0x30<<2, 1]])

    def startCapture(self):
        self._reset_ddr()
        # self.start_alg()
        self.adc_check()
        self.start_sample(0)
        self.start_sample(1)

    def setADCspi(self, spi_sel, addr, data):
        """[set the adc spi]
                if( cpu_op_addr == 'h00 ) begin
                    spi0_addr    <= cpu_wr_data[14:0];
                    spi0_rwn     <= cpu_wr_data[15];
                end
                if( cpu_op_addr == 'h01 )
                    spi0_wr_data[7:0] <= cpu_wr_data[7:0];
                if( cpu_op_addr == 'h03 ) begin
                    spi1_addr    <= cpu_wr_data[14:0];
                    spi1_rwn     <= cpu_wr_data[15];
                end
                if( cpu_op_addr == 'h04 )
                    spi1_wr_data[15:0] <= cpu_wr_data[15:0];
        Arguments:
            spi_sel {[u8]} -- [0,1, 0 for adc clk chip, 1 for adc chip]
            addr {[u16]} -- [spi address]
            data {[u8]} -- [spi write data]
        
        Returns:
            [u8] -- [write status]
        """
        _reg_data0 = (spi_sel*3+0 << 16) | addr
        self.write_regs([[self.spi_module_idx,0x40, _reg_data0]])
        _reg_data1 = (spi_sel*3+1 << 16) | data
        self.write_regs([[self.spi_module_idx,0x40, _reg_data1]])

    def getADCspi(self, spi_sel, addr):
        """[get the adc spi]
        
        Arguments:
            spi_sel {[u8]} -- [0,1, 0 for adc clk chip, 1 for adc chip]
            addr {[u16]} -- [spi address]
                else if( cpu_op_req && cpu_op_rwn ) begin
                    if( cpu_op_addr == 'h00 ) begin
                        cpu_rd_data[14:0]   <= spi0_addr;
                        cpu_rd_data[15]     <= spi0_rwn;
                    end
                    if( cpu_op_addr == 'h01 )
                        cpu_rd_data <= { 8'hAA, spi0_wr_data };
                    if( cpu_op_addr == 'h02 )
                        cpu_rd_data <= { 8'hAA, spi0_rd_data};

                    if( cpu_op_addr == 'h03 ) begin
                        cpu_rd_data[14:0]   <= spi1_addr;
                        cpu_rd_data[15]     <= spi1_rwn;
                    end
                    if( cpu_op_addr == 'h04 )
                        cpu_rd_data <= spi1_wr_data;
                    if( cpu_op_addr == 'h05 )
                        cpu_rd_data <= spi1_rd_data;
                end       
        Returns:
            [u8] -- [reg data]
        """
        self.write_regs([[self.spi_module_idx,0x40, (spi_sel*3+0 << 16) | addr | 0x8000]])
        self.write_regs([[self.spi_module_idx,0x40, (spi_sel*3+1 << 16) | 0]])
        self.write_regs([[self.spi_module_idx,0x40, (spi_sel*3+2 << 16) | 0]])
        ret = self.read_regs([[self.spi_module_idx,0x40, 0]])
        # print(ret)
        return ret

    def samples_got(self):
        return self.read_regs([[self.ad_module_idx,0x58, 0]])[-1]

    def frames_got(self):
        return self.read_regs([[self.ad_module_idx,0x54, 0]])[-1]
    
    def get_ID(self):
        return self.read_regs([[self.ad_module_idx,0x00, 0]])[-1]
    
    def adc_check(self):
        return
        # self.write_regs([[0x81, 0xCC, 1]])
        # return
        expect = tuple([0x3C]*4)
        regs = [[0x81, 0x830+(i*0x40), 0] for i in range(4)]
        d = self.read_regs(regs)[3::4]
        # # print(f'adc link delay is {d}')
        # return 
        try_cnt = 0
        while d != expect and try_cnt < 10:
            off = [0x004,0x008,0x00C,0x010,0x020,0x024,0x02C,0x030]
            dat = [0x1,0x1,0x1,0x10001,0x1,0x1f,0x1,0x0]
            regs = [[0x81, _off, _dat] for _off, _dat in zip(off, dat)]
            self.write_regs(regs)
            time.sleep(0.05)
            regs = [[0x81, 0x830+(i*0x40), 0] for i in range(4)]
            d = self.read_regs(regs)[3::4]
            try_cnt += 1
        if try_cnt == 10:
            print(f'read:{d}, expect:{expect}')
            self.log.critical(f"adc status isn't correct")

    def _wait_data(self, processed_cnt, alg_data=False):
        for _ in range(2000):
            self.sampled_cnt = self.frames_got() 
            if self.sampled_cnt >= self.frame_cnt:
                if self.trig_mode == 0:
                    ## 停止采数
                    self.start_sample(0)
                self.flush_data()
                if self.trig_mode == 1 and self.sampled_cnt > self.frame_cnt:
                    self.log.critical('sampled trigger count {0} is large than expected {1}'.format(self.sampled_cnt, self.frame_cnt))
                    return 0
                self.sampled_cnt = self.frame_cnt
            # self.sampled_cnt = self.frame_cnt if self.sampled_cnt > self.frame_cnt else self.sampled_cnt
            new_cnt = self.sampled_cnt-processed_cnt
            
            if new_cnt > 0:
                if alg_data:
                    return new_cnt
                new_data_size = new_cnt * self.frame_size * 4
                start_addr = (self.raw_data_ddr_addr+(processed_cnt * self.frame_size * 4)) & 0x3FFFF000
                # 溢出处理
                if start_addr+new_data_size > self.raw_data_ddr_addr+self.raw_data_space:
                    print('ADC数据量超过{0} GB'.format(((processed_cnt * self.frame_size * 4)>>30)+1))
                    new_data_size = self.raw_data_ddr_addr+self.raw_data_space - start_addr
                    new_cnt = int(new_data_size / (self.frame_size * 4))
                rd_len     = (new_data_size + 4095) & 0x3FFFF000
                # log.debug('sampled_cnt:{0}, new_cnt:{1}'.format(self.sampled_cnt, new_cnt))
                # log.debug('start_addr:{0}, rd_len:{1}'.format(start_addr, rd_len))
                if self.read_ddr(1, start_addr, rd_len):
                    return new_cnt
                return 0
            # print(f'wait {_} {self.sampled_cnt}')
            time.sleep(0.01)
        print('sampled_cnt:{0}, expected count:{1}'.format(self.sampled_cnt, self.frame_cnt))    
        print('Warning!!! no data sampled, please check if the trigger is connected')
        self.flush_data()
        return 0

    # def get_data_size(self, size_type)
    #     '''calculate the data size in different senerio'''

    def read_algdata(self, alg_num):
        """[readout onboard algorithm data]
        
        Arguments:
            alg_num {[integer]} --  [读取算法通道数，1-10]
            every freq data has maxmun memory space of 32MB
        """ 
        rd_len = (self.frame_cnt * 16 + 4095) & 0xFFF000
        for freq_idx in range(alg_num):
            start_addr = self.alg_data_ddr_addr+(freq_idx * self.alg_data_space)
            # print('read ddr', hex(start_addr))
            sta = self.read_ddr(1, start_addr, rd_len)
            if not sta:
                return False
        return True

    def get_algData(self, alg_num=1):
        """[get algrithm data from device]
        
        Arguments:
            alg_num {[integer]} -- [读取算法通道数，1-10]
            every trig will generate 8 byte i (8 byte alg i data)
            every trig will generate 8 byte q (8 byte alg q data)
        """        
        assert alg_num in range(1,11)
        self.generate_zero_copy(((self.frame_cnt * 16 + 4095) >> 10) * self.network_frame_size * alg_num)
        processed_cnt = 0
        # print('start', time.time())
        while processed_cnt < self.frame_cnt:
            new_cnt = self._wait_data(processed_cnt, alg_data=True)
            if new_cnt == 0:
                self.bytes_data = None
                self.flush_data()
                return False
            processed_cnt += new_cnt
        if self.read_algdata(alg_num):
            self.process_algdata(alg_num)
            return True
        return False
        
    def get_ts(self):
        return time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime(time.time()))

    def store_data(self, dir=None):       
        '''
        
        '''
        self.clear_udp_buf()
        store_unit_size = 8*1024
        size = self.frame_cnt * self.frame_size * 4 
        size = 100*1024*1024 if size > 100*1024*1024 else size   
        self.generate_zero_copy((size >> 10) * self.network_frame_size)
        self.sampled_cnt = 0
        processed_cnt = 0
        print('start store data at time {0}, file size unit is {1} kB'.format(self.get_ts(), store_unit_size*4))
        file_no = 0
        to_be_store_cnt = 0
        dir = './' if dir is None else f'{dir}/'
        os.mkdir(dir) if not os.path.exists(dir) else None
        f_path = os.path.join(os.getcwd(), dir)
        print(f'路径:{f_path}')
        while processed_cnt < self.frame_cnt:
            new_cnt = self._wait_data(processed_cnt, alg_data=True)
            # print(f'new_cnt: {new_cnt}')
            if new_cnt == 0:
                self.bytes_data = None
                self.flush_data()
                print('采集失败')
                return False, None
            to_be_store_cnt = new_cnt
            while to_be_store_cnt >= store_unit_size:
                # 读数据
                new_data_size = store_unit_size * self.frame_size * 4
                start_addr = self.raw_data_ddr_addr+(processed_cnt * self.frame_size * 4) & (self.alg_data_ddr_addr-1)
                rd_len     = (new_data_size + 4095) & 0xFFFFF000
                self.read_ddr(1, start_addr, rd_len)
                processed_cnt += store_unit_size
                # 写数据
                file_no += 1
                print(file_no, 'store sampled data', self.get_ts())
                with open(f'{dir}{file_no}.dat', 'wb') as f:
                    f.write(self.bytes_data[0:store_unit_size*self.network_frame_size*4])
                    self.view_start = 0
                to_be_store_cnt -= store_unit_size
            if processed_cnt + to_be_store_cnt >= self.frame_cnt:
                break
            # print(f'processed_cnt: {processed_cnt}')

        if to_be_store_cnt >0:
            file_no += 1
            print(file_no, 'store last ddr data', time.time())
            with open(f'{dir}{file_no}.dat', 'wb') as f:
                f.write(self.bytes_data[0:to_be_store_cnt*self.network_frame_size*4])
                self.view_start = 0

        if self.sample_false is not True:
            self.bytes_data = None
            self.flush_data()
            return True, f_path
        
        # analyse data or check false data
        # self.check_data(size)
        self.bytes_data = None
        return True, f_path

    def get_Data(self, lzy=False):       
        '''
        readout data from ddr memory,
        1. calculate the expected data size in bytes
        2. according to read block size , calculate the repeats to read data
        3. befor read, we should check that if the data in ddr memory is ready to be readout
        4. read out data into a shared memory
        5. check if we have left data to be readout
        6. if failed, we can reduce the read block size and try again, maxim try count is 5

        1. 检查已采集数据是否已达到最小读取字节数
        2. 读出数据，
        3. 处理数据
        边接收边处理模式下，每一次读取的数据量应该正好是触发帧数据大小的整数倍
        所有的原始数据在bytes data中，整个过程不传递数据，只传递位置
        self.mode {[str]} -- ['raw_alg', 读出的数据进行算法计算，用于算法对比，'raw',只读出并恢复出原始ADC数据]
        '''
        self.clear_udp_buf()
        size = self.frame_cnt * self.frame_size * 4    
        self.i_data = np.zeros((self.frame_cnt, self.frame_size), dtype=np.float64)
        self.q_data = np.zeros((self.frame_cnt, self.frame_size), dtype=np.float64)
        self.generate_zero_copy((size >> 10) * self.network_frame_size)
        if self.mode=='raw_alg':
            shape = self.mixerTable.shape
            frame_cnt_per_coef = int(self.frame_cnt/shape[0])
            _dtype = complex if lzy else float
            self.iqDataf = np.zeros((shape[0],shape[1],shape[2],frame_cnt_per_coef), dtype=_dtype)
            # self.qDataf = np.zeros(shape, dtype=float)
        # print(self.iDataf.shape)
        # print(self.iq_data.shape)
        self.sampled_cnt = 0
        processed_cnt = 0
        # print('start', time.time())
        while processed_cnt < self.frame_cnt:
            new_cnt = self._wait_data(processed_cnt)
            if new_cnt == 0:
                self.bytes_data = None
                self.flush_data()
                return False
            if self.mode=='raw_alg':
                if lzy is True:
                    self.process_data_lzy(processed_cnt, new_cnt)
                else:
                    self.process_data_f(processed_cnt, new_cnt)
            else:
                self.process_data(processed_cnt, new_cnt)
            processed_cnt += new_cnt

        if self.sample_false is not True:
            self.bytes_data = None
            self.flush_data()
            return True
        
        # analyse data or check false data
        self.check_data(size)
        return True
       
    def process_data_f(self, start_frame_cnt, frame_cnt):
        """[算法处理函数，对每一帧I，Q通道数据按以下公式计算]
        (I + j*Q)*(coeffi + j*coeffq)

        mixerTable(系数数据)形状：
        # 系数数据(coef_data)为IQ，IQ.shape：3维，(N,M,L)
        # N每个频点有多少组系数
        # M有多少组频点,取值范围（1，11）最多10个算法模块
        # L帧长度, (1k,2k,3k,4k,5k,6k,7k,8k) 复数 (coeffi + 1j*coeffq)
        Arguments:
            start_frame_cnt {[int]} -- [起始数据帧编号]
            frame_cnt {[int]} -- [待己算帧数]
        """        
        self.process_data(start_frame_cnt, frame_cnt)
        
        # allDataRest = self.i_data[start_frame_cnt:start_frame_cnt+frame_cnt] + 1j*self.q_data[start_frame_cnt:start_frame_cnt+frame_cnt]
        # 新接收到的数据可能需要使用多组系数进行计算
        N = self.mixerTable.shape[0]
        frame_cnt_per_coef = int(self.frame_cnt / N)
        coef_idx1 = int(np.floor(start_frame_cnt/frame_cnt_per_coef)) #
        coef_idx2 = int(np.ceil((start_frame_cnt+frame_cnt)/frame_cnt_per_coef)) #
        process_cnt_list = [frame_cnt_per_coef]*(coef_idx2-coef_idx1)
        process_cnt_list[0] = frame_cnt_per_coef- (start_frame_cnt%frame_cnt_per_coef) if len(process_cnt_list) > 1 else frame_cnt
        process_cnt_list[-1] = frame_cnt-sum(process_cnt_list[:-1])  if len(process_cnt_list) > 1 else process_cnt_list[-1]
        s_cnt = start_frame_cnt
        for cnt in process_cnt_list:
            # print(s_cnt,s_cnt+cnt, coef_idx1, frame_cnt)
            mixerTable = self.mixerTable[coef_idx1]
            allDataRest = self.i_data[s_cnt:s_cnt+cnt] + 1j*self.q_data[s_cnt:s_cnt+cnt]
            dataf = np.matmul(mixerTable, allDataRest.T)
            # dataf = np.array([np.sum(allDataRest*(mixerTable[idx][0]+1j*mixerTable[idx][1]),axis=1) for idx in range(lenCh)])
            s_cnt_in_coef = s_cnt % frame_cnt_per_coef
            self.iqDataf[coef_idx1][:,0,s_cnt_in_coef:s_cnt_in_coef+cnt] = np.real(dataf)
            self.iqDataf[coef_idx1][:,1,s_cnt_in_coef:s_cnt_in_coef+cnt] = np.imag(dataf)
            s_cnt += cnt 
            coef_idx1 += 1
    
    def process_data_lzy(self, start_frame_cnt, frame_cnt):
        """[算法处理函数，对每一帧I，Q通道数据按以下公式计算]
        I*(coeffi + j*coeffq)
        Q*(coeffi + j*coeffq)
        mixerTable(系数数据)形状：
        # 系数数据(coef_data)为IQ，IQ.shape：3维，(N,M,L)
        # N每个频点有多少组系数
        # M有多少组频点,取值范围（1，11）最多10个算法模块
        # L帧长度, (1k,2k,3k,4k,5k,6k,7k,8k), L是复数 (coeffi + j*coeffq)
        Arguments:
            start_frame_cnt {[int]} -- [起始数据帧编号]
            frame_cnt {[int]} -- [待己算帧数]
        """        
        self.process_data(start_frame_cnt, frame_cnt)
        
        # 新接收到的数据可能需要使用多组系数进行计算
        N = self.mixerTable.shape[0]
        frame_cnt_per_coef = int(self.frame_cnt / N)
        coef_idx1 = int(np.floor(start_frame_cnt/frame_cnt_per_coef)) #
        coef_idx2 = int(np.ceil((start_frame_cnt+frame_cnt)/frame_cnt_per_coef)) #
        process_cnt_list = [frame_cnt_per_coef]*(coef_idx2-coef_idx1)
        process_cnt_list[0] = frame_cnt_per_coef- (start_frame_cnt%frame_cnt_per_coef) if len(process_cnt_list) > 1 else frame_cnt
        process_cnt_list[-1] = frame_cnt-sum(process_cnt_list[:-1])  if len(process_cnt_list) > 1 else process_cnt_list[-1]
        s_cnt = start_frame_cnt

        for cnt in process_cnt_list:
            mixerTable = self.mixerTable[coef_idx1]
            # allDataRest = self.i_data[s_cnt:s_cnt+cnt] + 1j*self.q_data[s_cnt:s_cnt+cnt]
            # lenCh = len(mixerTable)
            lzy_data_i = np.matmul(mixerTable, self.i_data[s_cnt:s_cnt+cnt].T)
            lzy_data_q = np.matmul(mixerTable, self.q_data[s_cnt:s_cnt+cnt].T)
            # lzy_data_i = np.array([np.sum(self.i_data[s_cnt:s_cnt+cnt]*(mixerTable[idx][0]+1j*mixerTable[idx][1]),axis=1) for idx in range(lenCh)])
            # lzy_data_q = np.array([np.sum(self.q_data[s_cnt:s_cnt+cnt]*(mixerTable[idx][0]+1j*mixerTable[idx][1]),axis=1) for idx in range(lenCh)])
            # dataf = np.array([np.sum(allDataRest*(mixerTable[idx][0]+1j*mixerTable[idx][1]),axis=1) for idx in range(lenCh)])
            s_cnt_in_coef = s_cnt % frame_cnt_per_coef
            self.iqDataf[coef_idx1][:,0,s_cnt_in_coef:s_cnt_in_coef+cnt] = lzy_data_i
            self.iqDataf[coef_idx1][:,1,s_cnt_in_coef:s_cnt_in_coef+cnt] = lzy_data_q
            s_cnt += cnt 
            coef_idx1 += 1

    def process_data(self, start_frame_cnt, frame_cnt):
        """[恢复原始数据帧， 处理frame_cnt次触发数据，所以size应该是整数个触发的数据]
        Arguments:
            start_frame_cnt {[int]} -- [起始数据帧编号]
            frame_cnt {[int]} -- [待己算帧数]
        """        
        # network frame length：1032byte，8byte is not active data
        network_frame_cnt = round(frame_cnt*self.frame_size * 4 >> 10)
        start_pos = round(start_frame_cnt * self.frame_size * 4 *self.network_frame_size >> 10)
        end_pos = start_pos + network_frame_cnt*self.network_frame_size
        raw_data = np.frombuffer(self.bytes_data[start_pos:end_pos], dtype='i2')
        all_data1 = np.reshape(raw_data, (network_frame_cnt, 516))[:, 4:]
        all_data = np.reshape(all_data1, (frame_cnt*self.frame_size, 2))
        i_data = np.reshape(all_data[:,0], (frame_cnt, self.frame_size))
        q_data = np.reshape(all_data[:,1], (frame_cnt, self.frame_size))
        self.i_data[start_frame_cnt:start_frame_cnt+frame_cnt] = i_data
        self.q_data[start_frame_cnt:start_frame_cnt+frame_cnt] = q_data
        # self.iq_data[0,start_frame_cnt:start_frame_cnt+frame_cnt] = (i_data -9.0) * 0.0248
        # self.iq_data[1,start_frame_cnt:start_frame_cnt+frame_cnt] = (q_data -45.0)* 0.0248
    
    def process_algdata(self, alg_num):
        """[处理算法数据， 恢复每个算法通道的算法数据]
        
        Arguments:
            alg_num {[int]} -- [算法通道数]
        """                
        # network frame length：1032byte，8byte is not active data
        network_frame_cnt_per_freq = ((self.frame_cnt * 16 + 4095) & 0xFFF000) >> 10
        read_frame_cnt = network_frame_cnt_per_freq * 64 #每一帧数据里有64个算法数据
        shape = self.mixerTable.shape
        frame_cnt_per_coef = int(self.frame_cnt/shape[0])
        self.alg_iqDataf = np.zeros((shape[0], alg_num, 2, frame_cnt_per_coef), dtype=np.float64)
        for i in range(alg_num):
            start_pos = i * network_frame_cnt_per_freq * self.network_frame_size 
            end_pos   = start_pos + network_frame_cnt_per_freq * self.network_frame_size 
            raw_data = np.frombuffer(self.bytes_data[start_pos:end_pos], dtype='i8')

            all_data1 = np.reshape(raw_data, (network_frame_cnt_per_freq, 129))[:, 1:]
            all_data = np.reshape(all_data1, (read_frame_cnt, 2))
            for j in range(shape[0]):
                self.alg_iqDataf[j][i][0]=all_data[j*frame_cnt_per_coef:(j+1)*frame_cnt_per_coef,0]
                self.alg_iqDataf[j][i][1]=all_data[j*frame_cnt_per_coef:(j+1)*frame_cnt_per_coef,1]
    def _set_alg_para(self, frame_cnt=None, alg_num=1, test=False):
        """[设置算法模块参数]
        系数的长度应该和每帧波形数据长度一致
        Arguments:
            frame_cnt {[integer]} -- [每多少帧切换一次算法系数, None时用ADC的帧数输入]
            alg_num {[integer]} -- [算法通道数，1-10个]
            test {[bool]} -- [是否是测试模式, True, 测试模式， False， 真实数据]
        """            
        assert alg_num in range(1,11)
        assert frame_cnt is None or frame_cnt > 0  
        assert self.frame_size <= 8192, '使能算法模块时，最大系数长度为8k'
        _test_val = 1 if test else 0
        _frame_cnt = self.frame_cnt if frame_cnt is None else frame_cnt
        cmds = []
        alg_ch_enable = (1 << (alg_num*2)) - 1 
        cmds.append([self.alg_module_idx, 0x2f<<2, alg_ch_enable]) # 使能多少个算法通道
        cmds.append([self.alg_module_idx, 0x2b<<2, _test_val]) #1 算法结果为计数器, 算法结果为真实计算结果
        cmds.append([self.alg_module_idx, 0x2d<<2, self.frame_size*2]) #每个系数数据的字节长度
        cmds.append([self.alg_module_idx, 0x2c<<2, _frame_cnt])  # 多少帧切换一次系数
        self.write_regs(cmds)
    
    def lcm(self, a,b):
        gcd = lambda a, b: a if b == 0 else gcd(b, a % b)
        return a*b//gcd(a,b)

    def gen_iq_line(self, freq, phase=0, length=None, complex_data=False):
        """[生成给定频率和相位的IQ信号]
        
        Arguments:
            freq {[int]} -- [频率，单位Hz]
        
        Keyword Arguments:
            phase {int} -- [相位，弧度] (default: {0})
        
        Returns:
            [numpy array] -- [生成归一化的IQ信号]
        """        
        _length = self.frame_size/self.frequency if length is None else length

        s_freq = self.lcm(freq, self.frequency)
        Oversampling = int(s_freq/self.frequency)
        size = int(_length*s_freq)
        line = np.linspace(0,_length/(1/freq)*2*np.pi, size)+phase
        line = line[::Oversampling]
        i_line = np.sin(line)
        q_line = np.cos(line)
        if self.sample_false:
            size = int(_length*self.frequency)
            print('generate false iq line')
            q_line = np.linspace(1,size, size)
            i_line = np.linspace(0,size-1, size)
            q_line = q_line/size
            i_line = i_line/size
        # q_line = q_line.astype('int16')
        # i_line = i_line.astype('int16')
        if complex_data:
            return i_line + 1j*q_line
        else:
            return [i_line, q_line]

    def _write_coef(self, alg_num, offset_addr, coef_i, coef_q):
        """[将算法模块系数数据写入存储器]
        write algorithm i data and q data to ddr, 最大支持10对，20个频率系数，每个频率系数的总空间为16MB
        Arguments:
            alg_num {[int]} -- [算法组编号，1，10]
            offset_addr {[int]} -- [系数偏移地址]
            coef_i {[numpy array]} -- [I系数数据]
            coef_q {[numpy array]} -- [Q系数数据]
        """        
        _a = np.array([1], dtype='int16')
        assert alg_num in range(1,11)
        assert coef_i.dtype is _a.dtype, (coef_i.dtype, _a.dtype)
        i_ddr_addr = (alg_num-1)*2*self.coef_data_space+offset_addr+self.coef_data_ddr_addr
        q_ddr_addr = i_ddr_addr + self.coef_data_space
        # print('coef ddr address', hex(i_ddr_addr), hex(q_ddr_addr))
        self.write_ddr(1, i_ddr_addr, coef_i.tobytes())
        self.write_ddr(1, q_ddr_addr, coef_q.tobytes())

    def adc_self_test(self, TriggerType=0, frame_cnt=2000, frame_len=1):
        """[ADC自测试]
        
        Keyword Arguments:
            TriggerType {int} -- [采集方式，0，连续，1，触发]] (default: {0} 连续采集，不需要触发)
            frame_cnt {int} -- [采集帧数] (default: {2000})
            frame_len {int} -- [每帧长度，单位1024采样点] (default: {1})
        """        
        alg_num = 1
        self.flush_data()
        self.sample_with_false_data(True)
        self.setTriggerType(TriggerType)
        self.setFrameNumber(frameNum=frame_cnt)
        self.setRecordLength(recordLength = frame_len)
        arr = np.array([self.gen_iq_line((i+1)*10e6, complex_data=True) for i in range(alg_num)])
        arr = arr*32767.5
        self.mixerTable = np.reshape(arr, (1, alg_num, self.frame_size))
        self.startCapture()
        self.get_Data()
        self.sample_with_false_data(False)
    
    def write_coef(self, coef_data):
        """
        [如果需要FPGA算法模块进行计算：
            # 系数数据(coef_data)为IQ，IQ.shape：4维，(N,M,2,L)
            # N每个频点有多少组系数
            # M有多少组频点,取值范围（1，11）最多10个算法模块
            # 2，I，Q
            # L帧长度, (1k,2k,3k,4k,5k,6k,7k,8k)
            # 如果shape是(2,L), 表明只有1个频点，1组系数(N=1, M=1)
            # 如果shape是(M,2,L),表明有M个频点，每个频点1组系数(N=1)
            # 如果shape是(N,M,2,L), 表明有M个频点，每个频点N组系数
            # 根据系数数据的shape,将算法系数数据写入存储区，使能M个算法模块
            # 每个算法模块在运行的过程中，在初始时自动加载对应的第一组算法系数进行计算，
            # 在接收到frame_cnt/N次触发后，自动切换到下一组系数进行计算
        ]
        注意写系数时会调用ADC采集参数，所以写系数时要确保ADC采集参数已设置为预期值
        如帧数frame_cnt，每帧长度：frame_size
        Args:
            coef_data ([type], optional): [系数数据]. Defaults to None.
        """        
        assert coef_data is not None 
        self.mixerTable = None
        # 算法模式时，每帧长度最大8k
        assert self.frame_size <= 8192
        # 写入算法系数，检查系数数据并得到 N,M,2,L
        shape = coef_data.shape
        assert 0 < shape[-1] <= 8192
        assert shape[-2] == 2
        M = 1 if len(shape) < 3 else shape[-3]
        assert M in range(1,11)
        self.alg_num = M
        N = 1 if len(shape) < 4 else shape[-4]
        frame_cnt_per_coef = int(self.frame_cnt/N)
        assert frame_cnt_per_coef * N == self.frame_cnt, '{0} should be multiple of {1}'.format(self.frame_cnt, N)
        L = shape[-1]

        # 设置算法模块 寄存器
        self._set_alg_para(frame_cnt_per_coef, M, test=False) 

        # 处理系数数据
        pkt_unit = 512
        pad_cnt = (pkt_unit - L & (pkt_unit-1)) & (pkt_unit-1)
        # 调整系数数据
        if len(shape) == 2:
            _shape = (1, 1, shape[0], shape[1])
        elif len(shape) == 3:
            _shape = (1, shape[0], shape[1], shape[2])
        else:
            _shape = shape
        _coef_data = np.reshape(coef_data, _shape) 
        # 系数数据要求是归一化的，然后扩展到16位有符号整数
        _coef_data *= 32767.5
        _coef_data = _coef_data.astype('int16')
        _coef_data = np.pad(_coef_data, ((0,0),(0,0),(0,0),(0,pad_cnt)), mode='constant')
        # print(_coef_data.dtype)
        self.mixerTable = _coef_data[:, :, 0, :]+1j*_coef_data[:, :, 1, :]
        # print(_coef_data)
        # 写入系数数据
        offset_addr = 0
        for n in range(N):
            # print(L+pad_cnt, offset_addr)
            for m in range(M):
                self._write_coef(m+1, offset_addr, _coef_data[n][m][0], _coef_data[n][m][1])
            offset_addr += (L+pad_cnt)*2

    # 配置 AD采集
    def configCapture(self,
                      triggerSource='External',
                      triggerEdge='Rising',
                      triggerDelay=100e-9,
                      frame_cnt=1000,
                      Mode='raw',
                      frameSize=1,
                      isTestData=False
                      ):
        """[配置AD采集:
            triggerSource:
                External/external/Ext/ext is external trigger
                Continue/continue/Cont/cont is internal continue sample
            ]
        Args:
            triggerSource (str, optional): [触发方式]. Defaults to 'External'.
            triggerEdge (str, optional): [触发电平，未使用]. Defaults to 'Rising'.
            triggerDelay (int, optional): [触发延时，单位，秒]]. Defaults to 100e-9秒，100ns.
            frame_cnt (int, optional): [帧数]. Defaults to 1000.
            Mode (str, optional): [模式]. Defaults to 'raw'.
            frameSize (int, optional): [每帧长度，单位1kB]. Defaults to 1.
            isTestData (bool, optional): [测试数据开关]. Defaults to False, data is adc data.
        """        
        ts_map = {'ext':1, 'external':1, 'cont':0, 'continue':0}
       
        self.sample_with_false_data(isTestData)
        self.setTriggerType(ts_map[triggerSource.lower()])
        self.set_adc_trig_delays([triggerDelay])
        self.setFrameNumber(frameNum=frame_cnt)
        self.setRecordLength(recordLength = frameSize)
        

    def set_mode(self, mode='raw'):
        """Mode:
                raw: only sample raw adc data
                alg: only sample alg data calculated from adc data, coef data must be set before
                raw_alg: sample raw adc data and alg data,  coef data must be set before
                store: sample raw adc data and store in pc   

        Args:
            mode (str, optional): [ADC工作模式]. Defaults to 'raw'.
        """        
        mode_map = {'raw':0, 'alg':1, 'raw_alg':2, 'store':3}
        _mode = mode.lower()
        assert _mode in mode_map, mode_map
        self.mode = _mode
        if _mode not in ['alg', 'raw_alg']:
            #禁止算法模块
            self.write_regs([[self.alg_module_idx, 0x2f<<2, 0]]) # 使能0个算法通道
        else:
            assert self.alg_num in range(1, 11)
            alg_ch_enable = (1 << (self.alg_num*2)) - 1 
            self.write_regs([[self.alg_module_idx, 0x2f<<2, alg_ch_enable]]) # 使能多少个算法通道
            self._start_alg()
        if _mode == 'alg':  # 只存算法数据
            _reg_val = 2
        elif _mode == 'raw_alg':  # 同时使能算法和ADC数据
            _reg_val = 3
        else:  # 只使能原始ADC数据
            _reg_val = 1 
        self.write_regs([[self.ad_module_idx, 0x88, _reg_val]])

# import matplotlib.pyplot as plt
# if __name__ == '__main__':
#     ip = '192.168.1.148'
#     ad_core = mf_daq()                                                                                                                              
#     ad_core.connect(ip)
   
#     fig, ax=plt.subplots(3,1, figsize=(6,8))
#     i_line=[]
#     q_line=[]
#     t_line=[]
#     # print(ax)
#     ax0 = ax[0]
#     ax1 = ax[1]
#     ax2 = ax[2]
#     for i in range(200000):
#         print(i)
#         frame_cnt = 3000 ## 采集数据帧数
#         frame_size = 2 ## 每帧数据大小 1k个采样点
#         sample_mode = 1 ### =0，触发采数，需外部触发
#         _ts = time.time()
#         ad_core.adc_self_test()
#         _te = time.time()
#         # print(ad_core.iDataf.mean())
#         # _d = ad_core.iDataf.mean()
#         i_line.append(ad_core.iqDataf[0].mean())
#         q_line.append(ad_core.iqDataf[1].mean())
#         t_line.append(round(_te-_ts, 3))

#         ax0.cla()
#         ax1.cla()
#         ax2.cla()
#         ax0.set_title(u'mean value of FFT data')
#         ax0.set_xlabel('iDataf')
#         ax1.set_xlabel('qDataf')
#         ax2.set_xlabel('time consumed:frame count:{0}, frame size:{1}'.format(ad_core.frame_cnt, ad_core.frame_size))
#         ax0.plot(i_line)
#         ax1.plot(q_line)
#         ax2.plot(t_line)
#         # ax.bar(y1,label='test',height=0.3,width=0.3)
#         # ax.legend()
#         plt.pause(0.1)

