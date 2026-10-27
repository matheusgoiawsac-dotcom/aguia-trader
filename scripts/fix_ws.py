from pathlib import Path
p = Path("static/auth.js")
c = p.read_text(encoding="utf-8")
c2 = "\n".join([l.rstrip() for l in c.splitlines()]) + "\n"
p.write_text(c2, encoding="utf-8")
