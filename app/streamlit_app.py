"""The Streamlit prototype (v1) has moved. This page points old links to the new atlas."""
import streamlit as st

NEW_URL = "https://harvester-risk-atlas.vercel.app"

st.set_page_config(page_title="Harvester Risk Atlas has moved", page_icon="🌿")
st.title("The Harvester Risk Atlas has moved")
st.write(
    "This was the first prototype. The new atlas ranks wild medicinal plants of the Philippines "
    "with a revised method, shows how sure each rank is, and works on phones."
)
st.link_button("Open the new atlas", NEW_URL, type="primary")
st.caption(f"{NEW_URL} · source: https://github.com/yuan05-afk/harvester-risk-atlas")
