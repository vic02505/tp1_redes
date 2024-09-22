#crear main para iniciar el servidor
from sys import argv
from client import Client

if __name__ == '__main__':
    if len(argv) < 3:
        print("Use: python download.py <nombre_documento> <puerto_servidor>")
        exit(1)

    try:
        document_name = argv[1]
        server_port = int(argv[2])
        client = Client(document_name, server_port)
        client.connect()
        client.download()
        client.close()
    except Exception as e:
        print(f"Fallo el client al subir: {e}")
        exit(1)