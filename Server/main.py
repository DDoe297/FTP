import sys
import logging
import socket
from server.threaded_server import ThreadedServer
from server.client_handlers import ClientHandler
from server.utils import setup_logger
from server.constants import HOST, PORT


def main(host: str, port: int):
    logger = setup_logger(__name__, logging.DEBUG)
    server = ThreadedServer(ClientHandler, logger,
                            socket.AF_INET, socket.SOCK_STREAM)
    server.bind_and_listen(host, port)
    server.start()


if __name__ == '__main__':
    if sys.argv[1]:
        host = sys.argv[1]
    else:
        host = HOST
    if sys.argv[2]:
        port = int(sys.argv[2])
    else:
        port = PORT
    main(host, port)
