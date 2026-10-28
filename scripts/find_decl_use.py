with open("static/auth.js","r",encoding="utf-8-sig") as f:
    lines=f.readlines()
decl=None
for i,l in enumerate(lines):
    if "loginForm" in l and ("var " in l or "let " in l or "const " in l):
        decl=i+1
        break
use=None
for i,l in enumerate(lines):
    if "loginForm.addEventListener" in l:
        use=i+1
        break
print(decl,use)
