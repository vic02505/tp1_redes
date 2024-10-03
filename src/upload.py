from lib.client import Client
import argparse

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Upload files to a server.")

    # Argumentos opcionales
    parser.add_argument('-v', '--verbose', action='store_true', help="Increase output verbosity")
    parser.add_argument('-q', '--quiet', action='store_true', help="Decrease output verbosity")
    parser.add_argument('-H', '--host', type=str, default="127.0.0.1", help="Server IP address")
    parser.add_argument('-p', '--port', type=int, default=12345, help="Server port")
    parser.add_argument('-s', '--src', type=str, default="", help="Source file path")
    parser.add_argument('-n', '--name', type=str, default="", help="File name")
    parser.add_argument('-a', '--algorithm', type=str, default="sw", help="sw or sack")

    # Parsear los argumentos
    args = parser.parse_args()

    # Ajustar verbosidad
    verbose = args.verbose and not args.quiet

    client = Client(args.host, args.port, args.algorithm)
    client.upload(args.name, args.algorithm)
    client.close()