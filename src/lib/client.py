import math
import socket
import time
import os

from lib.communications import (
    DATAGRAM_SIZE,
    FRAGMENT_SIZE,
    Datagram,
    DatagramDeserialized,
    TypeOfDatagram,
)

from lib.sack_communications import (
    SackDatagram,
    SackDatagramDeserialized,
    TypeOfSackDatagram,
    SACK_DATAGRAM_SIZE,
)

PORT = 123

from lib.selective_ack_vic import SelectiveAck
from lib.stop_and_wait import StopAndWait

class Client:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #self.stop_and_wait = StopAndWait.create_stop_and_wait_for_client(self.socket,("127.0.0.1", 1234))
        self.selective_ack = SelectiveAck.create_selective_ack_for_client(("127.0.0.1", 1234), self.socket)

    def upload(self, file_name):
        #self.stop_and_wait.start_client(file_name, TypeOfDatagram.HEADER_UPLOAD.value)
        self.selective_ack.start_client(file_name, TypeOfSackDatagram.HEADER_UPLOAD.value)

    def download(self, file_name):
        self.stop_and_wait.start_client(file_name, TypeOfDatagram.HEADER_DOWNLOAD.value)

    def close(self):
        self.socket.close()
