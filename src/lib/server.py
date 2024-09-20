import queue
import socket
import threading

class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.clients = {}
        self.queues = {}
        self.running = True
        self.protocolo = "Stop and Wait" or "Selective ACK"

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
                operation = data.operation
                print(f"[SERVIDOR - Hilo principal] Informacion recibida {client_address}: {data.decode()}")

                if client_address not in self.clients:
                    new_client_queue = queue.Queue()
                    # Agregar el thread del la conexion con el cliente al diccionario.
                    self.queues[client_address] = new_client_queue

                    #Add the client to the list of clients.
                    #new_client_thread = threading.Thread(target=client_thread, args=(client_address, new_client_queue, self.protocol, operation))
                    new_client_thread = threading.Thread(target=client_thread, args=(client_address, new_client_queue))
                    self.clients[client_address] = new_client_thread
                    new_client_thread.start()

                self.queues[client_address].put(data)

            except Exception as e:
                print(e)

def client_thread(address, client_queue, protocol, operation):
    print(f"[SERVIDOR - Hilo #{address}]Comienza a correr el thread del cliente")
    socket_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if protocol == "Stop and Wait" and operation == "upload":
        stop_wait_receive(socket_client, address, client_queue)
    elif protocol == "Stop and Wait" and operation == "download":
        stop_wait_send(socket_client, address, client_queue)

def stop_wait_receive(client_queue, address, socket_client):
    paquet_number = 0
    paquet_total_size = 0
    while paquet_number < paquet_total_size:
        # Esperar paquete
        message = client_queue.get()
        # guardo paquete
        # message.save()
        paquet_number += 1
        # envio ack
        socket_client.sendto(message, address)

def stop_wait_send(client_queue, address, socket_client):
    paquet_number = 0
    paquet_total_size = 0
    while paquet_number < paquet_total_size
        # saco paquete
        message = "Saco paquete"
        # envio paquete
        socket.sendto(message, address)
        # espero ack
        ack = client_queue.get()

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