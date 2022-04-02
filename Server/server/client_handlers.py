import logging
import pathlib
import socket
import threading
from .constants import DEFAULT_DIR


class ClientHandler(threading.Thread):
    def __init__(self, logger: logging.Logger) -> None:
        self.logger: logging.Logger = logger
        self.socket: socket.socket = socket.socket()
        threading.Thread.__init__(self)

    def run(self) -> None:
        try:
            while True:
                data: bytes = self.socket.recv(1024)
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

    def handle_message(self, data: bytes) -> None:
        message = data.decode('utf-8')
        self.logger.info(f'Client {self.socket.getpeername()} sent {message}')
        self.send_message(message)

    def send_message(self, message: str) -> None:
        self.logger.debug(
            f'Sent {message.strip()} to client {self.socket.getpeername()}.')
        self.socket.send(message.encode())


class FTPClientHandler(ClientHandler):
    def __init__(self, logger: logging.Logger) -> None:
        super().__init__(logger)
        self.working_wirectory: pathlib.Path = DEFAULT_DIR
        self.passive_mode: bool = False

    def run(self) -> None:
        self.welcome()
        super().run()

    def handle_message(self, data: bytes) -> None:
        message: str = data.decode('utf-8')[:-1]
        command: str = message[:4].strip().upper()
        argument: str | None = message[4:].strip() or None
        if command == "QUIT":
            self.QUIT()
        else:
            try:
                command_handler_function = getattr(self, command)
                if argument:
                    command_handler_function(argument)
                else:
                    command_handler_function()
            except:
                self.send_message(
                    '500 Syntax error, command unrecognized.\r\n')

    def CDUP(self) -> None:
        self.logger.info(f'Client {self.socket.getpeername()} sent CUDP.')
        if self.working_wirectory != DEFAULT_DIR:
            self.logger.debug(f'Client {self.socket.getpeername()} CDUP: successful. ' +
                              f'Current working directory: {self.working_wirectory}')
            self.working_wirectory = self.working_wirectory.parent
            self.send_message("226 Operation successful\r\n")
        else:
            self.logger.debug(f'Client {self.socket.getpeername()} CDUP: already in root directory. ' +
                              f'Current working directory: {self.working_wirectory}')
            self.send_message("226 Operation successful\r\n")

    def CWD(self, argument: str) -> None:
        self.logger.info(
            f'Client {self.socket.getpeername()} sent CWD with argument {argument}.')
        path: pathlib.Path = self.working_wirectory/argument
        if path.is_dir() and str(path.resolve()).startswith(str(DEFAULT_DIR.resolve())):
            self.logger.debug(f'Client {self.socket.getpeername()} CWD: successful. ' +
                              f'Current working directory: {self.working_wirectory}')
            self.working_wirectory = path
            self.send_message("226 Operation successful\r\n")
        else:
            self.logger.debug(f'Client {self.socket.getpeername()} CWD: wrong folder path. ' +
                              f'Current working directory: {self.working_wirectory}')
            self.send_message("550 Couldn't open the file or directory\r\n")

    def HELP(self) -> None:
        self.logger.info(f'Client {self.socket.getpeername()} sent HELP.')
        reply: str = "214\r\n" +\
            "CDUP Changes the working directory on the remote host to the parent of the current directory.\r\n" +\
            "CWD  [Directory path] Change the working directory to the one specified in argument.\r\n" +\
            "HELP Displays help information.\r\n" +\
            "LIST This command allows the server to send the list of files to the passive data channel.\r\n" +\
            "PASV Get the data channel's port.\r\n" +\
            "PWD  Get current working directory.\r\n" +\
            "QUIT Terminate connection.\r\n" +\
            "RETR [File name] Sned a copy of a file with the specified path name to the passive data channel.\r\n" +\
            "\r\n"
        self.send_message(reply)

    def LIST(self) -> None:
        self.logger.info(f'Client {self.socket.getpeername()} sent LIST.')
        if self.passive_mode:
            message: str = ''
            for file in self.working_wirectory.iterdir():
                if file.is_dir():
                    message += f'>{file.name}\r\n'
                elif file.is_file():
                    message += f'{file.name} Size: {file.stat().st_size} bytes\r\n'
            message += '\r\n'
            self.send_message('150 About to start data transfer.\r\n')
            self.logger.debug(
                f'Client {self.socket.getpeername()} LIST: starting data transfer')
            self.start_data_channel()
            self.send_data(message.encode())
            self.logger.debug(
                f'Client {self.socket.getpeername()} LIST: sending data over data channel')
            self.stop_data_channel()
            self.send_message('226 Operation successful\r\n')
            self.logger.debug(
                f'Client {self.socket.getpeername()} LIST: successful')
        else:
            self.logger.debug(
                f'Client {self.socket.getpeername()} LIST: passive mode is disabled.')
            self.send_message('500 Passive mode is disabled\r\n')

    def PASV(self) -> None:
        self.logger.info(f'Client {self.socket.getpeername()} sent PASV.')
        host = self.socket.getsockname()[0]
        self.passive_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.passive_socket.bind((host, 0))
        self.passive_socket.listen()
        address, port = self.passive_socket.getsockname()
        message: str = f'227 Entering Passive Mode ({",".join(address.split("."))},{port>>8&0xFF},{port&0xFF}).\r\n'
        self.passive_mode = True
        self.logger.debug(
            f'Client {self.socket.getpeername()} PASV: passive mode started on {address}:{port}')
        self.send_message(message)

    def PWD(self) -> None:
        self.logger.info(f'Client {self.socket.getpeername()} sent PWD.')
        self.logger.debug(
            f'Client {self.socket.getpeername()} PWD: current working directory: {self.working_wirectory}')
        if self.working_wirectory == DEFAULT_DIR:
            self.send_message(f'257 "/" is current directory.\r\n')
        else:
            path = self.working_wirectory.relative_to(DEFAULT_DIR)
            self.send_message(f'257 "/{str(path)}" is current directory.\r\n')

    def QUIT(self) -> None:
        self.logger.info(f'Client {self.socket.getpeername()} sent QUIT.')
        self.send_message('221 Goodbye.\r\n')
        raise Exception

    def RETR(self, argument: str) -> None:
        self.logger.info(
            f'Client {self.socket.getpeername()} sent RETR with argument {argument}.')
        if self.passive_mode:
            file:pathlib.Path = self.working_wirectory/argument
            if file.is_file():
                self.logger.debug(
                    f'Client {self.socket.getpeername()} RETR: starting data transfer.')
                self.send_message('150 About to start data transfer.\r\n')
                self.start_data_channel()
                self.logger.debug(
                    f'Client {self.socket.getpeername()} RETR: sending data over data channel')
                with file.open('rb') as data:
                    self.send_data(data.read())
                self.stop_data_channel()
                self.send_message('226 Operation successful\r\n')
                self.logger.debug(
                    f'Client {self.socket.getpeername()} LIST: successful')
            else:
                self.logger.debug(
                    f'Client {self.socket.getpeername()} RETR: specified argument was not a file.')
                self.send_message(
                    "550 Couldn't open the file or directory.\r\n")
        else:
            self.logger.debug(
                f'Client {self.socket.getpeername()} RETR: passive mode is disabled.')
            self.send_message('500 Passive mode is disabled\r\n')

    def welcome(self) -> None:
        self.send_message('220 Welcome.\r\n')

    def start_data_channel(self) -> None:
        self.logger.debug(
            f'Data channel started for client {self.socket.getpeername()}.')
        try:
            self.data_socket, _ = self.passive_socket.accept()
        except socket.error as _:
            self.logger.debug(
                f'Exception occurred while starting data channel for {self.socket.getpeername()}',
                exc_info=True)

    def stop_data_channel(self) -> None:
        self.logger.debug(
            f'Data channel stopped for client {self.socket.getpeername()}.')
        try:
            self.data_socket.close()
            self.passive_socket.close()
            self.passive_mode = False
        except socket.error as _:
            self.logger.debug(
                f'Exception occurred while closing data channel for {self.socket.getpeername()}',
                exc_info=True)

    def send_data(self, message: bytes) -> None:
        self.logger.debug(
            f'Sending data for client {self.socket.getpeername()}')
        self.data_socket.send(message)
