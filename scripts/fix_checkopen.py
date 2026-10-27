from pathlib import Path
p = Path("static/auth.js")
c = p.read_text(encoding="utf-8")
old = """  async function checkAndOpen(){
    try {
      if(overlay.classList.contains('open')) return;
      const data = await (window._aguiaAuthFetch ? window._aguiaAuthFetch() : fetch('/api/auth/me').then(r=>r.json()));
      const authed = data && data.sucesso && data.dados && data.dados.autenticado;
      const guest = sessionStorage.getItem('aguia_guest') === '1';
      if(!authed && !guest){
        if(typeof window.openAuthModal === 'function') window.openAuthModal();
      }
    } catch(e){
      const guest = sessionStorage.getItem('aguia_guest') === '1';
      if(!guest && typeof window.openAuthModal === 'function') window.openAuthModal();
    }
  }"""
new = """  async function checkAndOpen(){
    try {
      if(overlay && overlay.classList && overlay.classList.contains('open')) return;
      var guest = sessionStorage.getItem('aguia_guest') === '1';
      if(guest) return;
      try {
        var data = await (window._aguiaAuthFetch ? window._aguiaAuthFetch() : fetch('/api/auth/me').then(function(r){ if(!r.ok) throw new Error('http'); return r.json(); }));
        var authed = data && data.sucesso && data.dados && data.dados.autenticado;
        if(!authed){
          if(typeof window.openAuthModal === 'function') {
            if(!(overlay && overlay.classList && overlay.classList.contains('open'))) window.openAuthModal();
          }
        }
        return;
      } catch(e){
        if(typeof window.openAuthModal === 'function') {
          if(!(overlay && overlay.classList && overlay.classList.contains('open'))) window.openAuthModal();
        }
        return;
      }
    } catch(e){
      var guest2 = sessionStorage.getItem('aguia_guest') === '1';
      if(!guest2 && typeof window.openAuthModal === 'function') {
        try { if(!(overlay && overlay.classList && overlay.classList.contains('open'))) window.openAuthModal(); } catch(ex){}
      }
    }
  }"""
if old in c:
    c2 = c.replace(old, new)
    p.write_text(c2, encoding="utf-8")
    print("done")
else:
    print("notfound")
