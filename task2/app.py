import os
import json
import redis
import streamlit as st
from streamlit_autorefresh import st_autorefresh

def main():
    st.title("Serverless VM Monitoring Dashboard")

    st_autorefresh(interval=5000, limit=None, key="refresh")

    redis_host = os.getenv("REDIS_HOST", "127.0.0.1")
    redis_port = os.getenv("REDIS_PORT", "6379")
    redis_output_key = os.getenv("REDIS_OUTPUT_KEY", "my-proj3-output")

    st.write(f"Connecting to Redis at {redis_host}:{redis_port}")
    st.write(f"Reading key: {redis_output_key}")

    r = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)

    data_json = r.get(redis_output_key)
    st.write("---")
    if data_json:
        try:
            data_dict = json.loads(data_json)
        except json.JSONDecodeError:
            st.error("Invalid JSON in Redis key.")
            return

        st.subheader("Serverless Function Metrics")
        st.json(data_dict)

        network_egress = data_dict.get("percent-network-egress")
        if network_egress is not None:
            st.metric("Network Egress (%)", f"{network_egress:.2f}")

        mem_cache = data_dict.get("percent-memory-cache")
        if mem_cache is not None:
            st.metric("Memory Cache (%)", f"{mem_cache:.2f}")

        cpu_keys = [k for k in data_dict.keys() if k.startswith("avg-util-cpu")]
        if cpu_keys:
            for ck in sorted(cpu_keys):
                st.write(f"{ck}: {data_dict[ck]:.2f} %")
    else:
        st.warning("No data found in Redis yet. Waiting for serverless function output...")

if __name__ == "__main__":
    main()
