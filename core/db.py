
# core/db.py

import os
import time
import streamlit as st
from st_supabase_connection import SupabaseConnection
from supabase import create_client
from supabase import create_client as supabase_create_client
import json
from datetime import datetime, date

CLIENT_TABLE = "clients"
STATEMENT_TABLES = {"manufacturing", "trading_pl", "balance_sheet", "cash_flow"}
BACKUP_TABLES = [CLIENT_TABLE, "manufacturing", "trading_pl", "balance_sheet", "cash_flow"]


def get_supabase():
    """Connect to Supabase using Streamlit secrets or environment variables."""

    url = None
    key = None

    # Option 1: Streamlit Secrets under [connections.supabase]
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

    # Option 3: Environment variables
    url = url or os.getenv("SUPABASE_URL")
    key = key or os.getenv("SUPABASE_KEY")

    if not url or not key:
        try:
            top_level_keys = list(st.secrets.keys())
            print("Secrets top-level keys:", top_level_keys)

            if "connections" in st.secrets:
                connections = st.secrets["connections"]
                print("Connection names:", list(connections.keys()))

                if "supabase" in connections:
                    supabase_config = connections["supabase"]
                    print("Supabase config keys:", list(supabase_config.keys()))
            else:
                print("No 'connections' section found in st.secrets")

        except Exception as e:
            print("Secrets diagnostic error:", type(e).__name__, str(e))

        raise RuntimeError(
            f"Supabase configuration missing: "
            f"url_found={bool(url)}, key_found={bool(key)}"
        )
    

    start = time.time()
    client = supabase_create_client(url, key)

    return client

def init_db():
    # Supabase schema is managed outside this application.
    return None


def get_dashboard_stats() -> dict:
    """Dashboard အတွက် client နှင့် statement အရေအတွက်များ ရယူခြင်း။"""
    default_stats = {
        "total_clients": 0,
        "total_statements": 0,
        "latest_update": "—",
    }

    try:
        conn = get_supabase()

        # 1. Total clients
        clients_res = (
            conn.table("clients")
            .select("id", count="exact")
            .execute()
        )
        total_clients = clients_res.count or 0

        # 2. Client တစ်ဦးချင်းစီမှာ statement type တစ်မျိုးစီ
        #    အနည်းဆုံးတစ်ခု ရှိ/မရှိ စစ်မယ်။
        total_statements = 0

        clients = (
            conn.table("clients")
            .select("id")
            .execute()
        ).data or []

        statement_tables = [
            "manufacturing",
            "trading_pl",
            "balance_sheet",
            "cash_flow",
        ]

        for client in clients:
            client_id = client["id"]

            for table in statement_tables:
                result = (
                    conn.table(table)
                    .select("id")
                    .eq("client_id", client_id)
                    .limit(1)
                    .execute()
                )

                if result.data:
                    total_statements += 1

        # 3. နောက်ဆုံးဖန်တီးထားသော client ရက်စွဲ
        latest_res = (
            conn.table("clients")
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

    except Exception as e:
        print(f"Dashboard stats error: {e}")
        return default_stats



# ============================================================
# INTERNAL HELPERS
# ============================================================

def _validate_statement_type(statement_type):
    if statement_type not in STATEMENT_TABLES:
        raise ValueError(
            f"Unsupported statement type: {statement_type}"
        )


def _normalise_period(value):
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
    if value is None:
        return default

    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError("Invalid JSON data.") from exc

    return value


def _statement_query(client_id, statement_type):
    _validate_statement_type(statement_type)

    return (
        get_supabase()
        .table(statement_type)
        .select("*")
        .eq("client_id", client_id)
    )


# ============================================================
# CLIENTS
# ============================================================

# def get_all_clients():
#     response = (
#         get_supabase()
#         .table("clients")
#         .select("*")
#         .order("updated_at", desc=True)
#         .execute()
#     )
#     return response.data or []



def get_all_clients():

    supabase = get_supabase()

    response = (
        supabase
        .table("clients")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )

    return response.data or []




def get_client(client_id):
    response = (
        get_supabase()
        .table("clients")
        .select("*")
        .eq("id", client_id)
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None


def create_client(
    name="",
    business_name="",
    business_type="",
    email="",
    address="",
    fiscal_year_end="09-30",
):
    payload = {
        "name": name or "",
        "business_name": business_name or "",
        "business_type": business_type or "",
        "email": email or "",
        "address": address or "",
        "fiscal_year_end": fiscal_year_end or "09-30",
    }
    res = get_supabase().table(CLIENT_TABLE).insert(payload).execute()
    if not res.data:
        raise RuntimeError("Supabase did not return the newly created client.")
    return int(res.data[0]["id"])


def get_all_clients() -> list:
    try:
        res = get_supabase().table(CLIENT_TABLE).select("*").order("name").execute()
        return res.data or []
    except Exception as exc:
        st.error("Supabase query failed")
        st.code(f"{type(exc).__name__}: {exc}")
        return []


def get_client(client_id: int):
    try:
        res = get_supabase().table(CLIENT_TABLE).select("*").eq("id", client_id).limit(1).execute()
        return res.data[0] if res.data else None
    except Exception as exc:
        print(f"Get client error: {exc}")
        return None


def update_client(client_id, **fields):
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
        .table("clients")
        .update(payload)
        .eq("id", client_id)
        .execute()
    )

    if not response.data:
        raise RuntimeError("Client was not updated.")

    return response.data[0]


def delete_client(client_id):
    """
    Delete the client row.

    Whether related statements are deleted depends on the database's
    foreign-key configuration. Verify cascade behaviour before use.
    """
    response = (
        get_supabase()
        .table("clients")
        .delete()
        .eq("id", client_id)
        .execute()
    )
    return response.data


# ============================================================
# STATEMENT READ
# ============================================================

def get_statement(client_id, statement_type, period_end=None):
    """
    With a period: read the newest matching row for that exact period.
    Without a period: read the latest saved period.
    """

    query = _statement_query(client_id, statement_type)
    period = _normalise_period(period_end)

    if period:
        query = query.eq("period_end", period)

    response = (
        query
        .order("period_end", desc=True)
        .order("id", desc=True)
        .limit(1)
        .execute()
    )

    return response.data[0] if response.data else None


def get_statement_history(client_id, statement_type):
    response = (
        _statement_query(client_id, statement_type)
        .order("period_end", desc=True)
        .order("id", desc=True)
        .execute()
    )
    return response.data or []

def get_statement_years(client_id: int) -> list:
    """Return calendar years represented by any statement table for this client."""
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


def get_statement_year_summary(client_id: int, year: int) -> dict:
    """Count statement rows whose period_end falls in the selected calendar year."""
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


def delete_statements_for_year(client_id: int, year: int) -> dict:
    """Delete this client's statement rows whose period_end falls in a calendar year.

    This performs a preflight read, then deletes table by table. Supabase does not
    make these separate requests one atomic transaction; a later failure can mean
    some earlier tables have already been deleted.
    """
    conn = get_supabase()
    year = int(year)
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"

    # Preflight all tables before starting deletion, so query/schema errors are
    # discovered before any table is changed.
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
# STATEMENT SAVE
# ============================================================


def save_statement(
    client_id,
    statement_type,
    period_end=None,
    data_json=None,
    custom_data=None,
):
    """Insert a new period or update the existing client-period record."""

    _validate_statement_type(statement_type)

    period = _normalise_period(period_end)

    if period is None:
        raise ValueError("A statement period is required.")

    data = _decode_json(data_json, default={})

    if not isinstance(data, dict):
        raise ValueError("Statement data must be a JSON object.")

    payload = {
        "client_id": client_id,
        "period_end": period,
        "data": data,
    }

    if statement_type in {
        "manufacturing",
        "trading_pl",
        "balance_sheet",
    }:
        custom = _decode_json(custom_data, default={})

        if not isinstance(custom, dict):
            raise ValueError("Custom data must be a JSON object.")

        payload["custom_data"] = custom

    response = (
        get_supabase()
        .table(statement_type)
        .upsert(
            payload,
            on_conflict="client_id,period_end",
        )
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
    """
    Delete exactly one statement row belonging to the specified client.
    """

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

def get_statement_year_summary(client_id: int, year: int) -> dict:
    """Count all statement rows for one client and calendar year."""
    conn = get_supabase()
    start_date = f"{int(year)}-01-01"
    end_date = f"{int(year)}-12-31"

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


def delete_statements_for_year(client_id: int, year: int) -> dict:
    """Delete all statement rows for one client in one calendar year."""
    conn = get_supabase()
    start_date = f"{int(year)}-01-01"
    end_date = f"{int(year)}-12-31"

    # First verify all tables can be queried.
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

    # Delete only matching client and year.
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
# BACKUP
# ============================================================

def get_all_data_for_backup():
    """
    Return all application table rows as a JSON-serialisable dictionary.
    """

    backup = {
        "backup_format_version": 1,
        "created_at": datetime.now().isoformat(),
        "tables": {},
    }

    for table_name in BACKUP_TABLES:
        response = (
            get_supabase()
            .table(table_name)
            .select("*")
            .execute()
        )
        backup["tables"][table_name] = response.data or []

    return backup


def auto_backup_to_file():
    """
    Save a local JSON backup and retain up to five files.

    Note: local files on Streamlit Cloud may not persist across
    restarts or redeployments. Download backups to a separate device.
    """

    try:
        backup_dir = Path("backups")
        backup_dir.mkdir(parents=True, exist_ok=True)

        backup_data = get_all_data_for_backup()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = backup_dir / f"accounting_backup_{timestamp}.json"

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

    except Exception:
        return False


# ============================================================
# RESTORE
# ============================================================

def restore_from_backup(backup_data):
    """
    Non-destructive restore by ID.

    Existing rows with matching IDs are updated; rows with new IDs
    are inserted. This does not delete rows missing from the backup.

    Restore is not transactional: if a later table fails, earlier
    tables may already have been restored. Always back up the current
    database before restoring.
    """

    if not isinstance(backup_data, dict):
        raise ValueError("Backup must be a JSON object.")

    tables = backup_data.get("tables", backup_data)

    if not isinstance(tables, dict):
        raise ValueError("Backup table collection is invalid.")

    results = {}

    # Clients first, so referenced client IDs can exist before statements.
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

        # Avoid writing unknown table names or arbitrary table payloads.
        if table_name not in BACKUP_TABLES:
            continue

        # Rows should retain their original IDs to merge safely.
        if not all(row.get("id") is not None for row in rows):
            raise ValueError(
                f"Every row in {table_name!r} must contain its original ID."
            )

        response = (
            get_supabase()
            .table(table_name)
            .upsert(rows, on_conflict="id")
            .execute()
        )

        results[table_name] = len(response.data or [])

    return results
