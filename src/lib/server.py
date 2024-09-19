import queue
import socket
import threading

class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.clients = {}
        self.queues = {}                    # Colas de queues
        self.running = True

    def start(self):
        try:
            self.socket.bind((self.host, self.port))
            print(f"[SERVIDOR - Hilo principal] Servidor iniciado en: {self.host}:{self.port}")

        except socket.error as e:
            print(f"Error creando o bindeando el socket: {e}")
            return None

        while True:
            try:
                print(f"[SERVIDOR - Hilo principal] Esperando mensajes")
                data, client_address = self.socket.recvfrom(1024)
                print(f"[SERVIDOR - Hilo principal] Informacion recibida {client_address}: {data.decode()}")

                if client_address not in self.clients:
                    new_client_queue = queue.Queue()
                    # Agregar el thread del la conexion con el cliente al diccionario.
                    self.queues[client_address] = new_client_queue

                    #Add the client to the list of clients.
                    new_client_thread = threading.Thread(target=client_thread, args=(client_address, new_client_queue))
                    self.clients[client_address] = new_client_thread
                    new_client_thread.start()

                self.queues[client_address].put(data)

            except Exception as e:
                print(e)

def client_thread(address, client_queue):
    print(f"[SERVIDOR - Hilo #{address}]Comienza a correr el thread del cliente")
    socket_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
        print(f"[SERVIDOR - Hilo #{address}] Esperando nuevo mensaje")
        message = client_queue.get()
        print(f"[SERVIDOR - Hilo #{address}] Mensaje recibido: {message.decode()}")
        # Envio ACK
        # Proceso
        # Envio data
        socket_client.sendto(message, address) # Echo the data back to the client

