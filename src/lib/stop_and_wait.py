import math

from lib.communications import TypeOfDatagram, DatagramDeserialized, Datagram, FRAGMENT_SIZE, DATAGRAM_SIZE
import os

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
            self.socket.sendto(upload_header.get_datagram_bytes(), self.address)
            datagram, client_address = self.socket.recvfrom(DATAGRAM_SIZE)
            self.send(file_name)
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

    def send_ack(self, paquet_number):
        ACK_datagram = Datagram.create_ack()
        bytes = ACK_datagram.get_datagram_bytes()
        self.socket.sendto(bytes, self.address)


    def receive(self, total_datagrams, file_name):
        #TODO MANEJO DE ACK
        received_data = []
        for i in range(total_datagrams):
            # Esperar paquete
            if self.is_server:
                deserialized_datagram = self.queue.get()
            else:
                datagram, client_address = self.socket.recvfrom(DATAGRAM_SIZE) # no recibe aca
                deserialized_datagram = DatagramDeserialized(datagram)

            # Guardo paquete
            received_data.append(deserialized_datagram.content)
            # Envio de ack
            self.send_ack(0)

        # Unir todo el contenido de los datagramas
        file = b''.join(received_data)

        # Asegúrate de que el directorio 'server_files' exista
        os.makedirs(os.path.dirname('files/' + file_name), exist_ok=True)

        # Guardar el contenido en un archivo
        with open('files/' + file_name, 'wb') as f:
            f.write(file)

    def send(self, file_name):

        # TODO MANEJO DE ACK

        try:
            with open(file_name, "rb") as file:
                file_contents = file.read()
        except:
            raise "Archivo no encontrado"

        datagrams = self.get_datagramas(file_contents)

        # Stop and wait
        for i in datagrams:
            print(f"Enviando fragmento {i.datagram_number} de {i.total_datagrams}")

            # Enviar datagrama i
            self.socket.sendto(i.get_datagram_bytes(), self.address)
            if self.is_server:
                datagram = self.queue.get()
            else:
                datagram, client_address = self.socket.recvfrom(DATAGRAM_SIZE)

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