import socket
import time
import random
from datetime import datetime
from tzlocal import get_localzone
import pytz

HOST = input("Enter controller IP address: ")  # e.g., 10.113.22.83
PORT = 9999
name = input("Enter your node name (e.g., Node1): ")

lamport_clock = random.randint(1, 5)
local_tz = get_localzone()  # Auto-detect system timezone
timezone_name = str(local_tz)

def node():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            while True:
                time.sleep(2)
                global lamport_clock
                lamport_clock += 1

                now = datetime.now(local_tz)
                current_time = now.astimezone(pytz.utc).timestamp()

                s.sendall(f"{name}:{current_time}:{lamport_clock}:{timezone_name}".encode())

                data = s.recv(1024).decode()
                if data.startswith("SYNC"):
                    _, _, interval = data.split(":")
                    print(f"[{name}] SYNC RECEIVED (Interval {interval}s)")
                    time.sleep(int(interval))
                elif data.startswith("IGNORE"):
                    _, interval = data.split(":")
                    print(f"[{name}] Ignored (Interval {interval}s)")
                    time.sleep(int(interval))

    except Exception as e:
        print(f"[{name}] Error: {e}")

if __name__ == "__main__":
    node()