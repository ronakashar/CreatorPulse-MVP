import os
from pathlib import Path

import streamlit as st
from utils.ui import inject_global_css

# Local imports
from services.supabase_client import (
    get_client,
    get_current_user,
    sign_in_with_password,
    sign_up_with_password,
    sign_out,
)


def require_env():
    missing = []
    for key in [
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "GROQ_API_KEY",
        "RESEND_API_KEY",
    ]:
        if not os.getenv(key):
            missing.append(key)
    if missing:
        st.warning(
            "Missing environment variables: " + ", ".join(missing) + 
            ". Create an app/.env (or set system env) and restart."
        )


def ensure_session_keys():
    if "auth_view" not in st.session_state:
        st.session_state["auth_view"] = "login"


def render_auth():
    st.title("CreatorPulse — Login / Signup")
    tabs = st.tabs(["Login", "Signup"])

    with tabs[0]:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
        if submitted:
            try:
                sign_in_with_password(email=email, password=password)
                st.success("Logged in.")
                st.rerun()
            except Exception as e:
                st.error(f"Login failed: {e}")

    with tabs[1]:
        with st.form("signup_form"):
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password", type="password", key="signup_pw")
            name = st.text_input("Name")
            timezone = st.text_input("Timezone (e.g. UTC, PST)")
            submitted = st.form_submit_button("Create account")
        if submitted:
            try:
                sign_up_with_password(email=email, password=password, name=name, timezone=timezone)
                st.success("Account created. Please log in.")
                st.rerun()
            except Exception as e:
                st.error(f"Signup failed: {e}")


def render_home():
    st.set_page_config(page_title="CreatorPulse", page_icon="📰", layout="wide")
    inject_global_css()
    require_env()
    ensure_session_keys()

    user = get_current_user()
    if not user:
        render_auth()
        return

    st.sidebar.success(f"Logged in as {user.get('email')}")
    if st.sidebar.button("Logout"):
        sign_out()
        st.rerun()

    st.title("CreatorPulse")
    st.caption("Your AI-powered daily feed curator and newsletter generator.")
    st.write("Use the sidebar to navigate pages: Dashboard, Sources, Style Upload, Settings.")
    st.page_link("pages/1_Dashboard.py", label="Go to Dashboard →")


if __name__ == "__main__":
    render_home()


