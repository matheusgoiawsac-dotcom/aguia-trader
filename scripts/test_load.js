const fs=require('fs');
const vm=require('vm');
const code=fs.readFileSync('static/auth.js','utf8');
const sandbox={
  console,
  document:{
    createElement:()=>({style:{},innerHTML:'',appendChild:()=>{},className:'',querySelector:()=>null,querySelectorAll:()=>[],addEventListener:()=>{},setAttribute:()=>{},getElementsByTagName:()=>[],focus:()=>{},classList:{add:()=>{},remove:()=>{},contains:()=>false}}),
    body:{appendChild:()=>{}},
    addEventListener:()=>{},
    querySelector:()=>null,
    querySelectorAll:()=>[],
    getElementById:()=>null,
    documentElement:{}
  },
  window:{},
  setTimeout:(fn)=>{ try{fn();}catch(e){} },
  setInterval:()=>{},
  clearInterval:()=>{},
  clearTimeout:()=>{},
  sessionStorage:{_d:{},getItem(k){return this._d[k]||null;},setItem(k,v){this._d[k]=String(v);}},
  location:{reload:()=>{}},
  fetch:async()=>({ok:true,json:async()=>({sucesso:false,dados:{autenticado:false}})}),
  performance:{now:()=>Date.now()},
  CustomEvent: function(){},
  Event: function(){},
  alert:()=>{}
};
sandbox.globalThis=sandbox;
try{
  vm.runInNewContext(code,sandbox,{filename:'auth.js'});
  console.log(typeof sandbox.window.openAuthModal);
  console.log(typeof sandbox.window._aguiaAuthCheckOpen);
}catch(e){
  console.log('ERR');
  console.log(e.message);
}
