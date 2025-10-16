import streamlit as st
from utils.ui import inject_global_css, header
from services.supabase_client import get_current_user, get_email_analytics


def auth_guard():
    user = get_current_user()
    if not user:
        st.error("Please login from the main page.")
        st.stop()
    return user


def render():
    st.set_page_config(page_title="Analytics — CreatorPulse", page_icon="📊", layout="wide")
    inject_global_css()
    user = auth_guard()
    
    header("Analytics", "Email opens, clicks, and engagement metrics")
    
    days = st.selectbox("Time period", [7, 30, 90], index=1)
    analytics = get_email_analytics(user_id=user["id"], days=days)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Emails Sent", analytics["sent"])
    with col2:
        st.metric("Opens", analytics["opens"], f"{analytics['open_rate']:.1%} rate")
    with col3:
        st.metric("Clicks", analytics["clicks"], f"{analytics['ctr']:.1%} CTR")
    with col4:
        st.metric("Avg CTR", f"{analytics['ctr']:.1%}")
    
    st.divider()
    
    if analytics["clicks_by_url"]:
        st.subheader("Top Clicked Links")
        for url, count in sorted(analytics["clicks_by_url"].items(), key=lambda x: x[1], reverse=True)[:10]:
            st.write(f"**{count} clicks:** [{url}]({url})")
    else:
        st.info("No clicks recorded yet. Send some emails to see analytics.")


if __name__ == "__main__":
    render()
