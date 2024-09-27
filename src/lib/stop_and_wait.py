import math
import queue
from socket import socket
from lib.communications import TypeOfDatagram, DatagramDeserialized, Datagram, FRAGMENT_SIZE, DATAGRAM_SIZE
import os
import time
import src.lib.files_management as files_management

TIMEOUT = 2


class StopAndWait:
    def __init__(self, socket, destination_address, messages_queue, is_server):
        self.socket = socket
        self.address = destination_address
        self.queue = messages_queue
        self.is_server = is_server

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
                #self.send_ack(0)
                file_name = deserialized_datagram.file_name
                total_datagrams = deserialized_datagram.total_datagrams
                print(f"[SERVIDOR - Hilo #{self.address}] Inicio de subida de archivo: {file_name}")
                ack = Datagram.create_ack(0)
                self.socket.sendto(ack.get_datagram_bytes(), self.address)
                self.receive(total_datagrams, file_name)
            elif deserialized_datagram.datagram_type == TypeOfDatagram.HEADER_DOWNLOAD.value:
                file_name = deserialized_datagram.file_name
                file_size = os.path.getsize(file_name)
                total_datagrams = files_management.get_count_of_datagrams(file_name)
                download_header = Datagram.create_download_header_server(file_name, file_size, total_datagrams)
                self.socket.sendto(download_header.get_datagram_bytes(), self.address)
                print(f"[SERVIDOR - Hilo #{self.address}] Inicio de descarga de archivo: {file_name}")
                self.send(file_name, 0.0005)
            else:
                raise Exception("El primer mensaje no es un header")

        except Exception as e:
            raise e

    def start_client(self, file_name, datagram_type):
        print(f"[Cliente - {self.address}] Inicializando SW para cliente")
        if datagram_type == TypeOfDatagram.HEADER_UPLOAD.value:
            print(f"[Cliente - {self.address}] Accion a realizar: Carga de un archivo al servidor")
            file_size = files_management.get_file_size(file_name)
            total_datagrams = files_management.get_count_of_datagrams(file_name)
            upload_header = Datagram.create_upload_header_client(file_name,file_size, total_datagrams)

            print(f"[Cliente - {self.address}] Enviando solicitud de carga al servidor")
            self.socket.settimeout(0.5)
            self.socket.sendto(upload_header.get_datagram_bytes(), self.address)

            upload_accepted = False
            while not upload_accepted:
                try:
                    print(f"[Cliente - {self.address}] Espero por la confirmacion del servidor")
                    self.socket.settimeout(4)
                    datagram, client_address = self.socket.recvfrom(DATAGRAM_SIZE)
                    print(f"[Cliente - {self.address}] Recibi algo")
                    #receiving_time = time.time()
                    deserialized_datagram = DatagramDeserialized(datagram)
                    print(f"TIPO DE MENSAJE {deserialized_datagram.datagram_type}")
                    if deserialized_datagram.datagram_type == TypeOfDatagram.ACK.value:
                        upload_accepted = True
                        print(f"[Cliente - {self.address}] Recibi la confirmacion del servidor")

                except Exception as e:
                    print(f"[Cliente - {self.address}] Timeout alcanzado en la confirmacion del upload")
                    self.socket.sendto(upload_header.get_datagram_bytes(), self.address)
                    print(f"[Cliente - {self.address}] Solicitud de upload enviada de vuelta")


            #first_timeout_measure = receiving_time - start_time
            #approximate_timeout = first_timeout_measure  * 1.5 # Tiempo limite hasta que se considere que se perdio el paquete

            print("CLIENTE: CONFIRMACION RECIBIDA CORRECTAMENTE, SE INICIA ENVIO DEL ARCHIVO")

            self.send(file_name, 3)
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

                if deserialized_datagram.datagram_type == TypeOfDatagram.HEADER_UPLOAD.value:
                    print(f"[Servidor - Hilo #{self.address}] El cliente no recibio la confirmacion del upload")
                    self.send_ack(0)
                    continue

                print(f"[Servidor - Hilo #{self.address}] Recibi paquete posta")
                datagram_number = deserialized_datagram.datagram_number
                print(f"[Servidor - Hilo #{self.address}] Recibido paquete numero {datagram_number}/{total_datagrams}")

            else:
                datagram, client_address = self.socket.recvfrom(DATAGRAM_SIZE)
                deserialized_datagram = DatagramDeserialized(datagram)
                datagram_number = deserialized_datagram.datagram_number

            if datagram_number != next_datagram_number:
                print(f"Reenviando ACK de paquete anterior numero", datagram_number)
                self.send_ack(datagram_number)
                continue

            received_data.append(deserialized_datagram.content)
            self.send_ack(next_datagram_number)
            next_datagram_number += 1

        files_management.create_new_file(received_data, file_name)


    def manage_ack_reception_for_sending_operation(self, datagrams_list, actual_datagram):

        ack_received = False
        while not ack_received:
            if self.is_server:
                try:
                    deserialized_datagram = self.queue.get(timeout=TIMEOUT)
                    ack_number = deserialized_datagram.datagram_number
                    print(f"Recibido ack {ack_number}")
                    ack_received = True
                except queue.Empty:
                    self.socket.sendto(datagrams_list[actual_datagram].get_datagram_bytes(), self.address)
                    continue
            else:
                try:
                    self.socket.recvfrom(DATAGRAM_SIZE)
                    ack_received = True

                except Exception as e:
                    self.socket.sendto(datagrams_list[actual_datagram].get_datagram_bytes(), self.address)


    def send(self, file_name, aproximateTimeout):

        try:
                file_contents = files_management.get_file_content(file_name)
        except:
            raise "Archivo no encontrado"

        datagrams = self.get_datagramas(file_contents)
        datagrams_sent = 0

        self.socket.settimeout(4)

        while datagrams_sent < len(datagrams):
            print(f"Enviando fragmento {datagrams[datagrams_sent].datagram_number} de "
                  f"{datagrams[datagrams_sent].total_datagrams}")

            self.socket.sendto(datagrams[datagrams_sent].get_datagram_bytes(), self.address)
            self.manage_ack_reception_for_sending_operation(datagrams, datagrams_sent)
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