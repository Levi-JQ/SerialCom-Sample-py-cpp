#include <math.h>
#include <iostream>
#include <string>
#include "stdio.h"
using namespace std;

//g++ -fPIC -shared serialtrans.cpp -o serialtrans.so



//申明速度范围（单位m/s）
float Vx_MIN = -1.4;
float Vx_MAX = 1.4;
float Vy_MIN = -1.4;
float Vy_MAX = 1.4;
float Vz_MIN = -1.4;
float Vz_MAX = 1.4;

extern "C"{

/*用于协助python类构建需要的数据类型*/

// 创建一个长度为len的float型指针
float *get_pointer(int len)
{
	float *ptr = new float[len];
	return ptr;
}

// 释放指针
void free_pointer(float *ptr)
{
	if(ptr)
	{
		delete [] ptr;
	}
} 



unsigned char getBcc(unsigned char *data, int length)
{
    unsigned char i;
    unsigned char bcc = 0;        // Initial value
#if 1
    while(length--)
    {
        bcc ^= *data++;
    }
#else
    for ( i = 0; i < length; i++ )
    {
        bcc ^= data[i];        // crc ^= *data;
    }
#endif
    return bcc;
}

//typedef char arrT[11];	 //arrT是一个类型别名，表示的类型是含有11个char的数组
//char * setXyz(int x, int y, int z)
char * setXyz(unsigned short x, unsigned short y, unsigned short z)
{
    //if(x < 0){x = x + (1 << 16); }
    static char cmd[] = {0x7b, 0x00, 0x00, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x7B, 0x7d};
    static unsigned char xh,xl,yh,yl,zh,zl;

    xh = (x & 0xff00) >> 8;
    xl = (x & 0x00ff) >> 0;
    yh = (y & 0xff00) >> 8;
    yl = (y & 0x00ff) >> 0;
    zh = (z & 0xff00) >> 8;
    zl = (z & 0x00ff) >> 0;

    cmd[3] = xh;
    cmd[4] = xl;
    cmd[5] = yh;
    cmd[6] = yl;
    cmd[7] = zh;
    cmd[8] = zl;

    cmd[9] = getBcc((unsigned char*)cmd, 9);
    return cmd; 
}

// //发包时所有的数都要经以下函数转化成整型数之后再发给电机。
// int float_to_uint(float x, float x_min, float x_max, unsigned int bits)
// {
//     /// Converts a float to an unsigned int, given range and number of bits /// 
//     float span = x_max - x_min;
//     if (x < x_min) x = x_min;
//     else if (x > x_max) x = x_max;
//     return (int)((x - x_min) * ((float)(((1 << bits)-1) / span)));
// }

// //收包时所有的数都要经以下函数转化成浮点型。
// float uint_to_float(int x_int, float x_min, float x_max, int bits) 
// {
//     /// converts unsigned int to float, given range and number of bits /// 
//     float span = x_max - x_min;
//     float offset = x_min;
//     return ((float)x_int) * span / ((float)((1 << bits) - 1)) + offset;
// }

//发包时所有的数都要经以下函数转化成整型数之后再发给电机。
int float_to_uint(float x, float x_min, float x_max, unsigned int bits)
{
    /// Converts a float to an unsigned int, given range and number of bits /// 
    float span = x_max - x_min;
    if (x < x_min) x = x_min;
    else if (x > x_max) x = x_max;
    int re = (int)( x * ((float)(((1 << bits) - 1) / span)));
    return re;
}

//收包时所有的数都要经以下函数转化成浮点型。
float uint_to_float(int x_int, float x_min, float x_max, int bits) 
{
    /// converts unsigned int to float, given range and number of bits /// 
    float span = x_max - x_min;
    float offset = 0;
    if(x_int >= (1 << bits)*0.5)
    {
        x_int = x_int - ((1 << bits) - 1);
    }
    return ((float)x_int) * span / ((float)((1 << bits) - 1)) + offset;
}


char * DataTrans(float (*data)[3]){ 
    //这些设定的电机参数，根据他们生成待发送数据
	int vx_int,vy_int,vz_int;
	float vx_des,vy_des,vz_des;
	///（1） limit data to be within bounds ///
    vx_des = fminf(fmaxf(Vx_MIN, (*data)[0]), Vx_MAX);
    vy_des = fminf(fmaxf(Vy_MIN, (*data)[1]), Vy_MAX);
    vz_des = fminf(fmaxf(Vz_MIN, (*data)[2]), Vz_MAX);
    
    /// （2）convert floats to unsigned ints /// 
    vx_int = float_to_uint(vx_des, Vx_MIN, Vx_MAX, 16);
    vy_int = float_to_uint(vy_des, Vy_MIN, Vy_MAX, 16);
    vz_int = float_to_uint(vz_des, Vz_MIN, Vz_MAX, 16);
    
    char *transed = setXyz(vx_int,vy_int,vz_int);
    //printf("allocated address: %p\n", transed);////
    return transed;

}


//接收例程代码（将收到的16进制数据转化为单位为m/s的各轴速度值）
void unpack_reply(char (*msg)[11]) 
{
    /// unpack ints from can buffer /// 
	float vx,vy,vz;
	int vx_int,vy_int,vz_int;
    vx_int = ((*msg)[3] << 8) | (*msg)[4]; 			
    vy_int = ((*msg)[5] << 8) | (*msg)[6]; 		 
    vz_int = ((*msg)[7] << 8) | (*msg)[8];		
    /// convert ints to floats /// 
    vx = uint_to_float(vx_int, Vx_MIN, Vx_MAX, 16);
    vy = uint_to_float(vy_int, Vy_MIN, Vy_MAX, 16);
    vz = uint_to_float(vz_int, Vz_MIN, Vz_MAX, 16);
    std::cout << "Vx:"<< vx << std::endl;
    std::cout << "Vy:"<< vy << std::endl;
    std::cout << "Vz:"<< vz << std::endl;
}

}

int main(int argc, const char **argv)
{
    float data[3] = {0.0, 0.0, 0.010894942};
    char *ptr = DataTrans(&data);
    // char (*ptr)[11];
    // ptr = DataTrans(data);
    //验证发送数据
    for(int i=0; i<11; i++){    
        std::cout << "ptr:"<< hex << int(ptr[i])<<std::endl;    
    }

    //验证接收函数
    char temp[11];
    for(int i=0; i<11; i++){    
        temp[i] = ptr[i];    
    }
    char (*msg)[11] = &temp;
    unpack_reply(msg);

    return 0;
}
























