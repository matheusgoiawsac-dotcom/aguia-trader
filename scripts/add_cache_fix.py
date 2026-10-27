from pathlib import Path
p = Path("static/script.js")
c = p.read_text(encoding="utf-8")
old = """// Cache de autenticacao para evitar chamadas repetidas
window._aguiaAuthCache = window._aguiaAuthCache || {ts:0, data:null};
window._aguiaAuthFetch = window._aguiaAuthFetch || function(force){
  var now = Date.now();
  if(!force && window._aguiaAuthCache.data && now - window._aguiaAuthCache.ts < 60000){
    return Promise.resolve(window._aguiaAuthCache.data);
  }
  return fetch('/api/auth/me').then(function(r){return r.json();}).then(function(data){
    window._aguiaAuthCache = {ts: Date.now(), data: data};
    return data;
  });
};"""
new = """// Cache de autenticacao para evitar chamadas repetidas
window._aguiaAuthCache = window._aguiaAuthCache || {ts:0, data:null};
window._aguiaAuthFetchPromise = window._aguiaAuthFetchPromise || null;
window._aguiaAuthFetch = window._aguiaAuthFetch || function(force){
  var now = Date.now();
  if(!force && window._aguiaAuthCache.data && now - window._aguiaAuthCache.ts < 60000){
    return Promise.resolve(window._aguiaAuthCache.data);
  }
  if(!force && window._aguiaAuthFetchPromise){
    return window._aguiaAuthFetchPromise;
  }
  var p = fetch('/api/auth/me').then(function(r){
    if(!r.ok){
      throw new Error('http_' + r.status);
    }
    return r.json();
  }).then(function(data){
    window._aguiaAuthCache = {ts: Date.now(), data: data};
    window._aguiaAuthFetchPromise = null;
    return data;
  }).catch(function(err){
    window._aguiaAuthFetchPromise = null;
    throw err;
  });
  window._aguiaAuthFetchPromise = p;
  return p;
};
window._aguiaAuthInvalidate = function(){
  window._aguiaAuthCache = {ts:0, data:null};
  window._aguiaAuthFetchPromise = null;
};"""
if old in c:
    c2 = c.replace(old, new)
    p.write_text(c2, encoding="utf-8")
    print("done")
else:
    print("notfound")
