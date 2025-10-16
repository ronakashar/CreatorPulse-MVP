import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils.ui import inject_global_css, header, section_header
from services.supabase_client import (
    get_current_user,
    get_user_workspace_role,
    get_analytics_events,
    get_analytics_reports,
    get_analytics_dashboards,
    create_analytics_dashboard,
    update_analytics_dashboard,
    delete_analytics_dashboard,
    get_cost_trends,
    get_usage_trends,
    get_workspace_analytics,
)
from services.analytics_service import (
    AnalyticsReporter,
    AnalyticsTracker,
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
    
    # Only allow owners and admins to access analytics
    if user_role not in ["owner", "admin"]:
        st.error("❌ Analytics Dashboard is only available for workspace owners and admins.")
        st.stop()
    
    return user, current_workspace, user_role


def render():
    st.set_page_config(page_title="Analytics Dashboard — CreatorPulse", page_icon="📊", layout="wide")
    inject_global_css()
    user, current_workspace, user_role = auth_guard()

    workspace_name = current_workspace["workspaces"]["name"]
    workspace_id = current_workspace["workspace_id"]
    
    header("Analytics Dashboard", f"Advanced usage analytics and insights. Workspace: {workspace_name} ({user_role})")

    # Check if user has Pro or Agency plan
    from services.supabase_client import get_user_subscription
    subscription = get_user_subscription(user_id=user["id"])
    plan_id = subscription.get("plan_id", "free") if subscription else "free"
    
    if plan_id not in ["pro", "agency"]:
        st.warning("🚀 **Advanced Analytics** is available with Pro ($19/month) or Agency ($99/month) plans. Upgrade to access detailed usage analytics and reporting.")
        if st.button("Upgrade Plan"):
            st.page_link("pages/7_Billing.py", label="Go to Billing →")
        return

    # Time period selector
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        days = st.selectbox("Time Period", [7, 30, 90], index=1)
    with col2:
        refresh = st.button("🔄 Refresh Data")
    with col3:
        st.caption(f"Showing data for the last {days} days")

    # Initialize analytics services
    reporter = AnalyticsReporter()
    tracker = AnalyticsTracker()

    # Track page visit
    tracker.track_user_action(
        user_id=user["id"],
        workspace_id=workspace_id,
        action="page_visit",
        page="analytics_dashboard"
    )

    # Tabs for different analytics views
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview", "💰 Costs", "📈 Usage Trends", "📋 Reports", "⚙️ Settings"])

    with tab1:
        section_header("Analytics Overview")
        
        # Get usage summary
        usage_summary = reporter.get_usage_summary(workspace_id=workspace_id, days=days)
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Cost", f"${usage_summary['total_cost_dollars']:.2f}")
        with col2:
            st.metric("API Calls", usage_summary['api_calls']['total'])
        with col3:
            st.metric("Emails Sent", usage_summary['emails']['sent'])
        with col4:
            st.metric("Draft Generations", usage_summary['content']['draft_generations'])
        
        st.divider()
        
        # Cost breakdown pie chart
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Cost Breakdown")
            cost_data = reporter.get_cost_breakdown(workspace_id=workspace_id, days=days)
            
            if cost_data['by_category']:
                fig_pie = px.pie(
                    values=list(cost_data['by_category'].values()),
                    names=list(cost_data['by_category'].keys()),
                    title="Costs by Category"
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No cost data available for this period.")
        
        with col2:
            st.markdown("#### API Usage by Provider")
            api_providers = usage_summary['api_calls']['by_provider']
            
            if api_providers:
                fig_bar = px.bar(
                    x=list(api_providers.keys()),
                    y=list(api_providers.values()),
                    title="API Calls by Provider"
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("No API usage data available for this period.")
        
        # Recent events
        section_header("Recent Events")
        recent_events = get_analytics_events(workspace_id=workspace_id, days=days, limit=20)
        
        if recent_events:
            events_df = pd.DataFrame(recent_events)
            events_df['created_at'] = pd.to_datetime(events_df['created_at'])
            events_df['date'] = events_df['created_at'].dt.strftime('%Y-%m-%d %H:%M')
            
            # Display recent events
            for _, event in events_df.iterrows():
                event_emoji = {
                    'api_call': '🔌',
                    'storage_upload': '📁',
                    'email_sent': '📧',
                    'source_fetch': '📥',
                    'draft_generate': '✍️',
                    'user_action': '👤'
                }.get(event['event_type'], '❓')
                
                st.write(f"{event_emoji} **{event['event_name']}** - {event['date']}")
                if event.get('cost_cents', 0) > 0:
                    st.caption(f"Cost: ${event['cost_cents']/100:.2f}")
        else:
            st.info("No recent events found.")

    with tab2:
        section_header("Cost Analysis")
        
        # Cost trends over time
        cost_trends = get_cost_trends(workspace_id=workspace_id, days=days)
        
        if cost_trends:
            cost_df = pd.DataFrame(cost_trends)
            cost_df['date'] = pd.to_datetime(cost_df['date'])
            
            fig_line = px.line(
                cost_df,
                x='date',
                y='cost_dollars',
                title=f"Daily Costs (Last {days} Days)",
                labels={'cost_dollars': 'Cost ($)', 'date': 'Date'}
            )
            st.plotly_chart(fig_line, use_container_width=True)
            
            # Cost summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Cost", f"${cost_df['cost_dollars'].sum():.2f}")
            with col2:
                st.metric("Average Daily", f"${cost_df['cost_dollars'].mean():.2f}")
            with col3:
                st.metric("Peak Day", f"${cost_df['cost_dollars'].max():.2f}")
        else:
            st.info("No cost data available for this period.")
        
        # Detailed cost breakdown
        cost_breakdown = reporter.get_cost_breakdown(workspace_id=workspace_id, days=days)
        
        if cost_breakdown['by_event_type']:
            st.markdown("#### Cost by Event Type")
            cost_df = pd.DataFrame([
                {"Event Type": event_type, "Cost ($)": cost_cents / 100}
                for event_type, cost_cents in cost_breakdown['by_event_type'].items()
            ])
            st.dataframe(cost_df, use_container_width=True)

    with tab3:
        section_header("Usage Trends")
        
        # Event type selector
        event_types = ['api_call', 'email_sent', 'source_fetch', 'draft_generate', 'storage_upload']
        selected_event_type = st.selectbox("Select Event Type", event_types)
        
        # Get usage trends
        usage_trends = get_usage_trends(workspace_id=workspace_id, event_type=selected_event_type, days=days)
        
        if usage_trends:
            trends_df = pd.DataFrame(usage_trends)
            trends_df['date'] = pd.to_datetime(trends_df['date'])
            
            fig_area = px.area(
                trends_df,
                x='date',
                y='count',
                title=f"{selected_event_type.replace('_', ' ').title()} Trends",
                labels={'count': 'Count', 'date': 'Date'}
            )
            st.plotly_chart(fig_area, use_container_width=True)
            
            # Usage summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Events", trends_df['count'].sum())
            with col2:
                st.metric("Average Daily", f"{trends_df['count'].mean():.1f}")
            with col3:
                st.metric("Peak Day", trends_df['count'].max())
        else:
            st.info(f"No {selected_event_type} data available for this period.")

    with tab4:
        section_header("Analytics Reports")
        
        # Generate new report
        with st.expander("📊 Generate New Report"):
            col1, col2 = st.columns(2)
            
            with col1:
                report_type = st.selectbox("Report Type", ["usage", "cost", "performance", "engagement"])
                period_start = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))
            
            with col2:
                period_end = st.date_input("End Date", value=datetime.now())
                
                if st.button("Generate Report"):
                    try:
                        start_dt = datetime.combine(period_start, datetime.min.time())
                        end_dt = datetime.combine(period_end, datetime.max.time())
                        
                        report = reporter.generate_report(
                            workspace_id=workspace_id,
                            report_type=report_type,
                            period_start=start_dt,
                            period_end=end_dt,
                            generated_by=user["id"]
                        )
                        
                        st.success(f"✅ {report_type.title()} report generated successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Failed to generate report: {e}")
        
        # List existing reports
        reports = get_analytics_reports(workspace_id=workspace_id, limit=20)
        
        if reports:
            st.markdown("### Recent Reports")
            for report in reports:
                with st.expander(f"📋 {report['report_type'].title()} Report - {report['generated_at'][:10]}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**Period:** {report['period_start'][:10]} to {report['period_end'][:10]}")
                        st.write(f"**Generated by:** {report.get('users', {}).get('name', 'Unknown')}")
                        st.write(f"**Generated at:** {report['generated_at'][:16]}")
                    
                    with col2:
                        if st.button("View Data", key=f"view_{report['id']}"):
                            st.json(report['data'])
        else:
            st.info("No reports generated yet.")

    with tab5:
        section_header("Analytics Settings")
        
        # Dashboard management
        st.markdown("### Custom Dashboards")
        
        dashboards = get_analytics_dashboards(workspace_id=workspace_id)
        
        if dashboards:
            for dashboard in dashboards:
                with st.expander(f"📊 {dashboard['dashboard_name']}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**Created by:** {dashboard.get('users', {}).get('name', 'Unknown')}")
                        st.write(f"**Created:** {dashboard['created_at'][:16]}")
                        if dashboard.get('is_default'):
                            st.write("**Default Dashboard**")
                    
                    with col2:
                        if st.button("Edit", key=f"edit_dash_{dashboard['id']}"):
                            st.session_state[f"edit_dashboard_{dashboard['id']}"] = True
                        
                        if st.button("Delete", key=f"delete_dash_{dashboard['id']}"):
                            try:
                                delete_analytics_dashboard(dashboard_id=dashboard["id"])
                                st.success("Dashboard deleted")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to delete: {e}")
                    
                    # Edit form
                    if st.session_state.get(f"edit_dashboard_{dashboard['id']}", False):
                        st.markdown("---")
                        with st.form(f"edit_dashboard_form_{dashboard['id']}"):
                            new_name = st.text_input("Dashboard Name", value=dashboard["dashboard_name"])
                            
                            if st.form_submit_button("Update Dashboard"):
                                try:
                                    update_analytics_dashboard(
                                        dashboard_id=dashboard["id"],
                                        dashboard_name=new_name
                                    )
                                    st.success("Dashboard updated!")
                                    st.session_state[f"edit_dashboard_{dashboard['id']}"] = False
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed to update: {e}")
        else:
            st.info("No custom dashboards created yet.")
        
        # Create new dashboard
        with st.expander("➕ Create New Dashboard"):
            with st.form("create_dashboard_form"):
                dashboard_name = st.text_input("Dashboard Name", placeholder="My Custom Dashboard")
                is_default = st.checkbox("Set as Default Dashboard")
                
                if st.form_submit_button("Create Dashboard"):
                    if dashboard_name:
                        try:
                            dashboard = create_analytics_dashboard(
                                workspace_id=workspace_id,
                                dashboard_name=dashboard_name,
                                dashboard_config={},
                                created_by=user["id"],
                                is_default=is_default
                            )
                            st.success(f"✅ Dashboard '{dashboard_name}' created successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Failed to create dashboard: {e}")
                    else:
                        st.warning("Please enter a dashboard name.")


if __name__ == "__main__":
    render()
