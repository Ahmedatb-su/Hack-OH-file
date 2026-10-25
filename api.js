const BASE = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');
const demoForced = import.meta.env.VITE_DEMO_MODE === 'true';
const stamp = new Date().toISOString();
const demos = [
 {id:1,name:'Campus Loop North',kind:'bus',subtitle:'CABS · Campus Loop North',capacity:55,count:17,level:'low',updated_at:stamp,route:'CLN'},
 {id:2,name:'Campus Loop South',kind:'bus',subtitle:'CABS · Campus Loop South',capacity:55,count:39,level:'busy',updated_at:stamp,route:'CLS'},
 {id:3,name:'East Residential',kind:'bus',subtitle:'CABS · East Residential',capacity:55,count:29,level:'moderate',updated_at:stamp,route:'ER'},
 {id:4,name:'COTA Route 2',kind:'bus',subtitle:'COTA · High St',capacity:45,count:44,level:'full',updated_at:stamp,route:'2'},
 {id:5,name:'Traditions at Scott',kind:'food_court',subtitle:'Dining · North Campus',capacity:480,count:132,level:'low',updated_at:stamp},
 {id:6,name:'Union Market',kind:'food_court',subtitle:'Dining · Ohio Union',capacity:240,count:167,level:'moderate',updated_at:stamp},
 {id:7,name:'Traditions at Kennedy',kind:'food_court',subtitle:'Dining · South Campus',capacity:350,count:293,level:'busy',updated_at:stamp},
 {id:8,name:'Mirror Lake Eatery',kind:'food_court',subtitle:'Dining · South Campus',capacity:160,count:56,level:'low',updated_at:stamp}
];
function unwrap(payload) { return Array.isArray(payload) ? payload : (payload?.locations || payload?.items || payload?.results || payload?.data || []); }
export function normalizeLocation(loc) {
 const rawKind = String(loc.kind || loc.type || 'bus').toLowerCase();
 const kind = ['food_court','food-court','food court','dining'].includes(rawKind) ? 'food_court' : 'bus';
 const capacity = Number(loc.capacity ?? loc.max_capacity ?? loc.occupancy?.capacity ?? 0);
 const count = Number(loc.count ?? loc.current_count ?? loc.occupancy_count ?? loc.occupancy?.count ?? loc.occupancy?.current_count ?? loc.occupancy?.occupancy ?? 0);
 const percentage = Math.max(0,Math.round(Number(loc.percent_full ?? loc.occupancy?.percent_full ?? loc.percentage ?? loc.occupancy?.percentage ?? (capacity ? 100*count/capacity : 0))));
 const level = String(loc.level ?? loc.occupancy?.level ?? (percentage < 40 ? 'low' : percentage < 70 ? 'moderate' : percentage < 95 ? 'busy' : 'full')).toLowerCase();
 return {...loc,id:loc.id ?? loc.location_id,kind,capacity,count,percentage,level,name:loc.name || loc.label || `Location ${loc.id}`,subtitle:loc.subtitle || (kind==='bus'?'Campus transportation':'Campus dining')};
}
async function fetchJson(path, signal) {
 const res = await fetch(`${BASE}${path}`,{signal});
 if (!res.ok) throw new Error(`API returned ${res.status} for ${path}`);
 return res.json();
}
export async function getLocations(signal) {
 if(demoForced) return {locations:demos.map(normalizeLocation),demo:true};
 try {
  const all = unwrap(await fetchJson('/locations',signal));
  if(!Array.isArray(all)) throw Error('Locations response was not a list');
  const filled = await Promise.all(all.map(async item=>{
   if (item.id==null) return item;
   try {const occupancy = await fetchJson(`/locations/${encodeURIComponent(item.id)}/occupancy`,signal);return {...item,occupancy};}catch {return item;}
  }));
  return {locations:filled.map(normalizeLocation),demo:false};
 } catch(e) {
  if(signal?.aborted) throw e;
  return {locations:demos.map(normalizeLocation),demo:true,error:e.message};
 }
}
export async function getForecast(id,signal) {
 if(demoForced) return demoForecast(id);
 try {
  const data = await fetchJson(`/locations/${encodeURIComponent(id)}/forecast?hours=12&weeks=4`,signal);
  const entries = Array.isArray(data)?data:(data.forecast || data.hours || data.predictions || data.data || []);
  return entries.map((item,i)=>({label: new Date(item.hour || item.timestamp || item.datetime || Date.now()+i*3600000).toLocaleTimeString([],{hour:'numeric'}),value:Number(item.percentage ?? item.percent_full ?? item.expected_percent ?? item.predicted_percent ?? (item.capacity ? 100*(item.expected_count ?? item.predicted_count ?? 0)/item.capacity : item.occupancy ?? item.count ?? 0))})).filter(x=>Number.isFinite(x.value));
 } catch {return demoForecast(id);}
}
function demoForecast(id){return Array.from({length:12},(_,i)=>({label:new Date(Date.now()+i*3600000).toLocaleTimeString([],{hour:'numeric'}),value:Math.min(100,Math.max(8,Math.round(35+25*Math.sin(i*.62+Number(id))+(Number(id)*7)%26)))}));}
export function watchLocation(id,onUpdate){
 if(demoForced)return ()=>{};
 let ws;let reconnect;let stopped=false;
 function connect(){
  const u = new URL(`${BASE || window.location.origin}/locations/${encodeURIComponent(id)}/live`,window.location.origin);
  u.protocol=u.protocol==='https:'?'wss:':'ws:';
  ws=new WebSocket(u);
  ws.onmessage=event=>{try{onUpdate(JSON.parse(event.data));}catch{onUpdate(null);}};
  ws.onclose=()=>{if(!stopped)reconnect=setTimeout(connect,5000);};
  ws.onerror=()=>ws.close();
 }
 connect();
 return ()=>{stopped=true;clearTimeout(reconnect);ws?.close();};
}
