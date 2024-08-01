import json
import socket
import threading

from CommandManagement import CommandManagement

settings = json.load(
    open("bin/settings.json", "r", encoding="utf-8")
)
HOST = settings["server_adress"]  # The server's hostname or IP address
PORT = settings["server_port"]  # The port used by the server


class Server(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.is_running = True
        self.cmdmanagement = CommandManagement.CommandManagement()
        self.cmdmanagement.start()

    def run(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((HOST, PORT))

        while self.is_running:
            self.socket.listen(1)
            conn, addr = s.accept()
            # print('Verbindung mit ', addr, " gefunden und hergestellt.")
            data = conn.recv(1024)
            if data:
                command = data.decode()

                response = self.cmdmanagement.execute_command(command, conn)
                print(response)
                if response is not None:
                    conn.sendall(str(response).encode())

    def stop_server(self):
        print("Server wird gestoppt.")
        self.is_running = False
        self.socket.close()
