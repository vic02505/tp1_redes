import math
import queue
import sys
from socket import socket
from lib.communications import TypeOfDatagram, DatagramDeserialized, Datagram, FRAGMENT_SIZE, DATAGRAM_SIZE
import lib.files_management as files_management

TIMEOUT_CLIENT = 0.5
TIMEOUT_SERVER = 0.5


class StopAndWait:
    def __init__(self, socket, destination_address, messages_queue, is_server):
        self.socket = socket
        self.address = destination_address
        self.queue = messages_queue
        self.is_server = is_server

    # Funciones constructoras
    @classmethod
    def create_stop_and_wait_for_server(cls, socket, destination_address, messages_queue):
        return cls(socket=socket, destination_address=destination_address, messages_queue=messages_queue,
                   is_server=True)

    @classmethod
    def create_stop_and_wait_for_client(cls, socket, destination_address):
        return cls(socket=socket, destination_address=destination_address, messages_queue=None,
                   is_server=False)

    # Inicio server
    def start_server(self):
        deserialized_datagram = self.queue.get()
        print(f"[SERVIDOR - Hilo #{self.address}] Recibio mensaje de: {self.address}")

        if deserialized_datagram.datagram_type == TypeOfDatagram.HEADER_UPLOAD.value:
            file_name = deserialized_datagram.file_name
            total_datagrams = deserialized_datagram.total_datagrams
            datagram_number = deserialized_datagram.datagram_number
            self.send_ack(datagram_number)
            self.receive_server_file(total_datagrams, file_name, datagram_number)
        elif deserialized_datagram.datagram_type == TypeOfDatagram.HEADER_DOWNLOAD.value:
            file_name = deserialized_datagram.file_name
            file_size = files_management.get_file_size(file_name)

            print(f"[SERVIDOR - Hilo #{self.address}] Inicio de descarga de archivo: {file_name}")

            total_datagrams = files_management.get_count_of_datagrams(file_name)
            ack_with_data = Datagram.create_download_header_server(file_name, file_size, total_datagrams)
            self.socket.sendto(ack_with_data.get_datagram_bytes(), self.address)
            self.wait_ack(ack_with_data)
            self.send_server_file(file_name)
        else:
            raise Exception("El primer mensaje no es un header")

    # Inicio de client
    def start_client(self, file_name, datagram_type):
        self.socket.settimeout(TIMEOUT_CLIENT)
        print(f"[Cliente - {self.address}] Inicializando SW para cliente")
        if datagram_type == TypeOfDatagram.HEADER_UPLOAD.value:
            print(f"[Cliente - {self.address}] Accion a realizar: Carga de un archivo al servidor")

            # Armo el header UPLOAD
            file_size = files_management.get_file_size(file_name)
            total_datagrams = files_management.get_count_of_datagrams(file_name)
            print(f"EL NUMERO DE DATAGRAMAS ES {total_datagrams}")
            upload_header = Datagram.create_upload_header_client(file_name, file_size, total_datagrams)

            # Envio el header
            self.socket.sendto(upload_header.get_datagram_bytes(), self.address)
            # Espero el ACK
            self.wait_ack(upload_header)
            # Comienzo a enviar el file
            self.send_client_file(file_name)
        elif datagram_type == TypeOfDatagram.HEADER_DOWNLOAD.value:
            # Armo el header DOWNLOAD
            download_header = Datagram.create_download_header_client(file_name)

            # Envio el header
            self.socket.sendto(download_header.get_datagram_bytes(), self.address)

            # Espero el ACK
            ack_with_data = self.wait_ack(download_header)

            # Send ack
            self.send_ack(ack_with_data.datagram_number)

            # Comienzo a recibir el archivo
            self.recive_client_file(ack_with_data.total_datagrams, ack_with_data.file_name)
        else:
            raise Exception("El primer mensaje no es un header")

    # Wait ack: espera que llegue un ack, si no llega, reenvia el datagrama
    def wait_ack(self, datagram):
        # Mientras no recibo el ack, mando de vuelta el datagram
        while True:
            try:
                if self.is_server:
                    ack_deserialized = self.queue.get()
                else:
                    ack, client_address = self.socket.recvfrom(DATAGRAM_SIZE)
                    ack_deserialized = DatagramDeserialized(ack)
                if ack_deserialized.datagram_number == datagram.datagram_number:
                    print(f"[Cliente - {self.address}] Recibi ACK correcto")
                    return ack_deserialized
            # Excepción por timeout
            except Exception:
                print(f"[Cliente - {self.address}] Timeout alcanzado esperando ACK")
                self.socket.sendto(datagram.get_datagram_bytes(), self.address)
                print(f"[Cliente - {self.address}] Datagrama enviado nuevamente")

    # Send ack: envia un ack y espera que llegue un paquete distinto al ack_number
    def send_ack(self, ack_number):
        # Envio el ack
        ack_datagram = Datagram.create_ack(ack_number)
        bytes = ack_datagram.get_datagram_bytes()
        self.socket.sendto(bytes, self.address)

    # Operaciones para el UPLOAD
    def send_client_file(self, file_name):
        # Busca el archivo.
        try:
            file_contents = files_management.get_file_content(file_name)
        except:
            raise "Archivo no encontrado"

        # Obtenemos los datagramas
        # FIX datagram number o binario
        datagrams = files_management.get_datagramas(file_contents)

        # Enviamos los datagramas
        for datagram in datagrams:
            print(f"[Cliente - {self.address}] Enviando datagrama {datagram.datagram_number} de " f"{datagram.total_datagrams}")
            self.socket.sendto(datagram.get_datagram_bytes(), self.address)
            self.wait_ack(datagram)

    def receive_server_file(self, total_datagrams, file_name, datagram_number):
        received_data = []
        for i in range(1, total_datagrams + 1):
            datagram_deserialized = self.queue.get()
            while i != datagram_deserialized.datagram_number:
                print(f"[SERVIDOR - Hilo #{self.address}] Ya recibí este datagrama  {datagram_deserialized.datagram_number}")
                self.send_ack(datagram_deserialized.datagram_number)
                datagram_deserialized = self.queue.get()
            received_data.append(datagram_deserialized.content)
            self.send_ack(datagram_deserialized.datagram_number)

        print(f"[SERVIDOR - Hilo #{self.address}] Creado con éxito el archivo {file_name}")
        files_management.create_new_file(received_data, file_name)

    # Operaciones para el DOWNLOAD
    def recive_client_file(self, total_datagrams, file_name):
        received_data = []
        for i in range(1, total_datagrams + 1):
            datagram_deserialized = DatagramDeserialized(self.socket.recv(DATAGRAM_SIZE))
            while i != datagram_deserialized.datagram_number:
                print(f"[Cliente - {self.address}] Ya recibí este datagrama  {datagram_deserialized.datagram_number}")
                self.send_ack(datagram_deserialized.datagram_number)
                datagram_deserialized = DatagramDeserialized(self.socket.recv(DATAGRAM_SIZE))
            received_data.append(datagram_deserialized.content)
            self.send_ack(datagram_deserialized.datagram_number)

        print(f"[Cliente - {self.address}] Descarga realizada con éxito")
        files_management.create_new_file(received_data, file_name)

    def send_server_file(self, file_name):
        # Busca el archivo.
        try:
            file_contents = files_management.get_file_content(file_name)
        except:
            raise "Archivo no encontrado"

        # Obtenemos los datagramas
        datagrams = files_management.get_datagramas(file_contents)

        # Enviamos los datagramas
        for datagram in datagrams:
            print(f"[SERVIDOR - Hilo #{self.address}] Datagrama {datagram.datagram_number} de " f"{datagram.total_datagrams}")
            self.socket.sendto(datagram.get_datagram_bytes(), self.address)
            self.wait_ack(datagram)
