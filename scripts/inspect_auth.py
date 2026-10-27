from pathlib import Path
p = Path("static/auth.js")
c = p.read_text(encoding="utf-8")
idx = c.find("openAuthModal")
if idx >= 0:
    print(c[max(0,idx-60):idx+120])
else:
    print("not found")
