from pathlib import Path
p = Path("static/script.js")
c = p.read_text(encoding="utf-8")
idx = c.rfind("// Auth integration")
if idx >= 0:
    c2 = c[:idx]
    p.write_text(c2, encoding="utf-8")
    print("cut")
else:
    print("no")
