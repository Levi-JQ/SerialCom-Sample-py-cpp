import serial as ser
import struct,time


def recv(serial):
    while True:
        data=serial.read(64)
        if data=='':
            continue
        else:
            break
    return data


if __name__ == "__main__":
    a ='z'
    c=a.encode('utf-8')
    b=678
    se = ser.Serial('/dev/ttyTHS1',115200,timeout=0.5)
    while True:
        data=recv(se)
        if data!='':
            print(data)   #这里是调试的串口接收，接受函数看自己需要定，这里只是方便博主调试
        se.write(str(b).encode('utf-8'))
        se.write(a.encode('utf-8'))
        time.sleep(1)
    

