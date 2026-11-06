const C="as-v20",A=["./","index.html","desktop.html","media.html","basketball.html","manifest.webmanifest","icon-192.png","icon-512.png","apple-touch-icon.png","favicon.ico","hero.mp4","photo.jpg","Bg/frame-halloween.webp","Bg/frame-urban.webp"];
self.addEventListener("install",e=>{e.waitUntil(caches.open(C).then(c=>Promise.all(A.map(a=>c.add(a).catch(()=>{})))));self.skipWaiting()});
self.addEventListener("activate",e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x!==C).map(x=>caches.delete(x)))));self.clients.claim()});
self.addEventListener("fetch",e=>{const r=e.request,u=new URL(r.url);if(r.method!=="GET"||u.origin!==location.origin||r.headers.has("range")||/\.(mp3|json)$/i.test(u.pathname))return;
e.respondWith(fetch(r).then(x=>{if(x.ok){const y=x.clone();caches.open(C).then(c=>c.put(r,y))}return x}).catch(()=>caches.match(r)))});
