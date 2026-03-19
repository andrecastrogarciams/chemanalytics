# MVP Readiness Review

## Objetivo

Checklist operacional para decisao `go/no-go` do MVP do ChemAnalytics no estado atual do repositorio.

## Escopo do review

Este review cobre o fluxo principal ja implementado:

1. autenticacao e perfis
2. sincronizacao de catalogos
3. carga inicial de formulas
4. execucao de conferencia
5. revisao manual
6. consulta de historico
7. gestao de usuarios
8. operacao basica e documentacao

## Premissas

- O estado validado atual do MVP usa SQLite local.
- Integracao Oracle real depende de ambiente e `backend\requirements-integration.txt`.
- MySQL, Gunicorn e cron continuam fora do caminho homologado atual.

## Responsaveis sugeridos

- Produto/PM: decidir `go/no-go`
- QA: executar roteiro e registrar evidencias
- TI/Operacao: validar documentacao e bootstrap
- Usuario interno chave: validar aderencia minima do fluxo

## Roteiro de execucao

### 1. Preparacao do ambiente

- [x] Copiar `.env.example` para `.env`
- [x] Preencher `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `FRONTEND_URL`
- [x] Subir backend conforme [install-deploy.md](C:/Users/ANDREGARCIA/ChemAnalytics_v3/docs/install-deploy.md)
- [x] Subir frontend conforme [install-deploy.md](C:/Users/ANDREGARCIA/ChemAnalytics_v3/docs/install-deploy.md)
- Evidencia:
  - Deploy isolado validado em Ubuntu com `systemd`, Nginx e hostname interno `chemanalytics.viposa.local`
  - Frontend publicado com `VITE_API_BASE_URL=/api`

### 2. Health e status operacional

- [x] `GET /api/v1/health/live` retorna `ok`
- [x] `GET /api/v1/health/dependencies` responde para perfil `admin`
- [x] `python backend\manage.py system_status --format=json` executa sem erro
- Evidencia:
  - `health/live` validado no servidor e via hostname interno
  - `system_status` em 2026-03-19 retornou `dependencies.status = ok`

### 3. Autenticacao e perfis

- [x] Usuario ativo autentica com sucesso
- [ ] Usuario inativo recebe `USER_INACTIVE`
- [ ] Perfil `consulta` nao acessa endpoint restrito de `reviewer`
- [ ] Troca de senha limpa `must_change_password`
- Evidencia:
  - Login JWT validado com usuario `andre` no ambiente Ubuntu
  - UI saiu de `Visual demo` apos autenticacao real

### 4. Formulas e governanca

- [x] Bootstrap de formulas roda com `imports\PREVISAO_CONSUMO_PQ.xlsx`
- [x] Formula e versao inicial ficam persistidas
- [ ] Nova versao de formula pode ser criada
- [ ] Versao usada em reconciliacao nao pode ser editada
- Evidencia:
  - Bootstrap inicial executado em 2026-03-19 com resultado:
    - `formulas_created = 13`
    - `versions_created = 14`
    - `items_created = 352`
    - `incomplete_items_created = 10`
    - `rejected_rows = []`

### 5. Sincronizacao de catalogos

- [x] `python backend\manage.py sync_catalogs --format=json` executa
- [ ] `GET /api/v1/sync/runs` lista a ultima sincronizacao
- [x] `health/dependencies` reflete `last_sync`
- Evidencia:
  - Sincronizacao Oracle real validada em 2026-03-19
  - Resultado da ultima execucao:
    - `articles = 26`
    - `chemicals = 1803`
    - `status = success`

### 6. Conferencia operacional

- [x] `POST /api/v1/reconciliation/runs` executa com janela valida
- [x] A conferencia persiste `run`, `lotes` e `itens`
- [ ] Pelo menos um caso divergente e um inconsistente ficam identificaveis
- [x] O detalhe mostra codigos de inconsistencia compreensiveis
- Evidencia:
  - Runs reais executadas com sucesso no ambiente Oracle
  - Exemplo validado:
    - `run.id = 5`
    - `processed_lots = 8`
    - `processed_items = 200`
    - `execution_time_ms = 9205`
  - No primeiro ciclo, o detalhe do lote mostrou `formula_not_found`, o que levou ao bootstrap inicial das formulas
  - Apos a carga inicial, a UI passou a retornar validacoes reais no navegador

### 7. Revisao manual

- [ ] Apenas `reviewer` ou `admin` conseguem revisar
- [ ] Revisao exige `justification`
- [ ] Revisao cria trilha imutavel
- [ ] `status_calculated` permanece preservado
- [ ] `status_final` do item e do lote reflete o override mais recente
- Evidencia:

### 8. Historico e navegacao

- [x] `GET /api/v1/reconciliation/runs` lista execucoes historicas
- [x] `GET /api/v1/reconciliation/runs/{run_id}` mostra resumo por lote
- [x] `GET /api/v1/reconciliation/lots/{lot_id}` mostra detalhe por item
- [ ] Perfil `consulta` consegue navegar pelo historico
- Evidencia:
  - Historico e detalhe validados via API no ambiente Ubuntu com dados reais
  - A UI navegou os resultados da reconciliação no navegador

### 9. Gestao de usuarios

- [ ] `admin` consegue criar usuario
- [ ] `admin` consegue alterar perfil
- [ ] `admin` consegue inativar usuario
- [ ] `admin` consegue resetar senha
- [ ] `GET /api/v1/admin/audit-log` mostra acoes administrativas relevantes
- Evidencia:

### 10. Documentacao operacional

- [ ] [manual-rapido.md](C:/Users/ANDREGARCIA/ChemAnalytics_v3/docs/manual-rapido.md) e utilizavel por operador tecnico
- [ ] [install-deploy.md](C:/Users/ANDREGARCIA/ChemAnalytics_v3/docs/install-deploy.md) descreve corretamente o caminho homologado atual
- [ ] [runbook-operacao.md](C:/Users/ANDREGARCIA/ChemAnalytics_v3/docs/runbook-operacao.md) cobre incidentes basicos
- [ ] Nao existe dependencia critica de conhecimento tacito para o primeiro uso
- Evidencia:

## Criterios de aceite final

### Go

Marcar `GO` se:

- o fluxo ponta a ponta executa sem mudanca de codigo
- os endpoints principais respondem conforme esperado
- historico e auditoria permanecem consistentes
- QA esta em `PASS`
- os riscos remanescentes estao explicitamente aceitos

### No-Go

Marcar `NO-GO` se:

- houver quebra no fluxo principal do negocio
- a documentacao nao for suficiente para um operador tecnico
- persistencia historica ou auditoria falhar
- algum passo exigir intervencao de desenvolvimento para uso basico

## Riscos remanescentes conhecidos

- Deploy homologado em Ubuntu isolado com SQLite local e frontend publicado via Nginx
- Integracao Oracle real validada para sincronizacao de catalogos e consulta de reconciliacao
- MySQL, Gunicorn e cron ainda nao foram fechados como esteira operacional
- Nao existe pipeline formal de release/rollback automatizado

## Resultado do review

- Data: 2026-03-19
- Responsavel: Codex + validacao operacional em servidor Ubuntu
- Status final: `GO` parcial para fluxo tecnico principal / `PENDENTE` para aceite funcional completo
- Observacoes:
  - Deploy isolado validado em Ubuntu
  - Oracle real validado para conexao, catalogos e execucao de conferencia
  - Bootstrap inicial de formulas executado uma unica vez com a planilha `imports/PREVISAO_CONSUMO_PQ.xlsx`
  - Ainda faltam evidencias formais de revisao manual ponta a ponta e navegacao por perfil `consulta`
- Acoes pos-review:
  - Validar revisao manual com item real divergente
  - Validar navegacao somente leitura com perfil `consulta`
  - Registrar aceite funcional com usuario interno

## Pre-check tecnico executado em 2026-03-18

### Evidencias automaticas

- Suite backend principal:
  - `python backend\manage.py test apps.accounts apps.formulas apps.catalog apps.reconciliation apps.health`
  - Resultado: `46` testes passando
- Health operacional:
  - `python backend\manage.py check`
  - Resultado: `System check identified no issues`
- Status consolidado:
  - `python backend\manage.py system_status --format=json`
  - Resultado: `live.status = ok`, `dependencies.status = ok`
- Bootstrap de formulas:
  - `python backend\manage.py bootstrap_formulas imports\PREVISAO_CONSUMO_PQ.xlsx --format=json`
  - Resultado local atual: sem novas criacoes e sem rejeicoes
- Sincronizacao manual com fixture:
  - `$env:ORACLE_FIXTURE_PATH='backend\apps\catalog\fixtures\oracle_fixture.json'; python backend\manage.py sync_catalogs --format=json`
  - Resultado: `status = success`

### Observacoes do pre-check

- O pre-check confirmou coerencia tecnica do backend e dos comandos principais.
- Durante a validacao foi corrigido um bug no adapter de reconciliacao para tratar fixture Oracle invalida como indisponibilidade operacional, em vez de quebrar com `FileNotFoundError`.
- Ainda falta walkthrough humano dos documentos e aceite funcional por usuario interno para fechar `GO` definitivo.
