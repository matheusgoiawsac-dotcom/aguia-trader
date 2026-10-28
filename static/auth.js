/* Auth modal logic */
(function(){
  const overlay = document.createElement('div');
  overlay.className = 'auth-overlay';
  overlay.innerHTML = `
    <div class="auth-modal" role="dialog" aria-modal="true" tabindex="-1">
      <button class="auth-close" id="authClose" aria-label="Fechar e continuar como visitante">✕</button>
      <div class="auth-panel">
        <div class="auth-tabs">
          <button class="auth-tab active" data-tab="login">Entrar</button>
          <button class="auth-tab" data-tab="register">Criar conta</button>
        </div>
        <form class="auth-form" id="authLoginForm">
          <div class="auth-field"><label for="loginEmail">E-mail</label><input id="loginEmail" type="email" autocomplete="username" placeholder="Digite seu e-mail" required></div>
          <div class="auth-field"><label for="loginPass">Senha</label><div class="auth-password-wrap"><input id="loginPass" type="password" autocomplete="current-password" placeholder="Digite sua senha" required><button type="button" class="auth-pass-toggle" data-target="loginPass" aria-label="Mostrar/ocultar senha"><svg class="eye-open" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg><svg class="eye-closed" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="display:none"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg></button></div></div>
          <div class="auth-actions">
            <button class="auth-btn" type="submit">Entrar</button>
            <div class="auth-error" id="loginError"></div>
            <div class="auth-success" id="loginSuccess"></div>
          </div>
        </form>
        <form class="auth-form" id="authRegisterForm" style="display:none">
          <div class="auth-avatar-area">
            <div class="auth-avatar" id="regAvatar">
              <svg class="auth-avatar-empty" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="8" r="4"></circle><path d="M4 20c0-4 4-6 8-6s8 2 8 6"></path></svg>
              <img id="regAvatarImg" style="display:none" alt="Avatar">
              <button type="button" class="auth-camera" id="regCamera" aria-label="Selecionar foto"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path><circle cx="12" cy="13" r="4"></circle></svg></button>
            </div>
            <input type="file" id="regAvatarFile" accept="image/jpeg,image/png,image/webp" style="display:none">
          </div>
          <div class="auth-field"><label for="regNome">Nome completo</label><input id="regNome" autocomplete="name" placeholder="Digite seu nome" required></div>
          <div class="auth-field"><label for="regEmail">E-mail</label><input id="regEmail" type="email" autocomplete="email" placeholder="Digite seu e-mail" required></div>
          <div class="auth-row">
            <div class="auth-field"><label for="regSenha">Crie sua senha</label><div class="auth-password-wrap"><input id="regSenha" type="password" autocomplete="new-password" placeholder="Crie uma senha" required><button type="button" class="auth-pass-toggle" data-target="regSenha" aria-label="Mostrar/ocultar senha"><svg class="eye-open" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg><svg class="eye-closed" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="display:none"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg></button></div></div>
            <div class="auth-field"><label for="regSenha2">Confirme a senha</label><div class="auth-password-wrap"><input id="regSenha2" type="password" autocomplete="new-password" placeholder="Confirme sua senha" required><button type="button" class="auth-pass-toggle" data-target="regSenha2" aria-label="Mostrar/ocultar senha"><svg class="eye-open" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg><svg class="eye-closed" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="display:none"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg></button></div></div>
          </div>
          <div class="auth-field"><label for="regIdade">Data de nascimento</label><input id="regIdade" type="date" required></div>
          <div class="auth-actions">
            <button class="auth-btn" type="submit">Criar minha conta</button>
            <div class="auth-error" id="regError"></div>
            <div class="auth-success" id="regSuccess"></div>
          </div>
        </form>
        <div class="auth-visitor" id="authVisitor">Continuar como visitante</div>
      </div>
    </div>
  `;
  document.body.appendChild(overlay);

  const tabs = overlay.querySelectorAll('.auth-tab');
  const loginForm = overlay.querySelector('#authLoginForm');
  const regForm = overlay.querySelector('#authRegisterForm');
  const closeBtn = overlay.querySelector('#authClose');
  const visitorBtn = overlay.querySelector('#authVisitor');
  const modal = overlay.querySelector('.auth-modal');

  tabs.forEach(t=>{
    t.addEventListener('click',()=>{
      tabs.forEach(x=>x.classList.remove('active'));
      t.classList.add('active');
      if(t.dataset.tab==='login'){ loginForm.style.display='flex'; regForm.style.display='none'; }
      else { loginForm.style.display='none'; regForm.style.display='flex'; }
    });
  });

  function setGuestChoice(){
    try { sessionStorage.setItem('aguia_guest', '1'); } catch(e){}
    if(typeof window.aguiaAuthGuest === 'function') window.aguiaAuthGuest();
  }
  function closeModalOnly(){
    overlay.classList.remove('open');
  }
  if(closeBtn) closeBtn.addEventListener('click', closeModalOnly);
  if(visitorBtn) visitorBtn.addEventListener('click', function(){ overlay.classList.remove('open'); setGuestChoice(); });
  overlay.addEventListener('click', (e)=>{ if(e.target === overlay) closeModalOnly(); });
  document.addEventListener('keydown', (e)=>{ if(e.key==='Escape' && overlay.classList.contains('open')) closeModalOnly(); });

  window.openAuthModal = function(){
    overlay.classList.add('open');
    setTimeout(()=>{ try { modal.focus(); } catch(e){} }, 50);
  };
  window.closeAuthModal = function(){ overlay.classList.remove('open'); };

  // avatar
  const cam = overlay.querySelector('#regCamera');
  const file = overlay.querySelector('#regAvatarFile');
  const avImg = overlay.querySelector('#regAvatarImg');
  const avEmpty = overlay.querySelector('.auth-avatar svg');
  let avatarDataUrl = null;
  if(cam) cam.addEventListener('click', (e)=>{ e.preventDefault(); file.click(); });
  if(file) file.addEventListener('change', ()=>{
    const f = file.files[0];
    if(!f) return;
    if(f.size > 1024*1024){ alert('Imagem muito grande (máx. 1MB)'); return; }
    if(!['image/jpeg','image/png','image/webp'].includes(f.type)){ alert('Formato não suportado (JPG, PNG, WebP)'); return; }
    const reader = new FileReader();
    reader.onload = e=>{
      avatarDataUrl = e.target.result;
      if(avImg){ avImg.src = avatarDataUrl; avImg.style.display='block'; }
      if(avEmpty) avEmpty.style.display='none';
    };
    reader.readAsDataURL(f);
  });

  // password visibility toggles
  overlay.querySelectorAll('.auth-pass-toggle').forEach(btn=>{
    btn.addEventListener('click', (e)=>{
      e.preventDefault();
      e.stopPropagation();
      const targetId = btn.getAttribute('data-target');
      const input = targetId ? document.getElementById(targetId) : null;
      if(!input) return;
      if(input.type === 'password'){
        input.type = 'text';
        const eyeOpen = btn.querySelector('.eye-open');
        const eyeClosed = btn.querySelector('.eye-closed');
        if(eyeOpen) eyeOpen.style.display = 'none';
        if(eyeClosed) eyeClosed.style.display = 'block';
      }else{
        input.type = 'password';
        const eyeOpen = btn.querySelector('.eye-open');
        const eyeClosed = btn.querySelector('.eye-closed');
        if(eyeOpen) eyeOpen.style.display = 'block';
        if(eyeClosed) eyeClosed.style.display = 'none';
      }
    });
  });

  if(loginForm) loginForm.addEventListener('submit', async (e)=>{
    e.preventDefault();
    const email = document.getElementById('loginEmail').value;
    const pass = document.getElementById('loginPass').value;
    const err = document.getElementById('loginError');
    const ok = document.getElementById('loginSuccess');
    if(err) err.textContent=''; if(ok) ok.textContent='';
    try {
      const res = await fetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email, senha:pass})});
      const data = await res.json();
      if(data.sucesso){
        if(ok) ok.textContent='Login realizado';
        if(typeof window.aguiaAuthSuccess === 'function') window.aguiaAuthSuccess(data.dados && data.dados.user);
        setTimeout(()=>overlay.classList.remove('open'), 400);
      } else {
        if(err) err.textContent = data.erro || 'E-mail ou senha inválidos';
      }
    } catch(ex){
      if(err) err.textContent = 'Erro de rede';
    }
  });

  if(regForm) regForm.addEventListener('submit', async (e)=>{
    e.preventDefault();
    const nome = document.getElementById('regNome').value;
    const email = document.getElementById('regEmail').value;
    const senha = document.getElementById('regSenha').value;
    const senha2 = document.getElementById('regSenha2').value;
    const dataNasc = document.getElementById('regIdade').value;
    const err = document.getElementById('regError');
    const ok = document.getElementById('regSuccess');
    if(err) err.textContent=''; if(ok) ok.textContent='';
    if(senha !== senha2){ if(err) err.textContent='As senhas não coincidem'; return; }
    if(dataNasc){
      const nasc = new Date(dataNasc + 'T00:00:00');
      const hoje = new Date();
      hoje.setHours(0,0,0,0);
      if(nasc > hoje){ if(err) err.textContent='Data de nascimento inválida'; return; }
    }
    try {
      const body = {nome, email, senha, senha2, idade: dataNasc};
      if(avatarDataUrl) body.avatar = avatarDataUrl;
      const res = await fetch('/api/auth/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
      const data = await res.json();
      if(data.sucesso){
        if(ok) ok.textContent='Conta criada com sucesso';
        if(typeof window.aguiaAuthSuccess === 'function') window.aguiaAuthSuccess(data.dados && data.dados.user);
        setTimeout(()=>overlay.classList.remove('open'), 400);
      } else {
        if(err) err.textContent = data.erro || 'Erro ao cadastrar';
      }
    } catch(ex){
      if(err) err.textContent = 'Erro de rede';
    }
  });

    // Auto-show after splash
  async function checkAndOpen(){
    window._aguiaAuthCheckOpen = checkAndOpen;
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
  }
  window.addEventListener('aguia:splash-done', checkAndOpen);
  setTimeout(checkAndOpen, 6500);
  setTimeout(checkAndOpen, 8500);
  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', function(){ setTimeout(checkAndOpen, 7000); });
  } else {
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
})();
