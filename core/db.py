# core/db.py
import streamlit as st
from supabase import create_client, Client
import json

# ============================================================
# SUPABASE CONNECTION
# ============================================================

@st.cache_resource
def get_supabase() -> Client:
    """Supabase Client ကို ရယူခြင်း (secrets.toml မှ)"""
    url = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
    key = st.secrets["connections"]["supabase"]["SUPABASE_KEY"]
    return create_client(url, key)


def init_db():
    """Supabase မှာ Table တွေ ရှိပြီးသားဖြစ်လို့ ဘာမှ လုပ်စရာ မလိုပါ"""
    pass


# ============================================================
# DASHBOARD HELPERS
# ============================================================

def get_dashboard_stats() -> dict:
    """Dashboard အတွက် stats ရယူခြင်း"""
    supabase = get_supabase()
    try:
        # Total clients
        res = supabase.table("clients").select("*", count="exact").execute()
        total_clients = res.count if res.count else 0
        
        # Total statements (၄ ခုပေါင်း)
        total_statements = 0
        for table in ["manufacturing", "trading_pl", "balance_sheet", "cash_flow"]:
            try:
                res = supabase.table(table).select("*", count="exact").execute()
                total_statements += res.count if res.count else 0
            except Exception:
                pass
        
        # Latest update
        try:
            res = supabase.table("clients").select("created_at").order("created_at", desc=True).limit(1).execute()
            if res.data:
                latest = res.data[0]["created_at"]
                latest_update = latest[:10] if latest else "—"
            else:
                latest_update = "—"
        except Exception:
            latest_update = "—"
        
        return {
            "total_clients": total_clients,
            "total_statements": total_statements,
            "latest_update": latest_update,
        }
    except Exception as e:
        print(f"Dashboard stats error: {e}")
        return {"total_clients": 0, "total_statements": 0, "latest_update": "—"}


def get_recent_clients(limit: int = 5) -> list:
    """မကြာသေးမီ ဖောက်သည်များ ရယူခြင်း"""
    supabase = get_supabase()
    try:
        res = supabase.table("clients").select("*").order("created_at", desc=True).limit(limit).execute()
        return res.data
    except Exception:
        return []


# ============================================================
# CLIENT CRUD
# ============================================================

def create_client(name: str, business_name: str = "",
                  business_type: str = "", email: str = "",
                  address: str = "", fiscal_year_end: str = "09-30",
                  **kwargs) -> int:
    """ဖောက်သည် အသစ် ဖန်တီးခြင်း"""
    supabase = get_supabase()
    data = {
        "name": name,
        "business_name": business_name,
        "business_type": business_type,
        "email": email,
        "address": address,
        "fiscal_year_end": fiscal_year_end,
    }
    res = supabase.table("clients").insert(data).execute()
    return res.data[0]["id"]


def get_all_clients() -> list:
    """ဖောက်သည် အားလုံး"""
    supabase = get_supabase()
    try:
        res = supabase.table("clients").select("*").order("name").execute()
        return res.data
    except Exception:
        return []


def get_client(client_id: int):
    """ဖောက်သည် တစ်ဦး"""
    supabase = get_supabase()
    try:
        res = supabase.table("clients").select("*").eq("id", client_id).execute()
        return res.data[0] if res.data else None
    except Exception:
        return None


def update_client(client_id: int, **kwargs) -> bool:
    """ဖောက်သည် ပြင်ဆင်ခြင်း"""
    if not kwargs:
        return False
    
    allowed = {"name", "business_name", "business_type", 
               "email", "address", "fiscal_year_end"}
    fields_to_update = {k: v for k, v in kwargs.items() if k in allowed}
    
    if not fields_to_update:
        return False
    
    supabase = get_supabase()
    try:
        res = supabase.table("clients").update(fields_to_update).eq("id", client_id).execute()
        return len(res.data) > 0
    except Exception as e:
        print(f"Update error: {e}")
        return False


def delete_client(client_id: int) -> bool:
    """ဖောက်သည် ဖျက်ခြင်း"""
    supabase = get_supabase()
    try:
        res = supabase.table("clients").delete().eq("id", client_id).execute()
        return len(res.data) > 0
    except Exception as e:
        print(f"Delete error: {e}")
        return False


def count_clients() -> int:
    """ဖောက်သည် အရေအတွက်"""
    supabase = get_supabase()
    try:
        res = supabase.table("clients").select("*", count="exact").execute()
        return res.count if res.count else 0
    except Exception:
        return 0


# ============================================================
# STATEMENT HELPERS
# ============================================================

def get_statement(client_id: int, statement_type: str):
    """ရှင်းတမ်း တစ်ခု ရယူခြင်း"""
    supabase = get_supabase()
    try:
        res = supabase.table(statement_type).select("*").eq("client_id", client_id).order("id", desc=True).limit(1).execute()
        return res.data[0] if res.data else None
    except Exception:
        return None


def save_statement(client_id: int, statement_type: str,
                   period_end: str = "", data_json: str = "",
                   as_at_date: str = "", **kwargs) -> int:
    """ရှင်းတမ်း သိမ်းခြင်း (ရှိပြီးသားဆိုရင် update)"""
    supabase = get_supabase()
    
    # String ဖြစ်ရင် dict ပြောင်း
    if isinstance(data_json, str):
        data_dict = json.loads(data_json)
    else:
        data_dict = data_json
    
    date_val = period_end or as_at_date
    
    try:
        # ရှိပြီးသား စစ်
        existing = get_statement(client_id, statement_type)
        
        if existing:
            res = supabase.table(statement_type).update({
                "period_end": date_val,
                "data": data_dict,
            }).eq("id", existing["id"]).execute()
            return existing["id"]
        else:
            res = supabase.table(statement_type).insert({
                "client_id": client_id,
                "period_end": date_val,
                "data": data_dict,
            }).execute()
            return res.data[0]["id"]
    except Exception as e:
        print(f"Save statement error: {e}")
        raise e