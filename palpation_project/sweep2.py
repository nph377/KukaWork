"""
*** the computer running this script needs to be on the labview laptop's hotspot wifi for TCP connection to work ***


two threads:
1. receive_labview() will constantly listen for data from labview and update encoder_value
2. kuka_sweep() will command the robot to move to x,y points. at each point it will calculate the z value using encoder_value and record [x,y,z]
   - arm will stay at constant height where encoder can still reach the lowest point on surface 
after kuka_sweep() is completed, both threads terminate and the surface data is saved
"""

import socket
from threading import Thread
import time
import datetime
import numpy as np

WIFI_HOST = '0.0.0.0'        # Accept connections from any IP
WIFI_PORT = 5001             # Port to receive Wi-Fi data

KUKA_HOST = '172.31.1.147'   # KUKA iiwa robot IP address
KUKA_PORT = 30004           # KUKA listening port

BUFFER_SIZE = 1024           # Size of buffer for receiving data

# SET THESE
xspan = 0 # mm of total x travel
yspan = 100 # mm of total y travel
d = 1 # mm between each point

# init globals
done = False
encoder_value = None

print("are you on the laptop hotspot?")
print("is the kuka program running?")
input("press enter to continue")

def receive_labview():
    global encoder_value, done
    # Start server to receive data over Wi-Fi
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as wifi_socket:
        wifi_socket.bind((WIFI_HOST, WIFI_PORT))
        wifi_socket.listen(1)
        print(f"Listening for incoming Wi-Fi connection on port {WIFI_PORT}...")

        conn, addr = wifi_socket.accept()
        print(f"Connected to Wi-Fi client: {addr}")
        conn.sendall("hello from python\n".encode())

        try:
            while not done:
                data = conn.recv(BUFFER_SIZE).decode()
                conn.sendall("python received data\n".encode())
                print(f"received: {data} from labview")
                if data.isdigit():
                    encoder_value = int(data)
                else:
                    print("not a number, encoder_value unchanged")
        except:
            pass
    print('closing connection to labview')

def kuka_sweep():
    global encoder_value, done

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as kuka_socket:
            kuka_socket.connect((KUKA_HOST, KUKA_PORT))
            print(f"Connected to KUKA robot at {KUKA_HOST}:{KUKA_PORT}")
            x = 0
            y = 0
            dy = d
            dx = d
            positions = []

            # wait for encoder_value to update, confirm that it has
            for _ in range(15):
                if encoder_value is not None:
                    break
                time.sleep(1)
            if encoder_value is None:
                print("encoder_value is not set. terminating sweep.")
                done = True
                return
            else:
                e0 = encoder_value
                print("initial encoder_value set to {eo}")

            while x <= xspan: 
                while y >= 0 and y <= yspan:
                    # command KUKA to move
                    cmd = f"move {x} {y} {0}"
                    print(f"sending kuka: {cmd}")
                    kuka_socket.sendall((cmd + "\n").encode())
                    time.sleep(.5)

                    # record encoder position
                    z = (e0 - encoder_value) / 1000
                    print(f"record: {x},{y},{z}")
                    positions.append([x,y,z])

                    # move y
                    y += dy

                # move x and reverse y direction
                x += dx
                dy *= -1

            # tell kuka we're done
            kuka_socket.sendall("exit\n".encode())

            # save data
            positions = np.array(positions)
            epoch_time = time.time()
            dt_object = datetime.datetime.fromtimestamp(epoch_time)
            formatted_time = dt_object.strftime("%Y-%m-%d_%H-%M-%S")
            filename = "surface_data_" + formatted_time
            np.savetxt(f"surface_data/{filename}.csv", positions, delimiter=",", header="x,y,z", comments='', fmt="%.3f")

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