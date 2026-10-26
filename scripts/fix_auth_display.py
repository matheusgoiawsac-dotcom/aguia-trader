from pathlib import Path
p = Path("static/auth.js")
c = p.read_text(encoding="utf-8")
new = """  // Auto-show after splash
  async function checkAndOpen(){
    try {
      if(overlay.classList.contains('open')) return;
      const res = await fetch('/api/auth/me');
      const data = await res.json();
      const authed = data && data.sucesso && data.dados && data.dados.autenticado;
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
  setTimeout(checkAndOpen, 8500);
  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', function(){ setTimeout(checkAndOpen, 7000); });
  } else {
    setTimeout(checkAndOpen, 7000);
  }
})();"""
idx = c.find("// Auto-show after splash")
if idx >= 0:
    c2 = c[:idx] + new
    p.write_text(c2, encoding="utf-8")
    print("done")
else:
    print("nope")
