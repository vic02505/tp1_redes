import math
import socket
import time
import os

from lib.communications import (
    DATAGRAM_SIZE,
    FRAGMENT_SIZE,
    Datagram,
    DatagramDeserialized,
    TypeOfDatagram,
)


class Client:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def upload(self, file_name):
        # Dirección y puerto del servidor
        server_address = ("localhost", 1234)

        with open(file_name, "rb") as file:
            file_contents = file.read()
        print(f"Tamaño del file: {len(file_contents)} ")

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
                file_name = os.path.basename(file_name),
                datagram_size=end - start,
                content=fragment,
            )

            datagrams.append(datagram)

        # Creamos un datagrama de HS_UPLOAD
        header = Datagram.create_upload_header(
            os.path.basename(file_name), len(file_contents), total_datagrams
        )

        # Iniciamos tiempo para verificar si el timeout es muy grande
        sendTime = time.time()

        self.socket.sendto(
            header.get_datagram_bytes(), server_address
        )  # Send the header to the server

        # Esperar ack
        ack = self.socket.recv(DATAGRAM_SIZE)  # Wait to  an ACK from the server

        # Frenamos el tiempo para calcular el timeout
        recvTime = time.time()

        ack_deserilized = DatagramDeserialized(ack)
        if ack_deserilized.datagram_type != TypeOfDatagram.ACK.value:
            print("Error en la comunicacion")
            return

        print(f"ACK de conexion(header) recibido en {recvTime - sendTime} segundos")

        firstTimeoutMeasure = recvTime - sendTime

        # Timeout pasa a ser esta medida x 3,5 (flucutacion)
        aproximateTimeout = firstTimeoutMeasure * 3.5

        # Stop and wait
        for i in datagrams:
            print(f"Enviando fragmento {i.datagram_number} de {i.total_datagrams}")

            # Enviar datagrama i
            self.socket.sendto(i.get_datagram_bytes(), server_address)

            self.socket.settimeout(aproximateTimeout)
            try:
                ack = self.socket.recv(DATAGRAM_SIZE)
            except socket.timeout:
                print("Tiempo de espera excedido, no se recibió ACK.")

        print("Archivo enviado correctamente")
        # TODO: MANEJO DE ERRORES

    def download(self, file_name):
        # Dirección y puerto del servidor
        server_address = ("localhost", 1234)

        # Creamos un datagrama de HS_UPLOAD
        header = Datagram.create_download_header(os.path.basename(file_name))

        # Iniciamos tiempo para verificar si el timeout es muy grande
        sendTime = time.time()

        self.socket.sendto(
            header.get_datagram_bytes(), server_address
        )  # Send the header to the server

        # Esperar ack
        ack = self.socket.recv(DATAGRAM_SIZE)  # Wait to  an ACK from the server
        
        # Frenamos el tiempo para calcular el timeout
        recvTime = time.time()

        ack_deserilized = DatagramDeserialized(ack)
        if ack_deserilized.datagram_type != TypeOfDatagram.ACK.value:
            print("Error en la comunicacion")
            return

        print(f"ACK de conexion(header) recibido en {recvTime - sendTime} segundos")

        firstTimeoutMeasure = recvTime - sendTime

        # Timeout pasa a ser esta medida x 3,5 (flucutacion)
        aproximateTimeout = firstTimeoutMeasure * 3.5

        # En el ack le puedo mandar la cantidad de paquetes que voy a recibir
        total_datagrams = ack_deserilized.total_datagrams
        received_data = []
        print("Total de datagramas", total_datagrams)
        for i in range(total_datagrams):
            # Esperar paquete
            datagram = self.socket.recv(DATAGRAM_SIZE)
            datagram = DatagramDeserialized(datagram)

            # Guardo paquete
            received_data.append(datagram.content)

            # Envio de ack
            self.socket.sendto(Datagram.create_ack().get_datagram_bytes(), server_address)

        # Unir todo el contenido de los datagramas
        file = b''.join(received_data)

        # Asegúrate de que el directorio 'client_files' exista
        os.makedirs(os.path.dirname('client_files/' + file_name), exist_ok=True)
        # Guardar el contenido en un archivo
        with open('client_files/'+file_name, 'wb') as f:
            f.write(file)

    def close(self):
        self.socket.close()
