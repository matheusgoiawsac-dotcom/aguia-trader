from pathlib import Path
p = Path("static/auth.js")
c = p.read_text(encoding="utf-8")
if "aguia:splash-done" not in c:
    add = "\n  window.addEventListener('aguia:splash-done', function(){ try{ if(typeof checkAndOpen==='function') checkAndOpen(); }catch(e){} });\n"
    c += add
    p.write_text(c, encoding="utf-8")
    print("done")
else:
    print("exists")
