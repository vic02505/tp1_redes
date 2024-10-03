import math
import os

from PIL.ImImagePlugin import number
from lib.sw_communications import SwDatagram, SW_FRAGMENT_SIZE
from lib.sack_communications import SackDatagram, SACK_FRAGMENT_SIZE

# from lib.sack_communications import SackDatagram


def get_count_of_datagrams_sack(file_name):
    try:
        with open(file_name, "rb") as file:
            file_contents = file.read()
    except Exception as e:
        raise e

    return math.ceil(len(file_contents) / SACK_FRAGMENT_SIZE)

def get_count_of_datagrams_sw(file_name):
    try:
        with open(file_name, "rb") as file:
            file_contents = file.read()
    except:
        raise "Archivo no encontrado"

    return math.ceil(len(file_contents) / SW_FRAGMENT_SIZE)

def get_file_size(file_name):
    return os.path.getsize(file_name)

def get_file_content(file_name):
    try:
        with open(file_name, "rb") as file:
            file_contents = file.read()
        return file_contents
    except Exception as e:
        return e

def create_new_file(bytes_flow, file_name):
    file = b''.join(bytes_flow)

    os.makedirs(os.path.dirname('files/' + file_name), exist_ok=True)

    with open('files/' + file_name, 'wb') as f:
        f.write(file)

def get_datagrams_for_sack(file_contents):

    total_datagrams = math.ceil(len(file_contents) / SACK_FRAGMENT_SIZE)
    datagrams = []

    for i in range(total_datagrams):
        start = i * SACK_FRAGMENT_SIZE
        end = min(start + SACK_FRAGMENT_SIZE, len(file_contents))
        file_fragment = file_contents[start:end]

        datagram = SackDatagram.create_content(total_datagrams=total_datagrams,
                                               datagram_number=i+1, datagram_size=end-start, content=file_fragment,
                                               file_name="")
        datagrams.append(datagram)

    return datagrams


def get_datagrams_for_sw(file_contents):
    # Cantidad de fragmentos
    total_datagrams = math.ceil(len(file_contents) / SW_FRAGMENT_SIZE)
    datagrams = []

    # Generamos los datagramas a enviar
    for i in range(total_datagrams):
        start = i * SW_FRAGMENT_SIZE
        end = min(start + SW_FRAGMENT_SIZE, len(file_contents))
        fragment = file_contents[start:end]
        datagram = SwDatagram.create_content(
            datagram_number=i+1,
            total_datagrams=total_datagrams,
            file_name="",
            datagram_size=end - start,
            content=fragment,
        )

        datagrams.append(datagram)
    return datagrams

