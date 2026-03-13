from __future__ import annotations

import datetime as dt
import pandas as pd
import streamlit as st

from zoneinfo import ZoneInfo
from auth import AuthService
from config import AppConfig
from data_store import CSVDataStore


def rerun() -> None:
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()


class AppUI:
    def __init__(self, cfg: AppConfig, auth: AuthService, store: CSVDataStore):
        self.cfg = cfg
        self.auth = auth
        self.store = store

    # ----------------------------
    # GLOBAL STYLING
    # ----------------------------
    def apply_theme(self) -> None:
        st.markdown(
            """
            <style>
            .stApp {
                background: radial-gradient(circle at 20% 0%, rgba(74,144,226,.18), transparent 45%),
                            radial-gradient(circle at 80% 20%, rgba(80,227,194,.16), transparent 40%),
                            linear-gradient(180deg, rgba(250,250,252,1) 0%, rgba(245,246,250,1) 100%);
            }

            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}

            html, body, [class*="css"]  {
                font-family: -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Inter,Helvetica,Arial,sans-serif;
            }

            .card {
                background: white;
                border-radius: 16px;
                padding: 18px 18px;
                box-shadow: 0 8px 24px rgba(16,24,40,0.08);
                border: 1px solid rgba(16,24,40,0.06);
            }

            .topbar {
                display:flex;
                justify-content:space-between;
                align-items:center;
                background: rgba(255,255,255,0.75);
                border: 1px solid rgba(16,24,40,0.08);
                backdrop-filter: blur(10px);
                -webkit-backdrop-filter: blur(10px);
                padding: 12px 16px;
                border-radius: 18px;
                box-shadow: 0 8px 24px rgba(16,24,40,0.06);
                margin-bottom: 12px;
            }

            .pill {
                display:inline-flex;
                align-items:center;
                gap:8px;
                padding: 6px 10px;
                border-radius: 999px;
                font-size: 12px;
                font-weight: 700;
                border: 1px solid rgba(16,24,40,0.10);
                background: rgba(148,163,184,0.18);
                color: #334155;
            }

            .muted {
                color: rgba(15, 23, 42, 0.7);
                font-size: 13px;
            }

            div.stButton > button {
                border-radius: 12px !important;
                padding: 10px 14px !important;
                font-weight: 800 !important;
            }

            .stTextInput input,
            .stSelectbox > div {
                border-radius: 12px !important;
            }

            code {
                background: rgba(15,23,42,0.06);
                padding: 2px 6px;
                border-radius: 8px;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

    # ----------------------------
    # HELPERS
    # ----------------------------
    def _truncate(self, text: str, n: int) -> str:
        s = (text or "")
        if len(s) <= n:
            return s
        return s[:n].rstrip() + "…"

    def _normalize_username(self, name: str) -> str:
        # robust: lower + trim + collapse multiple spaces + join with underscores
        return "_".join(str(name).strip().lower().split())

    # ----------------------------
    # LOGIN
    # ----------------------------
    def render_login_page(self) -> None:
        self.apply_theme()

        st.markdown(
            f"""
            <div style="max-width: 900px; margin: 0 auto; padding-top: 50px;">
                <div class="card">
                    <h2 style="margin:0;">✨ {self.cfg.app_title}</h2>
                    <p class="muted">Centralized review and WorkStatus updates from a single interface.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div style="max-width: 520px; margin: 30px auto;">', unsafe_allow_html=True)
        st.markdown('<div class="card">', unsafe_allow_html=True)

        st.markdown("### Sign in")

        # include admin in the dropdown
        login_users = list(self.cfg.allowed_users) + [self.cfg.admin_user]

        with st.form("login_form"):
            username = st.selectbox("Username", options=login_users)
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log in")

        if submitted:
            if self.auth.login(username, password):
                rerun()
            else:
                st.error("Invalid username or password.")

        st.markdown("</div></div>", unsafe_allow_html=True)

    # ----------------------------
    # MAIN
    # ----------------------------
    def render_main_page(self) -> None:
        self.apply_theme()

        user = self.auth.current_user()
        is_admin = self.auth.is_admin()
        owner_col = self.cfg.owner_column

        admin_badge = "<span class='pill' style='margin-left:8px;'>Admin</span>" if is_admin else ""
        st.markdown(
            f"""
            <div class="topbar">
                <div>
                    <div style="font-size:18px; font-weight:900;">{self.cfg.app_title}</div>
                    <div class="muted">Logged in as <b>{user}</b> {admin_badge}</div>
                </div>
                <div class="pill">Data Source: CSV (POC)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        top_left, top_right = st.columns([0.25, 0.75])
        with top_left:
            if st.button("Logout"):
                self.auth.logout()
                rerun()
        with top_right:
            st.markdown(
                f'<div class="muted">📄 File: <code>{self.store.path.resolve()}</code></div>',
                unsafe_allow_html=True,
            )

        # Always load full df (for saving later)
        df_full = self.store.load().fillna("")
        if "WorkStatus" not in df_full.columns:
            df_full["WorkStatus"] = ""
        if "Comments" not in df_full.columns:
            df_full["Comments"] = ""

        # Create user-scoped df for display/edit (unless admin)
        df_view = df_full.copy()
        if owner_col in df_view.columns and not is_admin:
            normalized_user = self._normalize_username(user)
            df_view["_normalized_owner"] = df_view[owner_col].apply(self._normalize_username)
            df_view = df_view[df_view["_normalized_owner"] == normalized_user].copy()
            df_view.drop(columns=["_normalized_owner"], inplace=True)

        # If user has no rows
        if df_view.empty:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("#### No assigned rows")
            st.markdown(
                f"<div class='muted'>No rows found where <code>{owner_col}</code> matches <b>{user}</b>.</div>",
                unsafe_allow_html=True,
            )
            st.markdown("</div>", unsafe_allow_html=True)
            return

        # ----------------------------
        # FILTERS (within user scope)
        # ----------------------------
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### Filters")

        c1, c2, c3, c4 = st.columns([0.26, 0.26, 0.30, 0.18])

        type_col = "TYPE" if "TYPE" in df_view.columns else None
        type_options = ["All"] + (sorted(df_view[type_col].astype(str).unique().tolist()) if type_col else [])
        status_options = ["All"] + [s for s in self.cfg.status_options if s != ""]

        type_filter = c1.selectbox("TYPE", type_options) if type_col else "All"
        ws_filter = c2.selectbox("WorkStatus", status_options)
        search_text = c3.text_input("Search (any column)", value="")
        only_open = c4.checkbox("Only missing WorkStatus", value=False)

        filtered = df_view.copy()

        if type_col and type_filter != "All":
            filtered = filtered[filtered[type_col].astype(str) == type_filter]

        if ws_filter != "All":
            filtered = filtered[filtered["WorkStatus"].astype(str).str.strip() == ws_filter]

        if only_open:
            filtered = filtered[filtered["WorkStatus"].astype(str).str.strip() == ""]

        if search_text.strip():
            s = search_text.strip().lower()
            mask = None
            for col in filtered.columns:
                col_mask = filtered[col].astype(str).str.lower().str.contains(s, na=False)
                mask = col_mask if mask is None else (mask | col_mask)
            filtered = filtered[mask] if mask is not None else filtered

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<br/>", unsafe_allow_html=True)

        # ----------------------------
        # TABLE VIEW (READ-ONLY) - ALL COLS
        # ----------------------------
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### Current data (read-only view)")
        st.markdown(
            '<div class="muted">This is the data as fetched from the source table (POC uses CSV).</div>',
            unsafe_allow_html=True,
        )

        display_df = filtered.copy()
        if "ERROR_DETAILS" in display_df.columns:
            display_df["ERROR_DETAILS"] = display_df["ERROR_DETAILS"].astype(str).apply(
                lambda x: self._truncate(x, self.cfg.error_preview_chars)
            )

        st.dataframe(display_df, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br/>", unsafe_allow_html=True)

        # ----------------------------
        # UPDATE PANEL (TABULAR)
        # ----------------------------
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### Update WorkStatus / Comments")
        st.markdown(
            '<div class="muted">WorkStatus is required for your rows. Comments are required only if WorkStatus is <b>Not Required</b>.</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            "<hr style='border:none;border-top:1px solid rgba(16,24,40,0.08); margin: 12px 0;'/>",
            unsafe_allow_html=True,
        )

        all_cols = list(filtered.columns)
        readonly_cols = [c for c in all_cols if c not in ("WorkStatus", "Comments")]

        widths = []
        for c in readonly_cols:
            widths.append(2.6 if c == "ERROR_DETAILS" else 1.2)
        widths += [1.4, 2.2]  # WorkStatus, Comments

        header = st.columns(widths)
        for j, c in enumerate(readonly_cols):
            header[j].markdown(f"**{c}**")
        header[len(readonly_cols)].markdown("**WorkStatus**")
        header[len(readonly_cols) + 1].markdown("**Comments**")

        updated_rows = []
        status_opts = list(self.cfg.status_options)

        filtered_with_idx = filtered.reset_index(drop=False)

        for _, row in filtered_with_idx.iterrows():
            original_index = int(row["index"])
            cols = st.columns(widths)

            # readonly values
            for j, c in enumerate(readonly_cols):
                if c == "ERROR_DETAILS" and "ERROR_DETAILS" in filtered.columns:
                    full_text = str(df_full.loc[original_index, "ERROR_DETAILS"]) if "ERROR_DETAILS" in df_full.columns else ""
                    preview = self._truncate(full_text, self.cfg.error_preview_chars)
                    cols[j].write(preview if preview else "—")
                    if full_text and len(full_text) > self.cfg.error_preview_chars:
                        with cols[j].expander("View full"):
                            st.write(full_text)
                else:
                    val = row.get(c, "")
                    cols[j].write(str(val) if str(val).strip() else "—")

            # editable
            ws_key = f"workstatus_{original_index}"
            cm_key = f"comments_{original_index}"

            if ws_key not in st.session_state:
                st.session_state[ws_key] = str(df_full.loc[original_index, "WorkStatus"]).strip()
            if cm_key not in st.session_state:
                st.session_state[cm_key] = str(df_full.loc[original_index, "Comments"])

            current_ws = st.session_state[ws_key]
            ws_index = status_opts.index(current_ws) if current_ws in status_opts else 0

            ws_val = cols[len(readonly_cols)].selectbox(
                "WorkStatus",
                options=status_opts,
                index=ws_index,
                key=ws_key,
                label_visibility="collapsed",
            )

            help_txt = "Required when WorkStatus = Not Required" if ws_val == "Not Required" else "Optional"
            cm_val = cols[len(readonly_cols) + 1].text_input(
                "Comments",
                value=st.session_state[cm_key],
                key=cm_key,
                help=help_txt,
                label_visibility="collapsed",
                placeholder="Add comment if needed...",
            )

            updated_rows.append(
                {"row_index": original_index, "WorkStatus": ws_val, "Comments": cm_val}
            )

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<br/>", unsafe_allow_html=True)

        # ----------------------------
        # SUBMIT + DOWNLOAD
        # ----------------------------
        submit_col, download_col = st.columns([0.25, 0.75])

        if submit_col.button("✅ Submit updates", type="primary"):

            from datetime import datetime

            rows_changed = 0

            for u in updated_rows:
                idx = u["row_index"]

                if idx in df_full.index:
                    old_status = str(df_full.loc[idx, "WorkStatus"]).strip()
                    new_status = str(u["WorkStatus"]).strip()

                    # Only update timestamp if WorkStatus changed
                    if old_status != new_status:
                        df_full.loc[idx, "LastUpdatedAt"] = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S")
                        rows_changed += 1

                    df_full.loc[idx, "WorkStatus"] = new_status
                    df_full.loc[idx, "Comments"] = u["Comments"]

            # Validate scope
            if not is_admin and owner_col in df_full.columns:
                normalized_user = self._normalize_username(user)
                df_full["_normalized_owner"] = df_full[owner_col].apply(self._normalize_username)
                user_scope_df = df_full[df_full["_normalized_owner"] == normalized_user].copy()
                df_full.drop(columns=["_normalized_owner"], inplace=True)

                errors = self.store.validate(user_scope_df)
                saved_rows_count = len(user_scope_df)
                saved_msg = f"✅ Saved {rows_changed} updated rows for you."
            else:
                errors = self.store.validate(df_full)
                saved_rows_count = len(df_full)
                saved_msg = f"✅ Saved {rows_changed} updated rows across all users."

            if errors:
                st.error("Please fix these before submitting:")
                for e in errors:
                    st.write(e)
                return

            self.store.save(df_full)

            st.session_state["df"] = df_full.copy()

            st.success(saved_msg)

            csv_bytes = self.store.to_csv_bytes(df_full)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            download_col.download_button(
                "⬇️ Download updated CSV",
                data=csv_bytes,
                file_name=f"updated_data_{ts}.csv",
                mime="text/csv",
            )