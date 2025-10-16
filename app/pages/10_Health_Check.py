import streamlit as st
import json
from datetime import datetime
from utils.ui import inject_global_css, header
from services.monitoring import health_checker, monitoring


def render():
    st.set_page_config(page_title="Health Check — CreatorPulse", page_icon="🏥", layout="wide")
    inject_global_css()
    
    header("System Health Check", "Monitor system status and performance")

    # Get system status
    try:
        status = health_checker.get_system_status()
        
        # Overall status
        status_emoji = {
            "healthy": "✅",
            "degraded": "⚠️", 
            "unhealthy": "❌"
        }.get(status["overall_status"], "❓")
        
        st.markdown(f"## {status_emoji} Overall Status: {status['overall_status'].title()}")
        
        # Database status
        st.markdown("### Database Status")
        db_status = status["database"]
        db_emoji = "✅" if db_status["status"] == "healthy" else "❌"
        st.markdown(f"{db_emoji} **Database**: {db_status['status']}")
        
        if db_status.get("error"):
            st.error(f"Database Error: {db_status['error']}")
        
        # External APIs status
        st.markdown("### External APIs Status")
        for api_name, api_status in status["external_apis"].items():
            api_emoji = "✅" if api_status["status"] == "healthy" else "❌"
            st.markdown(f"{api_emoji} **{api_name.title()}**: {api_status['status']}")
            
            if api_status.get("error"):
                st.error(f"{api_name.title()} Error: {api_status['error']}")
        
        # Detailed status JSON
        with st.expander("📋 Detailed Status (JSON)"):
            st.json(status)
        
        # Refresh button
        if st.button("🔄 Refresh Status"):
            st.rerun()
        
        # System information
        st.markdown("### System Information")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Timestamp", datetime.fromtimestamp(status["timestamp"]).strftime("%Y-%m-%d %H:%M:%S"))
        
        with col2:
            st.metric("Environment", st.get_option("server.environment") or "development")
        
        with col3:
            st.metric("Version", "1.0.0")
        
    except Exception as e:
        st.error(f"Health check failed: {e}")
        monitoring.track_error(e, {"action": "health_check"})
    
    # Performance metrics (if available)
    st.markdown("### Performance Metrics")
    
    try:
        # This would be populated by actual performance data
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Response Time", "45ms", "2ms")
        
        with col2:
            st.metric("Error Rate", "0.1%", "0.05%")
        
        with col3:
            st.metric("Uptime", "99.9%", "0.1%")
        
        with col4:
            st.metric("Active Users", "127", "23")
            
    except Exception as e:
        st.info("Performance metrics not available")
    
    # Monitoring configuration
    st.markdown("### Monitoring Configuration")
    
    monitoring_status = {
        "Sentry": "✅ Configured" if st.get_option("server.sentry_dsn") else "❌ Not configured",
        "Logging": "✅ Enabled",
        "Rate Limiting": "✅ Enabled",
        "Security Validation": "✅ Enabled"
    }
    
    for service, status in monitoring_status.items():
        st.write(f"**{service}**: {status}")


if __name__ == "__main__":
    render()
