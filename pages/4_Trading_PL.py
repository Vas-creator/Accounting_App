# pages/4_Trading_PL.py
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
    page_title="Trading & P&L",
    page_icon="💰",
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

# ============================================================
# SESSION STATE & TARGET PERIOD
# ============================================================

# ⭐ Client Detail ကနေ လာတဲ့ ကာလကို အရင်ယူမယ်
target_period = st.session_state.get("target_period")

# ⭐ ဖောက်သည်အသစ်ဖြစ်နေရင် ရှင်းမယ်
if st.session_state.get("current_tpl_client_id") != client_id:
    st.session_state.current_tpl_client_id = client_id
    for k in list(st.session_state.keys()):
        if k.startswith("show_") or k.startswith("tpl_") or k.startswith("custom_"):
            if k != "tpl_period_input":
                del st.session_state[k]
    if "tpl_data" in st.session_state:
        del st.session_state["tpl_data"]
    if "custom_data" in st.session_state:
        del st.session_state["custom_data"]
    if "tpl_period" in st.session_state:
        del st.session_state["tpl_period"]

# ⭐ Target Period ရှိရင် အဲ့ဒါကို သတ်မှတ်မယ်
if target_period:
    st.session_state.tpl_period = target_period
    del st.session_state["target_period"] # သုံးပြီးရင် ဖျက်မယ်
elif "tpl_period" not in st.session_state:
    st.session_state.tpl_period = str(date.today()) # မရှိရင် ဒီနေ့ရက်စွဲ သတ်မှတ်မယ်

# ============================================================
# HISTORY
# ============================================================

history = []
try:
    history = db.get_statement_history(client_id, "trading_pl")
except Exception:
    history = []

history_periods = [h["period_end"] for h in history if h.get("period_end")]
history_periods = sorted(list(set(history_periods)), reverse=True)
# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown(
        f"""
        <div style="text-align: center; padding: 0.5rem 0;">
            <h2 style="color: #1f4788; font-size: 1.3rem; margin: 0;">📊 {t('app_title')}</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()
    if st.button(t('home'), use_container_width=True, key="nav_home"):
        st.switch_page("app.py")
    if st.button(t('clients'), use_container_width=True, key="nav_clients"):
        st.switch_page("pages/1_Clients.py")
    if st.button(t('detail'), use_container_width=True, key="nav_detail"):
        st.switch_page("pages/2_Client_Detail.py")
    if st.button(t('mfg_acc'), use_container_width=True, key="nav_mfg"):
        st.switch_page("pages/3_Manufacturing.py")
    st.divider()
    st.markdown(
        f"""
        <div style="background-color: #e3f2fd; padding: 0.8rem; border-radius: 8px; border-left: 4px solid #1565c0;">
            <p style="margin: 0; font-size: 0.85rem; color: #666;">{'ဖောက်သည်' if st.session_state.get('language', 'my') == 'my' else 'Client'}</p>
            <p style="margin: 0.2rem 0 0 0; font-weight: bold; color: #1565c0;">👤 {client['name']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ============================================================
# HEADER
# ============================================================

st.markdown(
    f"""
    <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 1.2rem 1.5rem; border-radius: 12px; color: white; margin-bottom: 1.5rem;">
        <h1 style="margin: 0; font-size: 1.8rem;">💰 {t('pdf_trading')}</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 0.95rem; opacity: 0.95;">Trading & Profit/Loss — {client['name']}</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# PERIOD & HISTORY
# ============================================================

col_date, col_hist = st.columns([1, 1])

with col_date:
    if "tpl_period" not in st.session_state:
        st.session_state.tpl_period = str(date.today())
    
    try:
        initial_date = date.fromisoformat(st.session_state.tpl_period)
    except Exception:
        initial_date = date.today()
        
    period_end = st.date_input(f"📅 {t('period_end')} (New/Update)", value=initial_date, key="tpl_period_input")
    st.session_state.tpl_period = str(period_end)

with col_hist:
    if history_periods:
        st.markdown("**📜 သိမ်းထားသော ကာလများ (History)**")
        options = ["-- ကာလအသစ် (New) --"] + history_periods
        selected_history = st.selectbox("ကာလဟောင်း ပြန်ကြည့်ရန်", options=options, label_visibility="collapsed")
        
        if selected_history != "-- ကာလအသစ် (New) --":
            if st.session_state.get("selected_history_period") != selected_history:
                st.session_state.selected_history_period = selected_history
                
                existing_hist = db.get_statement(client_id, "trading_pl", period_end=selected_history)
                if existing_hist:
                    raw_data = existing_hist.get("data")
                    if isinstance(raw_data, str):
                        st.session_state.tpl_data = json.loads(raw_data)
                    else:
                        st.session_state.tpl_data = raw_data or {}
                    
                    raw_custom = existing_hist.get("custom_data")
                    if isinstance(raw_custom, str):
                        st.session_state.custom_data = json.loads(raw_custom)
                    else:
                        st.session_state.custom_data = raw_custom or {"revenue": [], "cos": [], "expenses": []}
                    
                    st.session_state.tpl_period = selected_history
                    st.rerun()
    else:
        st.info("သိမ်းထားသော စာရင်း မရှိသေးပါ။")

# ============================================================
# LOAD EXISTING
# ============================================================

if "tpl_data" not in st.session_state:
    existing = db.get_statement(client_id, "trading_pl")
    if existing and existing.get("data"):
        raw_data = existing.get("data")
        if isinstance(raw_data, str):
            st.session_state.tpl_data = json.loads(raw_data)
        else:
            st.session_state.tpl_data = raw_data
    else:
        st.session_state.tpl_data = {}

if "custom_data" not in st.session_state:
    existing = db.get_statement(client_id, "trading_pl")
    if existing and existing.get("custom_data"):
        raw_custom = existing.get("custom_data")
        if isinstance(raw_custom, str):
            st.session_state.custom_data = json.loads(raw_custom)
        else:
            st.session_state.custom_data = raw_custom
    else:
        st.session_state.custom_data = {"revenue": [], "cos": [], "expenses": []}

# ⭐ Custom Cost of Sales Items အတွက် Session State အသစ်
if "tpl_cost_custom" not in st.session_state:
    st.session_state.tpl_cost_custom = {
        "opening_stock": [],
        "purchases": [],
        "closing_stock": []
    }

# Show/Hide State
if "show_revenue" not in st.session_state:
    st.session_state.show_revenue = {"cash_sales": True, "credit_sales": True, "sales_return": True}
if "show_cos" not in st.session_state:
    st.session_state.show_cos = {"opening_stock_finished": True, "purchases": True, "carriage_inward": True, "purchase_return": True, "closing_stock_finished": True}
if "show_expenses" not in st.session_state:
    st.session_state.show_expenses = {"staff_salary": True, "tax_other": True, "electricity": True, "telephone": True, "fuel": True, "repair_maintenance": True, "general_expenses": True, "dep_building": True, "dep_machine": True, "dep_furniture": True, "dep_vehicle": True}
if "show_other_income" not in st.session_state:
    st.session_state.show_other_income = {
        "discount_received": True, "commission_received": True,
        "interest_received": True, "rent_received": True,
        "bad_debt_recovered": True, "misc_income": True
    }

# ============================================================
# TRY TO PULL MANUFACTURING COST
# ============================================================

mfg_production_cost = 0.0
try:
    mfg_existing = db.get_statement(client_id, "manufacturing", period_end=st.session_state.tpl_period)
    if mfg_existing and mfg_existing.get("data"):
        raw_mfg = mfg_existing["data"]
        if isinstance(raw_mfg, str):
            mfg_data = json.loads(raw_mfg)
        else:
            mfg_data = raw_mfg
        mfg_production_cost = float(mfg_data.get("_production_cost", 0.0))
except Exception:
    mfg_production_cost = 0.0

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def num_input(label: str, key: str, is_deduction: bool = False, state_key: str = None) -> float:
    value = st.session_state.tpl_data.get(key, 0.0)
    prefix = "➖ " if is_deduction else ""
    
    col_show, col_input = st.columns([0.5, 9.5])
    with col_show:
        default_show = st.session_state.get(state_key, {}).get(key, True)
        show = st.checkbox(" ", value=default_show, key=f"show_{key}")
        st.session_state[state_key][key] = show
    
    with col_input:
        if show:
            result = st.number_input(
                f"{prefix}{label}", value=int(value) if value else 0,
                min_value=0, step=1000, format="%d", key=f"tpl_{key}",
            )
            st.session_state.tpl_data[key] = result
            return float(result)
        else:
            st.session_state.tpl_data[key] = 0.0
            return 0.0

def subtotal_box(label: str, value: float, color: str = "#1976d2"):
    st.markdown(
        f"""<div style="background-color: {color}20; border-left: 3px solid {color}; padding: 0.6rem 0.8rem; border-radius: 6px; margin: 0.5rem 0;">
            <span style="color: {color}; font-weight: bold;">{label}:</span>
            <span style="float: right; font-weight: bold; color: {color};">{format_number(value)}</span>
        </div>""",
        unsafe_allow_html=True,
    )

def render_custom_items(section_key: str, title: str):
    st.markdown(f"**➕ {title}**")
    
    items = st.session_state.custom_data.get(section_key, [])
    
    for i, item in enumerate(items):
        col_x, col_y, col_z = st.columns([2, 2, 1])
        with col_x:
            item["label"] = st.text_input("Name", value=item.get("label", ""), key=f"{section_key}_label_{i}", label_visibility="collapsed")
        with col_y:
            item["value"] = st.number_input(
                "Amount", value=int(item.get("value", 0)), 
                step=1000, format="%d", key=f"{section_key}_value_{i}", 
                label_visibility="collapsed"
            )
        with col_z:
            if st.button("🗑️", key=f"{section_key}_del_{i}"):
                items.pop(i)
                st.session_state.custom_data[section_key] = items
                st.rerun()
    
    if st.button(f"➕ {'Item ထည့်' if st.session_state.get('language') == 'my' else 'Add Item'}", key=f"add_{section_key}"):
        items.append({"label": "", "value": 0})
        st.session_state.custom_data[section_key] = items
        st.rerun()
    
    total = sum(item.get("value", 0) for item in items)
    if total > 0:
        st.markdown(f"**{'စုစုပေါင်း' if st.session_state.get('language') == 'my' else 'Total'}: {format_number(total)}**")
    
    return total

# ⭐ Cost of Sales အတွက် Custom Item ထည့်တဲ့ Function
def render_cost_custom_items(section_key: str, title: str):
    st.markdown(f"**➕ {title}**")
    items = st.session_state.tpl_cost_custom.get(section_key, [])
    
    for i, item in enumerate(items):
        col_x, col_y, col_z = st.columns([2, 2, 1])
        with col_x:
            item["label"] = st.text_input("Name", value=item.get("label", ""), key=f"tpl_cost_{section_key}_label_{i}", label_visibility="collapsed")
        with col_y:
            item["value"] = st.number_input(
                "Amount", value=int(item.get("value", 0)), 
                step=1000, format="%d", key=f"tpl_cost_{section_key}_value_{i}", 
                label_visibility="collapsed"
            )
        with col_z:
            if st.button("🗑️", key=f"tpl_cost_{section_key}_del_{i}"):
                items.pop(i)
                st.session_state.tpl_cost_custom[section_key] = items
                st.rerun()
    
    if st.button(f"➕ {'Item ထည့်' if st.session_state.get('language') == 'my' else 'Add Item'}", key=f"tpl_cost_add_{section_key}"):
        items.append({"label": "", "value": 0})
        st.session_state.tpl_cost_custom[section_key] = items
        st.rerun()
    
    total = sum(item.get("value", 0) for item in items)
    return total

# ============================================================
# 3 COLUMNS LAYOUT
# ============================================================

col1, col2, col3 = st.columns(3)

# ============================================================
# COLUMN 1 — REVENUE + COST OF SALES
# ============================================================

with col1:
    st.markdown(
        f"""<h3 style="color: #1976d2; font-size: 1.15rem; border-bottom: 2px solid #4facfe; padding-bottom: 0.3rem;">
            {'၁။ အရောင်းများ (Revenue)' if st.session_state.get('language', 'my') == 'my' else '1. Revenue'}
        </h3>""",
        unsafe_allow_html=True,
    )
    rev_cash = num_input("ငွေသား အရောင်း", "cash_sales", state_key="show_revenue")
    rev_credit = num_input("အကြွေး အရောင်း", "credit_sales", state_key="show_revenue")
    rev_return = num_input("အရောင်းပြန်အမ်း", "sales_return", is_deduction=True, state_key="show_revenue")
    
    custom_rev_total = render_custom_items("revenue", "Custom Revenue")
    
    total_revenue = rev_cash + rev_credit - rev_return + custom_rev_total
    subtotal_box("စုစုပေါင်း အရောင်း", total_revenue, "#1976d2")

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(
        f"""<h3 style="color: #1976d2; font-size: 1.15rem; border-bottom: 2px solid #4facfe; padding-bottom: 0.3rem;">
            {'၂။ ရောင်းကုန် ကုန်ကျစရိတ် (Cost of Sales)' if st.session_state.get('language', 'my') == 'my' else '2. Cost of Sales'}
        </h3>""",
        unsafe_allow_html=True,
    )

    mfg_direct_material = st.number_input(
        "🏭 ကုန်ထုတ်လုပ်မှု - Direct Materials",
        value=int(st.session_state.tpl_data.get("mfg_direct_material", 0)),
        min_value=0, step=1000, format="%d", key="tpl_mfg_direct_material",
    )
    st.session_state.tpl_data["mfg_direct_material"] = mfg_direct_material
    
    mfg_direct_labour = st.number_input(
        "🏭 ကုန်ထုတ်လုပ်မှု - Direct Labour",
        value=int(st.session_state.tpl_data.get("mfg_direct_labour", 0)),
        min_value=0, step=1000, format="%d", key="tpl_mfg_direct_labour",
    )
    st.session_state.tpl_data["mfg_direct_labour"] = mfg_direct_labour
    
    mfg_direct_overhead = st.number_input(
        "🏭 ကုန်ထုတ်လုပ်မှု - Direct Overhead",
        value=int(st.session_state.tpl_data.get("mfg_direct_overhead", 0)),
        min_value=0, step=1000, format="%d", key="tpl_mfg_direct_overhead",
    )
    st.session_state.tpl_data["mfg_direct_overhead"] = mfg_direct_overhead
    
    mfg_cost_input = mfg_direct_material + mfg_direct_labour + mfg_direct_overhead
    st.session_state.tpl_data["manufacturing_cost"] = mfg_cost_input

    # ၁။ Opening Stock
    cs_opening = st.number_input(
        "အဖွင့် ကုန်ချောလက်ကျန် (Opening Stock)", 
        value=int(st.session_state.tpl_data.get("opening_stock_finished", 0)),
        min_value=0, step=1000, format="%d", key="cs_opening"
    )
    st.session_state.tpl_data["opening_stock_finished"] = cs_opening
    
    # ⭐ Opening Stock အောက်မှာ Custom Input
    custom_opening_total = render_cost_custom_items("opening_stock", "Custom Opening Stock")
    final_opening_stock = cs_opening + custom_opening_total

    # ၂။ Purchases
    cs_purchases = st.number_input(
        "ကုန်ပစ္စည်းဝယ်ယူမှု (Purchases)", 
        value=int(st.session_state.tpl_data.get("add_purchases", 0)),
        min_value=0, step=1000, format="%d", key="cs_purchases"
    )
    st.session_state.tpl_data["add_purchases"] = cs_purchases
    
    # ⭐ Purchases အောက်မှာ Custom Input
    custom_purchases_total = render_cost_custom_items("purchases", "Custom Purchases")
    final_purchases = cs_purchases + custom_purchases_total
    
    cs_carriage = num_input("သယ်ယူပို့ဆောင်ခ", "carriage_inward", state_key="show_cos")
    cs_return = num_input("ဝယ်ယူမှု ပြန်အမ်း", "purchase_return", is_deduction=True, state_key="show_cos")

    # ၃။ Closing Stock
    cs_closing = st.number_input(
        "အပိတ် ကုန်ချောလက်ကျန် (Less: Closing Stock)", 
        value=int(st.session_state.tpl_data.get("closing_stock_finished", 0)),
        min_value=0, step=1000, format="%d", key="cs_closing"
    )
    st.session_state.tpl_data["closing_stock_finished"] = cs_closing
    
    # ⭐ Closing Stock အောက်မှာ Custom Input
    custom_closing_total = render_cost_custom_items("closing_stock", "Custom Closing Stock")
    final_closing_stock = cs_closing + custom_closing_total

    custom_cos_total = render_custom_items("cos", "Custom Cost of Sales")

    # ⭐ တွက်ချက်မှုမှာ final တန်ဖိုးတွေ သုံးမယ်
    total_cos = (mfg_cost_input + final_opening_stock + final_purchases + cs_carriage - cs_return - final_closing_stock + custom_cos_total)
    subtotal_box("အရောင်း ကုန်ကျစရိတ် စုစုပေါင်း", total_cos, "#1976d2")

    st.markdown("<br>", unsafe_allow_html=True)

    gross_profit = total_revenue - total_cos
    gp_color = "#43e97b" if gross_profit >= 0 else "#f5576c"
    gp_label = ("အမြတ် (Gross Profit)" if gross_profit >= 0 else "အရှုံး (Gross Loss)") if st.session_state.get("language") == "my" else ("Gross Profit" if gross_profit >= 0 else "Gross Loss")

    st.markdown(
        f"""<div style="background: linear-gradient(135deg, {gp_color} 0%, {gp_color}cc 100%); padding: 1.2rem; border-radius: 12px; color: white; margin-top: 1rem;">
            <p style="margin: 0; font-size: 0.95rem; opacity: 0.95;">💰 {gp_label}</p>
            <h2 style="margin: 0.4rem 0 0 0; font-size: 1.8rem;">{format_number(gross_profit)}</h2>
        </div>""",
        unsafe_allow_html=True,
    )

# ============================================================
# COLUMN 2 — ADMIN EXPENSES
# ============================================================

with col2:
    st.markdown(
        f"""<h3 style="color: #c2185b; font-size: 1.15rem; border-bottom: 2px solid #f093fb; padding-bottom: 0.3rem;">
            {'၃။ စီမံ သုံးစွဲမှုများ (Admin Expenses)' if st.session_state.get('language', 'my') == 'my' else '3. Admin Expenses'}
        </h3>""",
        unsafe_allow_html=True,
    )

    exp_salary = num_input("ဝန်ထမ်းခနှင့် အလုပ်သမားခ", "staff_salary", state_key="show_expenses")
    exp_tax = num_input("အခွန်နှင့် အခြား", "tax_other", state_key="show_expenses")
    exp_electricity = num_input("လျှပ်စစ်ခ", "electricity", state_key="show_expenses")
    exp_telephone = num_input("တယ်လီဖုန်းခ", "telephone", state_key="show_expenses")
    exp_fuel = num_input("လောင်စာ", "fuel", state_key="show_expenses")
    exp_repair = num_input("ပြုပြင်ထိန်းသိမ်းမှု", "repair_maintenance", state_key="show_expenses")
    exp_general = num_input("အထွေထွေ သုံးစွဲမှု", "general_expenses", state_key="show_expenses")

    st.markdown(
        f"""<p style="color: #666; font-size: 0.9rem; margin: 0.5rem 0;">
            📉 {'တန်ဖိုးကျဆင်းမှု (Depreciation):' if st.session_state.get('language', 'my') == 'my' else 'Depreciation:'}
        </p>""",
        unsafe_allow_html=True,
    )
    exp_dep_building = num_input("အဆောက်အအုံ", "dep_building", state_key="show_expenses")
    exp_dep_machine = num_input("စက်ပစ္စည်း", "dep_machine", state_key="show_expenses")
    exp_dep_furniture = num_input("ပရိဘောဂ", "dep_furniture", state_key="show_expenses")
    exp_dep_vehicle = num_input("ယာဉ်", "dep_vehicle", state_key="show_expenses")

    total_depreciation = (exp_dep_building + exp_dep_machine + exp_dep_furniture + exp_dep_vehicle)
    
    custom_exp_total = render_custom_items("expenses", "Custom Expenses")

    total_expenses = (exp_salary + exp_tax + exp_electricity + exp_telephone + exp_fuel + exp_repair + exp_general + total_depreciation + custom_exp_total)

    subtotal_box("စီမံ သုံးစွဲမှု စုစုပေါင်း", total_expenses, "#c2185b")
    st.session_state.tpl_data["_depreciation"] = total_depreciation
    st.session_state.tpl_data["_total_expenses"] = total_expenses

# ============================================================
# COLUMN 3 — LIVE CALC & OTHER INCOME
# ============================================================

with col3:
    st.markdown(
        f"""<h3 style="color: #2e7d32; font-size: 1.15rem; border-bottom: 2px solid #43e97b; padding-bottom: 0.3rem;">
            {'အခြား ဝင်ငွေများ (Other Income)' if st.session_state.get('language', 'my') == 'my' else 'Other Income'}
        </h3>""",
        unsafe_allow_html=True,
    )
    
    oi_discount = num_input("လျှော့စျေး ရရှိမှု", "discount_received", state_key="show_other_income")
    oi_commission = num_input("ကော်မရှင် ရရှိမှု", "commission_received", state_key="show_other_income")
    oi_interest = num_input("အတိုးရရှိမှု", "interest_received", state_key="show_other_income")
    oi_rent = num_input("ငှားရမ်းခရရှိမှု", "rent_received", state_key="show_other_income")
    oi_bad_debt = num_input("မစုရှိသောအကြေးပြန်ရ", "bad_debt_recovered", state_key="show_other_income")
    oi_misc = num_input("အထွေထွေဝင်ငွေ", "misc_income", state_key="show_other_income")

    total_other_income = oi_discount + oi_commission + oi_interest + oi_rent + oi_bad_debt + oi_misc
    subtotal_box("အခြား ဝင်ငွေ စုစုပေါင်း", total_other_income, "#2e7d32")

    st.markdown("<br>", unsafe_allow_html=True)

    net_profit = gross_profit + total_other_income - total_expenses
    np_color = "#43e97b" if net_profit >= 0 else "#f5576c"
    np_label = ("အသားတင် အမြတ်" if net_profit >= 0 else "အသားတင် အရှုံး") if st.session_state.get("language") == "my" else ("Net Profit" if net_profit >= 0 else "Net Loss")

    st.markdown(
        f"""<div style="background: linear-gradient(135deg, {np_color} 0%, {np_color}cc 100%); padding: 1.5rem; border-radius: 12px; color: white; margin-bottom: 1rem;">
            <p style="margin: 0; font-size: 1rem; opacity: 0.95;">🎯 {np_label}</p>
            <h1 style="margin: 0.5rem 0 0 0; font-size: 2.2rem;">{format_number(net_profit)}</h1>
        </div>""",
        unsafe_allow_html=True,
    )

    st.session_state.tpl_data["_net_profit"] = net_profit
    st.session_state.tpl_data["_gross_profit"] = gross_profit
    st.session_state.tpl_data["_total_revenue"] = total_revenue
    st.session_state.tpl_data["_total_cos"] = total_cos
    st.session_state.tpl_data["_total_other_income"] = total_other_income

    st.markdown(
        f"""<div style="background-color: #f5f5f5; padding: 1rem; border-radius: 8px; margin-top: 1rem;">
            <p style="margin: 0 0 0.5rem 0; font-size: 0.85rem; color: #666; font-weight: bold;">📊 {'အသေးစိတ်' if st.session_state.get('language', 'my') == 'my' else 'Breakdown'}</p>
            <table style="width: 100%; font-size: 0.9rem;">
                <tr><td>{'အရောင်း' if st.session_state.get('language', 'my') == 'my' else 'Revenue'}</td><td style="text-align: right; font-weight: bold;">{format_number(total_revenue)}</td></tr>
                <tr><td>{'ကုန်ကျစရိတ်' if st.session_state.get('language', 'my') == 'my' else 'Cost of Sales'}</td><td style="text-align: right; font-weight: bold; color: #c62828;">({format_number(total_cos)})</td></tr>
                <tr style="border-top: 1px solid #ddd;"><td><b>Gross Profit</b></td><td style="text-align: right; font-weight: bold; color: #1976d2;">{format_number(gross_profit)}</td></tr>
                <tr><td>{'အခြားဝင်ငွေ' if st.session_state.get('language', 'my') == 'my' else 'Other Income'}</td><td style="text-align: right; font-weight: bold; color: #2e7d32;">{format_number(total_other_income)}</td></tr>
                <tr><td>{'သုံးစွဲမှု' if st.session_state.get('language', 'my') == 'my' else 'Expenses'}</td><td style="text-align: right; font-weight: bold; color: #c62828;">({format_number(total_expenses)})</td></tr>
                <tr style="border-top: 2px solid {np_color};"><td><b>Net Profit</b></td><td style="text-align: right; font-weight: bold; color: {np_color}; font-size: 1.05rem;">{format_number(net_profit)}</td></tr>
            </table>
        </div>""",
        unsafe_allow_html=True,
    )

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
            data_json = json.dumps(st.session_state.tpl_data, ensure_ascii=False)
            
            # ⭐ Custom Data နှစ်မျိုးလုံးကို ပေါင်းပြီး သိမ်းမယ်
            combined_custom = dict(st.session_state.custom_data)
            combined_custom.update(st.session_state.tpl_cost_custom)
            
            db.save_statement(
                client_id=client_id,
                statement_type="trading_pl",
                period_end=st.session_state.tpl_period,
                data_json=data_json,
                custom_data=combined_custom,
            )
            st.success("✓ သိမ်းပြီးပါပြီ" if st.session_state.get("language") == "my" else "✓ Saved successfully")
            st.balloons()
        except Exception as e:
            st.error(f"❌ Save Error: {e}")
            st.exception(e) 

with col2:
    if st.button("📄 PDF", use_container_width=True):
        play_click_sound()
        try:
            # ၁။ UI မှာ ဖြည့်ထားတဲ့ တန်ဖိုးတွေကို အရင်ယူမယ်
            pdf_data = dict(st.session_state.tpl_data)
            
            # ⭐ UI မှာ ဖြည့်ထားတဲ့ တန်ဖိုးတွေကို pdf_data ထဲ တိုက်ရိုက်ထည့်မယ်
            pdf_data["opening_stock_finished"] = final_opening_stock
            pdf_data["add_purchases"] = final_purchases
            pdf_data["closing_stock_finished"] = final_closing_stock
            
            # Custom Data တွေကိုလည်း ထည့်မယ်
            combined_custom = dict(st.session_state.custom_data)
            combined_custom.update(st.session_state.tpl_cost_custom)
            pdf_data["custom_data"] = combined_custom
            
            # Checkbox အနေအထားတွေ ထည့်မယ်
            pdf_data["_show_revenue"] = st.session_state.show_revenue
            pdf_data["_show_cos"] = st.session_state.show_cos
            pdf_data["_show_expenses"] = st.session_state.show_expenses
            pdf_data["_show_other_income"] = st.session_state.show_other_income
            
            # Manufacturing Cost အကွက် ၃ ခုကို ထည့်မယ်
            pdf_data["mfg_direct_material"] = st.session_state.tpl_data.get("mfg_direct_material", 0)
            pdf_data["mfg_direct_labour"] = st.session_state.tpl_data.get("mfg_direct_labour", 0)
            pdf_data["mfg_direct_overhead"] = st.session_state.tpl_data.get("mfg_direct_overhead", 0)
            
            # ကုန်ပစ္စည်းဝယ်ယူမှု၊ သယ်ယူပို့ဆောင်ခ တွေကို ထည့်မယ်
            pdf_data["purchases"] = cs_purchases
            pdf_data["carriage_inward"] = cs_carriage
            pdf_data["add_carriage_inward"] = cs_carriage
            pdf_data["add_manufacturing_cost"] = mfg_cost_input
            
            # Total တွေကို ထည့်မယ်
            pdf_data["_total_revenue"] = total_revenue
            pdf_data["_total_cos"] = total_cos
            pdf_data["_gross_profit"] = gross_profit
            pdf_data["_total_expenses"] = total_expenses
            pdf_data["_net_profit"] = net_profit

            # ၂။ PDF ကို ဆောက်မယ်
            pdf_bytes = generate_pdf(
                statement_type="trading_pl",
                client_name=client["name"],
                client_id=st.session_state.get("selected_client_id"),
                business_name=client.get("business_name", ""),
                business_type=client.get("business_type", ""),
                data=pdf_data,
                period_end=st.session_state.tpl_period,
                lang=st.session_state.language,
            )

            st.download_button(
                "⬇️ PDF Download",
                data=pdf_bytes,
                file_name=f"{client['name']}_TradingPL_{st.session_state.tpl_period}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"❌ PDF Error: {e}")

with col3:
    if st.button("🔄 Reset", use_container_width=True):
        play_click_sound()
        st.session_state.tpl_data = {}
        st.session_state.custom_data = {"revenue": [], "cos": [], "expenses": []}
        st.session_state.tpl_cost_custom = {"opening_stock": [], "purchases": [], "closing_stock": []}
        st.rerun()

with col4:
    if st.button(t('detail'), use_container_width=True):
        play_click_sound()
        st.switch_page("pages/2_Client_Detail.py")

# ============================================================
# FOOTER
# ============================================================

st.divider()
st.caption(f"📅 {t('period_end')}: {format_date_mm(st.session_state.tpl_period)}")
st.caption(f"👤 {t('clients')}: {client['name']}")