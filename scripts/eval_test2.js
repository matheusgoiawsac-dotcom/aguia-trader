const fs=require('fs');
try{
  const code='(function(){'+fs.readFileSync('static/auth.js','utf8')+'})();';
  eval(code);
  console.log(typeof globalThis.window?.openAuthModal);
}catch(e){
  console.log(e.toString());
}
