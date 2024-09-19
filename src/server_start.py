#crear main para iniciar el servidor
from sys import argv
from server import Server

if __name__ == '__main__':
    server_host = argv[1]
    server_port = int(argv[2])
    server = Server(server_host, server_port)
    server.start()




