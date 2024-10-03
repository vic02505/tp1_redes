import time

from lib.sw_communications import TypeOfSwDatagram, SwDatagramDeserialized, SwDatagram, SW_DATAGRAM_SIZE
import lib.files_management as files_management
import logging

TIMEOUT_CLIENT = 0.1
TIMEOUT_SERVER = 0.1

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
        deserialized_datagram = SwDatagramDeserialized(self.queue.get())
        logging.info(print(f"[SERVIDOR - Hilo #{self.address}] Iniciando conexión con el cliente"))

        if deserialized_datagram.datagram_type == TypeOfSwDatagram.HEADER_UPLOAD.value:
            file_name = deserialized_datagram.file_name
            total_datagrams = deserialized_datagram.total_datagrams
            datagram_number = deserialized_datagram.datagram_number
            logging.info(print(f"[SERVIDOR - Hilo #{self.address}] El cliente solicita cargar el archivo: {file_name}"))
            self.send_ack(datagram_number)
            logging.info(print(f"[SERVIDOR - Hilo #{self.address}] Solicitud de carga aceptada"))
            self.receive_server_file(total_datagrams, file_name, datagram_number)
        elif deserialized_datagram.datagram_type == TypeOfSwDatagram.HEADER_DOWNLOAD.value:
            file_name = deserialized_datagram.file_name
            file_size = files_management.get_file_size(file_name)

            logging.info(print(f"[SERVIDOR - Hilo #{self.address}] El cliente desea descargar el archivo: {file_name}"))

            total_datagrams = files_management.get_count_of_datagrams_sw(file_name)
            ack_with_data = SwDatagram.create_download_header_server(file_name, file_size, total_datagrams)
            self.socket.sendto(ack_with_data.get_datagram_bytes(), self.address)
            self.wait_ack(ack_with_data)
            logging.info(print(f"[SERVIDOR - Hilo #{self.address}] Solicitud de descarga aceptada"))
            self.send_server_file(file_name)
        else:
            raise Exception("El primer mensaje no es un header")

    # Inicio de client
    def start_client(self, file_name, datagram_type):
        self.socket.settimeout(TIMEOUT_CLIENT)
        if datagram_type == TypeOfSwDatagram.HEADER_UPLOAD.value:
            # Armo el header UPLOAD
            file_size = files_management.get_file_size(file_name)
            total_datagrams = files_management.get_count_of_datagrams_sw(file_name)
            upload_header = SwDatagram.create_upload_header_client(file_name, file_size, total_datagrams)

            # Envio el header
            self.socket.sendto(upload_header.get_datagram_bytes(), self.address)
            logging.info(print("[Cliente] Solicitud de carga de archivo enviada al servidor "))
            # Espero el ACK
            self.wait_ack(upload_header)
            logging.info(print("[Cliente] Solicitud de carga de archivo aceptada por el servidor"))
            # Comienzo a enviar el file
            self.send_client_file(file_name)
        elif datagram_type == TypeOfSwDatagram.HEADER_DOWNLOAD.value:
            # Armo el header DOWNLOAD

            download_header = SwDatagram.create_download_header_client(file_name)

            # Envio el header
            self.socket.sendto(download_header.get_datagram_bytes(), self.address)

            logging.info(print(["[Cliente] Solucitud de descarga de archivo enviada al servidor"]))

            # Espero el ACK
            ack_with_data = self.wait_ack(download_header)

            logging.info(print(["[Cliente] Solucitud de descarga de archivo aceptada por el servidor"]))

            # Send ack
            self.send_ack(ack_with_data.datagram_number)

            self.socket.settimeout(None)

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
                    ack_deserialized = SwDatagramDeserialized(self.queue.get(timeout=TIMEOUT_SERVER))
                else:
                    ack, client_address = self.socket.recvfrom(SW_DATAGRAM_SIZE)
                    ack_deserialized = SwDatagramDeserialized(ack)
                if ack_deserialized.datagram_number == datagram.datagram_number:
                    return ack_deserialized
            # Excepción por timeout
            except Exception:
                self.socket.sendto(datagram.get_datagram_bytes(), self.address)

    # Send ack: envia un ack y espera que llegue un paquete distinto al ack_number
    def send_ack(self, ack_number):
        # Envio el ack
        ack_datagram = SwDatagram.create_ack(ack_number)
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
        datagrams =  files_management.get_datagrams_for_sw(file_contents)

        logging.info("[CLIENTE] Iniciando envío de archivo")

        begin = time.time()

        # Enviamos los datagramas
        for datagram in datagrams:
            self.socket.sendto(datagram.get_datagram_bytes(), self.address)
            self.wait_ack(datagram)

        end = time.time()
        sending_time = end - begin
        logging.info(f"[CLIENTE] Archivo enviado con éxito en {sending_time}segs")


    def receive_server_file(self, total_datagrams, file_name, datagram_number):
        received_data = []

        logging.info(print(f"[SERVIDOR - Hilo #{self.address}] Iniciando recepción de archivo"))
        begin = time.time()

        for i in range(1, total_datagrams + 1):
            datagram_deserialized = SwDatagramDeserialized(self.queue.get())
            while i != datagram_deserialized.datagram_number:
                self.send_ack(datagram_deserialized.datagram_number)
                datagram_deserialized = SwDatagramDeserialized(self.queue.get())
            received_data.append(datagram_deserialized.content)
            self.send_ack(datagram_deserialized.datagram_number)

        end = time.time()
        receiving_time = end - begin

        files_management.create_new_file(received_data, file_name)
        logging.info(print(f"[SERVIDOR - Hilo #{self.address}] Recibido con éxito el archivo {file_name} en " 
                           f"{receiving_time}segs"))

    # Operaciones para el DOWNLOAD
    def recive_client_file(self, total_datagrams, file_name):
        received_data = []

        logging.info(print("[CLIENTE] Iniciando recepción de archivo"))
        begin = time.time()

        for i in range(1, total_datagrams + 1):
            # Aca falta un try catch  (para mi no)
            datagram_deserialized = SwDatagramDeserialized(self.socket.recv(SW_DATAGRAM_SIZE))
            while i != datagram_deserialized.datagram_number:
                self.send_ack(datagram_deserialized.datagram_number)
                datagram_deserialized = SwDatagramDeserialized(self.socket.recv(SW_DATAGRAM_SIZE))
            received_data.append(datagram_deserialized.content)
            self.send_ack(datagram_deserialized.datagram_number)

        end = time.time()
        receiving_time = end - begin

        files_management.create_new_file(received_data, file_name)
        logging.info(print(f"[Cliente] Descarga realizada con éxito en {receiving_time}segs"))

    def send_server_file(self, file_name):
        # Busca el archivo.
        try:
            file_contents = files_management.get_file_content(file_name)
        except:
            raise "Archivo no encontrado"

        # Obtenemos los datagramas
        datagrams = files_management.get_datagrams_for_sw(file_contents)

        logging.info(print(f"[SERVIDOR - Hilo #{self.address}] Iniciando envío de archivo"))
        begin = time.time()

        # Enviamos los datagramas
        for datagram in datagrams:
            self.socket.sendto(datagram.get_datagram_bytes(), self.address)
            self.wait_ack(datagram)

        end = time.time()
        sending_time = end - begin
        logging.info(print(f"[SERVIDOR - Hilo #{self.address}] Archivo enviado con éxito en {sending_time}segs"))
