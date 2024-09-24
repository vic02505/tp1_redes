import queue
import socket
import threading
from lib.communications import Datagram, TypeOfDatagram, DatagramDeserialized, DATAGRAM_SIZE

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
                    if total_datagrams == 0:
                        raise Exception("El total de datagramas es 0")

                    new_client_thread = threading.Thread(target=client_thread, args=(client_address, new_client_queue, self.protocolo, datagram_type, total_datagrams, file_name))
                    
                    self.clients[client_address] = new_client_thread
                    
                    new_client_thread.start()

                else:
                    self.queues[client_address].put(datagram)

            except Exception as e:
                print(e)

def client_thread(address, client_queue, protocol, datagram_type, total_datagrams, file_name):
    print(f"[SERVIDOR - Hilo #{address}] Comienza a correr el thread del cliente")
    socket_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Envio ACK del HS_UPLOAD
    ACK_datagram = Datagram.create_ack()
    bytes = ACK_datagram.get_datagram_bytes()
    socket_client.sendto(bytes, address)

    if protocol == "Stop and Wait" and datagram_type == TypeOfDatagram.HEADER_UPLOAD.value:
        stop_wait_receive(socket_client, address, client_queue, total_datagrams, file_name)
    elif protocol == "Stop and Wait" and datagram_type == TypeOfDatagram.HEADER_DOWNLOAD.value:
        stop_wait_send(socket_client, address, client_queue, total_datagrams, file_name)

def stop_wait_receive( socket_client, address, client_queue, total_datagrams, file_name):
    received_data = []
    print("Total de datagramas", total_datagrams)
    for i in range(total_datagrams):
        # Esperar paquete
        datagram = client_queue.get()
        datagram = DatagramDeserialized(datagram)

        # Guardo paquete
        received_data.append(datagram.content)

        # Envio de ack
        socket_client.sendto(Datagram.create_ack().get_datagram_bytes(), address)

    # Unir todo el contenido de los datagramas
    file = b''.join(received_data)

    # Guardar el contenido en un archivo
    with open(file_name, 'wb') as f:
        f.write(file)

def stop_wait_send(client_queue, address, socket_client, total_datagrams, file_name):
    paquet_number = 0
    paquet_total_size = 0
    while paquet_number < paquet_total_size:
        # saco paquete
        message = "Saco paquete"
        # envio paquete
        socket.sendto(message, address)
        # espero ack
        ack = client_queue.get()
