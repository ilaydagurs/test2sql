from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, Tuple

import requests



def _parse_json_loose(content: str) -> dict:
    """
    Robustly parse JSON returned by the model.
    Handles:
      - pure JSON
      - JSON wrapped in extra whitespace/newlines
      - JSON with leading/trailing text
    """
    if isinstance(content, dict):
        return content

    text = str(content).strip()

    # First: direct parse (most common)
    try:
        return json.loads(text)
    except Exception:
        pass

    # Second: extract first JSON object by scanning braces
    start = text.find("{")
    if start == -1:
        raise ValueError(f"No JSON object found. Raw: {text[:500]}")

    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    blob = text[start : i + 1]
                    return json.loads(blob)

    raise ValueError(f"Unterminated JSON object. Raw: {text[:500]}")



# Repo paths
REPO_ROOT = Path(__file__).resolve().parents[1]
ALLOWLIST_PATH = REPO_ROOT / "data" / "metadata" / "allowlist.json"

ALLOWED_VIEW = "bank.v_transactions_enriched"


def _load_allowlist() -> Dict[str, Any]:
    return json.loads(ALLOWLIST_PATH.read_text(encoding="utf-8"))


def _allowed_columns() -> list[str]:
    allow = _load_allowlist()
    return allow["tables"][ALLOWED_VIEW]


_TABLE_REF_RE = re.compile(r"\b(from|join)\s+([a-zA-Z_][\w.]*)(?:\s+[a-zA-Z_]\w*)?\b", re.IGNORECASE)


def _validate_sql(sql: str) -> Tuple[bool, str]:
    s = (sql or "").strip().rstrip(";")
    if not s:
        return False, "Empty SQL"

    # Must be read-only (defense in depth; ui.validators.enforce_readonly will also check)
    if not re.match(r"^(select|with)\b", s, flags=re.IGNORECASE):
        return False, "Only SELECT/WITH allowed"

    # Block dangerous / out-of-scope keywords
    banned = ["information_schema", "pragma", "attach", "copy ", "install ", "load ", "create ", "drop ", "alter ", "update ", "delete ", "insert "]
    low = s.lower()
    if any(b in low for b in banned):
        return False, "Banned keyword detected"

    # Ensure only allowed view referenced in FROM/JOIN
    refs = [m.group(2) for m in _TABLE_REF_RE.finditer(s)]
    bad = [t for t in refs if t.lower() != ALLOWED_VIEW.lower()]
    if bad:
        return False, f"Disallowed table(s) referenced: {bad}. Allowed: {ALLOWED_VIEW}"

    return True, "OK"


def _build_messages(question: str, role: str) -> list[dict]:
    cols = _allowed_columns()
    cols_list = ", ".join(cols)

    system = f"""
You are a Text-to-SQL translator for DuckDB.

You MUST:
- Generate a single READ-ONLY SQL query (SELECT/WITH only).
- Query ONLY this view: {ALLOWED_VIEW}
- Use ONLY these columns (no other tables, no information_schema):
  {cols_list}
- Prefer explicit column lists (avoid SELECT *).
- Add ORDER BY TransactionDate DESC, TransactionID DESC when user asks for latest/son.
- Always include a LIMIT (default 10–50 based on question).

Return STRICT JSON that matches this schema:
{{
  "sql": "string",
  "answer": "string"
}}

Role context:
- bank_employee: avoid sensitive demographics unless explicitly asked (Age, Gender).
- manager/auditor: ok to include more fields, still minimal.
""".strip()

    user = f"Role={role}. Question (Turkish): {question}"

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def _openrouter_chat(messages: list[dict], model: str, debug: bool) -> Dict[str, Any]:
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Missing OPENROUTER_API_KEY env var")

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # Optional app attribution (recommended by OpenRouter docs)
    site = os.getenv("OPENROUTER_SITE_URL", "").strip()
    title = os.getenv("OPENROUTER_APP_NAME", "").strip()
    if site:
        headers["HTTP-Referer"] = site
    if title:
        headers["X-Title"] = title

    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 350,
        # Structured Outputs (if supported by the chosen model)
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "text2sql_result",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "sql": {"type": "string"},
                        "answer": {"type": "string"},
                    },
                    "required": ["sql", "answer"],
                    "additionalProperties": False,
                },
            },
        },
    }

    r = requests.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()

    content = data["choices"][0]["message"]["content"]
    obj = _parse_json_loose(content)
    return {"obj": obj, "raw": data}



def text2sql(question: str, role: str, debug: bool = False) -> Dict[str, Any]:
    model = os.getenv("OPENROUTER_MODEL", "openai/gpt-5.1-codex-max").strip()

    trace: Dict[str, Any] = {"debug": debug, "model": model}
    try:
        messages = _build_messages(question, role)
        out = _openrouter_chat(messages, model=model, debug=debug)

        obj = out["obj"]
        sql = (obj.get("sql") or "").strip()
        answer = (obj.get("answer") or "").strip()

        ok, msg = _validate_sql(sql)
        trace["sql_ok"] = ok
        trace["sql_check"] = msg

        if debug:
            # Keep trace lightweight
            trace["openrouter_id"] = out["raw"].get("id")
            trace["usage"] = out["raw"].get("usage")

        if not ok:
            safe_sql = f"""
SELECT TransactionID, TransactionDate, CustomerName, Amount, MerchantName, MerchantCategory, City
FROM {ALLOWED_VIEW}
ORDER BY TransactionDate DESC, TransactionID DESC
LIMIT 20
""".strip()
            return {
                "sql": safe_sql,
                "answer": f"AI sorgusu güvenlik kontrolünden geçmedi ({msg}). Güvenli bir sorgu çalıştırıyorum.",
                "trace": trace,
            }

        return {
            "sql": sql,
            "answer": answer or "Sorgu üretildi.",
            "trace": trace,
        }

    except Exception as e:
        trace["error"] = str(e)
        fallback = f"""
SELECT TransactionID, TransactionDate, CustomerName, Amount, MerchantName, MerchantCategory, City
FROM {ALLOWED_VIEW}
ORDER BY TransactionDate DESC, TransactionID DESC
LIMIT 20
""".strip()
        return {
            "sql": fallback,
            "answer": f"AI sorgu üretimi başarısız oldu: {e}. Geçici olarak örnek sorgu çalıştırıyorum.",
            "trace": trace,
        }
