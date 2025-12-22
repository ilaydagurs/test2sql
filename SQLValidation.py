import re
import datetime

def sql_validation_node(state: GraphState):
    # Boşlukları sil ve hepsini büyük harf yap
    query = state.get("sql_query", "").strip().upper()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Komut olarak sadece bunlarla başlayabilir
    allowed_starts = ("SELECT", "WITH")
    if not query.startswith(allowed_starts):
        log = f"[{timestamp}] SQL_DENIED: Query must start with SELECT or WITH. Detected: {query[:10]}..."
        return {"is_sql_safe": False, "logs": [log]}

    # Column isimlerini etkilemeden yasaklı komutlar
    forbidden_pattern = r"\b(DELETE|UPDATE|INSERT|DROP|TRUNCATE|ALTER|CREATE|RENAME|GRANT|REVOKE|REPLACE|EXEC|CALL)\b"
    
    if re.search(forbidden_pattern, query):
        
        detected = re.findall(forbidden_pattern, query)
        log = f"[{timestamp}] SQL_DENIED: Forbidden keyword(s) detected: {detected}"
        return {"is_sql_safe": False, "logs": [log]}

    # Birden fazla komutu engelleme
    if ";" in query.rstrip(";"):
        log = f"[{timestamp}] SQL_DENIED: Multiple statements (;) detected."
        return {"is_sql_safe": False, "logs": [log]}

    # Komut güvenli
    return {
        "is_sql_safe": True, 
        "logs": [f"[{timestamp}] SQL_SUCCESS: Complex Read-Only query validated."]
    }

workflow.add_node("sql_validation", sql_validation_node)
