#crear main para iniciar el servidor
from sys import argv
from lib.client import Client

if __name__ == '__main__':
    if len(argv) < 2:
        print("Use: python upload.py <nombre_documento> <puerto_servidor>")
        exit(1)
    
    try:
        file_name = argv[1]
        print(f"{file_name}")
        client = Client()
        client.upload(file_name)
        client.close()
    except Exception as e:
        print(f"Fallo el client al subir: {e}")
        exit(1)
