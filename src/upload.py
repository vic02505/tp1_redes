#crear main para iniciar el servidor
from sys import argv
from client import Client

if __name__ == '__main__':
    if len(argv) < 2:
        print("Use: python upload.py <nombre_documento> <puerto_servidor>")
        exit(1)
    
    try:
        document_name = argv[1]
        # server_port = int(argv[2])
        client = Client()
        # client.connect()
        client.upload(document_name)
        client.close()
    except Exception as e:
        print(f"Fallo el client al subir: {e}")
        exit(1)
