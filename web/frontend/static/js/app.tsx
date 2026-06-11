/*
 * MES Excel Validator – spletni vmesnik (React, brez build koraka).
 * Komunicira z FastAPI backendom; vsa validacijska logika je na strežniku
 * (obstoječi ValidatorEngine). Ta datoteka je samo predstavitvena plast.
 */

const { useState, useEffect, useRef, useMemo, useCallback } = React;

/* ----------------------------- API klient ------------------------------ */

const API = {
  async getRules() {
    const res = await fetch("/api/rules");
    if (!res.ok) throw new Error("Napaka pri nalaganju pravil");
    return res.json();
  },
  async startValidation(recipes, config, optional) {
    const fd = new FormData();
    recipes.forEach((f) => fd.append("recipes", f, f.name));
    fd.append("config", JSON.stringify(config));
    if (optional.sop) fd.append("sop", optional.sop, optional.sop.name);
    if (optional.raztopine) fd.append("catalog_raztopine", optional.raztopine, optional.raztopine.name);
    if (optional.kemikalije) fd.append("catalog_kemikalije", optional.kemikalije, optional.kemikalije.name);
    const res = await fetch("/api/validate", { method: "POST", body: fd });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Napaka pri zagonu validacije" }));
      throw new Error(err.detail || "Napaka pri zagonu validacije");
    }
    return res.json();
  },
  async jobStatus(jobId) {
    const res = await fetch(`/api/jobs/${jobId}`);
    if (!res.ok) throw new Error("Napaka pri branju stanja");
    return res.json();
  },
  async jobResults(jobId) {
    const res = await fetch(`/api/jobs/${jobId}/results`);
    if (!res.ok) throw new Error("Napaka pri branju rezultatov");
    return res.json();
  },
  reportUrl(jobId, fileIndex, filename) {
    return `/api/jobs/${jobId}/files/${fileIndex}/report/${encodeURIComponent(filename)}`;
  },
  combinedReportUrl(jobId, filename) {
    return `/api/jobs/${jobId}/report/${encodeURIComponent(filename)}`;
  },
};

/* ----------------------------- Pomožno --------------------------------- */

const SEVERITY_LABEL = { error: "Napake", warning: "Opozorila", info: "Info" };
const STATE_LABEL = { queued: "čaka", running: "v teku", done: "končano", error: "napaka" };

function classNames(...parts) {
  return parts.filter(Boolean).join(" ");
}

function bytesToHuman(n) {
  if (n < 1024) return n + " B";
  if (n < 1024 * 1024) return (n / 1024).toFixed(1) + " KB";
  return (n / (1024 * 1024)).toFixed(1) + " MB";
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

/* ------------------------- Multiselect (bypass) ------------------------ */

function MultiSelect({ options, selected, onToggle, renderOption, placeholder }) {
  const [filter, setFilter] = useState("");
  const lower = filter.toLowerCase();
  const visible = options.filter((o) => o.search.toLowerCase().includes(lower));
  return (
    <div>
      <div className="multiselect">
        <input
          className="ms-filter"
          placeholder={placeholder || "Filtriraj…"}
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        />
        {visible.length === 0 && <div className="opt muted">Ni zadetkov</div>}
        {visible.map((o) => (
          <label className="opt" key={o.value}>
            <input
              type="checkbox"
              checked={selected.has(o.value)}
              onChange={() => onToggle(o.value)}
            />
            {renderOption(o)}
          </label>
        ))}
      </div>
      {selected.size > 0 && (
        <div className="muted" style={{ marginTop: 4 }}>Izbranih: {selected.size}</div>
      )}
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

/* ---------------------------- Config card ------------------------------ */

function ConfigCard({ config, set, rules, codes }) {
  const toggle = (key) => set({ [key]: !config[key] });
  const toggleSet = (key, value) => {
    const next = new Set(config[key]);
    next.has(value) ? next.delete(value) : next.add(value);
    set({ [key]: next });
  };

  const ruleOptions = rules.map((r) => ({ value: r.name, search: r.name + " " + r.code, rule: r }));
  const codeOptions = codes.map((c) => ({ value: c.code, search: c.code + " " + c.description, code: c }));

  return (
    <div className="card">
      <div className="card-head"><h2><span className="step">2</span> Konfiguracija</h2></div>
      <div className="card-body">
        <CheckRow checked={config.strict_mode} onChange={() => toggle("strict_mode")}
          label="Strogi način" desc="Opozorila se obravnavajo kot napake" />
        <CheckRow checked={config.include_formulas} onChange={() => toggle("include_formulas")}
          label="Validacija formul" desc="Naloži in preveri tudi celične formule" />
        <CheckRow checked={config.enable_sop_validation} onChange={() => toggle("enable_sop_validation")}
          label="Preverjanje SOP skladnosti" desc="Navzkrižno preverjanje z naloženim SOP dokumentom" />
        <CheckRow checked={config.enable_catalog_validation} onChange={() => toggle("enable_catalog_validation")}
          label="Preverjanje šifrantov" desc="Preveri šifre kemikalij/raztopin proti naloženim šifrantom" />
        <CheckRow checked={config.apply_fixes} onChange={() => toggle("apply_fixes")}
          label="Samodejni popravki (auto-fix)" desc="Ustvari popravljeno kopijo recepture (faza 2)" />

        <div style={{ marginTop: 8 }}>
          <Collapsible title="Napredno – zaklenipolja zastavice">
            <CheckRow checked={config.bypass_zakleni_require_empty_for_checkbox}
              onChange={() => toggle("bypass_zakleni_require_empty_for_checkbox")}
              label="Obvod: prazno polje za checkbox" />
            <CheckRow checked={config.bypass_zakleni_require_pogoj_for_param1_steps}
              onChange={() => toggle("bypass_zakleni_require_pogoj_for_param1_steps")}
              label="Obvod: zahteva pogoja za Param1 korake" />
            <CheckRow checked={config.bypass_zakleni_inverse_pogoj_requirement}
              onChange={() => toggle("bypass_zakleni_inverse_pogoj_requirement")}
              label="Obvod: inverzna zahteva pogoja" />
          </Collapsible>
        </div>

        <div style={{ marginTop: 12 }}>
          <Collapsible title={`Preskoči pravila (${config.bypass_rules.size})`}>
            <MultiSelect
              options={ruleOptions}
              selected={config.bypass_rules}
              onToggle={(v) => toggleSet("bypass_rules", v)}
              placeholder="Filtriraj pravila…"
              renderOption={(o) => (
                <span>{o.rule.name} <code>{o.rule.code}</code></span>
              )}
            />
          </Collapsible>
        </div>

        <div style={{ marginTop: 12 }}>
          <Collapsible title={`Preskoči kode napak (${config.bypass_codes.size})`}>
            <MultiSelect
              options={codeOptions}
              selected={config.bypass_codes}
              onToggle={(v) => toggleSet("bypass_codes", v)}
              placeholder="Filtriraj kode…"
              renderOption={(o) => (
                <span><code>{o.code.code}</code> {o.code.description}</span>
              )}
            />
          </Collapsible>
        </div>
      </div>
    </div>
  );
}

function CheckRow({ checked, onChange, label, desc }) {
  return (
    <label className="check">
      <input type="checkbox" checked={checked} onChange={onChange} />
      <span>
        <span className="lbl">{label}</span>
        {desc && <span className="desc"> — {desc}</span>}
      </span>
    </label>
  );
}

/* ----------------------------- Run card -------------------------------- */

function RunCard({ canRun, phase, onRun, status }) {
  const running = phase === "running";
  return (
    <div className="card">
      <div className="card-head"><h2><span className="step">3</span> Validacija</h2></div>
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

function ResultsPanel({ results, jobId, onReset }) {
  const [search, setSearch] = useState("");
  const [severity, setSeverity] = useState("all");
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

  const hasFilter = search || severity !== "all" || fileFilter !== "all" || sheetFilter !== "all" || codeFilter !== "all";
  const resetFilters = () => {
    setSearch(""); setSeverity("all"); setFileFilter("all"); setSheetFilter("all"); setCodeFilter("all");
  };

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return allIssues.filter((iss) => {
      if (severity !== "all" && iss.severity !== severity) return false;
      if (fileFilter !== "all" && iss.file !== fileFilter) return false;
      if (sheetFilter !== "all" && iss.sheet !== sheetFilter) return false;
      if (codeFilter !== "all" && iss.code !== codeFilter) return false;
      if (q) {
        const hay = `${iss.sheet} ${iss.code} ${iss.code_desc} ${iss.message} ${iss.row} ${iss.col}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }, [allIssues, search, severity, fileFilter, sheetFilter, codeFilter]);

  const sorted = useMemo(() => sortIssues(filtered, sort), [filtered, sort]);
  const groups = useMemo(() => buildGroups(sorted, grouping), [sorted, grouping]);
  const totals = results.totals || {};
  const toggleSeverity = (sev) => setSeverity(severity === sev ? "all" : sev);

  return (
    <div className="card">
      <div className="card-head">
        <h2>📊 Rezultati validacije</h2>
        <span className="muted">{filtered.length} prikazanih / {allIssues.length} skupaj</span>
      </div>
      <div className="card-body">
        <div className="summary-tiles">
          {[["error", totals.error || 0, "Napake"], ["warning", totals.warning || 0, "Opozorila"], ["info", totals.info || 0, "Info"]].map(([sev, num, lbl]) => (
            <div key={sev}
              className={classNames("tile", sev, severity === sev && "active")}
              onClick={() => toggleSeverity(sev)}
              title="Klikni za filtriranje po resnosti">
              <div className="num">{num}</div><div className="lbl">{lbl}</div>
            </div>
          ))}
          <div className="tile files static">
            <div className="num">{totals.invalid_files || 0}/{totals.files || 0}</div>
            <div className="lbl">Neveljavnih datotek</div>
          </div>
        </div>

        {(results.combined_reports || []).length > 0 && (
          <div className="combined-reports">
            <div className="cr-title">📦 Skupna poročila za vse datoteke</div>
            <div className="downloads">
              {results.combined_reports.map((rep) => (
                <a key={rep.kind} className="btn btn-sm"
                  href={API.combinedReportUrl(jobId, rep.filename)} download>
                  ⬇ {rep.label}
                </a>
              ))}
            </div>
          </div>
        )}

        <DownloadSection results={results} jobId={jobId} />

        <div className="toolbar">
          <input type="text" placeholder="🔎 Iskanje po sporočilu, listu, kodi…"
            value={search} onChange={(e) => setSearch(e.target.value)} />
          <select value={severity} onChange={(e) => setSeverity(e.target.value)}>
            <option value="all">Vse resnosti</option>
            <option value="error">Napake</option>
            <option value="warning">Opozorila</option>
            <option value="info">Info</option>
          </select>
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
            {[["sheet", "Po listu"], ["code", "Po kodi"], ["severity", "Po resnosti"], ["file", "Po datoteki"], ["none", "Brez"]].map(([k, lbl]) => (
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
  severity: (iss) => ({ error: 0, warning: 1, info: 2 }[iss.severity] ?? 3),
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
    if (grouping === "severity") return SEVERITY_LABEL[iss.severity] || iss.severity;
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
  const colSpan = multiFile ? 6 : 5;
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
            {header("severity", "Resnost", { width: 70 })}
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
                  <td><span className={classNames("sev-pill", iss.severity)}>{iss.severity}</span></td>
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

function DownloadSection({ results, jobId }) {
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
                  {(fr.reports || []).map((rep) => (
                    <a key={rep.kind} className="btn btn-sm"
                      href={API.reportUrl(jobId, fr.index, rep.filename)} download>
                      ⬇ {rep.label}
                    </a>
                  ))}
                  {(!fr.reports || fr.reports.length === 0) && <span className="muted">Ni poročil.</span>}
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

/* ------------------------------- App ----------------------------------- */

const DEFAULT_CONFIG = {
  strict_mode: false,
  include_formulas: false,
  enable_sop_validation: true,
  enable_catalog_validation: true,
  apply_fixes: false,
  bypass_zakleni_require_empty_for_checkbox: true,
  bypass_zakleni_require_pogoj_for_param1_steps: true,
  bypass_zakleni_inverse_pogoj_requirement: false,
  bypass_rules: new Set(),
  bypass_codes: new Set(),
};

const CONFIG_STORAGE_KEY = "mes_validator_config_v1";

/* Konfiguracija se ohrani med sejami (localStorage); Set ⟷ Array pretvorba. */
function loadStoredConfig() {
  try {
    const raw = localStorage.getItem(CONFIG_STORAGE_KEY);
    if (!raw) return DEFAULT_CONFIG;
    const parsed = JSON.parse(raw);
    return {
      ...DEFAULT_CONFIG,
      ...parsed,
      bypass_rules: new Set(parsed.bypass_rules || []),
      bypass_codes: new Set(parsed.bypass_codes || []),
    };
  } catch {
    return DEFAULT_CONFIG;
  }
}

function storeConfig(config) {
  try {
    localStorage.setItem(
      CONFIG_STORAGE_KEY,
      JSON.stringify({
        ...config,
        bypass_rules: Array.from(config.bypass_rules),
        bypass_codes: Array.from(config.bypass_codes),
      })
    );
  } catch { /* localStorage ni na voljo – ignoriramo */ }
}

function App() {
  const [catalog, setCatalog] = useState({ rules: [], codes: [], version: "" });
  const [files, setFiles] = useState({ recipes: [], sop: null, raztopine: null, kemikalije: null });
  const [config, setConfig] = useState(loadStoredConfig);
  const [phase, setPhase] = useState("idle");
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const pollRef = useRef(null);

  useEffect(() => {
    API.getRules().then(setCatalog).catch((e) => setError(e.message));
  }, []);

  useEffect(() => { storeConfig(config); }, [config]);

  const setFilesPartial = useCallback((patch) => setFiles((s) => ({ ...s, ...patch })), []);
  const setConfigPartial = useCallback((patch) => setConfig((s) => ({ ...s, ...patch })), []);

  const stopPolling = () => {
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
  };

  const onRun = async () => {
    setError(null);
    setResults(null);
    setStatus(null);
    setPhase("running");
    const payload = {
      ...config,
      bypass_rules: Array.from(config.bypass_rules),
      bypass_codes: Array.from(config.bypass_codes),
    };
    try {
      const { job_id } = await API.startValidation(files.recipes, payload, {
        sop: files.sop, raztopine: files.raztopine, kemikalije: files.kemikalije,
      });
      setJobId(job_id);
      pollRef.current = setInterval(async () => {
        try {
          const st = await API.jobStatus(job_id);
          setStatus(st);
          if (st.state === "done" || st.state === "error") {
            stopPolling();
            const res = await API.jobResults(job_id);
            setResults(res);
            setPhase("done");
          }
        } catch (e) {
          stopPolling();
          setError(e.message);
          setPhase("idle");
        }
      }, 700);
    } catch (e) {
      setError(e.message);
      setPhase("idle");
    }
  };

  useEffect(() => () => stopPolling(), []);

  const onReset = () => {
    stopPolling();
    setResults(null);
    setStatus(null);
    setJobId(null);
    setError(null);
    setPhase("idle");
    setFiles({ recipes: [], sop: null, raztopine: null, kemikalije: null });
  };

  const canRun = files.recipes.length > 0 && phase !== "running";

  return (
    <>
      <header className="app-header">
        <div className="brand">
          <div className="logo">MES</div>
          <div>
            <h1>MES Excel Validator</h1>
            <p className="subtitle">Validacija IPO receptur — nalaganje, konfiguracija in poročila v brskalniku</p>
          </div>
        </div>
        {catalog.version && <span className="ver">{catalog.version}</span>}
      </header>

      <div className="container">
        {error && <div className="error-banner">⚠ {error}</div>}
        <div className="grid">
          <div>
            <UploadCard state={files} set={setFilesPartial} />
            <ConfigCard config={config} set={setConfigPartial} rules={catalog.rules} codes={catalog.codes} />
            <RunCard canRun={canRun} phase={phase} onRun={onRun} status={status} />
          </div>
          <div>
            {results ? (
              <ResultsPanel results={results} jobId={jobId} onReset={onReset} />
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
      </div>
    </>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
