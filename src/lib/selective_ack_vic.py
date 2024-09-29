
from src.lib.sack_communications import TypeOfSackDatagram, LengthsForSackDatagram, AmountOfSacks, SackDatagram



class SelectiveAcK:
    def __init__(self, origin_address, destination_address, is_server, socket, messages_queue, messages_vector,
                 congestion_window):
        self.origin_address = None
        self.destination_address = None
        self.is_server = False
        self.socket = None
        self.messages_queue = None
        self.messages_vector = None
        self.congestion_window = None

    @classmethod
    def create_stop_and_wait_for_server(cls, origin_address, destination_address, messages_queue, sending_socket):
        return cls(origin_address=origin_address, destination_address=destination_address, is_server=True,
                   socket=sending_socket,messages_queue=messages_queue, messages_vector=None,congestion_window=None)

    @classmethod
    def create_stop_and_wait_for_client(cls, origin_address, destination_address, communication_socket):
        return cls(origin_address=origin_address, destination_address=destination_address, is_server=True,
                   socket=communication_socket, messages_queue=None, messages_vector=None, congestion_window=None)

    def receiving_operation_for_client(self):
        pass

    def sending_operation_for_client(self):
        pass

    def start_client(self, file_name, datagram_type):
        if datagram_type == TypeOfSackDatagram.DOWNLOAD.value:
            pass
        elif datagram_type == TypeOfSackDatagram.UPLOAD.value:
            pass
        else:
           raise Exception(f"[Servidor - Hilo #{self.destination_address}] El primer mensaje no es un header")

    def receiving_operation_for_server(self):
        pass

    def sending_operation_for_server(self):
        pass

    def start_server(self):

        #SACO DE LA COLA
        #VERIFICO EL TIPO DE MENSAJE
        pass


