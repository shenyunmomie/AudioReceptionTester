from PySide6.QtCore import QThread,Signal,QWaitCondition,QMutex

import os
import re
import time
import wave
import random
import logging
import pandas as pd
import pyaudio

# 以下四个函数作用是识别文本进行扩充
def num2str(intnum):
    numberList = ['零','一','二','三','四','五','六','七','八','九']
    unitList = ['','十','百','千','万','十万','百万','千万','亿']

    strnum = str(intnum)
    lennum = len(strnum)

    if lennum == 1:
        return numberList[int(intnum)]

    string = ''
    for i in range(lennum):

        if int(strnum[i]) != 0:
            for unit in ['万','亿']:
                if string.count(unit) > 1:

                    string = string.replace(unit,'',1)
            # 获取单位
            string = string + numberList[int(strnum[i])] + unitList[lennum-i-1]
        elif int(strnum[i-1]) == 0:
            continue
        else:
            string += '零'
    string=string.strip('零')
    return string

def str2num(string):
    #十无法解决
    numDict = {'零':0,'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10,'百':100}
    unitList = {'十':2,'百':1,'千':0}
    string = str(string)
    if len(string)<=2:
        pass

    listnum = re.split('万|亿',string)
    if len(listnum) == 2:
        if '亿' in string:
            listnum.insert(1,'')

    shu = []
    for word in listnum:
        tmp_lst = [0, 0, 0, 0]
        if word == '':
            shu.extend(tmp_lst)
            continue
        if len(word) == 1:
            shu.extend([numDict[word[0]]])
            continue
        for i in range(len(word)):
            try:
                tmp_lst[unitList[word[i]]] = numDict[word[i-1]]
            except KeyError:
                continue
        if word[-1] not in unitList.keys():
            tmp_lst[3] = numDict[word[-1]]
        shu.extend(tmp_lst)
    # print(shu)
    intnum = ''.join([str(j) for j in shu]).lstrip('0')
    return intnum

def get_sub_set(nums):
    sub_sets = [[]]
    for x in nums:
        sub_sets.extend([item + [x] for item in sub_sets])
    return sub_sets

def txt_tran(txt):
    #提取成字典并拼接
    txt_lst = []
    repl_dict = {}
    #提取数字
    pattern = re.compile('[0-9]+')
    result = pattern.findall(txt)
    for r in result:
        rStr = num2str(r)
        repl_dict[r] = rStr
    #提取汉字
    pattern = re.compile('[零一二三四五六七八九十百千万亿]+')
    result = pattern.findall(txt)
    for r in result:
        rNum = str2num(r)
        repl_dict[r] = rNum
    #运算符
    calcu_dict = {'加':'+','等于':'=','减':'-','乘':'×','除':'÷','乘以':'×','加上':'+','减去':'-','除以':'÷','咗':'左','佢':'距'}
    pattern = re.compile('等于|乘以*|加上*|减去*|除以*|咗+|佢+')
    result = pattern.findall(txt)
    for r in result:
        repl_dict[r] = calcu_dict[r]
    #拼接
    all_sub = get_sub_set(list(range(len(repl_dict))))
    key = list(repl_dict.keys())
    value = list(repl_dict.values())
    for sub in all_sub:
        temp_txt = txt
        for s in sub:
            temp_txt = temp_txt.replace(key[s],value[s])
        txt_lst.append(temp_txt)
    # print(txt_lst)
    return txt_lst

#-------------播放-------------
def play_audio(audio_path):
    CHUNK = 1024

    wf = wave.open(audio_path,mode='rb')
    p = pyaudio.PyAudio()

    steam = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                   channels=wf.getnchannels(),
                   rate=wf.getframerate(),
                   output=True)

    data = wf.readframes(CHUNK)

    while data != b'':
        steam.write(data)
        data = wf.readframes(CHUNK)

    steam.stop_stream()
    steam.close()
    p.terminate()

#---------搜索文件夹-----------
def search_files(path,all_files = []):
    filename_list = os.listdir(path)
    for filename in filename_list:
        cur_path = os.path.join(path,filename)
        if os.path.isdir(cur_path):
            search_files(cur_path,all_files)
        else:
            cur_path_tr = cur_path.replace(' ','_')
            os.rename(cur_path,cur_path_tr)
            all_files.append(cur_path)
    return all_files

# 测试线程
class testThread(QThread):
    test_end = Signal()         # 测试结束信号
    test_one = Signal(int,int)  # 测试一个完成信号

    def __init__(self):
        super(testThread, self).__init__()

    # 设置参数
    def set_param(self,all_files,input_dict,rbtn_choice):
        self._pause = False # 暂停标志
        self._end = False   # 终止标志
        self.input_dict = input_dict    # 输入字典,history
        self.start_point = 0    # 文件指针，文件读写使用
        self.rbtn_choice = rbtn_choice  # 测试场景，标明是哪个测试场景
        self.df = pd.DataFrame(columns=['audio', 'result', 'expected', 'actual', 'play_aftertime', 'response_time'])    # 保存文件
        self.count = 0  # 测试计数器
        self.all_files = all_files  # 需要测试的语料

        self.mutex = QMutex     # 线程锁，暂无用
        self.condition = QWaitCondition()   # 线程暂停的判断

        # 输入变量的赋值
        self.tpath = input_dict['tpath']
        self.spath = input_dict['spath']
        self.test_num = input_dict['test_num']
        self.logpath = input_dict['logpath']
        self.a_re = input_dict['a_re']
        self.radioedit = input_dict['radioedit']

        self.read_logs()  # 初始化log，使其在最新内容开始位置
        self.pull_command = f'adb pull {self.logpath} {self.spath}' #pull命令

    # 判断是否唤醒
    def re_extract(self, log, awake_re):
        if re.findall(awake_re, log):
            return True
        else:
            return False

    # 读取日志信息并返回
    def read_logs(self):
        fo = open(f'{self.spath}\\{self.logpath.split("/")[-1]}', "rb")  # 一定要用'rb'因为seek 是以bytes来计算的
        fo.seek(self.start_point, 1)  # 移动文件读取指针到指定位置
        lines = fo.readlines()
        log = ''
        for line in lines:
            try:
                log = log + ''.join(line.decode('utf-8'))
            except UnicodeDecodeError:
                continue
        # 输出后的指针位置赋值给start_piont
        self.start_point = fo.tell()
        fo.close()
        return log

    # -----结果描述统计-------
    def desc_result(self):
        logging.info(f"总数：{len(self.df)} 正确数：{len(self.df[self.df['result'] == True])}")
        logging.info(
            f"准确率：{round(float(len(self.df[self.df['result'] == True]) / (len(self.df))) * 100, 2)}% 拒识率：{round(float(len(self.df[self.df['result'] == False]) / (len(self.df))) * 100, 2)}%")
        with open(f'{self.spath}\\记录.txt', mode='w', encoding='utf-8') as f:
            f.write(f"识别总数：{len(self.df)} 识别正确数：{len(self.df[self.df['result'] == True])}")
            f.write(
                f"准确率：{round(float(len(self.df[self.df['result'] == True]) / (len(self.df))) * 100, 2)}% 拒识率：{round(float(len(self.df[self.df['result'] == False]) / (len(self.df))) * 100, 2)}%")

    # df保存
    def save_df(self,temp_df):
        self.df = pd.concat([self.df, temp_df], ignore_index=True)
        self.df.to_excel(self.spath+ r'\result.xlsx')

    # 根据连接方式不同，将日志写入到保存文件，并返回最新内容
    def log_info(self):
        if self.rbtn_choice[-8:] == 'adb_wifi' or self.rbtn_choice[-3:] == 'adb':
            os.system(self.pull_command)
            log = self.read_logs()  # 读取log最新内容
            return log
        elif self.rbtn_choice[-6:] == 'serial':
            # 从串口中读取每一行日志信息
            lines = self.input_dict['com'].readlines()
            line = [line.decode('utf-8').strip() for line in lines]

            for l in line:
                with open(f'{self.spath}\\{self.logpath.split("/")[-1]}', mode='a', encoding='utf-8', ) as f:
                    f.write(l)
                    f.write('\n')
            return ';'.join(line)

    def test_main(self,audio_path):
        pass

    def run(self):
        for audio_path in self.all_files:
            # 暂停功能
            while self._pause:
                self.mutex.lock()
                # 此处没有锁住任何资源，因为该test本身就是顺序执行的
                # 后续如果有其他线程访问df、all_files、log文件，可以在此锁住
                self.condition.wait(self.mutex)

                self.mutex.unlock()

            # 终止功能
            if self._end == True:
                break

            self.count += 1

            # if self.count <= test_begin:
            #     continue

            # 测试该音频
            result, expected, actual, play_aftertime, response_time = self.test_main(audio_path)
            audio_name = audio_path.split('\\')[-1]  # 音频名

            # 临时df，用于add，因为df只推荐用concat这种添加方法
            temp_df = pd.DataFrame([[audio_name, result, expected, actual, play_aftertime, response_time]],
                                  columns=['audio', 'result', 'expected', 'actual', 'play_aftertime', 'response_time'])
            self.save_df(temp_df)

            self.test_one.emit(self.count,len(self.all_files))  # 该音频测试完毕信号

            # 打印该测试结果
            logging.info(f"NO.{self.count}:{audio_name}")
            logging.info(f'expected：{expected} \nactual：{actual}')
            logging.info(f"result: {result}\n")
            time.sleep(5)  # 测试间隔

            # 测试数量
            if self.count == self.test_num:
                break
        # 测试结果统计
        self.desc_result()
        self.test_end.emit()    # 测试结束信号

    # 暂停
    def pause_thd(self):
        self._pause = True

    # 继续
    def resume_thd(self):
        self._pause = False
        self.condition.wakeAll()

    # 终止
    def end_thd(self):
        self._end = True

# 唤醒线程
class awakeTestThread(testThread):

    def __init__(self):
        super(awakeTestThread, self).__init__()
        
    def set_param(self,all_files,input_dict,rbtn_choice):
        super(awakeTestThread, self).set_param(all_files,input_dict,rbtn_choice)
        
    # 测试运行的主函数，也是唤醒和识别的主要区别所在
    def test_main(self,audio_path):
        expected = self.input_dict['a_expect']
        play_audio(audio_path)  # 播放音频
        # 记录播放的时间和本地时间
        play_aftertime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        time.sleep(2)  # 等待响应
        times = 4  # 间隔0.5s检查，五次检查都为成功，判断未唤醒，退出循环
        # 判断是否响应
        while True:
            # 将日志写入到保存文件，并返回最新内容
            log = self.log_info()
            response_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            # 判读是否唤醒
            if self.re_extract(log, self.a_re) == True:
                result = True
                actual = expected
                break
            else:
                time.sleep(0.5)  # 无需看
            # 判断等待时间是否超时
            if times == 0:
                response_time = 0
                result = False
                actual = ''
                break
            else:
                times -= 1
        return result, expected, actual, play_aftertime, response_time

# 识别线程
class distTestThread(testThread):

    def __init__(self):
        super(distTestThread, self).__init__()

    def set_param(self,all_files,input_dict,rbtn_choice):
        super(distTestThread, self).set_param(all_files,input_dict,rbtn_choice)

        # 赋值识别需要的变量
        self.d_re = input_dict['d_re']
        # 唤醒音频，可多个，随机
        if os.path.isdir(input_dict['d_awkaudio']):
            self.awake_path_list = search_files(input_dict['d_awkaudio'])
        else:
            self.awake_path_list = [input_dict['d_awkaudio']]

    # 测试主要函数
    def test_main(self,audio_path):
        logging.info(f'当前语料：{audio_path}')
        # 判断是否响应
        while True:
            play_audio(random.choice(self.awake_path_list))  # 播放唤醒音频
            time.sleep(0.5)  # 等待响应
            play_audio(audio_path)  # 播放识别音频
            play_aftertime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            time.sleep(10)  # 等待响应

            # 将日志写入到保存文件，并返回最新内容
            log = self.log_info()
            # 判读是否唤醒
            if self.re_extract(log,self.a_re) == True:
                logging.info("唤醒成功")
                break
            else:
                time.sleep(0.5)
                logging.error("未成功唤醒")
                continue

        # 识别结果提取
        try:
            actual = re.findall(self.d_re, log)[-1].strip()
        except IndexError:
            actual = ''

        # 预期结果，从上一级文件夹查找
        expected = audio_path.split('\\')[-2]
        expected_lst = txt_tran(expected)

        # 判断是否正确
        if actual in expected_lst:
            result = True
        else:
            result = False
        # 记录响应的时间和本地时间
        response_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        return result, expected, actual, play_aftertime, response_time

