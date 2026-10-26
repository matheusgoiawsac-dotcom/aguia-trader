from pathlib import Path
p = Path("static/script.js")
c = p.read_text(encoding="utf-8")
if "aguiaAuthSuccess" not in c:
    add = r"""

// Auth integration
(function(){
  const btn = document.getElementById('btnEntrarCadastro');
  const menu = document.getElementById('userDropdown');
  const nameEl = document.querySelector('#userDropdown .user-name');
  const emailEl = document.querySelector('#userDropdown .user-email');
  const avatarLg = document.querySelector('#userDropdown .user-avatar-lg');
  const pills = Array.from(document.querySelectorAll('#userDropdown .user-pill'));
  const manageBtn = pills.find(x=>/Gerenciar/i.test(x.textContent||''));
  const relBtn = pills.find(x=>/Relat/i.test(x.textContent||''));
  const secBtn = pills.find(x=>/Segur/i.test(x.textContent||''));
  const sairBtn = pills.find(x=>/Sair/i.test(x.textContent||''));

  function setGuest(){
    if(nameEl) nameEl.textContent = 'Visitante';
    if(emailEl) emailEl.textContent = 'sem conta';
    if(avatarLg){ avatarLg.innerHTML=''; avatarLg.classList.remove('has-img'); }
    if(manageBtn){ manageBtn.onclick = ()=>{ if(typeof window.openAuthModal==='function') window.openAuthModal(); }; }
    if(secBtn){ secBtn.onclick = ()=>{ if(typeof window.openAuthModal==='function') window.openAuthModal(); }; }
    if(relBtn){ relBtn.onclick = ()=>{ alert('Relatórios em desenvolvimento'); }; }
    if(sairBtn){ sairBtn.textContent='Entrar / Criar conta'; sairBtn.classList.remove('danger'); sairBtn.onclick = ()=>{ if(typeof window.openAuthModal==='function') window.openAuthModal(); }; }
    if(btn){ btn.setAttribute('aria-label','Entrar / Cadastrar'); }
  }

  async function loadAuth(){
    try {
      const res = await fetch('/api/auth/me');
      const data = await res.json();
      if(data.sucesso && data.dados && data.dados.autenticado && data.dados.user){
        const u = data.dados.user;
        if(nameEl) nameEl.textContent = u.display_name || u.email_original || 'Usuário';
        if(emailEl) emailEl.textContent = u.email_original || u.email_normalized || '';
        if(avatarLg){
          avatarLg.innerHTML='';
          const img = document.createElement('img');
          img.src = '/api/auth/avatar/' + u.id + '?t=' + Date.now();
          img.style.width='100%'; img.style.height='100%'; img.style.objectFit='cover';
          avatarLg.appendChild(img);
          avatarLg.classList.add('has-img');
        }
        if(manageBtn){ manageBtn.onclick = ()=>{ window.location.href = 'conta.html'; }; }
        if(relBtn){ relBtn.onclick = ()=>{ window.location.href = 'conta.html'; }; }
        if(secBtn){ secBtn.onclick = ()=>{ window.location.href = 'conta.html'; }; }
        if(sairBtn){ sairBtn.textContent='Sair'; sairBtn.classList.add('danger'); sairBtn.onclick = async ()=>{
          try { await fetch('/api/auth/logout',{method:'POST'}); } catch(e){}
          location.reload();
        }; }
        if(btn){ btn.title = u.display_name || ''; btn.onclick = ()=>{ /* keep menu behavior */ }; }
        return;
      }
    } catch(e){}
    setGuest();
  }

  window.aguiaAuthSuccess = function(u){ loadAuth(); };
  window.aguiaAuthGuest = function(){ setGuest(); };

  if(btn){ btn.onclick = (e)=>{ e.stopPropagation(); const m=document.getElementById('userDropdown'); if(m) m.classList.toggle('open'); }; }
  loadAuth();
  setTimeout(async ()=>{
    try {
      const res = await fetch('/api/auth/me');
      const data = await res.json();
      const authed = data.sucesso && data.dados && data.dados.autenticado;
      const guest = sessionStorage.getItem('aguia_guest') === '1';
      if(!authed && !guest){
        if(typeof window.openAuthModal==='function') window.openAuthModal();
      }
    } catch(e){}
  }, 6200);
})();
"""
    c = c + add
    p.write_text(c, encoding="utf-8")
    print("done")
else:
    print("exists")
