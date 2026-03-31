/* booking.js — TractoNow v2.1 */
let _eq = {};
const TYPE_EMOJI = {
  tractor:"🚜", harvester:"🌾", sprayer:"💧", rotavator:"⚙️",
  seed_drill:"🌱", cultivator:"🔧", plough:"🪵", thresher:"🌀"
};

// ── Load equipment with filters ───────────────────────────────────────────────
async function loadEq() {
  const grid = document.getElementById("eq-grid");
  if (!grid) return;
  grid.innerHTML = `<div class="spinner" style="margin:2rem auto;display:block;"></div>`;

  let q = "/equipment/?";
  const v = document.getElementById("fv")?.value || "";
  const m = document.getElementById("fm")?.value || "";
  const d = document.getElementById("fd")?.value || "";
  const s = document.getElementById("fs")?.value || "";
  const t = document.getElementById("ft")?.value || "";
  if (v) q += `village=${encodeURIComponent(v)}&`;
  if (m) q += `mandal=${encodeURIComponent(m)}&`;
  if (d) q += `district=${encodeURIComponent(d)}&`;
  if (s) q += `state=${encodeURIComponent(s)}&`;
  if (t) q += `type=${t}&`;
  if (document.getElementById("fa")?.checked) q += `available=true&`;

  const res = await Api.get(q);
  const rc  = document.getElementById("result-count");

  if (!res?.success || !res.equipment.length) {
    grid.innerHTML = `<p style="color:var(--text-muted);text-align:center;padding:2rem;grid-column:1/-1;">
      No equipment found. Try different filters.</p>`;
    if (rc) rc.textContent = "0 results";
    return;
  }

  if (rc) rc.textContent = `${res.count} equipment found`;

  grid.innerHTML = res.equipment.map(eq => `
    <div class="card" style="padding:1rem;">
      <!-- PORTRAIT image wrapper -->
      <div class="eq-img-wrap">
        ${eq.image_url
          ? `<img src="${eq.image_url}" alt="${eq.name}" loading="lazy" style="object-fit:contain;"/>`
          : `<span class="eq-emoji-placeholder">${TYPE_EMOJI[eq.type]||"🚜"}</span>`}
      </div>

      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.35rem;">
        <span class="card-badge badge-blue"
          style="text-transform:capitalize;font-size:.72rem;">${eq.type.replace("_"," ")}</span>
        <span class="availability-dot ${eq.availability?"dot-green":"dot-red"}"></span>
      </div>
      <h3 style="font-size:.95rem;font-weight:600;margin-bottom:.2rem;">${eq.name}</h3>
      <p class="card-meta">${eq.brand} ${eq.model}${eq.hp?" · "+eq.hp+"HP":""}</p>
      <p class="card-meta" style="margin-top:.2rem;">📍 ${
        [eq.location?.village, eq.location?.mandal, eq.location?.district]
        .filter(Boolean).join(", ") || "—"}</p>
      <div style="display:flex;justify-content:space-between;align-items:center;margin:.6rem 0;">
        <div style="font-size:1.1rem;font-weight:700;color:var(--primary);">
          ${formatCurrency(eq.price_per_hour)}<span style="font-size:.8rem;font-weight:400;color:var(--text-muted);">/hr</span>
        </div>
        <div style="font-size:.82rem;">${starHtml(eq.avg_rating)}
          <small style="color:var(--text-muted);">(${eq.total_ratings})</small></div>
      </div>
      ${eq.description
        ? `<p style="font-size:.8rem;color:var(--text-muted);margin-bottom:.7rem;
             white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${eq.description}</p>` : ""}
      <button class="btn btn-primary btn-full"
        onclick="openBk('${eq.id}',
          '${eq.name.replace(/'/g,"\\'").replace(/"/g,"&quot;")}',
          ${eq.price_per_hour},'${eq.type}',
          '${eq.image_url||""}',
          '${[eq.location?.village,eq.location?.mandal,eq.location?.district].filter(Boolean).join(", ").replace(/'/g,"\\'")}')"
        ${eq.availability?"":"disabled"}>
        ${eq.availability?"📅 Book Now":"❌ Not Available"}
      </button>
    </div>`).join("");
}

// ── Open booking modal ────────────────────────────────────────────────────────
function openBk(id, name, price, type, img, loc) {
  _eq = { id, name, pricePerHour: price, type };
  document.getElementById("m-name").textContent  = name;
  document.getElementById("m-price").textContent = formatCurrency(price) + "/hr";
  document.getElementById("m-loc").textContent   = loc ? "📍 " + loc : "";

  // Portrait image in modal
  const imgDiv = document.getElementById("m-img");
  const imgEl  = document.getElementById("m-img-el");
  if (img) {
    imgEl.src = img;
    imgDiv.style.display = "block";
  } else {
    imgDiv.style.display = "none";
  }

  document.getElementById("bk-modal").style.display = "flex";
  document.getElementById("price-box").innerHTML =
    `<p style="color:var(--text-muted);font-size:.88rem;">
      Select crop, date & hours to see pricing.</p>`;
  document.getElementById("bk-err").style.display = "none";
}

function closeBk() {
  document.getElementById("bk-modal").style.display = "none";
}

// ── Live price + demand preview ───────────────────────────────────────────────
async function updatePrice() {
  const crop  = document.getElementById("crop")?.value;
  const hrs   = document.getElementById("hrs")?.value;
  const date  = document.getElementById("bdate")?.value;
  if (!crop || !hrs || !date || !_eq.id) return;

  const pb = document.getElementById("price-box");
  pb.innerHTML = `<div class="spinner" style="display:block;margin:.5rem auto;"></div>`;

  const res = await Api.post("/ml/predict", {
    crop_type: crop, equipment_type: _eq.type,
    booking_date: date, district: Auth.getUser()?.district || ""
  });

  const pred  = res?.prediction || {};
  const level = pred.demand_level || "Low";
  const dc    = { High:"demand-high", Moderate:"demand-moderate", Low:"demand-low" }[level] || "demand-low";
  const mult  = { High:1.6, Moderate:1.3, Low:1.0 }[level] || 1.0;
  const gross = (_eq.pricePerHour * Number(hrs) * mult).toFixed(2);
  const fee   = (gross * 0.05).toFixed(2);

  pb.innerHTML = `
    <div class="demand-widget ${dc}" style="margin-bottom:.85rem;">
      <div class="demand-title">${pred.icon||""} ${level} Demand
        (${Math.round((pred.confidence||0)*100)}%)</div>
      <div style="font-size:.82rem;margin-top:.25rem;">${pred.advice||""}</div>
    </div>
    <div style="background:#f9fafb;border-radius:var(--radius);padding:.85rem;font-size:.88rem;">
      <div style="display:flex;justify-content:space-between;margin-bottom:.3rem;">
        <span>Base rate</span>
        <span>${formatCurrency(_eq.pricePerHour)}/hr × ${hrs} hrs</span>
      </div>
      <div style="display:flex;justify-content:space-between;margin-bottom:.3rem;color:var(--accent);">
        <span>Demand multiplier</span><span>×${mult}</span>
      </div>
      <div style="display:flex;justify-content:space-between;margin-bottom:.3rem;">
        <span>Platform fee 5%</span><span>${formatCurrency(fee)}</span>
      </div>
      <hr style="margin:.4rem 0;border-color:var(--border);">
      <div style="display:flex;justify-content:space-between;font-weight:700;font-size:1rem;">
        <span>Total</span>
        <span style="color:var(--primary);">${formatCurrency(gross)}</span>
      </div>
    </div>
    ${res?.weather_tip
      ? `<div class="alert ${res.weather_tip.safe_to_operate?"alert-info":"alert-warning"}"
           style="margin-top:.65rem;font-size:.82rem;">
           ${res.weather_tip.suggestion}</div>`
      : ""}`;
}

// ── Submit booking ────────────────────────────────────────────────────────────
async function submitBooking(e) {
  e.preventDefault();
  const btn = e.target.querySelector(".btn-submit");
  btn.disabled = true;
  btn.innerHTML = `<span class="spinner"></span> Booking…`;
  const fd = new FormData(e.target);
  const res = await Api.post("/bookings/", {
    equipment_id:   _eq.id,
    crop_type:      fd.get("crop_type"),
    booking_date:   fd.get("booking_date"),
    hours_required: Number(fd.get("hours_required")),
    notes:          fd.get("notes") || ""
  });
  btn.disabled = false;
  btn.innerHTML = "📅 Confirm Booking";
  if (res?.success) {
    Toast.success("Booking confirmed! 🎉");
    closeBk();
    setTimeout(() => window.location.href = "/dashboard/farmer", 1100);
  } else {
    const el = document.getElementById("bk-err");
    el.textContent = res?.message || "Booking failed.";
    el.style.display = "block";
  }
}
