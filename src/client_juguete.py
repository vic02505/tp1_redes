import socket


def main():
    # Crear un socket UDP
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Dirección y puerto del servidor
    server_address = ('localhost', 1234)

    # Mensaje que se enviará al servidor
    message = 'Hola, servidor!'

    try:
        # Enviar el mensaje al servidor
        client_socket.sendto(message.encode('utf-8'), server_address)

        # Recibir la respuesta del servidor
        buf = bytearray(1024)
        amt, _ = client_socket.recvfrom_into(buf)

        # Convertir la respuesta en una cadena
        response = buf[:amt].decode('utf-8')

        # Mostrar la respuesta del servidor
        print(f"Respuesta del servidor: {response}")
    finally:
        # Cerrar el socket
        client_socket.close()


if __name__ == '__main__':
    main()
