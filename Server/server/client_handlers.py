import logging
import threading
import socket


class ClientHandler(threading.Thread):
    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger
        self.socket: socket.socket = socket.socket()
        threading.Thread.__init__(self)

    def run(self) -> None:
        try:
            while True:
                data = self.socket.recv(1024)
                if not data:
                    break
                self.handle_message(data)
        except Exception as _:
            self.logger.debug(
                f'Exception occurred while recieving data from {self.socket.getpeername()}',
                exc_info=True)
            self.logger.info(
                f'Client {self.socket.getpeername()} disconnected')
            self.socket.close()

    def handle_message(self, message: bytes) -> None:
        data = message.decode('utf-8')
        self.logger.info(f'Client {self.socket.getpeername()} sent {data}')
        self.send_message(data)

    def send_message(self, message: str) -> None:
        self.socket.send(message.encode())


class FTPClientHandler(ClientHandler):
    def CDUP(self) -> None:
        pass

    def CWD(self, argument: str) -> None:
        pass

    def HELP(self) -> None:
        reply = """
        214
        CDUP Changes the working directory on the remote host to the parent of the current directory.
        CWD  [Directory Path] Change the working directory to the one specified in argument.
        HELP Displays help information.
        LIST This command allows the server to send the list of files to the passive data channel.
        PASV Get the data channel's port.
        PWD  Get current working directory.
        RETR Sned a copy of a file with the specified path name to the passive data
             channel.
        """
        self.send_message(reply)

    def LIST(self) -> None:
        pass

    def PASV(self) -> None:
        pass

    def PWD(self) -> None:
        pass

    def RETR(self) -> None:
        pass
