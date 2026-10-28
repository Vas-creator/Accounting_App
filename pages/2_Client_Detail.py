# pages/2_Client_Detail.py
"""
Client Detail — ဖောက်သည် အသေးစိတ် + ရှင်းတမ်း ၄ ခု Overview (Multi-Year Support)
"""
import streamlit as st
from core import db
from core.utils import format_date_mm
from core.translations import t

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Client Detail",
    page_icon="📂",
    layout="wide",
)

# ============================================================
# AUTH CHECK
# ============================================================

if not st.session_state.get("authentication_status"):
    st.warning("⚠️ ကျေးဇူးပြု၍ အရင် ဝင်ရောက်ပါ" if st.session_state.get("language", "my") == "my" else "⚠️ Please login first")
    st.switch_page("app.py")
    st.stop()

# ============================================================
# CLIENT ID CHECK
# ============================================================

client_id = st.session_state.get("selected_client_id")

if not client_id:
    st.warning("⚠️ ဖောက်သည် မရွေးရသေးပါ" if st.session_state.get("language", "my") == "my" else "⚠️ No client selected")
    if st.button("← ဖောက်သည် စာရင်းသို့ ပြန်" if st.session_state.get("language", "my") == "my" else "← Back to Clients"):
        st.switch_page("pages/1_Clients.py")
    st.stop()

# ============================================================
# LOAD CLIENT
# ============================================================

try:
    client = db.get_client(client_id)
except Exception as e:
    st.error(f"❌ Database error: {e}")
    st.stop()

if not client:
    st.error("❌ ဖောက်သည် မတွေ့ပါ" if st.session_state.get("language", "my") == "my" else "❌ Client not found")
    if st.button("← ဖောက်သည် စာရင်းသို့ ပြန်" if st.session_state.get("language", "my") == "my" else "← Back to Clients"):
        st.switch_page("pages/1_Clients.py")
    st.stop()

# ⭐ Client Name မရှိရင် Business Name ကို ယူမယ်
client_display_name = client.get("name") if client.get("name") else client.get("business_name", "Unknown")

# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

with st.sidebar:
    st.markdown(
        f"""
        <div style="text-align: center; padding: 0.5rem 0;">
            <h2 style="color: #1f4788; font-size: 1.3rem; margin: 0;">
                📊 {t('app_title')}
            </h2>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

    if st.button(t('home'), use_container_width=True):
        st.switch_page("app.py")

    if st.button(t('clients'), use_container_width=True):
        st.switch_page("pages/1_Clients.py")

    st.divider()

    st.markdown(
        f"""
        <div style="
            background-color: #e3f2fd;
            padding: 0.8rem;
            border-radius: 8px;
            border-left: 4px solid #1565c0;
            margin-bottom: 1rem;
        ">
            <p style="margin: 0; font-size: 0.85rem; color: #666;">{'လက်ရှိ ဖောက်သည်' if st.session_state.get('language', 'my') == 'my' else 'Current Client'}</p>
            <p style="margin: 0.2rem 0 0 0; font-weight: bold; color: #1565c0;">
                👤 {client_display_name}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption(f"👤 {st.session_state.get('name', 'User')}")

# ============================================================
# HEADER — Client Info
# ============================================================

col_back, col_blank = st.columns([1, 5])
with col_back:
    if st.button("← " + ("ပြန်" if st.session_state.get("language", "my") == "my" else "Back"), use_container_width=True):
        st.switch_page("pages/1_Clients.py")

st.markdown(
    f"""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1.5rem;
    ">
        <h1 style="margin: 0; font-size: 2rem;">
            👤 {client_display_name}
        </h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1rem; opacity: 0.95;">
            {f'🏢 {client.get("business_name")}' if client.get('business_name') and client.get('business_name') != client_display_name else ''}
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Client Info Cards
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        f"""
        <div style="background-color: #f5f5f5; padding: 0.8rem; border-radius: 8px;">
            <p style="margin: 0; font-size: 0.8rem; color: #666;">📧 {t('email')}</p>
            <p style="margin: 0.3rem 0 0 0; font-weight: bold; color: #333;">
                {client.get('email') or '—'}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        f"""
        <div style="background-color: #f5f5f5; padding: 0.8rem; border-radius: 8px;">
            <p style="margin: 0; font-size: 0.8rem; color: #666;">📞 {t('phone')}</p>
            <p style="margin: 0.3rem 0 0 0; font-weight: bold; color: #333;">
                {client.get('phone') or '—'}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        f"""
        <div style="background-color: #f5f5f5; padding: 0.8rem; border-radius: 8px;">
            <p style="margin: 0; font-size: 0.8rem; color: #666;">📍 {t('address')}</p>
            <p style="margin: 0.3rem 0 0 0; font-weight: bold; color: #333;">
                {client.get('address') or '—'}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col4:
    st.markdown(
        f"""
        <div style="background-color: #f5f5f5; padding: 0.8rem; border-radius: 8px;">
            <p style="margin: 0; font-size: 0.8rem; color: #666;">💼 {t('business_type')}</p>
            <p style="margin: 0.3rem 0 0 0; font-weight: bold; color: #333; font-size: 0.85rem;">
                {client.get('business_type') or '—'}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ============================================================
# MULTI-YEAR PERIOD SELECTION
# ============================================================

st.markdown(
    f"""
    <h2 style="color: #1f4788; font-size: 1.6rem; margin-top: 1rem;">
        📅 {'ကာလ ရွေးချယ်ပါ' if st.session_state.get('language', 'my') == 'my' else 'Select Period'}
    </h2>
    """,
    unsafe_allow_html=True,
)

# ဖောက်သည်ရဲ့ သိမ်းထားတဲ့ ကာလတွေကို ရှာမယ်
try:
    history = db.get_statement_history(client_id, "trading_pl")
    history_periods = sorted(list(set([h["period_end"] for h in history if h.get("period_end")])), reverse=True)
except Exception:
    history_periods = []

# Session State မှာ ရွေးထားတဲ့ ကာလကို သိမ်းမယ်
if "selected_detail_period" not in st.session_state:
    st.session_state.selected_detail_period = history_periods[0] if history_periods else ""

# ကာလရွေးတဲ့ Dropdown
if history_periods:
    col_period, col_add = st.columns([2, 1])
    with col_period:
        selected_period = st.selectbox(
            "ကာလ (Period)",
            options=history_periods,
            index=history_periods.index(st.session_state.selected_detail_period) if st.session_state.selected_detail_period in history_periods else 0,
            key="detail_period_select"
        )
        st.session_state.selected_detail_period = selected_period
    with col_add:
        st.markdown("<br>", unsafe_allow_html=True) # Alignment အတွက်
        if st.button(f"➕ {'ကာလအသစ် ထပ်ထည့်ရန်' if st.session_state.get('language', 'my') == 'my' else 'Add New Period'}", use_container_width=True):
            # ကာလအသစ်ထည့်ဖို့ Trading PL ကို ပို့မယ်
            st.session_state["selected_client_id"] = client_id
            st.session_state["selected_client_name"] = client_display_name
            st.switch_page("pages/4_Trading_PL.py")
else:
    st.info("သိမ်းထားသော စာရင်း မရှိသေးပါ။ အောက်က ခလုတ်ကို နှိပ်ပြီး စတင်ပါ။" if st.session_state.get("language") == "my" else "No statements yet. Click below to start.")
    if st.button(f"➕ {'စာရင်းအသစ် စတင်ရန်' if st.session_state.get('language', 'my') == 'my' else 'Start New Statement'}", type="primary"):
        st.session_state["selected_client_id"] = client_id
        st.session_state["selected_client_name"] = client_display_name
        st.switch_page("pages/4_Trading_PL.py")

st.markdown("<br>", unsafe_allow_html=True)

# ============================================================
# STATEMENTS OVERVIEW (ရွေးထားတဲ့ ကာလအလိုက်)
# ============================================================

st.markdown(
    f"""
    <h2 style="color: #1f4788; font-size: 1.6rem; margin-top: 1rem;">
        {t('all_statements')} — {st.session_state.selected_detail_period}
    </h2>
    """,
    unsafe_allow_html=True,
)

# Statement types
statements_config = [
    {
        "key": "manufacturing",
        "icon": "🏭",
        "page": "pages/3_Manufacturing.py",
        "color": "#f093fb",
    },
    {
        "key": "trading_pl",
        "icon": "💰",
        "page": "pages/4_Trading_PL.py",
        "color": "#4facfe",
    },
    {
        "key": "balance_sheet",
        "icon": "📊",
        "page": "pages/5_Balance_Sheet.py",
        "color": "#43e97b",
    },
    {
        "key": "cash_flow",
        "icon": "💵",
        "page": "pages/6_Cash_Flow.py",
        "color": "#667eea",
    },
]

cols = st.columns(4)
for idx, stmt in enumerate(statements_config):
    with cols[idx]:
        try:
            # ⭐ ရွေးထားတဲ့ ကာလအတွက် စာရင်းရှိမရှိ စစ်မယ်
            existing = db.get_statement(client_id, stmt["key"], period_end=st.session_state.selected_detail_period)
            has_data = existing is not None and existing.get("data") is not None
        except Exception:
            has_data = False

        status_icon = "✓" if has_data else "○"
        status_text = t("has_data") if has_data else t("no_data")
        status_color = "#2e7d32" if has_data else "#999"
        
        title_key = stmt["key"]
        if title_key == "manufacturing":
            title = t("manufacturing")
        elif title_key == "trading_pl":
            title = t("trading_pl")
        elif title_key == "balance_sheet":
            title = t("balance_sheet_title")
        elif title_key == "cash_flow":
            title = t("cash_flow")

        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, {stmt['color']}40, {stmt['color']}20);
                border: 2px solid {stmt['color']};
                border-radius: 12px;
                padding: 1.5rem;
                text-align: center;
                margin-bottom: 0.5rem;
                min-height: 200px;
            ">
                <p style="font-size: 3rem; margin: 0;">{stmt['icon']}</p>
                <h3 style="margin: 0.5rem 0 0.3rem 0; color: #1f4788; font-size: 1.15rem;">
                    {title}
                </h3>
                <p style="margin: 0.8rem 0 0 0; color: {status_color}; font-weight: bold; font-size: 0.95rem;">
                    {status_icon} {status_text}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            t("open_page") if has_data else t("add_data"),
            key=f"goto_{stmt['key']}",
            use_container_width=True,
            type="primary" if not has_data else "secondary",
        ):
            st.session_state["selected_client_id"] = client_id
            st.session_state["selected_client_name"] = client_display_name
            # ⭐ ရွေးထားတဲ့ ကာလကို သက်ဆိုင်ရာ စာမျက်နှာတွေဆီ ပို့ပေးမယ်
            st.session_state["target_period"] = st.session_state.selected_detail_period
            st.switch_page(stmt["page"])

st.markdown("<br>", unsafe_allow_html=True)

# ============================================================
# PDF EXPORT SECTION
# ============================================================

st.markdown(
    f"""
    <h2 style="color: #1f4788; font-size: 1.6rem; margin-top: 1rem;">
        📄 {t('export_pdf')}
    </h2>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div style="
        background-color: #fff3e0;
        border-left: 5px solid #e65100;
        padding: 1rem 1.2rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    ">
        <p style="margin: 0; color: #e65100; font-size: 1rem;">
            💡 <b>{t('export_pdf')}</b> — {'ရွေးထားတဲ့ ကာလအတွက် ရှင်းတမ်း ၄ ခုလုံး ဖြည့်ပြီးမှ ဤနေရာမှ ထုတ်ယူပါ' if st.session_state.get('language', 'my') == 'my' else 'Fill all 4 statements for the selected period before exporting PDF'}
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

col1, col2 = st.columns(2)

with col1:
    if st.button(f"📄 {t('export_pdf')}", use_container_width=True, type="primary"):
        st.session_state["selected_client_id"] = client_id
        st.session_state["selected_client_name"] = client_display_name
        st.session_state["target_period"] = st.session_state.selected_detail_period
        st.switch_page("pages/7_Export.py")

with col2:
    if st.button(t("delete_client"), use_container_width=True):
        st.session_state["delete_from_detail"] = True
        st.rerun()

# ============================================================
# DELETE CONFIRMATION
# ============================================================

if st.session_state.get("delete_from_detail"):
    st.divider()
    st.markdown(
        f"""
        <div style="
            background-color: #ffebee;
            border-left: 5px solid #c62828;
            border-radius: 8px;
            padding: 1.2rem;
            margin: 1rem 0;
        ">
            <h3 style="color: #c62828; margin: 0;">
                ⚠️ {'ဖျက်ရန် အတည်ပြုပါ' if st.session_state.get('language', 'my') == 'my' else 'Confirm Delete'}
            </h3>
            <p style="color: #c62828; margin: 0.5rem 0 0 0; font-size: 1rem;">
                '<b>{client_display_name}</b>' {'နဲ့ ရှင်းတမ်းအားလုံးကို ဖျက်ပါမည်လား?' if st.session_state.get('language', 'my') == 'my' else 'and all statements will be deleted. Are you sure?'}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button(t("delete"), type="primary", use_container_width=True):
            try:
                db.delete_client(client_id)
                st.session_state.pop("selected_client_id", None)
                st.session_state.pop("selected_client_name", None)
                st.session_state["delete_from_detail"] = False
                st.success(f"✓ '{client_display_name}' {'ဖျက်ပြီးပါပြီ' if st.session_state.get('language', 'my') == 'my' else 'deleted successfully'}")
                st.switch_page("pages/1_Clients.py")
            except Exception as e:
                st.error(f"❌ Error: {e}")
    with col2:
        if st.button(t("cancel"), use_container_width=True):
            st.session_state["delete_from_detail"] = False
            st.rerun()

# ============================================================
# NOTES SECTION (optional)
# ============================================================

if client.get("notes"):
    st.divider()
    st.markdown(
        f"""
        <h3 style="color: #1f4788; font-size: 1.2rem;">
            📝 {t('notes')}
        </h3>
        """,
        unsafe_allow_html=True,
    )
    st.info(client["notes"])


# ============================================================
# META INFO
# ============================================================

st.divider()
col1, col2 = st.columns(2)
with col1:
    st.caption(f"📅 {t('created')}: {format_date_mm(client.get('created_at', ''))}")
with col2:
    st.caption(f"🔄 {t('updated')}: {format_date_mm(client.get('updated_at', ''))}")

# ============================================================
# AI CHAT BOX (ဖိုင်ရဲ့ အောက်ဆုံးမှာ ထည့်ပါ)
# ============================================================
from core.ai_help import get_ai_response
from core.utils import format_number
import json

st.divider()
st.markdown("### 🤖 AI စာရင်းအကူအညီ (Ask AI)")

chat_key = f"ai_chat_history_{client_id}"
if chat_key not in st.session_state:
    st.session_state[chat_key] = []

client_context = f"ဖောက်သည်အမည်: {client_display_name}\nလုပ်ငန်းအမျိုးအစား: {client.get('business_type', '')}\n"

try:
    # ⭐ ရွေးထားတဲ့ ကာလအတွက် Trading PL ကို ယူမယ်
    tpl_data = db.get_statement(client_id, "trading_pl", period_end=st.session_state.selected_detail_period)
    if tpl_data and tpl_data.get("data"):
        tpl_info = json.loads(tpl_data["data"])
        client_context += f"""
        ကာလ: {st.session_state.selected_detail_period}
        အရောင်း: {format_number(tpl_info.get('_total_revenue', 0))}
        ကုန်ကျစရိတ်: {format_number(tpl_info.get('_total_cos', 0))}
        အမြတ်: {format_number(tpl_info.get('_gross_profit', 0))}
        အသုံးစရိတ်: {format_number(tpl_info.get('_total_expenses', 0))}
        အသားတင်အမြတ်: {format_number(tpl_info.get('_net_profit', 0))}
        """
except Exception:
    pass

for message in st.session_state[chat_key]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("ဒီဖောက်သည်ရဲ့ စာရင်းအခြေအနေကို မေးပါ..."):
    st.session_state[chat_key].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("AI စဉ်းစားနေသည်..."):
            response = get_ai_response(prompt, client_context)
            st.markdown(response)
    st.session_state[chat_key].append({"role": "assistant", "content": response})