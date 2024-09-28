import struct
from enum import Enum


class TypeOfDatagram(Enum):
    ACK = 1
    HEADER_DOWNLOAD = 2
    HEADER_UPLOAD = 3
    CONTENT = 4


N = 256
FRAGMENT_SIZE = 40000
DATAGRAM_SIZE = 40117


class DatagramDeserialized:

    def __init__(self, bytes_flow):
        self.datagram_type = struct.unpack('<B', bytes_flow[0:1])[0]
        self.file_name = bytes_flow[1:101].decode().rstrip('\x00')
        self.file_size = struct.unpack('<I', bytes_flow[101:105])[0]
        self.datagram_number = struct.unpack('<I', bytes_flow[105:109])[0]
        self.total_datagrams = struct.unpack('<I', bytes_flow[109:113])[0]
        self.datagram_size = struct.unpack('<I', bytes_flow[113:117])[0]
        self.content = bytes_flow[117:40117]
        self.content = self.content[:self.datagram_size]

        # TODO: Porque falla el packjet size llega mal. Los campos llegan todos mal?


class Datagram():
    def __init__(self, datagram_type, file_name, file_size, datagram_number, total_datagrams, datagram_size, content):
        self.datagram_type = datagram_type  # Defino que tipo de mensaje es (ACK, HS_DOWNLOAD, HS_UPLOAD, CONTENT)
        self.file_name = file_name  # Nombre del archivo para guardar en servidor o cliente
        self.file_size = file_size  # Tamaño del archivo
        self.datagram_number = datagram_number  # Numero de paquete que estoy enviando
        self.total_datagrams = total_datagrams  # Cantidad total de paquetes que se enviaran o se recibiran
        self.datagram_size = datagram_size  # Tamaño del paquete que se envia
        self.content = content.ljust(40000, b'0')  # Contenido del paquete

    def get_datagram_bytes(self):
        format = '<B100sIIII40000s'
        return struct.pack(format, self.datagram_type, self.file_name.encode('utf-8'), self.file_size,
                           self.datagram_number, self.total_datagrams, self.datagram_size, self.content)

    @classmethod
    def create_ack(cls, ack_number):
        return cls(datagram_type=TypeOfDatagram.ACK.value, file_name="", file_size=0, datagram_number=ack_number,
                   total_datagrams=0, datagram_size=0, content=b"")

    @classmethod
    def create_download_header_client(cls, file_name):
        return cls(datagram_type=TypeOfDatagram.HEADER_DOWNLOAD.value, file_name=file_name, file_size=0,
                   datagram_number=0, total_datagrams=0, datagram_size=0, content=b"")

    @classmethod
    def create_upload_header_client(cls, file_name, file_size, total_datagrams):
        return cls(datagram_type=TypeOfDatagram.HEADER_UPLOAD.value, file_name=file_name, file_size=file_size,
                   datagram_number=0, total_datagrams=total_datagrams, datagram_size=0, content=b"")

    @classmethod
    def create_content(cls, datagram_number, total_datagrams, file_name,
                       datagram_size, content):
        return cls(datagram_type=TypeOfDatagram.CONTENT.value, file_name=file_name, file_size=0,
                   datagram_number=datagram_number, total_datagrams=total_datagrams,
                   datagram_size=datagram_size, content=content)

    @classmethod
    def create_download_header_server(cls, file_name, file_size, total_datagrams):
        return cls(datagram_type=TypeOfDatagram.HEADER_DOWNLOAD.value, file_name=file_name, file_size=file_size,
                   datagram_number=0, total_datagrams=total_datagrams, datagram_size=0, content=b"")

