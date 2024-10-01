from lib import files_management
from lib.sack_communications import TypeOfSackDatagram, LengthsForSackDatagram, AmountOfSacks, SackDatagram, \
    SackDatagramDeserialized, SACK_DATAGRAM_SIZE

import time

TIMEOUT = 2

TIMEOUT_CLIENT = 1
TIMEOUT_SERVER = 1
TIMEOUT_RESEND = 5 # For time_stamp


class SelectiveAck:
    def __init__(self, destination_address, is_server, socket, messages_queue, messages_vector,
                 congestion_window):
        self.destination_address = destination_address
        self.is_server = is_server
        self.socket = socket
        self.messages_queue = messages_queue
        self.messages_vector = messages_vector
        self.congestion_window_size = congestion_window

    @classmethod
    def create_selective_ack_for_server(cls, sending_socket, destination_address, messages_queue):
        return cls(destination_address=destination_address, is_server=True,
                   socket=sending_socket,messages_queue=messages_queue, messages_vector=None,congestion_window=5)

    @classmethod
    def create_selective_ack_for_client(cls, destination_address, communication_socket):
        return cls(destination_address=destination_address, is_server=False,
                   socket=communication_socket, messages_queue=None, messages_vector=None, congestion_window=5)

    def start_server(self):
        deserialized_datagram = SackDatagramDeserialized(self.messages_queue.get())

        if deserialized_datagram.datagram_type == TypeOfSackDatagram.HEADER_UPLOAD.value:
            print("start upload")
            file_name = deserialized_datagram.file_name
            total_datagrams = deserialized_datagram.total_datagrams
            datagram_number = deserialized_datagram.datagram_number
            self.send_ack(datagram_number)
            self.receiving_operation_for_server(total_datagrams)
        elif deserialized_datagram.datagram_type == TypeOfSackDatagram.HEADER_DOWNLOAD.value:
            file_name = deserialized_datagram.file_name
            file_size = files_management.get_file_size(file_name)
            total_datagrams = files_management.get_count_of_datagrams(file_name)

            self.send_ack()
            self.sending_operation_for_server()
        else:
            raise Exception("El primer mensaje no es un header")

    def start_client(self, file_name, datagram_type):
        self.socket.settimeout(TIMEOUT_CLIENT)
        if datagram_type == TypeOfSackDatagram.HEADER_DOWNLOAD.value:
            pass
        elif datagram_type == TypeOfSackDatagram.HEADER_UPLOAD.value:
            
            # Armo el header UPLOAD
            file_size = files_management.get_file_size(file_name)
            total_datagrams = files_management.get_count_of_datagrams(file_name)
            print(f"EL NUMERO DE DATAGRAMAS ES {total_datagrams}")
            upload_header = SackDatagram.create_upload_datagram_for_client(file_name, total_datagrams)
            # Envio el header
            self.socket.sendto(upload_header.get_datagram_bytes(), self.destination_address)
            # Espero el ACK
            self.wait_ack_client(upload_header)
            # Comienzo a enviar el file
            self.sending_operation_for_client(file_name)

        else:
           raise Exception(f"[Servidor - Hilo #{self.destination_address}] El primer mensaje no es un header")

    def send_ack(self, ack_number):
        # Envio el ack
        ack_datagram = SackDatagram.create_ack(0,[[0,0],[0,0],[0,0],[0,0]],ack_number)
        bytes = ack_datagram.get_datagram_bytes()
        self.socket.sendto(bytes, self.destination_address)

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
        print("BOooocaaaaa")
        try:
            file_contents = files_management.get_file_content(file_name)
        except:
            raise "Archivo no encontrado"

        datagrams = files_management.get_datagrams_for_sack(file_contents)

        congestion_window = [None] * self.congestion_window_size # (Datagrama, Hora de envio)
        recognized_file_fragments = 0
        datagrams_in_congestion_window = 0
        next_datagram_to_send = 0

        self.socket.settimeout(TIMEOUT_CLIENT) # setearlo en start client
        #self.socket.setblocking(False)

        # Si envio un archivo con pocos datagramas, la congestion window se ajusta
        if len(datagrams) < self.congestion_window_size:
            self.congestion_window_size = len(datagrams)

        while recognized_file_fragments < len(datagrams):

            while datagrams_in_congestion_window < (self.congestion_window_size -1):

                # TODO: en la primer iteracion se envian los 5 datagrams de una, pero desp quizas hay que enviar
                #       datagramas especificos. Tener en cuenta para el sendto
                # TODO: Actualizar hora de envio de datagrama enviado
                print(f"Enviando datagrama {next_datagram_to_send}")
                datagram = datagrams[next_datagram_to_send]
                self.socket.sendto(datagram.get_datagram_bytes(), self.destination_address)
                free_position = self.get_congestion_window_first_free_position(congestion_window)
                if free_position is not None:
                    congestion_window[free_position] = (datagram, time.time())

                datagrams_in_congestion_window += 1
                next_datagram_to_send += 1

            # puede pasar que no se reciba nada, deberia estar en try exception?
            # ack, client_address = None, None
            ack, client_address = self.socket.recv(SACK_DATAGRAM_SIZE)

            # no recibi nada, seteo el datagrams_in_congestion_window en 0
            if ack is None:
                datagrams_in_congestion_window = 0
                continue

            ack_deserialized = SackDatagramDeserialized(ack)
            datagrams_in_congestion_window -= 1
            ack_number = ack_deserialized.datagram_number

            # remplazo los mensajes que ya fueron reconocidos por None
            self.replace_recognized_datagrams_with_none(ack_deserialized, congestion_window)

            # TODO: Manejo de los timestamps
            datagrams_to_resend = []
            for datagram_sent, ts_datagram in congestion_window:
                if datagram_sent is None or ts_datagram is None:
                    continue
                ts = time.time()
                if (ts - ts_datagram) > TIMEOUT_RESEND:
                    datagrams_to_resend.append(datagram_sent)

            for datagram in datagrams_to_resend:
                self.socket.sendto(datagram.get_datagram_bytes(), self.destination_address)
                # Ya estan agregados a la lista de congestion, no hace falta agregarlos de nuevo


    def replace_recognized_datagrams_with_none(self, ack_deserialized, congestion_window):
        for datagram, _ in congestion_window:
            if datagram is None:
                continue
            if datagram.datagram_number == ack_deserialized.datagram_number:
                congestion_window[congestion_window.index((datagram, _))] = None

        # ahora los sacks (init, end)
        sacks = [ack_deserialized.first_sack, ack_deserialized.second_sack, ack_deserialized.third_sack, ack_deserialized.fourth_sack]
        for sack in sacks:
            if sack is None:
                continue
            self.replace_sacks_with_none(sack[0], sack[1], congestion_window)

    def replace_sacks_with_none(self, init, end, congestion_window):
        #TODO: handalear el caso que end sea None

        for i in range(init, end):
            for datagram, _ in congestion_window:
                if datagram is None:
                    continue
                if datagram.datagram_number == i:
                    # creo que esto del index se puede hacer de otra forma si quieren
                    congestion_window[congestion_window.index((datagram, _))] = None

    # Wait ack: espera que llegue un ack, si no llega, reenvia el datagrama
    def wait_ack_client(self, datagram):
        print("Esperando ack")
        # Mientras no recibo el ack, mando de vuelta el datagram
        while True:
            try:
                if not self.is_server:
                    ack, client_address = self.socket.recvfrom(SACK_DATAGRAM_SIZE)
                    ack_deserialized = SackDatagramDeserialized(ack)
                if ack_deserialized.datagram_number == datagram.datagram_number:
                    print(f"Recibi ACK correcto")
                    return ack_deserialized
            # Excepción por timeout
            except Exception:
                #print(f"[Cliente - {self.origin_address}] Timeout alcanzado esperando ACK")
                self.socket.sendto(datagram.get_datagram_bytes(), self.destination_address)
                #print(f"[Cliente - {self.origin_address}] Datagrama enviado nuevamente")

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
        print(f"Esperando recibir {amount_of_datagrams} datagramas")
        while received_datagrams < amount_of_datagrams:
            datagram, client_address = self.socket.recvfrom(SACK_DATAGRAM_SIZE)
            datagram_deserialized = SackDatagramDeserialized(datagram)
            print(f"Recibi datagrama {datagram_deserialized.datagram_number}")
            if received_data[datagram_deserialized.datagram_number] == -1:
                received_data[datagram_deserialized.datagram_number] = datagram_deserialized.content
            else:
                print("Me mandaste que ya recibi capo")

            sacks_list = self.build_sacks_from_received_data(received_data, amount_of_datagrams)
            ack_datagram = SackDatagram.create_ack(len(sacks_list), sacks_list, 1)
            ack_datagram_bytes = ack_datagram.get_datagram_bytes()

            self.socket.sendto(ack_datagram_bytes, client_address)
            received_datagrams += 1

    def sending_operation_for_server(self):
        pass


