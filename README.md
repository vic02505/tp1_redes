# Trabajo Practico 1 - Redes

## Ejecucion Cliente

### Upload
```bash
python upload [-h] [-v|-q] [-H ADDR ] [-p PORT] [-s FILEPATH] [-n FILENAME] [-a ALGORITHM]
```

Opciones:

| Opción         | Descripción                                  |
|----------------|----------------------------------------------|
| `-h`, `--help` | Muestra el mensaje de ayuda y sale.          |
| `-v`, `--verbose` | Incrementa la verbosidad de la salida.    |
| `-q`, `--quiet` | Disminuye la verbosidad de la salida.       |
| `-H`, `--host` | Dirección IP del servidor.                   |
| `-P`, `--port` | Puerto del servidor.                        |
| `-s`, `--src` | Ruta del archivo fuente que se desea subir.  |
| `-n`, `--name` | Nombre del archivo.                         |
| `-a`, `--algorithm` | Algoritmo elegido (sw or sack)         |
#### Ejemplo de uso
```bash
python3 upload.py -H 192.168.1.100 -p 8080 -s /ruta/al/archivo.txt -n archivo.txt -a sack
```

### Download
```bash
python download [-v|-q] [-H ADDR] [-p PORT] [-d FILEPATH ] [-n FILENAME ] [-a ALGORITHM]
```

Opciones:

| Opción            | Descripción                                      |
|-------------------|--------------------------------------------------|
| `-h`, `--help`    | Muestra el mensaje de ayuda y sale.              |
| `-v`, `--verbose` | Incrementa la verbosidad de la salida.           |
| `-q`, `--quiet`   | Disminuye la verbosidad de la salida.            |
| `-H`, `--host`    | Dirección IP del servidor.                       |
| `-p`, `--port`    | Puerto del servidor.                            |
| `-d`, `--dst`     | Ruta de destino del archivo descargado.          |
| `-n`, `--name`    | Nombre del archivo.                             |
| `-a`, `--algorithm` | Algoritmo elegido (sw or sack)               |


#### Ejemplo de uso
```bash
python3 download.py -H 192.168.1.100 -p 8080 -s /ruta/al/archivo.txt -n archivo.txt -a sack
```

## Ejecucion Servidor

```bash
python start-server [-h] [-v|-q] [-H ADDR] [-p PORT] [-s DIRPATH] [-a ALGORITHM]
```
Opciones:

| Opción              | Descripción                                   |
|---------------------|-----------------------------------------------|
| `-h`, `--help`      | Muestra el mensaje de ayuda y sale.           |
| `-v`, `--verbose`   | Incrementa la verbosidad de la salida.        |
| `-q`, `--quiet`     | Disminuye la verbosidad de la salida.         |
| `-H`, `--host`      | Dirección IP del servidor.                    |
| `-p`, `--port`      | Puerto del servidor.                          |
| `-s`, `--storage`   | Directorio donde se almacenarán los archivos. |
| `-a`, `--algorithm` | Algoritmo elegido (sw or sack).               |


#### Ejemplo de uso
```bash
python3 start_server.py -H 192.168.1.100 -p 8080 -s /ruta/de/stotage/ -a sack
```
