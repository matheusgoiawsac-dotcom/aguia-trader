with open("static/auth.js","r",encoding="utf-8-sig") as f:
    s=f.read()
old = "  if(loginForm) loginForm.addEventListener('submit', async (e)=>{"
new = "  try { var lf2 = (typeof loginForm !== 'undefined') ? loginForm : ((overlay && overlay.querySelector) ? overlay.querySelector('#authLoginForm') : null); if(lf2) lf2.addEventListener('submit', async function(e){"
if old in s:
    s2 = s.replace(old, new)
    with open("static/auth.js","w",encoding="utf-8") as f:
        f.write(s2)
    print("done")
else:
    print("not")
