# core/db.py
import streamlit as st
from st_supabase_connection import SupabaseConnection
import json
import os
from datetime import datetime

# ============================================================
# SUPABASE CONNECTION
# ============================================================

def get_supabase():
    """Supabase Connection ကို ရယူခြင်း (URL နဲ့ Key ကို တိုက်ရိုက်ထည့်ထားတယ်)"""
    try:
        conn = st.connection("supabase", type=SupabaseConnection)
        conn.table("clients").select("id").limit(1).execute()
        return conn
    except Exception:
        import os
        from supabase import create_client
        url = "https://oicutagoajugirdjoats.supabase.co"
        key = "sb_publishable_KEH3kxBvss2YZsJv6Ef5SA_uyfgmWyT"
        return create_client(url, key)

def init_db():
    """Supabase မှာ Table တွေ ရှိပြီးသားဖြစ်လို့ ဘာမှ လုပ်စရာ မလိုပါ"""
    pass

# ============================================================
# DASHBOARD HELPERS
# ============================================================

def get_dashboard_stats() -> dict:
    """Dashboard အတွက် stats ရယူခြင်း"""
    try:
        conn = get_supabase()
        
        res = conn.table("clients").select("id", count="exact").execute()
        total_clients = res.count if res.count else 0
        
        total_statements = 0
        for table in ["manufacturing", "trading_pl", "balance_sheet", "cash_flow"]:
            try:
                res = conn.table(table).select("id", count="exact").execute()
                total_statements += res.count if res.count else 0
            except Exception:
                pass
        
        try:
            res = conn.table("clients").select("created_at").order("created_at", desc=True).limit(1).execute()
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
    try:
        conn = get_supabase()
        res = conn.table("clients").select("*").order("created_at", desc=True).limit(limit).execute()
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
    conn = get_supabase()
    data = {
        "name": name,
        "business_name": business_name,
        "business_type": business_type,
        "email": email,
        "address": address,
        "fiscal_year_end": fiscal_year_end,
    }
    res = conn.table("clients").insert(data).execute()
    return res.data[0]["id"]


def get_all_clients() -> list:
    """ဖောက်သည် အားလုံး"""
    try:
        conn = get_supabase()
        res = conn.table("clients").select("*").order("name").execute()
        return res.data
    except Exception:
        return []


def get_client(client_id: int):
    """ဖောက်သည် တစ်ဦး"""
    try:
        conn = get_supabase()
        res = conn.table("clients").select("*").eq("id", client_id).execute()
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
    
    try:
        conn = get_supabase()
        res = conn.table("clients").update(fields_to_update).eq("id", client_id).execute()
        return len(res.data) > 0
    except Exception as e:
        print(f"Update error: {e}")
        return False


def delete_client(client_id: int) -> bool:
    """ဖောက်သည် ဖျက်ခြင်း"""
    try:
        conn = get_supabase()
        res = conn.table("clients").delete().eq("id", client_id).execute()
        return len(res.data) > 0
    except Exception as e:
        print(f"Delete error: {e}")
        return False


def count_clients() -> int:
    """ဖောက်သည် အရေအတွက်"""
    try:
        conn = get_supabase()
        res = conn.table("clients").select("id", count="exact").execute()
        return res.count if res.count else 0
    except Exception:
        return 0


# ============================================================
# STATEMENT HELPERS (HISTORY ENABLED)
# ============================================================

def get_statement(client_id: int, statement_type: str, period_end: str = None):
    """
    ရှင်းတမ်း တစ်ခု ရယူခြင်း။
    period_end ပေးထားရင် အဲ့ဒီကာလရဲ့ စာရင်းကို ယူမယ်။
    မပေးထားရင် နောက်ဆုံးသိမ်းထားတာကို ယူမယ်။
    """
    try:
        conn = get_supabase()
        query = conn.table(statement_type).select("*").eq("client_id", client_id)
        
        if period_end:
            query = query.eq("period_end", period_end)
            
        res = query.order("id", desc=True).limit(1).execute()
        return res.data[0] if res.data else None
    except Exception:
        return None


def get_statement_history(client_id: int, statement_type: str) -> list:
    """ရှင်းတမ်း တစ်ခုရဲ့ ကာလအလိုက် စာရင်းအားလုံး (History) ကို ရယူခြင်း"""
    try:
        conn = get_supabase()
        res = conn.table(statement_type).select("*").eq("client_id", client_id).order("period_end", desc=True).execute()
        return res.data if res.data else []
    except Exception as e:
        print(f"History error: {e}")
        return []


def save_statement(client_id: int, statement_type: str,
                   period_end: str = "", data_json: str = "",
                   as_at_date: str = "", custom_data: list = None, **kwargs) -> int:
    """
    ရှင်းတမ်း သိမ်းခြင်း။ 
    ကာလ (period_end) တူရင် အဟောင်းကို Update လုပ်မယ်။
    မတူရင် အသစ် (Insert) ထပ်ထည့်မယ် (History အတွက်)။
    """
    conn = get_supabase()
    
    if isinstance(data_json, str):
        data_dict = json.loads(data_json)
    else:
        data_dict = data_json
    
    date_val = period_end or as_at_date
    
    try:
        # ⭐ ကာလတူတဲ့ စာရင်း ရှိမရှိ စစ်မယ်
        existing = get_statement(client_id, statement_type, period_end=date_val)
        
        payload = {
            "period_end": date_val,
            "data": data_dict,
        }
        
        # trading_pl နဲ့ manufacturing အတွက် custom_data ထည့်မယ်
        if statement_type in ["trading_pl", "manufacturing"]:
            payload["custom_data"] = custom_data or []
        
        if existing:
            # ရှိရင် Update လုပ်မယ် (အဟောင်းကို ပြင်တာ)
            res = conn.table(statement_type).update(payload).eq("id", existing["id"]).execute()
            return existing["id"]
        else:
            # မရှိရင် အသစ်ထည့်မယ် (History အသစ်)
            payload["client_id"] = client_id
            res = conn.table(statement_type).insert(payload).execute()
            return res.data[0]["id"]
    except Exception as e:
        print(f"Save statement error: {e}")
        raise e

# ============================================================
# BACKUP & RESTORE
# ============================================================

def get_all_data_for_backup() -> dict:
    """ဒေတာအားလုံးကို Backup အတွက် ဆွဲထုတ်ခြင်း"""
    conn = get_supabase()
    
    backup = {
        "clients": [],
        "manufacturing": [],
        "trading_pl": [],
        "balance_sheet": [],
        "cash_flow": [],
    }
    
    for table in backup.keys():
        try:
            res = conn.table(table).select("*").execute()
            backup[table] = res.data or []
        except Exception as e:
            print(f"Backup error for {table}: {e}")
    
    return backup


def restore_from_backup(backup_data: dict) -> bool:
    """Backup ဖိုင်မှ ဒေတာများ ပြန်လည်သွင်းယူခြင်း"""
    conn = get_supabase()
    
    # ရှိပြီးသား ဒေတာတွေကို အရင်ရှင်းမယ် (လိုအပ်ရင်)
    # ... (ဒီအပိုင်းကို သတိထားရပါမယ်၊ ဒေတာဟောင်းတွေ အကုန်ပျက်သွားနိုင်လို့ပါ)
    
    # ဒါပေမယ့် လက်ရှိမှာတော့ Backup ထဲက ဒေတာတွေကိုပဲ ထပ်ဖြည့်သွားမယ်
    # (Duplicate ဖြစ်နိုင်တဲ့အတွက် သတိထားပါ)
    
    try:
        for table, records in backup_data.items():
            if not records:
                continue
            
            # ဒီနေရာမှာ သေချာစဉ်းစားဖို့ လိုပါတယ်
            # ဥပမာ - client_id တူတာတွေ ရှိရင် ဘယ်လိုလုပ်မလဲ?
            
            # လောလောဆယ် ရိုးရှင်းအောင် ဒေတာအသစ်တွေကိုပဲ ထည့်မယ်
            # (ဒါပေမယ့် ဒါက အန္တရာယ်ရှိနိုင်တဲ့အတွက် သေချာစဉ်းစားပါ)
            
            # အကောင်းဆုံးက ဒေတာဟောင်းကို မဖျက်ဘဲ ဒေတာအသစ်ကို သီးသန့်သိမ်းတာပါ
            pass
        
        return True
    except Exception as e:
        print(f"Restore error: {e}")
        return False

def restore_from_backup(backup_data: dict) -> bool:
    """Backup ဖိုင်မှ ဒေတာများ ပြန်လည်သွင်းယူခြင်း"""
    conn = get_supabase()
    
    try:
        # ⭐ ဒေတာဟောင်းတွေ အကုန်ရှင်းမယ် (ဒါပေမယ့် သတိထားရပါမယ်)
        # လက်ရှိ ဒေတာတွေကို မဖျက်ချင်ရင် ဒီအပိုင်းကို ဖျက်ပါ။
        for table in ["cash_flow", "balance_sheet", "trading_pl", "manufacturing", "clients"]:
            try:
                conn.table(table).delete().neq("id", 0).execute()
            except Exception as e:
                print(f"Delete error for {table}: {e}")
        
        # ⭐ Backup ထဲက ဒေတာတွေ ပြန်ထည့်မယ်
        for table, records in backup_data.items():
            if not records or not isinstance(records, list):
                continue
            
            # ဒေတာတွေကို Batch လုပ်ပြီး ထည့်မယ်
            try:
                conn.table(table).insert(records).execute()
            except Exception as e:
                print(f"Insert error for {table}: {e}")
                # တစ်ခုချင်း ထည့်ကြည့်မယ် (Batch မရရင်)
                for record in records:
                    try:
                        conn.table(table).insert(record).execute()
                    except Exception as inner_e:
                        print(f"Individual insert error: {inner_e}")
        
        return True
    except Exception as e:
        print(f"Restore error: {e}")
        return False


def auto_backup_to_file() -> bool:
    """ဒေတာများကို ဖိုင်အနေဖြင့် အလိုအလျောက် သိမ်းဆည်းခြင်း"""
    try:
        backup_data = get_all_data_for_backup()
        
        # Backup Folder မရှိရင် ဖန်တီးမယ်
        backup_dir = "backups"
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        # ဖိုင်နာမည်မှာ ရက်စွဲထည့်မယ်
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(backup_dir, f"auto_backup_{timestamp}.json")
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        # သက်တမ်းအရင့်ဆုံး ဖိုင်တွေကို ရှင်းမယ် (ဥပမာ - ၅ ခုထက် ပိုမသိမ်းဘူး)
        files = sorted([os.path.join(backup_dir, f) for f in os.listdir(backup_dir) if f.endswith(".json")])
        if len(files) > 5:
            for old_file in files[:-5]:
                os.remove(old_file)
                
        return True
    except Exception as e:
        print(f"Auto backup error: {e}")
        return False