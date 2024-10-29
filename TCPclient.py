import socket
import threading


server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.connect(('localhost', 3999))
msg= server_socket.recv(1024)
print(msg.decode("utf-8"))
