"""
this is very slow

the computer running this script needs to be on the labview laptop's hotspot wifi for TCP connection to work

PSEUDOCODE
----------
for each x,y:
    move arm above surface
    go to x,y
    move arm down until encoder senses surface
    record x,y,z
"""

import socket
from threading import Thread
import time
import numpy as np

WIFI_HOST = '0.0.0.0'        # Accept connections from any IP
WIFI_PORT = 5001             # Port to receive Wi-Fi data

KUKA_HOST = '172.31.1.147'   # KUKA iiwa robot IP address
KUKA_PORT = 30002           # KUKA listening port

BUFFER_SIZE = 1024           # Size of buffer for receiving data

encoder_value = 0
done = False
positions = np.zeros((1000, 3))


def receive_labview():
    global encoder_value, done
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
                encoder_value = int(data)
                print(f"received: {encoder_value} from labview")
        except Exception as e:
            print(f"exception: {e}")
            pass
    print('closing connection to labview')

xspan = 0
yspan = 100
d = 1
array_num = 0

def kuka_sweep():
    global encoder_value, done

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as kuka_socket:
            kuka_socket.connect((KUKA_HOST, KUKA_PORT))
            print(f"Connected to KUKA robot at {KUKA_HOST}:{KUKA_PORT}")
            time.sleep(15)
            e0 = encoder_value
            x = 0
            y = 0
            z = 0
            dy = d
            dz = 0.5
            z_init=0
            position_index = 1
            while x <= xspan: 
                while y >= 0 and y <= yspan:
                    # z = (e0 - encoder_value) / 1000
                    temp_encoder_value = encoder_value
                    for z in np.arange(z_init,-25,-0.5):
                        if encoder_value <= temp_encoder_value-200:
                            print(f"record:x={x} y={y} z={z}")
                            # positions[position_index] = [x,y,encoder_value]
                            positions[position_index] = [x,y,z]
                            position_index += 1
                            z_init = z + 2
                            cmd = f"move {x} {y} {z_init}"
                            print(f"sending kuka: {cmd}")
                            # Forward data to KUKA
                            kuka_socket.sendall((cmd + "\n").encode())
                            time.sleep(.5)
                            break
                        cmd = f"move {x} {y} {z}"
                        print(f"sending kuka: {cmd}")
                        # Forward data to KUKA`
                        kuka_socket.sendall((cmd + "\n").encode())
                        time.sleep(.5)
                    y += dy
                    cmd = f"move {x} {y} {z}"
                    print(f"sending kuka: {cmd}")
                    # Forward data to KUKA
                    kuka_socket.sendall((cmd + "\n").encode())
                    time.sleep(.5)
                y -= dy
                x += d
                dy *= -1

            kuka_socket.sendall("exit\n".encode())
            # Print full array
            np.savetxt("positions.csv", positions, delimiter=",", header="x,y,z", comments='', fmt="%.3f")

    except Exception as e:
        print(f"Error with KUKA connection: {e}")

    done = True

if __name__ == "__main__":

    thread1 = Thread(target=kuka_sweep)
    thread2 = Thread(target=receive_labview)

    # thread1.start()
    thread2.start()

    # thread1.join()
    thread2.join()

    
    
    

def receive_and_forward():
    """Receive data from a client over Wi-Fi and forward to KUKA until 'exit' is received."""

     # Start server to receive data over Wi-Fi
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as wifi_socket:
         wifi_socket.bind((WIFI_HOST, WIFI_PORT))
         wifi_socket.listen(1)
         print(f"Listening for incoming Wi-Fi connection on port {WIFI_PORT}...")

         conn, addr = wifi_socket.accept()
         print(f"Connected to Wi-Fi client: {addr}")
         # Connect once to KUKA and keep the connection open
         try:
             with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as kuka_socket:
                kuka_socket.connect((KUKA_HOST, KUKA_PORT))
                print(f"Connected to KUKA robot at {KUKA_HOST}:{KUKA_PORT}")

                with conn:
                     while True:
                         data = conn.recv(BUFFER_SIZE)
                         if not data:
                             print("Wi-Fi client closed the connection.")
                             break

                         decoded_data = data.decode('utf-8').strip()
                         print(f"Received: {decoded_data}")

                         if decoded_data.lower() == 'exit':
                             print("Received 'exit'. Closing all connections.")
                             break

                         # Forward data to KUKA
                         kuka_socket.sendall((decoded_data + '\n').encode())
                         print(f"Forwarded to KUKA: {decoded_data}")

         except Exception as e:
             print(f"Error with KUKA connection: {e}")

