"""Streamlit landing page linking to the web atlas."""
import streamlit as st

NEW_URL = "https://harvester-risk-atlas.vercel.app"

st.set_page_config(page_title="Harvester Risk Atlas", page_icon="🌿")
st.title("Harvester Risk Atlas")
st.write(
    "The atlas ranks wild medicinal plants of the Philippines, "
    "shows how sure each rank is, and works on phones."
)
st.link_button("Open the atlas", NEW_URL, type="primary")
st.caption(f"{NEW_URL} · source: https://github.com/yuan05-afk/harvester-risk-atlas")
