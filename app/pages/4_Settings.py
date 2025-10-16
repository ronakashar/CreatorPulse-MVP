import streamlit as st
from utils.ui import inject_global_css, header, section_header
from datetime import datetime
import pytz

from services.supabase_client import get_current_user, get_user_profile, update_user_profile


def auth_guard():
    user = get_current_user()
    if not user:
        st.error("Please login from the main page.")
        st.stop()
    return user


def render():
    st.set_page_config(page_title="Settings — CreatorPulse", page_icon="⚙️", layout="wide")
    inject_global_css()
    user = auth_guard()
    header("Settings", "Manage your profile and newsletter delivery preferences")

    profile = get_user_profile(user_id=user["id"]) or {}
    
    # Ensure profile has default values to prevent None errors
    if not profile:
        profile = {
            "name": "",
            "email": user.get("email", ""),
            "timezone": "UTC",
            "frequency": "daily",
            "send_days": ["Mon", "Tue", "Wed", "Thu", "Fri"],
            "send_time_local": "08:00"
        }
    
    # Profile section
    section_header("Profile Information")
    with st.form("profile_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Name", value=profile.get("name", ""), help="Your display name")
        with col2:
            email = st.text_input("Email", value=profile.get("email", ""), help="Email address for receiving newsletters")
        
        # Safe timezone selection
        user_timezone = profile.get("timezone", "UTC")
        try:
            timezone_index = pytz.all_timezones.index(user_timezone)
        except ValueError:
            timezone_index = pytz.all_timezones.index("UTC")
        
        timezone = st.selectbox(
            "Timezone", 
            options=pytz.all_timezones,
            index=timezone_index,
            help="Used for scheduling newsletter delivery"
        )
        
        profile_submitted = st.form_submit_button("💾 Save Profile")
    
    if profile_submitted:
        try:
            update_user_profile(user_id=user["id"], name=name, email=email, timezone=timezone)
            st.success("✅ Profile saved successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Save failed: {e}")

    st.divider()
    
    # Delivery preferences section
    section_header("Newsletter Delivery Preferences")
    with st.form("delivery_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📅 Schedule**")
            frequency = st.selectbox(
                "Frequency", 
                ["daily", "weekly"], 
                index=0 if (profile.get("frequency") or "daily") == "daily" else 1,
                help="How often to receive newsletters"
            )
            
            days_default = profile.get("send_days") or ["Mon","Tue","Wed","Thu","Fri"]
            send_days = st.multiselect(
                "Days of week", 
                ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"], 
                default=days_default,
                help="Select which days to receive newsletters"
            )
        
        with col2:
            st.markdown("**⏰ Timing**")
            
            # Fix the strptime error by handling None values properly
            default_time_str = profile.get("send_time_local") or "08:00"
            try:
                default_time = datetime.strptime(default_time_str, "%H:%M").time()
            except (ValueError, TypeError):
                default_time = datetime.strptime("08:00", "%H:%M").time()
            
            send_time_local = st.time_input(
                "Send time (local)", 
                value=default_time,
                help="Time in your local timezone to send newsletters"
            )
            
            # Show next delivery preview
            if send_days and send_time_local:
                try:
                    user_tz = pytz.timezone(timezone)
                    now = datetime.now(user_tz)
                    next_delivery = _calculate_next_delivery(now, send_days, send_time_local, user_tz)
                    st.info(f"📬 Next delivery: {next_delivery.strftime('%A, %B %d at %I:%M %p')}")
                except:
                    st.info("📬 Next delivery will be calculated after saving")
        
        delivery_submitted = st.form_submit_button("📧 Save Delivery Preferences")
    
    if delivery_submitted:
        try:
            update_user_profile(
                user_id=user["id"], 
                send_time_local=send_time_local.strftime("%H:%M"), 
                send_days=send_days, 
                frequency=frequency
            )
            st.success("✅ Delivery preferences saved successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Save failed: {e}")


def _calculate_next_delivery(now, send_days, send_time, timezone):
    """Calculate the next delivery time based on preferences"""
    import datetime as dt
    
    # Map day names to numbers
    day_map = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}
    send_day_nums = [day_map[day] for day in send_days]
    
    # Find next occurrence
    for i in range(7):  # Check next 7 days
        check_date = now.date() + dt.timedelta(days=i)
        if check_date.weekday() in send_day_nums:
            delivery_datetime = dt.datetime.combine(check_date, send_time)
            delivery_datetime = timezone.localize(delivery_datetime)
            if delivery_datetime > now:
                return delivery_datetime
    
    # Fallback to next week
    next_week = now + dt.timedelta(days=7)
    return next_week


if __name__ == "__main__":
    render()


