import streamlit as st


def inject_global_css():
    st.markdown(
        """
        <style>
        /* Global Layout */
        .block-container { 
            max-width: 1400px; 
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        
        /* Sidebar Improvements */
        .css-1d391kg {
            background: linear-gradient(180deg, #0F172A 0%, #1E293B 100%);
            border-right: 1px solid #334155;
        }
        
        /* Modern Card System */
        .cp-card { 
            background: linear-gradient(135deg, #1E293B 0%, #334155 100%);
            border: 1px solid #475569;
            border-radius: 16px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            transition: all 0.3s ease;
        }
        
        .cp-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }
        
        .cp-card h3 { 
            margin-top: 0; 
            color: #F8FAFC;
            font-weight: 600;
            font-size: 1.25rem;
        }
        
        /* Typography */
        .cp-section-title { 
            font-size: 1.5rem; 
            margin: 0.5rem 0 1rem; 
            color: #F8FAFC;
            font-weight: 700;
            background: linear-gradient(135deg, #8B5CF6 0%, #06B6D4 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .cp-muted { 
            color: #94A3B8; 
            font-size: 0.9rem;
        }
        
        /* Enhanced Buttons */
        .stButton>button { 
            border-radius: 12px;
            background: linear-gradient(135deg, #8B5CF6 0%, #06B6D4 100%);
            border: none;
            color: white;
            font-weight: 600;
            padding: 0.5rem 1.5rem;
            transition: all 0.3s ease;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        .stButton>button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
        }
        
        /* Modern Tabs */
        .stTabs [data-baseweb="tab-list"] { 
            gap: 8px; 
            background: #1E293B;
            border-radius: 12px;
            padding: 4px;
        }
        
        .stTabs [data-baseweb="tab"] { 
            background: transparent;
            border-radius: 8px; 
            padding: 8px 16px;
            color: #94A3B8;
            transition: all 0.3s ease;
        }
        
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background: linear-gradient(135deg, #8B5CF6 0%, #06B6D4 100%);
            color: white;
        }
        
        /* Input Styling */
        .stTextInput>div>div>input,
        .stTextArea>div>div>textarea,
        .stSelectbox>div>div>select {
            border-radius: 8px;
            border: 1px solid #475569;
            background: #1E293B;
            color: #F8FAFC;
        }
        
        .stTextInput>div>div>input:focus,
        .stTextArea>div>div>textarea:focus {
            border-color: #8B5CF6;
            box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.2);
        }
        
        /* Slider Styling */
        .stSlider>div>div>div>div {
            background: linear-gradient(135deg, #8B5CF6 0%, #06B6D4 100%);
        }
        
        /* Metric Cards */
        .metric-card {
            background: linear-gradient(135deg, #1E293B 0%, #334155 100%);
            border: 1px solid #475569;
            border-radius: 12px;
            padding: 1rem;
            text-align: center;
            transition: all 0.3s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
        }
        
        .metric-value {
            font-size: 2rem;
            font-weight: 700;
            color: #8B5CF6;
            margin: 0;
        }
        
        .metric-label {
            color: #94A3B8;
            font-size: 0.9rem;
            margin: 0.5rem 0 0 0;
        }
        
        /* Status Indicators */
        .status-success {
            background: linear-gradient(135deg, #10B981 0%, #059669 100%);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            font-weight: 600;
        }
        
        .status-warning {
            background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            font-weight: 600;
        }
        
        .status-error {
            background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            font-weight: 600;
        }
        
        /* Progress Bars */
        .progress-container {
            background: #1E293B;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
        }
        
        .progress-bar {
            background: linear-gradient(135deg, #8B5CF6 0%, #06B6D4 100%);
            height: 8px;
            border-radius: 4px;
            transition: width 0.3s ease;
        }
        
        /* Loading Animation */
        .loading-spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #475569;
            border-radius: 50%;
            border-top-color: #8B5CF6;
            animation: spin 1s ease-in-out infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .block-container {
                max-width: 100%;
                padding: 1rem;
            }
            
            .cp-card {
                padding: 1rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def card(title: str = "", body: str = ""):
    st.markdown(f"<div class='cp-card'><h3 class='cp-section-title'>{title}</h3>", unsafe_allow_html=True)
    if body:
        st.markdown(body)
    return st.container()


def header(title: str, subtitle: str = ""):
    st.markdown(f"### {title}")
    if subtitle:
        st.markdown(f"<span class='cp-muted'>{subtitle}</span>", unsafe_allow_html=True)


def section_header(title: str, subtitle: str = ""):
    st.markdown(f"<h3 class='cp-section-title'>{title}</h3>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f"<span class='cp-muted'>{subtitle}</span>", unsafe_allow_html=True)


def metric_card(value: str, label: str, delta: str = None):
    """Create a modern metric card with optional delta indicator"""
    delta_html = f'<div style="color: #10B981; font-size: 0.8rem; margin-top: 0.25rem;">{delta}</div>' if delta else ""
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def status_badge(status: str, status_type: str = "success"):
    """Create a status badge with different styles"""
    st.markdown(f'<span class="status-{status_type}">{status}</span>', unsafe_allow_html=True)


def progress_bar(current: int, total: int, label: str = ""):
    """Create a custom progress bar"""
    percentage = (current / total) * 100 if total > 0 else 0
    st.markdown(f"""
    <div class="progress-container">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
            <span style="color: #F8FAFC; font-weight: 600;">{label}</span>
            <span style="color: #94A3B8;">{current}/{total}</span>
        </div>
        <div style="background: #334155; border-radius: 4px; height: 8px; overflow: hidden;">
            <div class="progress-bar" style="width: {percentage}%;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def loading_spinner(text: str = "Loading..."):
    """Show a loading spinner with text"""
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 0.5rem; margin: 1rem 0;">
        <div class="loading-spinner"></div>
        <span style="color: #94A3B8;">{text}</span>
    </div>
    """, unsafe_allow_html=True)


def empty_state(icon: str, title: str, description: str, action_text: str = None, action_func=None):
    """Create an empty state component"""
    action_html = ""
    if action_text and action_func:
        action_html = f'<button onclick="{action_func}" style="margin-top: 1rem; padding: 0.75rem 1.5rem; background: linear-gradient(135deg, #8B5CF6 0%, #06B6D4 100%); color: white; border: none; border-radius: 8px; font-weight: 600; cursor: pointer;">{action_text}</button>'
    
    st.markdown(f"""
    <div style="text-align: center; padding: 3rem 1rem; color: #94A3B8;">
        <div style="font-size: 3rem; margin-bottom: 1rem;">{icon}</div>
        <h3 style="color: #F8FAFC; margin-bottom: 0.5rem;">{title}</h3>
        <p style="margin-bottom: 1rem;">{description}</p>
        {action_html}
    </div>
    """, unsafe_allow_html=True)


def info_card(title: str, content: str, icon: str = "ℹ️"):
    """Create an informational card"""
    st.markdown(f"""
    <div class="cp-card" style="border-left: 4px solid #8B5CF6;">
        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
            <span style="font-size: 1.2rem;">{icon}</span>
            <h4 style="margin: 0; color: #F8FAFC;">{title}</h4>
        </div>
        <p style="margin: 0; color: #94A3B8;">{content}</p>
    </div>
    """, unsafe_allow_html=True)


def success_card(title: str, content: str, icon: str = "✅"):
    """Create a success card"""
    st.markdown(f"""
    <div class="cp-card" style="border-left: 4px solid #10B981;">
        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
            <span style="font-size: 1.2rem;">{icon}</span>
            <h4 style="margin: 0; color: #F8FAFC;">{title}</h4>
        </div>
        <p style="margin: 0; color: #94A3B8;">{content}</p>
    </div>
    """, unsafe_allow_html=True)


def warning_card(title: str, content: str, icon: str = "⚠️"):
    """Create a warning card"""
    st.markdown(f"""
    <div class="cp-card" style="border-left: 4px solid #F59E0B;">
        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
            <span style="font-size: 1.2rem;">{icon}</span>
            <h4 style="margin: 0; color: #F8FAFC;">{title}</h4>
        </div>
        <p style="margin: 0; color: #94A3B8;">{content}</p>
    </div>
    """, unsafe_allow_html=True)


def error_card(title: str, content: str, icon: str = "❌"):
    """Create an error card"""
    st.markdown(f"""
    <div class="cp-card" style="border-left: 4px solid #EF4444;">
        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
            <span style="font-size: 1.2rem;">{icon}</span>
            <h4 style="margin: 0; color: #F8FAFC;">{title}</h4>
        </div>
        <p style="margin: 0; color: #94A3B8;">{content}</p>
    </div>
    """, unsafe_allow_html=True)


def create_navigation():
    """Create a modern navigation component"""
    st.markdown("""
    <nav style="background: linear-gradient(135deg, #1E293B 0%, #334155 100%); 
                padding: 1rem; border-radius: 12px; margin-bottom: 2rem;">
        <div style="display: flex; align-items: center; gap: 1rem;">
            <div style="font-size: 1.5rem;">📰</div>
            <h2 style="margin: 0; color: #F8FAFC;">CreatorPulse</h2>
            <div style="margin-left: auto; display: flex; gap: 0.5rem;">
                <span style="background: #8B5CF6; color: white; padding: 0.25rem 0.75rem; 
                           border-radius: 20px; font-size: 0.8rem;">Pro</span>
            </div>
        </div>
    </nav>
    """, unsafe_allow_html=True)


def feature_card(title: str, description: str, icon: str, status: str = "active"):
    """Create a feature card with status indicator"""
    status_color = "#10B981" if status == "active" else "#94A3B8"
    st.markdown(f"""
    <div class="cp-card" style="position: relative;">
        <div style="position: absolute; top: 1rem; right: 1rem;">
            <div style="width: 8px; height: 8px; background: {status_color}; 
                       border-radius: 50%;"></div>
        </div>
        <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.75rem;">
            <span style="font-size: 1.5rem;">{icon}</span>
            <h4 style="margin: 0; color: #F8FAFC;">{title}</h4>
        </div>
        <p style="margin: 0; color: #94A3B8; line-height: 1.5;">{description}</p>
    </div>
    """, unsafe_allow_html=True)


def timeline_item(title: str, description: str, time: str, status: str = "completed"):
    """Create a timeline item"""
    status_icon = "✅" if status == "completed" else "⏳" if status == "pending" else "❌"
    status_color = "#10B981" if status == "completed" else "#F59E0B" if status == "pending" else "#EF4444"
    
    st.markdown(f"""
    <div style="display: flex; gap: 1rem; margin-bottom: 1rem;">
        <div style="flex-shrink: 0; width: 40px; height: 40px; background: {status_color}; 
                   border-radius: 50%; display: flex; align-items: center; justify-content: center;">
            <span style="font-size: 1.2rem;">{status_icon}</span>
        </div>
        <div style="flex: 1;">
            <h4 style="margin: 0 0 0.25rem 0; color: #F8FAFC;">{title}</h4>
            <p style="margin: 0 0 0.25rem 0; color: #94A3B8;">{description}</p>
            <span style="color: #64748B; font-size: 0.8rem;">{time}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


