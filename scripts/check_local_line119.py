with open("static/auth.js","r",encoding="utf-8-sig") as f:
    lines=f.readlines()
if len(lines)>=119:
    print(repr(lines[118]))
