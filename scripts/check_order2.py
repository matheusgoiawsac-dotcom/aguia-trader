with open("static/auth.js","r",encoding="utf-8-sig") as f:
    content=f.read()
decl = content.find("loginForm")
use = content.find("loginForm.addEventListener")
print(decl, use)
