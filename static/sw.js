// ============================================================
// CLAYVILLE GARDENS SDA CHURCH — SERVICE WORKER v2
// Served from root /sw.js so it can control the full site
// ============================================================

const CACHE_NAME = 'clayville-sda-v2';
const OFFLINE_URL = '/offline';

// All core assets to pre-cache on first install
const PRECACHE = [
  '/',
  '/about',
  '/services',
  '/events',
  '/sermons',
  '/gallery',
  '/contact',
  '/offline',
  '/static/css/style.css',
  '/static/js/main.js',
  '/static/logo.png',
  '/static/favicon.png',
  '/static/hero1.jpg',
  '/static/hero2.jpg',
  '/static/hero3.jpg',
  '/static/about.jpg',
];

// ── INSTALL: cache all core assets ──────────────────────────
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(PRECACHE))
      .then(() => self.skipWaiting())
  );
});

// ── ACTIVATE: delete old cache versions ─────────────────────
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

// ── FETCH: smart caching strategy ───────────────────────────
self.addEventListener('fetch', event => {
  const req = event.request;
  const url = new URL(req.url);

  // Only handle GET requests from our own origin
  if (req.method !== 'GET' || url.origin !== location.origin) return;

  // Never intercept admin pages — admin always needs live server
  if (url.pathname.startsWith('/admin')) return;

  const isNavigation = req.mode === 'navigate';

  if (isNavigation) {
    // NETWORK FIRST for HTML pages:
    // Try to get a fresh page; if offline, serve cached version; last resort = offline page
    event.respondWith(
      fetch(req)
        .then(res => {
          // Cache the fresh response for next time
          const copy = res.clone();
          caches.open(CACHE_NAME).then(c => c.put(req, copy));
          return res;
        })
        .catch(() =>
          caches.match(req)
            .then(cached => cached || caches.match(OFFLINE_URL))
        )
    );
  } else {
    // CACHE FIRST for static assets (CSS, JS, images, fonts):
    // Serve from cache instantly; fetch & cache if not found
    event.respondWith(
      caches.match(req)
        .then(cached => {
          if (cached) return cached;
          return fetch(req)
            .then(res => {
              if (res && res.ok) {
                const copy = res.clone();
                caches.open(CACHE_NAME).then(c => c.put(req, copy));
              }
              return res;
            })
            .catch(() => new Response('Not found', { status: 404 }));
        })
    );
  }
});
