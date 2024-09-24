import queue
import socket
import threading
from lib.communications import Datagram, TypeOfDatagram, DatagramDeserialized, DATAGRAM_SIZE, FRAGMENT_SIZE
from lib.stop_and_wait import StopAndWait

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
                bytes_flow, client_address = self.socket.recvfrom(DATAGRAM_SIZE)
                deserialized_datagram = DatagramDeserialized(bytes_flow)

                print(f"[SERVIDOR - Hilo principal] Recibio mensaje para: {client_address}")

                if client_address not in self.clients:

                    new_client_queue = queue.Queue()
                    self.queues[client_address] = new_client_queue

                    if ((deserialized_datagram.datagram_type != TypeOfDatagram.HEADER_UPLOAD.value)
                            and (deserialized_datagram.datagram_type != TypeOfDatagram.HEADER_DOWNLOAD.value)):
                        raise Exception("El primer mensaje no es un header")

                    new_client_thread = threading.Thread(target=client_thread, args=(client_address, new_client_queue))
                    
                    self.clients[client_address] = new_client_thread
                    
                    new_client_thread.start()
                    new_client_queue.put(deserialized_datagram)

                else:
                    self.queues[client_address].put(deserialized_datagram)

            except Exception as e:
                print(e)

def client_thread(address, client_queue):
    print(f"[SERVIDOR - Hilo #{address}] Comienza a correr el thread del cliente")
    socket_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    stop_and_wait =  StopAndWait.create_stop_and_wait_for_server(socket_client, address, client_queue)
    stop_and_wait.start_server()
