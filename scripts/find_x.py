with open("static/auth.js",encoding="utf-8") as f:
    for i,l in enumerate(f,1):
        if "\u2715" in l:
            print(i)
            break
