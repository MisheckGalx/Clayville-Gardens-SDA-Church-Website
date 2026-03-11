// ================================================================
// CLAYVILLE GARDENS SDA CHURCH — SERVICE WORKER v2
// Full offline support · Cache-first for assets · Network-first for pages
// ================================================================

const CACHE_NAME = 'clayville-sda-v2';
const OFFLINE_URL = '/offline';

// Pages and assets to pre-cache on install
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
  '/static/manifest.json',
  '/static/logo.png',
  '/static/favicon.png',
  '/static/hero1.jpg',
  '/static/hero2.jpg',
  '/static/hero3.jpg',
  '/static/about.jpg',
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-512x512.png'
];

// ── INSTALL: cache all core assets ────────────────────────────────
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(PRECACHE))
      .then(() => self.skipWaiting())
  );
});

// ── ACTIVATE: delete old caches ───────────────────────────────────
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

// ── FETCH: smart caching strategy ─────────────────────────────────
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Only handle GET requests from same origin
  if (request.method !== 'GET' || url.origin !== location.origin) return;

  // Never intercept admin routes — they need live data
  if (url.pathname.startsWith('/admin')) return;

  const isNavigate = request.mode === 'navigate';

  if (isNavigate) {
    // HTML pages: Network-first → cached page → offline fallback
    event.respondWith(
      fetch(request)
        .then(res => {
          const copy = res.clone();
          caches.open(CACHE_NAME).then(c => c.put(request, copy));
          return res;
        })
        .catch(() =>
          caches.match(request)
            .then(cached => cached || caches.match(OFFLINE_URL))
        )
    );
  } else {
    // Static assets: Cache-first → network → silent fail
    event.respondWith(
      caches.match(request)
        .then(cached => {
          if (cached) return cached;
          return fetch(request).then(res => {
            if (res && res.ok) {
              const copy = res.clone();
              caches.open(CACHE_NAME).then(c => c.put(request, copy));
            }
            return res;
          });
        })
        .catch(() => new Response('', { status: 408 }))
    );
  }
});
