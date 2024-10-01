from socket import socket
from lib.sack_communications import TypeOfDatagram, DatagramDeserialized, Datagram, SACK_DATAGRAM_SIZE
import lib.files_management as files_management

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
        deserialized_datagram = DatagramDeserialized(self.queue.get())
        print(f"[SERVIDOR - Hilo #{self.address}] Recibio mensaje de: {self.address}")

        if deserialized_datagram.datagram_type == TypeOfDatagram.HEADER_UPLOAD.value:
            file_name = deserialized_datagram.file_name
            total_datagrams = deserialized_datagram.total_datagrams
            datagram_number = deserialized_datagram.datagram_number
            self.send_ack(datagram_number)
            self.receive_server_file(total_datagrams, file_name, datagram_number)
        elif deserialized_datagram.datagram_type == TypeOfDatagram.HEADER_DOWNLOAD.value:
            file_name = deserialized_datagram.file_name
            file_size = files_management.get_file_size(file_name)

            print(f"[SERVIDOR - Hilo #{self.address}] Inicio de descarga de archivo: {file_name}")

            total_datagrams = files_management.get_count_of_datagrams(file_name)
            ack_with_data = Datagram.create_download_header_server(file_name, file_size, total_datagrams)
            self.socket.sendto(ack_with_data.get_datagram_bytes(), self.address)
            self.wait_ack(ack_with_data)
            self.send_server_file(file_name)
        else:
            raise Exception("El primer mensaje no es un header")

    # Inicio de client
    def start_client(self, file_name, datagram_type):
        print(f"[Cliente - {self.address}] Inicializando SW para cliente")
        self.socket.settimeout(TIMEOUT_CLIENT)
        if datagram_type == TypeOfDatagram.HEADER_UPLOAD.value:
            print(f"[Cliente - {self.address}] Accion a realizar: Carga de un archivo al servidor")

            # Armo el header UPLOAD
            file_size = files_management.get_file_size(file_name)
            total_datagrams = files_management.get_count_of_datagrams(file_name)
            print(f"EL NUMERO DE DATAGRAMAS ES {total_datagrams}")
            upload_header = Datagram.create_upload_header_client(file_name, file_size, total_datagrams)

            # Envio el header
            self.socket.sendto(upload_header.get_datagram_bytes(), self.address)
            # Espero el ACK
            self.wait_ack(upload_header)
            # Comienzo a enviar el file
            self.send_client_file(file_name)
        elif datagram_type == TypeOfDatagram.HEADER_DOWNLOAD.value:
            # Armo el header DOWNLOAD
            download_header = Datagram.create_download_header_client(file_name)

            # Envio el header
            self.socket.sendto(download_header.get_datagram_bytes(), self.address)

            # Espero el ACK
            ack_with_data = self.wait_ack(download_header)

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
                    ack_deserialized = DatagramDeserialized(self.queue.get(timeout=TIMEOUT_SERVER))
                else:
                    ack, client_address = self.socket.recvfrom(SACK_DATAGRAM_SIZE)
                    ack_deserialized = DatagramDeserialized(ack)
                if ack_deserialized.datagram_number == datagram.datagram_number:
                    print(f"[Cliente - {self.address}] Recibi ACK correcto")
                    return ack_deserialized
            # Excepción por timeout
            except Exception:
                print(f"[Cliente - {self.address}] Timeout alcanzado esperando ACK")
                self.socket.sendto(datagram.get_datagram_bytes(), self.address)
                print(f"[Cliente - {self.address}] Datagrama enviado nuevamente")

    # Send ack: envia un ack con un ack_number
    def send_ack(self, ack_number):
        # Envio el ack
        ack_datagram = Datagram.create_ack(ack_number)
        bytes = ack_datagram.get_datagram_bytes()
        self.socket.sendto(bytes, self.address)

    # Send sack: envia un sack con un ack_number y con una lista de sacks
    def send_sack(self, ack_number, list_of_sacks, amount_of_sacks):
        # Envio el sack
        sack_datagram = Datagram.create_sack(ack_number, amount_of_sacks, list_of_sacks)
        bytes = sack_datagram.get_datagram_bytes()
        self.socket.sendto(bytes, self.address)

    # Funcion que recibe todos los datagramas disponibles para enviar y envia los que puede.
    def send_datagrams(self, datagrams, window_size_remaining):
        # Itera sobre el window size o los datagramas, lo que sea menor
        for i in range(min(window_size_remaining, len(datagrams))):
            print("Enviando datagrama: ", datagrams[i].datagram_number)
            self.socket.sendto(datagrams[i].get_datagram_bytes(), self.address)
        return min(window_size_remaining, len(datagrams))

    # Operaciones para el UPLOAD
    def send_client_file(self, file_name):
        # Busca el archivo.
        try:
            file_contents = files_management.get_file_content(file_name)
        except:
            raise "Archivo no encontrado"

        # Obtenemos los datagramas
        # FIX datagram number o binario
        datagrams = files_management.get_datagrams(file_contents)
        datagrams_flying = []
        window_size_remaining = self.window_size
        recognized_datagrams = 0
        total_datagrams = len(datagrams)
        last_ack_number = 0
        ack_repetitions = 0
        self.socket.setblocking(False)

        while datagrams or datagrams_flying:
            datagrams_sending = self.send_datagrams(datagrams, window_size_remaining)
            window_size_remaining -= datagrams_sending
            # Esos datagrams los agrego a una lista a parte para poder reenviarlos si es necesario
            for datagram in datagrams[:datagrams_sending]:
                datagrams_flying.append(datagram)
            # Aquellos paquetes que envie los elimino de mi lista de datagramas
            datagrams = datagrams[datagrams_sending:]

            #datagram_deserialized = None

            # Espero
            try:
                self.socket.settimeout(2)
                datagram_deserialized = DatagramDeserialized(self.socket.recv(SACK_DATAGRAM_SIZE))
            except Exception as e:
                print(f"No hay nada en el buffer rey {e}")
                continue

            if datagram_deserialized.datagram_type == TypeOfDatagram.SACK.value:
                print(f"SACK {datagram_deserialized.datagram_number} recibido ")
                # Manejo el ack repetido
                if last_ack_number != datagram_deserialized.datagram_number:
                    last_ack_number = datagram_deserialized.datagram_number
                    ack_repetitions = 1
                    # Saco el paquete de flying del ACK recibido
                    window_size_remaining += self.remove_datagram_from_flying(datagrams_flying, datagram_deserialized)
                else:
                    ack_repetitions += 1
                    datagram_to_resend = None

                    if ack_repetitions == MAX_ACK_REPETITIONS:
                        print("ACK repetido, reinserto")
                        # Reenvio el paquete
                        for datagram in datagrams_flying:
                            if datagram.datagram_number == last_ack_number:
                                datagram_to_resend = datagram
                        '''
                        datagram_to_resend = next((datagram for datagram in datagrams_flying if
                                                   last_ack_number == datagram.datagram_number - 1), None)
                        '''

                        ##LEER!!!!!!!!!!!!!!!!!!!!!!!!
                        ##El datagram_to_resend entro del insert me hace ruido, chequear que onda,
                        ##la ide me lo marcar en rojo.

                        if datagram_to_resend is not None:
                            datagrams.insert(0, datagram_to_resend)
                            datagrams_flying.remove(datagram_to_resend)


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
    def remove_datagram_from_flying(self, datagrams_flying, datagram_deserialized):
        for datagram in datagrams_flying:
            if datagram.datagram_number == datagram_deserialized.datagram_number - 1:
                datagrams_flying.remove(datagram)
                return 1
        return 0


    def get_sacks(self, received, total):
        sacks = []
        print("Received: ", received)
        # Empezar a recorrer los datagramas recibidos
        i = 0
        while i < len(received):
            start = received[i]  # Primer datagrama del bloque
            # Encontrar el fin del bloque continuo
            while i + 1 < len(received) and received[i + 1] == received[i] + 1:
                i += 1
            end = received[i]  # Último datagrama del bloque
            # Determinar el siguiente esperado
            next_expected = end + 1 if end + 1 <= total else None
            sacks.append((start, next_expected))
            i += 1

        return sacks[0:4]


    def get_next_ack_number(self, received_datagrams_numbers):

        next_ack_number = len(received_datagrams_numbers)

        for i in range(1, len(received_datagrams_numbers)):

            if (received_datagrams_numbers[i] - received_datagrams_numbers[i-1]) > 1:
                next_ack_number = received_datagrams_numbers[i-1]
                break

        return next_ack_number


    def receive_server_file(self, total_datagrams, file_name, datagram_number):
        received_data = [None] * total_datagrams
        received_datagrams_numbers = []
        contador_aux = 0
        last_ack_number = 0
        amount_of_sacks = 0

        while len(received_datagrams_numbers) < total_datagrams:
            datagram_deserialized = DatagramDeserialized(self.queue.get())
            

            # # Pruena de perdida de paquetes a mano
            contador_aux += 1
            if contador_aux == 3:
                print("entro al contador")
                continue

            print("recibio datagrama numero:", datagram_deserialized.datagram_number)

            received_data[datagram_deserialized.datagram_number - 1] = datagram_deserialized.content
            if datagram_deserialized.datagram_number not in received_datagrams_numbers:
                received_datagrams_numbers.append(datagram_deserialized.datagram_number)
                received_datagrams_numbers.sort()
            print(f"Last ack number: {last_ack_number}", f"recibido: {datagram_deserialized.datagram_number}")
            if last_ack_number + 1 == datagram_deserialized.datagram_number:
                list_of_sacks = [[0,0],[0,0],[0,0],[0,0]]
                amount_of_sacks = 0
            else:
                list_of_sacks = self.get_sacks(received_datagrams_numbers, total_datagrams)
                amount_of_sacks = len(list_of_sacks)
                self.fill_with_ceros(list_of_sacks)
            print("Lista de sacks: ", list_of_sacks)

            if list_of_sacks == [[0, 0], [0, 0], [0, 0], [0, 0]]:
                last_ack_number = self.get_next_ack_number(received_datagrams_numbers)
                self.send_sack(last_ack_number + 1, list_of_sacks, amount_of_sacks)
                print("Last ack number: ", last_ack_number)
            else:
                print("No esta en orden, envio: ", last_ack_number + 1)
                self.send_sack(last_ack_number + 1, list_of_sacks, amount_of_sacks)
        
        print(f"[SERVIDOR - Hilo #{self.address}] Creado con éxito el archivo {file_name}")
        files_management.create_new_file(received_data, file_name)

    def fill_with_ceros(self, list_of_sacks):
        while len(list_of_sacks) < 4:
            list_of_sacks.append((0, 0))

    # Operaciones para el DOWNLOAD
    def recive_client_file(self, total_datagrams, file_name):
        #print("acabo de entrar a esta puta mierda que no se que carajo hace")
        received_data = []
        for i in range(1, total_datagrams + 1):
            # Aca falta un try catch  (para mi no)
            datagram_deserialized = DatagramDeserialized(self.socket.recv(SACK_DATAGRAM_SIZE))
            while i != datagram_deserialized.datagram_number:
                print(f"[Cliente - {self.address}] Ya recibí este datagrama  {datagram_deserialized.datagram_number}")
                self.send_ack(datagram_deserialized.datagram_number)
                datagram_deserialized = DatagramDeserialized(self.socket.recv(SACK_DATAGRAM_SIZE))
            received_data.append(datagram_deserialized.content)
            self.send_ack(datagram_deserialized.datagram_number)

        print(f"[Cliente - {self.address}] Descarga realizada con éxito")
        files_management.create_new_file(received_data, file_name)

    def send_server_file(self, file_name):
        # Busca el archivo.
        try:
            file_contents = files_management.get_file_content(file_name)
        except:
            raise "Archivo no encontrado"

        # Obtenemos los datagramas
        datagrams = files_management.get_datagrams(file_contents)

        # Enviamos los datagramas
        for datagram in datagrams:
            print(f"[SERVIDOR - Hilo #{self.address}] Datagrama {datagram.datagram_number} de " f"{datagram.total_datagrams}")
            self.socket.sendto(datagram.get_datagram_bytes(), self.address)
            self.wait_ack(datagram)
