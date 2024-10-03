import queue
import socket
import threading
#from lib.communications import Datagram, TypeOfDatagram, DatagramDeserialized, DATAGRAM_SIZE, FRAGMENT_SIZE
from lib.sack_communications import SACK_DATAGRAM_SIZE 

from lib.stop_and_wait import StopAndWait
from lib.selective_ack import SelectiveAck

class Server:
    def __init__(self, host, port, algorithm):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.clients = {}
        self.queues = {}
        self.running = True
        self.algorithm = algorithm

    def start(self):
        try:
            self.socket.bind((self.host, self.port))
            print(f"[SERVIDOR - Hilo principal] Servidor iniciado en: {self.host}:{self.port}")

        except socket.error as e:
            print(f"Error creando o bindeando el socket: {e}")
            return None

        while True:
            try:
                # print(f"[SERVIDOR - Hilo principal] Esperando mensajes")

                # En la espera de recibir un datagrama
                bytes_flow, client_address = self.socket.recvfrom(SACK_DATAGRAM_SIZE)
                #deserialized_datagram = DatagramDeserialized(bytes_flow)

                # print(f"[SERVIDOR - Hilo principal] Recibio mensaje para: {client_address}")

                if client_address not in self.clients:

                    new_client_queue = queue.Queue()
                    self.queues[client_address] = new_client_queue

                    new_client_thread = threading.Thread(target=self.client_thread, args=(client_address, new_client_queue))
                    
                    self.clients[client_address] = new_client_thread
                    
                    new_client_thread.start()
                    new_client_queue.put(bytes_flow)

                else:
                    self.queues[client_address].put(bytes_flow)

            except Exception as e:
                print(e)

    def client_thread(self, address, client_queue):
        print(f"[SERVIDOR - Hilo #{address}] Comienza a correr el thread del cliente")
        socket_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if self.algorithm == "sw":
            stop_and_wait =  StopAndWait.create_stop_and_wait_for_server(socket_client, address, client_queue)
            stop_and_wait.start_server()
        elif self.algorithm == "sack":
            selective_ack = SelectiveAck.create_selective_ack_for_server(socket_client, address, client_queue)
            selective_ack.start_server()
