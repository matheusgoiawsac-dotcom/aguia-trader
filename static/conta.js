(function(){
  let currentUser = null;
  let avatarDataUrl = null;
  async function load(){
    try {
      const res = await fetch('/api/auth/me');
      const data = await res.json();
      if(!data.sucesso || !data.dados || !data.dados.autenticado){
        alert('Sessão não encontrada. Faça login novamente.');
        window.location.href = 'index.html';
        return;
      }
      currentUser = data.dados.user;
      document.getElementById('contaNome').textContent = currentUser.display_name || '-';
      document.getElementById('contaEmail').textContent = currentUser.email_original || currentUser.email_normalized || '-';
      document.getElementById('perfilNome').value = currentUser.display_name || '';
      document.getElementById('perfilIdade').value = currentUser.age || '';
      document.getElementById('perfilEmail').value = currentUser.email_original || currentUser.email_normalized || '';
      const av = document.getElementById('contaAvatar');
      const avImg = document.getElementById('contaAvatarImg');
      if(currentUser.id){
        avImg.src = '/api/auth/avatar/' + currentUser.id + '?t=' + Date.now();
        avImg.style.display = 'block';
        const svg = av.querySelector('svg');
        if(svg) svg.style.display = 'none';
      }
    } catch(e){
      window.location.href = 'index.html';
    }
  }
  document.getElementById('btnTrocarFoto').addEventListener('click', ()=>{
    document.getElementById('perfilAvatarFile').click();
  });
  document.getElementById('perfilAvatarFile').addEventListener('change', (e)=>{
    const f = e.target.files[0];
    if(!f) return;
    if(f.size > 1024*1024){ alert('Imagem muito grande'); return; }
    if(!['image/jpeg','image/png','image/webp'].includes(f.type)){ alert('Formato não suportado'); return; }
    const reader = new FileReader();
    reader.onload = ev=>{
      avatarDataUrl = ev.target.result;
      const av = document.getElementById('contaAvatar');
      const avImg = document.getElementById('contaAvatarImg');
      avImg.src = avatarDataUrl;
      avImg.style.display = 'block';
      const svg = av.querySelector('svg');
      if(svg) svg.style.display = 'none';
    };
    reader.readAsDataURL(f);
  });
  document.getElementById('btnRemoverFoto').addEventListener('click', async ()=>{
    const ok = document.getElementById('perfilSuccess');
    const err = document.getElementById('perfilError');
    ok.textContent=''; err.textContent='';
    try {
      const res = await fetch('/api/auth/update',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({remover_foto:true})});
      const data = await res.json();
      if(data.sucesso){
        ok.textContent='Foto removida';
        setTimeout(()=>location.reload(), 500);
      } else err.textContent = data.erro || 'Erro';
    } catch(ex){ err.textContent='Erro de rede'; }
  });
  document.getElementById('btnSalvarPerfil').addEventListener('click', async ()=>{
    const ok = document.getElementById('perfilSuccess');
    const err = document.getElementById('perfilError');
    ok.textContent=''; err.textContent='';
    const body = {nome: document.getElementById('perfilNome').value, idade: document.getElementById('perfilIdade').value};
    if(avatarDataUrl) body.avatar = avatarDataUrl;
    try {
      const res = await fetch('/api/auth/update',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
      const data = await res.json();
      if(data.sucesso){
        ok.textContent='Perfil atualizado';
        setTimeout(()=>location.reload(), 600);
      } else err.textContent = data.erro || 'Erro';
    } catch(ex){ err.textContent='Erro de rede'; }
  });
  document.getElementById('btnAlterarSenha').addEventListener('click', async ()=>{
    const ok = document.getElementById('senhaSuccess');
    const err = document.getElementById('senhaError');
    ok.textContent=''; err.textContent='';
    const body = {senha_atual: document.getElementById('senhaAtual').value, nova_senha: document.getElementById('novaSenha').value};
    try {
      const res = await fetch('/api/auth/change-password',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
      const data = await res.json();
      if(data.sucesso){
        ok.textContent='Senha alterada. Faça login novamente.';
        setTimeout(()=>{ window.location.href='index.html'; }, 800);
      } else err.textContent = data.erro || 'Erro';
    } catch(ex){ err.textContent='Erro de rede'; }
  });
  load();
})();
