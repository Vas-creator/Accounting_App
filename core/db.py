"""Database helpers for the Accounting App.

Statement identity: (client_id, statement_type, period_end).
Same period updates that period; a different period creates a new history row.
Backup restore is non-destructive and never clears existing tables.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

import streamlit as st
from st_supabase_connection import SupabaseConnection

CLIENT_TABLE = "clients"
STATEMENT_TABLES = {"manufacturing", "trading_pl", "balance_sheet", "cash_flow"}
BACKUP_TABLES = [CLIENT_TABLE, "manufacturing", "trading_pl", "balance_sheet", "cash_flow"]


def get_supabase():
    """Connect directly to Supabase using Streamlit secrets."""
    from supabase import create_client

    try:
        url = st.secrets["connections"]["supabase"]["url"]
        key = st.secrets["connections"]["supabase"]["key"]
    except Exception:
        try:
            url = st.secrets["SUPABASE_URL"]
            key = st.secrets["SUPABASE_KEY"]
        except Exception as exc:
            raise RuntimeError(
                "Supabase URL or key is missing from Streamlit secrets."
            ) from exc

    if not url or not key:
        raise RuntimeError("Supabase URL or key is empty.")

    return create_client(url, key)


def init_db() -> None:
    """The schema is managed in Supabase; no tables are created here."""
    return None


def _validate_statement_table(statement_type: str) -> str:
    if statement_type not in STATEMENT_TABLES:
        raise ValueError(f"Unsupported statement type: {statement_type!r}")
    return statement_type


def _decode_json(value: Any, default: Any):
    if value is None or value == "":
        return default
    return json.loads(value) if isinstance(value, str) else value


def _period_string(period_end: Any = None, as_at_date: Any = None) -> str:
    value = period_end or as_at_date
    return str(value).strip() if value is not None else ""


# ---------------------------- Dashboard ----------------------------
def get_dashboard_stats() -> dict:
    try:
        conn = get_supabase()
        clients_res = conn.table(CLIENT_TABLE).select("id", count="exact").execute()
        total_clients = int(clients_res.count or 0)
        total_statements = 0
        for table in sorted(STATEMENT_TABLES):
            try:
                res = conn.table(table).select("id", count="exact").execute()
                total_statements += int(res.count or 0)
            except Exception as exc:
                print(f"Statement count error for {table}: {exc}")
        latest_update = "—"
        try:
            res = (conn.table(CLIENT_TABLE).select("created_at")
                   .order("created_at", desc=True).limit(1).execute())
            if res.data:
                latest = res.data[0].get("created_at")
                latest_update = str(latest)[:10] if latest else "—"
        except Exception as exc:
            print(f"Latest update lookup error: {exc}")
        return {"total_clients": total_clients,
                "total_statements": total_statements,
                "latest_update": latest_update}
    except Exception as exc:
        print(f"Dashboard stats error: {exc}")
        return {"total_clients": 0, "total_statements": 0, "latest_update": "—"}


def get_recent_clients(limit: int = 5) -> list:
    try:
        conn = get_supabase()
        res = (conn.table(CLIENT_TABLE).select("*")
               .order("created_at", desc=True).limit(max(1, int(limit))).execute())
        return res.data or []
    except Exception as exc:
        print(f"Recent clients error: {exc}")
        return []


# ---------------------------- Client CRUD ----------------------------
def create_client(name: str, business_name: str = "", business_type: str = "",
                  email: str = "", address: str = "", fiscal_year_end: str = "09-30",
                  **kwargs) -> int:
    if not str(name).strip():
        raise ValueError("Client name is required.")
    payload = {
        "name": str(name).strip(), "business_name": business_name or "",
        "business_type": business_type or "", "email": email or "",
        "address": address or "", "fiscal_year_end": fiscal_year_end or "09-30",
    }
    res = get_supabase().table(CLIENT_TABLE).insert(payload).execute()
    if not res.data:
        raise RuntimeError("Supabase did not return the newly created client.")
    return int(res.data[0]["id"])


def get_all_clients():
    try:
        conn = get_supabase()

        res = (
            conn.table(CLIENT_TABLE)
            .select("*")
            .order("name")
            .execute()
        )

        rows = res.data or []

        st.info(f"DEBUG: Supabase returned {len(rows)} client rows")

        return rows

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


def update_client(client_id: int, **kwargs) -> bool:
    allowed = {"name", "business_name", "business_type", "email", "address", "fiscal_year_end", "phone"}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return False
    try:
        res = get_supabase().table(CLIENT_TABLE).update(fields).eq("id", client_id).execute()
        return bool(res.data)
    except Exception as exc:
        print(f"Update client error: {exc}")
        return False


def delete_client(client_id: int) -> bool:
    try:
        res = get_supabase().table(CLIENT_TABLE).delete().eq("id", client_id).execute()
        return bool(res.data)
    except Exception as exc:
        print(f"Delete client error: {exc}")
        return False


def count_clients() -> int:
    try:
        res = get_supabase().table(CLIENT_TABLE).select("id", count="exact").execute()
        return int(res.count or 0)
    except Exception as exc:
        print(f"Count clients error: {exc}")
        return 0


# ------------------------- Statements / History -------------------------
def get_statement(client_id: int, statement_type: str, period_end: str = None):
    """Fetch an exact period, or the latest period if period_end is omitted."""
    table = _validate_statement_table(statement_type)
    try:
        query = get_supabase().table(table).select("*").eq("client_id", client_id)
        if period_end:
            query = query.eq("period_end", str(period_end).strip()).order("id", desc=True)
        else:
            query = query.order("period_end", desc=True).order("id", desc=True)
        res = query.limit(1).execute()
        return res.data[0] if res.data else None
    except Exception as exc:
        print(f"Get statement error ({table}, client {client_id}): {exc}")
        return None


def get_statement_history(client_id: int, statement_type: str) -> list:
    """Return all periods for a client, newest period first."""
    table = _validate_statement_table(statement_type)
    try:
        res = (get_supabase().table(table).select("*").eq("client_id", client_id)
               .order("period_end", desc=True).order("id", desc=True).execute())
        return res.data or []
    except Exception as exc:
        print(f"History error for {table}, client {client_id}: {exc}")
        return []


def save_statement(client_id: int, statement_type: str, period_end: str = "",
                   data_json: Any = "", as_at_date: str = "", custom_data: Any = None,
                   **kwargs) -> int:
    """Save by exact period: update matching period, otherwise insert a new row.

    A database lookup error is allowed to raise; it must not be mistaken for
    'no existing row', because that could create accidental duplicate history.
    """
    table = _validate_statement_table(statement_type)
    period = _period_string(period_end, as_at_date)
    if not period:
        raise ValueError("Statement period date is required.")

    data = _decode_json(data_json, {})
    if data is None:
        data = {}
    if not isinstance(data, (dict, list)):
        raise ValueError("Statement data must be a JSON object or list.")

    conn = get_supabase()
    lookup = (conn.table(table).select("id").eq("client_id", client_id)
              .eq("period_end", period).order("id", desc=True).limit(1).execute())
    existing = lookup.data or []

    payload = {"period_end": period, "data": data}
    if table in {"trading_pl", "manufacturing"}:
        # Do not erase custom_data on an update when the caller omits it.
        if custom_data is not None:
            payload["custom_data"] = custom_data
        elif not existing:
            payload["custom_data"] = []

    if existing:
        row_id = existing[0]["id"]
        result = conn.table(table).update(payload).eq("id", row_id).execute()
        if not result.data:
            raise RuntimeError(f"Update returned no row for {table}, client {client_id}, period {period}.")
        return int(row_id)

    payload["client_id"] = client_id
    result = conn.table(table).insert(payload).execute()
    if not result.data:
        raise RuntimeError(f"Insert returned no row for {table}, client {client_id}, period {period}.")
    return int(result.data[0]["id"])


# ---------------------------- Backup / Restore ----------------------------
def get_all_data_for_backup() -> dict:
    conn = get_supabase()
    backup = {}
    for table in BACKUP_TABLES:
        try:
            res = conn.table(table).select("*").execute()
            backup[table] = res.data or []
        except Exception as exc:
            print(f"Backup read error for {table}: {exc}")
            raise
    return backup


def restore_from_backup(backup_data: dict) -> bool:
    """Insert backup records without deleting any existing data.

    This is deliberately non-destructive. Restoring rows with IDs into a
    non-empty database may fail on duplicate keys; perform replacement only
    through a separately planned and verified migration.
    """
    if not isinstance(backup_data, dict):
        raise ValueError("Backup data must be a dictionary.")
    conn = get_supabase()
    try:
        for table in BACKUP_TABLES:
            records = backup_data.get(table, [])
            if not records:
                continue
            if not isinstance(records, list):
                raise ValueError(f"Backup table {table!r} must contain a list.")
            conn.table(table).insert(records).execute()
        return True
    except Exception as exc:
        print(f"Restore error: {exc}")
        return False


def auto_backup_to_file() -> bool:
    """Write a timestamped JSON backup locally (cloud storage may be ephemeral)."""
    try:
        backup_data = get_all_data_for_backup()
        backup_dir = "backups"
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(backup_dir, f"auto_backup_{timestamp}.json")
        with open(path, "w", encoding="utf-8") as file:
            json.dump(backup_data, file, ensure_ascii=False, indent=2)
        files = sorted(os.path.join(backup_dir, name) for name in os.listdir(backup_dir)
                       if name.endswith(".json"))
        for old_path in files[:-5]:
            os.remove(old_path)
        return True
    except Exception as exc:
        print(f"Auto backup error: {exc}")
        return False
