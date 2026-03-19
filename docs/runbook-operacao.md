# Runbook Operacao

## Objetivo

Referência rápida para diagnóstico e resposta operacional do MVP no estado atual.

## Validar Oracle

1. Verifique a variável `ORACLE_DSN` no `.env`.
2. Rode:

```powershell
python backend\manage.py system_status --format=json
```

3. Interprete:
   - `not_configured`: `ORACLE_DSN` ausente
   - `unavailable`: pacote `oracledb` não instalado no bootstrap atual
   - `configured`: dependência pronta para integração futura

Para teste offline use fixture:

- `ORACLE_FIXTURE_PATH`
- `ORACLE_RECONCILIATION_FIXTURE_PATH`

## Rodar sincronizacao manual

Via CLI:

```powershell
python backend\manage.py sync_catalogs --format=json
```

Via API:

- `POST /api/v1/sync/run`

Conferência posterior:

- `GET /api/v1/sync/runs`
- `GET /api/v1/health/dependencies`

## Investigar falha de conferencia

1. Verifique se o Oracle mock/fixture ou conexão está disponível.
2. Rode `system_status`:

```powershell
python backend\manage.py system_status --format=json
```

3. Confirme se a fórmula existe para `codpro`, `codder` e data do lote.
4. Consulte o histórico:
   - `GET /api/v1/reconciliation/runs`
   - `GET /api/v1/reconciliation/runs/{run_id}`
   - `GET /api/v1/reconciliation/lots/{lot_id}`
5. Procure por códigos de inconsistência:
   - `formula_not_found`
   - `chemical_not_in_formula`
   - `formula_item_incomplete`
   - `formula_item_without_usage`
   - `predicted_zero`
   - `inactive_or_stale_catalog_code`

## Resetar senha

Requer perfil `admin`.

1. Liste usuários:
   - `GET /api/v1/admin/users`
2. Resete a senha:
   - `POST /api/v1/admin/users/{user_id}/reset-password`
3. O usuário receberá `must_change_password = true` no próximo login.

## Inativar usuario

Requer perfil `admin`.

1. Altere o usuário:
   - `PATCH /api/v1/admin/users/{user_id}`
2. Payload mínimo:

```json
{
  "is_active": false
}
```

3. Valide que o login passa a retornar `USER_INACTIVE`.

## Checar ultima sincronizacao

1. API dedicada:
   - `GET /api/v1/sync/runs`
2. Health consolidado:
   - `GET /api/v1/health/dependencies`
3. Interpretação do `last_sync`:
   - `not_available`: nenhuma sincronização registrada
   - `running`: job ainda em execução
   - `ok`: última sincronização concluída com sucesso
   - `error`: última sincronização falhou

## Checar health dependencies

Requer perfil `admin`.

- `GET /api/v1/health/dependencies`

Campos relevantes:

- `database`
- `mysql`
- `oracle`
- `last_sync`

## Localizar logs

Os logs da aplicação ficam em:

- `backend/logs/app.log`

Eventos úteis já implementados:

- login bem-sucedido e falho
- logout
- troca de senha
- criação e alteração administrativa de usuários

## Comandos uteis

```powershell
python backend\manage.py check
python backend\manage.py system_status --format=json
python backend\manage.py sync_catalogs --format=json
python backend\manage.py bootstrap_formulas imports\PREVISAO_CONSUMO_PQ.xlsx --format=json
```

## Limitacoes atuais

- Deploy homologado apenas em modo local com SQLite.
- Gunicorn, cron e MySQL ainda não foram validados no código atual.
- Integração Oracle real depende da instalação de `backend\requirements-integration.txt`.
