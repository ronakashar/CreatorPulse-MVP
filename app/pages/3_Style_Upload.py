import io
import streamlit as st
from utils.ui import inject_global_css, header

from services.supabase_client import get_current_user, upload_style_file, list_style_files, delete_style_file


def auth_guard():
    user = get_current_user()
    if not user:
        st.error("Please login from the main page.")
        st.stop()
    return user


def render():
    st.set_page_config(page_title="Style Upload — CreatorPulse", page_icon="📝", layout="wide")
    inject_global_css()
    user = auth_guard()
    header("Style Upload", "Upload .txt or .csv of past newsletters. Used to match your writing style.")

    uploaded = st.file_uploader("Upload style samples (.txt or .csv)", type=["txt", "csv"], accept_multiple_files=True)
    if uploaded:
        for f in uploaded:
            data = f.read()
            try:
                upload_style_file(user_id=user["id"], filename=f.name, data=data)
                st.success(f"Uploaded {f.name}")
            except Exception as e:
                st.error(f"Upload failed for {f.name}: {e}")

    st.subheader("Your style files")
    files = list_style_files(user_id=user["id"]) or []
    for obj in files:
        cols = st.columns([3, 1])
        cols[0].write(obj.get("name"))
        if cols[1].button("Delete", key=f"del_{obj.get('name')}"):
            try:
                delete_style_file(user_id=user["id"], filename=obj.get("name"))
                st.success("Deleted.")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Delete failed: {e}")


if __name__ == "__main__":
    render()


