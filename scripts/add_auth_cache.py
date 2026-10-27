from pathlib import Path
p = Path("static/script.js")
c = p.read_text(encoding="utf-8")
if "aguiaAuthCache" not in c:
    add = "\n// Cache de autenticacao para evitar chamadas repetidas\nwindow._aguiaAuthCache = window._aguiaAuthCache || {ts:0, data:null};\nwindow._aguiaAuthFetch = window._aguiaAuthFetch || function(force){\n  var now = Date.now();\n  if(!force && window._aguiaAuthCache.data && now - window._aguiaAuthCache.ts < 60000){\n    return Promise.resolve(window._aguiaAuthCache.data);\n  }\n  return fetch('/api/auth/me').then(function(r){return r.json();}).then(function(data){\n    window._aguiaAuthCache = {ts: Date.now(), data: data};\n    return data;\n  });\n};\n"
    c2 = c.replace("// Auth integration\n(function(){", add + "// Auth integration\n(function(){")
    p.write_text(c2, encoding="utf-8")
    print("done")
else:
    print("exists")
