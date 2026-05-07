import re
import sqlite3
from pathlib import Path

from src.config import DATABASE_PATH

ALLOWED_TABLES = {"monthly_costs", "incidents", "sla_targets", "daily_metrics"}


def query_database(sql: str) -> dict:
    """Execute a read-only SQL query against geekbrain.db.

    Returns dict with 'columns' and 'rows' keys, or 'error' on failure.
    """
    sql_upper = sql.strip().upper()
    if not sql_upper.startswith("SELECT"):
        return {"error": "Only SELECT queries are allowed."}

    if "--" in sql or "/*" in sql:
        return {"error": "SQL comments not allowed."}

    if ";" in sql.strip().rstrip(";"):
        return {"error": "Multiple statements not allowed."}

    dangerous_keywords = {"DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE", "EXEC"}
    if any(kw in sql_upper for kw in dangerous_keywords):
        return {"error": "Query contains disallowed keywords."}

    tables_in_query = set(re.findall(r"\bFROM\s+(\w+)", sql_upper))
    tables_in_query.update(re.findall(r"\bJOIN\s+(\w+)", sql_upper))
    invalid_tables = tables_in_query - {t.upper() for t in ALLOWED_TABLES}
    if invalid_tables:
        return {"error": f"Access to tables {invalid_tables} not allowed."}

    db_path = Path(DATABASE_PATH)
    if not db_path.exists():
        return {"error": f"Database not found at {DATABASE_PATH}"}

    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        conn.close()

        return {
            "columns": columns,
            "rows": [dict(row) for row in rows],
            "row_count": len(rows),
        }
    except sqlite3.Error as e:
        return {"error": f"SQL error: {e}"}


def get_schema_info() -> str:
    """Return schema information for the LLM to generate queries."""
    return """Available tables:
- monthly_costs (service, month, compute_cost, storage_cost, network_cost, third_party_cost, total_cost)
  Example: SELECT service, SUM(total_cost) FROM monthly_costs WHERE month IN ('2026-01','2026-02','2026-03') GROUP BY service
- incidents (incident_id, service, date, severity, duration_minutes, root_cause, resolution, team_responsible, reported_by)
  Example: SELECT * FROM incidents WHERE service = 'PaymentGW'
- sla_targets (service, metric, target, measurement_window)
  Example: SELECT * FROM sla_targets WHERE service = 'NotificationSvc'
- daily_metrics (date, service, latency_p99_ms, error_rate_percent, requests_per_minute, availability_percent)
  Example: SELECT AVG(latency_p99_ms) FROM daily_metrics WHERE service = 'AuthSvc' AND date >= '2026-03-01'

Services: PaymentGW, OrderSvc, AuthSvc, NotificationSvc, ReportingSvc, FraudDetector
Months format: YYYY-MM (e.g., '2026-01')
Dates format: YYYY-MM-DD"""
