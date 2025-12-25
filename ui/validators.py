import re

def enforce_readonly(sql: str, default_limit: int = 200) -> str:
    s = (sql or "").strip().rstrip(";")
    if not s:
        raise ValueError("boş sql")

    if not re.match(r"^(select|with)\b", s, flags=re.IGNORECASE):
        raise ValueError("sadece SELECT/WITH sorgularına izin var")

    if re.search(r"\blimit\b", s, flags=re.IGNORECASE) is None:
        s = f"{s} LIMIT {default_limit}"

    return s + ";"
