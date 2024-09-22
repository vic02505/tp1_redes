import ctypes
from enum import Enum

N = 256

class MessageType(Enum):
    ACK = 1
    HEADER_DOWNLOAD = 2
    HEADER_UPLOAD = 3
    CONTENT = 4

class Datagram(ctypes.LittleEndianStructure):
    _fields_ = [
        ("file_type", ctypes.c_uint8),  
        ("file_name", ctypes.c_char * 100),  
        ("file_size", ctypes.c_uint32),  
        ("packet_number", ctypes.c_uint32),  
        ("total_packet_count", ctypes.c_uint32),  
        ("packet_size", ctypes.c_uint32),  
        ("content", ctypes.c_char * 40000)  
    ]

    def __init__(self, file_type, file_name="None", file_size=0, 
                 packet_number=0, total_packet_count=0, 
                 packet_size=0, content=""):
        super().__init__()
        self.file_type = file_type
        self.file_name = file_name.encode('utf-8')[:100].ljust(100, b'\x00')  # Rellenar con ceros si es más corto
        self.file_size = file_size
        self.packet_number = packet_number
        self.total_packet_count = total_packet_count
        self.packet_size = packet_size
        self.content = content.encode('utf-8')[:40000].ljust(40000, b'\x00')  # Rellenar con ceros si es más corto

    @classmethod
    def create_ack(cls, packet_number):
        return cls(file_type=MessageType.ACK, packet_number=packet_number)

    @classmethod
    def create_download_header(cls, file_name, file_size):
        return cls(file_type=MessageType.HEADER_DOWNLOAD, 
                    file_name=file_name, 
                    file_size=file_size)
    
    @classmethod
    def create_upload_header(cls, file_name, file_size):
        return cls(file_type=MessageType.HEADER_UPLOAD, 
                    file_name=file_name, 
                    file_size=file_size)

    @classmethod
    def create_content(cls, packet_number, total_packet_count, 
                        packet_size, content):
        return cls(file_type=MessageType.CONTENT, 
                    packet_number=packet_number, 
                    total_packet_count=total_packet_count, 
                    packet_size=packet_size, 
                    content=content)
