import os
import sys
from pathlib import Path

# Ensure repo root is importable when running `streamlit run ui/app.py`
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(REPO_ROOT))

import streamlit as st

from ui.db import init_conn, run_sql, get_schema_overview
from ui.validators import enforce_readonly
from ui.graph_client import text2sql


st.set_page_config(page_title="Text2SQL", layout="wide")

# ----------------------------
# Session state init
# ----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "history" not in st.session_state:
    st.session_state.history = []
if "conn" not in st.session_state:
    default_db = REPO_ROOT / "data" / "duckdb" / "bank_txn_analytics.duckdb"
    db_path = os.getenv("DUCKDB_PATH", str(default_db))
    st.session_state.conn = init_conn(db_path)


# ----------------------------
# Sidebar controls
# ----------------------------
st.sidebar.title("Ayarlar")

role = st.sidebar.selectbox("Kullanıcı rolü", ["bank_employee", "manager", "auditor"])
debug = st.sidebar.toggle("Debug/trace göster", value=True)
auto_run = st.sidebar.toggle("SQL otomatik çalıştır", value=True)
default_limit = st.sidebar.number_input("Varsayılan LIMIT", min_value=10, max_value=5000, value=200, step=10)

# Show DB path
try:
    # duckdb connection doesn't expose path reliably; store via env/default logic again
    default_db = REPO_ROOT / "data" / "duckdb" / "bank_txn_analytics.duckdb"
    db_path = os.getenv("DUCKDB_PATH", str(default_db))
    st.sidebar.caption(f"DB: `{db_path}`")
except Exception:
    pass

st.sidebar.divider()

# Schema browser
st.sidebar.subheader("Şema (bank)")
with st.sidebar.expander("Tablolar / View'lar", expanded=False):
    try:
        schema_df = get_schema_overview(st.session_state.conn, schema_name="bank")
        if schema_df.empty:
            st.info("Şema bilgisi bulunamadı. DB doğru mu?")
        else:
            st.dataframe(schema_df, use_container_width=True, height=260)
    except Exception as e:
        st.warning(f"Şema okunamadı: {e}")

# Quick demo queries (optional but very useful in meetings)
st.sidebar.subheader("Hızlı sorgular")
quick_queries = {
    "Top 10 merchant (harcama)": """
        SELECT MerchantName, SUM(Amount) AS total_spend
        FROM bank.v_transactions_enriched
        GROUP BY MerchantName
        ORDER BY total_spend DESC
        LIMIT 10
    """,
    "Kategori bazlı harcama": """
        SELECT MerchantCategory, SUM(Amount) AS total_spend, COUNT(*) AS txn_count
        FROM bank.v_transactions_enriched
        GROUP BY MerchantCategory
        ORDER BY total_spend DESC
        LIMIT 50
    """,
    "Ödeme tipi dağılımı": """
        SELECT Mode, COUNT(*) AS txn_count, SUM(Amount) AS total_amount
        FROM bank.v_transactions_enriched
        GROUP BY Mode
        ORDER BY txn_count DESC
        LIMIT 50
    """,
}
selected_quick = st.sidebar.selectbox("Seç", ["(yok)"] + list(quick_queries.keys()))
run_quick = st.sidebar.button("Seçileni çalıştır", type="secondary", use_container_width=True)

st.title("Text2SQL Chat (MVP)")

left, right = st.columns([1, 1], gap="large")


# ----------------------------
# Left: chat
# ----------------------------
with left:
    st.subheader("Sohbet")

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.write(m["content"])

    question = st.chat_input("Sorunu yaz: örn. 'son 10 işlem?'")
    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.write(question)

        result = text2sql(question=question, role=role, debug=debug)
        sql = (result.get("sql") or "").strip()
        answer = (result.get("answer") or "").strip()
        trace = result.get("trace") or {}

        st.session_state.history.append(
            {"question": question, "sql": sql, "answer": answer, "trace": trace}
        )

        with st.chat_message("assistant"):
            st.write(answer if answer else "Sorgu üretildi.")
            st.code(sql, language="sql")


# ----------------------------
# Right: results + execution
# ----------------------------
with right:
    st.subheader("Son sonuç")

    # Quick query execution block
    if run_quick and selected_quick != "(yok)":
        sql_q = quick_queries[selected_quick].strip()
        st.session_state.history.append(
            {"question": f"[quick] {selected_quick}", "sql": sql_q, "answer": "", "trace": {"mode": "quick_query"}}
        )

    if st.session_state.history:
        last = st.session_state.history[-1]
        sql_raw = (last.get("sql") or "").strip()

        st.caption("Üretilen SQL")
        st.code(sql_raw, language="sql")

        col1, col2 = st.columns([1, 1])
        with col1:
            run_btn = st.button("SQL'i çalıştır", type="primary", use_container_width=True)
        with col2:
            explain_btn = st.button("Sadece doğrula (run yok)", type="secondary", use_container_width=True)

        if auto_run or run_btn:
            try:
                safe_sql = enforce_readonly(sql_raw, default_limit=int(default_limit))
                df = run_sql(st.session_state.conn, safe_sql)
                st.dataframe(df, use_container_width=True, height=420)
                st.caption(f"{len(df)} satır gösteriliyor.")
            except Exception as e:
                st.error(f"Çalıştırma hatası: {e}")

        if explain_btn and not (auto_run or run_btn):
            try:
                safe_sql = enforce_readonly(sql_raw, default_limit=int(default_limit))
                st.success("SQL read-only doğrulamasından geçti.")
                st.code(safe_sql, language="sql")
            except Exception as e:
                st.error(f"Doğrulama hatası: {e}")

        if debug:
            st.caption("Trace")
            st.json(last.get("trace", {}))
    else:
        st.info("Henüz soru sorulmadı.")
