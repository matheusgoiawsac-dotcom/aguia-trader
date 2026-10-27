from pathlib import Path
p = Path("static/script.js")
c = p.read_text(encoding="utf-8")
old1 = "      var res = await fetch('/api/auth/me');\n      var data = await res.json();"
new1 = "      var data = await (window._aguiaAuthFetch ? window._aguiaAuthFetch() : fetch('/api/auth/me').then(function(r){return r.json();}));"
if old1 in c:
    c2 = c.replace(old1, new1)
    p.write_text(c2, encoding="utf-8")
    print("done")
else:
    print("notfound")
