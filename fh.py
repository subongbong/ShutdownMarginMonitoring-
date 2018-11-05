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


class DataShare:
    def __init__(self, ip, port):
        # socket part
        self.ip, self.port = ip, port  # remote computer

        # cns-data memory
        self.mem = {}  # {'PID val': {'Sig': sig, 'Val': val, 'Num': idx }}
        self.list_mem = {}          ##
        self.list_mem_number = []   ##
        self.number = 0             ##

        self.tt=[]

        self.result=[]

        self.fig = plt.figure()
        self.ax1 = self.fig.add_subplot(3, 1, 1)
        self.ax2 = self.fig.add_subplot(3, 1, 2)
        self.ax3 = self.fig.add_subplot(3, 1, 3)

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
    # 테스트용
    def test(self):
        a=self.mem['ZINST65']['Val'] + self.mem['UAVLEG1']['Val']
        self.tt.append(a)
        print(self.tt)


    # (sub) 1.
    def animate(self,i):
        # 1. 값을 로드.
        # 2. 로드한 값을 리스로 저장.
        self.update_mem()
        self.list_mem_number.append(self.number)

        #self.test()
        self.P_Tcold()
        self.number += 1

        # 3. 이전의 그렸던 그래프를 지우는거야.
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()
        # 4. 그래프 업데이트.
        #self.ax1.set_ylim([0,400] ) #y축 범위 설정
        self.ax1.plot(self.list_mem_number, self.list_mem['ZINST65']['Val'],label='PRZ Pre',linewidth=1)
        self.ax2.plot(self.list_mem_number, self.list_mem['UCOLEG1']['Val'], label='Loop1 Tcold', linewidth=1)
        self.ax2.plot(self.list_mem_number, self.list_mem['UCOLEG2']['Val'], label='Loop2 Tcold', linewidth=1)
        self.ax2.plot(self.list_mem_number, self.list_mem['UCOLEG3']['Val'], label='Loop3 Tcold', linewidth=1)
        self.ax3.plot(self.list_mem_number, self.result, label='Result', linewidth=1)

        self.ax1.legend(loc='upper right', ncol=5, fontsize=10)
        self.ax2.legend(loc='upper right', ncol=5, fontsize=10)
        self.ax3.legend(loc='upper right', ncol=5, fontsize=10)

        self.ax1.axhline(y=161.6, ls='--', color='r',linewidth=1)
        self.ax1.axhline(y=154.7, ls='--', color='r',linewidth=1)
        self.ax1.set_ylim(152,164)
        self.ax2.axhline(y=305, ls='--', color='r',linewidth=1)
        self.ax2.axhline(y=286.7, ls='--', color='r',linewidth=1)
        self.ax2.set_ylim(285.5,310)
        self.ax3.set_ylim(0, 1.2)
        self.ax1.set_xlabel('time')
        self.ax1.set_ylabel('value')
        self.ax2.set_xlabel('time')
        self.ax2.set_ylabel('value')
        self.ax3.set_xlabel('time')
        self.ax3.set_ylabel('value')
        self.fig.tight_layout()


    # (sub) 1.1make grape
    def make_gp(self):
        style.use('fivethirtyeight')  # 뭔지 몰라 # 스타일..
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
    def P_Tcold(self):

        PP= self.mem['ZINST65']['Val']
        T1 = self.mem['UCOLEG1']['Val']

        if 154.7 < PP <  161.6 and 286.7 < T1 < 293.3:
          self.result.append(1)
        else :
          self.result.append(0)

        print(self.result)

if __name__ == '__main__':

    # unit test
    test = DataShare('192.168.0.192', 8001)  # current computer ip / port
    test.reset()

    test.make_gp()