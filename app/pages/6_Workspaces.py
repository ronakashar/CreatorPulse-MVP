import streamlit as st
from utils.ui import inject_global_css, header, section_header
import re

from services.supabase_client import (
    get_current_user,
    create_workspace,
    get_user_workspaces,
    get_workspace_members,
    invite_user_to_workspace,
    update_workspace_member_role,
    remove_workspace_member,
    get_user_workspace_role,
    get_user_plan_limits,
    check_usage_limit,
)


def auth_guard():
    user = get_current_user()
    if not user:
        st.error("Please login from the main page.")
        st.stop()
    return user


def _slugify(text: str) -> str:
    """Convert text to URL-friendly slug"""
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')


def render():
    st.set_page_config(page_title="Workspaces — CreatorPulse", page_icon="🏢", layout="wide")
    inject_global_css()
    user = auth_guard()
    header("Workspaces", "Create and manage team workspaces for collaborative newsletter creation")

    # Get user's workspaces
    workspaces = get_user_workspaces(user_id=user["id"])
    
    # Create new workspace section
    section_header("Create New Workspace")
    with st.form("create_workspace_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            workspace_name = st.text_input("Workspace Name", placeholder="My Agency", help="Name of your workspace")
            workspace_slug = st.text_input("Workspace Slug", placeholder="my-agency", help="URL-friendly identifier")
        
        with col2:
            workspace_description = st.text_area("Description", placeholder="Brief description of this workspace", height=100)
        
        # Auto-generate slug from name
        if workspace_name and not workspace_slug:
            workspace_slug = _slugify(workspace_name)
            st.info(f"Auto-generated slug: {workspace_slug}")
        
        create_submitted = st.form_submit_button("🏢 Create Workspace")
    
    if create_submitted and workspace_name and workspace_slug:
        try:
            # Check workspace limit
            limits = get_user_plan_limits(user_id=user["id"])
            current_workspaces = len(get_user_workspaces(user_id=user["id"]))
            max_workspaces = limits.get("max_workspaces", 1)
            
            if current_workspaces >= max_workspaces:
                st.error(f"❌ You've reached your workspace limit ({max_workspaces}). Upgrade your plan to create more workspaces.")
                return
            
            workspace = create_workspace(
                name=workspace_name,
                slug=workspace_slug,
                description=workspace_description,
                owner_id=user["id"]
            )
            st.success(f"✅ Workspace '{workspace_name}' created successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Failed to create workspace: {e}")

    st.divider()
    
    # Display existing workspaces
    section_header("Your Workspaces")
    if not workspaces:
        st.info("No workspaces yet. Create your first workspace to get started!")
    else:
        for workspace_data in workspaces:
            workspace = workspace_data["workspaces"]
            role = workspace_data["role"]
            
            with st.expander(f"🏢 {workspace['name']} ({role.title()})"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Description:** {workspace.get('description', 'No description')}")
                    st.write(f"**Slug:** `{workspace['slug']}`")
                    st.write(f"**Created:** {workspace['created_at'][:10]}")
                
                with col2:
                    if role in ["owner", "admin"]:
                        if st.button("👥 Manage Members", key=f"manage_{workspace['slug']}"):
                            st.session_state[f"manage_workspace_{workspace['slug']}"] = True
                    
                    if st.button("📊 View Analytics", key=f"analytics_{workspace['slug']}"):
                        st.info("Analytics coming soon!")
                
                # Member management section
                if st.session_state.get(f"manage_workspace_{workspace['slug']}", False):
                    st.markdown("---")
                    st.markdown("#### 👥 Manage Members")
                    
                    # Get workspace members
                    members = get_workspace_members(workspace_id=workspace_data["workspace_id"])
                    
                    # Invite new member
                    with st.form(f"invite_form_{workspace['slug']}"):
                        col1, col2, col3 = st.columns([2, 1, 1])
                        
                        with col1:
                            invite_email = st.text_input("Email", placeholder="user@example.com", key=f"email_{workspace['slug']}")
                        with col2:
                            invite_role = st.selectbox("Role", ["viewer", "editor", "admin"], key=f"role_{workspace['slug']}")
                        with col3:
                            invite_submitted = st.form_submit_button("📧 Invite")
                    
                    if invite_submitted and invite_email:
                        try:
                            invite_user_to_workspace(
                                workspace_id=workspace_data["workspace_id"],
                                email=invite_email,
                                role=invite_role,
                                invited_by=user["id"]
                            )
                            st.success(f"✅ Invited {invite_email} as {invite_role}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Failed to invite user: {e}")
                    
                    # List existing members
                    st.markdown("**Current Members:**")
                    for member in members:
                        member_cols = st.columns([2, 1, 1, 1])
                        
                        with member_cols[0]:
                            user_info = member.get("users", {})
                            status = "✅ Joined" if member.get("joined_at") else "📧 Pending"
                            st.write(f"**{user_info.get('name', 'Unknown')}** ({user_info.get('email', 'No email')}) - {status}")
                        
                        with member_cols[1]:
                            st.write(f"Role: {member['role'].title()}")
                        
                        with member_cols[2]:
                            if role in ["owner", "admin"] and member["role"] != "owner":
                                new_role = st.selectbox(
                                    "Change role",
                                    ["viewer", "editor", "admin"],
                                    index=["viewer", "editor", "admin"].index(member["role"]),
                                    key=f"role_change_{member['id']}"
                                )
                                if new_role != member["role"]:
                                    try:
                                        update_workspace_member_role(member_id=member["id"], role=new_role)
                                        st.success(f"✅ Updated role to {new_role}")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Failed to update role: {e}")
                        
                        with member_cols[3]:
                            if role == "owner" and member["role"] != "owner":
                                if st.button("🗑️ Remove", key=f"remove_{member['id']}"):
                                    try:
                                        remove_workspace_member(member_id=member["id"])
                                        st.success("✅ Member removed")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Failed to remove member: {e}")


if __name__ == "__main__":
    render()

