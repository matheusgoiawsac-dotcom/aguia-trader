import urllib.request
r=urllib.request.urlopen('http://127.0.0.1:8000/auth.js')
d=r.read()
s=d.decode('utf-8','replace')
idx=s.find('openAuthModal')
print('idx',idx)
