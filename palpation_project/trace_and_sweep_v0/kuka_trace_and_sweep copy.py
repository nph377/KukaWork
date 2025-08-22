"""
*** the computer running this script needs to be on the labview laptop's hotspot wifi for TCP connection to work ***
*** MAKE SURE THE FIREWALL IS OFF ***


two threads:
1. receive_labview() will constantly listen for data from labview and update encoder_value
2. kuka_trace_and_sweep()
    - record the starting position

    - trace
        command the robot to move to x,y points
        at each point
            record the encoder value before moving down
            move down until encoder value changes
            calculate the z value using encoder_value and record [x,y,z]

    - record the surface data
    - move back to the starting position

    - sweep
        wait for user input
        loop
            labview tell python when to move to next point
            python async move the kuka
            labview wait a few sec for python to move the kuka to that point
            labview does the sweep

after kuka_trace_and_sweep() is completed, both threads terminate

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
xspan = 0 # [mm] of total x travel
yspan = 80 # [mm] of total y travel
d = 1 # [mm] between each point
zspan = 20 # [mm] of maximum z travel (to prevent running into table)
dz = 1 # [mm] of z increment (how far it will move down on each iteration before checking if encoder_value has changed)
encoder_value_delta_threshold = 10 # [nm] amount encoder value must change to detect surface

n_sweep_points = 3
sweep_z_offset = 0 # [mm] above the recorded z for each x,y the kuka arm will move to before beginning a sweep

# init globals
done = False
encoder_value = None
wait_for_labview = True

print("are you on the laptop hotspot?")
print("is the kuka program running?")
input("press enter to continue")

def receive_labview():
    global encoder_value, done, wait_for_labview
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
                # print(f"received: {data} from labview")
                if data.isdigit():
                    encoder_value = int(data)
                elif data == "finish":
                    wait_for_labview = False
                else:
                    print(f"labview data not recognized: {data}")
        except:
            pass
    print('closing connection to labview')

def kuka_trace_and_sweep():
    global encoder_value, done, wait_for_labview

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
                print("encoder_value is not set. terminating program.")
                done = True
                return
            else:
                print("encoder_value is being updated properly. proceeding to trace")

            ##### TRACE SURFACE
            while x <= xspan: 
                while y >= 0 and y <= yspan:
                    # command KUKA to move
                    cmd = f"move {x} {y} {0}"
                    print(f"moving to next point: {cmd}")
                    kuka_socket.sendall((cmd + "\n").encode())
                    time.sleep(.5)

                    # move down to contact surface
                    e0 = encoder_value
                    z = 0
                    print(f"moving down to contact surface")
                    while abs(e0 - encoder_value) < encoder_value_delta_threshold and abs(z) < zspan:
                        z -= dz 
                        print(f"{z = }")
                        cmd = f"move {x} {y} {z}"
                        kuka_socket.sendall((cmd + "\n").encode())
                        time.sleep(.5)

                    # record surface data
                    print("contacted surface or hit zspan")
                    z_record = z + (e0 - encoder_value) / 1000
                    print(f"record: {x},{y},{z_record}")
                    positions.append([x,y,z_record])

                    # go back to z0
                    cmd = f"move {x} {y} {0}"
                    print(f"moving back up to z0: {cmd}")
                    kuka_socket.sendall((cmd + "\n").encode())
                    time.sleep(1)

                    # set next y
                    y += dy

                # set next x and reverse y direction
                x += dx
                dy *= -1

            # save data
            positions = np.array(positions)
            epoch_time = time.time()
            dt_object = datetime.datetime.fromtimestamp(epoch_time)
            formatted_time = dt_object.strftime("%Y-%m-%d_%H-%M-%S")
            filename = "surface_data_" + formatted_time
            np.savetxt(f"surface_data/{filename}.csv", positions, delimiter=",", header="x,y,z", comments='', fmt="%.3f")

            # move back to starting position
            cmd = f"move 0 0 0"
            print(f"sending kuka: {cmd}")
            kuka_socket.sendall((cmd + "\n").encode())
            time.sleep(5)

            input("hit enter to continue")

        # loop
        #     labview tell python when to move to next point
        #     python async move the kuka
        #     labview wait a few sec for python to move the kuka to that point
        #     labview does the sweep

            ##### SWEEP
            i_points = [int(i*len(positions)/(n_sweep_points-1)) for i in range(n_sweep_points)]

            # wait for labview
            while wait_for_labview:
                print("waiting for labview...")
                time.sleep(1)

            for i in range(n_sweep_points):
                # move kuka to next x,y,z0
                x,y,z = positions[i]
                cmd = f"move {x} {y} {0}"
                print(f"moving to next point: {cmd}")
                kuka_socket.sendall((cmd + "\n").encode())
                time.sleep(1)

                # move kuka to next x,y,z+offset
                cmd = f"move {x} {y} {z+sweep_z_offset}"
                print(f"moving down to surface (z_record + sweep_z_offset): {cmd}")
                kuka_socket.sendall((cmd + "\n").encode())
                time.sleep(1)

                wait_for_labview = True

                # wait for labview
                while wait_for_labview:
                    print("waiting for labview...")
                    time.sleep(.5)

                # move kuka back to z0
                cmd = f"move {x} {y} {0}"
                print(f"moving to next point: {cmd}")
                kuka_socket.sendall((cmd + "\n").encode())
                time.sleep(1)

            # move back to starting position
            cmd = f"move 0 0 0"
            print(f"sending kuka: {cmd}")
            kuka_socket.sendall((cmd + "\n").encode())
            time.sleep(5)

    except Exception as e:
        print(f"Error with KUKA connection: {e}")

    finally:
        # tell kuka we're done
        kuka_socket.sendall("exit\n".encode())
        done = True

if __name__ == "__main__":

    thread1 = Thread(target=kuka_trace_and_sweep)
    thread2 = Thread(target=receive_labview)

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()