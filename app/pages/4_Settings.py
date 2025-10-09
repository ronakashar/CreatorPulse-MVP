import streamlit as st
from utils.ui import inject_global_css, header

from services.supabase_client import get_current_user, get_user_profile, update_user_profile


def auth_guard():
    user = get_current_user()
    if not user:
        st.error("Please login from the main page.")
        st.stop()
    return user


def render():
    st.set_page_config(page_title="Settings — CreatorPulse", page_icon="⚙️", layout="wide")
    inject_global_css()
    user = auth_guard()
    header("Settings", "Update your name, email (display), and timezone.")

    profile = get_user_profile(user_id=user["id"]) or {}
    with st.form("settings_form"):
        name = st.text_input("Name", value=profile.get("name", ""))
        email = st.text_input("Email", value=profile.get("email", ""))
        timezone = st.text_input("Timezone", value=profile.get("timezone", ""))
        submitted = st.form_submit_button("Save")
    if submitted:
        try:
            update_user_profile(user_id=user["id"], name=name, email=email, timezone=timezone)
            st.success("Saved.")
        except Exception as e:
            st.error(f"Save failed: {e}")


if __name__ == "__main__":
    render()


