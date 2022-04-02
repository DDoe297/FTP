import logging
import socket
from typing import List, Any, Mapping, Type
from .client_handlers import ClientHandler
from .constants import PORT


class ThreadedServer(socket.socket):
    def __init__(self, handler: Type[ClientHandler], logger: logging.Logger,
                 *args: Any, **kwargs: Mapping[str, Any]) -> None:
        self.logger: logging.Logger = logger
        self.clients: List[ClientHandler] = []
        super(ThreadedServer, self).__init__(*args, **kwargs)
        self.logger.debug('Server is initialized')
        self.handler: Type[ClientHandler] = handler

    def bind_and_listen(self, IP: str, port: int) -> None:
        self.bind((IP, PORT))
        self.listen()
        self.logger.info(f'Server is listening on {IP}:{port}')

    def start(self) -> None:
        try:
            while True:
                (client_socket, _) = self.accept()
                client_thread: ClientHandler = self.handler(self.logger)
                client_thread.socket = client_socket
                self.clients.append(client_thread)
                self.logger.info(
                    f'Client {client_socket.getpeername()} connected')
                client_thread.start()
        except KeyboardInterrupt:
            self.logger.debug('Server got stop command',
                              exc_info=True)
            raise
        except Exception as _:
            self.logger.error(
                'Exception occurred while accepting client',
                exc_info=True)
