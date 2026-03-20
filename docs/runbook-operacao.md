# Runbook Operacao

## Objetivo

Referencia rapida para diagnostico e resposta operacional do ChemAnalytics no estado validado atual.

## Estado validado atual

- deploy isolado em Ubuntu com `systemd` + Nginx
- backend Django com SQLite local
- frontend publicado via `chemanalytics.viposa.local`
- integracao Oracle real validada para sincronizacao de catalogos
- reconciliacao real validada com dados Oracle
- carga inicial de formulas executada a partir de `imports/PREVISAO_CONSUMO_PQ.xlsx`

## Validar health geral

```powershell
python backend\manage.py system_status --format=json
```

Interpretacao rapida:

- `live.status = ok`: backend respondendo
- `dependencies.status = ok`: dependencias principais operacionais
- `last_sync.status = ok`: ultima sincronizacao concluida com sucesso

## Validar Oracle

No `.env`, configurar uma destas formas:

- `ORACLE_DSN`
- ou `ORACLE_HOST` + `ORACLE_PORT` + `ORACLE_SERVICE_NAME`

Tambem sao obrigatorios:

- `ORACLE_USER`
- `ORACLE_PASSWORD`

Teste rapido de conexao manual:

```bash
set -a
source /opt/chemanalytics/.env
set +a
python -c "import os,oracledb; dsn=os.getenv('ORACLE_DSN') or oracledb.makedsn(os.getenv('ORACLE_HOST'), int(os.getenv('ORACLE_PORT','1521')), service_name=os.getenv('ORACLE_SERVICE_NAME')); conn=oracledb.connect(user=os.getenv('ORACLE_USER'), password=os.getenv('ORACLE_PASSWORD'), dsn=dsn); print('oracle ok'); conn.close()"
```

Interpretacao:

- `not_configured`: Oracle ausente no `.env`
- `unavailable`: pacote `oracledb` nao instalado
- `configured`: configuracao presente
- `oracle ok`: conexao manual validada

## Rodar sincronizacao manual

Via CLI:

```powershell
python backend\manage.py sync_catalogs --format=json
```

Depois conferir:

- `GET /api/v1/sync/runs`
- `GET /api/v1/health/dependencies`

Resultado validado em 2026-03-19:

- `articles = 26`
- `chemicals = 1803`
- `status = success`

## Carga inicial de formulas

Executar apenas uma vez para iniciar a base de formulas:

```powershell
python backend\manage.py bootstrap_formulas imports\PREVISAO_CONSUMO_PQ.xlsx --format=json
```

Resultado validado em 2026-03-19:

- `formulas_created = 13`
- `versions_created = 14`
- `items_created = 352`
- `incomplete_items_created = 10`
- `rejected_rows = []`

Observacao:

- este comando deve ser tratado como bootstrap inicial
- nao usar como rotina recorrente
- novas formulas e versionamentos devem seguir pelo fluxo administrativo da aplicacao

## Investigar falha de conferencia

1. Rode:

```powershell
python backend\manage.py system_status --format=json
```

2. Confirme se o Oracle esta configurado e sincronizado.
3. Confirme se existe formula para `codpro`, `codder` e data do lote.
4. Consulte:
   - `GET /api/v1/reconciliation/runs`
   - `GET /api/v1/reconciliation/runs/{run_id}`
   - `GET /api/v1/reconciliation/lots/{lot_id}`
5. Procure por `inconsistency_code`:
   - `formula_not_found`
   - `chemical_not_in_formula`
   - `formula_item_incomplete`
   - `formula_item_without_usage`
   - `predicted_zero`
   - `inactive_or_stale_catalog_code`

Leitura importante:

- se todos os itens vierem com `formula_not_found`, Oracle e motor podem estar corretos; o gap esta no cadastro de formulas

## Resetar senha

Requer perfil `admin`.

1. Liste usuarios:
   - `GET /api/v1/admin/users`
2. Resete:
   - `POST /api/v1/admin/users/{user_id}/reset-password`
3. O usuario volta com `must_change_password = true`

## Inativar usuario

Requer perfil `admin`.

Payload minimo:

```json
{
  "is_active": false
}
```

Validar depois:

- login deve retornar `USER_INACTIVE`

## Checar ultima sincronizacao

1. `GET /api/v1/sync/runs`
2. `GET /api/v1/health/dependencies`

Interpretacao do `last_sync`:

- `not_available`
- `running`
- `ok`
- `error`

## Localizar logs

Logs da aplicacao:

- `backend/logs/app.log`

Eventos uteis:

- login bem-sucedido e falho
- logout
- troca de senha
- criacao e alteracao administrativa de usuarios
- falha e sucesso de sincronizacao

## Atualizacao segura no Ubuntu

```bash
sudo -u chemanalytics -H bash
cd /opt/chemanalytics
git pull origin chore/ubuntu-deploy-templates
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
python -m pip install -r backend/requirements-integration.txt
python backend/manage.py migrate
python backend/manage.py collectstatic --noinput
python backend/manage.py check
cd frontend
npm ci
npm run build
```

Depois:

```bash
sudo systemctl restart chemanalytics
sudo systemctl status chemanalytics
sudo nginx -t
sudo systemctl reload nginx
```

## Comandos uteis

```powershell
python backend\manage.py check
python backend\manage.py system_status --format=json
python backend\manage.py sync_catalogs --format=json
python backend\manage.py bootstrap_formulas imports\PREVISAO_CONSUMO_PQ.xlsx --format=json
```

## Limitacoes atuais

- deploy homologado em Ubuntu isolado com SQLite local
- Gunicorn e Nginx ja validados no servidor Ubuntu
- cron e MySQL ainda nao foram fechados como rotina operacional oficial
- integracao Oracle real depende da conectividade correta e da manutencao do contrato das views
