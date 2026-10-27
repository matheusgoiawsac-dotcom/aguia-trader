from pathlib import Path
p = Path("static/auth.js")
c = p.read_text(encoding="utf-8")
old = """  function closeGuest(){
    overlay.classList.remove('open');
    try { sessionStorage.setItem('aguia_guest', '1'); } catch(e){}
    if(typeof window.aguiaAuthGuest === 'function') window.aguiaAuthGuest();
  }
  closeBtn.addEventListener('click', closeGuest);
  visitorBtn.addEventListener('click', closeGuest);
  overlay.addEventListener('click', (e)=>{ if(e.target === overlay) closeGuest(); });
  document.addEventListener('keydown', (e)=>{ if(e.key==='Escape' && overlay.classList.contains('open')) closeGuest(); });"""
new = """  function setGuestChoice(){
    try { sessionStorage.setItem('aguia_guest', '1'); } catch(e){}
    if(typeof window.aguiaAuthGuest === 'function') window.aguiaAuthGuest();
  }
  function closeGuest(){
    overlay.classList.remove('open');
    setGuestChoice();
  }
  closeBtn.addEventListener('click', closeGuest);
  visitorBtn.addEventListener('click', closeGuest);
  overlay.addEventListener('click', (e)=>{ if(e.target === overlay) closeGuest(); });
  document.addEventListener('keydown', (e)=>{ if(e.key==='Escape' && overlay.classList.contains('open')) closeGuest(); });"""
if old in c:
    c2 = c.replace(old, new)
    p.write_text(c2, encoding="utf-8")
    print("done")
else:
    print("notfound")
