import math

from exceptiongroup import catch

from src.lib.communications import TypeOfDatagram, DatagramDeserialized, Datagram, FRAGMENT_SIZE, DATAGRAM_SIZE
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
            datagram = self.queue.get()
            datagram = DatagramDeserialized(datagram)
            print(f"[SERVIDOR - Hilo #{self.address}] Recibio mensaje de: {self.address}")

            if datagram.datagram_type == TypeOfDatagram.HEADER_UPLOAD.value:
                self.send_ack(0)
                total_datagrams = datagram.total_datagrams
                file_name = datagram.file_name
                print(f"[SERVIDOR - Hilo #{self.address}] Inicio de subida de archivo: {self.file_name}")
                self.receive_server(total_datagrams, file_name)
            elif datagram.datagram_type == TypeOfDatagram.HEADER_DOWNLOAD.value:
                file_name = datagram.file_name
                print(f"[SERVIDOR - Hilo #{self.address}] Inicio de descarga de archivo: {self.file_name}")
                self.send(file_name)
            else:
                raise Exception("El primer mensaje no es un header")

        except Exception as e:
            raise(e)

    def start_client(self, filename):


    def send_ack(self, paquet_number):
        # Envio ACK del HS_UPLOAD
        ACK_datagram = Datagram.create_ack()
        bytes = ACK_datagram.get_datagram_bytes()
        self.socket.sendto(bytes, self.address)



    def receive_server(self, total_datagrams, file_name):
        received_data = []
        for i in range(total_datagrams):
            # Esperar paquete
            datagram = self.queue.get()
            datagram = DatagramDeserialized(datagram)

            # Guardo paquete
            received_data.append(datagram.content)

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
        try:
            with open('files/' + file_name, "rb") as file:
                file_contents = file.read()
        except:
            raise ("Archivo no encontrado")

        datagrams = self.get_datagramas(file_contents)

        # Envio ACK del HS_UPLOAD
        self.send_ack(0)
        self.socket.sendto(bytes, self.address)

        # Stop and wait
        for i in datagrams:
            print(f"Enviando fragmento {i.datagram_number} de {i.total_datagrams}")

            # Enviar datagrama i
            self.socket.sendto(i.get_datagram_bytes(), self.address)

            if self.is_server:
                datagram = self.queue.get()
            else:
                datagram, client_address = self.socket.recvfrom(DATAGRAM_SIZE)

            datagram = DatagramDeserialized(datagram)
            if datagram.datagram_type != TypeOfDatagram.ACK.value:
                print("Error en la comunicacion")
                return

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