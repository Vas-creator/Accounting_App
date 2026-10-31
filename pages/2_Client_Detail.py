
"""
Client Detail — ဖောက်သည် အသေးစိတ် + ရှင်းတမ်း ၄ ခု Overview
Multi-Year / Period-Based Support
"""

import streamlit as st
import json
from datetime import date

from core import db
from core.utils import format_date_mm, format_number
from core.translations import t
from core.ai_help import get_ai_response


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Client Detail",
    page_icon="📂",
    layout="wide",
)


# ============================================================
# HELPERS
# ============================================================

LANG = st.session_state.get("language", "my")
IS_MY = LANG == "my"

STATEMENT_TYPES = [
    "manufacturing",
    "trading_pl",
    "balance_sheet",
    "cash_flow",
]


def parse_json_data(raw_data):
    """Database က JSON string သို့မဟုတ် dict ပြန်ပေးနိုင်သည်။"""
    if isinstance(raw_data, dict):
        return raw_data

    if isinstance(raw_data, str):
        try:
            parsed = json.loads(raw_data)
            return parsed if isinstance(parsed, dict) else {}
        except (json.JSONDecodeError, TypeError):
            return {}

    return {}


def get_client_periods(client_id):
    """
    ရှင်းတမ်း ၄ မျိုးလုံး၏ history ကို စုစည်းပြီး
    period တူနေပါက တစ်ခုတည်းအဖြစ် ပြန်ပေးသည်။
    """
    periods = set()
    errors = []

    for statement_type in STATEMENT_TYPES:
        try:
            history = db.get_statement_history(
                client_id,
                statement_type,
            ) or []

            for item in history:
                period = item.get("period_end")
                if period:
                    periods.add(str(period))

        except Exception as e:
            errors.append(f"{statement_type}: {e}")

    return sorted(periods, reverse=True), errors


def get_statement_for_period(client_id, statement_type, period):
    """သတ်မှတ်ထားသော period အတွက် statement တစ်ခုတည်းကို ဖတ်သည်။"""
    if not period:
        return None

    return db.get_statement(
        client_id,
        statement_type,
        period_end=period,
    )


def statement_has_data(statement):
    """Row ရှိရုံနဲ့ မလုံလောက်ဘဲ data အမှန်တကယ်ရှိမရှိ စစ်သည်။"""
    if not statement:
        return False

    data = parse_json_data(statement.get("data"))
    return bool(data)


# ============================================================
# AUTH CHECK
# ============================================================

if not st.session_state.get("authentication_status"):
    st.warning(
        "⚠️ ကျေးဇူးပြု၍ အရင် ဝင်ရောက်ပါ"
        if IS_MY
        else "⚠️ Please login first"
    )
    st.switch_page("app.py")
    st.stop()


# ============================================================
# CLIENT ID CHECK
# ============================================================

client_id = st.session_state.get("selected_client_id")

if not client_id:
    st.warning(
        "⚠️ ဖောက်သည် မရွေးရသေးပါ"
        if IS_MY
        else "⚠️ No client selected"
    )

    if st.button(
        "← ဖောက်သည် စာရင်းသို့ ပြန်"
        if IS_MY
        else "← Back to Clients"
    ):
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
    st.error(
        "❌ ဖောက်သည် မတွေ့ပါ"
        if IS_MY
        else "❌ Client not found"
    )

    if st.button(
        "← ဖောက်သည် စာရင်းသို့ ပြန်"
        if IS_MY
        else "← Back to Clients"
    ):
        st.switch_page("pages/1_Clients.py")

    st.stop()


client_display_name = (
    client.get("name")
    or client.get("business_name")
    or "Unknown"
)


# ============================================================
# CLIENT CHANGE — RESET PAGE SELECTION
# ============================================================

if st.session_state.get("detail_client_id") != client_id:

    st.session_state.detail_client_id = client_id

    st.session_state.pop("selected_detail_period", None)
    st.session_state.pop("detail_period_select", None)

    st.session_state.pop("confirm_delete_statement_year", None)
    st.session_state.pop("delete_from_detail", None)


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

    if st.button(t("home"), use_container_width=True):
        st.switch_page("app.py")

    if st.button(t("clients"), use_container_width=True):
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
            <p style="margin: 0; font-size: 0.85rem; color: #666;">
                {'လက်ရှိ ဖောက်သည်' if IS_MY else 'Current Client'}
            </p>
            <p style="margin: 0.2rem 0 0 0; font-weight: bold; color: #1565c0;">
                👤 {client_display_name}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption(f"👤 {st.session_state.get('name', 'User')}")


# ============================================================
# HEADER — CLIENT INFO
# ============================================================

col_back, col_blank = st.columns([1, 5])

with col_back:
    if st.button(
        "← " + ("ပြန်" if IS_MY else "Back"),
        use_container_width=True,
    ):
        st.switch_page("pages/1_Clients.py")


business_name = client.get("business_name", "")

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
            {
                f'🏢 {business_name}'
                if business_name and business_name != client_display_name
                else ''
            }
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# CLIENT INFO CARDS
# ============================================================

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
        📅 {'ကာလ ရွေးချယ်ပါ' if IS_MY else 'Select Period'}
    </h2>
    """,
    unsafe_allow_html=True,
)


history_periods, history_errors = get_client_periods(client_id)

if history_errors:
    st.warning(
        "ရှင်းတမ်း History အချို့ကို ရယူရာတွင် အမှားရှိနေသည်။ "
        "အောက်ပါစာရင်းများကို စစ်ဆေးပါ။"
        if IS_MY
        else "Some statement histories could not be loaded. Please check the affected statements."
    )


# History မရှိသေးလျှင် ယနေ့ရက်စွဲကို ယာယီကာလအဖြစ် သတ်မှတ်မည်။
if not history_periods:
    default_period = str(date.today())

else:
    default_period = history_periods[0]


# လက်ရှိရွေးထားသော period မရှိတော့ပါက valid period သို့ ပြန်ညှိမည်။
current_period = st.session_state.get("selected_detail_period")

if current_period not in history_periods and history_periods:
    current_period = history_periods[0]

elif not current_period:
    current_period = default_period

st.session_state.selected_detail_period = current_period


if history_periods:

    col_period, col_add = st.columns([2, 1])

    with col_period:

        selected_period = st.selectbox(
            "ကာလ (Period)" if IS_MY else "Period",
            options=history_periods,
            index=history_periods.index(current_period),
            key="detail_period_select",
        )

        st.session_state.selected_detail_period = selected_period

    with col_add:

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button(
            f"➕ {'ကာလအသစ် ထပ်ထည့်ရန်' if IS_MY else 'Add New Period'}",
            use_container_width=True,
        ):
            st.session_state["selected_client_id"] = client_id
            st.session_state["selected_client_name"] = client_display_name

            # New period ကို လက်ရှိရက်စွဲဖြင့် စတင်မည်။
            st.session_state["target_period"] = str(date.today())

            st.switch_page("pages/4_Trading_PL.py")

else:

    st.info(
        "သိမ်းထားသော စာရင်း မရှိသေးပါ။ အောက်က ခလုတ်ကို နှိပ်ပြီး စတင်ပါ။"
        if IS_MY
        else "No statements yet. Click below to start."
    )

    if st.button(
        f"➕ {'စာရင်းအသစ် စတင်ရန်' if IS_MY else 'Start New Statement'}",
        type="primary",
    ):
        st.session_state["selected_client_id"] = client_id
        st.session_state["selected_client_name"] = client_display_name
        st.session_state["target_period"] = str(date.today())

        st.switch_page("pages/4_Trading_PL.py")


selected_period = st.session_state.selected_detail_period


st.markdown("<br>", unsafe_allow_html=True)


# ============================================================
# DELETE STATEMENTS BY YEAR
# ============================================================

st.divider()

st.markdown(
    "### 🗑️ နှစ်အလိုက် စာရင်းဒေတာ ဖျက်ရန်"
    if IS_MY
    else "### 🗑️ Delete Statement Data by Year"
)

st.caption(
    "ရွေးချယ်ထားသော နှစ်အတွင်းရှိ Manufacturing, Trading P/L, "
    "Balance Sheet နှင့် Cash Flow စာရင်းများကိုသာ ဖျက်ပါမည်။ "
    "Client ကို မဖျက်ပါ။"
    if IS_MY
    else "This deletes only Manufacturing, Trading P/L, Balance Sheet and Cash Flow records whose period_end falls in the selected calendar year. The client will not be deleted."
)


try:
    available_years = db.get_statement_years(client_id) or []

except Exception as e:
    available_years = []
    st.error(
        f"နှစ်စာရင်း ရယူရာတွင် အမှားဖြစ်နေသည်: {e}"
        if IS_MY
        else f"Could not load statement years: {e}"
    )


if available_years:

    selected_delete_year = st.selectbox(
        "ဖျက်လိုသောနှစ် ရွေးပါ"
        if IS_MY
        else "Select year to delete",
        options=available_years,
        format_func=lambda year: str(year),
        key="delete_statement_year_select",
    )

    try:
        year_summary = db.get_statement_year_summary(
            client_id,
            selected_delete_year,
        )

        total_year_rows = sum(year_summary.values())

        summary_labels = {
            "manufacturing": "ထုတ်လုပ်မှုစာရင်း" if IS_MY else "Manufacturing",
            "trading_pl": "အရှုံးအမြတ်စာရင်း" if IS_MY else "Trading P/L",
            "balance_sheet": "လက်ကျန်ရှင်းတမ်း" if IS_MY else "Balance Sheet",
            "cash_flow": "ငွေသားစီးဆင်းမှု" if IS_MY else "Cash Flow",
        }

        st.write(
            f"**{selected_delete_year} ခုနှစ်အတွက် တွေ့ရှိသော စာရင်းများ**"
            if IS_MY
            else f"**Records found for {selected_delete_year}**"
        )

        count_cols = st.columns(4)

        for col, table_name in zip(
            count_cols,
            STATEMENT_TYPES,
        ):
            with col:
                st.metric(
                    summary_labels[table_name],
                    year_summary.get(table_name, 0),
                )

        if total_year_rows == 0:

            st.info(
                "ဒီနှစ်အတွက် ဖျက်ရန် စာရင်းမရှိပါ။"
                if IS_MY
                else "There are no statement records to delete for this year."
            )

        else:

            if st.button(
                f"🗑️ {selected_delete_year} ခုနှစ် စာရင်းများ ဖျက်ရန်"
                if IS_MY
                else f"🗑️ Delete {selected_delete_year} Statement Data",
                type="primary",
                key="start_delete_year",
            ):
                st.session_state["confirm_delete_statement_year"] = int(
                    selected_delete_year
                )
                st.rerun()

    except Exception as e:
        st.error(
            f"စာရင်းအရေအတွက် စစ်ဆေးရာတွင် အမှားဖြစ်နေသည်: {e}"
            if IS_MY
            else f"Could not count records for this year: {e}"
        )

else:
    st.info(
        "ဖျက်နိုင်သော နှစ်အလိုက် စာရင်းဒေတာ မရှိသေးပါ။"
        if IS_MY
        else "No statement years are available to delete."
    )


# ------------------------------------------------------------
# DELETE YEAR CONFIRMATION
# ------------------------------------------------------------

if st.session_state.get("confirm_delete_statement_year"):

    year_to_delete = int(
        st.session_state["confirm_delete_statement_year"]
    )

    st.warning(
        f"⚠️ သေချာပါသလား။ {year_to_delete} ခုနှစ်အတွင်းရှိ "
        "ရှင်းတမ်းဒေတာများကို ဖျက်ပါမည်။ ဤလုပ်ဆောင်ချက်ကို "
        "ပြန်လည်ပြင်ဆင်၍ မရနိုင်ပါ။"
        if IS_MY
        else f"⚠️ Are you sure? All statement records with a period_end in {year_to_delete} will be deleted. This action cannot be undone."
    )

    confirm_col, cancel_col, _ = st.columns([1, 1, 4])

    with confirm_col:

        if st.button(
            "အတည်ပြု ဖျက်မည်" if IS_MY else "Confirm Delete",
            type="primary",
            key="confirm_delete_year_button",
        ):

            try:
                deleted_counts = db.delete_statements_for_year(
                    client_id,
                    year_to_delete,
                )

                deleted_total = sum(deleted_counts.values())

                st.session_state.pop(
                    "confirm_delete_statement_year",
                    None,
                )

                current_period = st.session_state.get(
                    "selected_detail_period",
                    "",
                )

                if str(current_period).startswith(str(year_to_delete)):
                    st.session_state.pop(
                        "selected_detail_period",
                        None,
                    )
                    st.session_state.pop(
                        "detail_period_select",
                        None,
                    )

                st.success(
                    f"✓ {year_to_delete} ခုနှစ်၏ စာရင်း {deleted_total} ခု ဖျက်ပြီးပါပြီ။"
                    if IS_MY
                    else f"✓ Deleted {deleted_total} statement records for {year_to_delete}."
                )

                st.rerun()

            except Exception as e:
                st.error(
                    f"ဖျက်ရာတွင် အမှားဖြစ်နေသည်: {e}။ "
                    "အချို့ဇယားများမှ ဖျက်ပြီးသား ဖြစ်နိုင်သဖြင့် Database ကို ပြန်စစ်ပါ။"
                    if IS_MY
                    else f"Delete failed: {e}. Some tables may already have been deleted; please check the database."
                )

    with cancel_col:

        if st.button(
            "မဖျက်တော့ပါ" if IS_MY else "Cancel",
            key="cancel_delete_year_button",
        ):
            st.session_state.pop(
                "confirm_delete_statement_year",
                None,
            )
            st.rerun()


st.markdown("<br>", unsafe_allow_html=True)


# ============================================================
# STATEMENTS OVERVIEW — SELECTED PERIOD
# ============================================================

st.markdown(
    f"""
    <h2 style="color: #1f4788; font-size: 1.6rem; margin-top: 1rem;">
        {t('all_statements')} — {selected_period}
    </h2>
    """,
    unsafe_allow_html=True,
)


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
            existing = get_statement_for_period(
                client_id,
                stmt["key"],
                selected_period,
            )

            has_data = statement_has_data(existing)

        except Exception as e:
            has_data = False
            st.error(
                f"{stmt['key']} load error: {e}"
            )

        status_icon = "✓" if has_data else "○"
        status_text = t("has_data") if has_data else t("no_data")
        status_color = "#2e7d32" if has_data else "#999"

        if stmt["key"] == "manufacturing":
            title = t("manufacturing")

        elif stmt["key"] == "trading_pl":
            title = t("trading_pl")

        elif stmt["key"] == "balance_sheet":
            title = t("balance_sheet_title")

        else:
            title = t("cash_flow")

        st.markdown(
            f"""
            <div style="
                background: linear-gradient(
                    135deg,
                    {stmt['color']}40,
                    {stmt['color']}20
                );
                border: 2px solid {stmt['color']};
                border-radius: 12px;
                padding: 1.5rem;
                text-align: center;
                margin-bottom: 0.5rem;
                min-height: 200px;
            ">
                <p style="font-size: 3rem; margin: 0;">
                    {stmt['icon']}
                </p>
                <h3 style="margin: 0.5rem 0 0.3rem 0;
                           color: #1f4788; font-size: 1.15rem;">
                    {title}
                </h3>
                <p style="margin: 0.8rem 0 0 0;
                          color: {status_color};
                          font-weight: bold; font-size: 0.95rem;">
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

            # ရွေးထားသော period ကို သက်ဆိုင်ရာ page သို့ ပို့မည်။
            st.session_state["target_period"] = selected_period

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
            💡 <b>{t('export_pdf')}</b> —
            {
                'ရွေးထားတဲ့ ကာလအတွက် ရှင်းတမ်း ၄ ခုလုံး ဖြည့်ပြီးမှ ဤနေရာမှ ထုတ်ယူပါ'
                if IS_MY
                else 'Fill all 4 statements for the selected period before exporting PDF'
            }
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


col1, col2 = st.columns(2)

with col1:

    if st.button(
        f"📄 {t('export_pdf')}",
        use_container_width=True,
        type="primary",
    ):

        st.session_state["selected_client_id"] = client_id
        st.session_state["selected_client_name"] = client_display_name
        st.session_state["target_period"] = selected_period

        st.switch_page("pages/7_Export.py")


with col2:

    if st.button(
        t("delete_client"),
        use_container_width=True,
    ):
        st.session_state["delete_from_detail"] = True
        st.rerun()


# ============================================================
# DELETE CLIENT CONFIRMATION
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
                ⚠️ {'ဖျက်ရန် အတည်ပြုပါ' if IS_MY else 'Confirm Delete'}
            </h3>
            <p style="color: #c62828; margin: 0.5rem 0 0 0; font-size: 1rem;">
                '<b>{client_display_name}</b>'
                {
                    'နဲ့ ရှင်းတမ်းအားလုံးကို ဖျက်ပါမည်လား?'
                    if IS_MY
                    else 'and all statements will be deleted. Are you sure?'
                }
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 1, 4])

    with col1:

        if st.button(
            t("delete"),
            type="primary",
            use_container_width=True,
        ):

            try:
                db.delete_client(client_id)

                st.session_state.pop("selected_client_id", None)
                st.session_state.pop("selected_client_name", None)
                st.session_state["delete_from_detail"] = False

                st.success(
                    f"✓ '{client_display_name}' "
                    f"{'ဖျက်ပြီးပါပြီ' if IS_MY else 'deleted successfully'}"
                )

                st.switch_page("pages/1_Clients.py")

            except Exception as e:
                st.error(f"❌ Error: {e}")

    with col2:

        if st.button(
            t("cancel"),
            use_container_width=True,
        ):
            st.session_state["delete_from_detail"] = False
            st.rerun()


# ============================================================
# NOTES SECTION
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
    st.caption(
        f"📅 {t('created')}: "
        f"{format_date_mm(client.get('created_at', ''))}"
    )

with col2:
    st.caption(
        f"🔄 {t('updated')}: "
        f"{format_date_mm(client.get('updated_at', ''))}"
    )


# ============================================================
# AI CHAT BOX
# ============================================================

st.divider()

st.markdown("### 🤖 AI စာရင်းအကူအညီ (Ask AI)")


chat_key = f"ai_chat_history_{client_id}"

if chat_key not in st.session_state:
    st.session_state[chat_key] = []


client_context = (
    f"ဖောက်သည်အမည်: {client_display_name}\n"
    f"လုပ်ငန်းအမျိုးအစား: {client.get('business_type', '')}\n"
    f"ရွေးထားသောကာလ: {selected_period}\n"
)


# ------------------------------------------------------------
# BUILD AI CONTEXT — SELECTED PERIOD ONLY
# ------------------------------------------------------------

try:

    tpl_data = get_statement_for_period(
        client_id,
        "trading_pl",
        selected_period,
    )

    if tpl_data:

        tpl_info = parse_json_data(
            tpl_data.get("data")
        )

        if tpl_info:

            client_context += f"""
အောက်ပါအချက်အလက်များသည် {selected_period} ကာလ၏ Trading P&L စာရင်းဖြစ်သည်။

အရောင်း: {format_number(tpl_info.get('_total_revenue', 0))}
ကုန်ကျစရိတ်: {format_number(tpl_info.get('_total_cos', 0))}
အမြတ်: {format_number(tpl_info.get('_gross_profit', 0))}
အသုံးစရိတ်: {format_number(tpl_info.get('_total_expenses', 0))}
အသားတင်အမြတ်: {format_number(tpl_info.get('_net_profit', 0))}
"""

except Exception as e:
    st.warning(
        f"AI Context ရယူရာတွင် အမှားရှိနေသည်: {e}"
    )


# ------------------------------------------------------------
# CHAT HISTORY
# ------------------------------------------------------------

for message in st.session_state[chat_key]:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ------------------------------------------------------------
# CHAT INPUT
# ------------------------------------------------------------

if prompt := st.chat_input(
    "ဒီဖောက်သည်ရဲ့ စာရင်းအခြေအနေကို မေးပါ..."
):

    st.session_state[chat_key].append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):

        with st.spinner("AI စဉ်းစားနေသည်..."):

            try:
                response = get_ai_response(
                    prompt,
                    client_context,
                )

                if not response:
                    response = (
                        "AI မှ အဖြေမရရှိပါ။ ထပ်မံကြိုးစားကြည့်ပါ။"
                        if IS_MY
                        else "No response was returned. Please try again."
                    )

            except Exception as e:
                response = (
                    f"AI Error: {e}"
                )

            st.markdown(response)

    st.session_state[chat_key].append(
        {
            "role": "assistant",
            "content": response,
        }
    )
