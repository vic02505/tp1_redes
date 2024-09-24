import queue
import socket
import threading
from lib.communications import Datagram, TypeOfDatagram, DatagramDeserialized, DATAGRAM_SIZE, FRAGMENT_SIZE
import math
import os
from stop_and_wait import StopAndWait

class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.clients = {}
        self.queues = {}
        self.running = True
        self.protocolo = "Stop and Wait"

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

                # En la espera de recibir un datagrama
                datagram, client_address = self.socket.recvfrom(DATAGRAM_SIZE)

                print(f"[SERVIDOR - Hilo principal] Recibio mensaje para: {client_address}")

                if client_address not in self.clients:
                    # Creamos la queue que el hilo del cliente va a utilizar
                    new_client_queue = queue.Queue()

                    # Agregar el thread del la conexion con el cliente al diccionario.
                    self.queues[client_address] = new_client_queue

                    #Add the client to the list of clients.
                    datagram = DatagramDeserialized(datagram)
                    datagram_type = datagram.datagram_type
                    if datagram_type != TypeOfDatagram.HEADER_UPLOAD.value and datagram_type != TypeOfDatagram.HEADER_DOWNLOAD.value:
                        raise Exception("El primer mensaje no es un header")
                    
                    total_datagrams = datagram.total_datagrams
                    file_name = datagram.file_name

                    new_client_thread = threading.Thread(target=client_thread, args=(client_address, new_client_queue))
                    
                    self.clients[client_address] = new_client_thread
                    
                    new_client_thread.start()

                else:
                    self.queues[client_address].put(datagram)

            except Exception as e:
                print(e)

def client_thread(address, client_queue):
    print(f"[SERVIDOR - Hilo #{address}] Comienza a correr el thread del cliente")
    socket_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    StopAndWait(socket_client, address, client_queue).start()
