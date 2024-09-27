import math
import os

FRAGMENT_SIZE = 40000

def get_count_of_datagrams(file_name):
    try:
        with open(file_name, "rb") as file:
            file_contents = file.read()
    except:
        raise "Archivo no encontrado"

    return math.ceil(len(file_contents) / FRAGMENT_SIZE)


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