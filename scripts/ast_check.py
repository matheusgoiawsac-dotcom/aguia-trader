import ast
with open("static/auth.js","r",encoding="utf-8-sig") as f:
    code=f.read()
try:
    ast.parse(code)
    print("ok")
except Exception as e:
    print(e)
