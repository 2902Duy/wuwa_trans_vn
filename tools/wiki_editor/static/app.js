const state = {
  summary: null,
  domain: "",
  page: 1,
  pageSize: 50,
  query: "",
};

async function api(path, options) {
  const res = await fetch(path, options);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function esc(text) {
  return String(text ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function splitSegments(text) {
  const value = String(text ?? "");
  if (!value.includes("\n\n")) return [value];
  return value.split(/\n\s*\n/g);
}

function joinSegments(values) {
  return values.join("\n\n");
}

function renderBilingualEditor(row) {
  const sourceSegments = splitSegments(row.source_en);
  const viSegments = splitSegments(row.new_translation_vi);
  if (sourceSegments.length <= 1) {
    return `
      <div class="bilingual">
        <div>
          <div class="label">English source</div>
          <div class="source-box">${esc(row.source_en)}</div>
        </div>
        <div>
          <div class="label">Vietnamese translation</div>
          <textarea class="translation-main">${esc(row.new_translation_vi)}</textarea>
        </div>
      </div>
    `;
  }

  return `
    <div class="segment-editor" data-segmented="true">
      ${sourceSegments.map((source, index) => `
        <div class="segment-pair">
          <div class="segment-label">Phần ${index + 1}</div>
          <div class="bilingual">
            <div>
              <div class="label">English source</div>
              <div class="source-box">${esc(source)}</div>
            </div>
            <div>
              <div class="label">Vietnamese translation</div>
              <textarea class="translation-segment" data-index="${index}">${esc(viSegments[index] ?? "")}</textarea>
            </div>
          </div>
        </div>
      `).join("")}
    </div>
  `;
}

function setView(name) {
  document.querySelectorAll(".view").forEach(v => v.classList.toggle("active", v.id === name));
  document.querySelectorAll(".nav").forEach(b => b.classList.toggle("active", b.dataset.view === name));
}

function card(label, value) {
  return `<div class="card"><div class="num">${esc(value)}</div><div class="label">${esc(label)}</div></div>`;
}

async function loadSummary() {
  state.summary = await api("/api/summary");
  document.querySelector("#summaryCards").innerHTML = [
    card("Tổng dòng", state.summary.total_rows.toLocaleString()),
    card("Phần dữ liệu", state.summary.domains.length),
    card("File nguồn", state.summary.source_files),
    card("Nhân vật", state.summary.characters),
  ].join("");

  const domainGrid = document.querySelector("#domainGrid");
  domainGrid.innerHTML = state.summary.domains.map(d => `
    <div class="domain-card" data-domain="${esc(d.domain)}">
      <div class="list-title">${esc(d.domain)}</div>
      <div class="list-sub">${d.translated.toLocaleString()} / ${d.rows.toLocaleString()} đã có bản Việt</div>
      <div class="list-sub">${d.source_files} file nguồn</div>
    </div>
  `).join("");

  const select = document.querySelector("#domainSelect");
  select.innerHTML = state.summary.domains.map(d => `<option value="${esc(d.domain)}">${esc(d.domain)} (${d.rows})</option>`).join("");
  state.domain = select.value;

  domainGrid.querySelectorAll(".domain-card").forEach(el => {
    el.addEventListener("click", () => {
      state.domain = el.dataset.domain;
      select.value = state.domain;
      state.page = 1;
      setView("domains");
      loadRows();
    });
  });
}

function renderRows(container, rows) {
  container.innerHTML = rows.map(row => `
    <article class="row-card" data-split-id="${esc(row.split_id)}">
      <div class="meta">
        <span class="pill">${esc(row.prompt_domain)}</span>
        <span>${esc(row.source_file)}</span>
        <span>${esc(row.primary_key)}</span>
        <span>${esc(row.split_id)}</span>
      </div>
      ${renderBilingualEditor(row)}
      <div class="save-line">
        <input class="note" placeholder="Ghi chú" value="${esc(row.translator_note)}" />
        <button class="primary save-btn">Lưu</button>
        <span class="save-status"></span>
      </div>
    </article>
  `).join("");

  container.querySelectorAll(".row-card").forEach(card => {
    const splitId = card.dataset.splitId;
    card.querySelector(".save-btn").addEventListener("click", async () => {
      const status = card.querySelector(".save-status");
      status.textContent = "Đang lưu...";
      const segmented = card.querySelector(".segment-editor");
      let translation = "";
      if (segmented) {
        const values = [...card.querySelectorAll(".translation-segment")].map(input => input.value);
        translation = joinSegments(values);
      } else {
        translation = card.querySelector(".translation-main").value;
      }
      const payload = {
        split_id: splitId,
        new_translation_vi: translation,
        translator_note: card.querySelector(".note").value,
      };
      const result = await api("/api/row", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(payload),
      });
      status.textContent = result.ok ? "Đã lưu" : "Lỗi";
    });
  });
}

async function loadRows() {
  const params = new URLSearchParams({
    domain: state.domain,
    q: state.query,
    page: state.page,
    page_size: state.pageSize,
  });
  const data = await api(`/api/rows?${params.toString()}`);
  renderRows(document.querySelector("#rowsList"), data.rows);
  const pages = Math.max(Math.ceil(data.total / data.page_size), 1);
  document.querySelector("#pageInfo").textContent = `Trang ${data.page} / ${pages} (${data.total.toLocaleString()} dòng)`;
  document.querySelector("#prevPage").disabled = data.page <= 1;
  document.querySelector("#nextPage").disabled = data.page >= pages;
}

async function loadQuests() {
  const q = document.querySelector("#questSearch").value;
  const data = await api(`/api/quests?q=${encodeURIComponent(q)}`);
  const list = document.querySelector("#questList");
  list.innerHTML = data.quests.map(item => `
    <div class="list-item" data-id="${esc(item.quest_id)}">
      <div class="list-title">${esc(item.title)}</div>
      <div class="list-sub">${esc(item.quest_id)} · ${item.translated}/${item.rows}</div>
    </div>
  `).join("");
  list.querySelectorAll(".list-item").forEach(el => {
    el.addEventListener("click", () => loadQuestDetail(el.dataset.id));
  });
}

async function loadQuestDetail(id) {
  const data = await api(`/api/quest/${encodeURIComponent(id)}`);
  document.querySelector("#questDetail").innerHTML = `<h2>${esc(id)}</h2><div id="questRows" class="rows"></div>`;
  renderRows(document.querySelector("#questRows"), data.rows);
}

async function loadCharacters() {
  const data = await api("/api/characters");
  const q = document.querySelector("#characterSearch").value.toLowerCase();
  const chars = data.characters.filter(c => `${c.name} ${c.title}`.toLowerCase().includes(q));
  const list = document.querySelector("#characterList");
  list.innerHTML = chars.map(char => `
    <div class="list-item" data-name="${esc(char.name)}">
      <div class="list-title">${esc(char.name)}</div>
      <div class="list-sub">${esc(char.title)}</div>
    </div>
  `).join("");
  list.querySelectorAll(".list-item").forEach(el => {
    el.addEventListener("click", () => loadCharacterDetail(el.dataset.name));
  });
}

async function loadCharacterDetail(name) {
  const data = await api(`/api/character/${encodeURIComponent(name)}`);
  const char = data.character;
  const detail = document.querySelector("#characterDetail");
  const labels = {
    profile: "Hồ sơ nhân vật",
    skill_names: "Tên skill",
    skill_descriptions: "Chi tiết mô tả skill",
    rc_names: "Tên Resonance Chain",
    rc_descriptions: "Chi tiết mô tả RC",
    lore: "Lore / thoại / favor",
    other: "Khác",
  };
  detail.innerHTML = `
    <h2>${esc(char.name)}</h2>
    <div class="row-card">
      <div class="bilingual">
        <div><div class="label">English</div><div class="source-box">${esc(char.title)}\n\n${esc(char.description)}</div></div>
        <div><div class="label">Vietnamese current</div><div class="source-box">${esc(char.vi_title)}\n\n${esc(char.vi_description)}</div></div>
      </div>
    </div>
    <h2>Cấu trúc liên quan (${data.related_total})</h2>
    <div class="section-tabs">
      ${Object.entries(labels).map(([key, label]) => `
        <button class="section-tab" data-section="${key}">${esc(label)} <span>${data.section_counts[key] ?? 0}</span></button>
      `).join("")}
    </div>
    <div id="characterSectionRows" class="rows"></div>
  `;
  const renderSection = (section) => {
    document.querySelectorAll(".section-tab").forEach(btn => btn.classList.toggle("active", btn.dataset.section === section));
    renderRows(document.querySelector("#characterSectionRows"), data.sections[section] ?? []);
  };
  detail.querySelectorAll(".section-tab").forEach(btn => {
    btn.addEventListener("click", () => renderSection(btn.dataset.section));
  });
  const firstNonEmpty = Object.keys(labels).find(key => (data.section_counts[key] ?? 0) > 0) ?? "profile";
  renderSection(firstNonEmpty);
}

document.querySelectorAll(".nav").forEach(button => {
  button.addEventListener("click", () => setView(button.dataset.view));
});

document.querySelector("#domainSelect").addEventListener("change", e => {
  state.domain = e.target.value;
  state.page = 1;
  loadRows();
});

document.querySelector("#globalSearch").addEventListener("input", e => {
  state.query = e.target.value;
  state.page = 1;
  if (document.querySelector("#domains").classList.contains("active")) loadRows();
});

document.querySelector("#prevPage").addEventListener("click", () => {
  state.page -= 1;
  loadRows();
});

document.querySelector("#nextPage").addEventListener("click", () => {
  state.page += 1;
  loadRows();
});

document.querySelector("#questSearch").addEventListener("input", loadQuests);
document.querySelector("#characterSearch").addEventListener("input", loadCharacters);
document.querySelector("#reloadBtn").addEventListener("click", async () => {
  await api("/api/reload");
  await loadSummary();
  await loadRows();
  await loadQuests();
  await loadCharacters();
});

(async function init() {
  await loadSummary();
  await loadRows();
  await loadQuests();
  await loadCharacters();
})();
