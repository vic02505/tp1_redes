# Trabajo Practico 1 - Redes

## Integrantes
- GALIÁN, Tomás Ezequiel - 104354
- SAEZ, Edgardo Francisco - 104896      
- PUJATO, Iñaki - 109131 
- LARDIEZ, Mateo - 107992 
- ZACARIAS, Victor - 107080 

## Ejecucion Cliente

**NOTA: el flag -s no se encuentra implementado, usar por defecto el flag -n con alguno de los nombres de archivos contenidos dentro de del directorio archivos_de_prueba. Lo mismo aplica para el caso de especificar del destino de la descarga (operación download), no hay que especificar la ruta de descarga.**


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

--- 

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
