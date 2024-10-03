import socket

from lib.sw_communications import TypeOfSwDatagram
from lib.sack_communications import TypeOfSackDatagram

from lib.selective_ack import SelectiveAck
from lib.stop_and_wait import StopAndWait

class Client:
    def __init__(self, host, port, algorithm):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if algorithm == "sw":
            self.stop_and_wait = StopAndWait.create_stop_and_wait_for_client(self.socket, (host, port))
        elif algorithm == "sack":
            self.selective_ack = SelectiveAck.create_selective_ack_for_client(self.socket, (host, port))

    def upload(self, file_name, algorithm):
        if algorithm == "sw":
            self.stop_and_wait.start_client(file_name, TypeOfSwDatagram.HEADER_UPLOAD.value)
        elif algorithm == "sack":
            self.selective_ack.start_client(file_name, TypeOfSackDatagram.HEADER_UPLOAD.value)

    def download(self, file_name, algorithm):
        if algorithm == "sw":
            self.stop_and_wait.start_client(file_name, TypeOfSwDatagram.HEADER_DOWNLOAD.value)
        elif algorithm == "sack":
            self.selective_ack.start_client(file_name, TypeOfSackDatagram.HEADER_DOWNLOAD.value)

    def close(self):
        self.socket.close()
