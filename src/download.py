#crear main para iniciar el servidor
from sys import argv
from lib.client import Client
import os 

if __name__ == '__main__':
    try:
        file_name = argv[1]
        client = Client()
        client.download(file_name)
        client.close()
    except Exception as e:
        print(f"Fallo el client al subir: {e}")
        exit(1)