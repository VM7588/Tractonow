/* ══════════════════════════════════════════
   pwa.js  —  Offline booking queue (IndexedDB)
   Saves bookings when offline, syncs on reconnect
══════════════════════════════════════════ */

const PWA = {
  dbName:    "tractonow_offline",
  storeName: "offline_bookings",
  db:        null,

  // ── Open IndexedDB ──────────────────────────────────────────────────────────
  async openDB() {
    if (this.db) return this.db;
    return new Promise((resolve, reject) => {
      const req = indexedDB.open(this.dbName, 1);
      req.onupgradeneeded = (e) => {
        e.target.result.createObjectStore(this.storeName,
          { keyPath: "id", autoIncrement: true });
      };
      req.onsuccess  = (e) => { this.db = e.target.result; resolve(this.db); };
      req.onerror    = (e) => reject(e.target.error);
    });
  },

  // ── Save booking to offline queue ───────────────────────────────────────────
  async queueBooking(bookingData, token) {
    const db  = await this.openDB();
    const tx  = db.transaction(this.storeName, "readwrite");
    const store = tx.objectStore(this.storeName);
    store.add({ data: bookingData, token, queued_at: new Date().toISOString() });
    return new Promise((res, rej) => {
      tx.oncomplete = () => res(true);
      tx.onerror    = () => rej(tx.error);
    });
  },

  // ── Get all queued bookings ─────────────────────────────────────────────────
  async getQueued() {
    const db    = await this.openDB();
    const tx    = db.transaction(this.storeName, "readonly");
    const store = tx.objectStore(this.storeName);
    return new Promise((res, rej) => {
      const req = store.getAll();
      req.onsuccess = () => res(req.result);
      req.onerror   = () => rej(req.error);
    });
  },

  // ── Delete a synced record ──────────────────────────────────────────────────
  async deleteQueued(id) {
    const db    = await this.openDB();
    const tx    = db.transaction(this.storeName, "readwrite");
    const store = tx.objectStore(this.storeName);
    store.delete(id);
    return new Promise((res, rej) => {
      tx.oncomplete = () => res(true);
      tx.onerror    = () => rej(tx.error);
    });
  },

  // ── Sync queued bookings when back online ───────────────────────────────────
  async syncQueue() {
    const pending = await this.getQueued();
    if (!pending.length) return;

    console.log(`[PWA] Syncing ${pending.length} queued bookings...`);
    let synced = 0;

    for (const item of pending) {
      try {
        const res = await fetch("/api/bookings/", {
          method:  "POST",
          headers: {
            "Content-Type":  "application/json",
            "Authorization": `Bearer ${item.token}`
          },
          body: JSON.stringify(item.data)
        });
        const data = await res.json();
        if (data.success) {
          await this.deleteQueued(item.id);
          synced++;
        }
      } catch (err) {
        console.warn("[PWA] Sync item failed:", err);
      }
    }

    if (synced > 0) {
      Toast.success(`✅ ${synced} offline booking(s) synced successfully!`);
    }
    return synced;
  },

  // ── Show offline banner ─────────────────────────────────────────────────────
  showOfflineBanner() {
    let banner = document.getElementById("offline-banner");
    if (!banner) {
      banner = document.createElement("div");
      banner.id = "offline-banner";
      banner.style.cssText = `
        position: fixed; top: 60px; left: 0; right: 0; z-index: 9997;
        background: #f59e0b; color: #fff; text-align: center;
        padding: .6rem 1rem; font-size: .9rem; font-weight: 600;
      `;
      banner.textContent = "📡 You are offline. Bookings will be saved and sent when reconnected.";
      document.body.appendChild(banner);
    }
    banner.style.display = "block";
  },

  hideOfflineBanner() {
    const banner = document.getElementById("offline-banner");
    if (banner) banner.style.display = "none";
  },

  // ── Count badge for queued items ────────────────────────────────────────────
  async updateQueueBadge() {
    const pending = await this.getQueued();
    const badge   = document.getElementById("offline-queue-count");
    if (badge) {
      badge.textContent = pending.length > 0 ? `(${pending.length} pending)` : "";
      badge.style.display = pending.length > 0 ? "inline" : "none";
    }
  },

  // ── Init all listeners ──────────────────────────────────────────────────────
  init() {
    window.addEventListener("offline", () => {
      this.showOfflineBanner();
      Toast.warning("You are offline.");
    });

    window.addEventListener("online", async () => {
      this.hideOfflineBanner();
      Toast.success("Back online! Syncing...");
      await this.syncQueue();
      this.updateQueueBadge();

      // Request background sync via SW if available
      if ("serviceWorker" in navigator && "SyncManager" in window) {
        const reg = await navigator.serviceWorker.ready;
        reg.sync.register("sync-bookings").catch(console.warn);
      }
    });

    // Check initial state
    if (!navigator.onLine) this.showOfflineBanner();
    this.updateQueueBadge();
  }
};

// Auto-init
document.addEventListener("DOMContentLoaded", () => PWA.init());
