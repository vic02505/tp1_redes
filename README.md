# tp1_redes

## Ejecucion
    server: python3 start_server.py {host} {nro_puerto}
        ej: python3 start_server.py 127.0.0.1 1234

    client: upload.py {archivo} {nro_puerto}
        ej: upload.py tp.pdf 1234
        

## Selective ACK:
### Propuesta
    Hay 3 cosas a tener en cuenta principalmente: Manejo de timeouts, que no bloquee, solicitar paquetes a reenviar
    Manejo de Timeouts:
        Cada vez que el cliente envia algo anota en un vector en la posicion del nuemro del paquete (TS, false). A su vez cada vez que repite el bucle revisa que no haya superado el TO y en caso de haberlo hecho reenvia. Cuando recibe un ack lo refleja cambiando el false a true para que ese TS sea ignorado en futuras revisiones. 
    Que no bloquee:
        Esto aplica al cliente, usando socket.setblocking(false) hace que si no puede recibir lanze la excepcion, al catchearla continuamos el bucle y puede seguir enviando. El problema de esto es que el timeout del socket no es mas valido, pero el punto de arriba lo soluciona
    Solicitar paquetes:
        Esto aplica al server, que al ver que le llega el paquete 1 y 3 evidentemente nota que falta el 2. Ante la falta del 2 lo solicita enviando un ack al cliente con el numero -2. De esta manera el cliente al ver el negativo entiende que es una solicitud y el numero absoluto le da el valor de cual es el que debe reenviar. 

### Preparacion
    Client: la preparacion es la misma, corta el archiov y envia un header de van a ser n cantidad de paquetes. Crea un vector de n (int, bool)
    Server: Recibe el header y construye un vector de bytes del tamaño del payload de tamaño n
### Protocolo
    Client: Corre constantemente el siguiente while. Es FUNDAMENTAL setear socket.setblocink(False)
    while no termino de recibir acks:
        try:
            reviso los TS del vector -> si alguno mayor a TO reenvio y actualizo el tiempo
            envio el proximo que haga falta mandar
            registro el enviado en el vector con (time.time(), false) -> el false hace referencia a que no recibio ack
            socekt.recv(DATAGRAMSIZE)
            si entra un ack reviso el numero:
                si negativo -> esta solicitando que se reenvie ese numero
                si positivo -> ir a el vector y ponerle true
        
        except BroadcastIOError: -> esto es el nonblocking si no hay nada tira esta exception
            continue

    Server:
    del header obtengo n (paquetes a recibir) y creo un vector de n posiciones 
    while recibidos menor a n:
        socket.recv
        en el vector en la pos numero de paquete pongo el data
            si el numero hizo un salto send ack -numero salteado
        send ack del recibido
        recibidos += 1 si no es repetido

    al terminar escribimos en disco el contenido del vector en orden
