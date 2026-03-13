import os
import streamlit as st
from pathlib import Path

class AppConfig:
    def __init__(self):
        self.app_title = "Work Status Management"

        # Users
        self.allowed_users = [
            "abhishek_mishra",
            "raja_parella",
            "anjali_shrikrishna_wadhokar",
            "kashinath_balasaheb_chougule",
            "parvez_shamim_idrisi",
            "adarsh_pandey",
            "prashanth_mallesh_seepathi",
            "dhanalaxmi_nagesh_pittla",
            "rupali_mohan_gaikwad",
            "madhav_balaji_bhale",
            "pratik_pratap_wagh"
        ]
        self.admin_user = "admin"

        # Passwords
        # self.user_password = "ChangeMe123!"   # shared password for regular users
        # self.admin_password = "Admin@123!"    # separate admin password
        self.user_password = st.secrets.get("USER_PASSWORD", os.getenv("USER_PASSWORD", ""))
        self.admin_password = st.secrets.get("ADMIN_PASSWORD", os.getenv("ADMIN_PASSWORD", ""))

        # CSV
        # self.data_path = Path("poc_data_1.csv")
        self.data_path = Path(os.getenv("DATA_PATH", "poc_data_1.csv"))

        # WorkStatus dropdown options
        self.status_options = ["", "Completed", "Not Completed", "Not Required"]

        # UI settings
        self.error_preview_chars = 80

        # Column used for ownership filtering
        self.owner_column = "CASEDISPOSEDBYNAME"