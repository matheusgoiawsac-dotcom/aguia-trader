from pathlib import Path
p = Path("static/auth.js")
c = p.read_text(encoding="utf-8")
if "_directAutoOpen" not in c:
    add = "\n// Abertura direta apos splash (garantia)\n(function(){\n  var fired = false;\n  function tryOpen(){ if(fired) return; fired = true; try{ if(typeof checkAndOpen === 'function') checkAndOpen(); }catch(e){} }\n  window.addEventListener('aguia:splash-done', tryOpen, {once:true});\n  setTimeout(tryOpen, 6600);\n  setTimeout(tryOpen, 8800);\n  if(document.readyState === 'loading'){ document.addEventListener('DOMContentLoaded', function(){ setTimeout(tryOpen, 7200); }); } else { setTimeout(tryOpen, 7200); }\n})();\n"
    c += add
    p.write_text(c, encoding="utf-8")
    print("done")
else:
    print("exists")
