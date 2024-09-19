import socket

class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.host, self.port))
        self.clients = {}
        self.running = True

    def start(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            print("Socket created successfully")

            self.socket.bind((self.host, self.port))
            print(f"Server started at {self.host}:{self.port}")

        except socket.error as e:
            print(f"Error creating or binding the socket: {e}")
            return None

        while True:
            try:
                data, address = self.socket.recvfrom(1024)
                print(f"Received data from {address}: {data.decode()}")

                #if address not in self.clients:
                #Add the client to the list of clients

                self.socket.sendto(data, address) # Echo the data back to the client

            except Exception as e:
                print(e)
