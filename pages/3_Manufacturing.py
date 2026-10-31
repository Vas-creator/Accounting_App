# ============================================================
# CORE DATABASE — SUPABASE
# ============================================================

import os
import json
import time
from pathlib import Path
from datetime import datetime, date

import streamlit as st
from supabase import create_client


# ============================================================
# TABLE CONFIGURATION
# ============================================================

CLIENT_TABLE = "clients"

STATEMENT_TABLES = {
    "manufacturing",
    "trading_pl",
    "balance_sheet",
    "cash_flow",
}

BACKUP_TABLES = [
    CLIENT_TABLE,
    "manufacturing",
    "trading_pl",
    "balance_sheet",
    "cash_flow",
]


# ============================================================
# SUPABASE CONNECTION
# ============================================================

def get_supabase():
    """Streamlit Secrets သို့မဟုတ် Environment Variables မှ Supabase ချိတ်ဆက်ခြင်း။"""

    url = None
    key = None

    # Option 1: [connections.supabase]
    try:
        config = st.secrets.get("connections", {}).get("supabase", {})
        url = config.get("url") or config.get("SUPABASE_URL")
        key = config.get("key") or config.get("SUPABASE_KEY")
    except Exception:
        pass

    # Option 2: Top-level Streamlit Secrets
    if not url or not key:
        try:
            url = url or st.secrets.get("SUPABASE_URL")
            key = key or st.secrets.get("SUPABASE_KEY")
        except Exception:
            pass

    # Option 3: Environment Variables
    url = url or os.getenv("SUPABASE_URL")
    key = key or os.getenv("SUPABASE_KEY")

    if not url or not key:
        raise RuntimeError(
            "Supabase configuration missing: "
            f"url_found={bool(url)}, key_found={bool(key)}"
        )

    return create_client(url, key)


def init_db():
    """Database schema ကို application ထဲမှ မပြင်ပါ။"""
    return None


# ============================================================
# INTERNAL HELPERS
# ============================================================

def _validate_statement_type(statement_type):
    if statement_type not in STATEMENT_TABLES:
        raise ValueError(
            f"Unsupported statement type: {statement_type}"
        )


def _normalise_period(value):
    """Period ကို YYYY-MM-DD ပုံစံတစ်မျိုးတည်းဖြစ်အောင် ပြောင်းခြင်း။"""

    if value is None:
        return None

    if isinstance(value, datetime):
        return value.date().isoformat()

    if isinstance(value, date):
        return value.isoformat()

    text = str(value).strip()

    if not text:
        return None

    try:
        return date.fromisoformat(text[:10]).isoformat()
    except ValueError as exc:
        raise ValueError(
            f"Invalid period: {value!r}. Expected YYYY-MM-DD."
        ) from exc


def _decode_json(value, default=None):
    """Database မှ JSON string သို့မဟုတ် Python object ကို ပြန်လည်ဖတ်ခြင်း။"""

    if value is None:
        return default

    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError("Invalid JSON data.") from exc

    return value


def _statement_query(client_id, statement_type):
    """Client နှင့် Statement Type အလိုက် Query တည်ဆောက်ခြင်း။"""

    _validate_statement_type(statement_type)

    return (
        get_supabase()
        .table(statement_type)
        .select("*")
        .eq("client_id", client_id)
    )


# ============================================================
# DASHBOARD STATS
# ============================================================

def get_dashboard_stats() -> dict:
    """Dashboard အတွက် Client နှင့် Statement အရေအတွက်များ ရယူခြင်း။"""

    default_stats = {
        "total_clients": 0,
        "total_statements": 0,
        "latest_update": "—",
    }

    try:
        conn = get_supabase()

        # Total Clients
        clients_res = (
            conn.table(CLIENT_TABLE)
            .select("id", count="exact")
            .execute()
        )

        total_clients = clients_res.count or 0

        # Client တစ်ဦးချင်းစီတွင် Statement Type တစ်မျိုးစီ
        # အနည်းဆုံးတစ်ခု ရှိ/မရှိ စစ်ဆေးခြင်း။
        total_statements = 0

        clients = (
            conn.table(CLIENT_TABLE)
            .select("id")
            .execute()
        ).data or []

        for client in clients:
            client_id = client["id"]

            for table in sorted(STATEMENT_TABLES):
                result = (
                    conn.table(table)
                    .select("id")
                    .eq("client_id", client_id)
                    .limit(1)
                    .execute()
                )

                if result.data:
                    total_statements += 1

        # နောက်ဆုံးဖန်တီးထားသော Client ရက်စွဲ
        latest_res = (
            conn.table(CLIENT_TABLE)
            .select("created_at")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        latest_update = "—"

        if latest_res.data:
            created_at = latest_res.data[0].get("created_at")

            if created_at:
                latest_update = str(created_at)[:10]

        return {
            "total_clients": total_clients,
            "total_statements": total_statements,
            "latest_update": latest_update,
        }

    except Exception as exc:
        print(f"Dashboard stats error: {exc}")
        return default_stats


# ============================================================
# CLIENTS — READ
# ============================================================

def get_all_clients() -> list:
    """Client အားလုံးကို အမည်အလိုက် ရယူခြင်း။"""

    response = (
        get_supabase()
        .table(CLIENT_TABLE)
        .select("*")
        .order("name")
        .execute()
    )

    return response.data or []


def get_client(client_id):
    """Client ID တစ်ခုအတွက် Client အချက်အလက် ရယူခြင်း။"""

    response = (
        get_supabase()
        .table(CLIENT_TABLE)
        .select("*")
        .eq("id", client_id)
        .limit(1)
        .execute()
    )

    return response.data[0] if response.data else None


# ============================================================
# CLIENTS — CREATE
# ============================================================

def create_client(
    name="",
    business_name="",
    business_type="",
    email="",
    address="",
    fiscal_year_end="09-30",
):
    """Client အသစ်ဖန်တီးခြင်း။"""

    payload = {
        "name": name or "",
        "business_name": business_name or "",
        "business_type": business_type or "",
        "email": email or "",
        "address": address or "",
        "fiscal_year_end": fiscal_year_end or "09-30",
    }

    response = (
        get_supabase()
        .table(CLIENT_TABLE)
        .insert(payload)
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Supabase did not return the newly created client."
        )

    return int(response.data[0]["id"])


# ============================================================
# CLIENTS — UPDATE
# ============================================================

def update_client(client_id, **fields):
    """ခွင့်ပြုထားသော Client fields များကိုသာ Update လုပ်ခြင်း။"""

    allowed = {
        "name",
        "business_name",
        "business_type",
        "email",
        "address",
        "fiscal_year_end",
    }

    payload = {
        key: value
        for key, value in fields.items()
        if key in allowed
    }

    if not payload:
        raise ValueError("No valid client fields supplied.")

    response = (
        get_supabase()
        .table(CLIENT_TABLE)
        .update(payload)
        .eq("id", client_id)
        .execute()
    )

    if not response.data:
        raise RuntimeError("Client was not updated.")

    return response.data[0]


# ============================================================
# CLIENTS — DELETE
# ============================================================

def delete_client(client_id):
    """Client တစ်ဦးကို ဖျက်ခြင်း။

    Related statements များပါ ဖျက်မဖျက်သည်
    Database Foreign Key Cascade Setting ပေါ်တွင် မူတည်သည်။
    """

    response = (
        get_supabase()
        .table(CLIENT_TABLE)
        .delete()
        .eq("id", client_id)
        .execute()
    )

    return response.data


# ============================================================
# STATEMENT READ — ONE PERIOD
# ============================================================

def get_statement(client_id, statement_type, period_end=None):
    """
    period_end ပေးထားလျှင် ထိုကာလတစ်ခုတည်း၏ Statement ကို ရယူမည်။

    period_end မပေးထားလျှင် နောက်ဆုံးသိမ်းထားသောကာလကို ရယူမည်။
    """

    query = _statement_query(client_id, statement_type)

    period = _normalise_period(period_end)

    if period is not None:
        query = query.eq("period_end", period)

    response = (
        query
        .order("period_end", desc=True)
        .order("id", desc=True)
        .limit(1)
        .execute()
    )

    return response.data[0] if response.data else None


# ============================================================
# STATEMENT READ — HISTORY
# ============================================================

def get_statement_history(client_id, statement_type):
    """Client နှင့် Statement Type တူသော History အားလုံးကို ရယူခြင်း။"""

    response = (
        _statement_query(client_id, statement_type)
        .order("period_end", desc=True)
        .order("id", desc=True)
        .execute()
    )

    return response.data or []


# ============================================================
# STATEMENT READ — YEARS
# ============================================================

def get_statement_years(client_id: int) -> list:
    """Statement များရှိနေသော Calendar Year များကို ရယူခြင်း။"""

    conn = get_supabase()
    years = set()

    for table in sorted(STATEMENT_TABLES):
        response = (
            conn.table(table)
            .select("period_end")
            .eq("client_id", client_id)
            .execute()
        )

        for row in response.data or []:
            period = row.get("period_end")

            if period:
                try:
                    years.add(int(str(period)[:4]))
                except (TypeError, ValueError):
                    continue

    return sorted(years, reverse=True)


# ============================================================
# STATEMENT YEAR SUMMARY
# ============================================================

def get_statement_year_summary(client_id: int, year: int) -> dict:
    """Client တစ်ဦး၏ ရွေးချယ်ထားသော Calendar Year အတွင်း
    Statement တစ်မျိုးစီရှိသော Row အရေအတွက်ကို ရေတွက်ခြင်း။
    """

    conn = get_supabase()

    year = int(year)
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"

    summary = {}

    for table in sorted(STATEMENT_TABLES):
        response = (
            conn.table(table)
            .select("id")
            .eq("client_id", client_id)
            .gte("period_end", start_date)
            .lte("period_end", end_date)
            .execute()
        )

        summary[table] = len(response.data or [])

    return summary


# ============================================================
# DELETE STATEMENTS FOR ONE YEAR
# ============================================================

def delete_statements_for_year(client_id: int, year: int) -> dict:
    """Client တစ်ဦး၏ ရွေးချယ်ထားသော Calendar Year အတွင်း
    Statement အားလုံးကို ဖျက်ခြင်း။

    သီးခြား Table များကို Request တစ်ခုစီဖြင့် ဖျက်သောကြောင့်
    လုပ်ဆောင်မှုအားလုံးသည် Atomic Transaction မဟုတ်ပါ။
    """

    conn = get_supabase()

    year = int(year)
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"

    # Delete မလုပ်မီ Table အားလုံးကို Query လုပ်၍ စစ်ဆေးခြင်း။
    for table in sorted(STATEMENT_TABLES):
        (
            conn.table(table)
            .select("id")
            .eq("client_id", client_id)
            .gte("period_end", start_date)
            .lte("period_end", end_date)
            .execute()
        )

    deleted = {}

    for table in sorted(STATEMENT_TABLES):
        response = (
            conn.table(table)
            .delete()
            .eq("client_id", client_id)
            .gte("period_end", start_date)
            .lte("period_end", end_date)
            .execute()
        )

        deleted[table] = len(response.data or [])

    return deleted


# ============================================================
# STATEMENT SAVE — INSERT OR UPDATE BY PERIOD
# ============================================================

def save_statement(
    client_id,
    statement_type,
    period_end=None,
    data_json=None,
    custom_data=None,
):
    """
    Client + Statement Type + Period အလိုက် သိမ်းဆည်းခြင်း။

    Period အသစ်ဖြစ်လျှင် Record အသစ်ဖန်တီးမည်။
    Period တူပြီးသားဖြစ်လျှင် ထို Record ကို Update လုပ်မည်။
    """

    _validate_statement_type(statement_type)

    period = _normalise_period(period_end)

    if period is None:
        raise ValueError("A statement period is required.")

    # Statement Data စစ်ဆေးခြင်း။
    data = _decode_json(data_json, default={})

    if not isinstance(data, dict):
        raise ValueError(
            "Statement data must be a JSON object."
        )

    payload = {
        "client_id": client_id,
        "period_end": period,
        "data": data,
    }

    # Custom Data ပါဝင်သော Statement Types
    if statement_type in {
        "manufacturing",
        "trading_pl",
        "balance_sheet",
    }:
        custom = _decode_json(custom_data, default={})

        if not isinstance(custom, dict):
            raise ValueError(
                "Custom data must be a JSON object."
            )

        payload["custom_data"] = custom

    # Client + Period တူသော Record ရှိ/မရှိ စစ်ဆေးခြင်း။
    existing = (
        get_supabase()
        .table(statement_type)
        .select("id")
        .eq("client_id", client_id)
        .eq("period_end", period)
        .order("id", desc=True)
        .limit(1)
        .execute()
    )

    if existing.data:
        # ရှိပြီးသား Period ကိုသာ Update လုပ်မည်။
        statement_id = existing.data[0]["id"]

        response = (
            get_supabase()
            .table(statement_type)
            .update(payload)
            .eq("id", statement_id)
            .eq("client_id", client_id)
            .execute()
        )

    else:
        # Period အသစ်ဖြစ်လျှင် Record အသစ် Insert လုပ်မည်။
        response = (
            get_supabase()
            .table(statement_type)
            .insert(payload)
            .execute()
        )

    if not response.data:
        raise RuntimeError(
            "Statement save failed. Check the table schema, "
            "permissions, and row-level security policies."
        )

    return response.data[0]


# ============================================================
# DELETE ONE STATEMENT
# ============================================================

def delete_statement(client_id, statement_type, statement_id):
    """Client တစ်ဦး၏ Statement Record တစ်ခုတည်းကို ဖျက်ခြင်း။"""

    _validate_statement_type(statement_type)

    response = (
        get_supabase()
        .table(statement_type)
        .delete()
        .eq("id", statement_id)
        .eq("client_id", client_id)
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "No matching statement was deleted."
        )

    return response.data[0]


# ============================================================
# BACKUP — READ ALL DATA
# ============================================================

def get_all_data_for_backup():
    """Application Table အားလုံး၏ Data ကို Backup အတွက် ရယူခြင်း။"""

    backup = {
        "backup_format_version": 1,
        "created_at": datetime.now().isoformat(),
        "tables": {},
    }

    conn = get_supabase()

    for table_name in BACKUP_TABLES:
        response = (
            conn.table(table_name)
            .select("*")
            .execute()
        )

        backup["tables"][table_name] = response.data or []

    return backup


# ============================================================
# BACKUP — SAVE LOCAL JSON FILE
# ============================================================

def auto_backup_to_file():
    """Local JSON Backup ဖန်တီးပြီး နောက်ဆုံး Backup ၅ ခုကိုသာ ထားခြင်း။

    Streamlit Cloud တွင် Local File များသည် Restart သို့မဟုတ်
    Redeploy ပြုလုပ်သည့်အခါ မတည်မြဲနိုင်ပါ။
    """

    try:
        backup_dir = Path("backups")
        backup_dir.mkdir(parents=True, exist_ok=True)

        backup_data = get_all_data_for_backup()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        file_path = (
            backup_dir
            / f"accounting_backup_{timestamp}.json"
        )

        file_path.write_text(
            json.dumps(
                backup_data,
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

        backup_files = sorted(
            backup_dir.glob("accounting_backup_*.json"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )

        for old_file in backup_files[5:]:
            old_file.unlink()

        return True

    except Exception as exc:
        print(f"Backup error: {exc}")
        return False


# ============================================================
# RESTORE — FROM BACKUP
# ============================================================

def restore_from_backup(backup_data):
    """Backup Data ကို ID အလိုက် ပြန်လည်ထည့်သွင်းခြင်း။

    ID တူသော Row ရှိလျှင် Update လုပ်မည်။
    ID မရှိသေးလျှင် Insert လုပ်မည်။

    Backup ထဲတွင် မပါသော Database Row များကို မဖျက်ပါ။
    Restore သည် Atomic Transaction မဟုတ်ပါ။
    """

    if not isinstance(backup_data, dict):
        raise ValueError("Backup must be a JSON object.")

    tables = backup_data.get("tables", backup_data)

    if not isinstance(tables, dict):
        raise ValueError(
            "Backup table collection is invalid."
        )

    results = {}

    conn = get_supabase()

    # Client များကို အရင် Restore လုပ်မည်။
    # ထို့နောက် Client ID ကို ကိုးကားထားသော Statement များကို Restore လုပ်မည်။
    for table_name in BACKUP_TABLES:

        if table_name not in tables:
            continue

        rows = tables[table_name]

        if not isinstance(rows, list):
            raise ValueError(
                f"Backup table {table_name!r} must contain a list."
            )

        if not rows:
            results[table_name] = 0
            continue

        if not all(isinstance(row, dict) for row in rows):
            raise ValueError(
                f"Backup table {table_name!r} contains invalid rows."
            )

        if not all(row.get("id") is not None for row in rows):
            raise ValueError(
                f"Every row in {table_name!r} must contain its original ID."
            )

        response = (
            conn.table(table_name)
            .upsert(
                rows,
                on_conflict="id",
            )
            .execute()
        )

        results[table_name] = len(response.data or [])

    return results