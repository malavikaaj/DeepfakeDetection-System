import socket
import threading
import time
import random
import json
from datetime import datetime
import pytz

HOST = '0.0.0.0'
PORT = 9999
trust_scores = {}
node_states = {}
sync_intervals = {}
q_table = {}
learning_rate = 0.1
discount = 0.9
MAX_INTERVAL = 10

def q_learn(name, anomaly):
    state = "normal" if not anomaly else "anomaly"
    if name not in q_table:
        q_table[name] = {"normal": 5, "anomaly": 2}

    action = "increase" if not anomaly else "decrease"
    reward = 1 if not anomaly else -2

    old_value = q_table[name][state]
    new_value = old_value + learning_rate * (reward + discount * max(q_table[name].values()) - old_value)
    q_table[name][state] = new_value

    if name not in sync_intervals:
        sync_intervals[name] = 5
    if action == "increase":
        sync_intervals[name] = min(MAX_INTERVAL, sync_intervals[name] + 1)
    else:
        sync_intervals[name] = max(1, sync_intervals[name] - 1)

    return sync_intervals[name]

def handle_node(conn, addr):
    name = None
    while True:
        try:
            data = conn.recv(1024).decode()
            if not data:
                break

            name, reported_time, received_lamport, timezone_name = data.split(":")
            reported_time = float(reported_time)
            received_lamport = int(received_lamport)
            controller_time = time.time()

            if name not in trust_scores:
                trust_scores[name] = 100
            if name not in node_states:
                node_states[name] = {"lamport": 0, "timezone": timezone_name}

            node_states[name]["lamport"] = max(node_states[name]["lamport"], received_lamport) + 1
            node_states[name]["timezone"] = timezone_name

            anomaly = abs(reported_time - controller_time) > 5
            if anomaly:
                trust_scores[name] -= 10
                print(f"⚠ Anomaly from {name}")
            else:
                trust_scores[name] += 5

            trust_scores[name] = max(0, min(100, trust_scores[name]))
            interval = q_learn(name, anomaly)

            with open("sync_log.txt", "a", encoding="utf-8") as f:
                local_time = datetime.fromtimestamp(reported_time, pytz.timezone(timezone_name))
                f.write(f"[{time.ctime()}] SYSTEM TIME {local_time} from {name} ({timezone_name})\n")
                if anomaly:
                    f.write(f"[{time.ctime()}] ⚠ Anomaly from {name}\n")
                else:
                    f.write(f"[{time.ctime()}] ✅ Normal time from {name}\n")
                f.write(f"[{time.ctime()}] Trust Score {trust_scores[name]} | Sync Interval {interval}\n")
                f.write(f"[{time.ctime()}] Lamport Clock {node_states[name]['lamport']}\n")

            if trust_scores[name] > 50:
                conn.sendall(f"SYNC:{controller_time}:{interval}".encode())
                with open("sync_log.txt", "a", encoding="utf-8") as f:
                    f.write(f"[{time.ctime()}] SYNC → {name} to {datetime.fromtimestamp(controller_time)} (Interval {interval}s)\n")
            else:
                conn.sendall(f"IGNORE:{interval}".encode())
                with open("sync_log.txt", "a", encoding="utf-8") as f:
                    f.write(f"[{time.ctime()}] ❌ IGNORE → {name} (Interval {interval}s, Trust: {trust_scores[name]})\n")

            with open("q_table.json", "w", encoding="utf-8") as f:
                json.dump(q_table, f)

        except Exception as e:
            print(f"[{addr}] Connection error: {e}")
            break

def controller():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"🧠 Controller listening on {HOST}:{PORT} ...")

        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_node, args=(conn, addr)).start()

if __name__ == "__main__":
    controller()
