import streamlit as st
from utils.ui import (
    inject_global_css, header, section_header, metric_card, 
    progress_bar, empty_state, success_card, warning_card, 
    info_card, loading_spinner, status_badge
)
from services.supabase_client import list_recent_content, list_drafts, get_current_user, get_user_workspace_role


def auth_guard():
    user = get_current_user()
    if not user:
        st.error("Please login from the main page.")
        st.stop()
    
    # Check workspace context
    current_workspace = st.session_state.get("current_workspace")
    if not current_workspace:
        st.error("Please select a workspace from the main page.")
        st.stop()
    
    # Check user role in workspace
    workspace_id = current_workspace["workspace_id"]
    user_role = get_user_workspace_role(user_id=user["id"], workspace_id=workspace_id)
    
    return user, current_workspace, user_role


def render():
    st.set_page_config(page_title="Dashboard — CreatorPulse", page_icon="📊", layout="wide")
    inject_global_css()
    user, current_workspace, user_role = auth_guard()

    workspace_name = current_workspace["workspaces"]["name"]
    workspace_id = current_workspace["workspace_id"]
    
    header("Dashboard", f"Generate your curated newsletter draft and send via email. Workspace: {workspace_name} ({user_role})")

    # Quick Stats Row
    items = list_recent_content(user_id=user["id"], workspace_id=workspace_id, limit=50)
    drafts = list_drafts(user_id=user["id"], limit=10)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card(str(len(items)), "Content Items", "📰")
    with col2:
        metric_card(str(len(drafts)), "Drafts Created", "📝")
    with col3:
        sent_drafts = len([d for d in drafts if d.get("sent_at")])
        metric_card(str(sent_drafts), "Newsletters Sent", "📧")
    with col4:
        metric_card(f"{len(items)/5:.1f}", "Avg Items/Day", "📊")

    st.divider()

    with st.sidebar:
        section_header("🎛️ Generate Options")
        temperature = st.slider("Creativity", min_value=0.0, max_value=1.0, value=0.7, step=0.05, help="Higher values = more creative content")
        num_links = st.slider("Number of links", min_value=3, max_value=10, value=5, help="How many curated links to include")
        num_trends = st.slider("Trends to include", min_value=0, max_value=5, value=3, help="Number of trending topics to feature")
        
        st.divider()
        section_header("📰 Newsletter Sections")
        include_intro = st.checkbox("Include Intro", value=True, help="Add a personalized introduction")
        include_links = st.checkbox("Include Curated Links", value=True, help="Include your selected content")
        include_trends = st.checkbox("Include Trends to Watch", value=True, help="Add trending topics section")
        
        st.divider()
        section_header("🎨 Appearance")
        theme = st.radio("Theme", ["Dark", "Light"], index=0)
        accent = st.selectbox("Accent color", ["Purple", "Blue", "Green"], index=0)
        st.caption("Theme options apply on next reload.")

    col1, col2 = st.columns([2, 1])
    with col1:
        section_header("📥 Fetch and Select Content", "Get fresh content from your sources")
        
        # Fetch button with better styling
        fetch_col1, fetch_col2 = st.columns([1, 3])
        with fetch_col1:
            if st.button("🔄 Fetch Content", type="primary", use_container_width=True):
                with st.spinner("Fetching content..."):
                    from services.content_fetcher import fetch_all_sources
                    try:
                        num_items = fetch_all_sources(user_id=user["id"], workspace_id=workspace_id) or 0
                        if num_items > 0:
                            success_card("Content Fetched!", f"Successfully fetched {num_items} new items from your sources.")
                        else:
                            warning_card("No New Content", "No new items found. Try again later or check your sources.")
                    except Exception as e:
                        error_card("Fetch Failed", f"Error: {e}")
        
        with fetch_col2:
            items = list_recent_content(user_id=user["id"], workspace_id=workspace_id, limit=50)
            if items:
                progress_bar(len(items), 50, f"Content Items Available")
            else:
                empty_state("📭", "No Content Yet", "Fetch content from your sources to get started", "Fetch Content")

        if items:
            st.markdown("**Sort by:**")
            metric = st.radio("Pick top by", ["Recency", "Title length", "Random"], horizontal=True, label_visibility="collapsed")
            
            # Sort items based on selected metric
            if metric == "Title length":
                items = sorted(items, key=lambda x: len(x.get("title", "")), reverse=True)
            elif metric == "Random":
                import random
                random.shuffle(items)
            else:  # Recency
                items = sorted(items, key=lambda x: x.get("created_at", ""), reverse=True)
            
            selected_ids = st.multiselect(
                "Select items to include",
                options=[it["id"] for it in items],
                format_func=lambda i: next((f"{x['title'][:50]}... - {x['url'][:30]}..." for x in items if x['id'] == i), str(i)),
            )
        else:
            selected_ids = []

    with col2:
        st.subheader("2) Generate draft")
        st.caption("Use your style samples and selected content")
        if st.button("Generate newsletter draft"):
            from services.newsletter_generator import generate_and_save_draft
            try:
                draft_text = generate_and_save_draft(
                    user_id=user["id"], 
                    selected_item_ids=selected_ids, 
                    temperature=temperature, 
                    num_links=num_links, 
                    num_trends=num_trends,
                    include_intro=include_intro,
                    include_links=include_links,
                    include_trends=include_trends
                )
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
                from utils.formatting import markdown_to_html, inject_tracking
                from services.resend_client import send_email
                from services.supabase_client import get_latest_draft
                latest = get_latest_draft(user_id=user["id"]) or {}
                html = markdown_to_html(edited)
                html = inject_tracking(html, user_id=user.get("id"), draft_id=latest.get("id"), api_url="https://npedokgktkcbeltkaovz.supabase.co/functions/v1")
                try:
                    send_email(to_email=user.get("email"), subject="Your CreatorPulse Draft", html_content=html)
                    from services.supabase_client import mark_latest_draft_sent, track_usage
                    mark_latest_draft_sent(user_id=user["id"])
                    
                    # Track usage
                    track_usage(
                        user_id=user["id"],
                        workspace_id=workspace_id,
                        metric_type="newsletter_sent",
                        metric_value=1.0
                    )
                    
                    # Track analytics
                    try:
                        from services.analytics_service import track_email_sent
                        track_email_sent(
                            user_id=user["id"],
                            workspace_id=workspace_id,
                            recipient_count=1
                        )
                    except Exception:
                        pass  # Analytics tracking is optional
                    
                    st.success("Email sent.")
                except Exception as e:
                    st.error(f"Send failed: {e}")
        if st.button("Save edited draft"):
            from utils.formatting import unified_diff
            from services.supabase_client import save_draft_edit, get_latest_draft
            latest = get_latest_draft(user_id=user["id"]) or {}
            diff_text = unified_diff(draft_text, edited)
            try:
                save_draft_edit(user_id=user["id"], original_draft_id=latest.get("id"), original_text=draft_text, edited_text=edited, diff_text=diff_text)
                st.success("Edited draft saved.")
            except Exception as e:
                st.error(f"Save failed: {e}")
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


