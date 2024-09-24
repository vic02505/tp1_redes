import ctypes
import struct
from enum import Enum

class TypeOfDatagram(Enum):
    ACK = 1
    HEADER_DOWNLOAD = 2
    HEADER_UPLOAD = 3
    CONTENT = 4

N = 256


class DatagramDeserialized:

    def __init__ (self, bytes_flow):
        self.file_type = struct.unpack('B', bytes_flow[0:1])[0]
        self.file_name = bytes_flow[1:101].decode()
        self.file_size = struct.unpack('I', bytes_flow[101:105])[0]
        self.packet_number = struct.unpack('I', bytes_flow[105:109])[0]
        self.total_packet_count = struct.unpack('I', bytes_flow[109:113])[0]
        self.packet_size = struct.unpack('I', bytes_flow[113:117])[0]
        print(f"Packet sixze: {self.packet_size}")
        self.content = bytes_flow[117:40117]
        self.content = self.content[:self.packet_size]

        #TODO: Porque falla el packjet size llega mal. Los campos llegan todos mal?
        


class Datagram():
    def __init__(self, file_type, file_name, file_size, packet_number, total_packet_count, packet_size, content):
        # self.file_type = struct.pack('B', file_type)
        # self.file_name = file_name.encode().ljust(100, b'0')
        # self.file_size = struct.pack('I', file_size)
        # self.packet_number = struct.pack('I', packet_number)
        # self.total_packet_count = struct.pack('I', total_packet_count)
        # self.packet_size = struct.pack('I', packet_size)
        # self.content = content.ljust(40000, b'0')
        self.file_type = file_type
        self.file_name = file_name
        self.file_size = file_size
        self.packet_number = packet_number
        self.total_packet_count = total_packet_count
        self.packet_size = packet_size
        self.content = content.ljust(40000, b'0')

    def get_datagram_bytes(self):
        format = 'B100sIIII40000s'
        return struct.pack(format, self.file_type, self.file_name.encode('utf-8'), self.file_size, self.packet_number, self.total_packet_count, self.packet_size, self.content)
        


    @classmethod
    def create_ack(cls, packet_number):
        return cls(file_type=TypeOfDatagram.ACK.value, file_name="", file_size=0, packet_number=0,
                   total_packet_count=0, packet_size=0, content=b"")

    @classmethod
    def create_download_header(cls, file_name, file_size):
        return cls(file_type=TypeOfDatagram.HEADER_DOWNLOAD.value,
                   file_name=file_name,
                   file_size=file_size)

    @classmethod
    def create_upload_header(cls, file_name, file_size, fragment_count):
        return cls(file_type=TypeOfDatagram.HEADER_UPLOAD.value, file_name=file_name, file_size=file_size,
                   packet_number=0, total_packet_count=fragment_count, packet_size=0, content=b"")

    @classmethod
    def create_content(cls, packet_number, total_packet_count,
                       packet_size, content):
        return cls(file_type=TypeOfDatagram.CONTENT.value, file_name='', file_size=0,
                   packet_number=packet_number, total_packet_count=total_packet_count,
                   packet_size=packet_size, content=content)

