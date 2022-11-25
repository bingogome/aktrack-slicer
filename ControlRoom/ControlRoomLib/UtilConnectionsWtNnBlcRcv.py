"""
MIT License

Copyright (c) 2022 Yihao Liu, Johns Hopkins University

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import socket
import qt
from ControlRoomLib.UtilConnections import UtilConnections

class UtilConnectionsWtNnBlcRcv(UtilConnections):
    """
    Connection class that has an additional non-blocking receive
    socket (using qt Timer in Slicer since Slicer is single threaded)

    Received data is handled by overriding self.handleReceivedData()
    """

    def __init__(self, sock_ip_receive_nnblc, sock_port_receive_nnblc, packetInterval, \
            sock_ip_receive, sock_port_receive, sock_ip_send, sock_port_send):
        super().__init__(sock_ip_receive, sock_port_receive, sock_ip_send, sock_port_send)

        self._sock_ip_receive_nnblc = sock_ip_receive_nnblc
        self._sock_port_receive_nnblc = sock_port_receive_nnblc

        self._sock_receive_nnblc = None
        self._flag_receiving_nnblc = False

        self._data_buff = None

        self._packetInterval = packetInterval

    def setup(self):
        super().setup()
        self._sock_receive_nnblc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # set buffer size to 1 if want data to be time sensitive
        self._sock_receive_nnblc.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1)
        self._sock_receive_nnblc.connect(\
            (self._sock_ip_receive_nnblc, self._sock_port_receive_nnblc))
        # self._sock_receive_nnblc.settimeout(0.1/1000)
        self._sock_receive_nnblc.setblocking(0)

    def clear(self):
        super().clear()
        self._flag_receiving_nnblc = False
        if self._sock_receive_nnblc:
            self._sock_receive_nnblc.close()

    def handleReceivedData(self):
        """
        Will need to be overriden
        """
        return

    def receiveTimerCallBack(self):
        if self._flag_receiving_nnblc:
            try:
                # self._data_buff = self._sock_receive_nnblc.recvfrom(256)
                self._data_buff = self._sock_receive_nnblc.recv(2048)
                self.handleReceivedData()
                qt.QTimer.singleShot(self._packetInterval+1, self.receiveTimerCallBack)
            except:
                qt.QTimer.singleShot(self._packetInterval+1, self.receiveTimerCallBack)