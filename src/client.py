import ctypes
import socket
import math
import time
from communications import Datagram, MessageType


FRAGMENT_SIZE = 1024

class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.connect((self.host, self.port))

    def connect(self):
        self.socket.connect((self.host, self.port))
        # Esperar ACK del servidor
        self.socket.recv(1024)
        # TODO: Implementar los mensajes en conjunto de comunicacion cliente-servidor 
        
    def upload(self, document_name):
        
        # Enviar mensaje de upload a Servidor y espera ACK
        self.socket.send(b'upload')
        self.socket.recv(1024)
                
        # Abrir el archivo y leer su contenido
        with open(document_name, 'rb') as file:
            file_contents = file.read()
        
        # Now you can examine the contents of the file
        print(file_contents)
        
        # Cantidad de fragmentos
        fragment_count = math.ceil(len(file_contents) / FRAGMENT_SIZE) 
        datagrams = []
        
        # Generamos los datagramas a enviar
        for i in fragment_count:
            start = i * FRAGMENT_SIZE
            end = min(start + FRAGMENT_SIZE, len(file_contents))
            fragment = file_contents[start:end]
            datagram = Datagram.create_content(i, fragment_count, len(fragment), fragment)
            datagrams.append(datagram)
        
        # Timeout muy grande y tomamos medida de este ack 
        
        # enviar a server primera comunicacion de va archivo con x tamaño
        header = Datagram.create_download_header(document_name, len(file_contents), fragment_count)
        sendTime = time.time()
        self.socket.send(header.encode())  # Send the header to the server
        
        # esperar ack
        ack = self.socket.recv(len(Datagram))  # Wait to  an ACK from the server
        recvTime = time.time()
        
        rcvd: Datagram = ack.decode()
        
        if rcvd.total_packet_count != MessageType.ACK:
            print("Error en la comunicacion")
            return
        
        firstTimeoutMeasure = recvTime - sendTime
        
        aproximateTimeout = firstTimeoutMeasure * 1.5
        # Timeout pasa a ser esta medida x 1,5 (flucutacion)
        
        # Stop and wait
        for i in datagrams:
            # enviar datagrama i
            socket.send(bytes(i))
            
            socket.settimeout(aproximateTimeout)
            try:
                ack = socket.recv(ctypes.sizeof(Datagram))
            except socket.timeout:
                print("Tiempo de espera excedido, no se recibió ACK.")

        
        # TODO: MANEJO DE ERRORES Y TIMEOUTS
        # TODO: Como definir el timeout? -> 1.5 * RTT (1.5 puede variar)         
        
#        
#    def download(self, document_name):
#        Enviar al servidor solicitud de descarga como un header
#            # TODO Implementar mensaje de solicitud de descarga
#        Esperar ACK del servidor
#            # TODO Implementar ACK del servidor por si o por no (que traiga -1 de numero?)
#        
#        
#        for i in cantidad:
#            esperar datagrama i
#            enviar ack
#               # ! Reeler enunciado si es stop-and-wait o todo de un saque con hilos
#        
#        llega todo reconstruir archivo
#        guardar archivo en disco (?)
    
   
    def send(self, message):
        self.socket.sendto(message.encode('utf-8'), (self.host, self.port))
        data, address = self.socket.recvfrom(1024)
        print(f"Received data from {address}: {data.decode()}")

    def close(self):
        self.socket.close()