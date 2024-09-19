#crear main para iniciar el servidor
from sys import argv
from src.lib.server import Server

if __name__ == '__main__':

    if len(argv) != 3:
        print("Usage: python start_server.py <host> <port>")
        exit(1)

    server_host = argv[1]
    server_port = int(argv[2])
    print(server_host)
    print(server_port)
    server = Server(server_host, server_port)
    server.start()




