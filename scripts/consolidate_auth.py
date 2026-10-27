from pathlib import Path
p = Path("static/auth.js")
c = p.read_text(encoding="utf-8")
# Make checkAndOpen global
if "window._aguiaAuthCheckOpen" not in c:
    c = c.replace("  async function checkAndOpen(){", "  async function checkAndOpen(){\n    window._aguiaAuthCheckOpen = checkAndOpen;")
old_end = """})();\n// Abertura direta apos splash (garantia)\n(function(){\n  var fired = false;\n  function tryOpen(){ if(fired) return; fired = true; try{ if(typeof checkAndOpen === 'function') checkAndOpen(); }catch(e){} }\n  window.addEventListener('aguia:splash-done', tryOpen, {once:true});\n  setTimeout(tryOpen, 6600);\n  setTimeout(tryOpen, 8800);\n  if(document.readyState === 'loading'){ document.addEventListener('DOMContentLoaded', function(){ setTimeout(tryOpen, 7200); }); } else { setTimeout(tryOpen, 7200); }\n})();"""
new_end = """})();\n// Abertura direta apos splash (garantia) - unico fluxo\n(function(){\n  var fired = false;\n  function tryOpen(){ \n    if(fired) return; \n    fired = true; \n    try{ \n      if(typeof window._aguiaAuthCheckOpen === 'function') window._aguiaAuthCheckOpen(); \n      else if(typeof checkAndOpen === 'function') checkAndOpen(); \n    }catch(e){} \n  }\n  window.addEventListener('aguia:splash-done', tryOpen, {once:true});\n  setTimeout(tryOpen, 6800);\n  if(document.readyState === 'loading'){ document.addEventListener('DOMContentLoaded', function(){ setTimeout(tryOpen, 7400); }); } else { setTimeout(tryOpen, 7400); }\n})();"""
if old_end in c:
    c2 = c.replace(old_end, new_end)
    p.write_text(c2, encoding="utf-8")
    print("done")
else:
    print("notfound")
