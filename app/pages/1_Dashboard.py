import streamlit as st
from utils.ui import inject_global_css, header
from services.supabase_client import list_recent_content, list_drafts

from services.supabase_client import get_current_user


def auth_guard():
    user = get_current_user()
    if not user:
        st.error("Please login from the main page.")
        st.stop()
    return user


def render():
    st.set_page_config(page_title="Dashboard — CreatorPulse", page_icon="📊", layout="wide")
    inject_global_css()
    user = auth_guard()

    header("Dashboard", "Generate your curated newsletter draft and send via email.")

    with st.sidebar:
        st.markdown("#### Generate options")
        temperature = st.slider("Creativity", min_value=0.0, max_value=1.0, value=0.7, step=0.05)
        num_links = st.slider("Number of links", min_value=3, max_value=10, value=5)
        st.divider()
        theme = st.radio("Theme", ["Dark", "Light"], index=0)
        accent = st.selectbox("Accent color", ["Purple", "Blue", "Green"], index=0)
        st.caption("Theme options apply on next reload.")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("1) Fetch and select content")
        st.caption("Manually fetch, then select which items to include in the draft")
        if st.button("Fetch content now"):
            from services.content_fetcher import fetch_all_sources
            try:
                num_items = fetch_all_sources(user_id=user["id"]) or 0
                st.success(f"Fetched and saved {num_items} items.")
            except Exception as e:
                st.error(f"Fetch failed: {e}")

        items = list_recent_content(user_id=user["id"], limit=50)
        st.write(f"Found {len(items)} items")
        metric = st.radio("Pick top by", ["Recency", "Title length", "Random"], horizontal=True)
        if metric == "Title length":
            items = sorted(items, key=lambda x: len(x.get("title", "")), reverse=True)
        elif metric == "Random":
            import random
            random.shuffle(items)
        selected_ids = st.multiselect(
            "Select items to include",
            options=[it["id"] for it in items],
            format_func=lambda i: next((f"{x['title']}" for x in items if x['id'] == i), str(i)),
        )

    with col2:
        st.subheader("2) Generate draft")
        st.caption("Use your style samples and selected content")
        if st.button("Generate newsletter draft"):
            from services.newsletter_generator import generate_and_save_draft
            try:
                draft_text = generate_and_save_draft(user_id=user["id"], selected_item_ids=selected_ids, temperature=temperature, num_links=num_links)
                if draft_text:
                    st.success("Draft generated.")
                else:
                    st.warning("No draft generated. Add sources and style samples.")
            except Exception as e:
                st.error(f"Generation failed: {e}")

    st.divider()
    st.subheader("Latest draft")
    from services.supabase_client import get_latest_draft, save_draft_feedback
    draft = get_latest_draft(user_id=user["id"]) or {}
    draft_text = draft.get("draft_text")
    if draft_text:
        edited = st.text_area("Edit draft before sending", value=draft_text, height=420)
        cols = st.columns(3)
        with cols[0]:
            if st.button("👍 Helpful"):
                save_draft_feedback(user["id"], edited, feedback="up")
                st.toast("Feedback saved")
        with cols[1]:
            if st.button("👎 Not great"):
                save_draft_feedback(user["id"], edited, feedback="down")
                st.toast("Feedback saved")
        with cols[2]:
            if st.button("Send via email"):
                from utils.formatting import markdown_to_html
                from services.resend_client import send_email
                html = markdown_to_html(edited)
                try:
                    send_email(to_email=user.get("email"), subject="Your CreatorPulse Draft", html_content=html)
                    from services.supabase_client import mark_latest_draft_sent
                    mark_latest_draft_sent(user_id=user["id"]) 
                    st.success("Email sent.")
                except Exception as e:
                    st.error(f"Send failed: {e}")
    else:
        st.info("No draft yet. Fetch content and generate a draft.")

    st.divider()
    st.subheader("Past drafts")
    q = st.text_input("Search drafts")
    drafts = list_drafts(user_id=user["id"], limit=20, search=q or "")
    for d in drafts:
        with st.expander(f"{d['created_at']} — {'✅ sent' if d.get('sent') else '📝 draft'}"):
            st.markdown(d.get("draft_text", ""))
            if st.button("Resend this draft", key=f"resend_{d['id']}"):
                from utils.formatting import markdown_to_html
                from services.resend_client import send_email
                html = markdown_to_html(d.get("draft_text", ""))
                try:
                    send_email(to_email=user.get("email"), subject="Your CreatorPulse Draft", html_content=html)
                    st.success("Email sent.")
                except Exception as e:
                    st.error(f"Send failed: {e}")

if __name__ == "__main__":
    render()


