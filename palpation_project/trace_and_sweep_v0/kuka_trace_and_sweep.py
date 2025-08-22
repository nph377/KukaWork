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
WIFI_PORT = 5003             # Port to receive Wi-Fi data

KUKA_HOST = '172.31.1.147'   # KUKA iiwa robot IP address
KUKA_PORT = 30004           # KUKA listening port

BUFFER_SIZE = 1024           # Size of buffer for receiving data

# SET THESE

kuka_enable = False

xspan = 0 # [mm] of total x travel
yspan = 10 # [mm] of total y travel
d = 1 # [mm] between each point
zspan = 20 # [mm] of maximum z travel (to prevent running into table)
dz = 1 # [mm] of z increment (how far it will move down on each iteration before checking if encoder_value has changed)
encoder_value_delta_threshold = 10 # [nm] amount encoder value must change to detect surface

n_sweep_points = 3
sweep_z_offset = 0 # [mm] above the recorded z for each x,y the kuka arm will move to before beginning a sweep

# init globals
done = False
encoder_value = None
labview_state = None
labview_connected = False

if kuka_enable:
    print("is the kuka program running?")
else:
    print("WARNING: kuka is disabled")
print("are you on the laptop hotspot?\nfirewall disabled?")
input("press enter to continue")

def receive_labview():
    global encoder_value, done, labview_state, labview_connected
    # Start server to receive data over Wi-Fi
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as wifi_socket:
        wifi_socket.bind((WIFI_HOST, WIFI_PORT))
        wifi_socket.listen(1)
        print(f"Listening for incoming Wi-Fi connection on port {WIFI_PORT}...")

        conn, addr = wifi_socket.accept()
        print(f"Connected to Wi-Fi client: {addr}")
        labview_connected = True

        try:
            while not done:
                data = conn.recv(BUFFER_SIZE).decode()
                # print(f"received: {data} from labview")
                if data.isdigit():
                    encoder_value = int(data)
                elif data.lower() in ("finished", "start", "sweeping"):
                    labview_state = data.lower()
                    print(f"{labview_state = }")
                else:
                    print(f"labview data not recognized: {data}")
                    print(f"{type(data) = }")
        except Exception as e:
            print(f"Exception: {e}")

    print('closing connection to labview')

def kuka_trace_and_sweep():
    global encoder_value, done, labview_state

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as kuka_socket:
            kuka_socket.connect((KUKA_HOST, KUKA_PORT))
            print(f"Connected to KUKA robot at {KUKA_HOST}:{KUKA_PORT}")
            x = 0
            y = 0
            dy = d
            dx = d
            positions = []

            while not labview_connected:
                time.sleep(1)
            print("labview connected")

            # wait for encoder_value to update, confirm that it has
            for _ in range(30):
                print("waiting for encoder_value stream...")
                if encoder_value is not None:
                    break
                time.sleep(1)
            if encoder_value is None:
                print("encoder_value is not set. terminating program.")
                done = True
                return
            else:
                print("encoder_value is being updated properly. proceeding to trace")

            ####################    TRACE SURFACE    #####################
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
                        # print(f"{z = }")
                        cmd = f"move {x} {y} {z}"
                        kuka_socket.sendall((cmd + "\n").encode())
                        time.sleep(.5)

                    # record surface data
                    print("contacted surface or hit zspan")
                    z_record = z + (e0 - encoder_value) / 1000
                    if abs(z_record) > zspan:
                        z_record = zspan * np.sign(z_record)
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

            ####################    SWEEP    #####################
            i_points = [int(i*len(positions)/(n_sweep_points-1)) for i in range(n_sweep_points)]

            # move back to first sweep position
            x,y,z = positions[0]
            cmd = f"move {x} {y} 0"
            print(f"sending kuka: {cmd}")
            kuka_socket.sendall((cmd + "\n").encode())
            time.sleep(1)

            cmd = f"move {x} {y} {z+sweep_z_offset}"
            print(f"sending kuka: {cmd}")
            kuka_socket.sendall((cmd + "\n").encode())
            time.sleep(1)

            # wait for labview
            while labview_state not in ("start", "sweeping"):
                print("waiting for labview to begin first sweep...")
                time.sleep(1)

            for i in range(1,n_sweep_points):
                print(f"for loop: {i = }")
                # wait for labview to sweep
                while labview_state != "finished":
                    print("labview performing sweep...")
                    time.sleep(.5)

                # move kuka straight up
                x,y,z = positions[i-1]
                cmd = f"move {x} {y} {0}"
                print(f"moving to next point: {cmd}")
                kuka_socket.sendall((cmd + "\n").encode())
                time.sleep(1)

                # move kuka to next x,y,z+offset
                x,y,z = positions[i]
                cmd = f"move {x} {y} {z+sweep_z_offset}"
                print(f"moving down to surface (z_record + sweep_z_offset): {cmd}")
                kuka_socket.sendall((cmd + "\n").encode())
                time.sleep(1)

                # wait for labview
                while labview_state not in ("start", "sweeping"):
                    print("waiting for labview...")
                    time.sleep(1)

            print("out of for loop")
            while labview_state != "finished":
                print("waiting for labview...")
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




def kuka_sweep():
    global encoder_value, done, labview_state

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as kuka_socket:
            kuka_socket.connect((KUKA_HOST, KUKA_PORT))
            print(f"Connected to KUKA robot at {KUKA_HOST}:{KUKA_PORT}")
            positions = [(0,0,0), (0,10,0), (0,20,0)]

            while not labview_connected:
                time.sleep(1)
            print("labview connected")

            ####################    SWEEP    #####################

            # move back to first sweep position
            x,y,z = positions[0]
            cmd = f"move {x} {y} 0"
            print(f"sending kuka: {cmd}")
            kuka_socket.sendall((cmd + "\n").encode())
            time.sleep(1)

            cmd = f"move {x} {y} {z+sweep_z_offset}"
            print(f"sending kuka: {cmd}")
            kuka_socket.sendall((cmd + "\n").encode())
            time.sleep(1)

            # wait for labview
            while labview_state not in ("start", "sweeping"):
                print("waiting for labview to begin first sweep...")
                time.sleep(1)

            for i in range(1,n_sweep_points):
                print(f"for loop: {i = }")
                # wait for labview to sweep
                while labview_state != "finished":
                    print("labview performing sweep...")
                    time.sleep(.5)

                # move kuka straight up
                x,y,z = positions[i-1]
                cmd = f"move {x} {y} {0}"
                print(f"moving to next point: {cmd}")
                kuka_socket.sendall((cmd + "\n").encode())
                time.sleep(1)

                # move kuka to next x,y,z+offset
                x,y,z = positions[i]
                cmd = f"move {x} {y} {z+sweep_z_offset}"
                print(f"moving down to surface (z_record + sweep_z_offset): {cmd}")
                kuka_socket.sendall((cmd + "\n").encode())
                time.sleep(1)

                # wait for labview
                while labview_state not in ("start", "sweeping"):
                    print("waiting for labview...")
                    time.sleep(1)

            print("out of for loop")
            while labview_state != "finished":
                print("waiting for labview...")
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
    thread3 = Thread(target=kuka_sweep)

    if kuka_enable:
        thread1.start()
    thread2.start()
    thread3.start()

    if kuka_enable:
        thread1.join()
    thread2.join()
    thread3.join()
