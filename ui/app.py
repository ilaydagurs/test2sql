import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import streamlit as st

from ui.db import init_conn, run_sql
from ui.validators import enforce_readonly
from ui.graph_client import text2sql

st.set_page_config(page_title="Text2SQL", layout="wide")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "history" not in st.session_state:
    st.session_state.history = []
if "conn" not in st.session_state:
    st.session_state.conn = init_conn(":memory:")

st.sidebar.title("ayarlar")
role = st.sidebar.selectbox("kullanıcı rolü", ["bank_employee", "manager", "auditor"])
debug = st.sidebar.toggle("debug/trace göster", value=True)
auto_run = st.sidebar.toggle("sql otomatik çalıştır", value=True)

st.title("text2sql chat (mvp)")

left, right = st.columns([1, 1], gap="large")

with left:
    st.subheader("sohbet")
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.write(m["content"])

    question = st.chat_input("sorunu yaz: örn. 'son 10 işlem?'")
    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.write(question)

        result = text2sql(question=question, role=role, debug=debug)
        sql = result.get("sql", "")
        answer = result.get("answer", "")
        trace = result.get("trace", {})

        st.session_state.history.append(
            {"question": question, "sql": sql, "answer": answer, "trace": trace}
        )

        with st.chat_message("assistant"):
            st.write(answer)
            st.code(sql, language="sql")

with right:
    st.subheader("son sonuç")
    if st.session_state.history:
        last = st.session_state.history[-1]
        sql_raw = last["sql"]

        st.caption("üretilen sql")
        st.code(sql_raw, language="sql")

        run_btn = st.button("sql'i çalıştır", type="primary")

        if auto_run or run_btn:
            try:
                safe_sql = enforce_readonly(sql_raw, default_limit=200)
                df = run_sql(st.session_state.conn, safe_sql)
                st.dataframe(df, use_container_width=True)
            except Exception as e:
                st.error(f"çalıştırma hatası: {e}")

        if debug:
            st.caption("trace")
            st.json(last.get("trace", {}))
    else:
        st.info("henüz soru sorulmadı.")
