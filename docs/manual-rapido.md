# Manual Rapido

## Objetivo

Guia curto para o uso operacional do MVP do ChemAnalytics no estado atual do projeto.

## Acesso inicial

1. Acesse o frontend local configurado para o ambiente.
2. Faça login com usuário ativo.
3. Se `must_change_password` estiver ativo, troque a senha no primeiro acesso.

## Login

- Endpoint backend: `POST /api/v1/auth/login`
- Retorna `access`, `refresh` e dados básicos do usuário.
- Usuário inativo recebe `USER_INACTIVE` e não autentica.

## Troca de senha

- Endpoint: `POST /api/v1/auth/change-password`
- Requer `current_password` e `new_password`.
- Quando concluída, limpa `must_change_password`.

## Cadastro de formula

- Endpoint: `POST /api/v1/formulas`
- Perfil recomendado: `admin`
- O payload cria a fórmula base, a versão inicial e os itens químicos.
- Use o bootstrap inicial quando a carga vier de planilha:
  - `python backend\manage.py bootstrap_formulas imports\PREVISAO_CONSUMO_PQ.xlsx --format=json`

## Nova versao de formula

- Endpoint: `POST /api/v1/formulas/{formula_id}/versions`
- A versão anterior é fechada automaticamente quando a nova entra em vigor.
- Versões já usadas em reconciliação não devem ser alteradas.

## Sincronizacao manual

- Endpoint: `POST /api/v1/sync/run`
- Alternativa CLI:
  - `python backend\manage.py sync_catalogs --format=json`
- Consulte o histórico em:
  - `GET /api/v1/sync/runs`

## Execucao de conferencia

- Endpoint: `POST /api/v1/reconciliation/runs`
- Perfis autorizados: `reviewer` e `admin`
- Filtros mínimos:
  - `date_start`
  - `date_end`
- Filtros opcionais:
  - `nf1`
  - `codpro`
  - `codder`
  - `chemical_code`
  - `only_divergences`
  - `only_inconsistencies`

## Revisao manual

- Endpoint: `POST /api/v1/reconciliation/items/{item_id}/reviews`
- Perfis autorizados: `reviewer` e `admin`
- Campos obrigatórios:
  - `reviewed_status`
  - `justification`
- A revisão não apaga o cálculo original; ela gera trilha própria e atualiza o `status_final`.

## Leitura de inconsistencias

- Histórico de runs:
  - `GET /api/v1/reconciliation/runs`
- Resumo por lote:
  - `GET /api/v1/reconciliation/runs/{run_id}`
- Detalhe por item químico:
  - `GET /api/v1/reconciliation/lots/{lot_id}`
- Principais códigos já implementados:
  - `formula_not_found`
  - `chemical_not_in_formula`
  - `formula_item_incomplete`
  - `formula_item_without_usage`
  - `predicted_zero`
  - `inactive_or_stale_catalog_code`

## Gestao de usuarios

- Listar e criar:
  - `GET/POST /api/v1/admin/users`
- Alterar perfil ou inativar:
  - `PATCH /api/v1/admin/users/{user_id}`
- Resetar senha:
  - `POST /api/v1/admin/users/{user_id}/reset-password`
- Auditoria:
  - `GET /api/v1/admin/audit-log`
