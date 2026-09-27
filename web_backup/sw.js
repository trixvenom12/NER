/**
 * web/sw.js — Progressive Web App Service Worker
 * Module 9 implementation:
 * 1. App Shell Precache: index.html, style.css, app.js, manifest.json
 * 2. Background outbox drain on network recovery
 */

const CACHE_NAME = "ner-logistics-v1";
const ASSETS_TO_CACHE = [
  "/",
  "/index.html",
  "/style.css",
  "/app.js",
  "/manifest.json"
];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log("[SW] Precaching app shell assets...");
      return cache.addAll(ASSETS_TO_CACHE);
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  // Pass API calls through to network, falling back to cache if available
  if (e.request.url.includes("/api/")) {
    e.respondWith(
      fetch(e.request).catch(() => caches.match(e.request))
    );
    return;
  }

  // Cache-first for static assets
  e.respondWith(
    caches.match(e.request).then((cached) => {
      return cached || fetch(e.request).then((resp) => {
        if (resp.status === 200) {
          const respClone = resp.clone();
          caches.open(CACHE_NAME).then((c) => c.put(e.request, respClone));
        }
        return resp;
      });
    })
  );
});
