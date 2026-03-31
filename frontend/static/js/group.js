/* ════════════════════════════════════════════
   group.js  —  Group booking page logic
════════════════════════════════════════════ */

document.addEventListener("DOMContentLoaded", () => {
  redirectIfNotLoggedIn();
  loadOpenGroups();
  initCreateGroupForm();
});

// ── Load open groups ──────────────────────────────────────────────────────────
async function loadOpenGroups() {
  const list = document.getElementById("groups-list");
  if (!list) return;
  list.innerHTML = `<div class="spinner" style="margin:2rem auto;display:block;"></div>`;

  const district = Auth.getUser()?.district || "";
  const res = await Api.get(`/groups/open?district=${encodeURIComponent(district)}`);

  if (!res?.success || !res.groups.length) {
    list.innerHTML = `
      <div style="text-align:center;padding:2.5rem;color:var(--text-muted);">
        <p style="font-size:2rem;">👥</p>
        <p>No open groups in your area yet.</p>
        <p style="margin-top:.5rem;font-size:.9rem;">Be the first to create one and invite neighbours!</p>
      </div>`;
    return;
  }

  list.innerHTML = res.groups.map(g => renderGroupCard(g)).join("");
}

function renderGroupCard(g) {
  const user       = Auth.getUser();
  const isMember   = g.members.includes(user?.id);
  const isCreator  = g.creator_id === user?.id;
  const isFull     = g.status === "full";
  const pct        = Math.round((g.member_count / g.max_farmers) * 100);

  return `
    <div class="card group-card" id="group-${g.id}">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;">
        <div>
          <span class="card-badge badge-blue" style="margin-bottom:.5rem;display:inline-block;">
            ${g.equipment_type.replace("_"," ")}
          </span>
          <h3 class="card-title">${g.crop_type.charAt(0).toUpperCase()+g.crop_type.slice(1)} — ${formatDate(g.booking_date)}</h3>
          <p class="card-meta">📍 ${g.district || "—"} &nbsp;•&nbsp; ${g.hours_required} hrs</p>
        </div>
        ${statusBadge(g.status)}
      </div>

      <div style="margin:1rem 0;">
        <div style="display:flex;justify-content:space-between;font-size:.85rem;margin-bottom:.3rem;">
          <span class="group-members-count">👨‍🌾 ${g.member_count} / ${g.max_farmers} farmers joined</span>
          <span style="font-weight:600;color:var(--primary);">${pct}% full</span>
        </div>
        <div class="group-progress">
          <div class="group-progress-fill" style="width:${pct}%;"></div>
        </div>
      </div>

      <div style="display:flex;justify-content:space-between;align-items:center;">
        <div>
          <div style="font-size:1.2rem;font-weight:700;color:var(--primary);">
            ${formatCurrency(g.per_farmer_share)}<span style="font-size:.8rem;font-weight:400;color:var(--text-muted);"> /farmer</span>
          </div>
          <div style="font-size:.8rem;color:var(--text-muted);">
            Total: ${formatCurrency(g.base_price)}
          </div>
        </div>
        <div style="display:flex;gap:.5rem;">
          ${!isMember && !isFull ? `
            <button class="btn btn-primary btn-sm" onclick="joinGroup('${g.id}')">
              ➕ Join Group
            </button>` : ""}
          ${isMember && !isCreator ? `
            <button class="btn btn-secondary btn-sm" onclick="leaveGroup('${g.id}')">
              🚪 Leave
            </button>` : ""}
          ${isCreator ? `
            <span class="card-badge badge-green">✓ You created this</span>` : ""}
          ${isFull ? `
            <span class="card-badge badge-red">Group Full</span>` : ""}
        </div>
      </div>
    </div>
  `;
}

// ── Join Group ────────────────────────────────────────────────────────────────
async function joinGroup(groupId) {
  const res = await Api.post(`/groups/${groupId}/join`, {});
  if (res?.success) {
    Toast.success(`Joined! Your share: ${formatCurrency(res.your_share)} 🎉`);
    loadOpenGroups();
  } else {
    Toast.error(res?.message || "Could not join group.");
  }
}

// ── Leave Group ───────────────────────────────────────────────────────────────
async function leaveGroup(groupId) {
  if (!confirm("Are you sure you want to leave this group?")) return;
  const res = await Api.post(`/groups/${groupId}/leave`, {});
  if (res?.success) {
    Toast.success("Left the group.");
    loadOpenGroups();
  } else {
    Toast.error(res?.message || "Could not leave group.");
  }
}

// ── Create Group Form ─────────────────────────────────────────────────────────
function initCreateGroupForm() {
  const form = document.getElementById("create-group-form");
  if (!form) return;

  // Live cost-per-farmer preview
  ["group-hours", "group-max-farmers"].forEach(id => {
    document.getElementById(id)?.addEventListener("input", updateGroupCostPreview);
  });
  document.getElementById("group-equipment-id")?.addEventListener("change", updateGroupCostPreview);

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = form.querySelector(".btn-submit");
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner"></span> Creating...`;

    const fd = new FormData(form);
    const payload = {
      equipment_id:   fd.get("equipment_id"),
      crop_type:      fd.get("crop_type"),
      booking_date:   fd.get("booking_date"),
      hours_required: Number(fd.get("hours_required")),
      max_farmers:    Number(fd.get("max_farmers")) || 3
    };

    const res = await Api.post("/groups/", payload);
    btn.disabled = false;
    btn.innerHTML = "👥 Create Group";

    if (res?.success) {
      Toast.success(`Group created! Per farmer share: ${formatCurrency(res.per_farmer)} 🎉`);
      form.reset();
      loadOpenGroups();
      // Show shareable ID
      const shareDiv = document.getElementById("share-group-id");
      if (shareDiv) {
        shareDiv.textContent = `Share Group ID: ${res.group_id}`;
        shareDiv.style.display = "block";
      }
    } else {
      Toast.error(res?.message || "Could not create group.");
    }
  });
}

async function updateGroupCostPreview() {
  const eqSelect = document.getElementById("group-equipment-id");
  const hours    = Number(document.getElementById("group-hours")?.value || 0);
  const maxF     = Number(document.getElementById("group-max-farmers")?.value || 1);
  const preview  = document.getElementById("group-cost-preview");
  if (!preview || !eqSelect?.value || !hours) return;

  const res = await Api.get(`/equipment/${eqSelect.value}`);
  if (res?.success) {
    const pph   = res.equipment.price_per_hour;
    const total = pph * hours;
    const share = (total / maxF).toFixed(2);
    preview.innerHTML = `
      <span>Total: <strong>${formatCurrency(total)}</strong></span>
      &nbsp;•&nbsp;
      <span>Per farmer: <strong style="color:var(--primary);">${formatCurrency(share)}</strong></span>
    `;
  }
}
