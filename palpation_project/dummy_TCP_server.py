'''
for testing
'''
import socket
from threading import Thread
import time
import numpy as np

WIFI_HOST = '0.0.0.0'        # Accept connections from any IP
WIFI_PORT = 5000             # Port to receive Wi-Fi data

BUFFER_SIZE = 1024           # Size of buffer for receiving data

encoder_value = 0
done = False
data = None

def receive_data():
    global encoder_value, done, data
    # Start server to receive data over Wi-Fi
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as wifi_socket:
        wifi_socket.bind((WIFI_HOST, WIFI_PORT))
        wifi_socket.listen(1)
        print(f"Listening for incoming Wi-Fi connection on port {WIFI_PORT}...")

        conn, addr = wifi_socket.accept()
        print(f"Connected to Wi-Fi client: {addr}")

        try:
            while not done:
                data = conn.recv(BUFFER_SIZE).decode()
                print(f"received: {data}")
                if data == "exit":
                    done = True
                elif data.isdigit():
                    encoder_value = int(data)
        except Exception as e:
            print(f"Exception: {e}")
        finally:
            done = True
    print('closing connection to client')

def dummy_ctrl_program():
    while not done:
        print(f"{encoder_value = }")
        print(f"last received: {data}")
        time.sleep(.1)


if __name__ == "__main__":

    thread1 = Thread(target=dummy_ctrl_program)
    thread2 = Thread(target=receive_data)

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()
