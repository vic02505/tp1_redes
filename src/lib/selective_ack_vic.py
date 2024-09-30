from src.lib import files_management
from src.lib.sack_communications import TypeOfSackDatagram, LengthsForSackDatagram, AmountOfSacks, SackDatagram, \
    SackDatagramDeserialized, SACK_DATAGRAM_SIZE

import time

TIMEOUT_CLIENT = 0.1
TIMEOUT_SERVER = 0.1


class SelectiveAcK:
    def __init__(self, origin_address, destination_address, is_server, socket, messages_queue, messages_vector,
                 congestion_window):
        self.origin_address = None
        self.destination_address = None
        self.is_server = False
        self.socket = None
        self.messages_queue = None
        self.messages_vector = None
        self.congestion_window_size = None

    @classmethod
    def create_selective_ack_for_server(cls, origin_address, destination_address, messages_queue, sending_socket):
        return cls(origin_address=origin_address, destination_address=destination_address, is_server=True,
                   socket=sending_socket,messages_queue=messages_queue, messages_vector=None,congestion_window=None)

    @classmethod
    def create_selective_ack_for_client(cls, origin_address, destination_address, communication_socket):
        return cls(origin_address=origin_address, destination_address=destination_address, is_server=True,
                   socket=communication_socket, messages_queue=None, messages_vector=None, congestion_window=None)

    def start_server(self):
        sack_datagram = self.messages_queue.get()
        client_message = SackDatagramDeserialized(sack_datagram)

        if client_message.datagram_type == TypeOfSackDatagram.UPLOAD.value:
            file_name = client_message.file_name
            total_datagrams = client_message.total_datagrams
            datagram_number = client_message.datagram_number
            self.send_ack()
            self.receiving_operation_for_server()
        elif client_message.datagram_type == TypeOfSackDatagram.DOWNLOAD.value:
            file_name = client_message.file_name
            file_size = files_management.get_file_size(file_name)
            total_datagrams = files_management.get_count_of_datagrams(file_name)

            self.send_ack()
            self.sending_operation_for_server()
        else:
            raise Exception("El primer mensaje no es un header")

    def start_client(self, file_name, datagram_type):
        self.socket.settimeout(TIMEOUT_CLIENT)
        print(f"[Cliente - {self.origin_address}] Inicializando Selective ACK para cliente")
        if datagram_type == TypeOfSackDatagram.HEADER_DOWNLOAD.value:
            pass
        elif datagram_type == TypeOfSackDatagram.HEADER_UPLOAD.value:

            print(f"[Cliente - {self.origin_addressaddress}] Accion a realizar: Carga de un archivo al servidor")

            # Armo el header UPLOAD
            file_size = files_management.get_file_size(file_name)
            total_datagrams = files_management.get_count_of_datagrams(file_name)
            print(f"EL NUMERO DE DATAGRAMAS ES {total_datagrams}")
            upload_header = SackDatagram.create_upload_header_client(file_name, file_size, total_datagrams)

            # Envio el header
            self.socket.sendto(upload_header.get_datagram_bytes(), self.destination_address)
            # Espero el ACK
            self.wait_ack_client(upload_header)
            # Comienzo a enviar el file
            self.sending_operation_for_client(file_name)

        else:
           raise Exception(f"[Servidor - Hilo #{self.destination_address}] El primer mensaje no es un header")

    def send_ack(self):
        pass

    def receiving_operation_for_client(self):
        pass

    @staticmethod
    def get_congestion_window_first_free_position(sent_datagrams):
        for i in range(len(sent_datagrams)):
            if sent_datagrams[i] is None:
                return i

    @staticmethod
    def update_congestion_window():
       pass


    def sending_operation_for_client(self, file_name):
        ## Completar
        try:
            file_contents = files_management.get_file_content(file_name)
        except:
            raise "Archivo no encontrado"

        datagrams = files_management.get_datagrams_for_sack(file_contents)

        congestion_window = [None] * self.congestion_window_size # (Datagrama, Hora de envio)
        recognized_file_fragments = 0
        datagrams_in_congestion_window = 0
        next_datagram_to_send = 0

        self.socket.settimeout(0,1) # setearlo en start client
        self.socket.setblocking(False)

        while recognized_file_fragments < len(datagrams):

            while  datagrams_in_congestion_window < self.congestion_window_size:

                # TODO: en la primer iteracion se envian los 5 datagrams de una, pero desp quizas hay que enviar
                #       datagramas especificos. Tener en cuenta para el sendto
                # TODO: Actualizar hora de envio de datagrama enviado

                datagram = datagrams[next_datagram_to_send]
                self.socket.sendto(datagram.get_datagram_bytes(), self.destination_address)
                free_position = self.get_congestion_window_first_free_position(congestion_window)
                congestion_window[free_position] = (datagram, time.time())

                datagrams_in_congestion_window += 1
                next_datagram_to_send += 1

            # puede pasar que no se reciba nada, deberia estar en try exception?
            ack, client_address = None, None
            ack, client_address = self.socket.recv(SACK_DATAGRAM_SIZE)

            if ack is None:
                continue

            ack_deserialized = SackDatagramDeserialized(ack)
            datagrams_in_congestion_window -= 1
            ack_number = ack_deserialized.datagram_number

            
            # datagrams_to_resend = []
            # # TODO: Manejo de los timestamps
            # for datagram_sended in congestion_window:
            #
            #     ts_datagram = sent_datagrams[datagram_sended].1
            #     if ts_datagram:
            #         ts = time.time()
            #         if (ts - ts_datagram) > 0.5:
            #             # TODO: Tengo que volver a enviarlo porque hubo perdida de paquetes
            #             datagrams_to_resend.append(datagram_sended)
            #
            #             pass
            recognized_file_fragments = calculate_recog_file_datagrams(ack_number, sacks)
        pass


    # Wait ack: espera que llegue un ack, si no llega, reenvia el datagrama
    def wait_ack_client(self, datagram):
        # Mientras no recibo el ack, mando de vuelta el datagram
        while True:
            try:
                if not self.is_server:
                    ack, client_address = self.socket.recvfrom(SACK_DATAGRAM_SIZE)
                    ack_deserialized = SackDatagramDeserialized(ack)
                if ack_deserialized.datagram_number == datagram.datagram_number:
                    print(f"[Cliente - {self.origin_address}] Recibi ACK correcto")
                    return ack_deserialized
            # Excepción por timeout
            except Exception:
                print(f"[Cliente - {self.origin_address}] Timeout alcanzado esperando ACK")
                self.socket.sendto(datagram.get_datagram_bytes(), self.origin_address)
                print(f"[Cliente - {self.origin_address}] Datagrama enviado nuevamente")


    @staticmethod
    def get_second_sack_position(begin, received_data):
        for i in range(begin + 1, len(received_data)):

            if received_data[i] - received_data[i - 1] > 1:
                return received_data[i - 1] + 1

    def build_sacks_from_received_data(self, received_data, amount_of_datagrams):
        list_of_sacks = []

        for i in range(1, len(received_data)):

            if (received_data[i] - received_data[i - 1]) > 1:
                first_sack_possition = received_data[i]
                second_sack_position = self.get_second_sack_position(i, received_data)

                if second_sack_position is None:
                    second_sack_position = amount_of_datagrams

                list_of_sacks.append((first_sack_possition, second_sack_position))

        return list_of_sacks

    def receiving_operation_for_server(self, amount_of_datagrams):

        received_datagrams = 0
        received_data = [-1] * amount_of_datagrams

        while received_datagrams < amount_of_datagrams:
            datagram, client_address = self.socket.recvfrom(SACK_DATAGRAM_SIZE)
            datagram_deserialized = SackDatagramDeserialized(datagram)

            if received_data[datagram_deserialized.datagram_number] == -1:
                received_data[datagram_deserialized.datagram_number] = datagram_deserialized.content
            else:
                print("Me mandaste que ya recibi capo")

            sacks_list = self.build_sacks_from_received_data(received_data, amount_of_datagrams)
            ack_datagram = SackDatagram.create_ack(len(sacks_list), sacks_list, 1)
            ack_datagram_bytes = ack_datagram.get_datagram_bytes()

            self.socket.sendto(ack_datagram_bytes, client_address)

    def sending_operation_for_server(self):
        pass


