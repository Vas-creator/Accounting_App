# pages/3_Manufacturing.py
"""
Manufacturing Account — ကုန်ထုတ်လုပ်မှု စာရင်း
Real-time calculation + Save to DB + PDF Export + History
"""

import streamlit as st
import json
from datetime import date

from core import db
from core.utils import (
    format_number, format_currency, format_date_mm,
    info_box, parse_number
)
from core.templates import get_input_fields
from core.pdf_generator import generate_pdf, calculate_manufacturing
from core.translations import t

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Manufacturing",
    page_icon="🏭",
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
# SESSION STATE (ဖောက်သည်ပြောင်းရင် ရှင်းမယ်)
# ============================================================

if st.session_state.get("current_mfg_client_id") != client_id:
    st.session_state.current_mfg_client_id = client_id
    if "mfg_data" in st.session_state:
        del st.session_state["mfg_data"]
    if "mfg_custom_data" in st.session_state:
        del st.session_state["mfg_custom_data"]
    if "mfg_period" in st.session_state:
        del st.session_state["mfg_period"]
    for k in list(st.session_state.keys()):
        if k.startswith("mfg_show_") or k.startswith("mfg_"):
            if k != "mfg_period_input":
                del st.session_state[k]

# ============================================================
# HISTORY: ကာလအလိုက် စာရင်းဟောင်းများ ရယူခြင်း
# ============================================================

history = []
try:
    history = db.get_statement_history(client_id, "manufacturing")
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
                👤 {client['name']}
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
    <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 1.2rem 1.5rem; border-radius: 12px; color: white; margin-bottom: 1.5rem;">
        <h1 style="margin: 0; font-size: 1.8rem;">
            🏭 {t('pdf_mfg')}
        </h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 0.95rem; opacity: 0.95;">
            Manufacturing Account — {client['name']}
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# PERIOD & HISTORY
# ============================================================

col_date, col_hist = st.columns([1, 1])

with col_date:
    if "mfg_period" not in st.session_state:
        st.session_state.mfg_period = str(date.today())

    try:
        initial_date = date.fromisoformat(st.session_state.mfg_period)
    except Exception:
        initial_date = date.today()

    period_end = st.date_input(
        f"📅 {t('period_end')} (New/Update)",
        value=initial_date,
        key="mfg_period_input",
    )
    st.session_state.mfg_period = str(period_end)

with col_hist:
    if history_periods:
        st.markdown("**📜 သိမ်းထားသော ကာလများ (History)**")
        options = ["-- ကာလအသစ် (New) --"] + history_periods
        selected_history = st.selectbox("ကာလဟောင်း ပြန်ကြည့်ရန်", options=options, label_visibility="collapsed")

        if selected_history != "-- ကာလအသစ် (New) --":
            if st.session_state.get("selected_mfg_history") != selected_history:
                st.session_state.selected_mfg_history = selected_history

                existing_hist = db.get_statement(client_id, "manufacturing", period_end=selected_history)
                if existing_hist:
                    raw_data = existing_hist.get("data")
                    if isinstance(raw_data, str):
                        st.session_state.mfg_data = json.loads(raw_data)
                    else:
                        st.session_state.mfg_data = raw_data or {}

                    raw_custom = existing_hist.get("custom_data")
                    if isinstance(raw_custom, str):
                        st.session_state.mfg_custom_data = json.loads(raw_custom)
                    else:
                        st.session_state.mfg_custom_data = raw_custom or {
                            "direct_materials": [], 
                            "direct_labour": [], 
                            "direct_expenses": [], 
                            "factory_overhead": []
                        }

                    st.session_state.mfg_period = selected_history
                    st.rerun()
    else:
        st.info("သိမ်းထားသော စာရင်း မရှိသေးပါ။")

# ============================================================
# LOAD EXISTING (If New period)
# ============================================================

if "mfg_data" not in st.session_state:
    existing = db.get_statement(client_id, "manufacturing")
    if existing and existing.get("data"):
        raw_data = existing.get("data")
        if isinstance(raw_data, str):
            st.session_state.mfg_data = json.loads(raw_data)
        else:
            st.session_state.mfg_data = raw_data
    else:
        st.session_state.mfg_data = {}

if "mfg_custom_data" not in st.session_state:
    existing = db.get_statement(client_id, "manufacturing")
    if existing and existing.get("custom_data"):
        raw_custom = existing.get("custom_data")
        if isinstance(raw_custom, str):
            st.session_state.mfg_custom_data = json.loads(raw_custom)
        else:
            st.session_state.mfg_custom_data = raw_custom
    else:
        st.session_state.mfg_custom_data = {
            "direct_materials": [], 
            "direct_labour": [], 
            "direct_expenses": [], 
            "factory_overhead": []
        }

# Show/Hide State များ
if "mfg_show_dm" not in st.session_state:
    st.session_state.mfg_show_dm = {
        "opening_stock_raw": True, "purchases_raw": True, 
        "carriage_inward": True, "customs_duty": True, "closing_stock_raw": True
    }
if "mfg_show_dl" not in st.session_state:
    st.session_state.mfg_show_dl = {"wages_direct": True, "wages_overtime": True, "wages_contract": True}
if "mfg_show_de" not in st.session_state:
    st.session_state.mfg_show_de = {"royalty": True, "hire_plant": True, "fuel_power_direct": True}
if "mfg_show_fo" not in st.session_state:
    st.session_state.mfg_show_fo = {
        "factory_rent": True, "factory_rates": True, "factory_insurance": True,
        "factory_power": True, "factory_salary": True, "depreciation_plant": True,
        "repairs_plant": True, "indirect_wages": True, "factory_misc": True
    }
if "mfg_show_wip" not in st.session_state:
    st.session_state.mfg_show_wip = {"add_opening_wip": True, "less_closing_wip": True}

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def mfg_num_input(label: str, key: str, is_deduction: bool = False, state_key: str = None) -> float:
    value = st.session_state.mfg_data.get(key, 0.0)
    prefix = "➖ " if is_deduction else ""
    
    col_show, col_input = st.columns([0.5, 9.5])
    with col_show:
        default_show = st.session_state.get(state_key, {}).get(key, True)
        show = st.checkbox("", value=default_show, key=f"mfg_show_{key}", label_visibility="collapsed")
        st.session_state[state_key][key] = show
    
    with col_input:
        if show:
            result = st.number_input(
                f"{prefix}{label}", value=int(value) if value else 0,
                min_value=0, step=1000, format="%d", key=f"mfg_input_{key}",
            )
            st.session_state.mfg_data[key] = result
            return float(result)
        else:
            st.session_state.mfg_data[key] = 0.0
            return 0.0

def render_mfg_custom_items(section_key: str, title: str):
    st.markdown(f"**➕ {title}**")
    items = st.session_state.mfg_custom_data.get(section_key, [])
    
    for i, item in enumerate(items):
        col_x, col_y, col_z = st.columns([2, 2, 1])
        with col_x:
            item["label"] = st.text_input("Name", value=item.get("label", ""), key=f"mfg_{section_key}_label_{i}", label_visibility="collapsed")
        with col_y:
            item["value"] = st.number_input(
                "Amount", value=int(item.get("value", 0)), 
                step=1000, format="%d", key=f"mfg_{section_key}_value_{i}", 
                label_visibility="collapsed"
            )
        with col_z:
            if st.button("🗑️", key=f"mfg_{section_key}_del_{i}"):
                items.pop(i)
                st.session_state.mfg_custom_data[section_key] = items
                st.rerun()
    
    if st.button(f"➕ {'Item ထည့်' if st.session_state.get('language') == 'my' else 'Add Item'}", key=f"mfg_add_{section_key}"):
        items.append({"label": "", "value": 0})
        st.session_state.mfg_custom_data[section_key] = items
        st.rerun()
    
    total = sum(item.get("value", 0) for item in items)
    if total > 0:
        st.markdown(f"**{'စုစုပေါင်း' if st.session_state.get('language') == 'my' else 'Total'}: {format_number(total)}**")
    return total

def subtotal_box(label: str, value: float, color: str = "#1976d2"):
    st.markdown(f"""
        <div style="background-color: {color}20; border-left: 3px solid {color}; padding: 0.6rem 0.8rem; border-radius: 6px; margin: 0.5rem 0;">
            <span style="color: {color}; font-weight: bold;">{label}:</span>
            <span style="float: right; font-weight: bold; color: {color};">{format_number(value)}</span>
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# 2 COLUMNS LAYOUT
# ============================================================

col1, col2 = st.columns(2)

# ============================================================
# COLUMN 1 — DIRECT MATERIALS, LABOUR, EXPENSES
# ============================================================

with col1:
    st.markdown(f'<h3 style="color: #1976d2; font-size: 1.15rem; border-bottom: 2px solid #4facfe; padding-bottom: 0.3rem;">{"၁။ တိုက်ရိုက် ကုန်ကြမ်းများ" if st.session_state.get("language") == "my" else "1. Direct Materials"}</h3>', unsafe_allow_html=True)
    dm_opening = mfg_num_input("အဖွင့် ကုန်ကြမ်းလက်ကျန်", "opening_stock_raw", state_key="mfg_show_dm")
    dm_purchases = mfg_num_input("ကုန်ကြမ်းဝယ်ယူမှု", "purchases_raw", state_key="mfg_show_dm")
    dm_carriage = mfg_num_input("သယ်ယူပို့ဆောင်ခ", "carriage_inward", state_key="mfg_show_dm")
    dm_customs = mfg_num_input("အကောက်ခွန်", "customs_duty", state_key="mfg_show_dm")
    dm_closing = mfg_num_input("အပိတ် ကုန်ကြမ်းလက်ကျန်", "closing_stock_raw", is_deduction=True, state_key="mfg_show_dm")
    
    custom_dm_total = render_mfg_custom_items("direct_materials", "Custom Direct Materials")
    total_dm = dm_opening + dm_purchases + dm_carriage + dm_customs - dm_closing + custom_dm_total
    subtotal_box("အသုံးပြုသော ကုန်ကြမ်းကုန်ကျစရိတ်", total_dm, "#1976d2")
    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(f'<h3 style="color: #1976d2; font-size: 1.15rem; border-bottom: 2px solid #4facfe; padding-bottom: 0.3rem;">{"၂။ တိုက်ရိုက် အလုပ်သမားခ" if st.session_state.get("language") == "my" else "2. Direct Labour"}</h3>', unsafe_allow_html=True)
    dl_wages = mfg_num_input("တိုက်ရိုက် အလုပ်သမားခ", "wages_direct", state_key="mfg_show_dl")
    dl_ot = mfg_num_input("အချိန်ပို အလုပ်သမားခ", "wages_overtime", state_key="mfg_show_dl")
    dl_contract = mfg_num_input("စာချုပ် အလုပ်သမားခ", "wages_contract", state_key="mfg_show_dl")
    
    custom_dl_total = render_mfg_custom_items("direct_labour", "Custom Direct Labour")
    total_dl = dl_wages + dl_ot + dl_contract + custom_dl_total
    subtotal_box("တိုက်ရိုက် အလုပ်သမားခ စုစုပေါင်း", total_dl, "#1976d2")
    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(f'<h3 style="color: #1976d2; font-size: 1.15rem; border-bottom: 2px solid #4facfe; padding-bottom: 0.3rem;">{"၃။ တိုက်ရိုက် အသုံးစရိတ်များ" if st.session_state.get("language") == "my" else "3. Direct Expenses"}</h3>', unsafe_allow_html=True)
    de_royalty = mfg_num_input("မူပိုင်ခွင့်ကြေး", "royalty", state_key="mfg_show_de")
    de_hire = mfg_num_input("စက်ပစ္စည်း ငှားရမ်းခ", "hire_plant", state_key="mfg_show_de")
    de_fuel = mfg_num_input("လောင်စာနှင့် လျှပ်စစ်", "fuel_power_direct", state_key="mfg_show_de")
    
    custom_de_total = render_mfg_custom_items("direct_expenses", "Custom Direct Expenses")
    total_de = de_royalty + de_hire + de_fuel + custom_de_total
    subtotal_box("တိုက်ရိုက် အသုံးစရိတ် စုစုပေါင်း", total_de, "#1976d2")
    st.markdown("<br>", unsafe_allow_html=True)

    prime_cost = total_dm + total_dl + total_de
    st.markdown(f"""
        <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 1.2rem; border-radius: 12px; color: white; margin-top: 1rem;">
            <p style="margin: 0; font-size: 1rem; opacity: 0.95;">💵 {'အခြေခံ ကုန်ကျစရိတ် (Prime Cost)' if st.session_state.get('language') == 'my' else 'Prime Cost'}</p>
            <h1 style="margin: 0.4rem 0 0 0; font-size: 1.8rem;">{format_number(prime_cost)}</h1>
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# COLUMN 2 — FACTORY OVERHEAD + WIP + PRODUCTION COST
# ============================================================

with col2:
    st.markdown(f'<h3 style="color: #c2185b; font-size: 1.15rem; border-bottom: 2px solid #f093fb; padding-bottom: 0.3rem;">{"၄။ စက်ရုံ အသုံးစရိတ်များ" if st.session_state.get("language") == "my" else "4. Factory Overhead"}</h3>', unsafe_allow_html=True)
    fo_rent = mfg_num_input("စက်ရုံ ငှားရမ်းခ", "factory_rent", state_key="mfg_show_fo")
    fo_rates = mfg_num_input("စက်ရုံ အခွန်", "factory_rates", state_key="mfg_show_fo")
    fo_ins = mfg_num_input("စက်ရုံ အာမခံ", "factory_insurance", state_key="mfg_show_fo")
    fo_power = mfg_num_input("စက်ရုံ လျှပ်စစ်", "factory_power", state_key="mfg_show_fo")
    fo_salary = mfg_num_input("စက်ရုံ ဝန်ထမ်းခ", "factory_salary", state_key="mfg_show_fo")
    fo_dep = mfg_num_input("စက်ပစ္စည်း တန်ဖိုးကျဆင်း", "depreciation_plant", state_key="mfg_show_fo")
    fo_repairs = mfg_num_input("စက်ပစ္စည်း ပြုပြင်ခ", "repairs_plant", state_key="mfg_show_fo")
    fo_indirect = mfg_num_input("သွယ်ဝိုက် အလုပ်သမားခ", "indirect_wages", state_key="mfg_show_fo")
    fo_misc = mfg_num_input("အထွေထွေ စက်ရုံစရိတ်", "factory_misc", state_key="mfg_show_fo")
    
    custom_fo_total = render_mfg_custom_items("factory_overhead", "Custom Factory Overhead")
    total_fo = fo_rent + fo_rates + fo_ins + fo_power + fo_salary + fo_dep + fo_repairs + fo_indirect + fo_misc + custom_fo_total
    subtotal_box("စက်ရုံ အသုံးစရိတ် စုစုပေါင်း", total_fo, "#c2185b")
    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(f'<h3 style="color: #c2185b; font-size: 1.15rem; border-bottom: 2px solid #f093fb; padding-bottom: 0.3rem;">{"၅။ လုပ်ငန်း ဆောင်ရွက်ဆဲ (WIP)" if st.session_state.get("language") == "my" else "5. Work in Progress"}</h3>', unsafe_allow_html=True)
    wip_opening = mfg_num_input("အဖွင့် WIP", "add_opening_wip", state_key="mfg_show_wip")
    wip_closing = mfg_num_input("အပိတ် WIP", "less_closing_wip", is_deduction=True, state_key="mfg_show_wip")
    
    subtotal_box("WIP ပြောင်းလဲမှု", wip_opening - wip_closing, "#c2185b")
    st.markdown("<br>", unsafe_allow_html=True)

    production_cost = prime_cost + total_fo + wip_opening - wip_closing
    st.markdown(f"""
        <div style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); padding: 1.5rem; border-radius: 12px; color: white; margin-top: 1rem;">
            <p style="margin: 0; font-size: 1rem; opacity: 0.95;">🎯 {'ကုန်ထုတ်လုပ်မှု ကုန်ကျစရိတ် (Production Cost)' if st.session_state.get('language') == 'my' else 'Production Cost'}</p>
            <h1 style="margin: 0.5rem 0 0 0; font-size: 2.2rem;">{format_number(production_cost)}</h1>
        </div>
        """, unsafe_allow_html=True)

    st.session_state.mfg_data["_production_cost"] = production_cost
    st.session_state.mfg_data["_total_dm"] = total_dm
    st.session_state.mfg_data["_total_dl"] = total_dl
    st.session_state.mfg_data["_total_de"] = total_de
    st.session_state.mfg_data["_total_fo"] = total_fo

# ============================================================
# ACTION BUTTONS
# ============================================================

st.markdown("<br>", unsafe_allow_html=True)
st.divider()

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button(t('save'), use_container_width=True, type="primary"):
        try:
            data_json = json.dumps(st.session_state.mfg_data, ensure_ascii=False)
            db.save_statement(
                client_id=client_id,
                statement_type="manufacturing",
                period_end=st.session_state.mfg_period,
                data_json=data_json,
                custom_data=st.session_state.mfg_custom_data,
            )
            st.success("✓ သိမ်းပြီးပါပြီ" if st.session_state.get("language") == "my" else "✓ Saved successfully")
            st.balloons()
        except Exception as e:
            st.error(f"❌ Save Error: {e}")

with col2:
    if st.button("📄 PDF", use_container_width=True):
        try:
            pdf_data = dict(st.session_state.mfg_data)
            pdf_data["custom_data"] = st.session_state.mfg_custom_data
            
            pdf_bytes = generate_pdf(
                statement_type="manufacturing",
                client_name=client["name"],
                data=pdf_data,
                period_end=st.session_state.mfg_period,
                lang=st.session_state.language,
                business_type=client.get("business_type", ""),  # ⭐ ဒါလေး ထည့်မယ်
            )
            st.download_button(
                "⬇️ PDF Download",
                data=pdf_bytes,
                file_name=f"{client['name']}_Manufacturing_{st.session_state.mfg_period}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"❌ PDF Error: {e}")

with col3:
    if st.button("🔄 Reset", use_container_width=True):
        st.session_state.mfg_data = {}
        st.session_state.mfg_custom_data = {
            "direct_materials": [], 
            "direct_labour": [], 
            "direct_expenses": [], 
            "factory_overhead": []
        }
        st.rerun()

with col4:
    if st.button(t('detail'), use_container_width=True):
        st.switch_page("pages/2_Client_Detail.py")

# ============================================================
# FOOTER INFO
# ============================================================

st.divider()
st.caption(f"📅 {t('period_end')}: {format_date_mm(st.session_state.mfg_period)}")
st.caption(f"👤 {t('clients')}: {client['name']}")