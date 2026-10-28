# pages/1_Clients.py
import streamlit as st
from core import db
from core.utils import format_date_mm, info_box, clean_html
from core.translations import t

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Clients",
    page_icon="👥",
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
# BUSINESS TYPES
# ============================================================

# ============================================================
# BUSINESS TYPES (Bilingual)
# ============================================================

BUSINESS_TYPES_MY = [
    "ကုန်ထုတ်လုပ်ငန်း",
    "အရောင်းအဝယ်လုပ်ငန်း",
    "ဝန်ဆောင်မှုလုပ်ငန်း",
    "လယ်ယာစိုက်ပျိုးရေး",
    "ဆောက်လုပ်ရေး",
    "သယ်ယူပို့ဆောင်ရေး",
    "လက်လီ/လက်ကား",
    "အခြား",
]

BUSINESS_TYPES_EN = [
    "Manufacturing",
    "Trading",
    "Service",
    "Agriculture",
    "Construction",
    "Transportation",
    "Retail/Wholesale",
    "Others",
]

MANUFACTURING_TYPES_MY = [
    "ဆန်စက်",
    "သစ်စက်",
    "အထည်အလိပ်",
    "အစားအစာ ထုတ်လုပ်မှု",
    "အခြား (Other)",
]

MANUFACTURING_TYPES_EN = [
    "Rice Mill",
    "Saw Mill",
    "Textile",
    "Food Processing",
    "Other",
]

TRADING_TYPES_MY = [
    "ဆန်စပါးနှင့်ပဲမျိုးစုံရောင်းဝယ်ရေးလုပ်ငန်း",
    "ဓါတ်မြေဩဇာနှင့်စိုက်ပျိုးရေးဆေးရောင်းဝယ်ရေးလုပ်ငန်း",
    "ရွှေဆိုင်လုပ်ငန်း",
    "အရက်ဆိုင်လုပ်ငန်း",
    "အုတ်၊ သဲ၊ ကျောက် ရောင်းဝယ်ရေးလုပ်ငန်း",
    "ဆန်နှင့် အိမ်ဆောက်ပစ္စည်းအရောင်းဆိုင်လုပ်ငန်း",
    "ဒိန်ချဉ် အရောင်းဆိုင်နှင့် လက်ကားဖြန့်ချိရေးလုပ်ငန်း",
    "ဆောက်လုပ်ရေးပစ္စည်းအရောင်းဆိုင်လုပ်ငန်း",
]

TRADING_TYPES_EN = [
    "Rice, Paddy and Bean Trading Business",
    "Fertilizer, Agricultural Chemical Store",
    "Gold and Jewellery Shop Business",
    "Liquor Store Business",
    "Brick, Sand, River Gravel Trading Business",
    "Rice, House Building Material Trading Business",
    "Yogurt Shop and Whole Sale Business",
    "Construction Material Shop Business",
]
# ============================================================
# PAGE HEADER
# ============================================================

st.markdown(f"""
    <div style="padding: 0.5rem 0 1.5rem 0;">
        <h1 style="color: #1f4788; font-size: 2.3rem; margin: 0;">{t('client_management')}</h1>
    </div>
""", unsafe_allow_html=True)

# ============================================================
# SIDEBAR — Navigation
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
    
    st.divider()
    
    st.caption(f"👤 {st.session_state.get('name', 'User')}")

# ============================================================
# SESSION STATE INIT
# ============================================================

if "show_add_form" not in st.session_state:
    st.session_state.show_add_form = False
if "editing_client_id" not in st.session_state:
    st.session_state.editing_client_id = None
if "delete_confirm_id" not in st.session_state:
    st.session_state.delete_confirm_id = None
if "search_query" not in st.session_state:
    st.session_state.search_query = ""

# ============================================================
# TOP BAR — Search + Add Button
# ============================================================

col1, col2, col3 = st.columns([3, 2, 1])

with col1:
    search = st.text_input(
        t('search_placeholder'),
        value=st.session_state.search_query,
        placeholder=t('search_placeholder'),
        label_visibility="collapsed",
        key="search_input",
    )
    st.session_state.search_query = search

with col3:
    if st.button(
        t('add_client'), 
        use_container_width=True, 
        type="primary",
        key="add_client_btn_top"
    ):
        st.session_state.show_add_form = True
        st.session_state.editing_client_id = None
        st.rerun()

# ============================================================
# ADD CLIENT FORM
# ============================================================

if st.session_state.show_add_form:
    st.markdown(
        f"""
        <h3 style="color: #1565c0; margin-top: 1rem;">
            {t('add_client')}
        </h3>
        """,
        unsafe_allow_html=True,
    )
    
    col1, col2 = st.columns(2)
    lang = st.session_state.get("language", "my")
    
    with col1:
        name = st.text_input(
            f"{t('client_name')} (Optional)",
            placeholder="ဥပမာ — ရွှေမြို့တော် ကုမ္ပဏီ" if lang == "my" else "e.g. — Shwe Myo Taw Co.",
            key="add_name",
        )
        business_name = st.text_input(
            t('business_name'),
            placeholder="ဥပမာ — ရွှေမြို့တော် လီမိတက်" if lang == "my" else "e.g. — Shwe Myo Taw Ltd.",
            key="add_business_name",
        )
        
        # ⭐ ဘာသာစကားအလိုက် Business Type List ရွေးမယ်
        current_business_types = BUSINESS_TYPES_MY if lang == "my" else BUSINESS_TYPES_EN
        
                # ⭐ on_change ကို ထည့်ပါ (ရွေးတာနဲ့ Refresh ဖြစ်အောင်)
        def on_business_type_change():
            pass # ဒီ function က ဘာမှ မလုပ်ပါဘူး၊ Refresh ဖြစ်ဖို့ပဲ လုပ်တာပါ

        business_type = st.selectbox(
            t('business_type'),
            options=[""] + current_business_types,
            key="add_business_type_select",
            on_change=on_business_type_change, # ⭐ ဒါလေး ထည့်ပါ
        )
        
        # ⭐ Manufacturing Dropdown
        manufacturing_type = ""
        if business_type in ["ကုန်ထုတ်လုပ်ငန်း", "Manufacturing"]:
            current_mfg_types = MANUFACTURING_TYPES_MY if lang == "my" else MANUFACTURING_TYPES_EN
            manufacturing_type = st.selectbox(
                "ကုန်ထုတ်လုပ်မှု အမျိုးအစား" if lang == "my" else "Manufacturing Type",
                options=[""] + current_mfg_types,
                key="add_manufacturing_type_select",
            )
        
        # ⭐ Trading Dropdown
        trading_type = ""
        if business_type in ["အရောင်းအဝယ်လုပ်ငန်း", "Trading"]:
            current_trading_types = TRADING_TYPES_MY if lang == "my" else TRADING_TYPES_EN
            trading_type = st.selectbox(
                "အရောင်းအဝယ် အမျိုးအစား" if lang == "my" else "Trading Type",
                options=[""] + current_trading_types,
                key="add_trading_type_select",
            )
        
        # ⭐ "အခြား" ရွေးရင် Custom Input ပြမယ်
        custom_business_type = ""
        if business_type in ["အခြား", "Others"]:
            custom_business_type = st.text_input(
                "အခြား လုပ်ငန်းအမျိုးအစား ရိုက်ထည့်ပါ" if lang == "my" else "Please specify Business Type",
                key="add_custom_business_type"
            )
    
    with col2:
        email = st.text_input(
            t('email'),
            placeholder="example@email.com",
            key="add_email",
        )
        fiscal_year_end = st.text_input(
            "ဘဏ္ဍာရေးနှစ် ကုန်ဆုံးရက်" if lang == "my" else "Fiscal Year End",
            value="09-30",
            placeholder="MM-DD",
            key="add_fiscal_year_end",
        )
        address = st.text_input(
            t('address'),
            placeholder="ဥပမာ — ရန်ကုန်မြို့" if lang == "my" else "e.g. — Yangon",
            key="add_address",
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_a, col_b, col_c = st.columns([1, 1, 3])
    with col_a:
        if st.button(t('save'), use_container_width=True, type="primary", key="add_save_btn"):
            if not business_name or len(business_name.strip()) < 2:
                st.error("❌ လုပ်ငန်း အမည် ဖြည့်ပါ (အနည်းဆုံး ၂ လုံး)" if lang == "my" else "❌ Please enter Business Name (min 2 chars)")
            else:
                try:
                    final_business_type = business_type
                    
                    if business_type in ["အခြား", "Others"] and custom_business_type:
                        final_business_type = custom_business_type.strip()
                    
                    if business_type in ["ကုန်ထုတ်လုပ်ငန်း", "Manufacturing"] and manufacturing_type:
                        final_business_type = f"{business_type} - {manufacturing_type}"
                    
                    if business_type in ["အရောင်းအဝယ်လုပ်ငန်း", "Trading"] and trading_type:
                        final_business_type = f"{business_type} - {trading_type}"

                    db.create_client(
                        name=clean_html(name.strip()),
                        business_name=clean_html(business_name.strip()),
                        business_type=final_business_type,
                        email=email.strip(),
                        address=clean_html(address.strip()),
                        fiscal_year_end=fiscal_year_end.strip() or "09-30",
                    )
                    
                    display_name = name if name else business_name
                    st.success(f"✓ ဖောက်သည် '{display_name}' ထည့်ပြီးပါပြီ" if lang == "my" else f"✓ Client '{display_name}' added successfully")
                    st.session_state.show_add_form = False
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")
    with col_b:
        if st.button(t('cancel'), use_container_width=True, key="add_cancel_btn"):
            st.session_state.show_add_form = False
            st.rerun()
    
    st.divider()

# ============================================================
# EDIT CLIENT FORM
# ============================================================

if st.session_state.editing_client_id is not None:
    client = db.get_client(st.session_state.editing_client_id)
    
    if client:
        display_header_name = client['name'] if client['name'] else client['business_name']
        st.markdown(
            f"""
            <h3 style="color: #f57c00; margin-top: 1rem;">
                {t('edit')} — {clean_html(display_header_name)}
            </h3>
            """,
            unsafe_allow_html=True,
        )
        
        col1, col2 = st.columns(2)
        lang = st.session_state.get("language", "my")
        
        with col1:
            name = st.text_input(
                f"{t('client_name')} (Optional)",
                value=clean_html(client.get("name", "")),
                key="edit_name",
            )
            business_name = st.text_input(
                t('business_name'),
                value=clean_html(client.get("business_name", "")) or "",
                key="edit_business_name",
            )
            
            # ⭐ လက်ရှိ သိမ်းထားတဲ့ Business Type ကို ခွဲထုတ်မယ်
            current_type = client.get("business_type", "") or ""
            base_type = current_type
            current_mfg_type = ""
            current_trading_type = ""
            
            if " - " in current_type:
                parts = current_type.split(" - ")
                base_type = parts[0]
                detail_type = parts[1] if len(parts) > 1 else ""
                
                if base_type in ["ကုန်ထုတ်လုပ်ငန်း", "Manufacturing"]:
                    current_mfg_type = detail_type
                elif base_type in ["အရောင်းအဝယ်လုပ်ငန်း", "Trading"]:
                    current_trading_type = detail_type
            
            current_business_types = BUSINESS_TYPES_MY if lang == "my" else BUSINESS_TYPES_EN
            
            # "အခြား" ဖြစ်နေရင် သတ်မှတ်မယ်
            if base_type not in current_business_types:
                if base_type:
                    base_type = "အခြား (Others)" if lang == "my" else "Others"
            
            type_index = 0
            if base_type in current_business_types:
                type_index = current_business_types.index(base_type) + 1
            
            def on_edit_business_type_change():
                pass

            business_type = st.selectbox(
                t('business_type'),
                options=[""] + current_business_types,
                index=type_index,
                key="edit_business_type_select",
                on_change=on_edit_business_type_change, # ⭐ ဒါလေး ထည့်ပါ
            )

            # Other အတွက် Custom Input
            custom_business_type = ""
            if business_type in ["အခြား", "Others"]:
                default_custom = current_type if (base_type in ["အခြား", "Others"] and current_type != base_type) else ""
                custom_business_type = st.text_input(
                    "အခြား လုပ်ငန်းအမျိုးအစား ရိုက်ထည့်ပါ" if lang == "my" else "Please specify Business Type",
                    value=default_custom,
                    key="edit_custom_business_type"
                )

            # Manufacturing Dropdown
            manufacturing_type = ""
            if business_type in ["ကုန်ထုတ်လုပ်ငန်း", "Manufacturing"]:
                current_mfg_types = MANUFACTURING_TYPES_MY if lang == "my" else MANUFACTURING_TYPES_EN
                mfg_index = 0
                if current_mfg_type in current_mfg_types:
                    mfg_index = current_mfg_types.index(current_mfg_type) + 1
                    
                manufacturing_type = st.selectbox(
                    "ကုန်ထုတ်လုပ်မှု အမျိုးအစား" if lang == "my" else "Manufacturing Type",
                    options=[""] + current_mfg_types,
                    index=mfg_index,
                    key="edit_manufacturing_type_select",
                )
            
            # Trading Dropdown
            trading_type = ""
            if business_type in ["အရောင်းအဝယ်လုပ်ငန်း", "Trading"]:
                current_trading_types = TRADING_TYPES_MY if lang == "my" else TRADING_TYPES_EN
                trade_index = 0
                if current_trading_type in current_trading_types:
                    trade_index = current_trading_types.index(current_trading_type) + 1
                    
                trading_type = st.selectbox(
                    "အရောင်းအဝယ် အမျိုးအစား" if lang == "my" else "Trading Type",
                    options=[""] + current_trading_types,
                    index=trade_index,
                    key="edit_trading_type_select",
                )
        
        with col2:
            email = st.text_input(
                t('email'),
                value=client.get("email", "") or "",
                key="edit_email",
            )
            fiscal_year_end = st.text_input(
                "ဘဏ္ဍာရေးနှစ် ကုန်ဆုံးရက်" if lang == "my" else "Fiscal Year End",
                value=client.get("fiscal_year_end", "09-30") or "09-30",
                key="edit_fiscal_year_end",
            )
            address = st.text_input(
                t('address'),
                value=clean_html(client.get("address", "")) or "",
                key="edit_address",
            )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col_a, col_b, col_c = st.columns([1, 1, 3])
        with col_a:
            if st.button(t('save'), use_container_width=True, type="primary", key="edit_save_btn"):
                if not business_name or len(business_name.strip()) < 2:
                    st.error("❌ လုပ်ငန်း အမည် ဖြည့်ပါ" if lang == "my" else "❌ Please enter Business Name")
                else:
                    try:
                        final_business_type = business_type
                        
                        if business_type in ["အခြား", "Others"] and custom_business_type:
                            final_business_type = custom_business_type.strip()
                            
                        if business_type in ["ကုန်ထုတ်လုပ်ငန်း", "Manufacturing"] and manufacturing_type:
                            final_business_type = f"{business_type} - {manufacturing_type}"
                            
                        if business_type in ["အရောင်းအဝယ်လုပ်ငန်း", "Trading"] and trading_type:
                            final_business_type = f"{business_type} - {trading_type}"

                        db.update_client(
                            st.session_state.editing_client_id,
                            name=clean_html(name.strip()),
                            business_name=clean_html(business_name.strip()),
                            business_type=final_business_type,
                            email=email.strip(),
                            address=clean_html(address.strip()),
                            fiscal_year_end=fiscal_year_end.strip() or "09-30",
                        )
                        st.success("✓ ပြင်ဆင်ပြီးပါပြီ" if lang == "my" else "✓ Updated successfully")
                        st.session_state.editing_client_id = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
        with col_b:
            if st.button(t('cancel'), use_container_width=True, key="edit_cancel_btn"):
                st.session_state.editing_client_id = None
                st.rerun()
        
        st.divider()

# ============================================================
# CLIENT LIST
# ============================================================

try:
    all_clients = db.get_all_clients()
except Exception as e:
    st.error(f"Database error: {e}")
    all_clients = []

if st.session_state.search_query:
    q = st.session_state.search_query.lower()
    all_clients = [
        c for c in all_clients
        if q in (c.get("name") or "").lower()
        or q in (c.get("email") or "").lower()
        or q in (c.get("business_name") or "").lower()
    ]

search_info = f'(ရှာဖွေမှု — "{st.session_state.search_query}")' if (st.session_state.search_query and st.session_state.get("language") == "my") else f'(Search — "{st.session_state.search_query}")' if st.session_state.search_query else ''

st.markdown(
    f"""
    <p style="color: #666; font-size: 1rem; margin: 0.5rem 0;">
        {t('total')} <b style="color: #1565c0;">{len(all_clients)}</b> {t('clients')}
        {search_info}
    </p>
    """,
    unsafe_allow_html=True,
)

st.markdown("<br>", unsafe_allow_html=True)

# ============================================================
# EMPTY STATE
# ============================================================

if not all_clients:
    if st.session_state.search_query:
        info_box(
            f"'{st.session_state.search_query}' နဲ့ ကိုက်ညီတဲ့ ဖောက်သည် မတွေ့ပါ" if st.session_state.get("language") == "my" else f"No clients found matching '{st.session_state.search_query}'",
            "warning",
        )
    else:
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 3rem 2rem;
                border-radius: 16px;
                text-align: center;
                color: white;
                margin: 2rem 0;
            ">
                <h1 style="font-size: 4rem; margin: 0;">👥</h1>
                <h2 style="margin: 1rem 0 0.5rem 0; font-size: 1.5rem;">
                    {'ဖောက်သည် မရှိသေးပါ' if st.session_state.get('language') == 'my' else 'No clients yet'}
                </h2>
                <p style="opacity: 0.9; font-size: 1rem;">
                    {'➕ ဖောက်သည် အသစ် ကို နှိပ်ပြီး စတင်ပါ' if st.session_state.get('language') == 'my' else 'Click ➕ Add New Client to start'}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.stop()

# ============================================================
# CLIENT CARDS
# ============================================================

for client in all_clients:
    with st.container():
        c_name = clean_html(client.get('name', ''))
        c_business = clean_html(client.get('business_name', ''))
        c_email = clean_html(client.get('email', ''))
        c_address = clean_html(client.get('address', ''))
        c_type = clean_html(client.get('business_type', ''))
        
        # Client Name မရှိရင် Business Name ကို အဓိက ပြမယ်
        display_title = c_name if c_name else c_business
        
        details_html = ""
        # Title မှာ Name ပြထားပြီးသားဖြစ်လို့ Business Name ကို ထပ်မပြဘဲ ထားမယ် (တူနေရင်)
        if c_business and c_business != display_title:
            details_html += f'🏢 {c_business} &nbsp;'
        if c_email:
            details_html += f'•&nbsp; 📧 {c_email} &nbsp;'
        if c_address:
            details_html += f'•&nbsp; 📍 {c_address}'

        st.markdown(
            f"""
            <div style="
                background-color: white;
                border: 1px solid #e0e0e0;
                border-left: 5px solid #1565c0;
                border-radius: 8px;
                padding: 1rem 1.2rem;
                margin-bottom: 0.5rem;
            ">
                <h3 style="margin: 0; color: #1f4788; font-size: 1.2rem;">
                    👤 {display_title}
                </h3>
                <p style="margin: 0.3rem 0 0 0; color: #666; font-size: 0.95rem;">
                    {details_html}
                </p>
                <p style="margin: 0.3rem 0 0 0; color: #999; font-size: 0.85rem;">
                    {f'💼 {c_type}' if c_type else ''}
                    &nbsp;•&nbsp; 📅 {'နောက်ဆုံး' if st.session_state.get('language') == 'my' else 'Last'}: {format_date_mm(client.get('updated_at', ''))}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
        
        with col1:
            if st.button(t('details'), key=f"detail_{client['id']}", use_container_width=True):
                st.session_state["selected_client_id"] = client["id"]
                st.session_state["selected_client_name"] = display_title
                st.switch_page("pages/2_Client_Detail.py")
        with col2:
            if st.button(t('edit'), key=f"edit_{client['id']}", use_container_width=True):
                st.session_state.editing_client_id = client["id"]
                st.session_state.show_add_form = False
                st.rerun()
        with col3:
            if st.button(t('delete'), key=f"del_{client['id']}", use_container_width=True):
                st.session_state.delete_confirm_id = client["id"]
                st.rerun()
        with col4:
            if st.button("🏭", key=f"quick_mfg_{client['id']}", help="ကုန်ထုတ် စာရင်း", use_container_width=True):
                st.session_state["selected_client_id"] = client["id"]
                st.session_state["selected_client_name"] = display_title
                st.switch_page("pages/3_Manufacturing.py")
        with col5:
            if st.button("📊", key=f"quick_bs_{client['id']}", help="လက်ကျန်စာရင်း", use_container_width=True):
                st.session_state["selected_client_id"] = client["id"]
                st.session_state["selected_client_name"] = display_title
                st.switch_page("pages/5_Balance_Sheet.py")
        
        st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)

# ============================================================
# DELETE CONFIRMATION DIALOG
# ============================================================

if st.session_state.delete_confirm_id is not None:
    client = db.get_client(st.session_state.delete_confirm_id)
    
    if client:
        c_name = clean_html(client.get('name', ''))
        c_business = clean_html(client.get('business_name', ''))
        display_delete_name = c_name if c_name else c_business

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
                    ⚠️ {'ဖျက်ရန် အတည်ပြုပါ' if st.session_state.get('language') == 'my' else 'Confirm Delete'}
                </h3>
                <p style="color: #c62828; margin: 0.5rem 0 0 0; font-size: 1rem;">
                    '<b>{display_delete_name}</b>' {'ကို ဖျက်ပါမည်လား? ဒီဖောက်သည်ရဲ့ ရှင်းတမ်းအားလုံးလည်း ပါသွားပါမည်။' if st.session_state.get('language') == 'my' else 'will be deleted along with all its statements. Are you sure?'}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button(t('delete'), type="primary", use_container_width=True, key="confirm_del_btn"):
                try:
                    db.delete_client(st.session_state.delete_confirm_id)
                    st.success(f"✓ '{display_delete_name}' {'ဖျက်ပြီးပါပြီ' if st.session_state.get('language') == 'my' else 'deleted successfully'}")
                    st.session_state.delete_confirm_id = None
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        with col2:
            if st.button(t('cancel'), use_container_width=True, key="cancel_del_btn"):
                st.session_state.delete_confirm_id = None
                st.rerun()