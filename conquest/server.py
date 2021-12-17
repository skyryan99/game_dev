# Runs a server for the users to connect to when they are ready to play
import socket
from _thread import *
import pickle

server = "192.168.1.100"
port = 5555

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    sock.bind((server, port))
except socket.error as e:
    print(str(e))

sock.listen(2)
print("Waiting for a connection")

player_object1 = "Stand-in String for Player 1"
player_object2 = "Stand-in String for Player 2"
players = [player_object1, player_object2]


def threaded_client(conn, player_num):
    conn.send(pickle.dumps(players[player_num]))
    reply = ""
    while True:
        # Get data from client
        try:
            data = pickle.loads(conn.recv(2048))
            players[player_num] = data
            # If client left
            if not data:
                print("Disconnected")
                break
            else:
                if player_num == 1:
                    reply = players[0]
                else:
                    reply = players[1]
                print("Recieved: ", data)
                print("Sending: ", reply)

            conn.sendall(pickle.dumps(reply))
        except:
            print("Exception while fetching client data")
            break
    print("Lost connection to server")
    conn.close()


current_player = 0

while True:
    connection, address = sock.accept()
    print("Conneted to: ", address)
    start_new_thread(threaded_client, (connection, current_player))
    current_player += 1