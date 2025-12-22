from text2sql.app import run

def test_ask_metadata_path():
    out = run("Hangi tablolar var?", "manager")
    assert out["intent"] == "ASK_METADATA"
    assert "tablolar" in out["final_answer"].lower()

def test_generate_sql_path():
    out = run("Son 7 günde satışları getir", "manager")
    assert out["intent"] == "GENERATE_SQL"
    assert out.get("sql_ok") is True
    assert out.get("result") is not None

def test_refuse_drop():
    out = run("DROP TABLE satislar", "admin")
    assert out["intent"] == "REFUSE"
    assert "güvenlik" in out["final_answer"].lower()

def test_clarify_short():
    out = run("?", "manager")
    assert out["intent"] == "CLARIFY"
    assert len(out["final_answer"]) > 0

def test_execute_sql_provided():
    out = run("rapor", "manager", sql="SELECT * FROM satislar")
    assert out["intent"] == "EXECUTE_SQL"
    assert out.get("sql_ok") is True
