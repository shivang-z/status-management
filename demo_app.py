# app.py
# Streamlit POC:
# - Simple login (multiple usernames + one shared password)
# - Load Excel (POC for SQL table)
# - Show Product/UserName/RejectedReason (read-only)
# - Edit Status (dropdown) + Comments (text)
# - Validation: Status required; Comments required only when Status == "Not Required"
# - Submit writes back to Excel + offers download

import datetime as dt
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

# ----------------------------
# CONFIG (EDIT THESE)
# ----------------------------
APP_TITLE = "Status Updater"

ALLOWED_USERS = ["alice", "bob", "charlie"]  # add/remove usernames here
SINGLE_PASSWORD = "ChangeMe123!"            # shared password

DATA_PATH = Path("poc_data.xlsx")

REQUIRED_COLS = ["Product", "UserName", "RejectedReason", "Status", "Comments"]
STATUS_OPTIONS = ["", "Completed", "Not Completed", "Not Required"]


# ----------------------------
# HELPERS
# ----------------------------
def rerun() -> None:
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()


def ensure_data_file_exists() -> None:
    """Create a sample Excel file if none exists."""
    if DATA_PATH.exists():
        return

    sample = pd.DataFrame(
        {
            "Product": ["Prod A", "Prod B", "Prod C"],
            "UserName": ["user1", "user2", "user3"],
            "RejectedReason": ["Missing info", "Wrong format", "Out of scope"],
            "Status": ["", "", ""],
            "Comments": ["", "", ""],
        }
    )
    sample.to_excel(DATA_PATH, index=False)


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure required columns exist, order them, and remove NaNs."""
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]

    for c in REQUIRED_COLS:
        if c not in df.columns:
            df[c] = ""

    df = df[REQUIRED_COLS]
    for c in REQUIRED_COLS:
        df[c] = df[c].fillna("").astype(str)

    return df


def load_data_from_disk() -> pd.DataFrame:
    ensure_data_file_exists()
    df = pd.read_excel(DATA_PATH, engine="openpyxl")
    return normalize_columns(df)


def save_data_to_disk(df: pd.DataFrame) -> None:
    normalize_columns(df).to_excel(DATA_PATH, index=False)


def df_to_excel_bytes(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Data")
    return output.getvalue()


def validate_rows(df: pd.DataFrame) -> list[str]:
    """
    Rules:
    - Status required for every row
    - Comments required only when Status == 'Not Required'
    """
    errors: list[str] = []

    status = df["Status"].fillna("").astype(str).str.strip()
    comments = df["Comments"].fillna("").astype(str).str.strip()

    # Missing status
    missing_status_mask = status.eq("")
    if missing_status_mask.any():
        lines = []
        for idx in df.index[missing_status_mask]:
            lines.append(
                f"- Row {idx + 1}: Product={df.at[idx, 'Product']}, UserName={df.at[idx, 'UserName']}"
            )
        errors.append("Status is missing for these rows:\n" + "\n".join(lines))

    # Comments required when Not Required
    missing_comments_mask = status.eq("Not Required") & comments.eq("")
    if missing_comments_mask.any():
        lines = []
        for idx in df.index[missing_comments_mask]:
            lines.append(
                f"- Row {idx + 1}: Product={df.at[idx, 'Product']}, UserName={df.at[idx, 'UserName']}"
            )
        errors.append(
            "Comments are required when Status is 'Not Required' for these rows:\n"
            + "\n".join(lines)
        )

    return errors


# ----------------------------
# AUTH UI
# ----------------------------
def login_page() -> None:
    st.title(APP_TITLE)
    st.subheader("Login")

    with st.form("login_form"):
        username = st.selectbox("Username", options=ALLOWED_USERS)
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in")

    if submitted:
        if username in ALLOWED_USERS and password.strip() == SINGLE_PASSWORD:
            st.session_state["authenticated"] = True
            st.session_state["user"] = username
            rerun()
        else:
            st.error("Invalid username or password.")


# ----------------------------
# MAIN UI
# ----------------------------
def main_page() -> None:
    st.title(APP_TITLE)

    c1, c2 = st.columns([0.7, 0.3])
    with c1:
        st.caption(f"Logged in as **{st.session_state.get('user', '')}**")
    with c2:
        if st.button("Logout"):
            st.session_state.clear()
            rerun()

    st.divider()

    # Optional upload to replace Excel
    with st.expander("Load / Replace Excel file (optional)", expanded=False):
        st.write(
            "Upload an Excel file with at least: `Product`, `UserName`, `RejectedReason`.\n\n"
            "The app will add `Status` and `Comments` columns if missing, and save it as `poc_data.xlsx`."
        )
        uploaded = st.file_uploader("Upload .xlsx", type=["xlsx"])
        if uploaded is not None:
            df_up = pd.read_excel(uploaded, engine="openpyxl")
            df_up = normalize_columns(df_up)
            save_data_to_disk(df_up)
            st.session_state["df"] = df_up
            st.success("Excel loaded and saved as poc_data.xlsx")
            rerun()

    if "df" not in st.session_state:
        st.session_state["df"] = load_data_from_disk()

    df = st.session_state["df"].copy()

    st.subheader("Update Status and Comments")
    st.caption("Status is required for all rows. Comments are required only when Status = 'Not Required'.")

    # Header row
    header = st.columns([2.0, 1.6, 2.2, 1.6, 2.6])
    header[0].markdown("**Product**")
    header[1].markdown("**UserName**")
    header[2].markdown("**RejectedReason**")
    header[3].markdown("**Status**")
    header[4].markdown("**Comments**")

    updated_rows = []

    for i, row in df.iterrows():
        cols = st.columns([2.0, 1.6, 2.2, 1.6, 2.6])

        cols[0].write(row["Product"])
        cols[1].write(row["UserName"])
        cols[2].write(row["RejectedReason"])

        status_key = f"status_{i}"
        comment_key = f"comment_{i}"

        # Initialize session state once
        if status_key not in st.session_state:
            st.session_state[status_key] = row["Status"].strip()
        if comment_key not in st.session_state:
            st.session_state[comment_key] = row["Comments"]

        # Status dropdown
        current_status = st.session_state[status_key]
        status_index = STATUS_OPTIONS.index(current_status) if current_status in STATUS_OPTIONS else 0

        status_val = cols[3].selectbox(
            "Status",
            options=STATUS_OPTIONS,
            index=status_index,
            key=status_key,
            label_visibility="collapsed",
        )

        # Comments input (required only if Not Required)
        comment_help = "Required when Status = Not Required" if status_val == "Not Required" else "Optional"

        comment_val = cols[4].text_input(
            "Comments",
            value=st.session_state[comment_key],
            key=comment_key,
            help=comment_help,
            label_visibility="collapsed",
        )

        updated_rows.append(
            {
                "Product": row["Product"],
                "UserName": row["UserName"],
                "RejectedReason": row["RejectedReason"],
                "Status": status_val,
                "Comments": comment_val,
            }
        )

    updated_df = normalize_columns(pd.DataFrame(updated_rows))

    st.divider()

    left, right = st.columns([0.25, 0.75])
    submit = left.button("Submit", type="primary")
    right.caption(f"Excel file on disk: `{DATA_PATH.resolve()}`")

    if submit:
        errors = validate_rows(updated_df)
        if errors:
            st.error("Fix the following before submitting:")
            for e in errors:
                st.write(e)
            return

        save_data_to_disk(updated_df)
        st.session_state["df"] = updated_df
        st.success("Saved! Excel file updated.")

        xlsx_bytes = df_to_excel_bytes(updated_df)
        ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        st.download_button(
            "Download updated Excel",
            data=xlsx_bytes,
            file_name=f"updated_data_{ts}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, layout="wide")

    if not st.session_state.get("authenticated", False):
        login_page()
    else:
        main_page()


if __name__ == "__main__":
    main()