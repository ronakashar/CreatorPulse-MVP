import streamlit as st
from utils.ui import inject_global_css, header, section_header
from services.supabase_client import (
    get_current_user,
    get_user_workspace_role,
    get_client_profiles,
    create_client_profile,
    update_client_profile,
    delete_client_profile,
    get_client_workspaces,
    create_client_workspace,
    get_bulk_operations,
    get_workspace_analytics,
    get_user_workspaces,
    create_workspace,
)
from services.bulk_operations import (
    run_bulk_fetch,
    run_bulk_generate,
    run_bulk_send,
)


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
    
    # Only allow owners and admins to access agency dashboard
    if user_role not in ["owner", "admin"]:
        st.error("❌ Agency Dashboard is only available for workspace owners and admins.")
        st.stop()
    
    return user, current_workspace, user_role


def render():
    st.set_page_config(page_title="Agency Dashboard — CreatorPulse", page_icon="🏢", layout="wide")
    inject_global_css()
    user, current_workspace, user_role = auth_guard()

    workspace_name = current_workspace["workspaces"]["name"]
    workspace_id = current_workspace["workspace_id"]
    
    header("Agency Dashboard", f"Manage multiple clients and bulk operations. Workspace: {workspace_name} ({user_role})")

    # Check if user has Agency plan
    from services.supabase_client import get_user_subscription
    subscription = get_user_subscription(user_id=user["id"])
    plan_id = subscription.get("plan_id", "free") if subscription else "free"
    
    if plan_id != "agency":
        st.warning("🚀 **Agency Dashboard** is available with the Agency plan ($99/month). Upgrade to access multi-client management and bulk operations.")
        if st.button("Upgrade to Agency Plan"):
            st.page_link("pages/7_Billing.py", label="Go to Billing →")
        return

    # Tabs for different agency functions
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "👥 Client Management", "⚡ Bulk Operations", "📈 Analytics"])

    with tab1:
        section_header("Agency Overview")
        
        # Get analytics for current workspace
        analytics = get_workspace_analytics(workspace_id=workspace_id, days=30)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Newsletters Sent (30d)", int(analytics["newsletters_sent"]))
        with col2:
            st.metric("Active Sources", analytics["sources_count"])
        with col3:
            st.metric("Team Members", analytics["members_count"])
        with col4:
            st.metric("Drafts Created (30d)", analytics["drafts_count"])
        
        st.divider()
        
        # Recent bulk operations
        section_header("Recent Bulk Operations")
        bulk_ops = get_bulk_operations(workspace_id=workspace_id, limit=5)
        
        if bulk_ops:
            for op in bulk_ops:
                status_emoji = {
                    "pending": "⏳",
                    "running": "🔄",
                    "completed": "✅",
                    "failed": "❌"
                }.get(op["status"], "❓")
                
                st.write(f"{status_emoji} **{op['operation_type'].replace('_', ' ').title()}** - {op['status'].title()}")
                st.caption(f"Created by {op.get('users', {}).get('name', 'Unknown')} • {op['created_at'][:16]}")
        else:
            st.info("No bulk operations yet. Create some in the Bulk Operations tab.")

    with tab2:
        section_header("Client Management")
        
        # Create new client
        with st.expander("➕ Add New Client"):
            with st.form("add_client_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    client_name = st.text_input("Client Name", placeholder="Acme Corp")
                    client_email = st.text_input("Client Email", placeholder="contact@acme.com")
                    client_website = st.text_input("Client Website", placeholder="https://acme.com")
                
                with col2:
                    industry = st.text_input("Industry", placeholder="Technology")
                    contact_person = st.text_input("Contact Person", placeholder="John Doe")
                    notes = st.text_area("Notes", placeholder="Client preferences, special requirements...")
                
                submitted = st.form_submit_button("Add Client")
                
                if submitted and client_name:
                    try:
                        client = create_client_profile(
                            workspace_id=workspace_id,
                            client_name=client_name,
                            client_email=client_email,
                            client_website=client_website,
                            industry=industry,
                            contact_person=contact_person,
                            notes=notes
                        )
                        st.success(f"✅ Client '{client_name}' added successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Failed to add client: {e}")
        
        # List existing clients
        clients = get_client_profiles(workspace_id=workspace_id)
        
        if clients:
            st.markdown("### Client List")
            for client in clients:
                with st.expander(f"🏢 {client['client_name']}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**Email:** {client.get('client_email', 'Not provided')}")
                        st.write(f"**Website:** {client.get('client_website', 'Not provided')}")
                        st.write(f"**Industry:** {client.get('industry', 'Not specified')}")
                        st.write(f"**Contact:** {client.get('contact_person', 'Not specified')}")
                        if client.get('notes'):
                            st.write(f"**Notes:** {client['notes']}")
                    
                    with col2:
                        if st.button("Edit", key=f"edit_{client['id']}"):
                            st.session_state[f"edit_client_{client['id']}"] = True
                        
                        if st.button("Delete", key=f"delete_{client['id']}"):
                            try:
                                delete_client_profile(client_id=client["id"])
                                st.success("Client deleted")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to delete: {e}")
                    
                    # Edit form
                    if st.session_state.get(f"edit_client_{client['id']}", False):
                        st.markdown("---")
                        with st.form(f"edit_form_{client['id']}"):
                            new_name = st.text_input("Client Name", value=client["client_name"])
                            new_email = st.text_input("Client Email", value=client.get("client_email", ""))
                            new_website = st.text_input("Client Website", value=client.get("client_website", ""))
                            new_industry = st.text_input("Industry", value=client.get("industry", ""))
                            new_contact = st.text_input("Contact Person", value=client.get("contact_person", ""))
                            new_notes = st.text_area("Notes", value=client.get("notes", ""))
                            
                            if st.form_submit_button("Update Client"):
                                try:
                                    update_client_profile(
                                        client_id=client["id"],
                                        client_name=new_name,
                                        client_email=new_email,
                                        client_website=new_website,
                                        industry=new_industry,
                                        contact_person=new_contact,
                                        notes=new_notes
                                    )
                                    st.success("Client updated!")
                                    st.session_state[f"edit_client_{client['id']}"] = False
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed to update: {e}")
        else:
            st.info("No clients yet. Add your first client above.")

    with tab3:
        section_header("Bulk Operations")
        
        # Get all workspaces for bulk operations
        all_workspaces = get_user_workspaces(user_id=user["id"])
        workspace_options = {f"{w['workspaces']['name']} ({w['role']})": w["workspace_id"] for w in all_workspaces}
        
        if not workspace_options:
            st.info("No workspaces available for bulk operations.")
            return
        
        # Bulk operations
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### 📥 Bulk Fetch Sources")
            st.caption("Fetch content from all sources across selected workspaces")
            
            selected_workspaces_fetch = st.multiselect(
                "Select workspaces",
                options=list(workspace_options.keys()),
                key="bulk_fetch_workspaces"
            )
            
            if st.button("🚀 Run Bulk Fetch", key="bulk_fetch"):
                if selected_workspaces_fetch:
                    target_workspaces = [workspace_options[w] for w in selected_workspaces_fetch]
                    try:
                        with st.spinner("Running bulk fetch..."):
                            result = run_bulk_fetch(
                                workspace_id=workspace_id,
                                target_workspaces=target_workspaces,
                                created_by=user["id"]
                            )
                        st.success(f"✅ Bulk fetch completed! {result['progress']['completed']} workspaces processed.")
                    except Exception as e:
                        st.error(f"❌ Bulk fetch failed: {e}")
                else:
                    st.warning("Please select at least one workspace.")
        
        with col2:
            st.markdown("#### ✍️ Bulk Generate Drafts")
            st.caption("Generate newsletter drafts for selected workspaces")
            
            selected_workspaces_generate = st.multiselect(
                "Select workspaces",
                options=list(workspace_options.keys()),
                key="bulk_generate_workspaces"
            )
            
            temp = st.slider("Creativity", 0.0, 1.0, 0.7, key="bulk_temp")
            links = st.slider("Number of links", 3, 10, 5, key="bulk_links")
            
            if st.button("🚀 Run Bulk Generate", key="bulk_generate"):
                if selected_workspaces_generate:
                    target_workspaces = [workspace_options[w] for w in selected_workspaces_generate]
                    try:
                        with st.spinner("Running bulk generate..."):
                            result = run_bulk_generate(
                                workspace_id=workspace_id,
                                target_workspaces=target_workspaces,
                                created_by=user["id"],
                                temperature=temp,
                                num_links=links
                            )
                        st.success(f"✅ Bulk generate completed! {result['progress']['completed']} workspaces processed.")
                    except Exception as e:
                        st.error(f"❌ Bulk generate failed: {e}")
                else:
                    st.warning("Please select at least one workspace.")
        
        with col3:
            st.markdown("#### 📧 Bulk Send Newsletters")
            st.caption("Send newsletter drafts to all selected workspaces")
            
            selected_workspaces_send = st.multiselect(
                "Select workspaces",
                options=list(workspace_options.keys()),
                key="bulk_send_workspaces"
            )
            
            if st.button("🚀 Run Bulk Send", key="bulk_send"):
                if selected_workspaces_send:
                    target_workspaces = [workspace_options[w] for w in selected_workspaces_send]
                    try:
                        with st.spinner("Running bulk send..."):
                            result = run_bulk_send(
                                workspace_id=workspace_id,
                                target_workspaces=target_workspaces,
                                created_by=user["id"]
                            )
                        st.success(f"✅ Bulk send completed! {result['progress']['completed']} newsletters sent.")
                    except Exception as e:
                        st.error(f"❌ Bulk send failed: {e}")
                else:
                    st.warning("Please select at least one workspace.")
        
        st.divider()
        
        # Recent bulk operations
        section_header("Operation History")
        bulk_ops = get_bulk_operations(workspace_id=workspace_id, limit=10)
        
        if bulk_ops:
            for op in bulk_ops:
                status_emoji = {
                    "pending": "⏳",
                    "running": "🔄",
                    "completed": "✅",
                    "failed": "❌"
                }.get(op["status"], "❓")
                
                with st.expander(f"{status_emoji} {op['operation_type'].replace('_', ' ').title()} - {op['status'].title()}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Created:** {op['created_at'][:16]}")
                        st.write(f"**Created by:** {op.get('users', {}).get('name', 'Unknown')}")
                        st.write(f"**Target workspaces:** {len(op['target_workspaces'])}")
                    
                    with col2:
                        if op.get('progress'):
                            progress = op['progress']
                            st.write(f"**Progress:** {progress.get('completed', 0)}/{progress.get('total', 0)} completed")
                            if progress.get('failed', 0) > 0:
                                st.write(f"**Failed:** {progress['failed']}")
                    
                    if op.get('error_message'):
                        st.error(f"Error: {op['error_message']}")
                    
                    if op.get('results'):
                        st.json(op['results'])
        else:
            st.info("No bulk operations yet.")

    with tab4:
        section_header("Analytics Dashboard")
        
        # Workspace comparison
        st.markdown("### Workspace Comparison")
        
        workspace_analytics = []
        for workspace_data in all_workspaces:
            ws_id = workspace_data["workspace_id"]
            ws_name = workspace_data["workspaces"]["name"]
            analytics = get_workspace_analytics(workspace_id=ws_id, days=30)
            workspace_analytics.append({
                "name": ws_name,
                "newsletters": analytics["newsletters_sent"],
                "sources": analytics["sources_count"],
                "members": analytics["members_count"],
                "drafts": analytics["drafts_count"]
            })
        
        if workspace_analytics:
            import pandas as pd
            df = pd.DataFrame(workspace_analytics)
            st.dataframe(df, use_container_width=True)
            
            # Charts
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Newsletters Sent (30 days)")
                st.bar_chart(df.set_index("name")["newsletters"])
            
            with col2:
                st.markdown("#### Active Sources")
                st.bar_chart(df.set_index("name")["sources"])
        else:
            st.info("No workspace data available yet.")


if __name__ == "__main__":
    render()
