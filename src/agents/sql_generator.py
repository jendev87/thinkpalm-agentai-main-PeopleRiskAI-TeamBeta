"""
Natural-language → SQLite SELECT generation with safety checks.
"""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

# Live schema matches explainability / UI (Driver1/2/3, not TopDriver*).
DB_SCHEMA = """
SQLite tables (read-only):

employees (
  EmployeeID TEXT PRIMARY KEY,   -- e.g. EMP0001
  Tenure INTEGER,                -- years at company
  Department TEXT,               -- Engineering, HR, Operations, Finance, Sales, Marketing
  Role TEXT,                     -- job title
  MonthlyHours INTEGER,
  LastPromotion INTEGER,         -- years since last promotion
  Salary REAL,
  Attrition INTEGER              -- historical label 0/1 (not the prediction)
)

attrition_scores (
  EmployeeID TEXT PRIMARY KEY,
  RiskPercentage REAL,           -- predicted flight risk 0–100
  Driver1 TEXT,                  -- top SHAP risk driver
  Driver2 TEXT,
  Driver3 TEXT
)

Join key: employees.EmployeeID = attrition_scores.EmployeeID
Prefer aliases: e for employees, a for attrition_scores.
RiskPercentage > 75 is considered high risk.
"""

DEFAULT_FALLBACK_SQL = (
    "SELECT e.EmployeeID, e.Department, e.Role, a.RiskPercentage, "
    "a.Driver1, a.Driver2, a.Driver3 "
    "FROM employees e "
    "JOIN attrition_scores a ON e.EmployeeID = a.EmployeeID "
    "ORDER BY a.RiskPercentage DESC "
    "LIMIT 5"
)

MAX_ROWS = 50
ALLOWED_TABLES = {"employees", "attrition_scores"}
FORBIDDEN_SQL = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|ATTACH|DETACH|"
    r"PRAGMA|VACUUM|REINDEX|GRANT|REVOKE|TRUNCATE|INTO|EXEC|EXECUTE|"
    r"UNION\s+ALL)\b",
    re.IGNORECASE,
)


class GeneratedSQL(BaseModel):
    """Structured LLM output for a data query."""

    sql: str = Field(description="A single SQLite SELECT (or WITH ... SELECT) query only.")
    rationale: str = Field(
        default="",
        description="One short sentence explaining how this query answers the question.",
    )


def default_db_path() -> Path:
    return Path(__file__).parent.parent.parent / "hr_data.db"


def _strip_sql_fences(sql: str) -> str:
    text = (sql or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:sql)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    return text.strip().rstrip(";").strip()


def validate_sql(sql: str) -> tuple[bool, str, str]:
    """
    Returns (ok, cleaned_sql_or_empty, error_message).
    Only read-only SELECT / CTE queries against known tables are allowed.
    """
    cleaned = _strip_sql_fences(sql)
    if not cleaned:
        return False, "", "Empty SQL."

    # Reject multiple statements
    if ";" in cleaned:
        return False, "", "Multiple SQL statements are not allowed."

    if FORBIDDEN_SQL.search(cleaned):
        return False, "", "Only read-only SELECT queries are allowed."

    normalized = cleaned.lstrip().upper()
    if not (normalized.startswith("SELECT") or normalized.startswith("WITH")):
        return False, "", "Query must start with SELECT or WITH."

    # Table whitelist: FROM/JOIN targets must be known tables or CTE names
    referenced = {
        m.group(1).lower()
        for m in re.finditer(
            r"\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)",
            cleaned,
            flags=re.IGNORECASE,
        )
    }
    cte_names = {
        m.group(1).lower()
        for m in re.finditer(
            r"(?:WITH|,)\s*([a-zA-Z_][a-zA-Z0-9_]*)\s+AS\s*\(",
            cleaned,
            flags=re.IGNORECASE,
        )
    }

    unknown = referenced - ALLOWED_TABLES - cte_names
    if unknown:
        return False, "", f"Unknown or disallowed table(s): {', '.join(sorted(unknown))}."

    # Cap result size
    limit_match = re.search(r"\bLIMIT\s+(\d+)\b", cleaned, flags=re.IGNORECASE)
    if limit_match:
        limit_val = int(limit_match.group(1))
        if limit_val > MAX_ROWS:
            cleaned = re.sub(
                r"\bLIMIT\s+\d+\b",
                f"LIMIT {MAX_ROWS}",
                cleaned,
                count=1,
                flags=re.IGNORECASE,
            )
    else:
        cleaned = f"{cleaned} LIMIT {MAX_ROWS}"

    return True, cleaned, ""


def _sample_dimensions(db_path: Path) -> str:
    """Inject live department/role values so the LLM filters accurately."""
    try:
        with sqlite3.connect(db_path) as conn:
            depts = [r[0] for r in conn.execute(
                "SELECT DISTINCT Department FROM employees ORDER BY 1"
            ).fetchall()]
            roles = [r[0] for r in conn.execute(
                "SELECT DISTINCT Role FROM employees ORDER BY 1 LIMIT 40"
            ).fetchall()]
        return (
            f"Known Departments: {', '.join(depts) or '(none)'}\n"
            f"Sample Roles: {', '.join(roles) or '(none)'}"
        )
    except Exception:
        return "Known Departments/Roles unavailable."


def generate_sql(llm: Any, user_question: str, db_path: Optional[Path] = None) -> GeneratedSQL:
    """Ask the LLM to produce a SQLite SELECT for the HR question."""
    path = Path(db_path) if db_path else default_db_path()
    dims = _sample_dimensions(path)

    system = SystemMessage(
        content=(
            "You are a SQLite expert for an HR attrition database. "
            "Write ONE read-only SELECT (or WITH ... SELECT) that answers the user. "
            "Rules:\n"
            "- Use only the tables/columns in the schema.\n"
            "- Prefer JOIN employees e and attrition_scores a when risk columns are needed.\n"
            "- Never invent columns. Driver columns are Driver1/Driver2/Driver3 (not TopDriver*).\n"
            "- Match Department/Role values case-sensitively to the known lists when filtering.\n"
            "- Always include LIMIT (max 50). For 'top N' use ORDER BY RiskPercentage DESC.\n"
            "- For counts/aggregates, SELECT the aggregate columns clearly.\n"
            "- Do not use INSERT/UPDATE/DELETE/DROP/PRAGMA or multiple statements.\n\n"
            f"{DB_SCHEMA}\n{dims}"
        )
    )
    human = HumanMessage(content=user_question)

    structured = llm.with_structured_output(GeneratedSQL)
    result = structured.invoke([system, human])
    if isinstance(result, GeneratedSQL):
        return result
    # Some providers return dict-like objects
    return GeneratedSQL(
        sql=getattr(result, "sql", None) or result.get("sql", ""),
        rationale=getattr(result, "rationale", None) or result.get("rationale", ""),
    )


def run_sql(sql: str, db_path: Optional[Path] = None) -> pd.DataFrame:
    path = Path(db_path) if db_path else default_db_path()
    with sqlite3.connect(path) as conn:
        return pd.read_sql_query(sql, conn)


def nl_to_dataframe(
    llm: Any,
    user_question: str,
    db_path: Optional[Path] = None,
) -> tuple[pd.DataFrame, str, str]:
    """
    Full pipeline: NL → SQL → validate → execute.
    Returns (dataframe, sql_used, note). note explains fallbacks/errors.
    """
    path = Path(db_path) if db_path else default_db_path()
    note = ""
    sql = DEFAULT_FALLBACK_SQL

    try:
        generated = generate_sql(llm, user_question, db_path=path)
        ok, cleaned, err = validate_sql(generated.sql)
        if ok:
            sql = cleaned
            if generated.rationale:
                note = generated.rationale
        else:
            note = f"Generated SQL rejected ({err}); using default top-risk query."
            sql = DEFAULT_FALLBACK_SQL
    except Exception as e:
        note = f"SQL generation failed ({e}); using default top-risk query."
        sql = DEFAULT_FALLBACK_SQL

    try:
        df = run_sql(sql, db_path=path)
    except Exception as e:
        note = f"Query execution failed ({e}); using default top-risk query."
        sql = DEFAULT_FALLBACK_SQL
        df = run_sql(sql, db_path=path)

    return df, sql, note
