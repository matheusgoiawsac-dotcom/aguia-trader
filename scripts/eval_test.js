const fs=require('fs');
try{
  const code=fs.readFileSync('static/auth.js','utf8');
  eval(code);
}catch(e){
  console.log(e.toString());
}
