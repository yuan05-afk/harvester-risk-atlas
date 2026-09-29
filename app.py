"""Harvester Risk Atlas — EthnoHACK 2026 Track 3."""

import streamlit as st

from hra.ui import main

st.set_page_config(
    page_title="Harvester Risk Atlas",
    layout="wide",
    initial_sidebar_state="expanded",
)

main()
