from pathlib import Path
p = Path("static/script.js")
c = p.read_text(encoding="utf-8")
if "_aguiaAuthBound" not in c:
    c2 = c.replace("  if(btn){ btn.onclick = toggleMenu; }", "  if(btn){ btn.onclick = toggleMenu; try{btn._aguiaAuthBound=true;}catch(e){} }")
    p.write_text(c2, encoding="utf-8")
    print("done")
else:
    print("ok")
