import sys
import logging
import socket
from server.threaded_server import ThreadedServer
from server.client_handlers import FTPClientHandler
from server.utils import setup_logger
from server.constants import HOST, PORT


def main(host: str, port: int):
    logger:logging.Logger = setup_logger(__name__, logging.INFO, logging.DEBUG)
    server:ThreadedServer = ThreadedServer(FTPClientHandler, logger,
                            socket.AF_INET, socket.SOCK_STREAM)
    server.bind_and_listen(host, port)
    server.start()


if __name__ == '__main__':
    server_host: str = HOST
    server_port: int = PORT
    try:
        server_host:str = sys.argv[1]
    except IndexError:
        pass
    try:
        server_port:int = int(sys.argv[2])
    except IndexError:
        pass
    main(server_host, server_port)
