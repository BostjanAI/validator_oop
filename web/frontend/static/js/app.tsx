/*
 * IPO Excel Validator – spletni vmesnik (React, brez build koraka).
 * Komunicira z FastAPI backendom; vsa validacijska logika je na strežniku
 * (obstoječi ValidatorEngine). Ta datoteka je samo predstavitvena plast.
 *
 * Faza 2: prijava (AD/LDAP ali lokalni uporabnik), zgodovina validacij,
 * diff dveh verzij recepture, audit trail in napredek v realnem času
 * (WebSocket s fallbackom na polling).
 */

const { useState, useEffect, useRef, useMemo, useCallback } = React;

/* ----------------------------- API klient ------------------------------ */

async function apiFetch(url, options) {
  const res = await fetch(url, options);
  if (res.status === 401) {
    // Seja je potekla → obvesti aplikacijo, da pokaže prijavo
    window.dispatchEvent(new Event("mes-unauthorized"));
    const err = await res.json().catch(() => ({ detail: "Prijava je obvezna." }));
    throw new Error(err.detail || "Prijava je obvezna.");
  }
  return res;
}

const API = {
  async getRules() {
    const res = await apiFetch("/api/rules");
    if (!res.ok) throw new Error("Napaka pri nalaganju pravil");
    return res.json();
  },
  async me() {
    const res = await fetch("/api/auth/me");
    if (!res.ok) throw new Error("Napaka pri preverjanju prijave");
    return res.json();
  },
  async login(username, password) {
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Prijava ni uspela" }));
      throw new Error(err.detail || "Prijava ni uspela");
    }
    return res.json();
  },
  async logout() {
    await fetch("/api/auth/logout", { method: "POST" });
  },
  async startValidation(recipes, config, optional) {
    const fd = new FormData();
    recipes.forEach((f) => fd.append("recipes", f, f.name));
    fd.append("config", JSON.stringify(config));
    if (optional.sop) fd.append("sop", optional.sop, optional.sop.name);
    if (optional.raztopine) fd.append("catalog_raztopine", optional.raztopine, optional.raztopine.name);
    if (optional.kemikalije) fd.append("catalog_kemikalije", optional.kemikalije, optional.kemikalije.name);
    if (optional.repro) fd.append("catalog_repro", optional.repro, optional.repro.name);
    const res = await apiFetch("/api/validate", { method: "POST", body: fd });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Napaka pri zagonu validacije" }));
      throw new Error(err.detail || "Napaka pri zagonu validacije");
    }
    return res.json();
  },
  async jobStatus(jobId) {
    const res = await apiFetch(`/api/jobs/${jobId}`);
    if (!res.ok) throw new Error("Napaka pri branju stanja");
    return res.json();
  },
  async jobResults(jobId) {
    const res = await apiFetch(`/api/jobs/${jobId}/results`);
    if (!res.ok) throw new Error("Napaka pri branju rezultatov");
    return res.json();
  },
  reportUrl(jobId, fileIndex, filename) {
    return `/api/jobs/${jobId}/files/${fileIndex}/report/${encodeURIComponent(filename)}`;
  },
  combinedReportUrl(jobId, filename) {
    return `/api/jobs/${jobId}/report/${encodeURIComponent(filename)}`;
  },
  wsJobUrl(jobId) {
    const proto = location.protocol === "https:" ? "wss" : "ws";
    return `${proto}://${location.host}/api/ws/jobs/${jobId}`;
  },
  async history(limit, offset) {
    const res = await apiFetch(`/api/history?limit=${limit}&offset=${offset}`);
    if (!res.ok) throw new Error("Napaka pri nalaganju zgodovine");
    return res.json();
  },
  async historyDetail(jobId) {
    const res = await apiFetch(`/api/history/${jobId}`);
    if (!res.ok) throw new Error("Napaka pri nalaganju vnosa zgodovine");
    return res.json();
  },
  historyReportUrl(jobId, fileIndex, filename) {
    return `/api/history/${jobId}/files/${fileIndex}/report/${encodeURIComponent(filename)}`;
  },
  historyCombinedReportUrl(jobId, filename) {
    return `/api/history/${jobId}/report/${encodeURIComponent(filename)}`;
  },
  async diff(sideA, sideB) {
    const fd = new FormData();
    if (sideA.file) fd.append("file_a", sideA.file, sideA.file.name);
    if (sideA.historyId) {
      fd.append("history_a", sideA.historyId);
      fd.append("history_a_file", sideA.historyFile);
    }
    if (sideB.file) fd.append("file_b", sideB.file, sideB.file.name);
    if (sideB.historyId) {
      fd.append("history_b", sideB.historyId);
      fd.append("history_b_file", sideB.historyFile);
    }
    const res = await apiFetch("/api/diff", { method: "POST", body: fd });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Primerjava verzij ni uspela" }));
      throw new Error(err.detail || "Primerjava verzij ni uspela");
    }
    return res.json();
  },
  async audit(limit, offset, username, action) {
    const params = new URLSearchParams({ limit, offset });
    if (username) params.set("username", username);
    if (action) params.set("action", action);
    const res = await apiFetch(`/api/audit?${params}`);
    if (!res.ok) {
      if (res.status === 403) throw new Error("Nimaš pravic za vpogled v revizijsko sled.");
      throw new Error("Napaka pri nalaganju revizijske sledi");
    }
    return res.json();
  },
};

/* ----------------------------- Pomožno --------------------------------- */

const STATE_LABEL = { queued: "čaka", running: "v teku", done: "končano", error: "napaka" };

function classNames(...parts) {
  return parts.filter(Boolean).join(" ");
}

function bytesToHuman(n) {
  if (n < 1024) return n + " B";
  if (n < 1024 * 1024) return (n / 1024).toFixed(1) + " KB";
  return (n / (1024 * 1024)).toFixed(1) + " MB";
}

function formatDateTime(iso) {
  if (!iso) return "";
  try {
    const d = new Date(iso);
    return d.toLocaleDateString("sl-SI") + " " + d.toLocaleTimeString("sl-SI", { hour: "2-digit", minute: "2-digit" });
  } catch {
    return iso;
  }
}

/* --------------------------- File picker ------------------------------- */

function FilePicker({ accept, multiple, files, onChange, label, hint }) {
  const inputRef = useRef(null);
  const [drag, setDrag] = useState(false);

  const handleFiles = (fileList) => {
    let arr = Array.from(fileList || []);
    // Drag & drop ne upošteva atributa accept – filtriramo po končnici
    if (accept) {
      const allowed = accept.split(",").map((s) => s.trim().toLowerCase());
      arr = arr.filter((f) => allowed.some((ext) => f.name.toLowerCase().endsWith(ext)));
    }
    if (!arr.length) return;
    if (multiple) {
      const existing = new Set((files || []).map((f) => f.name + f.size));
      const merged = [...(files || [])];
      arr.forEach((f) => {
        if (!existing.has(f.name + f.size)) merged.push(f);
      });
      onChange(merged);
    } else {
      onChange(arr[0]);
    }
  };

  return (
    <div
      className={classNames("dropzone", drag && "drag")}
      onClick={() => inputRef.current && inputRef.current.click()}
      onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
      onDragLeave={() => setDrag(false)}
      onDrop={(e) => { e.preventDefault(); setDrag(false); handleFiles(e.dataTransfer.files); }}
    >
      <div><strong>{label}</strong></div>
      <div className="hint">{hint}</div>
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        multiple={multiple}
        style={{ display: "none" }}
        onChange={(e) => { handleFiles(e.target.files); e.target.value = ""; }}
      />
    </div>
  );
}

/* ---------------------------- Collapsible ------------------------------ */

function Collapsible({ title, children, defaultOpen }) {
  const [open, setOpen] = useState(!!defaultOpen);
  return (
    <div>
      <div className={classNames("collapsible-head", open && "open")} onClick={() => setOpen(!open)}>
        <span className="chev">▶</span> {title}
      </div>
      {open && <div style={{ paddingTop: 8 }}>{children}</div>}
    </div>
  );
}

/* ---------------------------- Upload card ------------------------------ */

function UploadCard({ state, set }) {
  return (
    <div className="card">
      <div className="card-head"><h2><span className="step">1</span> Datoteke</h2></div>
      <div className="card-body">
        <FilePicker
          multiple
          accept=".xlsx,.xlsm"
          files={state.recipes}
          onChange={(f) => set({ recipes: f })}
          label="Povleci recepture sem ali klikni za izbiro"
          hint="Podprto: .xlsx, .xlsm (več datotek hkrati)"
        />
        {state.recipes.length > 0 && (
          <ul className="file-list">
            {state.recipes.map((f, i) => (
              <li key={f.name + i}>
                <span className="fname">📄 {f.name} <span className="muted">({bytesToHuman(f.size)})</span></span>
                <button
                  className="remove"
                  title="Odstrani"
                  onClick={() => set({ recipes: state.recipes.filter((_, j) => j !== i) })}
                >×</button>
              </li>
            ))}
          </ul>
        )}

        <div style={{ marginTop: 16 }} className="optional-files">
          <Collapsible title="Dodatne datoteke (SOP, šifranti)">
            <OptionalFile label="SOP dokument (.docx)" accept=".docx" file={state.sop}
              onChange={(f) => set({ sop: f })} onClear={() => set({ sop: null })} />
            <OptionalFile label="Šifrant raztopin (.xlsx)" accept=".xlsx" file={state.raztopine}
              onChange={(f) => set({ raztopine: f })} onClear={() => set({ raztopine: null })} />
            <OptionalFile label="Šifrant kemikalij (.xlsx)" accept=".xlsx" file={state.kemikalije}
              onChange={(f) => set({ kemikalije: f })} onClear={() => set({ kemikalije: null })} />
            <OptionalFile label="Šifrant repro materiala (.xlsx)" accept=".xlsx" file={state.repro}
              onChange={(f) => set({ repro: f })} onClear={() => set({ repro: null })} />
          </Collapsible>
        </div>
      </div>
    </div>
  );
}

function OptionalFile({ label, accept, file, onChange, onClear }) {
  const inputRef = useRef(null);
  return (
    <div className="field">
      <label>{label}</label>
      {file ? (
        <ul className="file-list" style={{ margin: 0 }}>
          <li>
            <span className="fname">📎 {file.name}</span>
            <button className="remove" onClick={onClear} title="Odstrani">×</button>
          </li>
        </ul>
      ) : (
        <button className="btn btn-sm" onClick={() => inputRef.current && inputRef.current.click()}>
          Izberi datoteko
        </button>
      )}
      <input ref={inputRef} type="file" accept={accept} style={{ display: "none" }}
        onChange={(e) => { if (e.target.files[0]) onChange(e.target.files[0]); e.target.value = ""; }} />
    </div>
  );
}

/* ----------------------------- Run card -------------------------------- */

function RunCard({ canRun, phase, onRun, status, live }) {
  const running = phase === "running";
  return (
    <div className="card">
      <div className="card-head">
        <h2><span className="step">2</span> Validacija</h2>
        {running && live && <span className="live-badge" title="Napredek v realnem času (WebSocket)">⚡ v živo</span>}
      </div>
      <div className="card-body">
        <button className="btn btn-primary btn-block" disabled={!canRun || running} onClick={onRun}>
          {running ? <><span className="spinner"></span> Validacija poteka…</> : "▶ Zaženi validacijo"}
        </button>
        {status && (
          <div className="progress-wrap">
            <div className="progress-bar">
              <div className="fill" style={{ width: `${Math.round((status.progress || 0) * 100)}%` }}></div>
            </div>
            <div className="progress-meta">
              <span>{status.message || "…"}</span>
              <span>{status.processed_files}/{status.total_files}</span>
            </div>
            {status.files && status.files.length > 1 && (
              <ul className="file-list" style={{ marginTop: 10 }}>
                {status.files.map((f) => (
                  <li key={f.index}>
                    <span className="fname">{f.filename}</span>
                    <span className={classNames("state", f.state)}>{STATE_LABEL[f.state] || f.state}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

/* --------------------------- Results panel ----------------------------- */

function ResultsPanel({ results, reportUrlFn, combinedUrlFn, onReset, title }) {
  const [search, setSearch] = useState("");
  const [fileFilter, setFileFilter] = useState("all");
  const [sheetFilter, setSheetFilter] = useState("all");
  const [codeFilter, setCodeFilter] = useState("all");
  const [grouping, setGrouping] = useState("sheet");
  const [sort, setSort] = useState(null); // { key, dir }
  const [showChart, setShowChart] = useState(false);

  const allIssues = useMemo(() => {
    const out = [];
    (results.files || []).forEach((fr) => {
      (fr.issues || []).forEach((iss) => out.push({ ...iss, _fileIndex: fr.index }));
    });
    return out;
  }, [results]);

  const fileNames = useMemo(() => (results.files || []).map((f) => f.filename), [results]);
  const sheetNames = useMemo(
    () => Array.from(new Set(allIssues.map((i) => i.sheet).filter(Boolean))).sort(),
    [allIssues]
  );
  const codeNames = useMemo(
    () => Array.from(new Set(allIssues.map((i) => i.code).filter(Boolean))).sort(),
    [allIssues]
  );

  const hasFilter = search || fileFilter !== "all" || sheetFilter !== "all" || codeFilter !== "all";
  const resetFilters = () => {
    setSearch(""); setFileFilter("all"); setSheetFilter("all"); setCodeFilter("all");
  };

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return allIssues.filter((iss) => {
      if (fileFilter !== "all" && iss.file !== fileFilter) return false;
      if (sheetFilter !== "all" && iss.sheet !== sheetFilter) return false;
      if (codeFilter !== "all" && iss.code !== codeFilter) return false;
      if (q) {
        const hay = `${iss.sheet} ${iss.code} ${iss.code_desc} ${iss.message} ${iss.row} ${iss.col}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }, [allIssues, search, fileFilter, sheetFilter, codeFilter]);

  const sorted = useMemo(() => sortIssues(filtered, sort), [filtered, sort]);
  const groups = useMemo(() => buildGroups(sorted, grouping), [sorted, grouping]);
  const totals = results.totals || {};
  const excelCombined = (results.combined_reports || []).filter((rep) => rep.kind === "excel");

  return (
    <div className="card">
      <div className="card-head">
        <h2>{title || "📊 Rezultati validacije"}</h2>
        <span className="muted">{filtered.length} prikazanih / {allIssues.length} skupaj</span>
      </div>
      <div className="card-body">
        <div className="summary-tiles" style={{ gridTemplateColumns: "minmax(160px, 220px)" }}>
          <div className="tile files static">
            <div className="num">{totals.invalid_files || 0}/{totals.files || 0}</div>
            <div className="lbl">Neveljavnih datotek</div>
          </div>
        </div>

        {excelCombined.length > 0 && (
          <div className="combined-reports">
            <div className="cr-title">📦 Skupna poročila za vse datoteke</div>
            <div className="downloads">
              {excelCombined.map((rep) => (
                <a key={rep.kind} className="btn btn-sm"
                  href={combinedUrlFn(rep.filename)} download>
                  ⬇ {rep.label}
                </a>
              ))}
            </div>
          </div>
        )}

        <DownloadSection results={results} reportUrlFn={reportUrlFn} />

        <div className="toolbar">
          <input type="text" placeholder="🔎 Iskanje po sporočilu, listu, kodi…"
            value={search} onChange={(e) => setSearch(e.target.value)} />
          {sheetNames.length > 1 && (
            <select value={sheetFilter} onChange={(e) => setSheetFilter(e.target.value)}>
              <option value="all">Vsi listi</option>
              {sheetNames.map((n) => <option key={n} value={n}>{n}</option>)}
            </select>
          )}
          {codeNames.length > 1 && (
            <select value={codeFilter} onChange={(e) => setCodeFilter(e.target.value)}>
              <option value="all">Vse kode</option>
              {codeNames.map((n) => <option key={n} value={n}>{n}</option>)}
            </select>
          )}
          {fileNames.length > 1 && (
            <select value={fileFilter} onChange={(e) => setFileFilter(e.target.value)}>
              <option value="all">Vse datoteke</option>
              {fileNames.map((n) => <option key={n} value={n}>{n}</option>)}
            </select>
          )}
          {hasFilter && (
            <button className="link-btn" onClick={resetFilters}>Počisti filtre</button>
          )}
        </div>

        <div className="toolbar">
          <div className="seg">
            {[["sheet", "Po listu"], ["code", "Po kodi"], ["file", "Po datoteki"], ["none", "Brez"]].map(([k, lbl]) => (
              <button key={k} className={classNames(grouping === k && "active")} onClick={() => setGrouping(k)}>{lbl}</button>
            ))}
          </div>
          <button className="link-btn" onClick={() => setShowChart(!showChart)}>
            {showChart ? "Skrij graf po kodah" : "Pokaži graf po kodah"}
          </button>
          {onReset && (
            <button className="btn btn-sm btn-dark" style={{ marginLeft: "auto" }} onClick={onReset}>
              ⟲ Nova validacija
            </button>
          )}
        </div>

        {showChart && <CodeChart issues={filtered} onSelect={(c) => setCodeFilter(codeFilter === c ? "all" : c)} />}

        {filtered.length === 0 ? (
          <div className="empty"><div className="ic">✓</div><p>Ni napak za prikaz s temi filtri.</p></div>
        ) : (
          <IssuesTable
            groups={groups}
            grouped={grouping !== "none"}
            multiFile={fileNames.length > 1}
            sort={sort}
            onSort={setSort}
          />
        )}
      </div>
    </div>
  );
}

/* Preprost CSS stolpčni graf – top kode napak (brez zunanjih knjižnic). */
function CodeChart({ issues, onSelect }) {
  const data = useMemo(() => {
    const map = new Map();
    issues.forEach((iss) => {
      if (!iss.code) return;
      const cur = map.get(iss.code) || { count: 0, severity: iss.severity, desc: iss.code_desc };
      cur.count += 1;
      if (iss.severity === "error") cur.severity = "error";
      map.set(iss.code, cur);
    });
    return Array.from(map.entries())
      .sort((a, b) => b[1].count - a[1].count)
      .slice(0, 12);
  }, [issues]);

  if (data.length === 0) return null;
  const max = data[0][1].count;
  return (
    <div className="code-chart">
      {data.map(([code, info]) => (
        <div className="row" key={code} style={{ cursor: "pointer" }}
          onClick={() => onSelect && onSelect(code)}
          title={info.desc || code}>
          <span className="label"><code>{code}</code></span>
          <div className="bar-wrap">
            <div className={classNames("bar", info.severity)} style={{ width: `${(info.count / max) * 100}%` }}></div>
          </div>
          <span className="count">{info.count}</span>
        </div>
      ))}
    </div>
  );
}

const SORT_KEYS = {
  file: (iss) => iss.file || "",
  sheet: (iss) => iss.sheet || "",
  row: (iss) => (typeof iss.row === "number" ? iss.row : Number(iss.row) || 0),
  code: (iss) => iss.code || "",
  message: (iss) => iss.message || "",
};

function sortIssues(issues, sort) {
  if (!sort || !SORT_KEYS[sort.key]) return issues;
  const keyFn = SORT_KEYS[sort.key];
  const dir = sort.dir === "desc" ? -1 : 1;
  return [...issues].sort((a, b) => {
    const ka = keyFn(a), kb = keyFn(b);
    if (ka < kb) return -dir;
    if (ka > kb) return dir;
    return 0;
  });
}

function buildGroups(issues, grouping) {
  if (grouping === "none") return [{ key: "all", label: "", issues }];
  const map = new Map();
  const keyOf = (iss) => {
    if (grouping === "sheet") return iss.sheet || "(neznano)";
    if (grouping === "code") return iss.code ? `${iss.code} — ${iss.code_desc || ""}` : "(brez kode)";
    if (grouping === "file") return iss.file;
    return "";
  };
  issues.forEach((iss) => {
    const k = keyOf(iss);
    if (!map.has(k)) map.set(k, []);
    map.get(k).push(iss);
  });
  return Array.from(map.entries())
    .sort((a, b) => b[1].length - a[1].length)
    .map(([key, list]) => ({ key, label: key, issues: list }));
}

function IssuesTable({ groups, grouped, multiFile, sort, onSort }) {
  const [collapsed, setCollapsed] = useState({});
  const toggle = (k) => setCollapsed((c) => ({ ...c, [k]: !c[k] }));
  const colSpan = multiFile ? 5 : 4;
  const anyCollapsed = groups.some((g) => collapsed[g.key]);
  const toggleAll = () => {
    if (anyCollapsed) setCollapsed({});
    else setCollapsed(Object.fromEntries(groups.map((g) => [g.key, true])));
  };

  const header = (key, label, style) => (
    <th style={style} onClick={() => onSort(nextSort(sort, key))} title="Klikni za razvrščanje">
      {label}
      {sort && sort.key === key && <span className="arrow">{sort.dir === "asc" ? "▲" : "▼"}</span>}
    </th>
  );

  return (
    <div style={{ overflowX: "auto" }}>
      {grouped && groups.length > 1 && (
        <div style={{ textAlign: "right", marginBottom: 6 }}>
          <button className="link-btn" style={{ border: "none", background: "none", cursor: "pointer", fontSize: 12, textDecoration: "underline", color: "var(--text-muted)" }} onClick={toggleAll}>
            {anyCollapsed ? "Razširi vse skupine" : "Strni vse skupine"}
          </button>
        </div>
      )}
      <table className="issues-table">
        <thead>
          <tr>
            {multiFile && header("file", "Datoteka")}
            {header("sheet", "List")}
            {header("row", "Vrstica", { width: 60 })}
            {header("code", "Koda")}
            {header("message", "Sporočilo")}
          </tr>
        </thead>
        <tbody>
          {groups.map((g) => (
            <React.Fragment key={g.key}>
              {grouped && (
                <tr className="group-head" onClick={() => toggle(g.key)}>
                  <td colSpan={colSpan}>
                    {collapsed[g.key] ? "▶" : "▼"} {g.label} <span className="count">({g.issues.length})</span>
                  </td>
                </tr>
              )}
              {!collapsed[g.key] && g.issues.map((iss, i) => (
                <tr key={g.key + i}>
                  {multiFile && <td className="muted">{iss.file}</td>}
                  <td>{iss.sheet}{iss.col ? <span className="muted"> · {iss.col}</span> : null}</td>
                  <td>{iss.row != null ? iss.row : ""}</td>
                  <td className="code-cell">
                    {iss.code ? <code>{iss.code}</code> : <span className="muted">—</span>}
                    {iss.code_desc && <span className="desc">{iss.code_desc}</span>}
                  </td>
                  <td>{iss.message}</td>
                </tr>
              ))}
            </React.Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function nextSort(sort, key) {
  if (!sort || sort.key !== key) return { key, dir: "asc" };
  if (sort.dir === "asc") return { key, dir: "desc" };
  return null; // tretji klik: brez razvrščanja
}

function DownloadSection({ results, reportUrlFn }) {
  return (
    <div style={{ marginBottom: 18 }}>
      {(results.files || []).map((fr) => (
        <div className="file-result" key={fr.index}>
          <div className="fr-head">
            <span className="fr-name">
              📄 {fr.filename}
              {fr.error ? (
                <span className="badge invalid">napaka</span>
              ) : (
                <span className={classNames("badge", fr.is_valid ? "valid" : "invalid")}>
                  {fr.is_valid ? "veljavno" : "neveljavno"}
                </span>
              )}
            </span>
            <span className="muted">
              {fr.counts && (fr.counts.error || 0)} napak · {fr.counts && (fr.counts.warning || 0)} opozoril
            </span>
          </div>
          <div className="fr-body">
            {fr.error ? (
              <div className="error-banner">{fr.error}</div>
            ) : (
              <>
                <div className="downloads">
                  {(fr.reports || []).filter((rep) => rep.kind === "excel").map((rep) => (
                    <a key={rep.kind} className="btn btn-sm"
                      href={reportUrlFn(fr.index, rep.filename)} download>
                      ⬇ {rep.label}
                    </a>
                  ))}
                  {(fr.reports || []).filter((rep) => rep.kind === "excel").length === 0 && <span className="muted">Ni poročil.</span>}
                </div>
                {fr.catalog_validation && fr.catalog_validation.enabled && (
                  <div className="catalog-note">
                    Šifranti: {fr.catalog_validation.status} — pregledanih vrstic {fr.catalog_validation.rows_checked_total},
                    neujemanj šifer: {fr.catalog_validation.mismatches}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

/* --------------------------- Pogled: prijava --------------------------- */

function LoginView({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const submit = async (e) => {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const status = await API.login(username, password);
      onLogin(status);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="login-page">
      <div className="site-header">
        <div className="site-topbar">Sartorius BIA Separations</div>
        <header className="app-header">
          <div className="brand">
            <div>
              <h1>IPO Excel Validator</h1>
              <p className="subtitle">Validacija IPO receptur</p>
            </div>
          </div>
        </header>
      </div>
      <div className="login-wrap">
        <form className="login-card" onSubmit={submit}>
        <div className="login-logo">IPO</div>
        <h2>IPO Excel Validator</h2>
        <p className="muted">Prijava z domenskim (AD) ali lokalnim računom</p>
        {error && <div className="error-banner">⚠ {error}</div>}
        <div className="field">
          <label>Uporabniško ime</label>
          <input
            type="text" autoFocus autoComplete="username"
            value={username} onChange={(e) => setUsername(e.target.value)}
          />
        </div>
        <div className="field">
          <label>Geslo</label>
          <input
            type="password" autoComplete="current-password"
            value={password} onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        <button className="btn btn-primary btn-block" type="submit" disabled={busy || !username || !password}>
          {busy ? <><span className="spinner"></span> Prijavljanje…</> : "Prijava"}
        </button>
        </form>
      </div>
    </div>
  );
}

/* -------------------------- Pogled: validacija ------------------------- */

const DEFAULT_CONFIG = {
  strict_mode: false,
  include_formulas: false,
  enable_sop_validation: true,
  enable_catalog_validation: true,
  apply_fixes: false,
  bypass_zakleni_require_empty_for_checkbox: true,
  bypass_zakleni_require_pogoj_for_param1_steps: false,
  bypass_zakleni_inverse_pogoj_requirement: false,
  bypass_rules: [],
  bypass_codes: [],
};

function ValidateView() {
  const [files, setFiles] = useState({ recipes: [], sop: null, raztopine: null, kemikalije: null, repro: null });
  const [phase, setPhase] = useState("idle");
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [live, setLive] = useState(false);
  const pollRef = useRef(null);
  const wsRef = useRef(null);
  const finishedRef = useRef(false);

  const setFilesPartial = useCallback((patch) => setFiles((s) => ({ ...s, ...patch })), []);

  const stopPolling = () => {
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
  };
  const closeWs = () => {
    if (wsRef.current) {
      try { wsRef.current.close(); } catch { /* ignore */ }
      wsRef.current = null;
    }
    setLive(false);
  };

  const finish = async (job_id) => {
    if (finishedRef.current) return;
    finishedRef.current = true;
    stopPolling();
    closeWs();
    try {
      const res = await API.jobResults(job_id);
      setResults(res);
      setPhase("done");
    } catch (e) {
      setError(e.message);
      setPhase("idle");
    }
  };

  const startPolling = (job_id) => {
    if (pollRef.current) return;
    pollRef.current = setInterval(async () => {
      try {
        const st = await API.jobStatus(job_id);
        setStatus(st);
        if (st.state === "done" || st.state === "error") {
          await finish(job_id);
        }
      } catch (e) {
        stopPolling();
        setError(e.message);
        setPhase("idle");
      }
    }, 700);
  };

  /* Napredek v realnem času: najprej WebSocket, ob napaki fallback na polling. */
  const startProgress = (job_id) => {
    let opened = false;
    try {
      const ws = new WebSocket(API.wsJobUrl(job_id));
      wsRef.current = ws;
      ws.onopen = () => { opened = true; setLive(true); };
      ws.onmessage = (ev) => {
        try {
          const st = JSON.parse(ev.data);
          setStatus(st);
          if (st.state === "done" || st.state === "error") finish(job_id);
        } catch { /* neveljaven okvir – ignoriramo */ }
      };
      ws.onerror = () => {
        if (!finishedRef.current) startPolling(job_id);
        setLive(false);
      };
      ws.onclose = () => {
        if (!finishedRef.current && !pollRef.current) startPolling(job_id);
        setLive(false);
      };
      // Če se WS ne odpre v 2 s, začnemo polling (WS ostane kot dopolnilo)
      setTimeout(() => { if (!opened && !finishedRef.current) startPolling(job_id); }, 2000);
    } catch {
      startPolling(job_id);
    }
  };

  const onRun = async () => {
    setError(null);
    setResults(null);
    setStatus(null);
    setPhase("running");
    finishedRef.current = false;
    try {
      const { job_id } = await API.startValidation(files.recipes, DEFAULT_CONFIG, {
        sop: files.sop, raztopine: files.raztopine, kemikalije: files.kemikalije, repro: files.repro,
      });
      setJobId(job_id);
      startProgress(job_id);
    } catch (e) {
      setError(e.message);
      setPhase("idle");
    }
  };

  useEffect(() => () => { stopPolling(); closeWs(); }, []);

  const onReset = () => {
    stopPolling();
    closeWs();
    finishedRef.current = false;
    setResults(null);
    setStatus(null);
    setJobId(null);
    setError(null);
    setPhase("idle");
    setFiles({ recipes: [], sop: null, raztopine: null, kemikalije: null, repro: null });
  };

  const canRun = files.recipes.length > 0 && phase !== "running";

  return (
    <>
      {error && <div className="error-banner">⚠ {error}</div>}
      <div className="grid">
        <div>
          <UploadCard state={files} set={setFilesPartial} />
          <RunCard canRun={canRun} phase={phase} onRun={onRun} status={status} live={live} />
        </div>
        <div>
          {results ? (
            <ResultsPanel
              results={results}
              reportUrlFn={(idx, name) => API.reportUrl(jobId, idx, name)}
              combinedUrlFn={(name) => API.combinedReportUrl(jobId, name)}
              onReset={onReset}
            />
          ) : (
            <div className="card">
              <div className="card-body">
                <div className="empty">
                  <div className="ic">📋</div>
                  <p>{phase === "running" ? "Validacija poteka…" : "Naloži recepture in zaženi validacijo za prikaz rezultatov."}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}

/* -------------------------- Pogled: zgodovina -------------------------- */

function HistoryView() {
  const [data, setData] = useState(null);
  const [offset, setOffset] = useState(0);
  const [error, setError] = useState(null);
  const [selected, setSelected] = useState(null);   // job_id
  const [detail, setDetail] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const limit = 25;

  const load = async (off) => {
    setError(null);
    try {
      const res = await API.history(limit, off);
      setData(res);
      setOffset(off);
    } catch (e) {
      setError(e.message);
    }
  };

  useEffect(() => { load(0); }, []);

  const open = async (jobId) => {
    setSelected(jobId);
    setDetail(null);
    setLoadingDetail(true);
    try {
      setDetail(await API.historyDetail(jobId));
    } catch (e) {
      setError(e.message);
    } finally {
      setLoadingDetail(false);
    }
  };

  if (selected) {
    return (
      <div>
        <div className="toolbar" style={{ marginBottom: 14 }}>
          <button className="btn btn-sm" onClick={() => { setSelected(null); setDetail(null); }}>← Nazaj na zgodovino</button>
          {detail && (
            <span className="muted">
              {formatDateTime(detail.record.created_at)} · {detail.record.username || "(neznan uporabnik)"}
            </span>
          )}
        </div>
        {loadingDetail && <div className="card"><div className="card-body"><div className="empty"><div className="ic">⏳</div><p>Nalaganje…</p></div></div></div>}
        {detail && detail.results && (
          <ResultsPanel
            title="📊 Rezultati validacije (zgodovina)"
            results={detail.results}
            reportUrlFn={(idx, name) => API.historyReportUrl(selected, idx, name)}
            combinedUrlFn={(name) => API.historyCombinedReportUrl(selected, name)}
          />
        )}
        {detail && !detail.results && (
          <div className="card"><div className="card-body">
            <div className="empty"><div className="ic">🗂</div><p>Podrobni rezultati za ta vnos niso več na voljo (na voljo je samo povzetek).</p></div>
            <HistorySummary record={detail.record} />
          </div></div>
        )}
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-head">
        <h2>🗂 Zgodovina validacij</h2>
        {data && <span className="muted">{data.total} vnosov</span>}
      </div>
      <div className="card-body">
        {error && <div className="error-banner">⚠ {error}</div>}
        {!data ? (
          <div className="empty"><div className="ic">⏳</div><p>Nalaganje…</p></div>
        ) : data.records.length === 0 ? (
          <div className="empty"><div className="ic">🗂</div><p>Zgodovina je prazna. Zaženi prvo validacijo.</p></div>
        ) : (
          <>
            <div style={{ overflowX: "auto" }}>
              <table className="issues-table">
                <thead>
                  <tr>
                    <th>Datum in ura</th>
                    <th>Uporabnik</th>
                    <th style={{ width: 90 }}>Datoteke</th>
                    <th style={{ width: 90 }}>Napake</th>
                    <th style={{ width: 90 }}>Opozorila</th>
                    <th style={{ width: 110 }}>Rezultat</th>
                  </tr>
                </thead>
                <tbody>
                  {data.records.map((r) => (
                    <tr key={r.job_id} className="clickable" onClick={() => open(r.job_id)} title="Klikni za podrobnosti">
                      <td>{formatDateTime(r.created_at)}</td>
                      <td className="muted">{r.username || "—"}</td>
                      <td>{r.total_files}</td>
                      <td style={{ color: r.errors ? "var(--error)" : "inherit", fontWeight: r.errors ? 700 : 400 }}>{r.errors}</td>
                      <td>{r.warnings}</td>
                      <td>
                        <span className={classNames("badge", r.invalid_files === 0 && r.state === "done" ? "valid" : "invalid")}>
                          {r.state !== "done" ? "napaka" : r.invalid_files === 0 ? "veljavno" : `${r.invalid_files} neveljavnih`}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="toolbar" style={{ marginTop: 12, justifyContent: "space-between" }}>
              <button className="btn btn-sm" disabled={offset === 0} onClick={() => load(Math.max(0, offset - limit))}>← Novejši</button>
              <span className="muted">{offset + 1}–{Math.min(offset + limit, data.total)} od {data.total}</span>
              <button className="btn btn-sm" disabled={offset + limit >= data.total} onClick={() => load(offset + limit)}>Starejši →</button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function HistorySummary({ record }) {
  return (
    <div style={{ marginTop: 12 }}>
      {(record.files || []).map((f, i) => (
        <div className="file-result" key={i}>
          <div className="fr-head">
            <span className="fr-name">
              📄 {f.filename}
              <span className={classNames("badge", f.is_valid ? "valid" : "invalid")}>
                {f.is_valid ? "veljavno" : "neveljavno"}
              </span>
            </span>
            <span className="muted">
              {(f.counts && f.counts.error) || 0} napak · {(f.counts && f.counts.warning) || 0} opozoril
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}

/* ------------------------- Pogled: diff verzij ------------------------- */

function DiffSidePicker({ label, side, setSide, history }) {
  const record = history.find((r) => r.job_id === side.historyId);
  return (
    <div className="diff-side">
      <div className="diff-side-title">{label}</div>
      <div className="seg" style={{ marginBottom: 10, display: "inline-flex" }}>
        <button className={classNames(side.mode === "upload" && "active")}
          onClick={() => setSide({ mode: "upload", file: null, historyId: "", historyFile: "" })}>Naloži datoteko</button>
        <button className={classNames(side.mode === "history" && "active")}
          onClick={() => setSide({ mode: "history", file: null, historyId: "", historyFile: "" })}>Iz zgodovine</button>
      </div>
      {side.mode === "upload" ? (
        <FilePicker
          accept=".xlsx,.xlsm"
          files={side.file ? [side.file] : []}
          onChange={(f) => setSide({ ...side, file: f })}
          label={side.file ? `📄 ${side.file.name}` : "Izberi datoteko"}
          hint=".xlsx / .xlsm"
        />
      ) : (
        <div>
          <div className="field">
            <label>Validacija iz zgodovine</label>
            <select value={side.historyId}
              onChange={(e) => setSide({ ...side, historyId: e.target.value, historyFile: "" })}>
              <option value="">— izberi —</option>
              {history.map((r) => (
                <option key={r.job_id} value={r.job_id}>
                  {formatDateTime(r.created_at)} · {(r.files || []).map((f) => f.filename).join(", ").slice(0, 60)}
                </option>
              ))}
            </select>
          </div>
          {record && (
            <div className="field">
              <label>Datoteka</label>
              <select value={side.historyFile}
                onChange={(e) => setSide({ ...side, historyFile: e.target.value })}>
                <option value="">— izberi —</option>
                {(record.files || []).map((f) => (
                  <option key={f.filename} value={f.filename}>{f.filename}</option>
                ))}
              </select>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function DiffView() {
  const emptySide = { mode: "upload", file: null, historyId: "", historyFile: "" };
  const [sideA, setSideA] = useState(emptySide);
  const [sideB, setSideB] = useState(emptySide);
  const [history, setHistory] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  useEffect(() => {
    API.history(100, 0).then((res) => setHistory(res.records)).catch(() => setHistory([]));
  }, []);

  const sideReady = (s) =>
    (s.mode === "upload" && s.file) || (s.mode === "history" && s.historyId && s.historyFile);

  const run = async () => {
    setError(null);
    setResult(null);
    setBusy(true);
    try {
      setResult(await API.diff(
        sideA.mode === "upload" ? { file: sideA.file } : { historyId: sideA.historyId, historyFile: sideA.historyFile },
        sideB.mode === "upload" ? { file: sideB.file } : { historyId: sideB.historyId, historyFile: sideB.historyFile },
      ));
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      <div className="card">
        <div className="card-head"><h2>🔀 Primerjava dveh verzij recepture</h2></div>
        <div className="card-body">
          <div className="diff-pickers">
            <DiffSidePicker label="Verzija A (starejša)" side={sideA} setSide={setSideA} history={history} />
            <DiffSidePicker label="Verzija B (novejša)" side={sideB} setSide={setSideB} history={history} />
          </div>
          <button className="btn btn-primary btn-block" style={{ marginTop: 14 }}
            disabled={!sideReady(sideA) || !sideReady(sideB) || busy} onClick={run}>
            {busy ? <><span className="spinner"></span> Primerjava poteka…</> : "▶ Primerjaj verziji"}
          </button>
          {error && <div className="error-banner" style={{ marginTop: 12 }}>⚠ {error}</div>}
        </div>
      </div>

      {result && <DiffResult result={result} />}
    </div>
  );
}

function DiffResult({ result }) {
  const s = result.summary;
  const changedSheets = result.sheets.filter((sd) => sd.has_changes);
  return (
    <div className="card">
      <div className="card-head">
        <h2>Rezultat primerjave</h2>
        <span className="muted">{result.file_a} ⟷ {result.file_b}</span>
      </div>
      <div className="card-body">
        {!result.has_changes ? (
          <div className="success-banner">✓ Verziji sta identični (po vsebini listov).</div>
        ) : (
          <div className="summary-tiles" style={{ gridTemplateColumns: "repeat(3, 1fr)" }}>
            <div className="tile static"><div className="num" style={{ color: "var(--success)" }}>+{s.rows_added}</div><div className="lbl">Dodane vrstice</div></div>
            <div className="tile static"><div className="num" style={{ color: "var(--error)" }}>−{s.rows_removed}</div><div className="lbl">Odstranjene vrstice</div></div>
            <div className="tile static"><div className="num" style={{ color: "var(--warning)" }}>{s.rows_changed}</div><div className="lbl">Spremenjene vrstice</div></div>
          </div>
        )}

        {changedSheets.map((sd) => (
          <Collapsible key={sd.sheet} defaultOpen={changedSheets.length === 1}
            title={
              sd.status === "added" ? `List '${sd.sheet}' — nov v verziji B`
              : sd.status === "removed" ? `List '${sd.sheet}' — odstranjen v verziji B`
              : `List '${sd.sheet}' — +${sd.rows_added.length} / −${sd.rows_removed.length} / ~${sd.rows_changed.length}`
            }>
            {sd.status === "common" && (
              <div style={{ overflowX: "auto" }}>
                {(sd.columns_added.length > 0 || sd.columns_removed.length > 0) && (
                  <div className="muted" style={{ marginBottom: 8 }}>
                    {sd.columns_added.length > 0 && <>Dodani stolpci: {sd.columns_added.join(", ")}. </>}
                    {sd.columns_removed.length > 0 && <>Odstranjeni stolpci: {sd.columns_removed.join(", ")}.</>}
                  </div>
                )}
                <table className="issues-table diff-table">
                  <thead>
                    <tr><th style={{ width: 90 }}>Sprememba</th><th style={{ width: 90 }}>Vrstica</th><th>Vsebina</th></tr>
                  </thead>
                  <tbody>
                    {sd.rows_added.map((r, i) => (
                      <tr key={"a" + i} className="diff-added">
                        <td><span className="badge valid">dodana</span></td>
                        <td>B:{r.row}</td>
                        <td>{r.preview}</td>
                      </tr>
                    ))}
                    {sd.rows_removed.map((r, i) => (
                      <tr key={"r" + i} className="diff-removed">
                        <td><span className="badge invalid">odstranjena</span></td>
                        <td>A:{r.row}</td>
                        <td>{r.preview}</td>
                      </tr>
                    ))}
                    {sd.rows_changed.map((r, i) => (
                      <tr key={"c" + i} className="diff-changed">
                        <td><span className="badge changed">spremenjena</span></td>
                        <td>A:{r.row_a} → B:{r.row_b}</td>
                        <td>
                          <div className="muted" style={{ marginBottom: 4 }}>{r.preview}</div>
                          {r.changes.map((c, j) => (
                            <div key={j} className="diff-cell-change">
                              <strong>{c.column}:</strong>{" "}
                              <span className="old">{c.old || "(prazno)"}</span>{" → "}
                              <span className="new">{c.new || "(prazno)"}</span>
                            </div>
                          ))}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Collapsible>
        ))}
      </div>
    </div>
  );
}

/* ---------------------------- Pogled: audit ---------------------------- */

const AUDIT_ACTION_LABELS = {
  prijava: "Prijava",
  prijava_neuspesna: "Neuspešna prijava",
  odjava: "Odjava",
  validacija_zagnana: "Validacija zagnana",
  validacija_zakljucena: "Validacija zaključena",
  prenos_porocila: "Prenos poročila",
  primerjava_razdelkov: "Primerjava razdelkov",
  diff_receptur: "Primerjava verzij",
};

function AuditView() {
  const [data, setData] = useState(null);
  const [offset, setOffset] = useState(0);
  const [username, setUsername] = useState("");
  const [action, setAction] = useState("");
  const [error, setError] = useState(null);
  const limit = 50;

  const load = async (off, user, act) => {
    setError(null);
    try {
      const res = await API.audit(limit, off, user, act);
      setData(res);
      setOffset(off);
    } catch (e) {
      setError(e.message);
      setData(null);
    }
  };

  useEffect(() => { load(0, "", ""); }, []);

  return (
    <div className="card">
      <div className="card-head">
        <h2>🛡 Revizijska sled (audit trail)</h2>
        {data && <span className="muted">{data.total} vnosov</span>}
      </div>
      <div className="card-body">
        {error && <div className="error-banner">⚠ {error}</div>}
        <div className="toolbar">
          <input type="text" placeholder="Uporabnik…" value={username}
            onChange={(e) => setUsername(e.target.value)} style={{ maxWidth: 200 }} />
          <select value={action} onChange={(e) => setAction(e.target.value)}>
            <option value="">Vsa dejanja</option>
            {Object.entries(AUDIT_ACTION_LABELS).map(([k, v]) => (
              <option key={k} value={k}>{v}</option>
            ))}
          </select>
          <button className="btn btn-sm" onClick={() => load(0, username, action)}>Filtriraj</button>
        </div>
        {!data ? (
          !error && <div className="empty"><div className="ic">⏳</div><p>Nalaganje…</p></div>
        ) : data.entries.length === 0 ? (
          <div className="empty"><div className="ic">🛡</div><p>Ni vnosov revizijske sledi.</p></div>
        ) : (
          <>
            <div style={{ overflowX: "auto" }}>
              <table className="issues-table">
                <thead>
                  <tr>
                    <th style={{ width: 150 }}>Čas</th>
                    <th style={{ width: 130 }}>Uporabnik</th>
                    <th style={{ width: 170 }}>Dejanje</th>
                    <th>Podrobnosti</th>
                    <th style={{ width: 110 }}>IP</th>
                  </tr>
                </thead>
                <tbody>
                  {data.entries.map((e) => (
                    <tr key={e.id}>
                      <td>{formatDateTime(e.ts)}</td>
                      <td>{e.username || "—"}</td>
                      <td>{AUDIT_ACTION_LABELS[e.action] || e.action}</td>
                      <td className="muted">{e.detail}</td>
                      <td className="muted">{e.ip || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="toolbar" style={{ marginTop: 12, justifyContent: "space-between" }}>
              <button className="btn btn-sm" disabled={offset === 0}
                onClick={() => load(Math.max(0, offset - limit), username, action)}>← Novejši</button>
              <span className="muted">{offset + 1}–{Math.min(offset + limit, data.total)} od {data.total}</span>
              <button className="btn btn-sm" disabled={offset + limit >= data.total}
                onClick={() => load(offset + limit, username, action)}>Starejši →</button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

/* ------------------------------- App ----------------------------------- */

const VIEWS = [
  { id: "validate", label: "Validacija", icon: "✓" },
  { id: "history", label: "Zgodovina", icon: "🗂" },
  { id: "diff", label: "Diff verzij", icon: "🔀" },
  { id: "audit", label: "Audit", icon: "🛡", minRole: "qa" },
];

function roleAllows(user, minRole) {
  if (!minRole) return true;
  if (!user) return false;
  const rank = { tehnolog: 0, qa: 1, admin: 2 };
  return (rank[user.role] ?? -1) >= (rank[minRole] ?? 99);
}

function App() {
  const [auth, setAuth] = useState(null);   // null = še ne vemo; {auth_enabled, user}
  const [catalog, setCatalog] = useState({ rules: [], codes: [], version: "" });
  const [view, setView] = useState("validate");
  const [error, setError] = useState(null);

  useEffect(() => {
    API.me().then(setAuth).catch((e) => setError(e.message));
  }, []);

  useEffect(() => {
    const onUnauthorized = () => setAuth((a) => (a && a.auth_enabled ? { ...a, user: null } : a));
    window.addEventListener("mes-unauthorized", onUnauthorized);
    return () => window.removeEventListener("mes-unauthorized", onUnauthorized);
  }, []);

  const loggedIn = auth && (!auth.auth_enabled || auth.user);

  useEffect(() => {
    if (loggedIn) {
      API.getRules().then(setCatalog).catch((e) => setError(e.message));
    }
  }, [loggedIn]);

  const onLogout = async () => {
    await API.logout();
    setAuth((a) => ({ ...a, user: null }));
    setView("validate");
  };

  if (!auth) {
    return (
      <div className="empty" style={{ paddingTop: 120 }}>
        <div className="ic">⏳</div>
        <p>Nalaganje aplikacije…</p>
        {error && <div className="error-banner" style={{ maxWidth: 420, margin: "12px auto" }}>⚠ {error}</div>}
      </div>
    );
  }

  if (auth.auth_enabled && !auth.user) {
    return <LoginView onLogin={(status) => setAuth(status)} />;
  }

  const user = auth.user;
  const visibleViews = VIEWS.filter((v) => roleAllows(user, v.minRole));

  return (
    <>
      <div className="site-header">
        <div className="site-topbar">Sartorius BIA Separations</div>
        <header className="app-header">
        <div className="brand">
          <div>
            <h1>IPO Excel Validator</h1>
            <p className="subtitle">Validacija IPO receptur — nalaganje in poročila v brskalniku</p>
          </div>
        </div>
        <nav className="nav-tabs">
          {visibleViews.map((v) => (
            <button key={v.id}
              className={classNames("nav-btn", view === v.id && "active")}
              onClick={() => setView(v.id)}>
              {v.icon} {v.label}
            </button>
          ))}
        </nav>
        <div className="header-right">
          {catalog.version && <span className="ver">{catalog.version}</span>}
          {auth.auth_enabled && user && (
            <div className="user-chip" title={`Vir: ${user.source}`}>
              <span className="user-name">{user.display_name}</span>
              <span className="user-role">{user.role_label}</span>
              <button className="logout-btn" onClick={onLogout} title="Odjava">Odjava</button>
            </div>
          )}
        </div>
        </header>
      </div>

      <div className="container">
        {error && <div className="error-banner">⚠ {error}</div>}
        {view === "validate" && <ValidateView />}
        {view === "history" && <HistoryView />}
        {view === "diff" && <DiffView />}
        {view === "audit" && <AuditView />}
      </div>
    </>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
