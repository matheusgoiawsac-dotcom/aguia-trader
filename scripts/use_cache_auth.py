from pathlib import Path
p = Path("static/auth.js")
c = p.read_text(encoding="utf-8")
old = "      const res = await fetch('/api/auth/me');\n      const data = await res.json();"
new = "      const data = await (window._aguiaAuthFetch ? window._aguiaAuthFetch() : fetch('/api/auth/me').then(r=>r.json()));"
if old in c:
    c2 = c.replace(old, new)
    p.write_text(c2, encoding="utf-8")
    print("done")
else:
    print("notfound")
