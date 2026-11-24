import streamlit as st

from pages.SENTINEL_Dataset_Manager_Addon.sentinel.dataset_manager import render_dataset_manager

st.set_page_config(
    page_title="Dataset Manager | SENTINEL",
    page_icon="🛡️",
    layout="wide",
)

render_dataset_manager()
