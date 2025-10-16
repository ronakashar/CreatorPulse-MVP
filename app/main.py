import os
from pathlib import Path

import streamlit as st
from utils.ui import inject_global_css

# Initialize monitoring
try:
    from services.monitoring import monitoring, security_validator
    monitoring.track_event("app_startup", {"version": "1.0.0"})
except Exception as e:
    st.warning(f"Monitoring initialization failed: {e}")

# Local imports
from services.supabase_client import (
    get_client,
    get_current_user,
    sign_in_with_password,
    sign_up_with_password,
    sign_out,
    get_user_workspaces,
    create_workspace,
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
    if "current_workspace" not in st.session_state:
        st.session_state["current_workspace"] = None


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
                # Validate inputs
                if not security_validator.validate_email(email):
                    st.error("Please enter a valid email address.")
                    return
                
                if len(password) < 8:
                    st.error("Password must be at least 8 characters long.")
                    return
                
                if not name or len(name.strip()) < 2:
                    st.error("Please enter a valid name.")
                    return
                
                # Sanitize inputs
                email = security_validator.sanitize_input(email, max_length=255)
                name = security_validator.sanitize_input(name, max_length=100)
                timezone = security_validator.sanitize_input(timezone, max_length=50)
                
                sign_up_with_password(email=email, password=password, name=name, timezone=timezone)
                st.success("Account created. Please log in.")
                st.rerun()
            except Exception as e:
                st.error(f"Signup failed: {e}")
                # Track error
                try:
                    monitoring.track_error(e, {"action": "signup", "email": email})
                except:
                    pass


def render_home():
    st.set_page_config(page_title="CreatorPulse", page_icon="📰", layout="wide")
    inject_global_css()
    require_env()
    ensure_session_keys()

    user = get_current_user()
    if not user:
        render_auth()
        return

    # Workspace selection
    workspaces = get_user_workspaces(user_id=user["id"])
    
    st.sidebar.success(f"Logged in as {user.get('email')}")
    
    # Workspace selector
    if workspaces:
        workspace_options = {f"{w['workspaces']['name']} ({w['role']})": w for w in workspaces}
        selected_workspace_name = st.sidebar.selectbox(
            "Select Workspace",
            options=list(workspace_options.keys()),
            index=0
        )
        st.session_state["current_workspace"] = workspace_options[selected_workspace_name]
    else:
        st.sidebar.info("No workspaces yet")
        if st.sidebar.button("Create First Workspace"):
            st.session_state["show_create_workspace"] = True
    
    # Create workspace form
    if st.session_state.get("show_create_workspace", False):
        st.sidebar.markdown("---")
        st.sidebar.markdown("### Create Workspace")
        with st.sidebar.form("quick_create_workspace"):
            name = st.text_input("Name", placeholder="My Workspace")
            slug = st.text_input("Slug", placeholder="my-workspace")
            submitted = st.form_submit_button("Create")
        
        if submitted and name and slug:
            try:
                create_workspace(name=name, slug=slug, owner_id=user["id"])
                st.sidebar.success("Workspace created!")
                st.session_state["show_create_workspace"] = False
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"Failed: {e}")
    
    if st.sidebar.button("Logout"):
        sign_out()
        st.rerun()

    st.title("CreatorPulse")
    st.caption("Your AI-powered daily feed curator and newsletter generator.")
    
    if workspaces:
        current_workspace = st.session_state.get("current_workspace")
        if current_workspace:
            st.info(f"🏢 Working in: **{current_workspace['workspaces']['name']}** ({current_workspace['role']})")
    
    st.write("Use the sidebar to navigate pages: Dashboard, Sources, Style Upload, Settings, Workspaces, Billing, Agency Dashboard, Analytics.")
    st.page_link("pages/1_Dashboard.py", label="Go to Dashboard →")


if __name__ == "__main__":
    render_home()


