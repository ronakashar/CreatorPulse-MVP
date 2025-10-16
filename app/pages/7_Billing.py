import streamlit as st
from utils.ui import inject_global_css, header, section_header
from services.supabase_client import (
    get_current_user,
    get_user_subscription,
    get_subscription_plans,
    get_user_plan_limits,
    get_usage_for_period,
    create_user_subscription,
    get_user_workspaces,
    list_sources,
)
from services.stripe_client import (
    create_customer,
    create_checkout_session,
    create_portal_session,
    format_price,
    get_plan_features,
    get_plan_limits,
)


def auth_guard():
    user = get_current_user()
    if not user:
        st.error("Please login from the main page.")
        st.stop()
    return user


def render():
    st.set_page_config(page_title="Billing — CreatorPulse", page_icon="💳", layout="wide")
    inject_global_css()
    user = auth_guard()
    
    header("Billing & Subscription", "Manage your subscription plan and billing")

    # Get current subscription
    current_subscription = get_user_subscription(user_id=user["id"])
    current_plan_id = current_subscription.get("plan_id", "free") if current_subscription else "free"
    
    # Get all available plans
    plans = get_subscription_plans()
    
    # Display current plan
    section_header("Current Plan")
    if current_subscription:
        plan_data = current_subscription.get("subscription_plans", {})
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Plan", plan_data.get("name", "Free"))
        with col2:
            price = plan_data.get("price_monthly_cents", 0)
            st.metric("Price", format_price(price) + "/month" if price > 0 else "Free")
        with col3:
            status = current_subscription.get("status", "active")
            st.metric("Status", status.title())
        
        # Show billing period
        if current_subscription.get("current_period_end"):
            from datetime import datetime
            period_end = datetime.fromisoformat(current_subscription["current_period_end"].replace('Z', '+00:00'))
            st.info(f"📅 Next billing date: {period_end.strftime('%B %d, %Y')}")
        
        # Customer portal button
        if current_subscription.get("stripe_customer_id"):
            if st.button("🔧 Manage Billing"):
                try:
                    portal_session = create_portal_session(
                        customer_id=current_subscription["stripe_customer_id"],
                        return_url=st.get_option("browser.serverAddress") or "http://localhost:8501"
                    )
                    st.success("Redirecting to billing portal...")
                    st.markdown(f"[Open Billing Portal]({portal_session.url})")
                except Exception as e:
                    st.error(f"Failed to create portal session: {e}")
    else:
        st.info("You're currently on the Free plan")
    
    st.divider()
    
    # Usage overview
    section_header("Usage This Month")
    limits = get_user_plan_limits(user_id=user["id"])
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        newsletters_sent = get_usage_for_period(user_id=user["id"], metric_type="newsletter_sent", days=30)
        max_newsletters = limits.get("max_newsletters_per_month", 10)
        st.metric("Newsletters Sent", f"{newsletters_sent}/{max_newsletters}")
    
    with col2:
        workspaces_count = len(get_user_workspaces(user_id=user["id"]))
        max_workspaces = limits.get("max_workspaces", 1)
        st.metric("Workspaces", f"{workspaces_count}/{max_workspaces}")
    
    with col3:
        sources_count = len(list_sources(user_id=user["id"]))
        max_sources = limits.get("max_sources", 5)
        st.metric("Sources", f"{sources_count}/{max_sources}")
    
    with col4:
        api_calls = get_usage_for_period(user_id=user["id"], metric_type="api_call", days=30)
        st.metric("API Calls", api_calls)
    
    st.divider()
    
    # Available plans
    section_header("Available Plans")
    
    # Create columns for plan cards
    plan_cols = st.columns(len(plans))
    
    for i, plan in enumerate(plans):
        with plan_cols[i]:
            is_current_plan = plan["id"] == current_plan_id
            is_free_plan = plan["id"] == "free"
            
            # Plan card styling
            if is_current_plan:
                st.markdown("### ✅ " + plan["name"] + " (Current)")
            else:
                st.markdown("### " + plan["name"])
            
            # Price
            monthly_price = plan.get("price_monthly_cents", 0)
            yearly_price = plan.get("price_yearly_cents")
            
            if monthly_price == 0:
                st.markdown("**Free**")
            else:
                st.markdown(f"**{format_price(monthly_price)}/month**")
                if yearly_price:
                    savings = ((monthly_price * 12) - yearly_price) / (monthly_price * 12) * 100
                    st.markdown(f"*{format_price(yearly_price)}/year (Save {savings:.0f}%)*")
            
            # Features
            features = plan.get("features", {})
            limits_data = plan.get("limits", {})
            
            st.markdown("**Features:**")
            st.markdown(f"• {limits_data.get('max_workspaces', 1)} workspaces")
            st.markdown(f"• {limits_data.get('max_team_members', 1)} team members per workspace")
            st.markdown(f"• {limits_data.get('max_sources', 5)} content sources")
            st.markdown(f"• {limits_data.get('max_newsletters_per_month', 10)} newsletters/month")
            
            if features.get("analytics"):
                st.markdown("• 📊 Advanced analytics")
            if features.get("priority_support"):
                st.markdown("• 🚀 Priority support")
            if features.get("white_label"):
                st.markdown("• 🎨 White-label options")
            
            # Action buttons
            if is_current_plan:
                st.markdown("**✅ Current Plan**")
            elif is_free_plan:
                st.markdown("**📝 Default Plan**")
            else:
                # Subscribe button
                if st.button(f"Subscribe to {plan['name']}", key=f"subscribe_{plan['id']}"):
                    try:
                        # Create Stripe customer if not exists
                        customer_id = None
                        if current_subscription and current_subscription.get("stripe_customer_id"):
                            customer_id = current_subscription["stripe_customer_id"]
                        else:
                            customer = create_customer(email=user["email"], name=user.get("name", ""))
                            customer_id = customer.id
                        
                        # Create checkout session
                        checkout_session = create_checkout_session(
                            customer_id=customer_id,
                            price_id=plan.get("stripe_price_id_monthly", "price_test"),  # Use test price for now
                            success_url=f"{st.get_option('browser.serverAddress') or 'http://localhost:8501'}/billing?success=true",
                            cancel_url=f"{st.get_option('browser.serverAddress') or 'http://localhost:8501'}/billing?canceled=true"
                        )
                        
                        st.success("Redirecting to checkout...")
                        st.markdown(f"[Complete Payment]({checkout_session.url})")
                        
                    except Exception as e:
                        st.error(f"Failed to create checkout session: {e}")
    
    st.divider()
    
    # Billing history (placeholder)
    section_header("Billing History")
    st.info("Billing history will be available after Stripe integration is complete.")
    
    # Usage alerts
    section_header("Usage Alerts")
    
    # Check if approaching limits
    newsletters_usage = newsletters_sent / max_newsletters
    workspaces_usage = workspaces_count / max_workspaces
    sources_usage = sources_count / max_sources
    
    if newsletters_usage > 0.8:
        st.warning(f"⚠️ You've used {newsletters_usage:.0%} of your monthly newsletter limit")
    if workspaces_usage > 0.8:
        st.warning(f"⚠️ You've used {workspaces_usage:.0%} of your workspace limit")
    if sources_usage > 0.8:
        st.warning(f"⚠️ You've used {sources_usage:.0%} of your sources limit")
    
    if newsletters_usage < 0.5 and workspaces_usage < 0.5 and sources_usage < 0.5:
        st.success("✅ All usage within limits")


if __name__ == "__main__":
    render()
