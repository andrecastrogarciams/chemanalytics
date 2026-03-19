# ChemAnalytics

MVP para controle de formulas, sincronizacao de catalogos auxiliares, conferencia operacional de consumo quimico e revisao manual auditavel.

## Status atual

O projeto esta funcional no caminho validado de desenvolvimento:

- backend Django REST
- frontend React + Vite
- banco SQLite local
- fixtures locais para testes offline de Oracle

O MVP ja cobre:

- autenticacao e perfis `admin`, `reviewer`, `consulta`
- carga e versionamento de formulas
- sincronizacao manual de catalogos auxiliares
- conferencia com historico congelado
- revisao manual com justificativa e trilha auditavel
- gestao administrativa de usuarios
- documentacao operacional minima

## Estrutura

- `backend/`: API Django
- `frontend/`: app React/Vite
- `docs/`: PRD, SPEC, stories e documentacao operacional
- `imports/`: arquivos de carga inicial
- `scripts/`: scripts de bootstrap local
- `.aiox-core/`: framework e artefatos AIOX do projeto

## Como subir localmente

### Backend

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
python backend\manage.py migrate
python backend\manage.py runserver
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Acessos locais:

- backend: `http://localhost:8000`
- health: `http://localhost:8000/api/v1/health/live`
- frontend: `http://localhost:5173`

## Comandos uteis

### Suite principal

```powershell
python backend\manage.py test apps.accounts apps.formulas apps.catalog apps.reconciliation apps.health
```

### Health operacional

```powershell
python backend\manage.py system_status --format=json
```

### Bootstrap de formulas

```powershell
python backend\manage.py bootstrap_formulas imports\PREVISAO_CONSUMO_PQ.xlsx --format=json
```

### Sincronizacao manual de catalogos

```powershell
python backend\manage.py sync_catalogs --format=json
```

Para sync offline com fixture local:

```powershell
$env:ORACLE_FIXTURE_PATH='backend\apps\catalog\fixtures\oracle_fixture.json'
python backend\manage.py sync_catalogs --format=json
```

## Documentacao principal

- produto: [docs/PRD.md](docs/PRD.md)
- especificacao tecnica: [docs/SPEC.md](docs/SPEC.md)
- manual rapido: [docs/manual-rapido.md](docs/manual-rapido.md)
- install/deploy: [docs/install-deploy.md](docs/install-deploy.md)
- runbook operacional: [docs/runbook-operacao.md](docs/runbook-operacao.md)
- checklist de prontidao do MVP: [docs/mvp-readiness-review.md](docs/mvp-readiness-review.md)

## Observacoes importantes

- O caminho homologado atual usa SQLite local.
- Integracao Oracle real depende de `backend\requirements-integration.txt` e ambiente externo.
- MySQL, Gunicorn e cron aparecem na documentacao como preparacao futura, mas nao fazem parte do fluxo homologado atual.
