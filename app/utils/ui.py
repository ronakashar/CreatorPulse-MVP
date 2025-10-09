import streamlit as st


def inject_global_css():
    st.markdown(
        """
        <style>
        .block-container { max-width: 1100px; }
        .cp-card { background: #11162B; border: 1px solid #1F2542; border-radius: 12px; padding: 1rem 1.2rem; }
        .cp-card h3 { margin-top: 0; }
        .cp-section-title { font-size: 1.25rem; margin: 0.5rem 0 0.75rem; color: #E6E8F9; }
        .cp-muted { color: #9AA0C3; }
        .stButton>button { border-radius: 10px; }
        .stTabs [data-baseweb="tab-list"] { gap: 8px; }
        .stTabs [data-baseweb="tab"] { background: #141A33; border-radius: 8px; padding: 8px 14px; }
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


