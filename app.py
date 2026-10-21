# app.py
"""
Accounting App — Main Entry Point
Home Dashboard + Authentication
"""
from core.translations import t
import os
import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

# ============================================================
# 1. PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="စာရင်း အက်ပ် — Accounting App",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "language" not in st.session_state:
    st.session_state.language = "my"

# ============================================================
# 2. IMPORTS
# ============================================================

from core import db
from core.utils import format_currency, format_date_mm, info_box

# ============================================================
# 3. AUTHENTICATION SETUP
# ============================================================

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "auth_config.yaml")

def get_auth_config() -> dict:
    if not os.path.exists(CONFIG_PATH):
        default_config = {
            "credentials": {
                "usernames": {
                    "admin": {
                        "name": "အုပ်ချုပ်သူ",
                        "password": stauth.Hasher.hash("admin123"),
                        "email": "admin@example.com",
                    }
                }
            },
            "cookie": {
                "expiry_days": 30,
                "key": "accounting_app_secret_key_2024",
                "name": "accounting_app_cookie",
            },
        }
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            yaml.dump(default_config, f, allow_unicode=True, default_flow_style=False)
        return default_config
    
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.load(f, Loader=SafeLoader)

def setup_authenticator(config: dict):
    return stauth.Authenticate(
        config["credentials"],
        config["cookie"]["name"],
        config["cookie"]["key"],
        config["cookie"]["expiry_days"],
        auto_hash=True,
    )

# ============================================================
# 4. SIDEBAR
# ============================================================

def render_sidebar(authenticator):
    with st.sidebar:
        st.markdown(
            """
            <div style="text-align: center; padding: 1rem 0;">
                <h1 style="color: #1f4788; font-size: 2rem; margin: 0;">📊</h1>
                <h2 style="color: #1f4788; font-size: 1.3rem; margin: 0.3rem 0;">
                    စာရင်း အက်ပ်
                </h2>
                <p style="color: #666; font-size: 0.9rem; margin: 0;">
                    Accounting App
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        st.divider()

        st.markdown("**🌐 ဘာသာစကား / Language**")
        lang = st.radio(
            "ရွေးချယ်ပါ",
            options=["my", "en"],
            format_func=lambda x: "မြန်မာ" if x == "my" else "English",
            index=0 if st.session_state.language == "my" else 1,
            label_visibility="collapsed"
        )
        if lang != st.session_state.language:
            st.session_state.language = lang
            st.rerun()
        
        user_name = st.session_state.get("name", "User")
        st.markdown(
            f"""
            <div style="background-color: #e3f2fd; padding: 0.8rem; border-radius: 8px; border-left: 4px solid #1565c0; margin-bottom: 1rem;">
                <p style="margin: 0; font-size: 0.9rem; color: #666;">အသုံးပြုသူ</p>
                <p style="margin: 0.2rem 0 0 0; font-weight: bold; color: #1565c0;">
                    👤 {user_name}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        authenticator.logout(button_name="🚪 ထွက်ရန် (Logout)", location="sidebar")
        
        st.divider()
        st.markdown(
            """
            <div style="text-align: center; color: #999; font-size: 0.8rem; padding-top: 1rem;">
                <p>v1.0 — 2024</p>
                <p>Accounting App</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ============================================================
# 5. HOME PAGE
# ============================================================

def render_home():
    st.markdown(
        f"""
        <div style="padding: 0.5rem 0 1.5rem 0;">
            <h1 style="color: #1f4788; font-size: 2.5rem; margin: 0;">
                {t('home_title')}
            </h1>
            <p style="color: #666; font-size: 1.1rem; margin-top: 0.5rem;">
                {t('home_subtitle')}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    try:
        stats = db.get_dashboard_stats()
    except Exception as e:
        st.error(f"Database Error: {e}")
        stats = {"total_clients": 0, "total_statements": 0, "latest_update": "—"}
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1.5rem; border-radius: 12px; color: white; text-align: center;">
                <p style="font-size: 2.5rem; margin: 0;">👥</p>
                <p style="font-size: 0.95rem; margin: 0.5rem 0 0 0; opacity: 0.9;">{t('total_clients')}</p>
                <h2 style="font-size: 2.5rem; margin: 0.5rem 0 0 0;">{stats['total_clients']}</h2>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    with col2:
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 1.5rem; border-radius: 12px; color: white; text-align: center;">
                <p style="font-size: 2.5rem; margin: 0;">📄</p>
                <p style="font-size: 0.95rem; margin: 0.5rem 0 0 0; opacity: 0.9;">{t('total_statements')}</p>
                <h2 style="font-size: 2.5rem; margin: 0.5rem 0 0 0;">{stats['total_statements']}</h2>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    with col3:
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 1.5rem; border-radius: 12px; color: white; text-align: center;">
                <p style="font-size: 2.5rem; margin: 0;">🕒</p>
                <p style="font-size: 0.95rem; margin: 0.5rem 0 0 0; opacity: 0.9;">{t('latest_update')}</p>
                <h2 style="font-size: 1.3rem; margin: 0.8rem 0 0 0;">{stats['latest_update']}</h2>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f'<h2 style="color: #1f4788; font-size: 1.6rem; margin-top: 1rem;">{t("quick_actions")}</h2>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button(t('manage_clients'), use_container_width=True, type="primary"):
            st.switch_page("pages/1_Clients.py")
    
    with col2:
        if st.button(t('mfg_acc'), use_container_width=True):
            st.switch_page("pages/3_Manufacturing.py")
    
    with col3:
        if st.button(t('trading_acc'), use_container_width=True):
            st.switch_page("pages/4_Trading_PL.py")
    
    with col4:
        if st.button(t('balance_sheet'), use_container_width=True):
            st.switch_page("pages/5_Balance_Sheet.py")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f'<h2 style="color: #1f4788; font-size: 1.6rem; margin-top: 1rem;">{t("recent_clients")}</h2>', unsafe_allow_html=True)
    
    try:
        recent_clients = db.get_recent_clients(limit=5)
    except Exception:
        recent_clients = []
    
    if not recent_clients:
        info_box(t('no_clients'), "info")
    else:
        for client in recent_clients:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                with col1:
                    st.markdown(f"**{client['name']}**")
                    if client.get('business_type'):
                        st.caption(f"{client['business_type']}")
                with col2:
                    st.caption(f"Phone: {client.get('phone', '—')}")
                with col3:
                    st.caption(f"Date: {format_date_mm(client.get('updated_at', ''))}")
                with col4:
                    if st.button("Open", key=f"open_{client['id']}"):
                        st.session_state["selected_client_id"] = client["id"]
                        st.session_state["selected_client_name"] = client["name"]
                        st.switch_page("pages/2_Client_Detail.py")
                st.divider()
    
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander(t('help')):
        st.markdown(
            """
            ### 🚀 အစပြုရန် အဆင့်များ
            1. **ဖောက်သည် ထည့်ပါ**
            2. **ဖောက်သည် ရွေးပါ**
            3. **ရှင်းတမ်း ထည့်ပါ**
            4. **PDF ရယူပါ**
            """
        )

# ============================================================
# 6. MAIN
# ============================================================

def main():
    try:
        db.init_db()
    except Exception as e:
        st.error(f"Database initialize failed: {e}")
        st.stop()
    
    config = get_auth_config()
    authenticator = setup_authenticator(config)
    
    # ---------- Login ----------
    if not st.session_state.get("authentication_status"):
        st.markdown(
            """
            <div style="text-align: center; padding: 2rem 0 1rem 0;">
                <h1 style="color: #1f4788; font-size: 3rem; margin: 0;">📊</h1>
                <h1 style="color: #1f4788; font-size: 2rem; margin: 0.5rem 0;">Accounting App</h1>
                <p style="color: #666; font-size: 1.1rem;">Financial Statements Management</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            authenticator.login(
                location="main",
                fields={
                    "Form name": "🔐 Login",
                    "Username": "Username",
                    "Password": "Password",
                    "Login": "Login",
                },
            )
        
        auth_status = st.session_state.get("authentication_status")
        if auth_status is False:
            st.error("❌ Invalid username or password")
        elif auth_status is None:
            st.info("💡 Please enter your username and password")
        
        st.stop()
    
    # ---------- Authenticated ----------


    render_sidebar(authenticator)
    render_home()

if __name__ == "__main__":
    main()