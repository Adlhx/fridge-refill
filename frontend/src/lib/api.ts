const BASE=import.meta.env.VITE_API_URL||'/api';
export const token={get:()=>sessionStorage.getItem('access'),set:(v:string)=>sessionStorage.setItem('access',v),clear:()=>sessionStorage.clear()};
export async function api<T>(path:string,init:RequestInit={}):Promise<T>{const res=await fetch(`${BASE}${path}`,{...init,headers:{'Content-Type':'application/json',...(token.get()?{Authorization:`Bearer ${token.get()}`}:{}) ,...init.headers}});if(!res.ok){let detail;try{detail=await res.json()}catch{detail={detail:res.statusText}}throw Object.assign(new Error(detail.detail||'Request failed'),{status:res.status,data:detail})}return res.status===204?undefined as T:res.json()}
export const getResults=<T>(value:{results:T[]}|T[])=>Array.isArray(value)?value:value.results;
type Pending={path:string;body:unknown}; const KEY='fridge-refill-pending';
export function queueChange(change:Pending){const q:Pending[]=JSON.parse(localStorage.getItem(KEY)||'[]');q.push(change);localStorage.setItem(KEY,JSON.stringify(q))}
export async function flushQueue(){const q:Pending[]=JSON.parse(localStorage.getItem(KEY)||'[]'),left:Pending[]=[];for(const x of q)try{await api(x.path,{method:'PATCH',body:JSON.stringify(x.body)})}catch{left.push(x)}localStorage.setItem(KEY,JSON.stringify(left));return left.length}
window.addEventListener('online',()=>void flushQueue());
