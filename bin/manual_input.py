import socket


def send_to_server(command: str, *, slot1: str = None, slot2: str = None):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("localhost", 50007))

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


while True:
    command = input("Befehl: ")
    slot1 = input("Slot 1: ")
    slot2 = input("Slot 2: ")
    send_to_server(command, slot1=slot1, slot2=slot2)
