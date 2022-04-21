from http import client
import socket


class FTPClient():

    def __init__(self, host, port):

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.host = host
        self.port = int(port)

    def connect(self):
        print('Starting connection to', self.host, ':', self.port)
        self.sock.connect((self.host, self.port))
        self.sock.recv(1024)

    def run(self):
        while True:
            command = input('Enter a command: ')
            if len(command) == 0:
                print('Try again.')
                continue
            if 'HELP' in command:
                self.HELP()
            elif 'LIST' in command:
                self.LIST()
            elif 'PWD' in command:
                self.PWD()
            elif 'QUIT' in command:
                self.QUIT()
            elif 'CD' in command:
                self.CD(command[3:].strip())
            elif 'DWLD' in command:
                self.DWLD(command[4:].strip())
            else:
                print('Incorrect command, Try again.')
                continue

    def new_passive_connection(self):
        self.pasv()
        self.passive_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.passive_socket.connect((self.host, self.passive_port))

    def pasv(self):
        self.sock.send(b'PASV\r\n')
        reply = self.sock.recv(1024).decode()
        reply = reply.strip().strip('('+').').split(',')
        self.passive_port = int(reply[4])*256+int(reply[5])

    def LIST(self):
        print('Requesting files...')
        self.new_passive_connection()
        self.sock.send(b'LIST\r\n')
        self.sock.recv(1024)
        files = ""
        while True:
            data = self.passive_socket.recv(1024).decode()
            if len(data) == 0:
                break
            files += data
            print(files.strip())
        self.sock.recv(1024)
        self.passive_socket.close()

    def DWLD(self, file_path):
        print('Downloading', file_path, 'from server...')
        self.new_passive_connection()
        self.sock.send(f'RETR {file_path}\r\n'.encode())
        self.sock.recv(1024)
        with open(file_path, 'wb') as file:
            while True:
                data = self.passive_socket.recv(1024)
                if len(data) == 0:
                    break
                file.write(data)
        self.passive_socket.close()
        self.sock.recv(1024)
        print('Successfully downloaded: ', file_path)

    def PWD(self):
        print('Requesting path...')
        self.sock.send(b'PWD\r\n')
        path = self.sock.recv(1024).decode()
        print(path[4:].strip())

    def CD(self, dir_name):
        if dir_name == '..':
            self.sock.send(b'CDUP\r\n')
        else:
            self.sock.send(f'CWD {dir_name}\r\n'.encode())
        result = self.sock.recv(1024).decode()
        if '550' in result:
            print("Operation Failed")
        else:
            self.PWD()

    def QUIT(self):
        print('Closing socket connection')
        self.sock.close()
        quit()

    def HELP(self):
        print('Enter one of the following functions:')
        print('HELP\t\t', ': Show this text')
        print('LIST\t\t', ': List files')
        print('PWD\t\t', ': Show current directory')
        print('CD dir_name\t', ': change directory')
        print('DWLD file_path\t', ': Download file')
        print('QUIT\t\t', ': Exit')
        return


client = FTPClient('127.0.0.1', '2121')
client.connect()
client.run()
