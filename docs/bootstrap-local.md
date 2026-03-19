# Bootstrap Local

## Objetivo

Subir o scaffold inicial do projeto sem depender de Oracle ou MySQL reais.

## Backend

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
python backend\manage.py migrate
python backend\manage.py runserver
```

Backend esperado em `http://localhost:8000/` com health check em `http://localhost:8000/api/health/`.

## Frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend esperado em `http://localhost:5173/`.

## Observações

- Nesta fase o backend usa SQLite apenas para bootstrap local.
- Dependências de integração operacional ficam separadas em `backend\requirements-integration.txt`.
- Integração real com MySQL, Oracle, autenticação e observabilidade entram em stories posteriores.
- Os scripts em `scripts/` servem como atalho para lembrar a sequência de bootstrap.
