from __future__ import annotations


def render_manager_app() -> str:
    return """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>ONEF Manager Console</title>
  <style>
    :root {
      --bg: #f7f3eb;
      --panel: rgba(255, 255, 255, 0.9);
      --panel-strong: rgba(255, 255, 255, 0.98);
      --ink: #18212a;
      --muted: #607080;
      --line: rgba(24, 33, 42, 0.08);
      --accent: #0c7a67;
      --accent-2: #d17b23;
      --danger: #be4f48;
      --success: #0f7665;
      --shadow: 0 18px 36px rgba(38, 43, 47, 0.12);
      --radius: 22px;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      color: var(--ink);
      font-family: "Avenir Next", "Segoe UI Variable", "Segoe UI", sans-serif;
      background:
        radial-gradient(circle at top left, rgba(12,122,103,0.18), transparent 26%),
        radial-gradient(circle at 78% 12%, rgba(209,123,35,0.14), transparent 18%),
        linear-gradient(180deg, #f9f6f1 0%, #f2ede5 100%);
    }
    .layout {
      display: grid;
      grid-template-columns: 380px 1fr;
      min-height: 100vh;
    }
    .sidebar {
      padding: 28px;
      border-right: 1px solid var(--line);
      background: rgba(255,255,255,0.48);
      backdrop-filter: blur(10px);
      display: flex;
      flex-direction: column;
      gap: 18px;
    }
    .main {
      padding: 28px;
      display: flex;
      flex-direction: column;
      gap: 18px;
    }
    .hero, .panel, .card, .ticket, .inbox-item {
      background: var(--panel);
      border: 1px solid rgba(255,255,255,0.55);
      box-shadow: var(--shadow);
      border-radius: var(--radius);
    }
    .hero {
      background: linear-gradient(145deg, #0b584c 0%, #0c7a67 58%, #28a191 100%);
      color: white;
      padding: 24px;
    }
    .eyebrow {
      text-transform: uppercase;
      letter-spacing: 0.14em;
      font-size: 11px;
      opacity: 0.78;
      margin-bottom: 8px;
    }
    h1, h2, h3, h4, p { margin: 0; }
    .hero h1 { font-size: 28px; line-height: 1.12; }
    .hero p {
      margin-top: 10px;
      color: rgba(255,255,255,0.82);
      line-height: 1.5;
    }
    .grid-2, .grid-4 {
      display: grid;
      gap: 14px;
    }
    .grid-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
    .grid-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .card {
      padding: 16px;
    }
    .card strong {
      display: block;
      font-size: 28px;
      margin-top: 6px;
    }
    .card span {
      color: var(--muted);
      font-size: 13px;
    }
    .panel {
      padding: 18px;
    }
    .section-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 14px;
    }
    .section-head p {
      color: var(--muted);
      font-size: 13px;
      margin-top: 4px;
    }
    .toolbar {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
    }
    input, select, textarea {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 11px 13px;
      background: rgba(255,255,255,0.92);
      color: var(--ink);
      font: inherit;
    }
    textarea { min-height: 120px; resize: vertical; }
    .toolbar input { flex: 1; min-width: 200px; }
    button, .link-button {
      appearance: none;
      border: 0;
      border-radius: 999px;
      padding: 11px 16px;
      font: inherit;
      font-weight: 700;
      cursor: pointer;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      transition: transform 120ms ease, opacity 120ms ease;
    }
    button:hover, .link-button:hover { transform: translateY(-1px); }
    button:disabled { opacity: 0.45; cursor: wait; transform: none; }
    .primary { background: var(--accent); color: white; }
    .secondary { background: rgba(12,122,103,0.1); color: var(--accent); }
    .tertiary { background: rgba(24,33,42,0.06); color: var(--ink); }
    .danger { background: rgba(190,79,72,0.12); color: var(--danger); }
    .success { background: rgba(15,118,101,0.12); color: var(--success); }
    .muted { color: var(--muted); }
    .small { font-size: 13px; }
    .chips {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 10px;
    }
    .chip {
      border-radius: 999px;
      padding: 6px 10px;
      font-size: 12px;
      font-weight: 700;
      background: rgba(24,33,42,0.08);
    }
    .chip.success { background: rgba(15,118,101,0.12); color: var(--success); }
    .chip.warn { background: rgba(209,123,35,0.16); color: var(--accent-2); }
    .chip.danger { background: rgba(190,79,72,0.14); color: var(--danger); }
    .inbox-list, .queue-list {
      display: flex;
      flex-direction: column;
      gap: 10px;
      max-height: 340px;
      overflow: auto;
      padding-right: 2px;
    }
    .inbox-item, .ticket {
      padding: 14px 16px;
    }
    .inbox-item {
      display: grid;
      grid-template-columns: 26px 1fr auto;
      gap: 12px;
      align-items: start;
    }
    .ticket.active {
      border-color: rgba(12,122,103,0.24);
      background: rgba(12,122,103,0.08);
    }
    .ticket h4, .inbox-item h4 {
      font-size: 14px;
      line-height: 1.35;
      margin-bottom: 6px;
    }
    .ticket p, .inbox-item p {
      font-size: 12px;
      line-height: 1.45;
      color: var(--muted);
    }
    .main-grid {
      display: grid;
      grid-template-columns: 1.2fr 0.8fr;
      gap: 18px;
    }
    .detail-grid {
      display: grid;
      grid-template-columns: 1.15fr 0.85fr;
      gap: 18px;
    }
    .stack {
      display: flex;
      flex-direction: column;
      gap: 18px;
    }
    .mail-body, .reply-box, .pre {
      white-space: pre-wrap;
      line-height: 1.58;
      font-size: 14px;
      color: #324150;
      max-height: 290px;
      overflow: auto;
    }
    .bars {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .bar-row {
      display: grid;
      grid-template-columns: 120px 1fr 42px;
      gap: 12px;
      align-items: center;
      font-size: 13px;
    }
    .bar-track {
      width: 100%;
      height: 12px;
      background: rgba(24,33,42,0.08);
      border-radius: 999px;
      overflow: hidden;
    }
    .bar-fill {
      height: 100%;
      background: linear-gradient(90deg, #0c7a67, #36b6a1);
      border-radius: 999px;
    }
    .timeline {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(58px, 1fr));
      gap: 10px;
      align-items: end;
      min-height: 170px;
    }
    .timeline-col {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;
      font-size: 11px;
      color: var(--muted);
    }
    .timeline-bar {
      width: 100%;
      border-radius: 14px 14px 8px 8px;
      background: linear-gradient(180deg, #0c7a67, #d17b23);
      min-height: 8px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }
    th, td {
      text-align: left;
      padding: 10px 8px;
      border-bottom: 1px solid var(--line);
    }
    th { color: var(--muted); font-weight: 700; }
    .actions {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 12px;
    }
    .empty {
      border: 1px dashed var(--line);
      border-radius: 18px;
      padding: 26px;
      background: rgba(255,255,255,0.62);
      color: var(--muted);
      text-align: center;
    }
    @media (max-width: 1220px) {
      .layout, .main-grid, .detail-grid, .grid-4, .grid-2 { grid-template-columns: 1fr; }
      .inbox-list, .queue-list { max-height: none; }
    }
  </style>
</head>
<body>
  <div class="layout">
    <aside class="sidebar">
      <section class="hero">
        <div class="eyebrow">ONEF Manager Console</div>
        <h1>Pilotage réel des emails clients, envoi auto contrôlé et supervision managériale.</h1>
        <p>Tu peux maintenant choisir les emails à analyser, ouvrir le thread dans Gmail, laisser l’application répondre automatiquement aux cas simples et suivre l’évolution des plaintes par catégorie.</p>
      </section>

      <section class="panel">
        <div class="section-head">
          <div>
            <h3>Boîte Gmail à analyser</h3>
            <p>Sélection explicite des messages avant analyse.</p>
          </div>
          <button class="secondary" id="refreshInboxButton">Actualiser</button>
        </div>
        <div class="toolbar" style="margin-bottom: 10px;">
          <button class="tertiary" id="selectAllInboxButton">Tout sélectionner</button>
          <button class="primary" id="analyzeSelectedButton">Analyser la sélection</button>
        </div>
        <div class="inbox-list" id="inboxList"></div>
      </section>

      <section class="panel">
        <div class="section-head">
          <div>
            <h3>File manager</h3>
            <p>Tickets qualifiés et prêts pour l’action.</p>
          </div>
          <button class="primary" id="syncUnreadButton">Analyser les non lus</button>
        </div>
        <div class="toolbar" style="margin-bottom: 12px;">
          <input id="searchInput" placeholder="Sujet, client, catégorie, email..." />
          <select id="statusFilter">
            <option value="all">Tous les statuts</option>
            <option value="new">Nouveau</option>
            <option value="in_progress">En cours</option>
            <option value="treated">Traité</option>
            <option value="sent">Envoyé</option>
            <option value="ignored">Ignoré</option>
          </select>
        </div>
        <div class="queue-list" id="queueList"></div>
      </section>
    </aside>

    <main class="main">
      <section class="grid-4" id="metrics"></section>

      <section class="main-grid">
        <div class="stack">
          <section class="panel">
            <div class="section-head">
              <div>
                <h3>Évolution des plaintes</h3>
                <p>Volume traité par journée de synchronisation.</p>
              </div>
            </div>
            <div class="timeline" id="timeline"></div>
          </section>

          <section class="panel">
            <div class="section-head">
              <div>
                <h3>Répartition par catégorie</h3>
                <p>Plainte, commande, remboursement, question.</p>
              </div>
            </div>
            <div class="bars" id="categoryBars"></div>
          </section>
        </div>

        <section class="panel">
          <div class="section-head">
            <div>
              <h3>Tableau clients</h3>
              <p>Clients actifs et pression tickets récente.</p>
            </div>
          </div>
          <div id="clientsTable"></div>
        </section>
      </section>

      <section class="panel">
        <div class="section-head">
          <div>
            <div class="eyebrow">Dossier</div>
            <h2 id="detailTitle">Sélectionne un ticket</h2>
          </div>
          <div class="muted small" id="detailMeta">Aucun ticket sélectionné</div>
        </div>
        <div id="detailContent" class="empty">Choisis un email dans la file manager pour voir le contexte client, la réponse proposée et les actions possibles.</div>
      </section>
    </main>
  </div>

  <script>
    const state = {
      items: [],
      inbox: [],
      overview: {},
      dashboard: { categories: [], timeline: [], clients: [] },
      selectedId: null,
      selectedInboxIds: new Set()
    };

    const labels = {
      new: "Nouveau",
      in_progress: "En cours",
      treated: "Traité",
      sent: "Envoyé",
      ignored: "Ignoré",
      review: "À qualifier",
      relevant: "À traiter",
      irrelevant: "À ignorer"
    };

    function escapeHtml(value) {
      return String(value || "").replace(/[&<>\\"]/g, (char) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;"
      }[char]));
    }

    function badge(text, klass = "") {
      return `<span class="chip ${klass}">${escapeHtml(text)}</span>`;
    }

    function card(title, value, hint) {
      return `<article class="card"><span>${title}</span><strong>${value}</strong><span>${hint}</span></article>`;
    }

    async function api(path, options = {}) {
      const response = await fetch(path, {
        headers: { "Content-Type": "application/json" },
        ...options
      });
      if (!response.ok) {
        throw new Error(await response.text() || "Request failed");
      }
      return response.json();
    }

    function selectedInboxArray() {
      return Array.from(state.selectedInboxIds);
    }

    function filteredItems() {
      const status = document.getElementById("statusFilter").value;
      const query = document.getElementById("searchInput").value.trim().toLowerCase();
      return state.items.filter((item) => {
        const statusOk = status === "all" || item.status === status;
        const haystack = [
          item.subject, item.sender_email, item.customer_name, item.customer_email,
          item.complaint_category, item.intent, item.sentiment
        ].join(" ").toLowerCase();
        const searchOk = !query || haystack.includes(query);
        return statusOk && searchOk;
      });
    }

    function renderMetrics() {
      const overview = state.overview || {};
      document.getElementById("metrics").innerHTML = [
        card("Clients suivis", overview.clients || 0, "Clients distincts dans le scope"),
        card("À valider", overview.new || 0, "Tickets en attente d’action"),
        card("Envoyés", overview.sent || 0, "Réponses réellement parties"),
        card("Auto-envoyés", overview.auto_sent || 0, "Cas calmes et simples")
      ].join("");
    }

    function renderInbox() {
      const container = document.getElementById("inboxList");
      if (!state.inbox.length) {
        container.innerHTML = `<div class="empty">Aucun email inbox chargé pour le moment.</div>`;
        return;
      }
      container.innerHTML = state.inbox.map((item) => `
        <article class="inbox-item">
          <input type="checkbox" class="inbox-checkbox" data-id="${item.message_id}" ${state.selectedInboxIds.has(item.message_id) ? "checked" : ""} />
          <div>
            <h4>${escapeHtml(item.subject || "(Sans objet)")}</h4>
            <p>${escapeHtml(item.sender_email || item.sender || "Expéditeur inconnu")}</p>
            <div class="chips">
              ${badge(item.is_unread ? "Non lu" : "Lu", item.is_unread ? "warn" : "")}
              ${badge("Boîte Gmail")}
            </div>
          </div>
          <a class="link-button tertiary" href="${item.gmail_url}" target="_blank" rel="noreferrer">Ouvrir</a>
        </article>
      `).join("");
      container.querySelectorAll(".inbox-checkbox").forEach((checkbox) => {
        checkbox.addEventListener("change", () => {
          if (checkbox.checked) state.selectedInboxIds.add(checkbox.dataset.id);
          else state.selectedInboxIds.delete(checkbox.dataset.id);
        });
      });
    }

    function renderQueue() {
      const container = document.getElementById("queueList");
      const items = filteredItems();
      if (!items.length) {
        container.innerHTML = `<div class="empty">Aucun ticket ne correspond au filtre courant.</div>`;
        return;
      }
      container.innerHTML = items.map((item) => {
        const chips = [
          badge(labels[item.status] || item.status, item.status === "sent" ? "success" : item.status === "ignored" ? "warn" : ""),
          badge(item.complaint_category || "Autre"),
          badge(item.delivery_mode === "sent" ? "Envoyé réel" : item.delivery_mode === "draft" ? "Brouillon Gmail" : "En attente", item.delivery_mode === "sent" ? "success" : item.delivery_mode === "draft" ? "warn" : "")
        ];
        if (item.needs_human_validation) chips.push(badge("Validation humaine", "danger"));
        if (item.simple_request) chips.push(badge("Simple", "success"));
        return `
          <article class="ticket ${state.selectedId === item.message_id ? "active" : ""}" data-id="${item.message_id}">
            <h4>${escapeHtml(item.subject || "(Sans objet)")}</h4>
            <p>${escapeHtml(item.customer_name || item.sender_email || item.sender || "Client inconnu")}</p>
            <div class="chips">${chips.join("")}</div>
          </article>
        `;
      }).join("");
      container.querySelectorAll(".ticket").forEach((ticket) => {
        ticket.addEventListener("click", () => {
          state.selectedId = ticket.dataset.id;
          renderQueue();
          renderDetail();
        });
      });
    }

    function renderDashboard() {
      const categories = state.dashboard.categories || [];
      const categoryMax = Math.max(1, ...categories.map((item) => item.count));
      document.getElementById("categoryBars").innerHTML = categories.length ? categories.map((item) => `
        <div class="bar-row">
          <strong>${escapeHtml(item.category)}</strong>
          <div class="bar-track"><div class="bar-fill" style="width:${(item.count / categoryMax) * 100}%"></div></div>
          <span>${item.count}</span>
        </div>
      `).join("") : `<div class="empty">Aucune catégorie de plainte disponible.</div>`;

      const timeline = state.dashboard.timeline || [];
      const timelineMax = Math.max(1, ...timeline.map((item) => item.count));
      document.getElementById("timeline").innerHTML = timeline.length ? timeline.map((item) => `
        <div class="timeline-col">
          <span>${item.count}</span>
          <div class="timeline-bar" style="height:${Math.max(12, (item.count / timelineMax) * 140)}px"></div>
          <span>${escapeHtml((item.date || "").slice(5))}</span>
        </div>
      `).join("") : `<div class="empty">Aucune évolution disponible pour le moment.</div>`;

      const clients = state.dashboard.clients || [];
      document.getElementById("clientsTable").innerHTML = clients.length ? `
        <table>
          <thead>
            <tr>
              <th>Client</th>
              <th>Tickets</th>
              <th>Dernière catégorie</th>
              <th>Sentiment</th>
            </tr>
          </thead>
          <tbody>
            ${clients.map((item) => `
              <tr>
                <td>${escapeHtml(item.client)}${item.vip ? ` ${badge("VIP", "danger")}` : ""}<div class="muted small">${escapeHtml(item.email)}</div></td>
                <td>${item.tickets}</td>
                <td>${escapeHtml(item.last_category || "Autre")}</td>
                <td>${escapeHtml(item.last_sentiment || "N/A")}</td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      ` : `<div class="empty">Aucune donnée client exploitable pour le moment.</div>`;
    }

    function renderDetail() {
      const item = state.items.find((entry) => entry.message_id === state.selectedId);
      const title = document.getElementById("detailTitle");
      const meta = document.getElementById("detailMeta");
      const content = document.getElementById("detailContent");
      if (!item) {
        title.textContent = "Sélectionne un ticket";
        meta.textContent = "Aucun ticket sélectionné";
        content.className = "empty";
        content.innerHTML = "Choisis un ticket dans la file manager pour le travailler.";
        return;
      }
      title.textContent = item.subject || "(Sans objet)";
      meta.textContent = `${item.customer_email || item.sender_email || "Client inconnu"} · ${labels[item.status] || item.status}`;
      content.className = "";
      const chips = [
        badge(item.sentiment || "N/A", item.sentiment === "FURIEUX" ? "danger" : item.sentiment === "CALME" ? "success" : ""),
        badge(item.intent || "Intent inconnu"),
        badge(item.complaint_category || "Autre"),
        badge(item.delivery_mode === "sent" ? "Réponse envoyée" : item.delivery_mode === "draft" ? "Brouillon créé" : "À traiter", item.delivery_mode === "sent" ? "success" : item.delivery_mode === "draft" ? "warn" : "")
      ];
      if (item.needs_human_validation) chips.push(badge("Validation obligatoire", "danger"));
      if (item.simple_request) chips.push(badge("Demande simple", "success"));
      if (item.is_vip) chips.push(badge("VIP", "danger"));

      const sendDisabled = item.relevance === "irrelevant" || item.delivery_mode === "sent" || !item.reply_text;
      const draftDisabled = item.relevance === "irrelevant" || item.delivery_mode === "sent" || item.delivery_mode === "draft" || !item.reply_text;

      content.innerHTML = `
        <div class="detail-grid">
          <div class="stack">
            <section class="panel">
              <div class="section-head">
                <div>
                  <h3>Email reçu</h3>
                  <p>${escapeHtml(item.sender || item.sender_email || "Expéditeur inconnu")}</p>
                </div>
                <a class="link-button tertiary" href="${item.gmail_url || "#"}" target="_blank" rel="noreferrer">Ouvrir dans Gmail</a>
              </div>
              <div class="chips">${chips.join("")}</div>
              <div class="mail-body" style="margin-top:14px;">${escapeHtml(item.body || item.snippet || "")}</div>
            </section>

            <section class="panel">
              <div class="section-head">
                <div>
                  <h3>Réponse proposée</h3>
                  <p>${item.delivery_mode === "sent" ? "Réponse déjà envoyée" : item.delivery_mode === "draft" ? "Brouillon déjà généré" : "Prête à être envoyée ou transformée en brouillon"}</p>
                </div>
              </div>
              <div class="reply-box">${escapeHtml(item.reply_text || "Aucune réponse générée pour cet email.")}</div>
            </section>
          </div>

          <div class="stack">
            <section class="panel">
              <div class="section-head">
                <div>
                  <h3>Décision manager</h3>
                  <p>Mode réel: envoi direct possible depuis l’application.</p>
                </div>
              </div>
              <textarea id="managerNotes" placeholder="Notes internes, précisions, consignes commerciales...">${escapeHtml(item.manager_notes || "")}</textarea>
              <div class="actions">
                <button class="secondary" onclick="changeStatus('${item.message_id}', 'in_progress')">Prendre en charge</button>
                <button class="success" onclick="sendNow('${item.message_id}')" ${sendDisabled ? "disabled" : ""}>Envoyer maintenant</button>
                <button class="primary" onclick="createDraft('${item.message_id}')" ${draftDisabled ? "disabled" : ""}>Créer un brouillon</button>
                <button class="secondary" onclick="changeStatus('${item.message_id}', 'treated')">Marquer traité</button>
                <button class="danger" onclick="changeStatus('${item.message_id}', 'ignored')">Ignorer</button>
              </div>
            </section>

            <section class="panel">
              <div class="section-head">
                <div>
                  <h3>Contexte client</h3>
                  <p>${escapeHtml(item.customer_name || "Aucun client connu")}</p>
                </div>
              </div>
              <div class="small"><strong>Email</strong><div class="muted">${escapeHtml(item.customer_email || item.sender_email || "N/A")}</div></div>
              <div class="small" style="margin-top:10px;"><strong>Total achats</strong><div class="muted">${Number(item.total_achats || 0).toLocaleString("fr-FR")}</div></div>
              <div class="small" style="margin-top:10px;"><strong>Commandes</strong><div class="muted">${item.nombre_commandes || 0}</div></div>
              <div class="small" style="margin-top:10px;"><strong>Risque</strong><div class="muted">${escapeHtml(item.risk_level || "N/A")}</div></div>
              <div class="small" style="margin-top:10px;"><strong>Confiance IA</strong><div class="muted">${item.confidence == null ? "N/A" : Number(item.confidence).toFixed(2)}</div></div>
              <div class="small" style="margin-top:10px;"><strong>Motif d'escalade</strong><div class="muted">${escapeHtml(item.escalation_reason || "Aucun")}</div></div>
            </section>

            <section class="panel">
              <div class="section-head">
                <div>
                  <h3>Règles d’automatisation</h3>
                  <p>Seuls les cas calmes ou neutres et simples partent automatiquement.</p>
                </div>
              </div>
              <div class="chips">
                ${badge(item.simple_request ? "Simple" : "Complexe", item.simple_request ? "success" : "warn")}
                ${badge(item.sentiment || "N/A", item.sentiment === "FURIEUX" ? "danger" : "")}
                ${badge(item.needs_human_validation ? "Validation requise" : "Eligible auto si simple", item.needs_human_validation ? "danger" : "success")}
              </div>
              <div class="pre" style="margin-top:12px;">${escapeHtml(JSON.stringify(item.customer_json || {}, null, 2))}</div>
            </section>
          </div>
        </div>
      `;
    }

    async function loadInbox() {
      const payload = await api("/manager/api/inbox");
      state.inbox = payload.items || [];
      renderInbox();
    }

    async function loadQueue(selectFirst = false) {
      const payload = await api("/manager/api/items");
      state.items = payload.items || [];
      state.overview = payload.overview || {};
      state.dashboard = payload.dashboard || { categories: [], timeline: [], clients: [] };
      renderMetrics();
      renderDashboard();
      if (selectFirst && state.items.length && !state.selectedId) state.selectedId = state.items[0].message_id;
      if (state.selectedId && !state.items.some((item) => item.message_id === state.selectedId)) {
        state.selectedId = state.items[0]?.message_id || null;
      }
      renderQueue();
      renderDetail();
    }

    async function analyzeSelection() {
      const ids = selectedInboxArray();
      if (!ids.length) {
        alert("Sélectionne au moins un email dans la boîte Gmail.");
        return;
      }
      const button = document.getElementById("analyzeSelectedButton");
      button.disabled = true;
      button.textContent = "Analyse...";
      try {
        await api("/manager/api/sync", {
          method: "POST",
          body: JSON.stringify({ message_ids: ids })
        });
        state.selectedInboxIds.clear();
        await Promise.all([loadInbox(), loadQueue(true)]);
      } catch (error) {
        alert("Analyse impossible: " + error.message);
      } finally {
        button.disabled = false;
        button.textContent = "Analyser la sélection";
      }
    }

    async function syncUnread() {
      const button = document.getElementById("syncUnreadButton");
      button.disabled = true;
      button.textContent = "Analyse...";
      try {
        await api("/manager/api/sync", { method: "POST", body: JSON.stringify({ limit: 10 }) });
        await Promise.all([loadInbox(), loadQueue(true)]);
      } catch (error) {
        alert("Synchronisation impossible: " + error.message);
      } finally {
        button.disabled = false;
        button.textContent = "Analyser les non lus";
      }
    }

    async function changeStatus(messageId, status) {
      const notes = document.getElementById("managerNotes")?.value || "";
      try {
        await api(`/manager/api/items/${messageId}`, {
          method: "PATCH",
          body: JSON.stringify({ status, manager_notes: notes })
        });
        await loadQueue();
      } catch (error) {
        alert("Mise à jour impossible: " + error.message);
      }
    }

    async function createDraft(messageId) {
      const notes = document.getElementById("managerNotes")?.value || "";
      try {
        await api(`/manager/api/items/${messageId}/draft`, {
          method: "POST",
          body: JSON.stringify({ manager_notes: notes })
        });
        await loadQueue();
      } catch (error) {
        alert("Création du brouillon impossible: " + error.message);
      }
    }

    async function sendNow(messageId) {
      const notes = document.getElementById("managerNotes")?.value || "";
      try {
        await api(`/manager/api/items/${messageId}/send`, {
          method: "POST",
          body: JSON.stringify({ manager_notes: notes })
        });
        await loadQueue();
      } catch (error) {
        alert("Envoi impossible: " + error.message);
      }
    }

    document.getElementById("refreshInboxButton").addEventListener("click", () => loadInbox().catch((error) => alert(error.message)));
    document.getElementById("analyzeSelectedButton").addEventListener("click", analyzeSelection);
    document.getElementById("syncUnreadButton").addEventListener("click", syncUnread);
    document.getElementById("selectAllInboxButton").addEventListener("click", () => {
      const allSelected = state.inbox.length && state.selectedInboxIds.size === state.inbox.length;
      state.selectedInboxIds = allSelected ? new Set() : new Set(state.inbox.map((item) => item.message_id));
      renderInbox();
    });
    document.getElementById("searchInput").addEventListener("input", renderQueue);
    document.getElementById("statusFilter").addEventListener("change", renderQueue);

    Promise.all([loadInbox(), loadQueue(true)]).catch((error) => {
      document.getElementById("detailContent").className = "empty";
      document.getElementById("detailContent").textContent = "Chargement impossible: " + error.message;
    });
  </script>
</body>
</html>
"""


def render_privacy_policy() -> str:
    return """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Politique de confidentialite | ONEF</title>
  <style>
    :root {
      --panel: rgba(255, 255, 255, 0.94);
      --ink: #18212a;
      --accent: #0c7a67;
      --shadow: 0 20px 40px rgba(38, 43, 47, 0.12);
      --radius: 24px;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      color: var(--ink);
      font-family: "Avenir Next", "Segoe UI Variable", "Segoe UI", sans-serif;
      background:
        radial-gradient(circle at top left, rgba(12,122,103,0.16), transparent 28%),
        radial-gradient(circle at 85% 10%, rgba(209,123,35,0.12), transparent 20%),
        linear-gradient(180deg, #faf7f2 0%, #f2ece3 100%);
    }
    .shell {
      max-width: 920px;
      margin: 0 auto;
      padding: 36px 20px 56px;
    }
    .hero, .section {
      background: var(--panel);
      border: 1px solid rgba(255,255,255,0.7);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
    }
    .hero {
      padding: 28px;
      background: linear-gradient(145deg, #0b584c 0%, #0c7a67 58%, #28a191 100%);
      color: #fff;
      margin-bottom: 18px;
    }
    .eyebrow {
      text-transform: uppercase;
      letter-spacing: 0.14em;
      font-size: 11px;
      opacity: 0.8;
      margin-bottom: 10px;
    }
    h1, h2, p, li { margin: 0; }
    h1 { font-size: 32px; line-height: 1.1; }
    .hero p {
      margin-top: 12px;
      color: rgba(255,255,255,0.84);
      line-height: 1.55;
    }
    .section {
      padding: 24px;
      margin-bottom: 16px;
    }
    h2 {
      font-size: 18px;
      margin-bottom: 12px;
    }
    p, li {
      color: #334251;
      line-height: 1.7;
      font-size: 15px;
    }
    ul {
      margin: 0;
      padding-left: 20px;
    }
    .meta {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 16px;
    }
    .pill {
      display: inline-flex;
      align-items: center;
      padding: 8px 12px;
      border-radius: 999px;
      background: rgba(255,255,255,0.14);
      border: 1px solid rgba(255,255,255,0.18);
      font-size: 13px;
    }
    a {
      color: var(--accent);
      text-decoration: none;
      font-weight: 600;
    }
    a:hover { text-decoration: underline; }
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <div class="eyebrow">ONEF Customer Success AI</div>
      <h1>Politique de confidentialite</h1>
      <p>Derniere mise a jour : 15 avril 2026. Cette page explique comment l'application collecte, utilise et protege les donnees traitees dans le cadre de l'assistance client.</p>
      <div class="meta">
        <span class="pill">URL publique : /privacy</span>
        <span class="pill">Contact : support interne ONEF</span>
      </div>
    </section>
    <section class="section">
      <h2>Donnees traitees</h2>
      <p>L'application peut traiter les emails recus dans Gmail, les informations clients disponibles dans Google Sheets, ainsi que les brouillons ou reponses prepares pour le support client.</p>
    </section>
    <section class="section">
      <h2>Utilisation des donnees</h2>
      <ul>
        <li>Lire et analyser les messages entrants.</li>
        <li>Rechercher un contexte client dans une feuille Google Sheets.</li>
        <li>Generer des suggestions de reponse ou envoyer une reponse selon la configuration activee.</li>
        <li>Afficher un suivi operationnel dans la console manager.</li>
      </ul>
    </section>
    <section class="section">
      <h2>Partage et acces</h2>
      <p>Les donnees sont utilisees uniquement pour le fonctionnement de l'application et l'automatisation du support client. L'acces depend des services configures par l'exploitant, notamment Gmail, Google Sheets et, si active, une API de modele externe.</p>
    </section>
    <section class="section">
      <h2>Conservation</h2>
      <p>Les donnees conservees par l'application dependent de l'environnement de deploiement. En l'etat, certains elements de file manager peuvent etre stockes localement via SQLite, avec une persistance qui peut etre limitee sur certains hebergeurs.</p>
    </section>
    <section class="section">
      <h2>Droits et demandes</h2>
      <p>Pour toute question sur les donnees, leur suppression ou leur mise a jour, l'utilisateur doit contacter l'exploitant du service ONEF. Voir aussi les <a href="/terms">conditions d'utilisation</a>.</p>
    </section>
  </main>
</body>
</html>
"""


def render_terms_of_service() -> str:
    return """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Conditions d'utilisation | ONEF</title>
  <style>
    :root {
      --panel: rgba(255, 255, 255, 0.94);
      --ink: #18212a;
      --accent: #0c7a67;
      --shadow: 0 20px 40px rgba(38, 43, 47, 0.12);
      --radius: 24px;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      color: var(--ink);
      font-family: "Avenir Next", "Segoe UI Variable", "Segoe UI", sans-serif;
      background:
        radial-gradient(circle at top left, rgba(12,122,103,0.16), transparent 28%),
        radial-gradient(circle at 85% 10%, rgba(209,123,35,0.12), transparent 20%),
        linear-gradient(180deg, #faf7f2 0%, #f2ece3 100%);
    }
    .shell {
      max-width: 920px;
      margin: 0 auto;
      padding: 36px 20px 56px;
    }
    .hero, .section {
      background: rgba(255, 255, 255, 0.94);
      border: 1px solid rgba(255,255,255,0.7);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
    }
    .hero {
      padding: 28px;
      background: linear-gradient(145deg, #18212a 0%, #264252 62%, #37657a 100%);
      color: #fff;
      margin-bottom: 18px;
    }
    .eyebrow {
      text-transform: uppercase;
      letter-spacing: 0.14em;
      font-size: 11px;
      opacity: 0.8;
      margin-bottom: 10px;
    }
    h1, h2, p, li { margin: 0; }
    h1 { font-size: 32px; line-height: 1.1; }
    .hero p {
      margin-top: 12px;
      color: rgba(255,255,255,0.84);
      line-height: 1.55;
    }
    .section {
      padding: 24px;
      margin-bottom: 16px;
    }
    h2 {
      font-size: 18px;
      margin-bottom: 12px;
    }
    p, li {
      color: #334251;
      line-height: 1.7;
      font-size: 15px;
    }
    ul {
      margin: 0;
      padding-left: 20px;
    }
    .meta {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 16px;
    }
    .pill {
      display: inline-flex;
      align-items: center;
      padding: 8px 12px;
      border-radius: 999px;
      background: rgba(255,255,255,0.14);
      border: 1px solid rgba(255,255,255,0.18);
      font-size: 13px;
    }
    a {
      color: var(--accent);
      text-decoration: none;
      font-weight: 600;
    }
    a:hover { text-decoration: underline; }
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <div class="eyebrow">ONEF Customer Success AI</div>
      <h1>Conditions d'utilisation</h1>
      <p>Derniere mise a jour : 15 avril 2026. Ces conditions encadrent l'utilisation de l'application de gestion et d'automatisation du support client.</p>
      <div class="meta">
        <span class="pill">URL publique : /terms</span>
        <span class="pill">Service : ONEF</span>
      </div>
    </section>
    <section class="section">
      <h2>Objet du service</h2>
      <p>L'application permet de consulter des emails, d'analyser des demandes clients, de proposer des reponses et, selon la configuration, d'envoyer certaines reponses automatiquement.</p>
    </section>
    <section class="section">
      <h2>Responsabilites</h2>
      <ul>
        <li>L'exploitant reste responsable de la configuration, des acces Google et des regles metier appliquees.</li>
        <li>L'utilisateur doit verifier que les automatisations actives sont adaptees a son contexte operationnel.</li>
        <li>Les contenus generes automatiquement doivent etre revus si le niveau de risque ou le contexte l'exige.</li>
      </ul>
    </section>
    <section class="section">
      <h2>Disponibilite et limites</h2>
      <p>Le service depend de composants tiers et d'un environnement de deploiement pouvant imposer des limites de disponibilite, de stockage ou d'execution. Aucune disponibilite continue n'est garantie.</p>
    </section>
    <section class="section">
      <h2>Utilisation acceptable</h2>
      <p>Il est interdit d'utiliser l'application pour un traitement illicite, trompeur ou non autorise des donnees, ou pour envoyer des communications qui contreviennent aux obligations legales applicables.</p>
    </section>
    <section class="section">
      <h2>Confidentialite</h2>
      <p>L'utilisation du service implique le traitement de donnees professionnelles et potentiellement personnelles. Les modalites associees sont decrites dans la <a href="/privacy">politique de confidentialite</a>.</p>
    </section>
  </main>
</body>
</html>
"""
