from PySide6.QtWidgets import QApplication,QMainWindow,QFileDialog,QMessageBox
from PySide6.QtCore import QObject,Signal,QTimer
from PySide6.QtGui import QIcon
from PySide6.QtUiTools import QUiLoader

import serial.tools.list_ports
import subprocess
import sys,os
import json
import logging

from testThread import search_files,awakeTestThread,distTestThread
from logContent import readLog

log_format = "%(asctime)s - %(levelname)s - %(message)s"
date_format = "%Y-%m-%d %H:%M:%S"
logging.basicConfig(filename='app.log',level=logging.INFO,format=log_format,datefmt=date_format,encoding='utf-8')

# 自定义信号
class MySignal(QObject):

    # 保存完成时的信号
    save_end = Signal()


class Ui_MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()


    def setupUi(self):

        self.ui = QUiLoader().load('audioReceptionTester.ui')   #加载ui文件
        self.ui.setWindowTitle("语音测试工具")
        # 一些控件的初始值调整
        self.ui.pbar.setRange(0,100)
        self.ui.pbar.setValue(0)
        self.ui.a_test_num.setMaximum(999)
        self.ui.a_test_num.setValue(999)
        self.ui.tabWidget.setCurrentIndex(0)

        # 需要定义的变量
        self.history = {"d_awkaudio":'',"tpath":'',"spath":'',"test_num":999,"logpath":'',"a_expect":'',"a_re":'',"d_re":'',"radioedit":''} # 历史保存
        self.rbtn_choice = 'awake_adb_wifi'
        self.awake_testhd = awakeTestThread()   # 唤醒线程
        self.dist_testhd = distTestThread()     # 识别线程
        self.ms = MySignal()    # 自定义信号
        self.logthread = readLog()  # 读取日志
        self.timer = QTimer()  # 计时器，每隔500ms读一次日志

        # 改变单选框时，radioedit输入不同，进行不同内容的变化
        self.ui.awake_adb_wifi.clicked.connect(self.changeRadioLabel)
        self.ui.awake_adb.clicked.connect(self.changeRadioLabel)
        self.ui.awake_serial.clicked.connect(self.changeRadioLabel)
        self.ui.dist_adb_wifi.clicked.connect(self.changeRadioLabel)
        self.ui.dist_adb.clicked.connect(self.changeRadioLabel)
        self.ui.dist_serial.clicked.connect(self.changeRadioLabel)

        # tabWidget切换时，需要改变的内容
        self.ui.tabWidget.currentChanged.connect(self.changeTabWidget)

        # 重要按钮的连接
        self.ui.begin_btn.clicked.connect(self.showInvalidInput)    # 开始按钮：检查合法-保存输入-保存到文件-保存完成信号
        self.ui.history_btn.clicked.connect(self.load_input)        # 加载历史按钮：加载输入(加载文件-加载输入)
        self.ui.history_btn_2.clicked.connect(self.load_input)
        self.ui.clear_btn.clicked.connect(self.clear_input)         # 清除按钮：清除文本框的输入内容
        self.ui.clear_btn_2.clicked.connect(self.clear_input)
        self.ui.pause_btn.clicked.connect(self.pause_test)          # 暂停按钮：将测试暂停
        self.ui.end_btn.clicked.connect(self.end_test)              # 终止按钮，将测试终止，暂停时无法使用

        # 浏览按钮，作用仅为路径输入
        self.ui.search_btn.clicked.connect(self.selectFilePath)
        self.ui.search_btn_2.clicked.connect(self.selectFilePath)
        self.ui.search_btn_3.clicked.connect(self.selectFilePath)
        self.ui.search_btn_4.clicked.connect(self.selectFilePath)
        self.ui.search_btn_5.clicked.connect(self.selectFilePath)

        # 自定义信号连接
        self.ms.save_end.connect(self.testThdFun)   # 保存完成信号：运行测试线程函数

        # 测试线程信号连接
        self.awake_testhd.test_end.connect(self.success_test)   # 测试结束信号：测试成功弹窗
        self.dist_testhd.test_end.connect(self.success_test)
        self.awake_testhd.test_one.connect(self.refreshBar)     # 一个测试完成信号：进度条刷新
        self.dist_testhd.test_one.connect(self.refreshBar)

        self.timer.timeout.connect(self.outputControl)  #计时器，每500ms读取日志并打印控制台
        self.timer.start(500)   #计时器启动

    # 选择路径
    def selectFilePath(self):
        dir = QFileDialog(self.ui,'选择文件夹')
        dir.setAcceptMode(QFileDialog.AcceptOpen)
        dir.setFileMode(QFileDialog.Directory)
        dir.setDirectory(sys.argv[0])
        path = dir.getExistingDirectory()

        sender = self.sender()
        if sender.objectName() == 'search_btn':
            self.ui.a_tpath.setText(path)
        elif sender.objectName() == 'search_btn_2':
            self.ui.a_spath.setText(path)
        elif sender.objectName() == 'search_btn_3':
            self.ui.d_tpath.setText(path)
        elif sender.objectName() == 'search_btn_4':
            self.ui.d_spath.setText(path)
        elif sender.objectName() == 'search_btn_5':
            self.ui.d_awkaudio.setText(path)

    # 根据单选框选择连接设备的方式，不同方式a_radioedit文本框输入不同
    def changeRadioLabel(self):
        if self.ui.tabWidget.currentIndex() == 0:
            if self.ui.awake_adb_wifi.isChecked() == True:
                self.ui.a_radiolabel.setText('ip地址')
                self.ui.a_radioedit.setEnabled(True)
                self.rbtn_choice = 'awake_adb_wifi'
            elif self.ui.awake_serial.isChecked() == True:
                self.ui.a_radiolabel.setText('串口名称')
                self.ui.a_radioedit.setEnabled(True)
                self.rbtn_choice = 'awake_serial'
            else:
                self.ui.a_radiolabel.setText('无需输入')
                self.ui.a_radioedit.setEnabled(False)
                self.rbtn_choice = 'awake_adb'
        elif self.ui.tabWidget.currentIndex() == 1:
            if self.ui.dist_adb_wifi.isChecked() == True:
                self.ui.d_radiolabel.setText('ip地址')
                self.ui.d_radioedit.setEnabled(True)
                self.rbtn_choice = 'dist_adb_wifi'
            elif self.ui.dist_serial.isChecked() == True:
                self.ui.d_radiolabel.setText('串口名称')
                self.ui.d_radioedit.setEnabled(True)
                self.rbtn_choice = 'dist_serial'
            else:
                self.ui.d_radiolabel.setText('无需输入')
                self.ui.d_radioedit.setEnabled(False)
                self.rbtn_choice = 'dist_adb'

    # 切换选项卡时
    def changeTabWidget(self,index):
        if index == 0:
            self.rbtn_choice = 'awake_adb_wifi'
        elif index == 1:
            self.rbtn_choice = 'dist_adb_wifi'

    # 保存输入
    def save_input(self):
        # 赋值到history中
        self.history["tpath"] = self.tpath
        self.history["spath"] = self.spath
        self.history["test_num"] = self.test_num
        self.history["logpath"] = self.logpath
        self.history["a_re"] = self.a_re
        self.history["radioedit"] = self.radioedit

        # 赋值，测试环境不同，对应参数也有所不同
        if self.ui.tabWidget.currentIndex() == 0:
            self.history["a_expect"] = self.a_expect
        elif self.ui.tabWidget.currentIndex() == 1:
            self.history["d_awkaudio"] = self.d_awkaudio
            self.history["d_re"] = self.d_re
        self.save_history(self.rbtn_choice)

    # 将输入保存到不同的json文件
    def save_history(self,filename):
        with open(f'json/{filename}.json','w',encoding='utf-8') as file:
            json.dump(self.history,file)
        logging.info('===保存输入完成===')
        self.ms.save_end.emit()

    # 加载上一次的输入
    def load_input(self):
        # 清除history，避免一些bug
        self.history = {"d_awkaudio": '', "tpath": '', "spath": '', "test_num": 999, "logpath": '', "a_expect": '',
                        "a_re": '', "d_re": '', "radioedit": ''}
        # 加载文件
        self.load_history(self.rbtn_choice)
        # 从history中填入文本框
        if self.ui.tabWidget.currentIndex() == 0:
            self.ui.a_tpath.setText(self.history['tpath'])
            self.ui.a_spath.setText(self.history['spath'])
            self.ui.a_test_num.setValue(int(self.history['test_num']))
            self.ui.a_logpath.setText(self.history['logpath'])
            self.ui.a_except.setText(self.history['a_expect'])
            self.ui.a_re.setText(self.history['a_re'])
            if self.ui.awake_adb.isChecked()==False:
                self.ui.a_radioedit.setText(self.history['radioedit'])
        elif self.ui.tabWidget.currentIndex() == 1:
            self.ui.d_awkaudio.setText(self.history['d_awkaudio'])
            self.ui.d_tpath.setText(self.history['tpath'])
            self.ui.d_spath.setText(self.history['spath'])
            self.ui.d_test_num.setValue(int(self.history['test_num']))
            self.ui.d_logpath.setText(self.history['logpath'])
            self.ui.d_awkre.setText(self.history['a_re'])
            self.ui.d_re.setText(self.history['d_re'])
            if self.ui.dist_adb.isChecked()==False:
                self.ui.d_radioedit.setText(self.history['radioedit'])
        logging.info('加载上一次输入')

    # 从不同的history中读取上一次的输入
    def load_history(self,filename):
        try:
            with open(f'json/{filename}.json','r') as file:
                self.history = json.load(file)
        except FileNotFoundError as error:
            logging.error(error)
            QMessageBox.information(self.ui,'文件错误','文件不存在',QMessageBox.Ok)

    # 清除文本框的内容
    def clear_input(self):
        if self.ui.tabWidget.currentIndex() == 0:
            self.ui.a_tpath.clear()
            self.ui.a_spath.clear()
            self.ui.a_test_num.setValue(999)
            self.ui.a_logpath.clear()
            self.ui.a_except.clear()
            self.ui.a_re.clear()
            self.ui.a_radioedit.clear()
        elif self.ui.tabWidget.currentIndex() == 1:
            self.ui.d_awkaudio.clear()
            self.ui.d_tpath.clear()
            self.ui.d_spath.clear()
            self.ui.d_test_num.setValue(999)
            self.ui.d_logpath.clear()
            self.ui.d_re.clear()
            self.ui.d_awkre.clear()
            self.ui.d_radioedit.clear()

    # 检查输入是否合法
    def showInvalidInput(self):
        # 将输入内容赋值到变量
        if self.ui.tabWidget.currentIndex() == 0:
            self.d_awkaudio = ''
            self.tpath = self.ui.a_tpath.text()
            self.spath = self.ui.a_spath.text()
            self.test_num = self.ui.a_test_num.value()
            self.logpath = self.ui.a_logpath.text()
            self.a_expect = self.ui.a_except.text()
            self.a_re = self.ui.a_re.text()
            self.radioedit = self.ui.a_radioedit.text()
        elif self.ui.tabWidget.currentIndex() == 1:
            self.d_awkaudio = self.ui.d_awkaudio.text()
            self.tpath = self.ui.d_tpath.text()
            self.spath = self.ui.d_spath.text()
            self.test_num = self.ui.d_test_num.value()
            self.logpath = self.ui.d_logpath.text()
            self.d_re = self.ui.d_re.text()
            self.a_re = self.ui.d_awkre.text()
            self.radioedit = self.ui.d_radioedit.text()
        logging.info('====检查路径是否合法====')
        # 检查路径是否为绝对路径，路径是否真实存在
        if os.path.isabs(self.tpath) and os.path.isabs(self.spath) and os.path.isabs(self.d_awkaudio) if self.d_awkaudio != '' else True:
            if os.path.exists(self.tpath) and os.path.exists(self.d_awkaudio) if self.d_awkaudio != '' else True:
                self.save_input()
            else:
                logging.error('路径问题：语料地址不存在')
                QMessageBox.information(self.ui,'路径问题','语料地址不存在',QMessageBox.Ok)
        else:
            logging.error('路径问题：路径输入不合法')
            QMessageBox.information(self.ui,'路径问题','路径输入不合法，请检查',QMessageBox.Ok)

    # 调用search_files函数，建议创建一个线程，音频文件检查包含wav和pcm，没有保证一定是wav
    def file_search(self):
        logging.info('====正在搜索路径内的所有音频文件====')
        all_files = search_files(self.tpath)
        self.all_files = all_files

    # 测试开始前的准备内容的新建
    def newPrepFile(self):
        # 保存路径
        if not os.path.exists(self.spath):
            os.makedirs(self.spath)
        # 创建设备日志文件
        with open(f'{self.spath}\\{self.logpath.split("/")[-1]}', mode='w', encoding='utf-8') as f:
            f.write(str(self.history))
        logging.info('====日志文件创建====')
        return self.connectDevice()

    # 设备连接
    def connectDevice(self):
        if self.rbtn_choice == 'awake_serial' or self.rbtn_choice == 'dist_serial':
            try:
                # 链接串口
                logging.info(f'设备连接：{self.radioedit}')
                com = serial.Serial(port=self.radioedit, baudrate=115200, timeout=2)
            except serial.serialutil.SerialException as error:
                logging.error(error)
                return 1
            self.history["com"] = com
            return 0
        else:
            if self.rbtn_choice == 'awake_adb_wifi' or self.rbtn_choice == 'dist_adb_wifi':
                # adb_wifi连接
                connect_info = subprocess.run(f'adb connect {self.radioedit}',shell=True,capture_output=True,
                                              text=True)
                logging.info(f'设备连接：{connect_info.returncode,connect_info.stdout,connect_info.stderr}')
                try:
                    init_log = subprocess.run(f'adb pull {self.logpath} {self.spath}', capture_output=True,
                                              text=True)
                    logging.info(f'日志初始pull：{init_log.returncode, init_log.stdout, init_log.stderr}')
                except FileNotFoundError as error:
                    logging.error(error)
                    return 1
                return connect_info.returncode
            else:# awake_adb时下面代码足够
                try:
                    init_log = subprocess.run(f'adb pull {self.logpath} {self.spath}',capture_output=True,text=True)
                except FileNotFoundError as error:
                    logging.error(error)
                    return 1
                logging.info(f'日志初始pull：{init_log.stdout}')
                return init_log.returncode

    # 测试线程函数
    def testThdFun(self):
        self.file_search()  # 首先要获得语料：all_files
        connect_state = self.newPrepFile()  # 准备操作：新建需要准备的文件，并且连接设备，返回连接状态码，1-连接有误，0-连接成功
        if connect_state == 1:
            QMessageBox.information(self.ui,'连接错误','请检查输入或连接是否正确')
            return

        # 执行对应的测试线程
        if self.ui.tabWidget.currentIndex() == 0:
            self.awake_testhd.set_param(self.all_files,self.history,self.rbtn_choice)
            self.awake_testhd.start()
        else:
            self.dist_testhd.set_param(self.all_files,self.history,self.rbtn_choice)
            self.dist_testhd.start()
        logging.info('====测试开始====')

    # 完成时的弹窗
    def success_test(self):
        logging.info('测试完成\n')
        QMessageBox.information(self.ui, "完成", "已经完成测试", QMessageBox.Close)

    # 读取日志文件并写入控制台
    def outputControl(self):
        log_connect = self.logthread.main().decode("utf-8",errors="ignore")
        if log_connect != '':
            self.ui.control.append(log_connect)

    # 进度条更新
    def refreshBar(self,num,total):
        self.ui.pbar.setValue((num/total)*100)

    # 检查可用串口
    def search_port(self):
        # 读取可用串口列表
        port_list = list(serial.tools.list_ports.comports())
        # 打印结果
        if len(port_list) == 0:
            logging.error('===无可用串口===')
        else:
            for i in range(0, len(port_list)):
                logging.info(f'可用串口{i}：{port_list[i]}')

    # 暂停测试
    def pause_test(self):
        if self.awake_testhd.isRunning():
            if self.ui.pause_btn.text() == '暂停':
                self.awake_testhd.pause_thd()
                self.ui.pause_btn.setText('继续')
                logging.info('测试暂停')
            else:
                self.awake_testhd.resume_thd()
                self.ui.pause_btn.setText('暂停')
                logging.info('测试继续')
        elif self.dist_testhd.isRunning():
            if self.ui.pause_btn.text() == '暂停':
                self.dist_testhd.pause_thd()
                self.ui.pause_btn.setText('继续')
                logging.info('测试暂停')
            else:
                self.dist_testhd.resume_thd()
                self.ui.pause_btn.setText('暂停')
                logging.info('测试继续')
        else:
            logging.error('===暂停错误:测试未运行===')
            QMessageBox.information(self.ui,'暂停错误','测试未运行',QMessageBox.Ok)

    # 终止测试：暂停状态下，终止键无法起作用
    def end_test(self):
        if self.awake_testhd.isRunning():
            self.awake_testhd.end_thd()
            logging.info('测试已终止')
        elif self.dist_testhd.isRunning():
            self.dist_testhd.end_thd()
            logging.info('测试已终止')
        else:
            logging.error('===终止错误:测试未运行===')
            QMessageBox.information(self.ui, '终止错误', '测试未运行', QMessageBox.Ok)

if __name__ == '__main__':
    app = QApplication([])

    app.setApplicationName("语音测试工具")
    app.setWindowIcon(QIcon('png/logo.png'))

    tester = Ui_MainWindow()
    tester.setupUi()
    tester.ui.show()

    sys.exit(app.exec())
