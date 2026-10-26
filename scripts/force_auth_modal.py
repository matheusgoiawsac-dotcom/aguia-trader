from pathlib import Path
p = Path("static/script.js")
c = p.read_text(encoding="utf-8")
if "forceAuthModal" not in c:
    add = """

// Forçar abertura do modal de autenticação após splash (garantia)
setTimeout(function(){
  try {
    if(sessionStorage.getItem('aguia_guest') === '1') return;
    fetch('/api/auth/me').then(function(r){return r.json();}).then(function(data){
      var authed = data && data.sucesso && data.dados && data.dados.autenticado;
      if(!authed && typeof window.openAuthModal === 'function'){
        window.openAuthModal();
      }
    }).catch(function(){
      if(typeof window.openAuthModal === 'function') window.openAuthModal();
    });
  } catch(e){}
}, 6600);
"""
    c += add
    p.write_text(c, encoding="utf-8")
    print("done")
else:
    print("exists")
