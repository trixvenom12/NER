import { openDB } from 'idb';

const DB_NAME = 'ner-logistics-db';
const DB_VERSION = 1;

export async function initDB() {
  return openDB(DB_NAME, DB_VERSION, {
    upgrade(db) {
      if (!db.objectStoreNames.contains('outbox')) {
        db.createObjectStore('outbox', { keyPath: 'client_id' });
      }
      if (!db.objectStoreNames.contains('map_data')) {
        db.createObjectStore('map_data');
      }
    },
  });
}

export async function idbGetAll(storeName) {
  const db = await initDB();
  return db.getAll(storeName);
}

export async function idbPut(storeName, val, key) {
  const db = await initDB();
  return db.put(storeName, val, key);
}

export async function idbGet(storeName, key) {
  const db = await initDB();
  return db.get(storeName, key);
}

export async function idbDeleteMany(storeName, keys) {
  const db = await initDB();
  const tx = db.transaction(storeName, 'readwrite');
  keys.forEach((key) => {
    tx.store.delete(key);
  });
  await tx.done;
}
