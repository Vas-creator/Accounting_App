# pages/5_Balance_Sheet.py
"""
Balance Sheet — ငွေစာရင်း လက်ကျန်စာရင်း
"""

import streamlit as st
import json
from datetime import date

from core import db
from core.utils import (
    format_number, format_date_mm, info_box, parse_number
)
from core.pdf_generator import generate_pdf
from core.translations import t
from core.utils import play_click_sound

st.set_page_config(
    page_title="Balance Sheet",
    page_icon="📊",
    layout="wide",
)

# ============================================================
# AUTH + CLIENT CHECK
# ============================================================

if not st.session_state.get("authentication_status"):
    st.warning("⚠️ ကျေးဇူးပြု၍ အရင် ဝင်ရောက်ပါ" if st.session_state.get("language", "my") == "my" else "⚠️ Please login first")
    st.switch_page("app.py")
    st.stop()

client_id = st.session_state.get("selected_client_id")
if not client_id:
    st.warning("⚠️ ဖောက်သည် မရွေးရသေးပါ" if st.session_state.get("language", "my") == "my" else "⚠️ No client selected")
    if st.button("← ဖောက်သည် စာရင်းသို့ ပြန်" if st.session_state.get("language", "my") == "my" else "← Back to Clients"):
        st.switch_page("pages/1_Clients.py")
    st.stop()

try:
    client = db.get_client(client_id)
except Exception as e:
    st.error(f"❌ Database error: {e}")
    st.stop()

if not client:
    st.error("❌ ဖောက်သည် မတွေ့ပါ" if st.session_state.get("language", "my") == "my" else "❌ Client not found")
    st.stop()

# ⭐ ဒီနေရာမှာ ထည့်ပါ (client ကို ရပြီးမှ ဒါကို သတ်မှတ်မယ်)
client_display_name = client.get("name") if client.get("name") else client.get("business_name", "Unknown")

# ============================================================
# SESSION STATE & TARGET PERIOD
# ============================================================

# ⭐ Client Detail ကနေ လာတဲ့ ကာလကို အရင်ယူမယ်
target_period = st.session_state.get("target_period")

# ⭐ ဖောက်သည်အသစ်ဖြစ်နေရင် ရှင်းမယ်
if st.session_state.get("current_bs_client_id") != client_id:
    st.session_state.current_bs_client_id = client_id
    if "bs_data" in st.session_state:
        del st.session_state["bs_data"]
    if "bs_date" in st.session_state:
        del st.session_state["bs_date"]
    for k in list(st.session_state.keys()):
        if k.startswith("bs_"):
            del st.session_state[k]

# ⭐ Target Period ရှိရင် အဲ့ဒါကို သတ်မှတ်မယ်
if target_period:
    st.session_state.bs_date = target_period
    del st.session_state["target_period"] # သုံးပြီးရင် ဖျက်မယ်
elif "bs_date" not in st.session_state:
    st.session_state.bs_date = str(date.today()) # မရှိရင် ဒီနေ့ရက်စွဲ သတ်မှတ်မယ်

# ============================================================
# HISTORY: ကာလအလိုက် စာရင်းဟောင်းများ ရယူခြင်း
# ============================================================

history = []
try:
    history = db.get_statement_history(client_id, "balance_sheet")
except Exception:
    history = []

history_dates = [h["period_end"] for h in history if h.get("period_end")]
history_dates = sorted(list(set(history_dates)), reverse=True)

# ============================================================
# SIDEBAR
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
    if st.button(t('detail'), use_container_width=True):
        st.switch_page("pages/2_Client_Detail.py")

    st.divider()

    st.markdown(
        f"""
        <div style="background-color: #e3f2fd; padding: 0.8rem; border-radius: 8px; border-left: 4px solid #1565c0;">
            <p style="margin: 0; font-size: 0.85rem; color: #666;">{'ဖောက်သည်' if st.session_state.get('language', 'my') == 'my' else 'Client'}</p>
            <p style="margin: 0.2rem 0 0 0; font-weight: bold; color: #1565c0;">
                👤 {client_display_name}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ============================================================
# HEADER
# ============================================================

st.markdown(
    f"""
    <div style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); padding: 1.2rem 1.5rem; border-radius: 12px; color: white; margin-bottom: 1.5rem;">
        <h1 style="margin: 0; font-size: 1.8rem;">📊 {t('pdf_balance')}</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 0.95rem; opacity: 0.95;">
            Balance Sheet — {client_display_name}
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# DATE & HISTORY
# ============================================================

col_date, col_hist = st.columns([1, 1])

with col_date:
    if "bs_date" not in st.session_state:
        st.session_state.bs_date = str(date.today())

    try:
        initial_date = date.fromisoformat(st.session_state.bs_date)
    except Exception:
        initial_date = date.today()

    as_at_date = st.date_input(
        f"📅 {t('as_at_date')} (New/Update)",
        value=initial_date,
        key="bs_date_input",
    )
    st.session_state.bs_date = str(as_at_date)

with col_hist:
    if history_dates:
        st.markdown("**📜 သိမ်းထားသော ကာလများ (History)**")
        options = ["-- ကာလအသစ် (New) --"] + history_dates
        selected_history = st.selectbox("ကာလဟောင်း ပြန်ကြည့်ရန်", options=options, label_visibility="collapsed")

        if selected_history != "-- ကာလအသစ် (New) --":
            if st.session_state.get("selected_bs_history") != selected_history:
                st.session_state.selected_bs_history = selected_history

                existing_hist = db.get_statement(client_id, "balance_sheet", period_end=selected_history)
                if existing_hist:
                    raw_data = existing_hist.get("data")
                    if isinstance(raw_data, str):
                        st.session_state.bs_data = json.loads(raw_data)
                    else:
                        st.session_state.bs_data = raw_data or {}

                    st.session_state.bs_date = selected_history
                    st.rerun()
    else:
        st.info("သိမ်းထားသော စာရင်း မရှိသေးပါ။")

# ============================================================
# LOAD EXISTING (If New period)
# ============================================================

if "bs_data" not in st.session_state:
    existing = db.get_statement(client_id, "balance_sheet")
    if existing and existing.get("data"):
        raw_data = existing.get("data")
        if isinstance(raw_data, str):
            st.session_state.bs_data = json.loads(raw_data)
        else:
            st.session_state.bs_data = raw_data
    else:
        st.session_state.bs_data = {}

# ⭐ Custom Data အတွက် Session State
if "bs_custom_data" not in st.session_state:
    st.session_state.bs_custom_data = {
        "current_assets": [],
        "fixed_assets": [],
        "equity": [],
        "liabilities": []
    }

# ===========================================================
# SESSION STATE FOR SHOW/HIDE ASSETS, EQUITY, LIABILITIES
# ===========================================================

if "show_bs_assets" not in st.session_state:
    st.session_state.show_bs_assets = {
        "ca_inventories": True, "ca_receivable": True, "ca_advance": True, "ca_cash": True,
        "nca_land": True, "nca_building": True, "nca_machine": True, "nca_furniture": True, "nca_vehicle": True
    }
if "show_bs_equity" not in st.session_state:
    st.session_state.show_bs_equity = {
        "eq_capital": True, "eq_retain": True, "eq_profit": True, "eq_drawing": True
    }
if "show_bs_liab" not in st.session_state:
    st.session_state.show_bs_liab = {"liab_bank_loan": True, "liab_payable": True}

# ============================================================
# TRY TO PULL TRADING PL DATA
# ============================================================

auto_net_profit = 0.0
auto_depreciation = 0.0

try:
    tpl_existing = db.get_statement(client_id, "trading_pl", period_end=st.session_state.bs_date)
    if tpl_existing and tpl_existing.get("data"):
        raw_tpl = tpl_existing["data"]
        if isinstance(raw_tpl, str):
            tpl_data = json.loads(raw_tpl)
        else:
            tpl_data = raw_tpl
        auto_net_profit = float(tpl_data.get("_net_profit", 0.0))
        auto_depreciation = float(tpl_data.get("_depreciation", 0.0))
except Exception:
    pass

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def num_input(label: str, key: str, is_deduction: bool = False, default: float = None, help_text: str = "", state_key: str = None) -> float:
    if default is None:
        value = st.session_state.bs_data.get(key, 0.0)
    else:
        value = st.session_state.bs_data.get(key, default)

    prefix = "➖ " if is_deduction else ""
    
    if state_key:
        col_show, col_input = st.columns([0.5, 9.5])
        with col_show:
            default_show = st.session_state.get(state_key, {}).get(key, True)
            show = st.checkbox(" ", value=default_show, key=f"show_bs_{key}")
            st.session_state[state_key][key] = show
        
        with col_input:
            if show:
                result = st.number_input(
                    f"{prefix}{label}",
                    value=int(value) if value else 0,
                    min_value=0, step=1000, format="%d",
                    key=f"bs_{key}", help=help_text,
                )
                st.session_state.bs_data[key] = result
                return float(result)
            else:
                st.session_state.bs_data[key] = 0.0
                return 0.0
    else:
        result = st.number_input(
            f"{prefix}{label}",
            value=int(value) if value else 0,
            min_value=0, step=1000, format="%d",
            key=f"bs_{key}", help=help_text,
        )
        st.session_state.bs_data[key] = result
        return float(result)

def subtotal_box(label: str, value: float, color: str = "#1976d2"):
    st.markdown(
        f"""
        <div style="background-color: {color}20; border-left: 3px solid {color}; padding: 0.6rem 0.8rem; border-radius: 6px; margin: 0.5rem 0;">
            <span style="color: {color}; font-weight: bold;">{label}:</span>
            <span style="float: right; font-weight: bold; color: {color};">
                {format_number(value)}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_bs_custom_items(section_key: str, title: str):
    st.markdown(f"**➕ {title}**")
    items = st.session_state.bs_custom_data.get(section_key, [])
    
    for i, item in enumerate(items):
        col_x, col_y, col_z = st.columns([2, 2, 1])
        with col_x:
            item["label"] = st.text_input("Name", value=item.get("label", ""), key=f"bs_{section_key}_label_{i}", label_visibility="collapsed")
        with col_y:
            item["value"] = st.number_input(
                "Amount", value=int(item.get("value", 0)), 
                step=1000, format="%d", key=f"bs_{section_key}_value_{i}", 
                label_visibility="collapsed"
            )
        with col_z:
            if st.button("🗑️", key=f"bs_{section_key}_del_{i}"):
                items.pop(i)
                st.session_state.bs_custom_data[section_key] = items
                st.rerun()
    
    if st.button(f"➕ {'Item ထည့်' if st.session_state.get('language') == 'my' else 'Add Item'}", key=f"bs_add_{section_key}"):
        items.append({"label": "", "value": 0})
        st.session_state.bs_custom_data[section_key] = items
        st.rerun()
    
    total = sum(item.get("value", 0) for item in items)
    if total > 0:
        st.markdown(f"**{'စုစုပေါင်း' if st.session_state.get('language') == 'my' else 'Total'}: {format_number(total)}**")
    return total

# ============================================================
# 3 COLUMNS LAYOUT
# ============================================================

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f'<h3 style="color: #2e7d32; font-size: 1.15rem; border-bottom: 2px solid #43e97b; padding-bottom: 0.3rem;">{"၁။ ပုံသေ ပိုင်ဆိုင်မှုများ" if st.session_state.get("language") == "my" else "1. Fixed Assets"}</h3>', unsafe_allow_html=True)
    nca_land = num_input("မြေ (Land)", "nca_land", state_key="show_bs_assets")
    nca_building = num_input("အဆောက်အအုံ (Building)", "nca_building", state_key="show_bs_assets")
    nca_machine = num_input("စက်ပစ္စည်း (Machine)", "nca_machine", state_key="show_bs_assets")
    nca_furniture = num_input("ပရိဘောဂ (Furniture)", "nca_furniture", state_key="show_bs_assets")
    nca_vehicle = num_input("ယာဉ် (Vehicle)", "nca_vehicle", state_key="show_bs_assets")
    
    # ⭐ Fixed Assets Custom Items
    custom_nca_total = render_bs_custom_items("fixed_assets", "Custom Fixed Assets")

    total_nca = nca_land + nca_building + nca_machine + nca_furniture + nca_vehicle + custom_nca_total
    subtotal_box("ပုံသေ ပိုင်ဆိုင်မှု စုစုပေါင်း" if st.session_state.get("language") == "my" else "Total Fixed Assets", total_nca, "#2e7d32")
    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(f'<h3 style="color: #2e7d32; font-size: 1.15rem; border-bottom: 2px solid #43e97b; padding-bottom: 0.3rem;">{"၂။ လက်ရှိ ပိုင်ဆိုင်မှုများ" if st.session_state.get("language") == "my" else "2. Current Assets"}</h3>', unsafe_allow_html=True)
    ca_inventories = num_input("ကုန်ပစ္စည်းလက်ကျန် (Inventories)", "ca_inventories", state_key="show_bs_assets")
    ca_receivable = num_input("ရရန်ကျန်ငွေ (A/C Receivable)", "ca_receivable", state_key="show_bs_assets")
    ca_advance = num_input("ကြိုတင်ပေးငွေ (Advance Payments)", "ca_advance", state_key="show_bs_assets")
    ca_cash = num_input("လက်ထဲ/ဘဏ် ငွေသား (Cash)", "ca_cash", state_key="show_bs_assets")
    
    # ⭐ Current Assets Custom Items
    custom_ca_total = render_bs_custom_items("current_assets", "Custom Current Assets")

    total_ca = ca_inventories + ca_receivable + ca_advance + ca_cash + custom_ca_total
    subtotal_box("လက်ရှိ ပိုင်ဆိုင်မှု စုစုပေါင်း" if st.session_state.get("language") == "my" else "Total Current Assets", total_ca, "#2e7d32")
    st.markdown("<br>", unsafe_allow_html=True)

    total_assets = total_nca + total_ca
    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); padding: 1.2rem; border-radius: 12px; color: white; margin-top: 1rem;">
            <p style="margin: 0; font-size: 1rem; opacity: 0.95;">📊 {'ပိုင်ဆိုင်မှု စုစုပေါင်း' if st.session_state.get('language') == 'my' else 'Total Assets'}</p>
            <h1 style="margin: 0.4rem 0 0 0; font-size: 1.8rem;">{format_number(total_assets)}</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(f'<h3 style="color: #c2185b; font-size: 1.15rem; border-bottom: 2px solid #f093fb; padding-bottom: 0.3rem;">{"၃။ အရင်း ငွေ (Equity)" if st.session_state.get("language") == "my" else "3. Equity"}</h3>', unsafe_allow_html=True)
    eq_capital = num_input("အရင်း (Capital)", "eq_capital", state_key="show_bs_equity")
    eq_retain = num_input("စုဆောင်း အမြတ် (Retain Earning)", "eq_retain", state_key="show_bs_equity")

    eq_profit = st.number_input(
        "📈 ယခုနှစ် အမြတ် (Profit for the year) — Trading မှ" if st.session_state.get("language") == "my" else "📈 Profit for the year (from Trading)",
        value=int(st.session_state.bs_data.get("eq_profit", auto_net_profit)),
        min_value=-999999999999,
        step=1000,
        format="%d",
        key="bs_eq_profit_input",
        help="Trading & P&L page မှ auto-fill — လိုအပ်ရင် ပြင်လို့ရ" if st.session_state.get("language") == "my" else "Auto-filled from Trading & P&L",
    )
    st.session_state.bs_data["eq_profit"] = eq_profit

    eq_drawing = num_input("ပိုင်ရှင် ထုတ်ယူမှု (Drawing)" if st.session_state.get("language") == "my" else "Drawing", "eq_drawing", is_deduction=True)
    
    # ⭐ Equity Custom Items
    custom_eq_total = render_bs_custom_items("equity", "Custom Equity")
    
    total_equity = eq_capital + eq_retain + eq_profit - eq_drawing + custom_eq_total
    subtotal_box("အရင်း စုစုပေါင်း" if st.session_state.get("language") == "my" else "Total Equity", total_equity, "#c2185b")
    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(f'<h3 style="color: #c2185b; font-size: 1.15rem; border-bottom: 2px solid #f093fb; padding-bottom: 0.3rem;">{"၄။ အကြွေးများ (Liabilities)" if st.session_state.get("language") == "my" else "4. Liabilities"}</h3>', unsafe_allow_html=True)
    liab_bank_loan = num_input("ဘဏ် ချေးငွေ (Bank Loan)", "liab_bank_loan", state_key="show_bs_liab")
    liab_payable = num_input("ပေးရန်ကျန်ငွေ (A/C Payable)", "liab_payable", state_key="show_bs_liab")
    
    # ⭐ Liabilities Custom Items
    custom_liab_total = render_bs_custom_items("liabilities", "Custom Liabilities")

    total_liab = liab_bank_loan + liab_payable + custom_liab_total
    subtotal_box("အကြွေး စုစုပေါင်း" if st.session_state.get("language") == "my" else "Total Liabilities", total_liab, "#c2185b")
    st.markdown("<br>", unsafe_allow_html=True)

    total_eq_liab = total_equity + total_liab
    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 1.2rem; border-radius: 12px; color: white; margin-top: 1rem;">
            <p style="margin: 0; font-size: 1rem; opacity: 0.95;">💰 {'အရင်း + အကြွေး စုစုပေါင်း' if st.session_state.get('language') == 'my' else 'Total Equity & Liabilities'}</p>
            <h1 style="margin: 0.4rem 0 0 0; font-size: 1.8rem;">{format_number(total_eq_liab)}</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    difference = total_assets - total_eq_liab
    is_balanced = abs(difference) < 0.01

    if is_balanced:
        check_color = "#43e97b"
        check_icon = "✓"
        check_text = "ဟန်ချက်ကိုက်ညီပါသည်" if st.session_state.get("language") == "my" else "Balanced"
    else:
        check_color = "#f5576c"
        check_icon = "✗"
        check_text = "ဟန်ချက်မကိုက်ညီပါ" if st.session_state.get("language") == "my" else "Not Balanced"

    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, {check_color} 0%, {check_color}cc 100%); padding: 1.5rem; border-radius: 12px; color: white; margin-bottom: 1rem; text-align: center;">
            <p style="margin: 0; font-size: 3rem;">{check_icon}</p>
            <h3 style="margin: 0.5rem 0 0 0; font-size: 1.2rem;">{check_text}</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    diff_color = "#2e7d32" if is_balanced else "#c62828"
    st.markdown(
        f"""
        <div style="background-color: #f5f5f5; padding: 1rem; border-radius: 8px;">
            <p style="margin: 0 0 0.5rem 0; font-size: 0.85rem; color: #666; font-weight: bold;">📊 {'အသေးစိတ်' if st.session_state.get('language') == 'my' else 'Breakdown'}</p>
            <table style="width: 100%; font-size: 0.9rem;">
                <tr><td>{'ပိုင်ဆိုင်မှု' if st.session_state.get('language') == 'my' else 'Assets'}</td><td style="text-align: right; font-weight: bold;">{format_number(total_assets)}</td></tr>
                <tr><td>{'အရင်း' if st.session_state.get('language') == 'my' else 'Equity'}</td><td style="text-align: right; font-weight: bold;">{format_number(total_equity)}</td></tr>
                <tr><td>{'အကြွေး' if st.session_state.get('language') == 'my' else 'Liabilities'}</td><td style="text-align: right; font-weight: bold;">{format_number(total_liab)}</td></tr>
                <tr style="border-top: 1px solid #ddd;"><td><b>{'အရင်း + အကြွေး' if st.session_state.get('language') == 'my' else 'Equity + Liab'}</b></td><td style="text-align: right; font-weight: bold; color: #c2185b;">{format_number(total_eq_liab)}</td></tr>
                <tr style="border-top: 2px solid {diff_color};"><td><b>{'ကွာဟမှု' if st.session_state.get('language') == 'my' else 'Difference'}</b></td><td style="text-align: right; font-weight: bold; color: {diff_color};">{format_number(difference)}</td></tr>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.session_state.bs_data["_total_assets"] = total_assets
    st.session_state.bs_data["_total_equity"] = total_equity
    st.session_state.bs_data["_total_liab"] = total_liab
    st.session_state.bs_data["_current_assets"] = total_ca
    st.session_state.bs_data["_current_liab"] = total_liab
    st.session_state.bs_data["_cash"] = ca_cash
    st.session_state.bs_data["_depreciation"] = auto_depreciation

# ============================================================
# ACTION BUTTONS
# ============================================================

st.markdown("<br>", unsafe_allow_html=True)
st.divider()

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button(t('save'), use_container_width=True, type="primary"):
        play_click_sound()
        try:
            bs_data = st.session_state.bs_data
            bs_data["ca_inventories"] = ca_inventories
            bs_data["ca_receivable"] = ca_receivable
            bs_data["ca_advance"] = ca_advance
            bs_data["ca_cash"] = ca_cash
            bs_data["nca_land"] = nca_land
            bs_data["nca_building"] = nca_building
            bs_data["nca_machine"] = nca_machine
            bs_data["nca_furniture"] = nca_furniture
            bs_data["nca_vehicle"] = nca_vehicle
            bs_data["liab_payable"] = liab_payable
            bs_data["liab_bank_loan"] = liab_bank_loan
            bs_data["eq_capital"] = eq_capital
            bs_data["eq_retain"] = eq_retain
            bs_data["eq_profit"] = eq_profit
            bs_data["eq_drawing"] = eq_drawing

            data_json = json.dumps(bs_data, ensure_ascii=False)
            db.save_statement(
                client_id=client_id,
                statement_type="balance_sheet",
                period_end=st.session_state.bs_date,
                data_json=data_json,
                custom_data=st.session_state.bs_custom_data, # ⭐ Custom Data ပါ သိမ်းမယ်
            )
            st.success("✓ သိမ်းပြီးပါပြီ" if st.session_state.get("language") == "my" else "✓ Saved successfully")
            st.balloons()
        except Exception as e:
            st.error(f"❌ Error: {e}")

with col2:
    if st.button("📄 PDF", use_container_width=True):
        play_click_sound()
        try:
            pdf_data = dict(st.session_state.bs_data)
            pdf_data["_show_bs_assets"] = st.session_state.show_bs_assets
            pdf_data["_show_bs_equity"] = st.session_state.show_bs_equity
            pdf_data["_show_bs_liab"] = st.session_state.show_bs_liab
            pdf_data["custom_data"] = st.session_state.bs_custom_data # ⭐ PDF ထဲ Custom Data ထည့်မယ်

            pdf_bytes = generate_pdf(
                statement_type="balance_sheet",
                client_name=client_display_name,
                client_id=client_id, 
                business_name=client.get("business_name", ""),       
                business_type=client.get("business_type", ""),
                data=pdf_data,
                as_at_date=st.session_state.bs_date, 
                lang=st.session_state.language,
            )
            st.download_button(
                "⬇️ PDF Download",
                data=pdf_bytes,
                file_name=f"{client['name']}_BalanceSheet.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"❌ PDF Error: {e}")

with col3:
    if st.button("🔄 Reset", use_container_width=True):
        play_click_sound()
        st.session_state.bs_data = {}
        st.session_state.bs_custom_data = {
            "current_assets": [],
            "fixed_assets": [],
            "equity": [],
            "liabilities": []
        }
        st.rerun()

with col4:
    if st.button(t('detail'), use_container_width=True):
        play_click_sound()
        st.switch_page("pages/2_Client_Detail.py")

st.divider()
st.caption(f"📅 {t('as_at_date')}: {format_date_mm(st.session_state.bs_date)}")
st.caption(f"👤 {t('clients')}: {client['name']}")