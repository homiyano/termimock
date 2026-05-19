from __future__ import annotations


HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Termimock</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f6f7f9;
      --panel: #ffffff;
      --text: #18202b;
      --muted: #687384;
      --line: #d9dee7;
      --accent: #0f766e;
      --accent-dark: #115e59;
      --danger: #b42318;
      --shadow: 0 8px 24px rgba(22, 32, 43, 0.08);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font: 14px/1.45 ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--text);
    }
    header {
      height: 56px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 20px;
      background: #18202b;
      color: #fff;
    }
    header strong { font-size: 16px; }
    header span { color: #c6d1df; }
    main {
      display: grid;
      grid-template-columns: minmax(360px, 0.92fr) minmax(420px, 1.08fr);
      gap: 16px;
      padding: 16px;
      min-height: calc(100vh - 56px);
    }
    section {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
      min-width: 0;
    }
    .section-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 12px;
      border-bottom: 1px solid var(--line);
    }
    h1, h2 { margin: 0; font-size: 15px; }
    .toolbar { display: flex; gap: 8px; align-items: center; }
    button, select, input, textarea {
      font: inherit;
    }
    button {
      border: 1px solid var(--line);
      background: #fff;
      color: var(--text);
      border-radius: 6px;
      min-height: 34px;
      padding: 6px 10px;
      cursor: pointer;
    }
    button.primary {
      background: var(--accent);
      color: #fff;
      border-color: var(--accent);
    }
    button.primary:hover { background: var(--accent-dark); }
    button.danger { color: var(--danger); }
    button:disabled { opacity: 0.5; cursor: not-allowed; }
    .routes {
      display: grid;
      gap: 8px;
      padding: 12px;
      max-height: calc(100vh - 170px);
      overflow: auto;
    }
    .route {
      display: grid;
      grid-template-columns: 72px 1fr 52px;
      gap: 8px;
      align-items: center;
      padding: 10px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      cursor: pointer;
    }
    .route.active { border-color: var(--accent); box-shadow: inset 0 0 0 1px var(--accent); }
    .method { font-weight: 700; color: var(--accent-dark); }
    .path { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .status { color: var(--muted); text-align: right; }
    .muted { color: var(--muted); }
    .editor {
      display: grid;
      grid-template-columns: repeat(6, 1fr);
      gap: 12px;
      padding: 12px;
    }
    label {
      display: grid;
      gap: 5px;
      color: var(--muted);
      font-size: 12px;
      font-weight: 600;
    }
    input, select, textarea {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 8px;
      color: var(--text);
      background: #fff;
    }
    textarea {
      min-height: 160px;
      resize: vertical;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 13px;
    }
    .span-1 { grid-column: span 1; }
    .span-2 { grid-column: span 2; }
    .span-3 { grid-column: span 3; }
    .span-6 { grid-column: span 6; }
    .logs {
      border-top: 1px solid var(--line);
      padding: 12px;
    }
    .log-list {
      display: grid;
      gap: 6px;
      max-height: 180px;
      overflow: auto;
      margin-top: 8px;
    }
    .log {
      display: grid;
      grid-template-columns: 70px 1fr 52px 50px;
      gap: 8px;
      border-bottom: 1px solid #edf0f4;
      padding: 6px 0;
    }
    @media (max-width: 900px) {
      main { grid-template-columns: 1fr; }
      .routes { max-height: 320px; }
      .span-1, .span-2, .span-3 { grid-column: span 6; }
    }
  </style>
</head>
<body>
  <header>
    <strong>Termimock</strong>
    <span id="status">Loading...</span>
  </header>
  <main>
    <section>
      <div class="section-head">
        <h1>Routes</h1>
        <div class="toolbar">
          <button id="add">Add</button>
          <button class="primary" id="save">Save</button>
        </div>
      </div>
      <div class="routes" id="routes"></div>
    </section>
    <section>
      <div class="section-head">
        <h2>Editor</h2>
        <div class="toolbar">
          <button id="duplicate">Duplicate</button>
          <button class="danger" id="delete">Delete</button>
        </div>
      </div>
      <form class="editor" id="editor">
        <label class="span-1">Method
          <select id="method">
            <option>GET</option><option>POST</option><option>PUT</option><option>PATCH</option>
            <option>DELETE</option><option>OPTIONS</option><option>HEAD</option>
          </select>
        </label>
        <label class="span-3">Path
          <input id="path" placeholder="/api/users/:id">
        </label>
        <label class="span-1">Status
          <input id="statusCode" type="number" min="100" max="599">
        </label>
        <label class="span-1">Delay ms
          <input id="delay" type="number" min="0">
        </label>
        <label class="span-2">Content type
          <input id="contentType">
        </label>
        <label class="span-2">Response mode
          <select id="responseMode">
            <option>first</option><option>cycle</option><option>random</option>
          </select>
        </label>
        <label class="span-2">Enabled
          <select id="enabled"><option value="true">true</option><option value="false">false</option></select>
        </label>
        <label class="span-6">Body match JSON
          <textarea id="bodyMatch" spellcheck="false" placeholder="{&quot;email&quot;:&quot;admin@test.com&quot;}"></textarea>
        </label>
        <label class="span-6">Response body
          <textarea id="body" spellcheck="false" placeholder="{&quot;id&quot;:&quot;{{params.id}}&quot;}"></textarea>
        </label>
      </form>
      <div class="logs">
        <div class="section-head" style="padding:0;border:0;">
          <h2>Requests</h2>
          <button id="refreshLogs">Refresh</button>
        </div>
        <div class="log-list" id="logs"></div>
      </div>
    </section>
  </main>
  <script>
    let routes = [];
    let selected = 0;
    const $ = (id) => document.getElementById(id);

    function emptyRoute() {
      return {
        method: "GET",
        path: "/api/example",
        status: 200,
        content_type: "application/json",
        headers: {},
        body: "{\\\"ok\\\":true}",
        enabled: true,
        delay_ms: 0,
        responses: [],
        response_mode: "first",
        body_match: {}
      };
    }

    async function load() {
      const res = await fetch("/_termimock/api/routes");
      const data = await res.json();
      routes = data.routes || [];
      selected = Math.min(selected, Math.max(routes.length - 1, 0));
      renderRoutes();
      renderEditor();
      loadLogs();
      $("status").textContent = `${routes.length} routes`;
    }

    async function save() {
      syncEditor();
      const res = await fetch("/_termimock/api/routes", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({routes})
      });
      if (!res.ok) {
        $("status").textContent = await res.text();
        return;
      }
      $("status").textContent = "Saved";
      await load();
    }

    function renderRoutes() {
      const root = $("routes");
      root.innerHTML = "";
      if (!routes.length) {
        root.innerHTML = '<div class="muted">No routes yet.</div>';
        return;
      }
      routes.forEach((route, index) => {
        const el = document.createElement("div");
        el.className = `route ${index === selected ? "active" : ""}`;
        el.innerHTML = `<div class="method">${route.method}</div><div class="path">${route.path}</div><div class="status">${route.status}</div>`;
        el.onclick = () => { syncEditor(); selected = index; renderRoutes(); renderEditor(); };
        root.appendChild(el);
      });
    }

    function renderEditor() {
      const route = routes[selected];
      for (const id of ["method", "path", "statusCode", "delay", "contentType", "responseMode", "enabled", "bodyMatch", "body"]) {
        $(id).disabled = !route;
      }
      $("duplicate").disabled = !route;
      $("delete").disabled = !route;
      if (!route) return;
      $("method").value = route.method || "GET";
      $("path").value = route.path || "/";
      $("statusCode").value = route.status || 200;
      $("delay").value = route.delay_ms || 0;
      $("contentType").value = route.content_type || "application/json";
      $("responseMode").value = route.response_mode || "first";
      $("enabled").value = String(route.enabled !== false);
      $("bodyMatch").value = JSON.stringify(route.body_match || {}, null, 2);
      $("body").value = route.body || "{}";
    }

    function syncEditor() {
      const route = routes[selected];
      if (!route) return;
      route.method = $("method").value;
      route.path = $("path").value || "/";
      route.status = Number($("statusCode").value || 200);
      route.delay_ms = Number($("delay").value || 0);
      route.content_type = $("contentType").value || "application/json";
      route.response_mode = $("responseMode").value || "first";
      route.enabled = $("enabled").value === "true";
      route.body = $("body").value || "{}";
      try {
        route.body_match = JSON.parse($("bodyMatch").value || "{}");
      } catch {
        $("status").textContent = "Body match must be valid JSON";
      }
    }

    async function loadLogs() {
      const res = await fetch("/_termimock/api/logs");
      const data = await res.json();
      const root = $("logs");
      root.innerHTML = "";
      (data.logs || []).forEach((log) => {
        const el = document.createElement("div");
        el.className = "log";
        el.innerHTML = `<strong>${log.method}</strong><span>${log.path}</span><span>${log.status}</span><span>${log.matched ? "hit" : "miss"}</span>`;
        root.appendChild(el);
      });
      if (!root.innerHTML) root.innerHTML = '<div class="muted">No requests yet.</div>';
    }

    $("add").onclick = () => { syncEditor(); routes.push(emptyRoute()); selected = routes.length - 1; renderRoutes(); renderEditor(); };
    $("duplicate").onclick = () => { syncEditor(); routes.splice(selected + 1, 0, JSON.parse(JSON.stringify(routes[selected]))); selected += 1; renderRoutes(); renderEditor(); };
    $("delete").onclick = () => { routes.splice(selected, 1); selected = Math.max(0, selected - 1); renderRoutes(); renderEditor(); };
    $("save").onclick = save;
    $("refreshLogs").onclick = loadLogs;
    $("editor").oninput = () => { syncEditor(); renderRoutes(); };
    setInterval(loadLogs, 2000);
    load();
  </script>
</body>
</html>
"""
