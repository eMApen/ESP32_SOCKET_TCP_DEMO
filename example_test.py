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

fmt = '!10s3s'
headerSize = 13
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
        dataBuffer = bytes()
        # 这个函数整体都是在处理socket server过程，
        while not self.shutdown.is_set():
            try:
                conn, address = self.socket.accept()  # accept new connection
                print('Connection from: {}'.format(address))
                conn.setblocking(1)
                st = time.time() 
                reply = 'Picture'
                conn.send(reply.encode())
                print('Request Pictrue Transmit')
                while True:
                    data = conn.recv(60000)
                    if not data:
                        return
                    elif data:
                        dataBuffer += data
                        while True:
                            if len(dataBuffer)<headerSize:
                                print("数据包（%s Byte）小于消息头部长度，跳出小循环" % len(dataBuffer))
                                break

                            # 读取包头
                            # struct中:!代表Network order，3I代表3个unsigned int数据
                            headPack = struct.unpack(fmt, dataBuffer[:headerSize])
                            bodySize = int(headPack[0])
                            print('hp = ',headPack,'headsize = ',headerSize,'bodysize = ',bodySize)

                            # 分包情况处理，跳出函数继续接收数据
                            if len(dataBuffer) < headerSize+bodySize :
                                print("数据包（%s Byte）不完整（总共%s Byte），跳出小循环" % (len(dataBuffer), headerSize+bodySize))
                                break
                            # 读取消息正文的内容
                            body = dataBuffer[headerSize:headerSize+bodySize]

                            # 数据处理
                            dataHandle(headPack, body)

                            # 粘包情况的处理
                            dataBuffer = dataBuffer[headerSize+bodySize:] # 获取下一个数据包，类似于把数据pop出
                        # print('这里是小循环末尾')
                    # print('这里是接收循环末尾')
                # conn.close()
            except socket.error as e:
                print('Running server failed:{}'.format(e))
            if not self.persist:
                break

def dataHandle(head, body):
    print('Data head = ',head)
    if(len(body)>1000):
        print(len(body))
        b64img = body.decode()
        # print(len(b64img),b64img)
        img = base64.b64decode(b64img)
        with open('img.jpg', 'wb') as fp:
            fp.write(img)
        print('complete')
    else:
        print('Data recieved:',body)
    

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
   

    # if sys.argv[1:] and sys.argv[1].startswith('IPv'):     # if additional arguments provided:
    #     # Usage: example_test.py <IPv4|IPv6>
    #     family_addr = socket.AF_INET6 if sys.argv[1] == 'IPv6' else socket.AF_INET
    #     with TcpServer(PORT, family_addr,persist=True) as s:
    #         print(input('Press Enter stop the server...'))
    # else:
    #     test_examples_protocol_socket_tcpclient()

    with TcpServer(PORT, socket.AF_INET,persist=True) as s:
        print(input('Press Enter stop the server...'))
    
    
    
    