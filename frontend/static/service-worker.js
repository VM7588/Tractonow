// TractoNow Service Worker — PWA Offline Support
const CACHE_NAME    = "tractonow-v1";
const OFFLINE_URL   = "/offline";

// Assets to cache on install
const PRECACHE_URLS = [
  "/",
  "/offline",
  "/static/css/style.css",
  "/static/js/main.js",
  "/static/js/booking.js",
  "/static/js/group.js",
  "/static/js/tracking.js",
  "/static/js/rating.js",
  "/static/images/logo.png",
  "/manifest.json"
];

// ── Install ───────────────────────────────────────────────────────────────────
self.addEventListener("install", event => {
  console.log("[SW] Installing...");
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      console.log("[SW] Pre-caching assets");
      return cache.addAll(PRECACHE_URLS);
    }).then(() => self.skipWaiting())
  );
});

// ── Activate ──────────────────────────────────────────────────────────────────
self.addEventListener("activate", event => {
  console.log("[SW] Activating...");
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.filter(k => k !== CACHE_NAME).map(k => {
          console.log(`[SW] Deleting old cache: ${k}`);
          return caches.delete(k);
        })
      )
    ).then(() => self.clients.claim())
  );
});

// ── Fetch ─────────────────────────────────────────────────────────────────────
self.addEventListener("fetch", event => {
  const { request } = event;
  const url = new URL(request.url);

  // API calls: network first, no caching
  if (url.pathname.startsWith("/api/")) {
    event.respondWith(networkFirst(request));
    return;
  }

  // Navigation requests: network first, fallback to offline page
  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request).catch(() => caches.match(OFFLINE_URL))
    );
    return;
  }

  // Static assets: cache first
  event.respondWith(cacheFirst(request));
});

// ── Strategies ────────────────────────────────────────────────────────────────
async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    return new Response("Offline", { status: 503 });
  }
}

async function networkFirst(request) {
  try {
    const response = await fetch(request);
    return response;
  } catch {
    // For API calls while offline — return a clean error JSON
    return new Response(
      JSON.stringify({ success: false, message: "You are offline. Please check your connection." }),
      { status: 503, headers: { "Content-Type": "application/json" } }
    );
  }
}

// ── Background Sync — queue offline booking requests ─────────────────────────
self.addEventListener("sync", event => {
  if (event.tag === "sync-bookings") {
    event.waitUntil(syncOfflineBookings());
  }
});

async function syncOfflineBookings() {
  const db      = await openIndexedDB();
  const pending = await getAll(db, "offline_bookings");
  for (const booking of pending) {
    try {
      const res = await fetch("/api/bookings/", {
        method:  "POST",
        headers: { "Content-Type": "application/json",
                   "Authorization": `Bearer ${booking.token}` },
        body:    JSON.stringify(booking.data)
      });
      if (res.ok) await deleteRecord(db, "offline_bookings", booking.id);
    } catch (e) {
      console.warn("[SW] Sync failed, will retry:", e);
    }
  }
}

// ── Minimal IndexedDB helpers ─────────────────────────────────────────────────
function openIndexedDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open("tractonow_offline", 1);
    req.onupgradeneeded = e => {
      e.target.result.createObjectStore("offline_bookings",
        { keyPath: "id", autoIncrement: true });
    };
    req.onsuccess  = e => resolve(e.target.result);
    req.onerror    = e => reject(e);
  });
}

function getAll(db, store) {
  return new Promise((resolve, reject) => {
    const tx  = db.transaction(store, "readonly");
    const req = tx.objectStore(store).getAll();
    req.onsuccess = e => resolve(e.target.result);
    req.onerror   = e => reject(e);
  });
}

function deleteRecord(db, store, id) {
  return new Promise((resolve, reject) => {
    const tx  = db.transaction(store, "readwrite");
    const req = tx.objectStore(store).delete(id);
    req.onsuccess = () => resolve();
    req.onerror   = e => reject(e);
  });
}