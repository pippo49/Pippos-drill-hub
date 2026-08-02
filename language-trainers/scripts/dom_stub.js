// Minimal DOM/window/localStorage stub so the trainer JS runs under Node for validation.
const store={};
global.localStorage={getItem:k=>k in store?store[k]:null,setItem:(k,v)=>{store[k]=String(v)},removeItem:k=>{delete store[k]}};
const el=()=>({style:{},classList:{add(){},remove(){},toggle(){},contains(){return false}},addEventListener(){},appendChild(){},setAttribute(){},removeAttribute(){},focus(){},querySelector(){return el()},querySelectorAll(){return []},innerHTML:'',textContent:'',value:'',insertAdjacentHTML(){},remove(){},dataset:{}});
// createTextNode was missing, so any probe that rendered a multiple-choice
// card crashed inside buildChoiceSection. A text node needs the same shape as
// an element here because the app appends it into one.
// getElementById is memoised by id: it used to hand back a fresh object every
// call, so a probe could never read back what the app had just written into an
// element (e.g. the header's selection-count text).
const byIdCache={};
global.document={getElementById:id=>byIdCache[id]||(byIdCache[id]=el()),querySelector:()=>el(),querySelectorAll:()=>[],createElement:()=>el(),createTextNode:t=>{const n=el();n.textContent=String(t);return n;},addEventListener(){},body:el()};
global.window={addEventListener(){},matchMedia:()=>({matches:false,addEventListener(){}}),location:{href:''}};
global.navigator={serviceWorker:{register(){return{then(){return{catch(){}}}}}}};
