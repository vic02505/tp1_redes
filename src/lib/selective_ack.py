from socket import socket
from lib.sack_communications import TypeOfSackDatagram, SackDatagramDeserialized, SackDatagram, SACK_DATAGRAM_SIZE
import lib.files_management as files_management

# Delete import
import random

TIMEOUT_CLIENT = 0.1
TIMEOUT_SERVER = 0.1
WINDOWS_SIZE = 5
MAX_ACK_REPETITIONS = 2


class SelectiveAck:
    def __init__(self, socket, destination_address, messages_queue, is_server):
        self.socket = socket
        self.address = destination_address
        self.queue = messages_queue
        self.is_server = is_server
        self.window_size = WINDOWS_SIZE

    # Funciones constructoras
    @classmethod
    def create_selective_ack_for_server(cls, socket, destination_address, messages_queue):
        return cls(socket=socket, destination_address=destination_address, messages_queue=messages_queue,
                   is_server=True)

    @classmethod
    def create_selective_ack_for_client(cls, destination_address, socket):
        return cls(socket=socket, destination_address=destination_address, messages_queue=None,
                   is_server=False)

    # Inicio server
    def start_server(self):
        deserialized_datagram = SackDatagramDeserialized(self.queue.get())
        print(f"[SERVIDOR - Hilo #{self.address}] Recibio mensaje de: {self.address}")

        if deserialized_datagram.datagram_type == TypeOfSackDatagram.HEADER_UPLOAD.value:
            self._start_server_upload(deserialized_datagram)
        elif deserialized_datagram.datagram_type == TypeOfSackDatagram.HEADER_DOWNLOAD.value:
            self._start_server_download(deserialized_datagram)
        else:
            raise Exception(f"[SERVIDOR - Hilo #{self.address}] El primer mensaje no es del tipo esperado (HEADER)")

    def _start_server_download(self, deserialized_datagram):
        file_name = deserialized_datagram.file_name
        file_size = files_management.get_file_size(file_name)

        print(f"[SERVIDOR - Hilo #{self.address}] Iniciando descarga del archivo: {file_name}")

        total_datagrams = files_management.get_count_of_datagrams_sack(file_name)
        ack_with_data = SackDatagram.create_download_header_server(file_name, file_size, total_datagrams)

        self.socket.sendto(ack_with_data.get_datagram_bytes(), self.address)
        self.wait_ack(ack_with_data)
        self.sending_operation(file_name)

    def _start_server_upload(self, deserialized_datagram):
        file_name = deserialized_datagram.file_name
        total_datagrams = deserialized_datagram.total_datagrams
        datagram_number = deserialized_datagram.datagram_number
        self.send_ack(datagram_number)
        self.receiving_operation(total_datagrams, file_name)

    # Inicio de client
    def start_client(self, file_name, datagram_type):
        print(f"[Cliente] Iniciando conexion con el servidor: {self.address}")
        self.socket.settimeout(TIMEOUT_CLIENT)
        if datagram_type == TypeOfSackDatagram.HEADER_UPLOAD.value:
            self._start_client_upload(file_name)
        elif datagram_type == TypeOfSackDatagram.HEADER_DOWNLOAD.value:
            self._start_client_download(file_name)
        else:
            raise Exception(f"[Cliente - {self.address}] El primer mensaje no es del tipo esperado (HEADER)")

    def _start_client_download(self, file_name):
        # Armo el header DOWNLOAD
        download_header = SackDatagram.create_download_header_client(file_name)

        # Envio el header
        self.socket.sendto(download_header.get_datagram_bytes(), self.address)

        # Espero el ACK
        print(f"[Cliente] Esperando a que el servidor acepte la conexión")
        ack_with_data = self.wait_ack(download_header)
        print(f"[Cliente] Conexión con el servidor aceptada!")
        self.send_ack(ack_with_data.datagram_number)

        self.socket.settimeout(None)
        self.receiving_operation(ack_with_data.total_datagrams, ack_with_data.file_name)

    def _start_client_upload(self, file_name):
        print(f"[Cliente] Accion a realizar: Carga de un archivo al servidor")

        # Armo el header UPLOAD
        file_size = files_management.get_file_size(file_name)
        total_datagrams = files_management.get_count_of_datagrams_sack(file_name)
        upload_header = SackDatagram.create_upload_header_client(file_name, file_size, total_datagrams)
        print(f"[Cliente] Número de datagramas a enviar: {total_datagrams}")

        # Envio el header
        self.socket.sendto(upload_header.get_datagram_bytes(), self.address)
        # Espero el ACK para poder comenzar a enviar
        print(f"[Cliente] Esperando a que el servidor acepte la conexión")
        self.wait_ack(upload_header)
        # Comienzo a enviar el archivo una vez recibido confirmación del header!
        print(f"[Cliente] Conexión con el servidor aceptada!")
        self.sending_operation(file_name)

    # Wait ack: espera que llegue un ack, si no llega, reenvia el datagrama
    def wait_ack(self, datagram):
        # Mientras no recibo el ack, mando de vuelta el datagram
        while True:
            try:
                if self.is_server:
                    ack_deserialized = SackDatagramDeserialized(self.queue.get(timeout=TIMEOUT_SERVER))
                else:
                    ack, client_address = self.socket.recvfrom(SACK_DATAGRAM_SIZE)
                    ack_deserialized = SackDatagramDeserialized(ack)
                if ack_deserialized.datagram_number == datagram.datagram_number:
                    return ack_deserialized
            # Excepción por timeout
            except Exception:
                self.socket.sendto(datagram.get_datagram_bytes(), self.address)

    # Send ack: envia un ack con un ack_number
    def send_ack(self, ack_number):
        # Envio el ack
        ack_datagram = SackDatagram.create_ack(ack_number)
        bytes = ack_datagram.get_datagram_bytes()
        self.socket.sendto(bytes, self.address)

    # Send sack: envia un sack con un ack_number y con una lista de sacks
    def send_sack(self, ack_number, list_of_sacks):
        # Envio el sack
        print(f"Enviando ack: numero_ack-{ack_number}, cantidad_sacks-{len(list_of_sacks)} ,lista_sacks-{self.fill_with_ceros(list_of_sacks)}")
        sack_datagram = SackDatagram.create_sack(ack_number, len(list_of_sacks), self.fill_with_ceros(list_of_sacks))
        bytes = sack_datagram.get_datagram_bytes()
        self.socket.sendto(bytes, self.address)

    # Funcion que recibe todos los datagramas disponibles para enviar y envia los que puede.
    def send_datagrams(self, datagrams, window_size_remaining):
        # Itera sobre el window size o los datagramas, lo que sea menor
        for i in range(min(window_size_remaining, len(datagrams))):
            # Generar un número aleatorio entre 0 y 1
            print("Enviando datagrama #: ", datagrams[i].datagram_number)
            self.socket.sendto(datagrams[i].get_datagram_bytes(), self.address)
        return min(window_size_remaining, len(datagrams))

    # Operaciones para el UPLOAD
    def sending_operation(self, file_name):
        # Busca el archivo.
        try:
            file_contents = files_management.get_file_content(file_name)
        except:
            raise "Archivo no encontrado"

        self.socket.settimeout(TIMEOUT_CLIENT)

        # Obtenemos los datagramas
        # FIX datagram number o binario
        datagrams = files_management.get_datagrams_for_sack(file_contents)
        datagrams_flying = []
        window_size_remaining = self.window_size
        last_ack_number = 0
        ack_repetitions = 0

        while datagrams or datagrams_flying:
            datagrams_sending = self.send_datagrams(datagrams, window_size_remaining)
            window_size_remaining -= datagrams_sending

            # Esos datagrams los agrego a una lista a parte para poder reenviarlos si es necesario
            for datagram in datagrams[:datagrams_sending]:
                datagrams_flying.append(datagram)

            # Aquellos paquetes que envie los elimino de mi lista de datagramas
            datagrams = datagrams[datagrams_sending:]

            datagram_deserialized = None
            try:
                if self.is_server:
                    datagram_deserialized = SackDatagramDeserialized(self.queue.get(timeout = TIMEOUT_SERVER))
                else:
                    datagram_deserialized = SackDatagramDeserialized(self.socket.recv(SACK_DATAGRAM_SIZE))
            except Exception as _:
                if len(datagrams_flying) > 0:
                    datagrams.insert(0, datagrams_flying[0])
                    datagrams_flying.remove(datagrams_flying[0])
                    window_size_remaining += 1
                continue

            if datagram_deserialized.datagram_type == TypeOfSackDatagram.SACK.value:
                print(f"SACK {datagram_deserialized.datagram_number} recibido ")
                # Manejo el ack repetido
                window_size_remaining += self.remove_datagram_from_flying(datagrams_flying, datagram_deserialized)
                if last_ack_number != datagram_deserialized.datagram_number:
                    last_ack_number = datagram_deserialized.datagram_number
                    ack_repetitions = 1
                    # Saco el paquete de flying del ACK recibido
                else:
                    ack_repetitions += 1
                    datagram_to_resend = None

                    if ack_repetitions >= MAX_ACK_REPETITIONS:
                        print("Se detecto un ACK repetido que supera el limite de repeticiones, "
                              "reenvio el datagrama # ", last_ack_number)
                        # Reenvio el paquete
                        for datagram in datagrams_flying:
                            if datagram.datagram_number == last_ack_number:
                                datagram_to_resend = datagram

                        if datagram_to_resend is not None:
                            datagrams.insert(0, datagram_to_resend)
                            datagrams_flying.remove(datagram_to_resend)
                            window_size_remaining += 1

                        ack_repetitions = 0

                # Saco los paquetes que me indican en el SACK
                for sack_index in range(datagram_deserialized.sack_number):
                    sack = datagram_deserialized.sacks_content[sack_index]
                    sack_begin = sack[0]
                    sack_end = sack[1]
                    for datagram in datagrams_flying:
                        if datagram.datagram_number in range(sack_begin, sack_end):
                            datagrams_flying.remove(datagram)
                            window_size_remaining += 1

    # TODO modificar el return para que devuelva el windows size directamente
    @staticmethod
    def remove_datagram_from_flying(datagrams_flying, datagram_deserialized):
        for datagram in datagrams_flying:
            if datagram.datagram_number <= datagram_deserialized.datagram_number - 1:
                datagrams_flying.remove(datagram)
                return 1
        return 0

    def get_second_sack_possition(self, begin, received_data):
        for i in range(begin + 1, len(received_data)):
            if (received_data[i] - received_data[i - 1] > 1):
                return received_data[i - 1] + 1

    def get_sacks(self, received_data, amount_of_datagrams):
        list_of_sacks = []
        for i in range(1, len(received_data)):
            if (received_data[i] - received_data[i - 1]) > 1:
                first_sack_possition = received_data[i]
                second_sack_possition = self.get_second_sack_possition(i, received_data)
                if second_sack_possition == None and (len(received_data) == amount_of_datagrams):
                    second_sack_possition = amount_of_datagrams
                elif second_sack_possition == None:
                    second_sack_possition = received_data[-1] + 1
                list_of_sacks.append((first_sack_possition, second_sack_possition))
        return list_of_sacks
    
    # Funcion que devuelve el proximo ack a enviar
    def get_next_ack_number(self, received_datagrams_numbers):
        expected_set = set(range(1, max(received_datagrams_numbers) + 1))
        received_set = set(received_datagrams_numbers)
        missing_set = expected_set - received_set

        if not missing_set:
            return max(received_datagrams_numbers) + 1 # Si esta todo ordenado espero el proximo 
        else:
            return min(missing_set) # Si no esta ordenado devuelvo el primer faltante
        
    def receiving_operation(self, total_datagrams, file_name):
        # Guardo todo el contenido del archivo
        received_data = [None] * total_datagrams
        # Guardo el numero de datagrama que recibi
        received_datagrams_numbers = []
        # Ultimo ack que mande 
        last_ack_number = 1

        while len(received_datagrams_numbers) < total_datagrams:
            datagram_deserialized = -1
            if self.is_server:
                datagram_deserialized = SackDatagramDeserialized(self.queue.get())
            else:
                datagram, address = self.socket.recvfrom(SACK_DATAGRAM_SIZE)
                datagram_deserialized = SackDatagramDeserialized(datagram)

            #Se perdio la confirmacion del ack de descarga, lo reenvio de vuelta.
            if ((datagram_deserialized.datagram_type == TypeOfSackDatagram.HEADER_UPLOAD.value) or
                    (datagram_deserialized.datagram_type == TypeOfSackDatagram.HEADER_DOWNLOAD.value)):
                self.send_ack(0)
                continue

            print(f"Recibido: {datagram_deserialized.datagram_number}/{total_datagrams}")
            # En caso de haber recibido un datagrama que no habia recibido antes lo guardo y proceso
            # Si ya lo habia recibido lo descarto.
            if datagram_deserialized.datagram_number not in received_datagrams_numbers:
                received_data[datagram_deserialized.datagram_number - 1] = datagram_deserialized.content
                received_datagrams_numbers.append(datagram_deserialized.datagram_number)
                received_datagrams_numbers.sort()

            last_ack_number = self.get_next_ack_number(received_datagrams_numbers)
            list_of_sacks = self.get_sacks(received_datagrams_numbers, total_datagrams)
            self.send_sack(last_ack_number, list_of_sacks)

        for i in range(0,14):
            self.send_sack(last_ack_number, [])
    
        print("--------------------------------------------------------------------------")
        print(f"[SERVIDOR - Hilo #{self.address}] Creado con éxito el archivo {file_name}")
        print("--------------------------------------------------------------------------")
        files_management.create_new_file(received_data, file_name)

    def fill_with_ceros(self, list_of_sacks):
        while len(list_of_sacks) < 4:
            list_of_sacks.append([0, 0])
        return list_of_sacks
