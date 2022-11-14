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

#
# Connection
#

import socket
import json
import slicer


class UtilConnections():
    """
    Connection class.
    Blocking send and receive
    """

    def __init__(self, sock_ip_receive, sock_port_receive, sock_ip_send, sock_port_send):

        self._sock_ip_receive = sock_ip_receive
        self._sock_ip_send = sock_ip_send
        self._sock_port_receive = sock_port_receive
        self._sock_port_send = sock_port_send

        self._sock_receive = None
        self._sock_send = None

    def setup(self):
        self._sock_receive = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock_receive.bind(
            (self._sock_ip_receive, self._sock_port_receive))
        self._sock_receive.settimeout(0.5)

    def clear(self):
        if self._sock_receive:
            self._sock_receive.close()
        if self._sock_send:
            self._sock_send.close()

    def utilSendCommand(self, msg, errorMsg="Failed to send command ", res=False):
        msg = msg + self._eom
        if len(msg) > 2048:
            raise RuntimeError("Command contains too many characters.")
        try:
            self._sock_send.sendto(
                msg.encode('UTF-8'), (self._sock_ip_send, self._sock_port_send))
            try:
                data = self._sock_receive.recvfrom(2048)
            except socket.error:
                raise RuntimeError("Command response timedout")
        except Exception as e:
            slicer.util.errorDisplay(errorMsg+str(e))
            import traceback
            traceback.print_exc()
            raise
        if res:
            return data

    def receiveMsg(self):
        try:
            data = self._sock_receive.recvfrom(2048)
        except socket.error:
            raise RuntimeError("Command response timedout")
        return data[0].decode('UTF-8')