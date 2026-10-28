with open("static/auth.js","r",encoding="utf-8-sig") as f:
    s = f.read()
compile(s,"auth.js","exec")
print("ok")
