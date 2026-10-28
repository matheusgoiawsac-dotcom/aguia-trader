import urllib.request
r=urllib.request.urlopen('http://127.0.0.1:8000/auth.js?debug=x')
data=r.read().decode('utf-8','replace')
lines=data.splitlines()
for i in range(105,125):
    if i < len(lines):
        print(i+1, repr(lines[i]))
