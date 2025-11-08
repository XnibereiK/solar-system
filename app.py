import streamlit as st
import os
from datetime import datetime

st.set_page_config(page_title="Solar Dashboard", page_icon="☀️", layout="centered")

st.title("☀️ Solar")
st.caption("Deployed via Traefik + Cloudflare Tunnel")

st.write(
    "This is a minimal Streamlit app running behind Traefik on the shared 'edge' network.\n"
    "Traffic reaches this app via Cloudflare Tunnel → Traefik (HTTP :80) → container (:8501)."
)

col1, col2 = st.columns(2)
with col1:
    st.metric("Server Time", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"))
with col2:
    st.metric("Container Hostname", os.uname().nodename)

st.divider()

st.info(
    "If you can see this at https://solar.kierebinski.solutions, DNS and routing are working.")
