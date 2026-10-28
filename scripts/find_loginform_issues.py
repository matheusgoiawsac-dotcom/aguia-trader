with open("static/auth.js","r",encoding="utf-8-sig") as f:
    for i,l in enumerate(f,1):
        if "loginForm" in l:
            print(i, repr(l))
