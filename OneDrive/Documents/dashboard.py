import streamlit as st
import time

st.set_page_config(page_title="Time Sync Dashboard", layout="wide")
st.title("Time Synchronization Dashboard")

st.markdown("""
This dashboard displays real-time logs of communication between devices in a distributed system.

You will see:
- The latest system events such as time synchronization, anomalies, or ignored messages.
""")

def read_log():
    try:
        with open("sync_log.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()
        return lines[-100:]
    except:
        return []

placeholder = st.empty()

while True:
    with placeholder.container():
        st.subheader("1. Latest System Events")
        logs = read_log()
        if logs:
            for log in logs[-10:]:
                if "⚠" in log:
                    st.error(log.strip())
                elif "❌" in log:
                    st.warning(log.strip())
                elif "✅" in log:
                    st.success(log.strip())
                else:
                    st.write(log.strip())
        else:
            st.write("No events yet. Waiting for nodes to communicate...")

    time.sleep(3)
