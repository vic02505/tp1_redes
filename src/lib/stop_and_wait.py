import math
import queue
from socket import socket
from lib.communications import TypeOfDatagram, DatagramDeserialized, Datagram, FRAGMENT_SIZE, DATAGRAM_SIZE
import os
import time

from pexpect import TIMEOUT

TIMEOUT = 0.000000000000000000000000000000000000000000000005

class StopAndWait:
    def __init__(self, socket, destination_address, messages_queue, is_server):
        self.socket = socket
        self.address = destination_address
        self.queue = messages_queue
        self.is_server = is_server
        self.socket.settimeout(TIMEOUT)

    @classmethod
    def create_stop_and_wait_for_server(cls,socket, destination_address, messages_queue):
        return cls(socket=socket, destination_address=destination_address, messages_queue=messages_queue,
                   is_server=True)

    @classmethod
    def create_stop_and_wait_for_client(cls, socket, destination_address):
        return cls(socket=socket, destination_address=destination_address, messages_queue=None,
                   is_server=False)

    def start_server(self):
        try:
            deserialized_datagram = self.queue.get()

            print(f"[SERVIDOR - Hilo #{self.address}] Recibio mensaje de: {self.address}")

            if deserialized_datagram.datagram_type == TypeOfDatagram.HEADER_UPLOAD.value:
                self.send_ack(0)
                file_name = deserialized_datagram.file_name
                total_datagrams = deserialized_datagram.total_datagrams
                print(f"[SERVIDOR - Hilo #{self.address}] Inicio de subida de archivo: {file_name}")
                self.receive(total_datagrams, file_name)
            elif deserialized_datagram.datagram_type == TypeOfDatagram.HEADER_DOWNLOAD.value:
                file_name = deserialized_datagram.file_name
                file_size = os.path.getsize(file_name)
                total_datagrams = self.get_count_of_datagrams(file_name)
                download_header = Datagram.create_download_header_server(file_name, file_size, total_datagrams)
                self.socket.sendto(download_header.get_datagram_bytes(), self.address)
                print(f"[SERVIDOR - Hilo #{self.address}] Inicio de descarga de archivo: {file_name}")
                self.send(file_name)
            else:
                raise Exception("El primer mensaje no es un header")

        except Exception as e:
            raise e

    def get_count_of_datagrams(self, file_name):
        try:
            with open(file_name, "rb") as file:
                file_contents = file.read()
        except:
            raise "Archivo no encontrado"

        return math.ceil(len(file_contents) / FRAGMENT_SIZE)

    def start_client(self, file_name, datagram_type):
        if datagram_type == TypeOfDatagram.HEADER_UPLOAD.value:
            # TODO RECEPCION EFECTIVA DE ACK (TIMEOUT POR SI NO LO RECIBO, REENVIAR HEADER HASTA RECIBIR ACK
            file_size = os.path.getsize(file_name)
            total_datagrams = self.get_count_of_datagrams(file_name)
            upload_header = Datagram.create_upload_header_client(file_name,file_size, total_datagrams)
            sendTime = time.time()
            self.socket.sendto(upload_header.get_datagram_bytes(), self.address)
            datagram, client_address = self.socket.recvfrom(DATAGRAM_SIZE)
            recvTime = time.time()
            print(f"Tiempo de envio de header: {recvTime - sendTime}")

            firstTimeoutMeasure = recvTime - sendTime
            aproximateTimeout = firstTimeoutMeasure * 0.00000000000000005 # Tiempo limite hasta que se considere que se perdio el paquete

            self.send(file_name, aproximateTimeout)
        elif datagram_type == TypeOfDatagram.HEADER_DOWNLOAD.value:
            # TODO RECEPCION EFECTIVA DE ACK (TIMEOUT POR SI NO LO RECIBO, REENVIAR HEADER HASTA RECIBIR ACK
            download_header = Datagram.create_download_header_client(file_name)
            self.socket.sendto(download_header.get_datagram_bytes(), self.address)
            datagram, client_address = self.socket.recvfrom(DATAGRAM_SIZE)
            deserialized_datagram = DatagramDeserialized(datagram)
            total_datagrams = deserialized_datagram.total_datagrams
            file_name = deserialized_datagram.file_name
            self.receive(total_datagrams, file_name)
        else:
            raise Exception("El primer mensaje no es un header")

    def send_ack(self, ack_number):
        ack_datagram = Datagram.create_ack(ack_number)
        bytes = ack_datagram.get_datagram_bytes()
        self.socket.sendto(bytes, self.address)


    def receive(self, total_datagrams, file_name):
        received_data = []
        next_datagram_number = 0 # Numero de paquete que se espera recibir
        print(total_datagrams)
        while next_datagram_number < total_datagrams:
            if self.is_server:
                deserialized_datagram = self.queue.get()
                datagram_number = deserialized_datagram.datagram_number

            else:
                datagram, client_address = self.socket.recvfrom(DATAGRAM_SIZE)
                deserialized_datagram = DatagramDeserialized(datagram)
                datagram_number = deserialized_datagram.datagram_number

            # si recibo packete viejo es porque se perdio mi ack o tardo mucho en llegar
            if datagram_number != next_datagram_number:
                print(f"Reenviando ACK de paquete anterior numero", datagram_number)
                self.send_ack(datagram_number - 1)
                continue
            # Guardo paquete
            received_data.append(deserialized_datagram.content)
            # Envio de ack
            self.send_ack(next_datagram_number)
            next_datagram_number += 1

        # Unir todo el contenido de los datagramas
        file = b''.join(received_data)

        # Asegúrate de que el directorio 'server_files' exista
        os.makedirs(os.path.dirname('files/' + file_name), exist_ok=True)

        # Guardar el contenido en un archivo
        with open('files/' + file_name, 'wb') as f:
            f.write(file)

    def send(self, file_name, aproximateTimeout):

        try:
            with open(file_name, "rb") as file:
                file_contents = file.read()
        except:
            raise "Archivo no encontrado"

        datagrams = self.get_datagramas(file_contents)
        datagrams_sent = 0
        while datagrams_sent < len(datagrams):
            print(f"Enviando fragmento {datagrams[datagrams_sent].datagram_number} de {datagrams[datagrams_sent].total_datagrams}")


            # self.socket.settimeout(aproximateTimeout)
            # Enviar datagrama i
            self.socket.sendto(datagrams[datagrams_sent].get_datagram_bytes(), self.address)
            ack_number_received = False
            while not ack_number_received:
                if self.is_server:
                    # Esperar ack, si no recibo vuelvo a enviar datagrama
                    try:
                        deserialized_datagram = self.queue.get(timeout=TIMEOUT)
                        ack_number = deserialized_datagram.datagram_number
                        print(f"Recibido ack {ack_number}")
                        if ack_number == datagrams_sent:
                            ack_number_received = True
                    except queue.Empty:
                        print(f"Reenviando fragmento {datagrams[datagrams_sent].datagram_number} de {datagrams[datagrams_sent].total_datagrams}")
                        self.socket.sendto(datagrams[datagrams_sent].get_datagram_bytes(), self.address)
                else:
                    try:
                        datagram, client_address = self.socket.recvfrom(DATAGRAM_SIZE)
                        deserialized_datagram = DatagramDeserialized(datagram)
                        ack_number = deserialized_datagram.datagram_number
                        if ack_number == datagrams_sent:
                            ack_number_received = True
                    except socket.timeout:
                        print(f"Reenviando fragmento {datagrams[datagrams_sent].datagram_number} de {datagrams[datagrams_sent].total_datagrams}")
                        self.socket.sendto(datagrams[datagrams_sent].get_datagram_bytes(), self.address)
            datagrams_sent += 1

    def get_datagramas(self, file_contents):
        # Cantidad de fragmentos
        total_datagrams = math.ceil(len(file_contents) / FRAGMENT_SIZE)
        datagrams = []

        # Generamos los datagramas a enviar
        for i in range(total_datagrams):
            start = i * FRAGMENT_SIZE
            end = min(start + FRAGMENT_SIZE, len(file_contents))
            fragment = file_contents[start:end]
            datagram = Datagram.create_content(
                datagram_number=i,
                total_datagrams=total_datagrams,
                file_name="",
                datagram_size=end - start,
                content=fragment,
            )

            datagrams.append(datagram)

        return datagrams