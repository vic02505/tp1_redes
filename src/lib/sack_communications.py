import struct
from enum import Enum

class TypeOfDatagram(Enum):
    ACK = 1
    HEADER_DOWNLOAD = 2
    HEADER_UPLOAD = 3
    CONTENT = 4
    SACK = 5

N = 256
SACK_FRAGMENT_SIZE = 1343
SACK_DATAGRAM_SIZE = 1496

class DatagramDeserialized:

    def __init__(self, bytes_flow):
        self.datagram_type = struct.unpack('<B', bytes_flow[0:1])[0] # 1 byte
        self.file_name = bytes_flow[1:101].decode().rstrip('\x00') # 100
        self.file_size = struct.unpack('<I', bytes_flow[101:105])[0] # Podriamos sacarlo
        self.datagram_number = struct.unpack('<I', bytes_flow[105:109])[0] # 4 bytes
        self.sacks_content = [
            (struct.unpack('<I', bytes_flow[109:113])[0], struct.unpack('<I', bytes_flow[113:117])[0]),
            (struct.unpack('<I', bytes_flow[117:121])[0], struct.unpack('<I', bytes_flow[121:125])[0]),
            (struct.unpack('<I', bytes_flow[125:129])[0], struct.unpack('<I', bytes_flow[129:133])[0]),
            (struct.unpack('<I', bytes_flow[133:137])[0], struct.unpack('<I', bytes_flow[137:141])[0])
        ]
        self.sack_number = struct.unpack('<I', bytes_flow[141:145])[0]  # 4 bytes
        self.total_datagrams = struct.unpack('<I', bytes_flow[145:149])[0]  # 4 bytes
        self.datagram_size = struct.unpack('<I', bytes_flow[149:153])[0]  # 4 bytes
        self.content = bytes_flow[153:153 + SACK_FRAGMENT_SIZE]  # 1343 bytes
        self.content = self.content[:self.datagram_size]

        # TODO: Porque falla el packjet size llega mal. Los campos llegan todos mal?


class Datagram():
    def __init__(self, datagram_type, file_name, file_size, datagram_number, sacks_content, sack_number, total_datagrams, datagram_size, content):
        self.datagram_type = datagram_type  # Defino que tipo de mensaje es (ACK, HS_DOWNLOAD, HS_UPLOAD, CONTENT)
        self.file_name = file_name  # Nombre del archivo para guardar en servidor o cliente
        self.file_size = file_size  # Tamaño del archivo
        self.datagram_number = datagram_number  # Numero de paquete que estoy enviando
        self.sacks_content = sacks_content
        self.sack_number = sack_number
        self.total_datagrams = total_datagrams  # Cantidad total de paquetes que se enviaran o se recibiran
        self.datagram_size = datagram_size  # Tamaño del paquete que se envia
        self.content = content.ljust(SACK_DATAGRAM_SIZE, b'0')  # Contenido del paquete

    def get_datagram_bytes(self):
        format = f'<B100sIIIIIIIIIIIII{SACK_DATAGRAM_SIZE}s'
        return struct.pack(format, self.datagram_type, self.file_name.encode('utf-8'), self.file_size,
                            self.datagram_number, 
                            self.sacks_content[0][0], self.sacks_content[0][1],
                            self.sacks_content[1][0], self.sacks_content[1][1],
                            self.sacks_content[2][0], self.sacks_content[2][1],
                            self.sacks_content[3][0], self.sacks_content[3][1],
                            self.sack_number,
                            self.total_datagrams, self.datagram_size, self.content)

    @classmethod
    def create_ack(cls, ack_number):
        return cls(datagram_type=TypeOfDatagram.ACK.value, file_name="", file_size=0, datagram_number=ack_number, sacks_content=[[0,0],[0,0],[0,0],[0,0]],
                   sack_number=0, total_datagrams=0, datagram_size=0, content=b"")
    
    @classmethod
    def create_sack(cls, ack_number, sack_number, sacks_content):
        return cls(datagram_type=TypeOfDatagram.SACK.value, file_name="", file_size=0, datagram_number=ack_number, sacks_content=sacks_content,
                   sack_number = sack_number, total_datagrams=0, datagram_size=0, content=b"")

    @classmethod
    def create_download_header_client(cls, file_name):
        return cls(datagram_type=TypeOfDatagram.HEADER_DOWNLOAD.value, file_name=file_name, file_size=0,
                   datagram_number=0, sacks_content = [[0,0],[0,0],[0,0],[0,0]], sack_number = 0, total_datagrams=0, datagram_size=0, content=b"")

    @classmethod
    def create_upload_header_client(cls, file_name, file_size, total_datagrams):
        return cls(datagram_type=TypeOfDatagram.HEADER_UPLOAD.value, file_name=file_name, file_size=file_size,
                   datagram_number=0, sacks_content = [[0,0],[0,0],[0,0],[0,0]], sack_number = 0, total_datagrams=total_datagrams, datagram_size=0, content=b"")

    @classmethod
    def create_content(cls, datagram_number, total_datagrams, file_name,
                       datagram_size, content):
        return cls(datagram_type=TypeOfDatagram.CONTENT.value, file_name=file_name, file_size=0,
                   datagram_number=datagram_number, sacks_content=[[0,0],[0,0],[0,0],[0,0]], sack_number=0, total_datagrams=total_datagrams,
                   datagram_size=datagram_size, content=content)

    @classmethod
    def create_download_header_server(cls, file_name, file_size, total_datagrams):
        return cls(datagram_type=TypeOfDatagram.HEADER_DOWNLOAD.value, file_name=file_name, file_size=file_size,
                   datagram_number=0, sacks_content = [[0,0],[0,0],[0,0],[0,0]], sack_number=0, total_datagrams=total_datagrams, datagram_size=0, content=b"")

