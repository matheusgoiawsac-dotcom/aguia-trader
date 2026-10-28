from pathlib import Path
p = Path("static/auth.js")
c = p.read_text(encoding="utf-8")
old = """  } else {
    setTimeout(checkAndOpen, 7000);
  }
})();
  // Abertura direta apos splash (garantia) - unico fluxo
(function(){
  var fired = false;
  function tryOpen(){
    if(fired) return;
    fired = true;
    try{
      if(typeof window._aguiaAuthCheckOpen === 'function') window._aguiaAuthCheckOpen();
      else if(typeof checkAndOpen === 'function') checkAndOpen();
    }catch(e){}
  }
  window.addEventListener('aguia:splash-done', tryOpen, {once:true});
  setTimeout(tryOpen, 6800);
  if(document.readyState === 'loading'){ document.addEventListener('DOMContentLoaded', function(){ setTimeout(tryOpen, 7400); }); } else { setTimeout(tryOpen, 7400); }
})();"""
new = """  }
})();
// Abertura automática após splash - unico fluxo (2s após término)
(function(){
  var scheduled = false;
  function scheduleOpen(){
    if(scheduled) return;
    scheduled = true;
    setTimeout(function(){
      try{
        if(typeof window._aguiaAuthCheckOpen === 'function'){
          window._aguiaAuthCheckOpen();
        }else if(typeof checkAndOpen === 'function'){
          checkAndOpen();
        }
      }catch(e){}
    }, 2000);
  }
  window.addEventListener('aguia:splash-done', scheduleOpen, {once:true});
})();"""
if old in c:
    c2 = c.replace(old, new)
    p.write_text(c2, encoding="utf-8")
    print("done")
else:
    print("notfound")
