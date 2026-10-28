with open("static/auth.js","r",encoding="utf-8-sig") as f:
    content=f.read()
idx_decl = content.find("const loginForm")
idx_use = content.find("loginForm.addEventListener")
print(idx_decl, idx_use)
