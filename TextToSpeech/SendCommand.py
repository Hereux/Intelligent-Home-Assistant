import json
import os
import socket

path_to_json = os.path.join(os.path.dirname(os.getcwd()), 'settings.json')
settings = json.load(
    open(path_to_json, "r", encoding="utf-8")
)
HOST = "localhost"  # The server's hostname or IP address
PORT = settings["server_port"]  # The port used by the server


def send_to_server(command: str, *, slot1: str = None, slot2: str = None):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))

    if slot1:
        command = command + "||" + str(slot1)
    if slot2:
        command = command + "||" + str(slot2)
    s.send(command.encode())
    data = s.recv(1024)

    if data:
        received = data.decode()
        print('Received: ', received)
        s.close()
        return received
    else:
        print("No data received")
        s.close()
        return None


