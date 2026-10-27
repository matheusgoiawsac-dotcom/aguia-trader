from pathlib import Path
p = Path("static/auth.js")
c = p.read_text(encoding="utf-8")
idx = c.find("window.openAuthModal")
if idx >= 0:
    print(c[idx:idx+150])
else:
    print("not")
