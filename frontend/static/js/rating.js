/* ══════════════════════════════════════════
   rating.js  —  Star rating & submit
══════════════════════════════════════════ */

let _selectedRating = 0;

document.addEventListener("DOMContentLoaded", () => {
  redirectIfNotLoggedIn();
  initStarRating();
  initRatingForm();
  loadEquipmentRatings();
});

// ── Interactive star selector ─────────────────────────────────────────────────
function initStarRating() {
  const container = document.getElementById("star-rating");
  if (!container) return;

  container.innerHTML = [1,2,3,4,5].map(n => `
    <button type="button" class="star-btn" data-value="${n}" aria-label="${n} stars">★</button>
  `).join("");

  const stars = container.querySelectorAll(".star-btn");

  stars.forEach(star => {
    star.addEventListener("mouseover", () => highlightStars(stars, Number(star.dataset.value)));
    star.addEventListener("mouseleave", () => highlightStars(stars, _selectedRating));
    star.addEventListener("click", () => {
      _selectedRating = Number(star.dataset.value);
      highlightStars(stars, _selectedRating);
      document.getElementById("rating-value").value = _selectedRating;
      // Show review textarea once rated
      document.getElementById("review-section").style.display = "block";
    });
  });
}

function highlightStars(stars, upTo) {
  stars.forEach(s => s.classList.toggle("active", Number(s.dataset.value) <= upTo));
}

// ── Submit rating ─────────────────────────────────────────────────────────────
function initRatingForm() {
  const form = document.getElementById("rating-form");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!_selectedRating) {
      Toast.warning("Please select a star rating first.");
      return;
    }
    const btn = form.querySelector(".btn-submit");
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner"></span> Submitting...`;

    const fd = new FormData(form);
    const payload = {
      booking_id: fd.get("booking_id"),
      rating:     _selectedRating,
      review:     fd.get("review") || ""
    };

    const res = await Api.post("/ratings/", payload);
    btn.disabled = false;
    btn.innerHTML = "⭐ Submit Rating";

    if (res?.success) {
      Toast.success("Thank you for your rating! ⭐");
      form.reset();
      _selectedRating = 0;
      document.getElementById("star-rating").querySelectorAll(".star-btn")
              .forEach(s => s.classList.remove("active"));
      document.getElementById("review-section").style.display = "none";
      loadEquipmentRatings();
    } else {
      Toast.error(res?.message || "Could not submit rating.");
    }
  });
}

// ── Load ratings for an equipment ────────────────────────────────────────────
async function loadEquipmentRatings() {
  const eqId = document.getElementById("eq-id-hidden")?.value;
  const list  = document.getElementById("ratings-list");
  const summary = document.getElementById("rating-summary");
  if (!eqId || !list) return;

  const res = await Api.get(`/ratings/equipment/${eqId}`);
  if (!res?.success) return;

  // Summary
  if (summary) {
    summary.innerHTML = `
      <div style="text-align:center;margin-bottom:1rem;">
        <div style="font-size:3rem;font-weight:700;color:var(--primary);">${res.avg_rating}</div>
        <div style="font-size:1.2rem;">${starHtml(res.avg_rating)}</div>
        <div style="color:var(--text-muted);font-size:.9rem;">${res.total} ratings</div>
      </div>
      ${[5,4,3,2,1].map(n => {
        const count = res.ratings.filter(r => r.rating === n).length;
        const pct   = res.total ? Math.round((count/res.total)*100) : 0;
        return `
          <div class="rating-bar-wrap">
            <div class="rating-bar-label">${n}★</div>
            <div class="rating-bar"><div class="rating-bar-fill" style="width:${pct}%"></div></div>
            <div class="rating-bar-count">${count}</div>
          </div>`;
      }).join("")}
    `;
  }

  // Individual reviews
  if (!res.ratings.length) {
    list.innerHTML = `<p style="color:var(--text-muted);font-size:.9rem;">No reviews yet. Be the first!</p>`;
    return;
  }
  list.innerHTML = res.ratings.map(r => `
    <div class="card" style="padding:1rem;margin-bottom:.75rem;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.35rem;">
        <div>${starHtml(r.rating)}</div>
        <small style="color:var(--text-muted);">${formatDate(r.created_at)}</small>
      </div>
      ${r.review ? `<p style="font-size:.9rem;">${r.review}</p>` : ""}
    </div>
  `).join("");
}
