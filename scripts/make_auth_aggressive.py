from pathlib import Path
p = Path("static/auth.js")
c = p.read_text(encoding="utf-8")
old = """  // Auto-show after splash
  window.addEventListener('aguia:splash-done', async ()=>{
    try {
      const res = await fetch('/api/auth/me');
      const data = await res.json();
      const authed = data.sucesso && data.dados && data.dados.autenticado;
      const guest = sessionStorage.getItem('aguia_guest') === '1';
      if(!authed && !guest){
        if(typeof window.openAuthModal === 'function') window.openAuthModal();
      }
    } catch(e){
      const guest = sessionStorage.getItem('aguia_guest') === '1';
      if(!guest && typeof window.openAuthModal === 'function') window.openAuthModal();
    }
  });
"""
new = """  // Auto-show after splash
  async function checkAndOpen(){
    try {
      const res = await fetch('/api/auth/me');
      const data = await res.json();
      const authed = data.sucesso && data.dados && data.dados.autenticado;
      const guest = sessionStorage.getItem('aguia_guest') === '1';
      if(!authed && !guest){
        if(typeof window.openAuthModal === 'function') window.openAuthModal();
      }
    } catch(e){
      const guest = sessionStorage.getItem('aguia_guest') === '1';
      if(!guest && typeof window.openAuthModal === 'function') window.openAuthModal();
    }
  }
  window.addEventListener('aguia:splash-done', checkAndOpen);
  setTimeout(checkAndOpen, 6500);
  setTimeout(checkAndOpen, 8000);
"""
if old in c:
    c = c.replace(old, new)
    p.write_text(c, encoding="utf-8")
    print("done")
else:
    print("notfound")
