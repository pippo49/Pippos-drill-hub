// Minimal DOM/window/localStorage stub so the trainer JS runs under Node for validation.
const store={};
global.localStorage={getItem:k=>k in store?store[k]:null,setItem:(k,v)=>{store[k]=String(v)},removeItem:k=>{delete store[k]}};
const el=()=>({style:{},classList:{add(){},remove(){},toggle(){},contains(){return false}},addEventListener(){},appendChild(){},setAttribute(){},removeAttribute(){},focus(){},querySelector(){return el()},querySelectorAll(){return []},innerHTML:'',textContent:'',value:'',insertAdjacentHTML(){},remove(){},dataset:{}});
global.document={getElementById:()=>el(),querySelector:()=>el(),querySelectorAll:()=>[],createElement:()=>el(),addEventListener(){},body:el()};
global.window={addEventListener(){},matchMedia:()=>({matches:false,addEventListener(){}}),location:{href:''}};
global.navigator={serviceWorker:{register(){return{then(){return{catch(){}}}}}}};
