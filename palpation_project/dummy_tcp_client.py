'''
for testing
'''
import socket

host = 'localhost'
port = 5000

s = socket.socket()
s.connect((host,port))

while True:
    data = input("send to server: ")
    s.send(data.encode())
    if data == "exit":
        break

print("ending client")
s.close()