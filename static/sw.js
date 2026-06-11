const CACHE = 'tradecards-v1';
const PRECACHE = ['/', '/api/cards'];

// On install: cache the shell + card data
self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(PRECACHE))
      .then(() => self.skipWaiting())
  );
});

// On activate: clean up old caches
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

// Fetch strategy:
// - /api/cards  → network first, fall back to cache (keeps cards fresh)
// - /image/*    → cache first, then network (images rarely change)
// - everything else → cache first, fall back to network
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);

  if (url.pathname === '/api/cards') {
    // Network first — update cache in background
    e.respondWith(
      fetch(e.request)
        .then(res => {
          const clone = res.clone();
          caches.open(CACHE).then(c => c.put(e.request, clone));
          return res;
        })
        .catch(() => caches.match(e.request))
    );
    return;
  }

  if (url.pathname.startsWith('/image/')) {
    // Cache first — images don't change
    e.respondWith(
      caches.match(e.request).then(cached => {
        if (cached) return cached;
        return fetch(e.request).then(res => {
          const clone = res.clone();
          caches.open(CACHE).then(c => c.put(e.request, clone));
          return res;
        });
      })
    );
    return;
  }

  // Default: cache first
  e.respondWith(
    caches.match(e.request).then(cached => cached || fetch(e.request))
  );
});
