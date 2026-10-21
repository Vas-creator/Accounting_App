# pages/8_Backup.py
"""
Backup — ဒေတာများ သိမ်းဆည်းခြင်း နှင့် ပြန်လည်သွင်းယူခြင်း
"""

import streamlit as st
import json
from datetime import datetime
from core import db
from core.utils import format_date_mm

st.set_page_config(
    page_title="Backup & Restore",
    page_icon="💾",
    layout="wide",
)

# Auth Check
if not st.session_state.get("authentication_status"):
    st.warning("⚠️ ကျေးဇူးပြု၍ အရင် ဝင်ရောက်ပါ")
    st.switch_page("app.py")
    st.stop()

# Sidebar
with st.sidebar:
    st.markdown(
        """
        <div style="text-align: center; padding: 0.5rem 0;">
            <h2 style="color: #1f4788; font-size: 1.3rem; margin: 0;">📊 စာရင်း အက်ပ်</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()
    if st.button("🏠 ပင်မ", use_container_width=True):
        st.switch_page("app.py")

# Header
st.markdown(
    """
    <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 1.5rem; border-radius: 12px; color: white; margin-bottom: 1.5rem;">
        <h1 style="margin: 0; font-size: 1.8rem;">💾 Backup & Restore</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1rem; opacity: 0.95;">
            သင့်ရဲ့ ဒေတာအားလုံးကို လုံခြုံစွာ သိမ်းဆည်းထားပါ
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------
# EXPORT (BACKUP)
# ------------------------------------------------
st.markdown("### 📥 ဒေတာ သိမ်းဆည်းရန် (Backup)")
st.info("အောက်ပါ ခလုတ်ကို နှိပ်ပြီး သင့်ရဲ့ ဒေတာအားလုံးကို JSON ဖိုင်အနေနဲ့ သိမ်းဆည်းထားပါ။ (ဒီဖိုင်ကို ကွန်ပျူတာထဲမှာ သေချာသိမ်းထားပါ။)")

if st.button("📥 Backup ဆွဲမည် (Download JSON)", type="primary"):
    try:
        backup_data = db.get_all_data_for_backup()
        backup_json = json.dumps(backup_data, ensure_ascii=False, indent=2)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        st.download_button(
            "⬇️ ဖိုင်ရယူရန် (Download)",
            data=backup_json,
            file_name=f"accounting_backup_{timestamp}.json",
            mime="application/json",
        )
        st.success("✓ Backup ဖိုင် အဆင်သင့်ဖြစ်ပါပြီ။ အောက်က ခလုတ်ကို နှိပ်ပြီး သိမ်းပါ။")
    except Exception as e:
        st.error(f"❌ Error: {e}")

st.divider()

# ------------------------------------------------
# AUTO-SAVE (To Server File)
# ------------------------------------------------
st.markdown("### 🤖 အလိုအလျောက် သိမ်းဆည်းခြင်း (Auto-Save)")
st.info("ဤခလုတ်ကို နှိပ်လိုက်ပါက သင့်ဒေတာများကို ဆာဗာ၏ `backups` ဖိုလ်ဒါအတွင်းသို့ ဖိုင်အဖြစ် အလိုအလျောက် သိမ်းဆည်းပေးသွားမည် ဖြစ်ပါသည်။ (ဖိုင်အရေအတွက် ၅ ခုအထိသာ သိမ်းဆည်းထားမည်)။")

if st.button("🤖 Auto-Save လုပ်မည် (Server File)", type="secondary"):
    try:
        success = db.auto_backup_to_file()
        if success:
            st.success("✓ ဒေတာများကို ဆာဗာ၏ `backups` ဖိုလ်ဒါထဲသို့ သိမ်းဆည်းပြီးပါပြီ။")
        else:
            st.error("❌ Auto-Save လုပ်ရာတွင် အမှားအယွင်းရှိပါသည်။")
    except Exception as e:
        st.error(f"❌ Error: {e}")

# ------------------------------------------------
# IMPORT (RESTORE)
# ------------------------------------------------
st.markdown("### 📤 ဒေတာ ပြန်လည်သွင်းရန် (Restore)")
st.warning("⚠️ သတိပြုရန် - ဤနေရာတွင် ဖိုင်တင်ခြင်းက လက်ရှိဒေတာများကို အစားထိုးပစ်နိုင်ပါသည်။ သေချာစဉ်းစားပြီးမှ လုပ်ပါ။")

uploaded_file = st.file_uploader("Backup ဖိုင် (.json) ကို ရွေးပါ", type=["json"])

if uploaded_file is not None:
    try:
        backup_data = json.load(uploaded_file)
        
        st.markdown("**Backup ဖိုင်ထဲမှာ ပါဝင်တာတွေ:**")
        for table, records in backup_data.items():
            if isinstance(records, list):
                st.write(f"- {table}: {len(records)} ခု")
        
        if st.button("⚠️ ဒေတာများ ပြန်လည်သွင်းမည်", type="primary"):
            try:
                success = db.restore_from_backup(backup_data)
                if success:
                    st.success("✓ ဒေတာများ အောင်မြင်စွာ ပြန်လည်သွင်းပြီးပါပြီ။")
                    st.balloons()
                    # Refresh လုပ်မယ်
                    st.rerun()
                else:
                    st.error("❌ ဒေတာပြန်လည်သွင်းရာတွင် အမှားအယွင်းရှိပါသည်။")
            except Exception as e:
                st.error(f"❌ Error: {e}")
            
    except Exception as e:
        st.error(f"❌ ဖိုင်ဖတ်ရာတွင် အမှားအယွင်းရှိပါသည်: {e}")