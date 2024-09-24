import queue
import socket
import threading
import math
from communications import Datagram, TypeOfDatagram, DatagramDeserialized, FRAGMENT_SIZE

OK = 0

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
                data, client_address = self.socket.recvfrom(40117)
                rcvd_header = DatagramDeserialized(data)
                print(f"[SERVIDOR - Hilo principal] Recibio mensaje para: {client_address}")

                if client_address not in self.clients:
                    new_client_queue = queue.Queue()
                    # Agregar el thread del la conexion con el cliente al diccionario.
                    self.queues[client_address] = new_client_queue

                    #Add the client to the list of clients.
                    new_client_thread = threading.Thread(target=client_thread, args=(client_address, new_client_queue, rcvd_header))
                    #new_client_thread = threading.Thread(target=client_thread, args=(client_address, new_client_queue))
                    self.clients[client_address] = new_client_thread
                    
                    new_client_thread.start()

                    # self.queues[client_address].put(data)

                # Faltaba este else?
                else:
                    self.queues[client_address].put(data)

            except Exception as e:
                print(e)

# def client_thread(address, client_queue, protocol, operation):
#     print(f"[SERVIDOR - Hilo #{address}] Comienza a correr el thread del cliente")
#     socket_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

#     data = client_queue.get()
#     deserliazed_data = DatagramDeserialized(data)

#     ACK_datagram = Datagram.create_ack(deserliazed_data.packet_number)
#     bytes = ACK_datagram.get_datagram_bytes()
#     socket_client.sendto(bytes, address)

#     '''
#     if protocol == "Stop and Wait" and operation == "upload":
#         stop_wait_receive(socket_client, address, client_queue)
#     elif protocol == "Stop and Wait" and operation == "download":
#         stop_wait_send(socket_client, address, client_queue)
#     '''


def stop_wait_receive(client_queue, address, socket_client):
    paquet_number = 0
    paquet_total_size = 0
    while True:
        # Esperar paquete
        message = client_queue.get()
        # guardo paquete
        # message.save()
        paquet_number += 1
        # envio ack
        socket_client.sendto(Datagram.create_ack(), address)

def stop_wait_send(client_queue, address, socket_client):
    paquet_number = 0
    paquet_total_size = 0
    while paquet_number < paquet_total_size:
        # saco paquete
        message = "Saco paquete"
        # envio paquete
        socket.sendto(message, address)
        # espero ack
        ack = client_queue.get()

def client_thread(address, client_queue, rcvd_header):
    print(f"[SERVIDOR - Hilo #{address}]Comienza a correr el thread del cliente")
    
    
    
    socket_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    ACK_datagram = Datagram.create_ack(OK)
    bytes = ACK_datagram.get_datagram_bytes()
    socket_client.sendto(bytes, address)

    # El True tiene que ser remplazado por la cant de datagramas que se van a enviar en el header
    i = 0
    rcvd_bytes = b""
    for i in range(math.ceil(rcvd_header.file_size / FRAGMENT_SIZE)):
        # print(f"[SERVIDOR - Hilo #{address}] Esperando nuevo mensaje")
        message = client_queue.get()
        datagrama = DatagramDeserialized(message)
        print(f"[SERVIDOR - Hilo #{address}] Mensaje recibido datagrama completo: {datagrama.file_name}")
        print(f"[SERVIDOR - Hilo #{address}] Mensaje recibido datagrama completo: {datagrama.packet_size}")
        rcvd_bytes += datagrama.content
        ACK_datagram = Datagram.create_ack(datagrama.packet_number)
        bytes = ACK_datagram.get_datagram_bytes()
        socket_client.sendto(bytes, address)



    file_name = "server_files" + datagrama.file_name
    with open(file_name, 'wb') as file:
        file.write(rcvd_bytes)
        print(f"[SERVIDOR - Hilo #{address}] Archivo {datagrama.file_name} creado y guardado correctamente.")

        # Envio ACK
        # Proceso
        # Envio data