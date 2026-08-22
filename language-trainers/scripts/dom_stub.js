// Minimal DOM/window/localStorage stub so the trainer JS runs under Node for validation.
const store={};
global.localStorage={getItem:k=>k in store?store[k]:null,setItem:(k,v)=>{store[k]=String(v)},removeItem:k=>{delete store[k]}};
// Children, attributes and click listeners are RECORDED rather than discarded,
// so a probe can render a control and then press it. They used to be no-ops,
// which meant nothing could test what a button actually does when clicked --
// how the hardest-words round button stayed one-way without any check noticing.
// appendChild/removeChild maintain firstChild honestly: `while (row.firstChild)
// row.removeChild(row.firstChild)` is real code in the apps and must terminate.
const el=()=>({style:{},classList:{add(){},remove(){},toggle(){},contains(){return false}},
  children:[],attrs:{},listeners:{},firstChild:null,
  addEventListener(t,f){(this.listeners[t]=this.listeners[t]||[]).push(f)},
  appendChild(c){this.children.push(c);this.firstChild=this.children[0];return c},
  removeChild(c){const i=this.children.indexOf(c);if(i>=0)this.children.splice(i,1);
    this.firstChild=this.children[0]||null;return c},
  click(){(this.listeners.click||[]).forEach(f=>f.call(this,{type:'click',preventDefault(){},stopPropagation(){}}))},
  setAttribute(k,v){this.attrs[k]=String(v)},getAttribute(k){return k in this.attrs?this.attrs[k]:null},
  removeAttribute(k){delete this.attrs[k]},
  focus(){},querySelector(){return el()},querySelectorAll(){return []},
  innerHTML:'',textContent:'',value:'',insertAdjacentHTML(){},remove(){},dataset:{}});
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
