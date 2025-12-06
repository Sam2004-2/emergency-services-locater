/**
 * Service Worker for Emergency Services Locator PWA
 * 
 * Implements:
 * - App shell caching (HTML, CSS, JS)
 * - Map tile caching with cache-first strategy
 * - API response caching for offline viewing
 * - Background sync for offline facility submissions
 * 
 * @version 1.0.0
 */

const CACHE_VERSION = 'v1.2.0';
const STATIC_CACHE = `es-locator-static-${CACHE_VERSION}`;
const TILE_CACHE = `es-locator-tiles-${CACHE_VERSION}`;
const API_CACHE = `es-locator-api-${CACHE_VERSION}`;

// Static assets to cache on install
const STATIC_ASSETS = [
  '/',
  '/dashboard/',
  '/static/frontend/css/map.css',
  '/static/frontend/css/dashboard.css',
  '/static/frontend/js/map.js',
  '/static/frontend/js/api.js',
  '/static/frontend/js/icons.js',
  '/static/frontend/js/dashboard/dashboard.js',
  '/static/frontend/js/dashboard/dashboard-api.js',
  '/static/frontend/js/dashboard/dashboard-state.js',
  '/static/frontend/js/dashboard/dashboard-map.js',
  '/static/frontend/js/dashboard/dashboard-list.js',
  '/static/frontend/js/dashboard/dashboard-forms.js',
  '/static/frontend/js/dashboard/dashboard-polling.js',
  '/static/frontend/manifest.json',
  // External CDN resources
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js',
  'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',
  'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js',
  'https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css',
  'https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css',
  'https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js',
  'https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.css',
  'https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.js',
];

// Tile URL patterns to cache
const TILE_PATTERNS = [
  /^https:\/\/[a-c]\.tile\.openstreetmap\.org\//,
];

// API endpoints to cache
const API_PATTERNS = [
  /\/api\/counties\//,
  /\/api\/facilities\//,
  /\/api\/incidents\//,
  /\/api\/vehicles\//,
  /\/api\/dispatches\//,
  /\/api\/auth\/me\//,
];

// Maximum items per cache
const MAX_TILE_CACHE_ITEMS = 500;
const MAX_API_CACHE_ITEMS = 50;
const TILE_CACHE_MAX_AGE = 7 * 24 * 60 * 60 * 1000; // 7 days

/**
 * Install event - cache static assets
 */
self.addEventListener('install', (event) => {
  console.log('[SW] Installing service worker...');
  
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => {
        console.log('[SW] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => self.skipWaiting())
      .catch((error) => {
        console.error('[SW] Failed to cache static assets:', error);
      })
  );
});

/**
 * Activate event - clean up old caches
 */
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating service worker...');
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((name) => {
              // Delete caches that don't match current version
              return name.startsWith('es-locator-') && 
                     name !== STATIC_CACHE && 
                     name !== TILE_CACHE && 
                     name !== API_CACHE;
            })
            .map((name) => {
              console.log('[SW] Deleting old cache:', name);
              return caches.delete(name);
            })
        );
      })
      .then(() => self.clients.claim())
  );
});

/**
 * Fetch event - serve from cache with network fallback
 */
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }
  
  // Handle tile requests with cache-first strategy
  if (isTileRequest(url.href)) {
    event.respondWith(handleTileRequest(request));
    return;
  }
  
  // Handle API requests with network-first strategy
  if (isAPIRequest(url.pathname)) {
    event.respondWith(handleAPIRequest(request));
    return;
  }
  
  // Handle static assets with cache-first strategy
  event.respondWith(handleStaticRequest(request));
});

/**
 * Check if URL is a map tile request
 */
function isTileRequest(url) {
  return TILE_PATTERNS.some((pattern) => pattern.test(url));
}

/**
 * Check if URL is an API request
 */
function isAPIRequest(pathname) {
  return API_PATTERNS.some((pattern) => pattern.test(pathname));
}

/**
 * Handle tile requests - cache-first with network fallback
 */
async function handleTileRequest(request) {
  const cache = await caches.open(TILE_CACHE);
  const cached = await cache.match(request);
  
  if (cached) {
    // Return cached tile, but refresh in background
    refreshTileInBackground(request, cache);
    return cached;
  }
  
  try {
    const response = await fetch(request);
    if (response.ok) {
      // Clone and cache the response
      const clonedResponse = response.clone();
      cache.put(request, clonedResponse);
      
      // Trim cache if needed
      trimCache(TILE_CACHE, MAX_TILE_CACHE_ITEMS);
    }
    return response;
  } catch (error) {
    console.error('[SW] Tile fetch failed:', error);
    // Return a placeholder tile or offline image
    return new Response('', { status: 503, statusText: 'Tile unavailable offline' });
  }
}

/**
 * Refresh tile in background without blocking
 */
async function refreshTileInBackground(request, cache) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      cache.put(request, response);
    }
  } catch (error) {
    // Ignore background refresh errors
  }
}

/**
 * Handle API requests - network-first with cache fallback
 */
async function handleAPIRequest(request) {
  const cache = await caches.open(API_CACHE);
  
  try {
    const response = await fetch(request);
    if (response.ok) {
      // Cache successful responses
      const clonedResponse = response.clone();
      cache.put(request, clonedResponse);
      trimCache(API_CACHE, MAX_API_CACHE_ITEMS);
    }
    return response;
  } catch (error) {
    console.log('[SW] Network failed, falling back to cache:', request.url);
    const cached = await cache.match(request);
    
    if (cached) {
      return cached;
    }
    
    // Return offline-friendly error response
    return new Response(
      JSON.stringify({ 
        error: 'offline', 
        message: 'You are offline. This data is not available.' 
      }),
      { 
        status: 503, 
        headers: { 'Content-Type': 'application/json' } 
      }
    );
  }
}

/**
 * Handle static asset requests - cache-first
 */
async function handleStaticRequest(request) {
  const cached = await caches.match(request);
  
  if (cached) {
    return cached;
  }
  
  try {
    const response = await fetch(request);
    
    // Cache successful HTML/CSS/JS responses
    if (response.ok && shouldCacheStatic(request)) {
      const cache = await caches.open(STATIC_CACHE);
      cache.put(request, response.clone());
    }
    
    return response;
  } catch (error) {
    console.error('[SW] Static fetch failed:', error);
    
    // Return offline page for navigation requests
    if (request.mode === 'navigate') {
      return caches.match('/');
    }
    
    return new Response('Offline', { status: 503 });
  }
}

/**
 * Check if request should be cached as static asset
 */
function shouldCacheStatic(request) {
  const url = new URL(request.url);
  return url.pathname.startsWith('/static/') || 
         url.pathname === '/' ||
         url.pathname.endsWith('.html');
}

/**
 * Trim cache to maximum size
 */
async function trimCache(cacheName, maxItems) {
  const cache = await caches.open(cacheName);
  const keys = await cache.keys();
  
  if (keys.length > maxItems) {
    // Delete oldest entries (first in, first out)
    const deleteCount = keys.length - maxItems;
    for (let i = 0; i < deleteCount; i++) {
      await cache.delete(keys[i]);
    }
  }
}

/**
 * Background sync for offline facility submissions
 */
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-facilities') {
    event.waitUntil(syncOfflineFacilities());
  }
});

/**
 * Sync queued facility submissions
 */
async function syncOfflineFacilities() {
  try {
    // Get pending submissions from IndexedDB
    const db = await openDB();
    const tx = db.transaction('pending-facilities', 'readonly');
    const store = tx.objectStore('pending-facilities');
    const pending = await store.getAll();
    
    for (const facility of pending) {
      try {
        const response = await fetch('/api/facilities/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(facility.data),
        });
        
        if (response.ok) {
          // Remove from pending queue
          const deleteTx = db.transaction('pending-facilities', 'readwrite');
          const deleteStore = deleteTx.objectStore('pending-facilities');
          await deleteStore.delete(facility.id);
        }
      } catch (error) {
        console.error('[SW] Failed to sync facility:', error);
      }
    }
  } catch (error) {
    console.error('[SW] Sync failed:', error);
  }
}

/**
 * Open IndexedDB for offline storage
 */
function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('es-locator-offline', 1);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains('pending-facilities')) {
        db.createObjectStore('pending-facilities', { keyPath: 'id', autoIncrement: true });
      }
    };
  });
}

/**
 * Push notification handler
 */
self.addEventListener('push', (event) => {
  if (!event.data) return;
  
  const data = event.data.json();
  
  event.waitUntil(
    self.registration.showNotification(data.title || 'ES Locator', {
      body: data.body || 'New update available',
      icon: '/static/frontend/icons/icon-192x192.png',
      badge: '/static/frontend/icons/badge-72x72.png',
      tag: data.tag || 'es-locator-notification',
      data: data.url || '/',
    })
  );
});

/**
 * Notification click handler
 */
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  event.waitUntil(
    clients.openWindow(event.notification.data || '/')
  );
});

console.log('[SW] Service worker loaded');
