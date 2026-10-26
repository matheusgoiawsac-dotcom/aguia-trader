from pathlib import Path
p = Path("static/style.css")
c = p.read_text(encoding="utf-8")
old = """.navbar-right {
    display: flex;
    align-items: center;
    gap: 0.85rem;
    margin-right: 0;
}"""
new = """.navbar-right {
    display: flex;
    align-items: center;
    gap: 0.85rem;
    margin-right: 0;
    position: relative;
}"""
if old in c and "position: relative" not in c.split(old)[1][:80]:
    c2 = c.replace(old, new)
    p.write_text(c2, encoding="utf-8")
    print("done")
else:
    print("ok")
