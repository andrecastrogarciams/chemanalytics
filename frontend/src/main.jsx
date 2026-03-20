import React, { startTransition, useEffect, useRef, useState } from "react";
import ReactDOM from "react-dom/client";

import viposaLogo from "./assets/viposa-logo.png";
import "./styles.css";

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api").replace(/\/$/, "");
const storageKey = "chemanalytics.session";

const dashboardCards = [
  { label: "Lotes Processados", value: "1.254", trend: "+12%", tone: "primary" },
  { label: "Taxa de Divergencia", value: "2,4%", trend: "-0,5%", tone: "warning" },
  { label: "Inconsistencias Pendentes", value: "18", trend: "+2", tone: "danger" },
];

const recentActivities = [
  { title: "Lote #9822 conferido", meta: "Operador: Joao Silva | 12:45", tone: "success" },
  { title: "Divergencia detectada", meta: "Lote #9821 | Linha 03 | 11:30", tone: "warning" },
  { title: "Nova formula cadastrada", meta: "Poliuretano Flex | 10:15", tone: "primary" },
  { title: "Inconsistencia critica", meta: "Lote #9819 | aguardando revisao", tone: "danger" },
];

const mockLotRows = [
  { id: "#9825", formula: "Resina Termoplastica A1", date: "15/10/2023 - 14:22", operator: "Marcos Oliveira", status: "Conforme" },
  { id: "#9824", formula: "Verniz Acrilico High Gloss", date: "15/10/2023 - 13:50", operator: "Ana Costa", status: "Divergente" },
  { id: "#9823", formula: "Pigmento Organico Blue-7", date: "15/10/2023 - 13:15", operator: "Joao Silva", status: "Conforme" },
  { id: "#9822", formula: "Solvente Industrial 402", date: "15/10/2023 - 11:30", operator: "Carlos Lima", status: "Inconsistente" },
];

function readStoredSession() {
  try {
    const raw = window.localStorage.getItem(storageKey);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function persistSession(session) {
  if (!session) {
    window.localStorage.removeItem(storageKey);
    return;
  }

  window.localStorage.setItem(storageKey, JSON.stringify(session));
}

function readTokenExpiry(token) {
  if (!token) {
    return null;
  }

  try {
    const [, payload] = token.split(".");
    const normalized = payload.replaceAll("-", "+").replaceAll("_", "/");
    const decoded = JSON.parse(window.atob(normalized));
    return decoded.exp ? decoded.exp * 1000 : null;
  } catch {
    return null;
  }
}

async function requestJson(path, options = {}, accessToken = null) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  if (accessToken) {
    headers.Authorization = `Bearer ${accessToken}`;
  }

  const response = await fetch(`${apiBaseUrl}${path}`, { ...options, headers });
  const payload = await response.json().catch(() => ({}));

  if (!response.ok) {
    const message =
      payload.message ||
      payload.error?.message ||
      payload.error?.code ||
      payload.code ||
      "Nao foi possivel completar a requisicao.";
    const error = new Error(message);
    error.status = response.status;
    error.payload = payload;
    throw error;
  }

  return payload;
}

function App() {
  const storedSession = readStoredSession();
  const [view, setView] = useState(storedSession?.access ? "app" : "login");
  const [activeSection, setActiveSection] = useState("dashboard");
  const [health, setHealth] = useState({ status: "checking", message: "Conectando ao backend..." });
  const [authState, setAuthState] = useState({
    loading: false,
    error: "",
    user: storedSession?.user || null,
    access: storedSession?.access || "",
    refresh: storedSession?.refresh || "",
    mode: storedSession?.access ? "live" : "demo",
  });
  const [credentials, setCredentials] = useState({ username: "", password: "" });
  const [reconciliationForm, setReconciliationForm] = useState({
    date_start: "",
    date_end: "",
    nf1: "",
    codpro: "",
    codder: "",
    chemical_code: "",
    only_divergences: false,
    only_inconsistencies: false,
  });
  const [runsState, setRunsState] = useState({ loading: false, error: "", data: [] });
  const [runDetailState, setRunDetailState] = useState({ loading: false, error: "", data: null });
  const [lotDetailState, setLotDetailState] = useState({ loading: false, error: "", data: null });
  const [formulasState, setFormulasState] = useState({ loading: false, error: "", data: [] });
  const [chemicalsState, setChemicalsState] = useState({ loading: false, error: "", data: [] });
  const [selectedFormulaId, setSelectedFormulaId] = useState(null);
  const [isCreatingVersion, setIsCreatingVersion] = useState(false);
  const [newVersionData, setNewVersionData] = useState({
    start_date: "",
    observation: "",
    items: [],
  });
  const [actionMessage, setActionMessage] = useState("");
  const [reviewForm, setReviewForm] = useState({
    itemId: "",
    reviewed_status: "conform",
    justification: "",
    loading: false,
    error: "",
    success: "",
  });

  const isAuthenticated = Boolean(authState.access);
  const canUseLiveData = isAuthenticated && authState.mode === "live";

  useEffect(() => {
    let cancelled = false;

    async function loadHealth() {
      try {
        const payload = await requestJson("/v1/health/live");
        if (!cancelled) {
          setHealth({
            status: payload.status || "ok",
            message: "Backend conectado e pronto para operacao.",
          });
        }
      } catch {
        if (!cancelled) {
          setHealth({
            status: "offline",
            message: "Nao foi possivel validar o backend. A UI segue em modo demonstracao.",
          });
        }
      }
    }

    loadHealth();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    persistSession(
      authState.access
        ? {
            access: authState.access,
            refresh: authState.refresh,
            user: authState.user,
          }
        : null
    );
  }, [authState.access, authState.refresh, authState.user]);

  useEffect(() => {
    if (!authState.access || !authState.refresh || authState.mode !== "live") {
      return undefined;
    }

    const expiry = readTokenExpiry(authState.access);
    if (!expiry) {
      return undefined;
    }

    const refreshInMs = Math.max(expiry - Date.now() - 30000, 1000);
    const timerId = window.setTimeout(() => {
      refreshAccessToken().catch(() => {});
    }, refreshInMs);

    return () => {
      window.clearTimeout(timerId);
    };
  }, [authState.access, authState.refresh, authState.mode]);

  useEffect(() => {
    if (!canUseLiveData || (activeSection !== "history" && activeSection !== "reconciliation")) {
      return;
    }

    loadRuns();
  }, [activeSection, canUseLiveData]);

  useEffect(() => {
    if (!canUseLiveData || activeSection !== "formulas") {
      return;
    }

    loadFormulas();
    loadChemicals();
  }, [activeSection, canUseLiveData]);

  async function loadChemicals() {
    setChemicalsState((current) => ({ ...current, loading: true, error: "" }));
    try {
      const payload = await requestWithSession("/v1/catalog/chemicals");
      setChemicalsState({ loading: false, error: "", data: payload.data || [] });
    } catch (error) {
      setChemicalsState({ loading: false, error: error.message, data: [] });
    }
  }

  async function loadRuns(selectFirst = true, expandFirstLot = false) {
    setRunsState((current) => ({ ...current, loading: true, error: "" }));
    try {
      const payload = await requestWithSession("/v1/reconciliation/runs");
      const runs = payload.data || [];
      setRunsState({ loading: false, error: "", data: runs });

      if (selectFirst && runs.length > 0) {
        await loadRunDetail(runs[0].id, expandFirstLot);
      } else if (runs.length === 0) {
        setRunDetailState({ loading: false, error: "", data: null });
        setLotDetailState({ loading: false, error: "", data: null });
      }
    } catch (error) {
      setRunsState({ loading: false, error: error.message, data: [] });
    }
  }

  async function loadRunDetail(runId, selectFirstLot = false) {
    setRunDetailState({ loading: true, error: "", data: null });
    try {
      const payload = await requestWithSession(`/v1/reconciliation/runs/${runId}`);
      const run = payload.data;
      setRunDetailState({ loading: false, error: "", data: run });

      const firstLotId = run?.lots?.[0]?.id;
      if (selectFirstLot && firstLotId) {
        await loadLotDetail(firstLotId);
      } else if (!firstLotId) {
        setLotDetailState({ loading: false, error: "", data: null });
      }
    } catch (error) {
      setRunDetailState({ loading: false, error: error.message, data: null });
    }
  }

  async function handleToggleLot(lotId) {
    if (lotDetailState.data?.id === lotId) {
      setLotDetailState({ loading: false, error: "", data: null });
    } else {
      await loadLotDetail(lotId);
    }
  }

  async function loadLotDetail(lotId) {
    setLotDetailState({ loading: true, error: "", data: null });
    try {
      const payload = await requestWithSession(`/v1/reconciliation/lots/${lotId}`);
      setLotDetailState({ loading: false, error: "", data: payload.data });
    } catch (error) {
      setLotDetailState({ loading: false, error: error.message, data: null });
    }
  }

  async function loadFormulas() {
    setFormulasState((current) => ({ ...current, loading: true, error: "" }));
    try {
      const payload = await requestWithSession("/v1/formulas");
      const formulas = payload.data || [];
      setFormulasState({ loading: false, error: "", data: formulas });
      setSelectedFormulaId((current) => current || null);
    } catch (error) {
      setFormulasState({ loading: false, error: error.message, data: [] });
    }
  }

  function handleCredentialChange(event) {
    const { name, value } = event.target;
    setCredentials((current) => ({ ...current, [name]: value }));
  }

  function handleReconciliationInput(event) {
    const { name, value, type, checked } = event.target;
    setReconciliationForm((current) => ({
      ...current,
      [name]: type === "checkbox" ? checked : value,
    }));
  }

  function handleReviewInput(event) {
    const { name, value } = event.target;
    setReviewForm((current) => ({
      ...current,
      [name]: value,
      error: "",
      success: "",
    }));
  }

  async function handleLogin(event) {
    event.preventDefault();
    setAuthState((current) => ({ ...current, loading: true, error: "" }));

    try {
      const payload = await requestJson("/v1/auth/login", {
        method: "POST",
        body: JSON.stringify(credentials),
      });

      startTransition(() => {
        setAuthState({
          loading: false,
          error: "",
          user: payload.data.user,
          access: payload.data.access,
          refresh: payload.data.refresh,
          mode: "live",
        });
        setActionMessage("");
        setView("app");
      });
    } catch (error) {
      setAuthState((current) => ({
        ...current,
        loading: false,
        error: error.message || "Nao foi possivel autenticar.",
      }));
    }
  }

  function openAppInDemoMode() {
    startTransition(() => {
      setAuthState({
        loading: false,
        error: "",
        user: {
          first_name: "Equipe",
          last_name: "VIPOSA",
          group: "admin",
          must_change_password: false,
        },
        access: "",
        refresh: "",
        mode: "demo",
      });
      setView("app");
    });
  }

  function handleLogout() {
    startTransition(() => {
      persistSession(null);
      setAuthState({
        loading: false,
        error: "",
        user: null,
        access: "",
        refresh: "",
        mode: "demo",
      });
      setRunsState({ loading: false, error: "", data: [] });
      setRunDetailState({ loading: false, error: "", data: null });
      setLotDetailState({ loading: false, error: "", data: null });
      setFormulasState({ loading: false, error: "", data: [] });
      setSelectedFormulaId(null);
      setActionMessage("");
      setView("login");
    });
  }

  function expireSession(message = "Sua sessao expirou. Faca login novamente.") {
    startTransition(() => {
      persistSession(null);
      setAuthState({
        loading: false,
        error: message,
        user: null,
        access: "",
        refresh: "",
        mode: "demo",
      });
      setRunsState({ loading: false, error: "", data: [] });
      setRunDetailState({ loading: false, error: "", data: null });
      setLotDetailState({ loading: false, error: "", data: null });
      setFormulasState({ loading: false, error: "", data: [] });
      setSelectedFormulaId(null);
      setActionMessage("");
      setView("login");
    });
  }

  async function refreshAccessToken() {
    const session = readStoredSession() || authState;
    if (!session.refresh) {
      expireSession();
      throw new Error("Sessao expirada.");
    }

    try {
      const payload = await requestJson("/v1/auth/refresh", {
        method: "POST",
        body: JSON.stringify({ refresh: session.refresh }),
      });
      const nextAccess = payload.data.access;
      setAuthState((current) => ({
        ...current,
        access: nextAccess,
        mode: "live",
      }));
      return nextAccess;
    } catch (_error) {
      expireSession();
      throw new Error("Sessao expirada.");
    }
  }

  async function requestWithSession(path, options = {}) {
    const session = readStoredSession() || authState;
    try {
      return await requestJson(path, options, session.access);
    } catch (error) {
      const shouldRefresh =
        (error.status === 401 || error.payload?.code === "token_not_valid" || error.payload?.detail === "Given token not valid for any token type") &&
        session.refresh;

      if (shouldRefresh) {
        const nextAccess = await refreshAccessToken();
        return requestJson(path, options, nextAccess);
      }
      if (error.status === 401) {
        expireSession();
      }
      throw error;
    }
  }

  async function handleRunExecution(event) {
    event.preventDefault();
    setActionMessage("");

    try {
      const payload = await requestWithSession(
        "/v1/reconciliation/runs",
        {
          method: "POST",
          body: JSON.stringify({
            ...reconciliationForm,
            nf1: reconciliationForm.nf1 || null,
            codpro: reconciliationForm.codpro || null,
            codder: reconciliationForm.codder || null,
            chemical_code: reconciliationForm.chemical_code || null,
          }),
        }
      );

      setActionMessage(`Conferencia executada com sucesso. Run #${payload.data.id} criada.`);
      await loadRuns(false);
      await loadRunDetail(payload.data.id, true);
    } catch (error) {
      setActionMessage(error.message);
    }
  }

  async function handleManualReview(event) {
    event.preventDefault();

    if (!reviewForm.itemId) {
      setReviewForm((current) => ({ ...current, error: "Selecione um item para revisar.", success: "" }));
      return;
    }

    setReviewForm((current) => ({ ...current, loading: true, error: "", success: "" }));

    try {
      await requestWithSession(
        `/v1/reconciliation/items/${reviewForm.itemId}/reviews`,
        {
          method: "POST",
          body: JSON.stringify({
            reviewed_status: reviewForm.reviewed_status,
            justification: reviewForm.justification,
          }),
        }
      );

      if (lotDetailState.data?.id) {
        await loadLotDetail(lotDetailState.data.id);
      }
      if (runDetailState.data?.id) {
        await loadRunDetail(runDetailState.data.id, false);
      }

      setReviewForm({
        itemId: "",
        reviewed_status: "conform",
        justification: "",
        loading: false,
        error: "",
        success: "Revisao registrada com sucesso.",
      });
    } catch (error) {
      setReviewForm((current) => ({
        ...current,
        loading: false,
        error: error.message,
        success: "",
      }));
    }
  }

  if (view === "login") {
    return (
      <main className="login-shell">
        <section className="login-hero">
          <div className="brand-mark">
            <img alt="Logo VIPOSA" className="brand-image" src={viposaLogo} />
          </div>
          <p className="brand-kicker">VIPOSA Industrial ERP</p>
          <h1>Controle quimico com conferencias auditaveis</h1>
          <p className="hero-copy">
            Interface inicial baseada nos templates do projeto para acelerar a operacao do ChemAnalytics no ambiente interno.
          </p>
          <div className={`health-banner is-${health.status}`}>
            <span className="health-dot" />
            <span>{health.message}</span>
          </div>
        </section>

        <section className="login-panel">
          <div className="panel-header">
            <div className="brand-badge">
              <span className="brand-badge-icon">
                <img alt="Logo VIPOSA" className="brand-badge-image" src={viposaLogo} />
              </span>
              <div>
                <strong>VIPOSA</strong>
                <span>Industrial Intelligence Platform</span>
              </div>
            </div>
            <h2>Acesso ao sistema</h2>
            <p>Use suas credenciais ERP para entrar no modulo de formulas e conferencia.</p>
          </div>

          <form className="login-form" onSubmit={handleLogin}>
            <label>
              <span>Usuario</span>
              <input
                name="username"
                placeholder="Digite seu usuario"
                type="text"
                value={credentials.username}
                onChange={handleCredentialChange}
              />
            </label>

            <label>
              <span>Senha</span>
              <input
                name="password"
                placeholder="********"
                type="password"
                value={credentials.password}
                onChange={handleCredentialChange}
              />
            </label>

            {authState.error ? <p className="form-error">{authState.error}</p> : null}

            <button className="primary-button" disabled={authState.loading} type="submit">
              {authState.loading ? "Autenticando..." : "Entrar no ERP"}
            </button>
          </form>

          <div className="panel-footer">
            <button className="ghost-button" type="button" onClick={openAppInDemoMode}>
              Abrir demonstracao visual
            </button>
            <small>Use o modo demonstracao se o backend ainda nao tiver usuario cadastrado.</small>
          </div>

          <div className="support-strip">
            <span>Quimicos, formulas e conferencias em um unico fluxo.</span>
            <span>Status operacional via API e auditoria por item.</span>
          </div>
        </section>
      </main>
    );
  }

  const userName = authState.user?.first_name
    ? `${authState.user.first_name} ${authState.user.last_name || ""}`.trim()
    : "Operador VIPOSA";

  const selectedFormula = formulasState.data.find((formula) => formula.id === selectedFormulaId) || null;

  function handleStartNewVersion(formula) {
    const baseItems = formula.current_version?.items || [];
    setNewVersionData({
      start_date: new Date().toISOString().split("T")[0],
      observation: `Nova versao baseada na V${formula.current_version?.version_number || 0}`,
      items: baseItems.map((item) => ({
        chemical_code: item.chemical_code,
        chemical_description: item.chemical_description,
        percentual: item.percentual,
        tolerance_pct: item.tolerance_pct,
        is_incomplete: item.is_incomplete,
        incomplete_reason: item.incomplete_reason,
        _is_cloned: true,
      })),
    });
    setIsCreatingVersion(true);
  }

  function handleCancelNewVersion() {
    setIsCreatingVersion(false);
    setNewVersionData({ start_date: "", observation: "", items: [] });
  }

  function handleNewVersionChange(event) {
    const { name, value } = event.target;
    setNewVersionData((current) => ({ ...current, [name]: value }));
  }

  function handleUpdateVersionItem(index, field, value) {
    setNewVersionData((current) => {
      const newItems = [...current.items];
      newItems[index] = { ...newItems[index], [field]: value };
      return { ...current, items: newItems };
    });
  }

  function handleAddVersionItem() {
    setNewVersionData((current) => ({
      ...current,
      items: [
        ...current.items,
        {
          chemical_code: "",
          chemical_description: "",
          percentual: 0,
          tolerance_pct: 0,
          is_incomplete: false,
          incomplete_reason: "",
          _is_cloned: false,
        },
      ],
    }));
  }

  function handleRemoveVersionItem(index) {
    setNewVersionData((current) => {
      const newItems = current.items.filter((_, i) => i !== index);
      return { ...current, items: newItems };
    });
  }

  async function handleSubmitNewVersion(event) {
    event.preventDefault();
    setFormulasState((current) => ({ ...current, loading: true, error: "" }));

    try {
      await requestWithSession(`/v1/formulas/${selectedFormulaId}/versions`, {
        method: "POST",
        body: JSON.stringify(newVersionData),
      });
      setIsCreatingVersion(false);
      await loadFormulas();
    } catch (error) {
      setFormulasState((current) => ({ ...current, loading: false, error: error.message }));
    }
  }
  const liveLotRows = runDetailState.data?.lots?.map((lot) => ({
    id: lot.id,
    label: lot.nf1,
    formula: formatArticleLabels(lot),
    date: formatDateTime(lot.recurtimento_date),
    operator: runDetailState.data.executed_by_username || "Sistema",
    status: lot.status_final,
  })) || [];

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-logo">
            <img alt="Logo VIPOSA" className="sidebar-logo-image" src={viposaLogo} />
          </div>
          <div>
            <strong>VIPOSA</strong>
            <span>ChemAnalytics</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          <button className={activeSection === "dashboard" ? "nav-item active" : "nav-item"} onClick={() => setActiveSection("dashboard")} type="button">
            <span>Dashboard</span>
          </button>
          <button className={activeSection === "reconciliation" ? "nav-item active" : "nav-item"} onClick={() => setActiveSection("reconciliation")} type="button">
            <span>Conferencias</span>
          </button>
          <button className={activeSection === "history" ? "nav-item active" : "nav-item"} onClick={() => setActiveSection("history")} type="button">
            <span>Historico</span>
          </button>
          <button className={activeSection === "formulas" ? "nav-item active" : "nav-item"} onClick={() => setActiveSection("formulas")} type="button">
            <span>Formulas</span>
          </button>
        </nav>

        <div className="sidebar-user">
          <div className="user-avatar">{userName.slice(0, 1)}</div>
          <div>
            <strong>{userName}</strong>
            <span>{authState.user?.group || "admin"}</span>
          </div>
        </div>

        <button className="ghost-button sidebar-logout" type="button" onClick={handleLogout}>
          Sair
        </button>
      </aside>

      <main className="workspace">
        <header className="topbar">
          <div>
            <p className="page-kicker">ChemAnalytics MVP</p>
            <h2>{sectionTitle(activeSection)}</h2>
          </div>
          <div className="topbar-actions">
            <div className={`health-chip is-${health.status}`}>
              <span className="health-dot" />
              {health.status === "offline" ? "Modo demonstracao" : "Backend online"}
            </div>
            <span className="mode-chip">{canUseLiveData ? "Dados reais" : "Visual demo"}</span>
          </div>
        </header>

        {activeSection === "dashboard" ? (
          <DashboardView lotRows={canUseLiveData && liveLotRows.length > 0 ? liveLotRows : mockLotRows} />
        ) : null}
        {activeSection === "reconciliation" ? (
          <ReconciliationView
            actionMessage={actionMessage}
            canUseLiveData={canUseLiveData}
            form={reconciliationForm}
            reviewForm={reviewForm}
            lotDetailState={lotDetailState}
            onChange={handleReconciliationInput}
            onLoadLot={loadLotDetail}
            onLoadRun={loadRunDetail}
            onReviewChange={handleReviewInput}
            onReviewSubmit={handleManualReview}
            onSubmit={handleRunExecution}
            runDetailState={runDetailState}
            runsState={runsState}
          />
        ) : null}
        {activeSection === "history" ? (
          <HistoryView
            canUseLiveData={canUseLiveData}
            lotDetailState={lotDetailState}
            onLoadLot={handleToggleLot}
            onLoadRun={loadRunDetail}
            runDetailState={runDetailState}
            runsState={runsState}
          />
        ) : null}
        {activeSection === "formulas" ? (
          <FormulaView
            canUseLiveData={canUseLiveData}
            formulasState={formulasState}
            chemicalsState={chemicalsState}
            onSelectFormula={(id) => setSelectedFormulaId((current) => (current === id ? null : id))}
            selectedFormula={selectedFormula}
            isCreatingVersion={isCreatingVersion}
            newVersionData={newVersionData}
            onStartNewVersion={handleStartNewVersion}
            onCancelNewVersion={handleCancelNewVersion}
            onNewVersionChange={handleNewVersionChange}
            onUpdateVersionItem={handleUpdateVersionItem}
            onAddVersionItem={handleAddVersionItem}
            onRemoveVersionItem={handleRemoveVersionItem}
            onSubmitNewVersion={handleSubmitNewVersion}
          />
        ) : null}
      </main>
    </div>
  );
}

function sectionTitle(activeSection) {
  const titles = {
    dashboard: "Painel de Controle",
    reconciliation: "Execucao de Conferencia",
    history: "Historico de Conferencias",
    formulas: "Gestao de Formulas",
  };

  return titles[activeSection];
}

function DashboardView({ lotRows }) {
  return (
    <section className="page-grid">
      <div className="hero-card">
        <div>
          <p className="page-kicker">Resumo operacional</p>
          <h3>Bom dia, operador</h3>
          <p>Uma leitura rapida das conferencias e inconsistencias mais relevantes do turno.</p>
        </div>
        <div className="hero-actions">
          <button className="secondary-button" type="button">Nova conferencia</button>
          <button className="primary-button" type="button">Cadastrar formula</button>
        </div>
      </div>

      <div className="card-grid">
        {dashboardCards.map((card) => (
          <article key={card.label} className={`metric-card tone-${card.tone}`}>
            <span className="metric-trend">{card.trend}</span>
            <strong>{card.value}</strong>
            <span>{card.label}</span>
          </article>
        ))}
      </div>

      <div className="dashboard-columns">
        <article className="panel-card">
          <div className="panel-head">
            <h4>Conferencias da semana</h4>
            <span>7 dias</span>
          </div>
          <div className="bars">
            {[40, 65, 55, 90, 75, 82, 60].map((height, index) => (
              <div key={height} className="bar-wrap">
                <div className="bar" style={{ height: `${height}%` }} />
                <small>{["SEG", "TER", "QUA", "QUI", "SEX", "SAB", "DOM"][index]}</small>
              </div>
            ))}
          </div>
        </article>

        <article className="panel-card">
          <div className="panel-head">
            <h4>Atividades recentes</h4>
            <span>tempo real</span>
          </div>
          <div className="activity-list">
            {recentActivities.map((activity) => (
              <div key={activity.title} className="activity-item">
                <span className={`status-dot tone-${activity.tone}`} />
                <div>
                  <strong>{activity.title}</strong>
                  <span>{activity.meta}</span>
                </div>
              </div>
            ))}
          </div>
        </article>
      </div>

      <article className="panel-card">
        <div className="panel-head">
          <h4>Ultimos lotes processados</h4>
          <span>historico imediato</span>
        </div>
        <div className="table-shell">
          <table>
            <thead>
              <tr>
                <th>Lote</th>
                <th>Artigo / Derivacao</th>
                <th>Data/Hora</th>
                <th>Operador</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {lotRows.map((row) => (
                <tr key={row.id}>
                  <td>{row.label || row.id}</td>
                  <td>{row.formula}</td>
                  <td>{row.date}</td>
                  <td>{row.operator}</td>
                  <td><span className={`pill status-${normalizeStatus(row.status)}`}>{formatStatusLabel(row.status)}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </article>
    </section>
  );
}

function ReconciliationView({
  actionMessage,
  canUseLiveData,
  form,
  lotDetailState,
  onChange,
  onLoadLot,
  onLoadRun,
  onReviewChange,
  onReviewSubmit,
  onSubmit,
  reviewForm,
  runDetailState,
  runsState,
}) {
  const lots = runDetailState.data?.lots || [];
  const lotRefs = useRef({});

  useEffect(() => {
    if (lotDetailState.data?.id && lotRefs.current[lotDetailState.data.id]) {
      setTimeout(() => {
        lotRefs.current[lotDetailState.data.id]?.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      }, 100);
    }
  }, [lotDetailState.data?.id]);

  const items = lotDetailState.data?.items || [];
  const reviewableItems = items.filter((item) => item.status_final !== "inconsistent");

  return (
    <section className="page-grid">
      <article className="panel-card">
        <div className="panel-head">
          <h4>Filtros de conferencia</h4>
          <span>janela maxima de 90 dias</span>
        </div>
        {!canUseLiveData ? <p className="inline-message">Entre com um usuario reviewer/admin para executar conferencias reais.</p> : null}
        <form onSubmit={onSubmit}>
          <div className="filter-grid">
            <label>
              <span>Data inicial</span>
              <input name="date_start" type="date" value={form.date_start} onChange={onChange} />
            </label>
            <label>
              <span>Data final</span>
              <input name="date_end" type="date" value={form.date_end} onChange={onChange} />
            </label>
            <label>
              <span>NF1</span>
              <input name="nf1" placeholder="LT-2024-001" type="text" value={form.nf1} onChange={onChange} />
            </label>
            <label>
              <span>Artigo</span>
              <input name="codpro" placeholder="Codigo do artigo" type="text" value={form.codpro} onChange={onChange} />
            </label>
            <label>
              <span>Derivacao</span>
              <input name="codder" placeholder="Codigo da derivacao" type="text" value={form.codder} onChange={onChange} />
            </label>
            <label className="toggle-field">
              <span>Somente divergencias</span>
              <input checked={form.only_divergences} name="only_divergences" type="checkbox" onChange={onChange} />
            </label>
          </div>
          <div className="action-row">
            <button className="primary-button" disabled={!canUseLiveData} type="submit">Executar conferencia</button>
          </div>
        </form>
        {actionMessage ? <p className="inline-message">{actionMessage}</p> : null}
      </article>

      <article className="panel-card">
        <div className="panel-head">
          <h4>{runDetailState.data ? `Resultados da Run #${runDetailState.data.id}` : "Resultados da conferencia"}</h4>
          <span>{lots.length} lotes encontrados</span>
        </div>
        {runDetailState.error ? <p className="form-error">{runDetailState.error}</p> : null}
        
        <div className="formula-listing">
          {lots.map((lot) => (
            <div 
              key={lot.id} 
              ref={(el) => { lotRefs.current[lot.id] = el; }}
              className={lotDetailState.data?.id === lot.id ? "formula-row expanded" : "formula-row"}
            >
              <button 
                className={lotDetailState.data?.id === lot.id ? "formula-item active formula-button" : "formula-item formula-button"} 
                type="button" 
                onClick={() => onLoadLot(lot.id)}
              >
                <div style={{ display: "flex", justifyContent: "space-between", width: "100%", alignItems: "center" }}>
                  <div>
                    <strong>{lot.nf1}</strong>
                    <p style={{ margin: 0 }}>
                      <strong>{formatArticleLabels(lot)}</strong>
                      <span className="muted-inline">{formatArticleDerivation(lot.codpro, lot.codder)}</span>
                    </p>
                  </div>
                  <div style={{ textAlign: "right" }}>
                    <span className={`pill status-${normalizeStatus(lot.status_final)}`}>{formatStatusLabel(lot.status_final)}</span>
                    <small style={{ display: "block", marginTop: "4px", color: "#64748b" }}>{lot.items_count} itens</small>
                  </div>
                </div>
              </button>

              {lotDetailState.data?.id === lot.id ? (
                <div className="formula-expand">
                  <div className="panel-head">
                    <h5>Itens do Lote {lot.nf1}</h5>
                  </div>
                  
                  {lotDetailState.loading ? <p className="inline-message">Carregando itens...</p> : null}
                  
                  <div className="table-shell">
                    <table>
                      <thead>
                        <tr>
                          <th>Produto</th>
                          <th>Previsto</th>
                          <th>Realizado</th>
                          <th>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {items.map((item) => (
                          <tr key={item.id}>
                            <td>{item.chemical_description}</td>
                            <td>{formatNumber(item.predicted_qty)} kg</td>
                            <td>{formatNumber(item.used_qty)} kg</td>
                            <td><span className={`pill status-${normalizeStatus(item.status_final)}`}>{formatStatusLabel(item.status_final)}</span></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <div className="review-band" style={{ marginTop: "20px", padding: "20px", background: "#f8fafc", borderRadius: "16px" }}>
                    <div className="panel-head">
                      <h6>Revisao Manual</h6>
                    </div>
                    <form onSubmit={onReviewSubmit}>
                      <div className="review-grid">
                        <label>
                          <span>Item</span>
                          <select name="itemId" value={reviewForm.itemId} onChange={onReviewChange}>
                            <option value="">Selecione</option>
                            {reviewableItems.map((i) => (
                              <option key={i.id} value={i.id}>{i.chemical_description}</option>
                            ))}
                          </select>
                        </label>
                        <label>
                          <span>Status</span>
                          <select name="reviewed_status" value={reviewForm.reviewed_status} onChange={onReviewChange}>
                            <option value="conform">Conforme</option>
                            <option value="divergent">Divergente</option>
                          </select>
                        </label>
                        <label className="full-span">
                          <span>Justificativa</span>
                          <textarea name="justification" rows="2" value={reviewForm.justification} onChange={onReviewChange} />
                        </label>
                      </div>
                      <div className="action-row" style={{ marginTop: "10px" }}>
                        <button className="secondary-button btn-small" type="submit">Salvar Revisao</button>
                      </div>
                    </form>
                  </div>
                </div>
              ) : null}
            </div>
          ))}
        </div>
      </article>
    </section>
  );
}

function HistoryView({ canUseLiveData, lotDetailState, onLoadLot, onLoadRun, runDetailState, runsState }) {
  const selectedRunLots = runDetailState.data?.lots || [];
  const lotRefs = useRef({});

  useEffect(() => {
    if (lotDetailState.data?.id && lotRefs.current[lotDetailState.data.id]) {
      setTimeout(() => {
        lotRefs.current[lotDetailState.data.id]?.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      }, 100);
    }
  }, [lotDetailState.data?.id]);

  return (
    <section className="page-grid">
      {!canUseLiveData ? <p className="inline-message">Entre com usuario autenticado para consultar o historico real.</p> : null}

      <article className="panel-card">
        <div className="panel-head">
          <h4>{runDetailState.data ? `Lotes da Run #${runDetailState.data.id}` : "Lotes da ultima execucao"}</h4>
          <span>{selectedRunLots.length} lotes detectados</span>
        </div>
        {runsState.error ? <p className="form-error">{runsState.error}</p> : null}
        
        <div className="formula-listing">
          {selectedRunLots.map((lot) => (
            <div 
              key={lot.id} 
              ref={(el) => { lotRefs.current[lot.id] = el; }}
              className={lotDetailState.data?.id === lot.id ? "formula-row expanded" : "formula-row"}
            >
              <button 
                className={lotDetailState.data?.id === lot.id ? "formula-item active formula-button" : "formula-item formula-button"} 
                type="button" 
                onClick={() => onLoadLot(lot.id)}
              >
                <div style={{ display: "flex", justifyContent: "space-between", width: "100%", alignItems: "center" }}>
                  <div>
                    <strong>{lot.nf1}</strong>
                    <p style={{ margin: 0 }}>
                      <strong>{formatArticleLabels(lot)}</strong>
                      <span className="muted-inline">{formatArticleDerivation(lot.codpro, lot.codder)}</span>
                    </p>
                  </div>
                  <div style={{ textAlign: "right" }}>
                    <span className={`pill status-${normalizeStatus(lot.status_final)}`}>{formatStatusLabel(lot.status_final)}</span>
                    <small style={{ display: "block", marginTop: "4px", color: "#64748b" }}>{lot.items_count} itens</small>
                  </div>
                </div>
              </button>

              {lotDetailState.data?.id === lot.id ? (
                <div className="formula-expand">
                  <div className="panel-head">
                    <h5>Auditoria de itens e reviews</h5>
                  </div>
                  
                  {lotDetailState.loading ? <p className="inline-message">Carregando auditoria...</p> : null}
                  {lotDetailState.error ? <p className="form-error">{lotDetailState.error}</p> : null}
                  
                  {lotDetailState.data?.items?.length ? (
                    <div className="history-list">
                      {lotDetailState.data.items.map((item) => (
                        <div key={item.id} className="history-card" style={{ background: "white", borderRadius: "14px" }}>
                          <div style={{ flex: 1 }}>
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                              <strong>{item.chemical_description}</strong>
                              <span className={`pill status-${normalizeStatus(item.status_final)}`}>
                                {item.reviews.length} reviews
                              </span>
                            </div>
                            <p className="muted-inline" style={{ margin: "4px 0" }}>
                              Calculado: {formatStatusLabel(item.status_calculated)} | Final: {formatStatusLabel(item.status_final)}
                            </p>
                            
                            {item.reviews.length > 0 && (
                              <div style={{ marginTop: "10px", padding: "10px", background: "#f8fafc", borderRadius: "8px" }}>
                                {item.reviews.map((rev, rIdx) => (
                                  <div key={rIdx} style={{ fontSize: "0.85rem", marginBottom: rIdx === item.reviews.length - 1 ? 0 : "8px" }}>
                                    <strong>{rev.reviewed_by_username || "Revisor"}</strong>: {rev.justification}
                                    <div style={{ fontSize: "0.75rem", color: "#94a3b8" }}>{formatDateTime(rev.reviewed_at)}</div>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : !lotDetailState.loading ? (
                    <p className="inline-message">Nenhum item encontrado neste lote.</p>
                  ) : null}
                </div>
              ) : null}
            </div>
          ))}
        </div>
        {!selectedRunLots.length && !runsState.loading ? (
          <p className="inline-message">Nenhum lote encontrado no historico recente.</p>
        ) : null}
      </article>
    </section>
  );
}

function FormulaView({
  canUseLiveData,
  formulasState,
  chemicalsState,
  onSelectFormula,
  selectedFormula,
  isCreatingVersion,
  newVersionData,
  onStartNewVersion,
  onCancelNewVersion,
  onNewVersionChange,
  onUpdateVersionItem,
  onAddVersionItem,
  onRemoveVersionItem,
  onSubmitNewVersion,
}) {
  const formulas = formulasState.data || [];
  const chemicals = chemicalsState.data || [];
  const formulaRefs = useRef({});
  const [searchTerm, setSearchTerm] = useState("");
  const [activeItemIndex, setActiveItemIndex] = useState(null);

  useEffect(() => {
    if (selectedFormula?.id && formulaRefs.current[selectedFormula.id]) {
      // Small delay to ensure the browser has finished expanding/rendering the item
      setTimeout(() => {
        formulaRefs.current[selectedFormula.id]?.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      }, 100);
    }
  }, [selectedFormula?.id]);

  const filteredChemicals = searchTerm
    ? chemicals.filter(
        (c) =>
          c.chemical_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
          c.description.toLowerCase().includes(searchTerm.toLowerCase())
      )
    : chemicals.slice(0, 50);

  function handleSelectChemical(index, chem) {
    onUpdateVersionItem(index, "chemical_code", chem.chemical_code);
    onUpdateVersionItem(index, "chemical_description", chem.description);
    setActiveItemIndex(null);
    setSearchTerm("");
  }

  return (
    <section className="page-grid">
      <article className="panel-card formula-list formula-list--single-column">
        <div className="panel-head">
          <h4>Formulas existentes</h4>
          <span>artigos ativos e historico</span>
        </div>
        {!canUseLiveData ? <p className="inline-message">Entre como admin para carregar formulas reais.</p> : null}
        {formulasState.error ? <p className="form-error">{formulasState.error}</p> : null}
        <div className="formula-listing">
          {formulas.map((formula) => (
            <div
              key={formula.id}
              ref={(el) => {
                formulaRefs.current[formula.id] = el;
              }}
              className={selectedFormula?.id === formula.id ? "formula-row expanded" : "formula-row"}
            >
              <button
                className={selectedFormula?.id === formula.id ? "formula-item active formula-button" : "formula-item formula-button"}
                type="button"
                onClick={() => onSelectFormula(formula.id)}
              >
                <strong>{formatArticleLabels(formula)}</strong>
                <small>{formatArticleDerivation(formula.codpro, formula.codder)}</small>
                <span className={`pill ${formula.active ? "status-success" : "status-neutral"}`}>
                  {formula.current_version ? `Ativa V${formula.current_version.version_number}` : "Sem versao"}
                </span>
              </button>

              {selectedFormula?.id === formula.id ? (
                <div className="formula-expand">
                  <div className="detail-hero formula-inline-hero">
                    <div>
                      <strong>{formatArticleLabels(formula)}</strong>
                      <p className="formula-meta-line">{formatArticleDerivation(formula.codpro, formula.codder)}</p>
                      <p>
                        {formula.current_version
                          ? `Versao ${formula.current_version.version_number} vigente desde ${formatDateOnly(formula.current_version.start_date)}`
                          : "Sem versao ativa carregada"}
                      </p>
                    </div>
                    <div className="hero-actions">
                      <span className="pill status-success">{formula.active ? "Producao ativa" : "Inativa"}</span>
                      {!isCreatingVersion && (
                        <button className="primary-button" type="button" onClick={() => onStartNewVersion(formula)}>
                          Nova Versao
                        </button>
                      )}
                    </div>
                  </div>

                  {isCreatingVersion ? (
                    <form className="version-create-form" onSubmit={onSubmitNewVersion}>
                      <div className="form-grid">
                        <div className="form-field">
                          <span>Data de Inicio</span>
                          <input
                            required
                            name="start_date"
                            type="date"
                            value={newVersionData.start_date}
                            onChange={onNewVersionChange}
                          />
                        </div>
                        <div className="form-field">
                          <span>Observacao da Versao</span>
                          <input
                            name="observation"
                            placeholder="Ex: Ajuste de percentual para nova safra"
                            type="text"
                            value={newVersionData.observation}
                            onChange={onNewVersionChange}
                          />
                        </div>
                      </div>

                      <div className="items-editor">
                        <div className="items-header">
                          <h5>Itens da Formula</h5>
                          <button className="secondary-button btn-small" type="button" onClick={onAddVersionItem}>
                            + Adicionar Item
                          </button>
                        </div>
                        <div className="table-shell">
                          <table>
                            <thead>
                              <tr>
                                <th>Cod. Quimico</th>
                                <th>Descricao</th>
                                <th>%</th>
                                <th>Tol. %</th>
                                <th>Incompleto?</th>
                                <th>Acoes</th>
                              </tr>
                            </thead>
                            <tbody>
                              {newVersionData.items.map((item, idx) => (
                                <tr key={idx}>
                                  <td style={{ position: "relative" }}>
                                    <input
                                      required
                                      readOnly={item._is_cloned}
                                      className="input-table"
                                      type="text"
                                      value={item.chemical_code}
                                      placeholder="Pesquisar..."
                                      onFocus={() => !item._is_cloned && setActiveItemIndex(idx)}
                                      onBlur={() => {
                                        setTimeout(() => setActiveItemIndex(null), 200);
                                      }}
                                      onChange={(e) => {
                                        if (!item._is_cloned) {
                                          setSearchTerm(e.target.value);
                                          onUpdateVersionItem(idx, "chemical_code", e.target.value);
                                        }
                                      }}
                                    />
                                    {!item._is_cloned && activeItemIndex === idx && (
                                      <div className="catalog-dropdown">
                                        {filteredChemicals.length > 0 ? (
                                          filteredChemicals.map((c) => (
                                            <div
                                              key={c.chemical_code}
                                              className="catalog-option"
                                              onClick={() => handleSelectChemical(idx, c)}
                                            >
                                              <strong>{c.chemical_code}</strong> - {c.description}
                                            </div>
                                          ))
                                        ) : (
                                          <div className="catalog-no-results">Nenhum produto encontrado</div>
                                        )}
                                      </div>
                                    )}
                                  </td>
                                  <td>
                                    <input
                                      required
                                      readOnly={item._is_cloned}
                                      className="input-table"
                                      type="text"
                                      value={item.chemical_description}
                                      onChange={(e) => {
                                        if (!item._is_cloned) {
                                          onUpdateVersionItem(idx, "chemical_description", e.target.value);
                                        }
                                      }}
                                    />
                                  </td>
                                  <td>
                                    <input
                                      required
                                      className="input-table"
                                      disabled={item.is_incomplete}
                                      step="0.0001"
                                      type="number"
                                      value={item.percentual}
                                      onChange={(e) => onUpdateVersionItem(idx, "percentual", e.target.value)}
                                    />
                                  </td>
                                  <td>
                                    <input
                                      required
                                      className="input-table"
                                      step="0.01"
                                      type="number"
                                      value={item.tolerance_pct}
                                      onChange={(e) => onUpdateVersionItem(idx, "tolerance_pct", e.target.value)}
                                    />
                                  </td>
                                  <td>
                                    <input
                                      type="checkbox"
                                      checked={item.is_incomplete}
                                      onChange={(e) => onUpdateVersionItem(idx, "is_incomplete", e.target.checked)}
                                    />
                                  </td>
                                  <td>
                                    <button
                                      className="btn-danger btn-small"
                                      type="button"
                                      onClick={() => onRemoveVersionItem(idx)}
                                    >
                                      Remover
                                    </button>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>

                      <div className="form-actions">
                        <button className="secondary-button" type="button" onClick={onCancelNewVersion}>
                          Cancelar
                        </button>
                        <button className="primary-button" type="submit">
                          Salvar Nova Versao
                        </button>
                      </div>
                    </form>
                  ) : (
                    <div className="table-shell">
                      <table>
                        <thead>
                          <tr>
                            <th>Codigo</th>
                            <th>Descricao</th>
                            <th>Percentual</th>
                            <th>Tolerancia</th>
                            <th>Tipo</th>
                          </tr>
                        </thead>
                        <tbody>
                          {(formula.current_version?.items || []).map((row) => (
                            <tr key={row.id}>
                              <td>{row.chemical_code}</td>
                              <td>{row.chemical_description}</td>
                              <td>{row.percentual == null ? "Incompleto" : `${formatNumber(row.percentual)}%`}</td>
                              <td>{formatNumber(row.tolerance_pct)}%</td>
                              <td>
                                <span className="pill status-neutral">
                                  {row.is_incomplete ? "Pendente" : "Componente"}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              ) : null}
            </div>
          ))}
        </div>
        {!formulas.length ? (
          <p className="inline-message">Nenhuma formula carregada ou acesso nao permitido para o perfil atual.</p>
        ) : null}
      </article>
    </section>
  );
}

function humanizeInconsistencyCode(code) {
  const dictionary = {
    formula_not_found: "Formula nao encontrada",
    chemical_not_in_formula: "Quimico nao cadastrado na formula",
    formula_item_incomplete: "Item de formula incompleto",
    formula_item_without_usage: "Formula sem consumo Oracle",
    predicted_zero: "Previsto igual a zero",
    inactive_or_stale_catalog_code: "Quimico fora do catalogo ativo",
  };

  return dictionary[code] || formatStatusLabel(code);
}

function formatArticleDerivation(article, derivation) {
  return `${article} ${derivation}`;
}

function formatArticleLabels(formula) {
  const article = formula.article_description || "Artigo sem descricao";
  const derivation = formula.derivation_description || "Derivacao sem descricao";
  return `${article} ${derivation}`;
}

function formatDateTime(value) {
  if (!value) {
    return "-";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return String(value);
  }

  return parsed.toLocaleString("pt-BR");
}

function formatDateOnly(value) {
  if (!value) {
    return "-";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return String(value);
  }

  return parsed.toLocaleDateString("pt-BR");
}

function formatNumber(value) {
  if (value == null || value === "") {
    return "-";
  }

  return Number(value).toLocaleString("pt-BR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 4,
  });
}

function formatPercent(value) {
  if (value == null || value === "") {
    return "-";
  }

  return `${formatNumber(value)}%`;
}

function formatStatusLabel(status) {
  if (!status) {
    return "-";
  }

  return String(status).replaceAll("_", " ");
}

function normalizeStatus(status) {
  const normalized = String(status || "").toLowerCase();
  if (normalized.includes("incons")) return "danger";
  if (normalized.includes("diverg")) return "warning";
  if (normalized.includes("review")) return "warning";
  if (normalized.includes("success") || normalized.includes("conform") || normalized.includes("ativa")) return "success";
  return "neutral";
}

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
