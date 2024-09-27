import math
import queue
from socket import socket
from lib.communications import TypeOfDatagram, DatagramDeserialized, Datagram, FRAGMENT_SIZE, DATAGRAM_SIZE
import os
import time
import lib.files_management as files_management

TIMEOUT = 2

class SelectiveACK:
    def __init__(self, socket, destination_address, messages_queue, is_server):
        self.socket = socket
        self.address = destination_address
        self.queue = messages_queue
        self.is_server = is_server

    @classmethod
    def create_selective_ack_for_server(cls,socket, destination_address, messages_queue):
        return cls(socket=socket, destination_address=destination_address, messages_queue=messages_queue,
                   is_server=True)
    
    @classmethod
    def create_selective_ack_for_client(cls, socket, destination_address):
        return cls(socket=socket, destination_address=destination_address, messages_queue=None,
                   is_server=False)
    
    def start_server():
        # TODO: Implementar
        return

    def start_client(self, file_name, datagram_type):
        print(f"[Cliente - {self.address}] Inicializando Selective ACK para cliente")
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
        



    def send(self, file_name, aproximateTimeout):

        try:
            file_contents = files_management.get_file_content(file_name)
        except:
            raise "Archivo no encontrado"

        datagrams = self.get_datagramas(file_contents)
        datagrams_sent = 0

        self.socket.settimeout(aproximateTimeout)

        # Envio todos los datagramas de una
        for datagram_sent in len(datagrams):
            print(f"Enviando fragmento {datagrams[datagrams_sent].datagram_number} de "
                f"{datagrams[datagrams_sent].total_datagrams}")
            self.socket.sendto(datagrams[datagrams_sent].get_datagram_bytes(), self.address)

        self.manage_all_ack_receptions_for_sending_operation(datagrams, datagrams_sent)

    

    def manage_all_ack_receptions_for_sending_operation(self, datagrams_list, actual_datagram):

        # TODO: Este hay que cambiarlo para que quede como queremos
        ack_received = 0

        while ack_received < len(datagrams_list):
            if self.is_server:
                try:
                    deserialized_datagram = self.queue.get(timeout=TIMEOUT)
                    ack_number = deserialized_datagram.datagram_number
                    print(f"Recibido ack {ack_number}")
                    ack_received += 1
                except queue.Empty:
                    self.socket.sendto(datagrams_list[actual_datagram].get_datagram_bytes(), self.address)
                    continue
            else:
                try:
                    self.socket.recvfrom(DATAGRAM_SIZE)
                    ack_received += 1

                except Exception as e:
                    self.socket.sendto(datagrams_list[actual_datagram].get_datagram_bytes(), self.address)


    def send_missing_datagram(self, datagram_to_send):
        print(f"Reenviando fragmento {datagram_to_send.datagram_number} de "
                    f"{datagram_to_send.total_datagrams}")
        self.socket.sendto(datagram_to_send.get_datagram_bytes(), self.address)

    def recv():
        return