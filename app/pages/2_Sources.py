import streamlit as st
from utils.ui import inject_global_css, header

from services.supabase_client import (
    get_current_user,
    list_sources,
    add_source,
    remove_source,
    update_source_boost,
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
        boost_factor = st.slider("Boost factor", min_value=0.1, max_value=3.0, value=1.0, step=0.1, 
                                help="Higher values make content from this source more likely to appear in newsletters")
        submitted = st.form_submit_button("Add source")
    if submitted and source_value:
        try:
            add_source(user_id=user["id"], source_type=source_type, source_value=source_value, boost_factor=boost_factor)
            st.success("Source added.")
            st.rerun()
        except Exception as e:
            st.error(f"Add failed: {e}")

    st.subheader("Your sources")
    sources = list_sources(user_id=user["id"]) or []
    if not sources:
        st.info("No sources added yet. Add some Twitter handles, YouTube channels, or RSS feeds to get started!")
    else:
        for s in sources:
            cols = st.columns([2, 1, 1, 1])
            
            # Source info
            cols[0].write(f"🔗 **{s['source_type'].title()}**: {s['source_value']}")
            
            # Boost factor
            current_boost = float(s.get('boost_factor', 1.0))
            cols[1].write(f"⚡ Boost: {current_boost}x")
            
            # Boost control
            new_boost = cols[2].slider("Adjust", min_value=0.1, max_value=3.0, value=current_boost, 
                                       step=0.1, key=f"boost_{s['id']}")
            if new_boost != current_boost:
                try:
                    update_source_boost(source_id=s["id"], boost_factor=new_boost)
                    st.success(f"Updated boost to {new_boost}x")
                    st.rerun()
                except Exception as e:
                    st.error(f"Update failed: {e}")
            
            # Remove button
            if cols[3].button("🗑️ Remove", key=f"rm_{s['id']}"):
                try:
                    remove_source(s["id"]) 
                    st.success("Removed.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Remove failed: {e}")


if __name__ == "__main__":
    render()


