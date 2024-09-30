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

    def send_ack(self):
        pass

    def receiving_operation_for_client(self):

        pass
    def sending_operation_for_client(self, file_name):
        ## Completar
        try:
            file_contents = files_management.get_file_content(file_name)
        except:
            raise "Archivo no encontrado"

        datagrams = files_management.get_datagrams_for_sack(file_contents)

        sent_datagrams = [None]*self.congestion_window_size # (Datagrama, Hora de envio)
        recognized_file_fragments = 0
        datagrams_in_congestion_window = 0

        self.socket.settimeout(0,1)
        self.socket.setblocking(False)
        # Envio todos los datagramas de una

        while recognized_file_fragments < len(datagrams):

            while  datagrams_in_congestion_window < self.congestion_window_size:

                # TODO: en la primer iteracion se envian los 5 datagrams de una, pero desp quizas hay que enviar
                #       datagramas especificos. Tener en cuenta para el sendto
                # TODO: Actualizar hora de envio de datagrama enviado

                datagram = datagrams[datagrams_in_congestion_window]
                self.socket.sendto(datagram.get_datagram_bytes(), self.destination_address)

                sent_datagrams[datagrams_in_congestion_window] = (datagram, time.time())
                datagrams_in_congestion_window += 1


            ack, client_address = self.socket.recvfrom(SACK_DATAGRAM_SIZE)
            ack_deserialized = SackDatagramDeserialized(ack)
            #  Si no llego alguno modificar la variable datagrams_in_congestion_window restando

            ack_number = ack_deserialized.datagram_number

            sacks_content = ack_deserialized.sacks_content.split(',')
            for sack in sacks_content:
                initial_position, final_position = sack.split('-')
                initial_position = int(initial_position)
                final_position = int(final_position)
                # TODO: Manejar estas posiciones y el ack

            # datagrams_to_resend = []
            # # TODO: Manejo de los timestamps
            # for datagram_sended in sent_datagrams:
            #
            #     ts_datagram = sent_datagrams[datagram_sended].1
            #     if ts_datagram:
            #         ts = time.time()
            #         if (ts - ts_datagram) > 0.5:
            #             # TODO: Tengo que volver a enviarlo porque hubo perdida de paquetes
            #             datagrams_to_resend.append(datagram_sended)
            #
            #             pass
        pass

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


    def find_hole(self, received_data, begin, end):

        actual_position = begin

        hole_founded = False
        hole_begin = -1
        hole_end = -1

        while begin < end:

            if (not hole_founded) and (received_data[actual_position] == -1):
                hole_founded = True
                hole_begin = actual_position
            elif (hole_founded)

        return hole_begin, hole_end


    def get_sack(self, received_data):

        search_is_finished = False


        while not search_is_finished:

            for i in range(received_data):

                if received_data[i] == -1:




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

        self.get_sack()


        pass

    def sending_operation_for_server(self):
        pass

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

