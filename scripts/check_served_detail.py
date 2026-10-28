import urllib.request
r=urllib.request.urlopen('http://127.0.0.1:8000/auth.js')
data=r.read().decode('utf-8','replace')
lines=data.splitlines()
if len(lines)>=119:
    print('L119:', repr(lines[118]))
print('has_open:', 'openAuthModal' in data)
idx=data.find('openAuthModal')
print('first_idx:', idx)
