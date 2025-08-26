import socket

KUKA_HOST = '172.31.1.147'   # KUKA iiwa robot IP address
KUKA_PORT = 30007           # KUKA listening port

try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as kuka_socket:
        kuka_socket.connect((KUKA_HOST, KUKA_PORT))
        print(f"Connected to KUKA robot at {KUKA_HOST}:{KUKA_PORT}")

        kuka_socket.sendall("exit\n".encode())
        print("kuka disconnected")
except Exception as e:
    print(f"Error with KUKA connection: {e}")