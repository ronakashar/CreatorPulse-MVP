import streamlit as st
from utils.ui import inject_global_css, header

from services.supabase_client import (
    get_current_user,
    list_sources,
    add_source,
    remove_source,
)


def auth_guard():
    user = get_current_user()
    if not user:
        st.error("Please login from the main page.")
        st.stop()
    return user


def render():
    st.set_page_config(page_title="Sources — CreatorPulse", page_icon="🔗", layout="wide")
    inject_global_css()
    user = auth_guard()
    header("Sources", "Manage your Twitter handles, YouTube channels, and RSS feeds")

    with st.form("add_source_form"):
        source_type = st.selectbox("Source type", ["twitter", "youtube", "rss"])
        source_value = st.text_input("Handle / Channel URL / Feed URL")
        submitted = st.form_submit_button("Add source")
    if submitted and source_value:
        try:
            add_source(user_id=user["id"], source_type=source_type, source_value=source_value)
            st.success("Source added.")
        except Exception as e:
            st.error(f"Add failed: {e}")

    st.subheader("Your sources")
    sources = list_sources(user_id=user["id"]) or []
    for s in sources:
        cols = st.columns([3, 1])
        cols[0].write(f"{s['source_type']}: {s['source_value']}")
        if cols[1].button("Remove", key=f"rm_{s['id']}"):
            try:
                remove_source(s["id"]) 
                st.success("Removed.")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Remove failed: {e}")


if __name__ == "__main__":
    render()


