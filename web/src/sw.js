import { precacheAndRoute } from 'workbox-precaching';
import { idbGetAll, idbDeleteMany } from './utils/db';

// Precache the app shell built by Vite
precacheAndRoute(self.__WB_MANIFEST);

// Listen for background sync event for the SOS/Report outbox
self.addEventListener("sync", (e) => {
  if (e.tag === "outbox") e.waitUntil(drainOutbox());
});

const DEVICE_ID = 'tr-4471'; // Fake device ID for demo purposes

async function drainOutbox() {
  const items = await idbGetAll("outbox");
  if (!items.length) return;
  
  try {
    const res = await fetch("/api/sync/batch", {
      method: "POST", 
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ device_id: DEVICE_ID, items })
    });
    
    if (!res.ok) throw new Error("retry later"); // keeps the sync registered
    
    const { results } = await res.json();
    if (results && results.length > 0) {
      await idbDeleteMany("outbox", results.filter(r => r.status === "accepted").map(r => r.client_id));
    }
  } catch (err) {
    console.error("Background sync failed:", err);
    throw err; // retry later
  }
}
