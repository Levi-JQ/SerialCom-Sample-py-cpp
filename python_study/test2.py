import serial  # 导入模块
import threading
import time
import logging
import sys


class UartInfo(object):
    def __init__(self, fd, count, fail):
        self.fd = fd
        self.count = count  # 测试次数
        self.fail = fail  # 失败次数

    response = False
    image_addr = 0x00
    image_crc = 0x00
    version = 0
    write_event = threading.Event()


uart = UartInfo(-1, 0, 0)


def logging_init():
    logging.basicConfig(#  filename="test.log", # 指定输出的文件
        level=logging.DEBUG,
        format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')

    return True


# 十六进制显示
def hexShow(argv):
    try:
        result = ''
        hLen = len(argv)
        for i in range(hLen):
            hvol = argv[i]
            hhex = '%02x' % hvol
            result += hhex+' '

        logging.info('Led Read:%s', result)
        return result
    except Exception as e:
        print("---异常---:", e)


def crc_sum(data, data_len):
    crc = 0
    i = 0
    while(i < data_len):
        crc += data[i]
        i += 1
    return crc & 0x00FF


def crc_sum_u32(data, data_len):
    crc = 0
    i = 0
    while(i < data_len):
        crc += data[i]
        i += 1
    return crc

# 打开串口
def DOpenPort(portx, bps, timeout):
    try:
        # 打开串口，并得到串口对象
        ser = serial.Serial(portx, bps, timeout=timeout)
        # 判断是否打开成功
        if(False == ser.is_open):
           ser = -1
    except Exception as e:
        print("---异常---:", e)

    return ser


# 关闭串口
def DColsePort(ser):
    uart.fdstate = -1
    ser.close()


# 写数据
def DWritePort(ser, data):
    result = ser.write(data)  # 写数据
    logging.info(ser)
    logging.info("Led Write %s(%d)" % (data.hex(), result))
    return result


# 读数据
def ReadData_Thread(ser):
    # 循环接收数据，此为死循环，可用线程实现
    readstr = ""
    while(-1 != ser):
        if ser.in_waiting:
            try:  # 如果读取的不是十六进制数据--
                readbuf = ser.read(ser.in_waiting)
                if readbuf[0] == 0x55 and readbuf[1] == 0xaa:
                    readstr = readbuf
                else:
                    readstr = readstr + readbuf

                hexShow(readstr)

                if (readstr[3] == 0x01) and (len(readstr) > 10):
                    uart.version = readstr[16]
                    uart.response = True
                    uart.write_event.set()
                elif (readstr[3] == 0x21) and (readstr[4] == 0x00) and (readstr[5] == 0x00):
                    uart.response = True
                    uart.write_event.set()
                elif (readstr[3] == 0x22) and (len(readstr) > 10):
                    uart.image_addr = (readstr[6] << 24 & 0xFF000000)
                    uart.image_addr += (readstr[7] << 16 & 0x00FF0000)
                    uart.image_addr += (readstr[8] << 8 & 0x0000FF00)
                    uart.image_addr += (readstr[9] << 0 & 0x000000FF)
                    uart.response = True
                    uart.write_event.set()
                elif (readstr[3] == 0x23) and (len(readstr) > 25):
                    uart.response = True
                    uart.write_event.set()

            except:  # --则将其作为字符串读取
                readbuf = ser.read(ser.in_waiting)
                hexShow(readbuf)


def GetVersion(ser):
    print("GetVersion")
    writebuf = bytearray([0x55, 0xaa, 0x00, 0x01, 0x00, 0x00])
    # crc
    writebuf.append(crc_sum(writebuf, len(writebuf)))
    DWritePort(ser, writebuf)

    logging.info("take")
    uart.response = False
    uart.write_event.clear()
    uart.write_event.wait(timeout=3)
    uart.write_event.clear()
    logging.info("give")
    if uart.response == False:
        logging.info("fail")
        return False
    else:
        return True
        

# 测试任务
def Test_Thread(ser):
    while (-1 != ser):
        uart.response = False
        uart.image_addr = 0x00
        uart.image_crc = 0x00
        uart.version = 0
        logging.info("count:%d", uart.count)
        logging.info("fail:%d", uart.fail)
        print("count", uart.count)
        print("fail", uart.fail)

        if GetVersion(ser):
            logging.info(uart.version)
            if uart.version == 0x37:
                otafile = "./UartV108.bin"
            else:
                otafile = "./UartV107.bin"
        else:
            uart.fail += 1
            uart.count += 1
            continue

        print("ota:", otafile)
        logging.info("ota:%s", otafile)
        time.sleep(2)

        uart.count += 1
        time.sleep(5)


def TestStop(ser):
    DColsePort(uart.fd)  # 关闭串口


if __name__ == "__main__":
    if 2 != len(sys.argv):
        print("please enter COM")
        exit()
    else:
        uart.tty = sys.argv[1]

    logging_init()
    uart.fd = DOpenPort(uart.tty, 115200, None)

    if(uart.fd != -1):  # 判断串口是否成功打开
        threading.Thread(target=Test_Thread, args=(uart.fd,)).start()
        #threading.Thread(target=ReadData_Thread, args=(uart.fd,)).start()


