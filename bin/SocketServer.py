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
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((HOST, PORT))

        while self.is_running:
            print("Server läuft.")
            s.listen(1)
            conn, addr = s.accept()
            # print('Verbindung mit ', addr, " gefunden und hergestellt.")
            data = conn.recv(1024)
            if data:
                command = data.decode()

                self.cmdmanagement.execute_command(command, conn)

                conn.sendall(str('Befehl "' + command + '" ausgeführt.').encode())
    def stop_server(self):
        print("Server wird gestoppt.")
        self.is_running = False
