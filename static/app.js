// Логика сайта: загрузка новостей, фильтры, вкладки, тренды.

// topic: "kids" (детская литература) или "marketing" (маркетинг книг)
const state = { topic: "kids", source: "", q: "" };

const $ = (sel) => document.querySelector(sel);
const newsEl = $("#news");
const statusEl = $("#status");
const trendsEl = $("#trends");
const sourceSel = $("#source-filter");

// Форматирование даты в вид «6 июля 2026, 14:30»
function formatDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  if (isNaN(d)) return "";
  return d.toLocaleString("ru-RU", {
    day: "numeric", month: "long", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

function regionLabel(r) {
  return r === "ru" ? "Россия" : r === "int" ? "За рубежом" : "";
}

async function loadNews() {
  statusEl.textContent = "Загрузка…";
  const params = new URLSearchParams();
  if (state.topic) params.set("topic", state.topic);
  if (state.source) params.set("source", state.source);
  if (state.q) params.set("q", state.q);

  const res = await fetch("/api/news?" + params.toString());
  const items = await res.json();

  newsEl.innerHTML = "";
  if (items.length === 0) {
    statusEl.textContent = "Пока ничего не найдено. Попробуйте нажать «Обновить сейчас».";
    return;
  }
  statusEl.textContent = `Показано новостей: ${items.length}`;

  for (const a of items) {
    const card = document.createElement("article");
    card.className = "card";
    card.innerHTML = `
      <div class="meta">
        <span class="badge ${a.region}">${regionLabel(a.region)}</span>
        <span class="source">${escapeHtml(a.source || "")}</span>
        <span class="date">${formatDate(a.published)}</span>
      </div>
      <h3><a href="${encodeURI(a.link)}" target="_blank" rel="noopener">${escapeHtml(a.title)}</a></h3>
      ${a.summary ? `<p>${escapeHtml(a.summary)}</p>` : ""}
    `;
    newsEl.appendChild(card);
  }
}

async function loadSources() {
  const params = new URLSearchParams();
  if (state.topic) params.set("topic", state.topic);
  const res = await fetch("/api/sources?" + params.toString());
  const sources = await res.json();
  const current = state.source;
  sourceSel.innerHTML = '<option value="">Все источники</option>';
  for (const s of sources) {
    const opt = document.createElement("option");
    opt.value = s.source;
    opt.textContent = s.source;
    if (s.source === current) opt.selected = true;
    sourceSel.appendChild(opt);
  }
}

async function loadTrends() {
  const params = new URLSearchParams();
  if (state.topic) params.set("topic", state.topic);
  const res = await fetch("/api/trends?" + params.toString());
  const trends = await res.json();
  trendsEl.innerHTML = "";
  if (trends.length === 0) {
    trendsEl.innerHTML = '<span class="hint">Пока мало данных для трендов.</span>';
    return;
  }
  for (const t of trends) {
    const chip = document.createElement("button");
    chip.className = "chip";
    chip.innerHTML = `${escapeHtml(t.word)}<span class="n">${t.count}</span>`;
    chip.onclick = () => {
      $("#search").value = t.word;
      state.q = t.word;
      loadNews();
    };
    trendsEl.appendChild(chip);
  }
}

function refreshAll() {
  loadNews();
  loadSources();
  loadTrends();
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// --- События интерфейса ---

document.querySelectorAll(".tab").forEach((tab) => {
  tab.onclick = () => {
    document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");
    state.topic = tab.dataset.topic;
    state.source = "";
    state.q = "";
    $("#search").value = "";
    refreshAll();
  };
});

let searchTimer;
$("#search").oninput = (e) => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    state.q = e.target.value.trim();
    loadNews();
  }, 300);
};

sourceSel.onchange = (e) => {
  state.source = e.target.value;
  loadNews();
};

$("#refresh-btn").onclick = async (e) => {
  const btn = e.target;
  btn.disabled = true;
  btn.textContent = "Обновляю…";
  try {
    await fetch("/api/refresh", { method: "POST" });
  } catch (_) {}
  btn.disabled = false;
  btn.textContent = "Обновить сейчас";
  refreshAll();
};

// Первая загрузка
refreshAll();
