import React from "react";
import ReactDOM from "react-dom/client";

import "./styles.css";

function App() {
  return (
    <main className="shell">
      <section className="card">
        <p className="eyebrow">ChemAnalytics MVP</p>
        <h1>Scaffold inicial pronto</h1>
        <p>
          Frontend React/Vite desacoplado do backend Django REST, preparado para
          as proximas stories.
        </p>
        <ul>
          <li>Health check previsto em <code>/api/health/</code></li>
          <li>Autenticacao entra na Story 1.2</li>
          <li>Observabilidade inicial entra na Story 1.3</li>
        </ul>
      </section>
    </main>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
