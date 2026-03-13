import streamlit as st

from auth import AuthService
from config import AppConfig
from data_store import CSVDataStore
from ui import AppUI


def main() -> None:
    cfg = AppConfig()
    st.set_page_config(page_title=cfg.app_title, layout="wide", initial_sidebar_state="collapsed")

    auth = AuthService(cfg)
    store = CSVDataStore(cfg)
    ui = AppUI(cfg, auth, store)

    if not auth.is_authenticated():
        ui.render_login_page()
    else:
        ui.render_main_page()


if __name__ == "__main__":
    main()