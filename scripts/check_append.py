from pathlib import Path
p = Path("static/auth.js")
c = p.read_text(encoding="utf-8")
print(c.count("appendChild"))
