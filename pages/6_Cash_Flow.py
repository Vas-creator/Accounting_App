"""
Cash Flow Statement — ငွေသား စီးဆင်းမှု ရှင်းတမ်း
Indirect Method
"""

import json
from datetime import date

import streamlit as st

from core import db
from core.utils import format_number, format_date_mm, play_click_sound
from core.pdf_generator import generate_pdf
from core.translations import t


st.set_page_config(
    page_title="Cash Flow Statement",
    page_icon="💵",
    layout="wide",
)

NEW_PERIOD_LABEL = "-- ကာလအသစ် (New) --"


# ============================================================
# HELPERS
# ============================================================

def parse_json_data(raw_data):
    if isinstance(raw_data, dict):
        return raw_data.copy()

    if isinstance(raw_data, str):
        try:
            parsed = json.loads(raw_data)
            return parsed if isinstance(parsed, dict) else {}
        except (json.JSONDecodeError, TypeError):
            return {}

    return {}


def safe_number(value):
    try:
        return float(value or 0)
    except (ValueError, TypeError):
        return 0.0


def clear_cf_widget_state():
    """Period selector များကို ချန်ပြီး Cash Flow widget state များရှင်းရန်။"""
    protected = {
        "cf_period_input",
        "cf_history_selector",
        "selected_cf_history",
    }
    for key in list(st.session_state.keys()):
        if key.startswith("cf_") and key not in protected:
            del st.session_state[key]


def make_widget_key(client_id, period_string, field):
    """Client/Period/Field တစ်ခုစီအတွက် သီးခြား widget key။"""
    return f"cf_input_{client_id}_{period_string}_{field}"


def cf_number_input(
    label,
    data,
    field,
    client_id,
    period_string,
    default=0,
    min_value=None,
    step=1000,
):
    """
    Widget state ကို ပထမဆုံးအကြိမ် data မှ initialize လုပ်သည်။
    st.number_input တွင် value= နှင့် key= ကို တွဲမသုံးပါ။
    """
    key = make_widget_key(client_id, period_string, field)

    if key not in st.session_state:
        try:
            st.session_state[key] = int(data.get(field, default) or 0)
        except (ValueError, TypeError, OverflowError):
            st.session_state[key] = int(default or 0)

    kwargs = {
        "label": label,
        "key": key,
        "step": step,
        "format": "%d",
    }
    if min_value is not None:
        kwargs["min_value"] = min_value

    return st.number_input(**kwargs)


def load_cf_period(period_string, client_id):
    """ရွေးထားသော Client နှင့် Period အတွက် data ကို DB မှ load လုပ်ရန်။"""
    clear_cf_widget_state()

    existing = db.get_statement(
        client_id,
        "cash_flow",
        period_end=period_string,
    )

    st.session_state["cf_data"] = (
        parse_json_data(existing.get("data"))
        if existing
        else {}
    )
    st.session_state["cf_period"] = period_string
    st.session_state["_cf_loaded_period"] = period_string


# ============================================================
# AUTHENTICATION + CLIENT
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

language = st.session_state.get("language", "my")
is_english = language == "en"


# ============================================================
# CLIENT SESSION INITIALIZATION
# ============================================================

if st.session_state.get("current_cf_client_id") != client_id:
    clear_cf_widget_state()
    st.session_state["current_cf_client_id"] = client_id
    st.session_state["cf_period"] = str(date.today())
    st.session_state["cf_data"] = {}
    st.session_state.pop("_cf_loaded_period", None)

target_period = st.session_state.pop("target_period", None)
if target_period:
    try:
        target_period = str(date.fromisoformat(str(target_period)))
        st.session_state["cf_period"] = target_period
        st.session_state["cf_period_input"] = date.fromisoformat(target_period)
        st.session_state.pop("_cf_loaded_period", None)
    except (ValueError, TypeError):
        pass

if "cf_period" not in st.session_state:
    st.session_state["cf_period"] = str(date.today())


# ============================================================
# HISTORY
# ============================================================

try:
    history = db.get_statement_history(client_id, "cash_flow") or []
except Exception as e:
    st.error(f"History load error: {e}")
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
                {'ဖောက်သည်' if language == 'my' else 'Client'}
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
        <h1 style="margin: 0; font-size: 1.8rem;">💵 {t('pdf_cashflow')}</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 0.95rem; opacity: 0.95;">
            Cash Flow Statement — {client['name']}
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# PERIOD + HISTORY SELECTORS
# ============================================================

col_date, col_hist = st.columns([1, 1])

with col_hist:
    if history_periods:
        st.markdown("**📜 သိမ်းထားသော ကာလများ (History)**")
        selected_history = st.selectbox(
            "ကာလဟောင်း ပြန်ကြည့်ရန်",
            options=[NEW_PERIOD_LABEL] + history_periods,
            key="cf_history_selector",
            label_visibility="collapsed",
        )

        previous_history = st.session_state.get(
            "selected_cf_history",
            NEW_PERIOD_LABEL,
        )

        if selected_history != previous_history:
            st.session_state["selected_cf_history"] = selected_history

            if selected_history != NEW_PERIOD_LABEL:
                selected_date = date.fromisoformat(selected_history)
                st.session_state["cf_period_input"] = selected_date
                st.session_state["cf_period"] = selected_history
                load_cf_period(selected_history, client_id)
                st.rerun()
            else:
                current_period = st.session_state.get(
                    "cf_period",
                    str(date.today()),
                )
                clear_cf_widget_state()
                st.session_state["cf_data"] = {}
                st.session_state["cf_period"] = current_period
                st.session_state["cf_period_input"] = date.fromisoformat(
                    current_period
                )
                st.session_state.pop("_cf_loaded_period", None)
                st.rerun()
    else:
        st.info("သိမ်းထားသော စာရင်း မရှိသေးပါ။")

with col_date:
    try:
        initial_date = date.fromisoformat(st.session_state["cf_period"])
    except (ValueError, TypeError):
        initial_date = date.today()

    if "cf_period_input" not in st.session_state:
        st.session_state["cf_period_input"] = initial_date

    period_end = st.date_input(
        f"📅 {t('period_end')} (New/Update)",
        key="cf_period_input",
    )
    period_string = str(period_end)


# ============================================================
# LOAD SELECTED PERIOD
# ============================================================

if st.session_state.get("_cf_loaded_period") != period_string:
    try:
        load_cf_period(period_string, client_id)
    except Exception as e:
        st.error(f"❌ Cash Flow load error: {e}")
        st.stop()
    st.rerun()

st.session_state["cf_period"] = period_string
if "cf_data" not in st.session_state:
    st.session_state["cf_data"] = {}


# ============================================================
# AUTO DATA — SAME PERIOD ONLY
# ============================================================

auto_net_profit = 0.0
auto_depreciation = 0.0
auto_bs = {}

try:
    tpl_existing = db.get_statement(
        client_id,
        "trading_pl",
        period_end=period_string,
    )
    if tpl_existing:
        tpl_data = parse_json_data(tpl_existing.get("data"))
        auto_net_profit = safe_number(tpl_data.get("_net_profit", 0))
        auto_depreciation = safe_number(tpl_data.get("_depreciation", 0))
except Exception:
    pass

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

cf = st.session_state["cf_data"]

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
    "financing_increase_loan": 0,
}
for field, default_value in defaults.items():
    if field not in cf:
        cf[field] = default_value


# ============================================================
# THREE-COLUMN LAYOUT
# ============================================================

col1, col2, col3 = st.columns(3)


# COLUMN 1 — OPERATING ACTIVITIES
with col1:
    st.markdown(
        f"""
        <h3 style="color: #1565c0; font-size: 1.1rem;
                   border-bottom: 2px solid #4facfe; padding-bottom: 0.3rem;">
            {'A. OPERATING ACTIVITIES' if is_english else 'က။ လုပ်ငန်း လည်ပတ်မှု လုပ်ဆောင်ချက်များမှ ငွေသား'}
        </h3>
        """,
        unsafe_allow_html=True,
    )

    net_profit = cf_number_input(
        "Net Profit/Loss before Taxation" if is_english
        else "အခွန်မဆိုင်မီ အသားတင် အမြတ်/အရှုံး",
        cf, "net_profit", client_id, period_string,
        default=int(auto_net_profit),
        min_value=-999999999999,
    )
    cf["net_profit"] = net_profit

    retain_change = cf_number_input(
        "Increase in Retain Earning" if is_english else "စုဆောင်းအမြတ် တိုးလာမှု",
        cf, "retain_earning_change", client_id, period_string,
    )
    cf["retain_earning_change"] = retain_change

    amortization = cf_number_input(
        "Amortization" if is_english else "တန်ဖိုးကျဆင်းမှု ဖြန့်ခွဲ (Amortization)",
        cf, "amortization", client_id, period_string,
        min_value=0,
    )
    cf["amortization"] = amortization

    depreciation = cf_number_input(
        "Depreciation" if is_english else "တန်ဖိုးကျဆင်းမှု (Depreciation)",
        cf, "depreciation", client_id, period_string,
        default=int(auto_depreciation),
        min_value=0,
    )
    cf["depreciation"] = depreciation

    op_before_wc = (
        net_profit + retain_change + amortization + depreciation
    )

    st.markdown(
        f"""
        <div style="background-color: #e3f2fd; padding: 0.6rem;
                    border-radius: 6px; margin: 0.5rem 0;">
            <span style="color: #1565c0; font-weight: bold; font-size: 0.85rem;">
                {'Operation Profit before WC' if is_english else 'လုပ်ငန်းလည်ပတ်မှု အမြတ် (WC မဆိုင်မီ)'}:
            </span>
            <span style="float: right; font-weight: bold; color: #1565c0;">
                {format_number(op_before_wc)}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


# COLUMN 2 — WORKING CAPITAL CHANGES
with col2:
    st.markdown(
        f"""
        <h3 style="color: #1976d2; font-size: 1.1rem;
                   border-bottom: 2px solid #4facfe; padding-bottom: 0.3rem;">
            {'B. WORKING CAPITAL CHANGES' if is_english else 'ခ။ လုပ်ငန်း အရင်းအနှီး ပြောင်းလဲမှုများ'}
        </h3>
        """,
        unsafe_allow_html=True,
    )

    if not is_english:
        st.caption("➡️ Asset တိုးရင် (−)၊ လျော့ရင် (+)")
        st.caption("➡️ Liability တိုးရင် (+)၊ လျော့ရင် (−)")
    else:
        st.caption("➡️ Asset increase (−), decrease (+)")
        st.caption("➡️ Liability increase (+), decrease (−)")

    st.markdown("<br>", unsafe_allow_html=True)

    change_inv = cf_number_input(
        "Increase/Decrease in Inventories",
        cf, "change_inventories", client_id, period_string,
    )
    cf["change_inventories"] = change_inv

    change_rec = cf_number_input(
        "Increase/Decrease in A/C Receivable",
        cf, "change_receivable", client_id, period_string,
    )
    cf["change_receivable"] = change_rec

    change_pay = cf_number_input(
        "Increase/Decrease in Creditors/A/P",
        cf, "change_payable", client_id, period_string,
    )
    cf["change_payable"] = change_pay

    change_prepay = cf_number_input(
        "Increase/Decrease in Prepayment",
        cf, "change_prepayment", client_id, period_string,
    )
    cf["change_prepayment"] = change_prepay

    total_wc_change = (
        change_inv + change_rec + change_pay + change_prepay
    )

    st.markdown(
        f"""
        <div style="background-color: #fce4ec; padding: 0.6rem;
                    border-radius: 6px; margin-top: 0.5rem;">
            <span style="color: #c2185b; font-weight: bold; font-size: 0.85rem;">
                {'Cash used in / generated from operation' if is_english else 'လုပ်ငန်းလည်ပတ်မှုမှ ငွေသား (Net)'}:
            </span>
            <span style="float: right; font-weight: bold; color: #c2185b;">
                {format_number(total_wc_change)}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


# COLUMN 3 — INVESTING, FINANCING AND CASH SUMMARY
with col3:
    net_operating = op_before_wc + total_wc_change

    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                    padding: 1.2rem; border-radius: 12px; color: white;
                    margin-bottom: 1rem;">
            <p style="margin: 0; font-size: 0.9rem; opacity: 0.95;">
                💰 {'Net Cash from Operating' if is_english else 'လုပ်ငန်းလည်ပတ်မှုမှ ရရှိသော ငွေသား (Net)'}
            </p>
            <h2 style="margin: 0.4rem 0 0 0; font-size: 1.6rem;">
                {format_number(net_operating)}
            </h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <h4 style="color: #1976d2; font-size: 1rem;
                   border-bottom: 1px solid #4facfe; padding-bottom: 0.2rem;">
            {'C. INVESTING ACTIVITIES' if is_english else 'ဂ။ ရင်းနှီးမြှုပ်နှံမှု လုပ်ဆောင်ချက်များမှ ငွေသား'}
        </h4>
        """,
        unsafe_allow_html=True,
    )

    invest_fa = cf_number_input(
        "Purchase of Fixed Assets" if is_english else "ပုံသေပိုင်ဆိုင်မှု ဝယ်ယူမှု",
        cf, "investing_purchase_fa", client_id, period_string,
    )
    cf["investing_purchase_fa"] = invest_fa
    net_investing = invest_fa

    st.markdown(
        f"""
        <div style="background-color: #e3f2fd; padding: 0.5rem;
                    border-radius: 6px; font-size: 0.85rem;">
            <span style="color: #1565c0; font-weight: bold;">
                {'Net Cash from Investing:' if is_english else 'ရင်းနှီးမြှုပ်နှံမှုမှ ငွေသား (Net):'}
            </span>
            <span style="float: right; font-weight: bold; color: #1565c0;">
                {format_number(net_investing)}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(
        f"""
        <h4 style="color: #1976d2; font-size: 1rem;
                   border-bottom: 1px solid #4facfe; padding-bottom: 0.2rem;">
            {'D. FINANCING ACTIVITIES' if is_english else 'ဃ။ ငွေကြေးရှာဖွေမှု လုပ်ဆောင်ချက်များမှ ငွေသား'}
        </h4>
        """,
        unsafe_allow_html=True,
    )

    finance_draw = cf_number_input(
        "Drawing" if is_english else "ပိုင်ရှင် ထုတ်ယူမှု (Drawing)",
        cf, "financing_drawing", client_id, period_string,
    )
    cf["financing_drawing"] = finance_draw

    finance_loan = cf_number_input(
        "Increase in Loan" if is_english else "ချေးငွေ တိုးလာမှု (Increase in Loan)",
        cf, "financing_increase_loan", client_id, period_string,
    )
    cf["financing_increase_loan"] = finance_loan
    net_financing = finance_draw + finance_loan

    st.markdown(
        f"""
        <div style="background-color: #e3f2fd; padding: 0.5rem;
                    border-radius: 6px; font-size: 0.85rem;">
            <span style="color: #1565c0; font-weight: bold;">
                {'Net Cash from Financing:' if is_english else 'ငွေကြေးရှာဖွေမှုမှ ငွေသား (Net):'}
            </span>
            <span style="float: right; font-weight: bold; color: #1565c0;">
                {format_number(net_financing)}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    net_change = net_operating + net_investing + net_financing

    opening_cash = cf_number_input(
        "Cash and Equivalents at beginning" if is_english else "ကာလအစ ငွေသား",
        cf, "opening_cash", client_id, period_string,
    )
    cf["opening_cash"] = opening_cash

    closing_cash_calc = opening_cash + net_change
    auto_closing_cash = safe_number(auto_bs.get("ca_cash", 0))

    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
                    padding: 1rem; border-radius: 12px; color: white;
                    margin-top: 0.5rem;">
            <p style="margin: 0; font-size: 0.85rem; opacity: 0.95;">
                {'Net Change in Cash' if is_english else 'ငွေသား ပြောင်းလဲမှု (Net)'}
            </p>
            <h3 style="margin: 0.3rem 0 0 0; font-size: 1.3rem;">
                {format_number(net_change)}
            </h3>
            <hr style="margin: 0.5rem 0; border-color: rgba(255,255,255,0.3);">
            <p style="margin: 0; font-size: 0.8rem; opacity: 0.9;">
                + {'Cash at Beginning' if is_english else 'ကာလအစ ငွေသား'}: {format_number(opening_cash)}
            </p>
            <p style="margin: 0.3rem 0 0 0; font-size: 0.9rem; font-weight: bold;">
                = {'Cash at End' if is_english else 'ကာလအဆုံး ငွေသား'}: {format_number(closing_cash_calc)}
            </p>
            <p style="margin: 0.5rem 0 0 0; font-size: 0.75rem; opacity: 0.85;">
                {'Closing Cash from BS' if is_english else 'BS မှ Closing Cash'}: {format_number(auto_closing_cash)}
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


# SAVE
with action_col1:
    if st.button(t("save"), use_container_width=True, type="primary"):
        play_click_sound()
        try:
            cf["_net_operating"] = net_operating
            cf["_net_investing"] = net_investing
            cf["_net_financing"] = net_financing
            cf["_net_change"] = net_change
            cf["_closing_cash"] = closing_cash_calc

            db.save_statement(
                client_id=client_id,
                statement_type="cash_flow",
                period_end=period_string,
                data_json=json.dumps(cf, ensure_ascii=False),
            )

            st.success(
                "✓ သိမ်းပြီးပါပြီ"
                if language == "my"
                else "✓ Saved successfully"
            )
            st.balloons()
        except Exception as e:
            st.error(f"❌ Error: {e}")


# PDF
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
                lang=language,
            )

            st.download_button(
                "⬇️ PDF Download",
                data=pdf_bytes,
                file_name=f"{client['name']}_CashFlow_{period_string}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"❌ PDF Error: {e}")


# RESET — only clears the current unsaved widget state; DB row is not deleted.
with action_col3:
    if st.button("🔄 Reset", use_container_width=True):
        play_click_sound()
        clear_cf_widget_state()
        st.session_state["cf_data"] = {}
        st.session_state["cf_period"] = period_string
        st.session_state["_cf_loaded_period"] = period_string
        st.rerun()


# BACK TO CLIENT DETAIL
with action_col4:
    if st.button(t("detail"), use_container_width=True):
        play_click_sound()
        st.switch_page("pages/2_Client_Detail.py")


# ============================================================
# FOOTER
# ============================================================

st.divider()
st.caption(f"📅 {t('period_end')}: {format_date_mm(period_string)}")
st.caption(f"👤 {t('clients')}: {client['name']}")
