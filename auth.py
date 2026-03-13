import streamlit as st
from config import AppConfig


class AuthService:
    def __init__(self, cfg: AppConfig):
        self.cfg = cfg

    def is_authenticated(self) -> bool:
        return bool(st.session_state.get("authenticated", False))

    def login(self, username: str, password: str) -> bool:

        if not self.cfg.user_password or not self.cfg.admin_password:
            st.error("Missing secrets. Set USER_PASSWORD and ADMIN_PASSWORD in .streamlit/secrets.toml or environment variables.")
            return False
        # Admin login
        if username == self.cfg.admin_user:
            if password.strip() == self.cfg.admin_password:
                st.session_state["authenticated"] = True
                st.session_state["user"] = username
                st.session_state["is_admin"] = True
                return True
            return False

        # Regular user login
        if username in self.cfg.allowed_users:
            if password.strip() == self.cfg.user_password:
                st.session_state["authenticated"] = True
                st.session_state["user"] = username
                st.session_state["is_admin"] = False
                return True

        return False

    def logout(self) -> None:
        st.session_state.clear()

    @staticmethod
    def current_user() -> str:
        return str(st.session_state.get("user", ""))

    def is_admin(self) -> bool:
        return bool(st.session_state.get("is_admin", False))