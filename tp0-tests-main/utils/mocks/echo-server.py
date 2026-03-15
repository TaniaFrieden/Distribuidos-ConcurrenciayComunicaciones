import socket
import sys

healthy = sys.argv[1]

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind(('0.0.0.0', 12345))
    s.listen()

    while True:
        conn, addr = s.accept()
        with conn:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                
                if healthy == 'true':
                  conn.sendall(data)
                else:
                  conn.sendall('error reading data: '.encode()+data)