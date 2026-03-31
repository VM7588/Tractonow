/* main.js — TractoNow v2.1 — All fixes */
const API_BASE = "/api";

// ── Auth ──────────────────────────────────────────────────────────────────────
const Auth = {
  getToken:  ()       => localStorage.getItem("tractonow_token"),
  getUser:   ()       => JSON.parse(localStorage.getItem("tractonow_user") || "null"),
  setSession:(t, u)   => {
    localStorage.setItem("tractonow_token", t);
    localStorage.setItem("tractonow_user", JSON.stringify(u));
    // Save language from user profile so it persists
    if (u.language) localStorage.setItem("tractonow_lang", u.language);
  },
  clear: () => {
    localStorage.removeItem("tractonow_token");
    localStorage.removeItem("tractonow_user");
  },
  isLoggedIn: () => !!localStorage.getItem("tractonow_token"),
};

// ── API client ────────────────────────────────────────────────────────────────
const Api = {
  async request(method, path, body = null) {
    const h = { "Content-Type": "application/json" };
    const t = Auth.getToken();
    if (t) h["Authorization"] = "Bearer " + t;
    const o = { method, headers: h };
    if (body) o.body = JSON.stringify(body);
    try {
      const r = await fetch(API_BASE + path, o);
      const d = await r.json();
      if (r.status === 401) { Auth.clear(); window.location.href = "/login"; return; }
      return d;
    } catch(e) {
      return { success: false, message: "Network error. You may be offline." };
    }
  },
  get:    p      => Api.request("GET",    p),
  post:   (p, b) => Api.request("POST",   p, b),
  put:    (p, b) => Api.request("PUT",    p, b),
  delete: p      => Api.request("DELETE", p),
};

// ── Toast ─────────────────────────────────────────────────────────────────────
const Toast = {
  _c: null,
  _init() {
    if (!this._c) {
      this._c = document.createElement("div");
      this._c.id = "toast-container";
      document.body.appendChild(this._c);
    }
  },
  show(msg, type = "success", dur = 3500) {
    this._init();
    const t = document.createElement("div");
    t.className   = `toast ${type}`;
    t.textContent = msg;
    this._c.appendChild(t);
    setTimeout(() => {
      t.style.opacity = "0";
      t.style.transition = "opacity .3s";
      setTimeout(() => t.remove(), 300);
    }, dur);
  },
  success: m => Toast.show(m, "success"),
  error:   m => Toast.show(m, "error"),
  warning: m => Toast.show(m, "warning"),
};

// ── Language / Translations — delegates to base.html global translator ──────────
const Lang = {
  // Priority: user saved pref > user profile language > "en"
  current: localStorage.getItem("tractonow_lang")
        || JSON.parse(localStorage.getItem("tractonow_user") || "null")?.language
        || "en",
  strings: {},

  async load(lang) {
    this.current = lang;
    // Delegate to base.html global changeLang (works everywhere)
    if (typeof changeLang === "function") {
      changeLang(lang);
    } else {
      localStorage.setItem("tractonow_lang", lang);
    }
  },

  t: k => Lang.strings[k] || k,

  apply() {
    if (typeof applyPageTranslations === "function") {
      applyPageTranslations(this.current);
    }
  },

  // Returns BCP-47 tag for Web Speech API — uses CURRENT selection
  getSpeechLang() {
    return { en: "en-IN", te: "te-IN", hi: "hi-IN" }[this.current] || "en-IN";
  },

  init() {
    // base.html handles lang buttons directly via onclick="changeLang()"
    // Just sync current state
    document.querySelectorAll(".lang-btn").forEach(btn =>
      btn.classList.toggle("active", btn.dataset.lang === this.current));
  }
};

// ── Voice — always uses currently selected language ───────────────────────────
const Voice = {
  _r: null,
  init(btnId, targetId) {
    const btn = document.getElementById(btnId);
    const tgt = document.getElementById(targetId);
    if (!btn || !tgt) return;
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { btn.style.display = "none"; return; }

    btn.addEventListener("click", () => {
      if (btn.classList.contains("recording")) {
        this._r?.stop();
        btn.classList.remove("recording");
        btn.innerHTML = "🎤 Voice";
        return;
      }
      this._r = new SR();
      this._r.lang = Lang.getSpeechLang();  // Current selected language
      this._r.continuous = false;
      this._r.onresult = e => {
        tgt.value = e.results[0][0].transcript;
        tgt.dispatchEvent(new Event("input"));
        btn.classList.remove("recording");
        btn.innerHTML = "🎤 Voice";
      };
      this._r.onerror = () => {
        btn.classList.remove("recording");
        btn.innerHTML = "🎤 Voice";
        Toast.error("Voice input failed. Try again.");
      };
      this._r.onend = () => {
        btn.classList.remove("recording");
        btn.innerHTML = "🎤 Voice";
      };
      this._r.start();
      btn.classList.add("recording");
      btn.innerHTML = "⏹ Stop";
    });
  }
};

// ── PWA Install ───────────────────────────────────────────────────────────────
let _dP = null;
window.addEventListener("beforeinstallprompt", e => {
  e.preventDefault(); _dP = e;
  const b = document.getElementById("pwa-install-banner");
  if (b) b.style.display = "flex";
});

// ── Service Worker ────────────────────────────────────────────────────────────
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () =>
    navigator.serviceWorker.register("/static/service-worker.js")
      .catch(e => console.warn("[SW]", e))
  );
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function formatCurrency(a) {
  return "₹" + Number(a).toLocaleString("en-IN", { minimumFractionDigits: 0 });
}
function formatDate(s) {
  if (!s) return "—";
  return new Date(s).toLocaleDateString("en-IN",
    { day: "2-digit", month: "short", year: "numeric" });
}
function statusBadge(s) {
  const m = {
    pending:"badge-yellow", confirmed:"badge-blue", in_progress:"badge-blue",
    completed:"badge-green", cancelled:"badge-gray", open:"badge-green", full:"badge-red"
  };
  return `<span class="card-badge ${m[s]||"badge-gray"}">${s.replace("_"," ")}</span>`;
}
function starHtml(r) {
  const f = Math.round(r);
  return Array.from({length:5},(_,i) =>
    `<span class="star">${i<f?"★":"☆"}</span>`).join("");
}
function redirectIfNotLoggedIn() {
  if (!Auth.isLoggedIn()) window.location.href = "/login";
}
function redirectIfLoggedIn() {
  if (Auth.isLoggedIn()) {
    const u = Auth.getUser();
    window.location.href = u?.role === "owner" ? "/dashboard/owner" : "/dashboard/farmer";
  }
}

// ── Boot ──────────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  // PWA install buttons
  const ib = document.getElementById("pwa-install-btn");
  const db = document.getElementById("pwa-dismiss-btn");
  if (ib) ib.addEventListener("click", async () => {
    if (!_dP) return;
    _dP.prompt();
    const { outcome } = await _dP.userChoice;
    if (outcome === "accepted") Toast.success("TractoNow installed! 🎉");
    _dP = null;
    document.getElementById("pwa-install-banner").style.display = "none";
  });
  if (db) db.addEventListener("click", () =>
    document.getElementById("pwa-install-banner").style.display = "none");

  // Load language translations
  Lang.init();
});
