# Install And Deploy

## Escopo desta versao

Este documento descreve o deploy do estado atual do MVP. O caminho validado em 2026-03-18 e:

- backend Django
- frontend Vite
- banco SQLite local
- dependências Oracle/MySQL separadas para integração futura

MySQL e Gunicorn aparecem abaixo porque a spec exige esses tópicos, mas ainda não existe configuração completa por ambiente no código para produção endurecida. Use esta documentação como guia operacional do estado atual, não como promessa de arquitetura já concluída.

## Pre-requisitos

- Python 3.13
- Node.js 20+
- npm 10+
- PowerShell no Windows ou shell equivalente
- Acesso ao diretório do projeto

## Variaveis de ambiente

Copie `.env.example` para `.env` e ajuste no mínimo:

- `APP_TIME_ZONE`
- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `FRONTEND_URL`
- `VITE_API_BASE_URL`
- `ORACLE_USER`
- `ORACLE_PASSWORD`
- `ORACLE_DSN`
- `MYSQL_DATABASE`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_HOST`
- `MYSQL_PORT`

Observações:

- O backend atual usa SQLite em `backend/config/settings.py`.
- As variáveis MySQL e Oracle já existem para preparação operacional, health check e futuras integrações.
- Para testes offline, os adapters aceitam fixtures locais por variável:
  - `ORACLE_FIXTURE_PATH`
  - `ORACLE_RECONCILIATION_FIXTURE_PATH`

## Instalacao local validada

### Backend

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
python backend\manage.py migrate
python backend\manage.py check
python backend\manage.py runserver
```

### Frontend

```powershell
cd frontend
npm install
npm run build
npm run dev
```

## Criacao do banco MySQL

Topico exigido pela spec, mas ainda nao utilizado pelo `settings.py` atual.

Quando o backend for promovido para MySQL, criar ao menos:

```sql
CREATE DATABASE chemanalytics CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'chemanalytics'@'%' IDENTIFIED BY 'senha-forte';
GRANT ALL PRIVILEGES ON chemanalytics.* TO 'chemanalytics'@'%';
FLUSH PRIVILEGES;
```

Enquanto essa troca não for implementada no código, o banco validado do MVP continua sendo SQLite local.

## Migrations

Sempre rodar antes da subida da aplicação:

```powershell
python backend\manage.py migrate
python backend\manage.py check
```

## Bootstrap

### Formulas

```powershell
python backend\manage.py bootstrap_formulas imports\PREVISAO_CONSUMO_PQ.xlsx --format=json
```

### Catalogos auxiliares

```powershell
python backend\manage.py sync_catalogs --format=json
```

## Build frontend

```powershell
cd frontend
npm install
npm run build
```

Artefato gerado em `frontend/dist`.

## Subida da aplicacao

### Modo validado no projeto

Backend:

```powershell
python backend\manage.py runserver
```

Frontend:

```powershell
cd frontend
npm run dev
```

### Gunicorn

Topico exigido pela spec. O pacote está listado em `backend/requirements-integration.txt`, mas o runtime com Gunicorn ainda não foi validado neste repositório no Windows. Se o deploy for feito em Linux depois da adaptação de ambiente, o comando base esperado será:

```bash
gunicorn config.wsgi:application --chdir backend --bind 0.0.0.0:8000
```

Trate isso como preparação futura, não como procedimento homologado do estado atual.

## Cron

Topico exigido pela spec. Ainda não existe scheduler versionado no repositório.

Sugestão operacional mínima quando houver ambiente Linux:

- sincronização periódica de catálogos via `python backend/manage.py sync_catalogs --format=json`
- health snapshot via `python backend/manage.py system_status --format=json`

Essas execuções ainda não estão empacotadas como rotina oficial.

## Validacao pos-deploy

1. Verifique live health:
   - `GET /api/v1/health/live`
2. Verifique dependências:
   - `GET /api/v1/health/dependencies`
3. Valide login com usuário ativo.
4. Rode uma sincronização manual.
5. Consulte `GET /api/v1/sync/runs`.
6. Execute uma conferência em janela curta.

## Rollback

Procedimento conservador para o estado atual:

1. Pare backend e frontend.
2. Restaure a cópia anterior do diretório do projeto ou do artefato implantado.
3. Se houve alteração de banco SQLite, restaure o arquivo `backend/db.sqlite3` do backup anterior.
4. Reexecute:
   - `python backend\manage.py migrate`
   - `python backend\manage.py check`
5. Suba a aplicação novamente e valide health.

Como ainda não existe pipeline formal de release, o rollback atual depende de backup de código e banco antes da mudança.

## Deploy Ubuntu isolado

Para servidores Ubuntu com outras aplicacoes ja em execucao, use os templates em `deploy/ubuntu/`:

- `deploy/ubuntu/chemanalytics.service`
- `deploy/ubuntu/nginx.chemanalytics.conf`
- `deploy/ubuntu/chemanalytics.env.example`
- `deploy/ubuntu/README.md`

Esse pacote assume isolamento por:

- usuario dedicado
- diretorio dedicado
- virtualenv dedicado
- bind interno em `127.0.0.1:8010`
- server block proprio no Nginx

Assim o deploy evita conflito direto com as demais aplicacoes do servidor.
