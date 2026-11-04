const C="as-v1",A=["./","index.html","manifest.webmanifest","icon-192.png","icon-512.png","hero.mp4"];
self.addEventListener("install",e=>{e.waitUntil(caches.open(C).then(c=>c.addAll(A)));self.skipWaiting()});
self.addEventListener("activate",e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x!==C).map(x=>caches.delete(x)))));self.clients.claim()});
self.addEventListener("fetch",e=>{const u=new URL(e.request.url);if(e.request.method!=="GET"||u.origin!==location.origin||u.pathname.endsWith("catalog.json")||e.request.headers.has("range"))return;e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request)))});
