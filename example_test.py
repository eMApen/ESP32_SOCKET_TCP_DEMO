# This example code is in the Public Domain (or CC0 licensed, at your option.)

# Unless required by applicable law or agreed to in writing, this
# software is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied.

# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals
from enum import Flag


import os
import re
import socket
import sys
from builtins import input
from threading import Event, Thread , Lock, ThreadError 
import netifaces
import ttfw_idf
import time
import base64
# import struct
import matplotlib.pyplot as plt
from PIL import Image
import json,struct

# -----------  Config  ----------
PORT = 12345
INTERFACE = 'eth0'
mutex = Lock()
enable = Lock()

# -------------------------------
# struct{
#     int length;
#     char sys.flags;

# }

def get_my_ip(type):
    for i in netifaces.ifaddresses(INTERFACE)[type]:
        return i['addr'].replace('%{}'.format(INTERFACE), '')

#dataAnalysis from Client



class TcpServer(Thread):    # Tcp服务器对象,也是用来socket中间件，这是Tcp连接初始化-进入-退出用的

    def __init__(self, port, family_addr, persist=True):
        super(TcpServer,self).__init__()   #重构run函数必须写
        self.port = port
        self.socket = socket.socket(family_addr, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.settimeout(60.0)
        self.shutdown = Event()
        self.persist = persist
        self.family_addr = family_addr


    def __enter__(self):
        try:
            self.socket.bind(('', self.port))
        except socket.error as e:
            print('Bind failed:{}'.format(e))
            raise
        self.socket.listen(1)

        print('Starting server on port={} family_addr={}'.format(self.port, self.family_addr))
        self.server_thread = Thread(target=self.run_server)
        self.server_thread.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.persist:
            sock = socket.socket(self.family_addr, socket.SOCK_STREAM)
            sock.connect(('localhost', self.port))
            sock.sendall(b'Stop', )
            sock.close()
            self.shutdown.set()
        self.shutdown.set()
        self.server_thread.join()
        self.socket.close()

    def run_server(self):
        # 这个函数整体都是在处理socket server过程，
        while not self.shutdown.is_set():
            try:
                conn, address = self.socket.accept()  # accept new connection
                print('Connection from: {}'.format(address))
                conn.setblocking(1)
                # data = conn.recv(1024)
                # if not data:
                #     return
                # data = data.decode()
                # print('Received data: ' + data)
                # reply = 'OdK: ' + data
                # conn.send(reply.encode())
                st = time.time()
                # pic trans test use a function to finish 
                reply = 'Picture'
                conn.send(reply.encode())
                # data = conn.recv(1024)
                # if not data:
                #     return
                # pic = data.decode()
                # if pic.find("PIC")>=0:
                # while 1:
                the = ""
                i=0;
                while(i<=66):
                # for i in range(1,66):
                    the = "Ready"+str(i)
                    conn.send(the.encode())
                    data = conn.recv(60000)
                    if not data:
                        return
                    pic = base64.b64decode(data.decode())
                    # picname = 'recievepic'+ str(i) +'.bmp'
                    picname = 'recievepic'+'.jpg'
                    mutex.acquire()
                    with open(picname, 'wb') as fp:
                        fp.write(pic)
                    mutex.release()
                    # enable.release()
                    cost = time.time()-st
                    print("Picture Recieved!",cost)  
                    conn.close()
                    #停顿时间
                    # plt.pause(0.1)
                    
                    # image = Image.open('recievepic.bmp')
                    # image.show()
                # conn.close()
            except socket.error as e:
                print('Running server failed:{}'.format(e))
            if not self.persist:
                break

    # def dataAnalysis(self):
    #     datafmt='<IIIIIIII'
    #     #定义struct 解包格式，相当协议格式
    #     fmtLen = struct.calcsize(datafmt)
    #     # 得到协议长度
    #     while len(self._buffer) >= fmtLen:
    #         print ("Buffer Length:%s" % len(self._buffer))
    #         (protocLength,) = \
    #             struct.unpack('<I',self._buffer[:self.HEADERSIZE])
    #         #取得协议体长度，协议体为protoc
    #         print (protocLength)
    #         if len(self._buffer) == fmtLen+protocLength:
    #         #得到完整协议+协议体
    #             HeadStr=self._buffer[:fmtLen]
    #             #取出协议
    #             ProtocStr=self._buffer[fmtLen:fmtLen+protocLength]
    #             srcStr = struct.unpack(datafmt,HeadStr)
    #             #解包协议格式
    #             toIP = lambda x: '.'.join([str(x/(256**i)%256) for i in range(3,-1,-1)])
    #             #取得IP地址，由整数转换成IP
    #             print (srcStr)
    #             print ('IP is',toIP(srcStr[6]))
                
    #             print( '处理protoc')
    #             print (test1)
    #             self._buffer = self._buffer[fmtLen+protocLength:]
    #             #分包
    #         elif len(self._buffer) < fmtLen+protocLength:
    #             print( "Continue Received")
    #             return
    #         else:
    #             print ("Error")
    #             self.transport.loseConnection()
    #             return

    

@ttfw_idf.idf_example_test(env_tag='Example_WIFI')
def test_examples_protocol_socket_tcpclient(env, extra_data):
    """
    steps:
      1. join AP
      2. have the board connect to the server
      3. send and receive data
    """
    dut1 = env.get_dut('tcp_client', 'examples/protocols/sockets/tcp_client', dut_class=ttfw_idf.ESP32DUT)
    # check and log bin size
    binary_file = os.path.join(dut1.app.binary_path, 'tcp_client.bin')
    bin_size = os.path.getsize(binary_file)
    ttfw_idf.log_performance('tcp_client_bin_size', '{}KB'.format(bin_size // 1024))

    # start test
    dut1.start_app()

    ipv4 = dut1.expect(re.compile(r' IPv4 address: ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)'), timeout=30)[0]
    ipv6_r = r':'.join((r'[0-9a-fA-F]{4}',) * 8)    # expect all 8 octets from IPv6 (assumes it's printed in the long form)
    ipv6 = dut1.expect(re.compile(r' IPv6 address: ({})'.format(ipv6_r)), timeout=30)[0]
    print('Connected with IPv4={} and IPv6={}'.format(ipv4, ipv6))

    # test IPv4
    with TcpServer(PORT, socket.AF_INET):
        server_ip = get_my_ip(netifaces.AF_INET)
        print('Connect tcp client to server IP={}'.format(server_ip))
        dut1.write(server_ip)
        dut1.expect(re.compile(r'OK: Python copy that'))
    # test IPv6
    with TcpServer(PORT, socket.AF_INET6):
        server_ip = get_my_ip(netifaces.AF_INET6)
        print('Connect tcp client to server IP={}'.format(server_ip))
        dut1.write(server_ip)
        dut1.expect(re.compile(r'OK: Python copy that'))


def TCP_Host():
    if sys.argv[1:] and sys.argv[1].startswith('IPv'):     # if additional arguments provided:
        # Usage: example_test.py <IPv4|IPv6>
        family_addr = socket.AF_INET6 if sys.argv[1] == 'IPv6' else socket.AF_INET
        with TcpServer(PORT, family_addr, persist=True) as s:
            print(input('Press Enter stop the server...'))
        # TcpServer(PORT, family_addr, persist=True)
    else:
        test_examples_protocol_socket_tcpclient()

# def showRxBuffer():
#     while True:
#         enable.acquire()
#         mutex.acquire()
#         img = Image.open(os.path.join('recievepic.bmp'))
#         mutex.release()
#         plt.figure("Image") # 图像窗口名称
#         plt.imshow(img)
#         plt.axis('on')  # 关掉坐标轴为 off
#         plt.xticks([])  # 去刻度
#         plt.yticks([])
#         # plt.show()


if __name__ == '__main__':
   
    picshow = Thread(target=showRxBuffer)
    # tcp.start()
    enable.acquire()
    picshow.start()
    if sys.argv[1:] and sys.argv[1].startswith('IPv'):     # if additional arguments provided:
        # Usage: example_test.py <IPv4|IPv6>
        family_addr = socket.AF_INET6 if sys.argv[1] == 'IPv6' else socket.AF_INET
        with TcpServer(PORT, family_addr,persist=True) as s:
            print(input('Press Enter stop the server...'))
    else:
        test_examples_protocol_socket_tcpclient()
    
    
    
    