/* tracking.js — Real GPS */
let _map=null,_marker=null,_path=null,_tInt=null,_gInt=null,_bkId=null;

document.addEventListener("DOMContentLoaded",()=>{
  redirectIfNotLoggedIn();
  _bkId=new URLSearchParams(window.location.search).get("booking_id");
  if(!_bkId){showErr("No booking ID.");return;}
  initMap();fetchLoc();fetchHist();_tInt=setInterval(fetchLoc,6000);initGps();
});

function initMap(){
  const el=document.getElementById("map-container");
  if(!el||typeof L==="undefined")return;
  _map=L.map("map-container").setView([17.58,80.64],13);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",{attribution:"© OpenStreetMap",maxZoom:18}).addTo(_map);
  const icon=L.divIcon({html:`<div style="font-size:2rem;filter:drop-shadow(0 2px 4px rgba(0,0,0,.4));">🚜</div>`,className:"",iconSize:[40,40],iconAnchor:[20,20]});
  _marker=L.marker([17.58,80.64],{icon}).addTo(_map).bindPopup("Equipment location");
  _path=L.polyline([],{color:"#16a34a",weight:4,opacity:.7}).addTo(_map);
}

async function fetchLoc(){
  const res=await Api.get(`/tracking/${_bkId}`);
  if(!res?.success)return;
  const loc=res.location;
  document.getElementById("sim-badge").style.display =loc.simulated?"block":"none";
  document.getElementById("real-badge").style.display=loc.simulated?"none":"block";
  updateMarker(loc.lat,loc.lng);updateETA(res.eta);
  document.getElementById("spd").textContent=`${loc.speed_kmh||0} km/h`;
  document.getElementById("upd").textContent=new Date(loc.timestamp).toLocaleTimeString("en-IN");
}

async function fetchHist(){
  const res=await Api.get(`/tracking/${_bkId}/history`);
  if(!res?.success||!res.path.length)return;
  if(_path)_path.setLatLngs(res.path.map(p=>[p.lat,p.lng]));
}

function updateMarker(lat,lng){
  if(!_marker||!_map)return;
  _marker.setLatLng([lat,lng]);_map.panTo([lat,lng],{animate:true,duration:1});
  if(_path){const p=_path.getLatLngs();p.push([lat,lng]);_path.setLatLngs(p);}
}

function updateETA(eta){
  const el=document.getElementById("eta");if(!el||!eta)return;
  el.textContent=eta.eta_minutes<2?"Arrived 🎉":`~${eta.eta_minutes} min (${eta.distance_km} km)`;
}

function showErr(m){const el=document.getElementById("trk-err");if(el){el.textContent=m;el.style.display="block";}}

// Owner real GPS
function initGps(){
  const btn=document.getElementById("gps-start");const stop=document.getElementById("gps-stop");
  if(!btn||!Auth.getUser()||Auth.getUser().role!=="owner")return;
  btn.style.display="inline-flex";stop.style.display="none";
  btn.onclick=()=>{
    if(!navigator.geolocation){Toast.warning("Geolocation not supported.");return;}
    sendGps();
    _gInt=setInterval(sendGps,5000);
    btn.style.display="none";stop.style.display="inline-flex";
    Toast.success("📡 Live GPS sharing started!");
  };
  stop.onclick=()=>{
    if(_gInt){clearInterval(_gInt);_gInt=null;}
    btn.style.display="inline-flex";stop.style.display="none";
    Toast.warning("GPS sharing stopped.");
  };
}

function sendGps(){
  navigator.geolocation.getCurrentPosition(async pos=>{
    await Api.post("/tracking/update",{
      booking_id:_bkId,lat:pos.coords.latitude,lng:pos.coords.longitude,
      speed_kmh:pos.coords.speed?Math.round(pos.coords.speed*3.6):0,
      heading:pos.coords.heading||0
    });
  },err=>Toast.error("GPS: "+err.message),{enableHighAccuracy:true,timeout:8000});
}

window.addEventListener("beforeunload",()=>{
  if(_tInt)clearInterval(_tInt);if(_gInt)clearInterval(_gInt);
});
