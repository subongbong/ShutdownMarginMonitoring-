import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
import numpy as np


'''
Class name  : Data share
Ver         : Ver 0
Release     : 2018 - 07 -06
Developer   : Deail Lee
'''

import socket
import pickle
from struct import pack, unpack
from numpy import shape
from time import sleep
from parameter import para
import csv


class DataShare:
    def __init__(self, ip, port):

        # socket part
        self.ip, self.port = ip, port  # remote computer

        # cns-data memory
        self.mem = {}  # {'PID val': {'Sig': sig, 'Val': val, 'Num': idx }}
        self.list_mem = {}          ##
        self.list_mem_number = []   ##
        self.number = 0             ##

        self.result=[]

        self.data=[]
        self.shut = []

        self.fig = plt.figure()
        self.ax1 = self.fig.add_subplot(2, 1, 1)
        self.ax2 = self.fig.add_subplot(2, 1, 2)

    # 1. memory reset and refresh UDP
    def reset(self):
        self.mem, self.list_mem = {}, {}
        self.initial_DB()
        for i in range(5):
            self.read_socketdata()
        print('Memory and UDP network reset ready...')

    # 2. update mem from read CNS
    def update_mem(self):
        data = self.read_socketdata()
        for i in range(0, 4000, 20):
            sig = unpack('h', data[24 + i: 26 + i])[0]
            para = '12sihh' if sig == 0 else '12sfhh'
            pid, val, sig, idx = unpack(para, data[8 + i:28 + i])
            pid = pid.decode().rstrip('\x00')  # remove '\x00'
            if pid != '':
                self.mem[pid]['Val'] = val
                self.list_mem[pid]['Val'].append(val)

    # 3. change value and send
    def sc_value(self, para, val, cns_ip, cns_port):
        self.change_value(para, val)
        self.send_data(para, cns_ip, cns_port)

    # 4. dump list_mem as pickle (binary file)
    def save_list_mem(self, file_name):
        with open(file_name, 'wb') as f:
            print('{}_list_mem save done'.format(file_name))
            pickle.dump(self.list_mem, f)

    # (sub) 1.
    def animate(self,i):
        # 1. 값을 로드.
        # 2. 로드한 값을 리스로 저장.
        self.update_mem()
        self.list_mem_number.append(self.number)

        self.ShutdownMarginCalculation()
        self.number += 1

        # 3. 이전의 그렸던 그래프를 지우는거야.
        self.ax1.clear()
        self.ax2.clear()

        # 4. 그래프 업데이트.
        self.ax1.set_title('Shutdown Monitoring', fontsize=15)
        self.ax1.plot(self.list_mem_number, self.shut, label= 'Shutdown Margin', linewidth=1)
        self.ax1.legend(loc='upper right', ncol=5, fontsize=10)
        self.ax1.set_ylim(0, 6000)
        self.ax1.axhline(y=1770, ls='--', color='r', linewidth=1.5)
        self.ax1.set_yticks([2000, 4000, 6000])
        self.ax1.set_yticklabels(['2000[pcm]', '4000[pcm]', '6000[pcm]'], fontsize=8)

        self.ax2.set_title('LCO 3.1.1 Monitoring', fontsize=15)
        self.ax2.plot(self.list_mem_number, self.result, label='Result', linewidth=1)
        self.ax2.legend(loc='upper right', ncol=5, fontsize=10)
        self.ax2.set_ylim(-0.1, 1.1)
        self.ax2.set_yticks([0, 1])
        self.ax2.set_xlabel('Time (s)')

        self.fig.tight_layout()


    # (sub) 1.1make grape
    def make_gp(self):
        style.use('fivethirtyeight')  # 스타일 형식
        ani = animation.FuncAnimation(self.fig, self.animate, interval=1000)
        plt.show()

    # (sub) socket part function
    def read_socketdata(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # socket definition
        sock.bind((self.ip, self.port))
        data, addr = sock.recvfrom(4008)
        sock.close()
        return data

    # (sub) initial memory
    def initial_DB(self):
        idx = 0
        with open('./db.txt', 'r') as f:   # use unit-test
        #with open('./fold/db.txt', 'r') as f: # This line is to use the "import" other function
            while True:
                temp_ = f.readline().split('\t')
                if temp_[0] == '':  # if empty space -> break
                    break
                sig = 0 if temp_[1] == 'INTEGER' else 1
                self.mem[temp_[0]] = {'Sig': sig, 'Val': 0, 'Num': idx}
                self.list_mem[temp_[0]] = {'Sig': sig, 'Val': [], 'Num': idx}
                idx += 1

    def ShutdownMarginCalculation(self):

        subdata=[]

        # 1. time
        Time = self.number
        print(Time)
        subdata.append(Time)

        # 2. BOL, 현출력% -> 0% 하기위한 출력 결손량 계산
        ReactorPower = self.mem['QPROLD']['Val']*100
        PowerDefect_BOL = para.TotalPowerDefect_BOL * ReactorPower / para.HFP
        print(PowerDefect_BOL)
        subdata.append(PowerDefect_BOL)

        # 3. EOL, 현출력% -> 0% 하기위한 출력 결손량 계산
        PowerDefect_EOL = para.TotalPowerDefect_EOL * ReactorPower / para.HFP
        print(PowerDefect_EOL)
        subdata.append(PowerDefect_EOL)

        # 4. 현재 연소도, 현출력% -> 0% 하기위한 출력 결손량 계산
        A = para.Burnup_EOL - para.Burnup_BOL
        B = PowerDefect_EOL - PowerDefect_BOL
        C = para.Burnup - para.Burnup_BOL

        PowerDefect_Burnup = B * C / A + PowerDefect_BOL
        print(PowerDefect_Burnup)
        subdata.append(PowerDefect_Burnup)

        # 5. 반응도 결손량을 계산
        PowerDefect_Final = PowerDefect_Burnup + para.VoidCondtent
        print(PowerDefect_Final)
        subdata.append(PowerDefect_Final)

        # 6. 운전불가능 제어봉 제어능을 계산
        InoperableRodWorth = para.InoperableRodNumber * para.WorstStuckRodWorth
        print(InoperableRodWorth)
        subdata.append(InoperableRodWorth)

        # 7. 비정상 제어봉 제어능을 계산
        if para.AbnormalRodName == 'C':
            AbnormalRodWorth = para.BankWorth_C / 8 * para.AbnormalRodNumber
            print(AbnormalRodWorth)
            subdata.append(AbnormalRodWorth)
        elif para.AbnormalRodName == 'A':
            AbnormalRodWorth = para.BankWorth_A / 8 * para.AbnormalRodNumber
            print(AbnormalRodWorth)
            subdata.append(AbnormalRodWorth)
        elif para.AbnormalRodName == 'B':
            AbnormalRodWorth = para.BankWorth_B / 8 * para.AbnormalRodNumber
            print(AbnormalRodWorth)
            subdata.append(AbnormalRodWorth)
        elif para.AbnormalRodName == 'D':
            AbnormalRodWorth = para.BankWorth_D / 8 * para.AbnormalRodNumber
            print(AbnormalRodWorth)
            subdata.append(AbnormalRodWorth)

        # 8. 운전 불능, 비정상 제어봉 제어능의 합 계산
        InoperableAbnormal_RodWorth = InoperableRodWorth + AbnormalRodWorth
        print(InoperableAbnormal_RodWorth)
        subdata.append(InoperableAbnormal_RodWorth)

        # 9. 현 출력에서의 정지여유도 계산
        ShutdownMargin = para.TotalRodWorth - InoperableAbnormal_RodWorth - PowerDefect_Final
        print(ShutdownMargin)
        subdata.append(ShutdownMargin)
        self.shut.append(ShutdownMargin)

        # 10. 정지여유도 제한치를 만족하는지 비교
        if ShutdownMargin >= para.ShutdownMarginValue:
            label = "만족"
        else:
            label = "불만족"

        with open('./data_save.txt', 'a') as f:
            f.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(Time, PowerDefect_BOL,PowerDefect_EOL,PowerDefect_Burnup,
                                   PowerDefect_Final, InoperableRodWorth, AbnormalRodWorth, InoperableAbnormal_RodWorth,
                                   ShutdownMargin, label))


        if ShutdownMargin >= para.ShutdownMarginValue:
            self.result.append(1) #만족
            return print('만족'), subdata.append('만족'), self.data.append(subdata)
        else:
            self.result.append(0) #불만족
            return print('불만족'), subdata.append('불만족'), self.data.append(subdata)


    def write(self):

        print(self.data)

    def csv(self):
        with open('output.csv','w') as file:
            writer =csv.writer(file)
            writer.writerow(self.data)

    def csv_np(self):
        data3=np.array(self.data)
        np.savetxt('./test3.csv',data3,delimiter=',')

if __name__ == '__main__':

    # unit test
    test = DataShare('192.168.0.192', 8001)  # current computer ip / port
    test.reset()
    test.make_gp()
    test.write()





