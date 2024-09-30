import struct
from enum import Enum
from fileinput import filename

from lib.communications import TypeOfDatagram


class LengthsForSackDatagram(Enum):
    SACK_HEADER_LENGTH = 145
    SACK_CONTENT_LENGTH = 1315

class TypeOfSackDatagram(Enum):
    ACK = 1
    DOWNLOAD = 2
    UPLOAD = 3
    CONTENT = 4

class AmountOfSacks(Enum):
    ONE_SACK = 1
    TWO_SACKS = 2
    THREE_SACKS = 3
    FOUR_SACKS = 4

SACK_DATAGRAM_SIZE = 1459

'''
    POR AHI FUE MEIOD AL PEDO INLCUIR ESTE MODULO, HAY UN TEMA, HABRIA QUE REFACTORIZAR UN POCO EL OTRO, AGREGAR
    UN CAMPO PARA LOS SACKS, OTRO PARA DECIR CUANTOS SACKS HAY, Y LUEGO CAMBIAR UNOS CUANTOS METODDOS DE CLASE,
    LOS OBJETOS DDE TIPO SOCKET DATAGRAM SE CONSTRUYEN HASTA AHORA SIN LOS DATOS DE SACK, INCLUIR ESA INFO NO HARIA, 
    COMO RECIEN MENCIONE, TENER QUE REFACTORIZAR. OTRO TEMA ES QUE ESTARIAMOS DEJANOD ESPACIO LIBRE AL PEDO 
    (SACK CONTENT SON 32 BYTES + 1 BYTES DEL NUMERO DE SACK.
'''

class SackDatagramDeserialized:
    def __init__(self, bytes_flow):
        self.datagram_type = struct.unpack('<B', bytes_flow[0:1])[0] # 1 byte
        self.number_of_sacks = struct.unpack('<B', bytes_flow[1:2])[0] # 1 byte
        self.sacks_content = bytes_flow[2:34].decode().rstrip('\x00')  # 32 bytes "2-3,5-6"
        self.file_name = bytes_flow[34:134].decode().rstrip('\x00') # 100
        self.datagram_number = struct.unpack('<I', bytes_flow[134:138])[0] # 4 bytes
        self.total_datagrams = struct.unpack('<I', bytes_flow[138:142])[0] # 4 bytes
        self.content_size = struct.unpack('<H', bytes_flow[142:144])[0] # 2 bytes
        self.content = bytes_flow[115:1430] # 1315 bytes
        self.content = self.content[:self.content_size]


class SackDatagram:
    def __init__(self, datagram_type, number_of_sacks, sacks_content, file_name, datagram_number, total_datagrams,
                 content_size, content):
        self.datagram_type = datagram_type # 1 byte
        self.number_of_sacks = number_of_sacks # 1 byte
        self.sacks_content = sacks_content # 32 bytes
        self.file_name = file_name # 100 bytes
        self.datagram_number = datagram_number # 4 bytes (puede ser usado como numero de ack)
        self.total_datagrams = total_datagrams # 4 bytes
        self.content_size = content_size # 2 bytes
        self.content =  content.ljust(1315, b'0')  #  1315 bytes

    def get_datagram_bytes(self):
        format = '<BB32s100sIIH1315s'
        return struct.pack(format, self.datagram_type, self.number_of_sacks, self.sacks_content, self.file_name,
                           self.datagram_number, self.total_datagrams, self.content_size, self.content)

    @classmethod
    def create_content(cls, datagram_number, total_datagrams, content_size, content):
        return cls(datagram_type=TypeOfSackDatagram.CONTENT.value, number_of_sacks= 0,
                   sacks_content="", file_name="", datagram_number=datagram_number,
                   total_datagrams=total_datagrams, content_size=content_size, content=content)

    @classmethod
    def create_ack(cls, number_of_sack, sacks_content, ack_number):
        return cls(datagram_type=TypeOfSackDatagram.ACK.value, number_of_sacks=number_of_sack,
                   sacks_content=sacks_content, file_name="", datagram_number=ack_number, total_datagrams=0,
                   content_size=0, content=b"")

    @classmethod
    def create_download_datagram_for_client(cls, file_name):
        return cls(datagram_type=TypeOfSackDatagram.DOWNLOAD.value, number_of_sacks=0, sacks_content="",
                     file_name=file_name, datagram_number=0, total_datagrams=0, content_size=0, content=b"")
    @classmethod
    def create_upload_datagram_for_client(cls, file_name, total_datagrams):
        return  cls(datagram_type=TypeOfSackDatagram.UPLOAD.value, number_of_sacks=0, sacks_content="",
                     file_name=file_name, datagram_number=0, total_datagrams=total_datagrams, content_size=0,
                    content=b"")

    #Se usa cuando se un cliente desea descargar un archivo. El servidor le informa al cliente la info del archivo.
    @classmethod
    def create_file_info_datagram_for_server(cls, file_name, total_datagrams):
        return cls(datagram_type=TypeOfSackDatagram.DOWNLOAD.value,   number_of_sacks=0, sacks_content="",
                     file_name=file_name, datagram_number=0, total_datagrams=total_datagrams, content_size=0,
                   content=b"")

    

