from pathlib import Path
p = Path("static/script.js")
c = p.read_text(encoding="utf-8")
old = """(function(){
  const btn = document.getElementById('btnEntrarCadastro');
  const menu = document.getElementById('userDropdown');
  if (!btn || !menu) return;
  const open = () => { menu.classList.add('open'); menu.setAttribute('aria-hidden','false'); };
  const close = () => { menu.classList.remove('open'); menu.setAttribute('aria-hidden','true'); };
  btn.addEventListener('click', (e) => { e.stopPropagation(); menu.classList.contains('open') ? close() : open(); });
  document.addEventListener('click', (e) => { if (!menu.contains(e.target) && e.target !== btn) close(); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') close(); });
})();
"""
new = """(function(){
  // Placeholder - handlers are managed by auth integration
})();
"""
if old in c:
    c2 = c.replace(old, new)
    p.write_text(c2, encoding="utf-8")
    print("done")
else:
    print("notfound")
