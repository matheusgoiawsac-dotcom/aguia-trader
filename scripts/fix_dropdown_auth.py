from pathlib import Path
p = Path("static/script.js")
c = p.read_text(encoding="utf-8")
old = """// Auth integration
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
    if(relBtn){ relBtn.onclick = ()=>{ alert('Relat\\u00f3rios em desenvolvimento'); }; }
    if(sairBtn){ sairBtn.textContent='Entrar / Criar conta'; sairBtn.classList.remove('danger'); sairBtn.onclick = ()=>{ if(typeof window.openAuthModal==='function') window.openAuthModal(); }; }
    if(btn){ btn.setAttribute('aria-label','Entrar / Cadastrar'); }
  }

  async function loadAuth(){
    try {
      const res = await fetch('/api/auth/me');
      const data = await res.json();
      if(data.sucesso && data.dados && data.dados.autenticado && data.dados.user){
        const u = data.dados.user;
        if(nameEl) nameEl.textContent = u.display_name || u.email_original || 'Usu\\u00e1rio';
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
})();"""
new = """// Auth integration
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

  function openMenu(){ if(menu){ menu.classList.add('open'); menu.setAttribute('aria-hidden','false'); } }
  function closeMenu(){ if(menu){ menu.classList.remove('open'); menu.setAttribute('aria-hidden','true'); } }
  function toggleMenu(e){ if(e){ e.preventDefault(); e.stopPropagation(); } if(menu){ menu.classList.contains('open') ? closeMenu() : openMenu(); } }

  function setGuest(){
    if(nameEl) nameEl.textContent = 'Visitante';
    if(emailEl) emailEl.textContent = 'sem conta';
    if(avatarLg){ avatarLg.innerHTML=''; avatarLg.classList.remove('has-img'); }
    if(manageBtn){ manageBtn.onclick = function(e){ e.preventDefault(); closeMenu(); if(typeof window.openAuthModal==='function') window.openAuthModal(); }; }
    if(secBtn){ secBtn.onclick = function(e){ e.preventDefault(); closeMenu(); if(typeof window.openAuthModal==='function') window.openAuthModal(); }; }
    if(relBtn){ relBtn.onclick = function(e){ e.preventDefault(); closeMenu(); alert('Relat\\u00f3rios em desenvolvimento'); }; }
    if(sairBtn){ sairBtn.textContent='Entrar / Criar conta'; sairBtn.classList.remove('danger'); sairBtn.onclick = function(e){ e.preventDefault(); closeMenu(); if(typeof window.openAuthModal==='function') window.openAuthModal(); }; }
    if(btn){ btn.setAttribute('aria-label','Entrar / Cadastrar'); btn.onclick = toggleMenu; }
  }

  async function loadAuth(){
    try {
      const res = await fetch('/api/auth/me');
      const data = await res.json();
      if(data.sucesso && data.dados && data.dados.autenticado && data.dados.user){
        const u = data.dados.user;
        if(nameEl) nameEl.textContent = u.display_name || u.email_original || 'Usu\\u00e1rio';
        if(emailEl) emailEl.textContent = u.email_original || u.email_normalized || '';
        if(avatarLg){
          avatarLg.innerHTML='';
          const img = document.createElement('img');
          img.src = '/api/auth/avatar/' + u.id + '?t=' + Date.now();
          img.style.width='100%'; img.style.height='100%'; img.style.objectFit='cover';
          avatarLg.appendChild(img);
          avatarLg.classList.add('has-img');
        }
        if(manageBtn){ manageBtn.onclick = function(e){ e.preventDefault(); closeMenu(); window.location.href = 'conta.html'; }; }
        if(relBtn){ relBtn.onclick = function(e){ e.preventDefault(); closeMenu(); window.location.href = 'conta.html'; }; }
        if(secBtn){ secBtn.onclick = function(e){ e.preventDefault(); closeMenu(); window.location.href = 'conta.html'; }; }
        if(sairBtn){ sairBtn.textContent='Sair'; sairBtn.classList.add('danger'); sairBtn.onclick = async function(e){
          e.preventDefault(); closeMenu();
          try { await fetch('/api/auth/logout',{method:'POST'}); } catch(ex){}
          location.reload();
        }; }
        if(btn){ btn.title = u.display_name || ''; btn.onclick = toggleMenu; }
        return;
      }
    } catch(e){}
    setGuest();
  }

  window.aguiaAuthSuccess = function(u){ loadAuth(); };
  window.aguiaAuthGuest = function(){ setGuest(); };

  if(btn){ btn.onclick = toggleMenu; }
  document.addEventListener('click', function(e){
    if(!menu) return;
    if(menu.contains(e.target)) return;
    if(btn && btn.contains(e.target)) return;
    closeMenu();
  });
  document.addEventListener('keydown', function(e){ if(e.key === 'Escape') closeMenu(); });

  loadAuth();
  setTimeout(async function(){
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
})();"""
if old in c:
    c2 = c.replace(old, new)
    p.write_text(c2, encoding="utf-8")
    print("done")
else:
    print("notfound")
