
"""
Cash Flow Statement — ငွေသား စီးဆင်းမှု ရှင်းတမ်း
Indirect Method
"""

import streamlit as st
import json
from datetime import date

from core import db
from core.utils import format_number, format_date_mm, play_click_sound
from core.pdf_generator import generate_pdf
from core.translations import t


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Cash Flow Statement",
    page_icon="💵",
    layout="wide",
)


# ============================================================
# HELPERS
# ============================================================

NEW_PERIOD_LABEL = "-- ကာလအသစ် (New) --"


def parse_json_data(raw_data):
    """JSON string သို့မဟုတ် dict ကို လုံခြုံစွာ dict ပြောင်းပေးရန်။"""
    if isinstance(raw_data, dict):
        return raw_data.copy()

    if isinstance(raw_data, str):
        try:
            parsed = json.loads(raw_data)
            return parsed if isinstance(parsed, dict) else {}
        except (json.JSONDecodeError, TypeError):
            return {}

    return {}


def clear_cf_widget_state(keep_period=True):
    """
    ကာလပြောင်းသည့်အခါ input widget အဟောင်းများကို ရှင်းရန်။
    Period input နှင့် history selector ကို မရှင်းပါ။
    """
    protected_keys = {
        "cf_period_input",
        "cf_history_selector",
        "selected_cf_history",
    }

    for key in list(st.session_state.keys()):
        if key.startswith("cf_") and key not in protected_keys:
            del st.session_state[key]


def load_cf_period(period_string):
    """ရွေးထားသော period အတွက် Cash Flow row ကိုသာ load လုပ်ရန်။"""
    clear_cf_widget_state()

    st.session_state.cf_period = period_string

    existing = db.get_statement(
        client_id,
        "cash_flow",
        period_end=period_string,
    )

    if existing:
        st.session_state.cf_data = parse_json_data(
            existing.get("data")
        )
    else:
        st.session_state.cf_data = {}

    st.session_state._cf_loaded_period = period_string


def safe_number(value):
    try:
        return float(value or 0)
    except (ValueError, TypeError):
        return 0.0


# ============================================================
# AUTH + CLIENT CHECK
# ============================================================

if not st.session_state.get("authentication_status"):
    st.warning(
        "⚠️ ကျေးဇူးပြု၍ အရင် ဝင်ရောက်ပါ"
        if st.session_state.get("language", "my") == "my"
        else "⚠️ Please login first"
    )
    st.switch_page("app.py")
    st.stop()


client_id = st.session_state.get("selected_client_id")

if not client_id:
    st.warning(
        "⚠️ ဖောက်သည် မရွေးရသေးပါ"
        if st.session_state.get("language", "my") == "my"
        else "⚠️ No client selected"
    )

    if st.button(
        "← ဖောက်သည် စာရင်းသို့ ပြန်"
        if st.session_state.get("language", "my") == "my"
        else "← Back to Clients"
    ):
        st.switch_page("pages/1_Clients.py")

    st.stop()


try:
    client = db.get_client(client_id)
except Exception as e:
    st.error(f"❌ Database error: {e}")
    st.stop()


if not client:
    st.error(
        "❌ ဖောက်သည် မတွေ့ပါ"
        if st.session_state.get("language", "my") == "my"
        else "❌ Client not found"
    )
    st.stop()


# ============================================================
# SESSION STATE — CLIENT CHANGE
# ============================================================

if st.session_state.get("current_cf_client_id") != client_id:

    for key in list(st.session_state.keys()):
        if key.startswith("cf_") or key.startswith("_cf_"):
            del st.session_state[key]

    st.session_state.current_cf_client_id = client_id
    st.session_state.cf_period = str(date.today())


# ============================================================
# TARGET PERIOD
# ============================================================

target_period = st.session_state.pop("target_period", None)

if target_period:
    try:
        target_period = str(date.fromisoformat(str(target_period)))
        st.session_state.cf_period = target_period
        st.session_state.cf_period_input = date.fromisoformat(target_period)
        st.session_state.pop("_cf_loaded_period", None)
    except (ValueError, TypeError):
        pass


if "cf_period" not in st.session_state:
    st.session_state.cf_period = str(date.today())


# ============================================================
# HISTORY
# ============================================================

history = []

try:
    history = db.get_statement_history(client_id, "cash_flow") or []
except Exception:
    history = []


history_periods = sorted(
    {
        str(item["period_end"])
        for item in history
        if item.get("period_end")
    },
    reverse=True,
)


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

    if st.button(t("home"), use_container_width=True):
        st.switch_page("app.py")

    if st.button(t("clients"), use_container_width=True):
        st.switch_page("pages/1_Clients.py")

    if st.button(t("detail"), use_container_width=True):
        st.switch_page("pages/2_Client_Detail.py")

    st.divider()

    st.markdown(
        f"""
        <div style="background-color: #e3f2fd; padding: 0.8rem;
                    border-radius: 8px; border-left: 4px solid #1565c0;">
            <p style="margin: 0; font-size: 0.85rem; color: #666;">
                {'ဖောက်သည်' if st.session_state.get('language', 'my') == 'my' else 'Client'}
            </p>
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
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 1.2rem 1.5rem; border-radius: 12px;
                color: white; margin-bottom: 1.5rem;">
        <h1 style="margin: 0; font-size: 1.8rem;">
            💵 {t('pdf_cashflow')}
        </h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 0.95rem; opacity: 0.95;">
            Cash Flow Statement — {client['name']}
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# PERIOD & HISTORY SELECTION
# ============================================================

col_date, col_hist = st.columns([1, 1])

with col_hist:

    if history_periods:

        st.markdown("**📜 သိမ်းထားသော ကာလများ (History)**")

        history_options = [NEW_PERIOD_LABEL] + history_periods

        selected_history = st.selectbox(
            "ကာလဟောင်း ပြန်ကြည့်ရန်",
            options=history_options,
            key="cf_history_selector",
            label_visibility="collapsed",
        )

        previous_history = st.session_state.get(
            "selected_cf_history",
            NEW_PERIOD_LABEL,
        )

        if selected_history != previous_history:

            st.session_state.selected_cf_history = selected_history

            if selected_history != NEW_PERIOD_LABEL:

                selected_date = date.fromisoformat(selected_history)

                st.session_state.cf_period_input = selected_date
                st.session_state.cf_period = selected_history

                load_cf_period(selected_history)
                st.rerun()

            else:
                # New ကိုရွေးလိုက်လျှင် ယခင် data မသယ်သွားရန်
                st.session_state.pop("_cf_loaded_period", None)

                current_period = st.session_state.get(
                    "cf_period",
                    str(date.today()),
                )

                clear_cf_widget_state()
                st.session_state.cf_period = current_period
                st.session_state.cf_period_input = date.fromisoformat(
                    current_period
                )

                st.rerun()

    else:
        st.info("သိမ်းထားသော စာရင်း မရှိသေးပါ။")


with col_date:

    try:
        initial_date = date.fromisoformat(
            st.session_state.cf_period
        )
    except (ValueError, TypeError):
        initial_date = date.today()

    if "cf_period_input" not in st.session_state:
        st.session_state.cf_period_input = initial_date

    period_end = st.date_input(
        f"📅 {t('period_end')} (New/Update)",
        key="cf_period_input",
    )

    period_string = str(period_end)


# ============================================================
# LOAD DATA FOR SELECTED PERIOD
# ============================================================

loaded_period = st.session_state.get("_cf_loaded_period")

if loaded_period != period_string:

    try:
        load_cf_period(period_string)
    except Exception as e:
        st.error(f"❌ Cash Flow load error: {e}")
        st.stop()

    st.rerun()


st.session_state.cf_period = period_string

if "cf_data" not in st.session_state:
    st.session_state.cf_data = {}


# ============================================================
# AUTO DATA — SAME ACCOUNTING PERIOD ONLY
# ============================================================

auto_net_profit = 0.0
auto_depreciation = 0.0
auto_bs = {}


# Trading P&L
try:
    tpl_existing = db.get_statement(
        client_id,
        "trading_pl",
        period_end=period_string,
    )

    if tpl_existing:
        tpl_data = parse_json_data(tpl_existing.get("data"))

        auto_net_profit = safe_number(
            tpl_data.get("_net_profit", 0)
        )

        auto_depreciation = safe_number(
            tpl_data.get("_depreciation", 0)
        )

except Exception:
    pass


# Balance Sheet
try:
    bs_existing = db.get_statement(
        client_id,
        "balance_sheet",
        period_end=period_string,
    )

    if bs_existing:
        auto_bs = parse_json_data(bs_existing.get("data"))

except Exception:
    auto_bs = {}


# ============================================================
# DEFAULT DATA
# ============================================================

cf = st.session_state.cf_data

defaults = {
    "opening_cash": 0,
    "opening_inventories": 0,
    "opening_receivable": 0,
    "opening_payable": 0,
    "opening_deposits": 0,
    "opening_prepayments": 0,
    "opening_other_assets": 0,
    "opening_deferred": 0,
    "net_profit": int(auto_net_profit),
    "depreciation": int(auto_depreciation),
    "amortization": 0,
    "retain_earning_change": 0,
    "change_inventories": 0,
    "change_receivable": 0,
    "change_payable": 0,
    "change_prepayment": 0,
    "investing_purchase_fa": 0,
    "financing_drawing": 0,
}

for key, value in defaults.items():
    if key not in cf:
        cf[key] = value


# ============================================================
# 3 COLUMNS LAYOUT
# ============================================================

col1, col2, col3 = st.columns(3)


# ============================================================
# COLUMN 1 — OPERATING ACTIVITIES
# ============================================================

with col1:

    st.markdown(
        f"""
        <h3 style="color: #1565c0; font-size: 1.1rem;
                   border-bottom: 2px solid #4facfe; padding-bottom: 0.3rem;">
            {'A. OPERATING ACTIVITIES' if st.session_state.get('language') == 'en'
             else 'က။ လုပ်ငန်း လည်ပတ်မှု လုပ်ဆောင်ချက်များမှ ငွေသား'}
        </h3>
        """,
        unsafe_allow_html=True,
    )

    net_profit = st.number_input(
        "Net Profit/Loss before Taxation"
        if st.session_state.get("language") == "en"
        else "အခွန်မဆိုင်မီ အသားတင် အမြတ်/အရှုံး",
        value=int(cf.get("net_profit", auto_net_profit)),
        min_value=-999999999999,
        step=1000,
        format="%d",
        key="cf_net_profit",
    )
    cf["net_profit"] = net_profit

    retain_change = st.number_input(
        "Increase in Retain Earning"
        if st.session_state.get("language") == "en"
        else "စုဆောင်းအမြတ် တိုးလာမှု",
        value=int(cf.get("retain_earning_change", 0)),
        min_value=-999999999999,
        step=1000,
        format="%d",
        key="cf_retain_change",
    )
    cf["retain_earning_change"] = retain_change

    amortization = st.number_input(
        "Amortization"
        if st.session_state.get("language") == "en"
        else "တန်ဖိုးကျဆင်းမှု ဖြန့်ခွဲ (Amortization)",
        value=int(cf.get("amortization", 0)),
        min_value=0,
        step=1000,
        format="%d",
        key="cf_amortization",
    )
    cf["amortization"] = amortization

    depreciation = st.number_input(
        "Depreciation"
        if st.session_state.get("language") == "en"
        else "တန်ဖိုးကျဆင်းမှု (Depreciation)",
        value=int(cf.get("depreciation", auto_depreciation)),
        min_value=0,
        step=1000,
        format="%d",
        key="cf_depreciation",
    )
    cf["depreciation"] = depreciation

    op_before_wc = (
        net_profit
        + retain_change
        + amortization
        + depreciation
    )

    st.markdown(
        f"""
        <div style="background-color: #e3f2fd; padding: 0.6rem;
                    border-radius: 6px; margin: 0.5rem 0;">
            <span style="color: #1565c0; font-weight: bold; font-size: 0.85rem;">
                {'Operation Profit before WC' if st.session_state.get('language') == 'en'
                 else 'လုပ်ငန်းလည်ပတ်မှု အမြတ် (WC မဆိုင်မီ)'}:
            </span>
            <span style="float: right; font-weight: bold; color: #1565c0;">
                {format_number(op_before_wc)}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# COLUMN 2 — WORKING CAPITAL CHANGES
# ============================================================

with col2:

    st.markdown(
        f"""
        <h3 style="color: #1976d2; font-size: 1.1rem;
                   border-bottom: 2px solid #4facfe; padding-bottom: 0.3rem;">
            {'B. WORKING CAPITAL CHANGES' if st.session_state.get('language') == 'en'
             else 'ခ။ လုပ်ငန်း အရင်းအနှီး ပြောင်းလဲမှုများ'}
        </h3>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.get("language") == "my":
        st.caption("➡️ Asset တိုးရင် (−)၊ လျော့ရင် (+)")
        st.caption("➡️ Liability တိုးရင် (+)၊ လျော့ရင် (−)")
    else:
        st.caption("➡️ Asset increase (−), decrease (+)")
        st.caption("➡️ Liability increase (+), decrease (−)")

    st.markdown("<br>", unsafe_allow_html=True)

    change_inv = st.number_input(
        "Increase/Decrease in Inventories",
        value=int(cf.get("change_inventories", 0)),
        step=1000,
        format="%d",
        key="cf_change_inv",
    )
    cf["change_inventories"] = change_inv

    change_rec = st.number_input(
        "Increase/Decrease in A/C Receivable",
        value=int(cf.get("change_receivable", 0)),
        step=1000,
        format="%d",
        key="cf_change_rec",
    )
    cf["change_receivable"] = change_rec

    change_pay = st.number_input(
        "Increase/Decrease in Creditors/A/P",
        value=int(cf.get("change_payable", 0)),
        step=1000,
        format="%d",
        key="cf_change_pay",
    )
    cf["change_payable"] = change_pay

    change_prepay = st.number_input(
        "Increase/Decrease in Prepayment",
        value=int(cf.get("change_prepayment", 0)),
        step=1000,
        format="%d",
        key="cf_change_prepay",
    )
    cf["change_prepayment"] = change_prepay

    total_wc_change = (
        change_inv
        + change_rec
        + change_pay
        + change_prepay
    )

    st.markdown(
        f"""
        <div style="background-color: #fce4ec; padding: 0.6rem;
                    border-radius: 6px; margin-top: 0.5rem;">
            <span style="color: #c2185b; font-weight: bold; font-size: 0.85rem;">
                {'Cash used in / generated from operation' if st.session_state.get('language') == 'en'
                 else 'လုပ်ငန်းလည်ပတ်မှုမှ ငွေသား (Net)'}:
            </span>
            <span style="float: right; font-weight: bold; color: #c2185b;">
                {format_number(total_wc_change)}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# COLUMN 3 — NET CASH FROM OPERATION
# ============================================================

with col3:

    net_operating = op_before_wc + total_wc_change

    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                    padding: 1.2rem; border-radius: 12px; color: white;
                    margin-bottom: 1rem;">
            <p style="margin: 0; font-size: 0.9rem; opacity: 0.95;">
                💰 {'Net Cash from Operating' if st.session_state.get('language') == 'en'
                 else 'လုပ်ငန်းလည်ပတ်မှုမှ ရရှိသော ငွေသား (Net)'}
            </p>
            <h2 style="margin: 0.4rem 0 0 0; font-size: 1.6rem;">
                {format_number(net_operating)}
            </h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # C. INVESTING ACTIVITIES
    # --------------------------------------------------------

    st.markdown(
        f"""
        <h4 style="color: #1976d2; font-size: 1rem;
                   border-bottom: 1px solid #4facfe; padding-bottom: 0.2rem;">
            {'C. INVESTING ACTIVITIES' if st.session_state.get('language') == 'en'
             else 'ဂ။ ရင်းနှီးမြှုပ်နှံမှု လုပ်ဆောင်ချက်များမှ ငွေသား'}
        </h4>
        """,
        unsafe_allow_html=True,
    )

    invest_fa = st.number_input(
        "Purchase of Fixed Assets"
        if st.session_state.get("language") == "en"
        else "ပုံသေပိုင်ဆိုင်မှု ဝယ်ယူမှု",
        value=int(cf.get("investing_purchase_fa", 0)),
        step=1000,
        format="%d",
        key="cf_invest_fa",
    )
    cf["investing_purchase_fa"] = invest_fa

    net_investing = invest_fa

    st.markdown(
        f"""
        <div style="background-color: #e3f2fd; padding: 0.5rem;
                    border-radius: 6px; font-size: 0.85rem;">
            <span style="color: #1565c0; font-weight: bold;">
                {'Net Cash from Investing:' if st.session_state.get('language') == 'en'
                 else 'ရင်းနှီးမြှုပ်နှံမှုမှ ငွေသား (Net):'}
            </span>
            <span style="float: right; font-weight: bold; color: #1565c0;">
                {format_number(net_investing)}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # D. FINANCING ACTIVITIES
    # --------------------------------------------------------

    st.markdown(
        f"""
        <h4 style="color: #1976d2; font-size: 1rem;
                   border-bottom: 1px solid #4facfe; padding-bottom: 0.2rem;">
            {'D. FINANCING ACTIVITIES' if st.session_state.get('language') == 'en'
             else 'ဃ။ ငွေကြေးရှာဖွေမှု လုပ်ဆောင်ချက်များမှ ငွေသား'}
        </h4>
        """,
        unsafe_allow_html=True,
    )

    finance_draw = st.number_input(
        "Drawing"
        if st.session_state.get("language") == "en"
        else "ပိုင်ရှင် ထုတ်ယူမှု (Drawing)",
        value=int(cf.get("financing_drawing", 0)),
        step=1000,
        format="%d",
        key="cf_finance_draw",
    )
    cf["financing_drawing"] = finance_draw

    net_financing = finance_draw

    st.markdown(
        f"""
        <div style="background-color: #e3f2fd; padding: 0.5rem;
                    border-radius: 6px; font-size: 0.85rem;">
            <span style="color: #1565c0; font-weight: bold;">
                {'Net Cash from Financing:' if st.session_state.get('language') == 'en'
                 else 'ငွေကြေးရှာဖွေမှုမှ ငွေသား (Net):'}
            </span>
            <span style="float: right; font-weight: bold; color: #1565c0;">
                {format_number(net_financing)}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # CASH SUMMARY
    # --------------------------------------------------------

    net_change = (
        net_operating
        + net_investing
        + net_financing
    )

    opening_cash = st.number_input(
        "Cash and Equivalents at beginning"
        if st.session_state.get("language") == "en"
        else "ကာလအစ ငွေသား",
        value=int(cf.get("opening_cash", 0)),
        step=1000,
        format="%d",
        key="cf_opening_cash",
    )
    cf["opening_cash"] = opening_cash

    closing_cash_calc = opening_cash + net_change

    auto_closing_cash = safe_number(
        auto_bs.get("ca_cash", 0)
    )

    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
                    padding: 1rem; border-radius: 12px; color: white;
                    margin-top: 0.5rem;">
            <p style="margin: 0; font-size: 0.85rem; opacity: 0.95;">
                {'Net Change in Cash' if st.session_state.get('language') == 'en'
                 else 'ငွေသား ပြောင်းလဲမှု (Net)'}
            </p>
            <h3 style="margin: 0.3rem 0 0 0; font-size: 1.3rem;">
                {format_number(net_change)}
            </h3>
            <hr style="margin: 0.5rem 0; border-color: rgba(255,255,255,0.3);">
            <p style="margin: 0; font-size: 0.8rem; opacity: 0.9;">
                + {'Cash at Beginning' if st.session_state.get('language') == 'en'
                   else 'ကာလအစ ငွေသား'}: {format_number(opening_cash)}
            </p>
            <p style="margin: 0.3rem 0 0 0; font-size: 0.9rem; font-weight: bold;">
                = {'Cash at End' if st.session_state.get('language') == 'en'
                   else 'ကာလအဆုံး ငွေသား'}: {format_number(closing_cash_calc)}
            </p>
            <p style="margin: 0.5rem 0 0 0; font-size: 0.75rem; opacity: 0.85;">
                {'Closing Cash from BS' if st.session_state.get('language') == 'en'
                 else 'BS မှ Closing Cash'}: {format_number(auto_closing_cash)}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# ACTION BUTTONS
# ============================================================

st.markdown("<br>", unsafe_allow_html=True)
st.divider()

action_col1, action_col2, action_col3, action_col4 = st.columns(4)


# ------------------------------------------------------------
# SAVE
# ------------------------------------------------------------

with action_col1:

    if st.button(
        t("save"),
        use_container_width=True,
        type="primary",
    ):
        play_click_sound()

        try:
            cf["_net_operating"] = net_operating
            cf["_net_investing"] = net_investing
            cf["_net_financing"] = net_financing
            cf["_net_change"] = net_change
            cf["_closing_cash"] = closing_cash_calc

            data_json = json.dumps(
                cf,
                ensure_ascii=False,
            )

            db.save_statement(
                client_id=client_id,
                statement_type="cash_flow",
                period_end=period_string,
                data_json=data_json,
            )

            st.success(
                "✓ သိမ်းပြီးပါပြီ"
                if st.session_state.get("language") == "my"
                else "✓ Saved successfully"
            )

            st.balloons()

        except Exception as e:
            st.error(f"❌ Error: {e}")


# ------------------------------------------------------------
# PDF
# ------------------------------------------------------------

with action_col2:

    if st.button("📄 PDF", use_container_width=True):

        play_click_sound()

        try:
            pdf_data = dict(cf)

            pdf_data["change_inventories"] = change_inv
            pdf_data["change_receivable"] = change_rec
            pdf_data["change_payable"] = change_pay
            pdf_data["change_prepayment"] = change_prepay

            pdf_bytes = generate_pdf(
                statement_type="cash_flow",
                client_name=client["name"],
                client_id=client_id,
                business_name=client.get("business_name", ""),
                business_type=client.get("business_type", ""),
                data=pdf_data,
                period_end=period_string,
                lang=st.session_state.get("language", "my"),
            )

            st.download_button(
                "⬇️ PDF Download",
                data=pdf_bytes,
                file_name=(
                    f"{client['name']}_CashFlow_{period_string}.pdf"
                ),
                mime="application/pdf",
                use_container_width=True,
            )

        except Exception as e:
            st.error(f"❌ PDF Error: {e}")


# ------------------------------------------------------------
# RESET
# ------------------------------------------------------------

with action_col3:

    if st.button("🔄 Reset", use_container_width=True):

        play_click_sound()

        clear_cf_widget_state()

        st.session_state.cf_data = {}
        st.session_state._cf_loaded_period = period_string
        st.session_state.cf_period = period_string

        st.rerun()


# ------------------------------------------------------------
# BACK TO CLIENT DETAIL
# ------------------------------------------------------------

with action_col4:

    if st.button(t("detail"), use_container_width=True):

        play_click_sound()
        st.switch_page("pages/2_Client_Detail.py")


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    f"📅 {t('period_end')}: {format_date_mm(period_string)}"
)

st.caption(
    f"👤 {t('clients')}: {client['name']}"
)
