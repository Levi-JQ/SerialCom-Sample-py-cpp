from ctypes import *
import serial  # 导入模块
import os
import time
import logging
import sys
import numpy as np


### 加载数据转换的C++外部动态库
# os.system("g++ -fPIC -shared \
#     /home/nvidia/MyCode/python_serial/serialtrans.cpp \
#     -o /home/nvidia/MyCode/python_serial/serialtrans.so")
lib = CDLL("/home/nvidia/MyCode/python_serial/serialtrans.so")


class SerialSend():
    def __init__(self, portx, bps, timeout):
        self.portx = portx  #设备，如'/dev/ttyUSB0'
        self.bps = bps  # 波特率
        self.timeout = timeout  
        self.ser = self.__DOpenPort(self.portx, self.bps, self.timeout)
        

    # 打开串口
    def __DOpenPort(self, portx, bps, timeout):
        try:
            # 打开串口，并得到串口对象
            ser = serial.Serial(portx, bps, timeout=timeout)
            # 判断是否打开成功
            if(False == ser.is_open):
                ser = -1
        except Exception as e:
            print("---异常---:", e)
            return
        print('串口已打开')
        return ser

    #调用外部函数，将数据转化为约定的格式
    def __DataTrans(self, data, length=3):
        #检查数据长度是否正确(理论上为三个数据：float类型的x,y,z三个轴的速度)
        if len(data) == length:
            ####python调用c++所需的转换

            ##由C++协助创建python中可用的float指针，长度为length
            lib.get_pointer.argtypes = [c_float]
            lib.get_pointer.restype = POINTER(c_float)
            ptr = lib.get_pointer(length)

            ##Create a python array
            py_array = np.asarray(data).astype(np.float)
            #逐个将Python数组py_array的元素拷贝到ctypes pointer（ptr）所指向的内存中
            for i in range(length):
                ptr[i] = py_array[i]

            ##调用C++库函数完成trans
            lib.DataTrans.argtypes = [POINTER(c_float)]
            lib.DataTrans.restype = POINTER(c_char)
            re_charptr = lib.DataTrans(ptr)
            datatransed = []
            for i in range(11):
                datatransed.append(int.from_bytes(re_charptr[i], byteorder='big', signed=False))
            
            return bytes(datatransed)
        else:
            print("输入数据长度错误")
            return False  

    # 关闭串口
    def DColsePort(self):
        self.ser.close()
        print('串口已关闭')


    def SendMsg(self,data,length=3,printFlag = False):
        #数据转换
        datatransed = self.__DataTrans(data,length) 
        if printFlag:
            for i in range(len(datatransed)):
                print('%#x  '%datatransed[i],end="")
            print(' ')
        #判断数据转换是否成功
        if datatransed != False:
            #print(length(datatransed))
            result = self.ser.write(datatransed) # 写数据,返回写入的字节数
            return result    
        else:
            print('数据转换失败')
            return -1


if __name__ == "__main__":
    #portx = '/dev/ttyTHS1'
    portx = '/dev/ttyUSB0'
    bps = 115200
    timeout = 0.5
    sersend = SerialSend(portx , bps , timeout)

    data = [0.0, 0.0, -0.1]
    #echo -e -n "\x7b\x00\x00\x00\xff\x00\x00\x00\x00\x84\x7d" > /dev/ttyUSB0
    #data = bytearray([0x7b, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x7B, 0x7d])
    #data = bytearray([0x7b, 0x00, 0x00, 0x00, 0xff, 0x00, 0x00, 0x00, 0x00, 0x84, 0x7d])
    try:
        while True:
            sersend.SendMsg(data,3,True)
            #print(data)
            time.sleep(2)
    except Exception as e:
        print("---异常---:", e)
    finally: 
        sersend.SendMsg([0, 0, 0],3,True)  
        sersend.DColsePort()




