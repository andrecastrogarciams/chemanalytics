
# SPEC - chemanalytics MVP v1

## METADADOS
- **Baseado em:** PRD v1.0
- **Arquiteto:** AI-Generated
- **Data:** 2026-03-18
- **Complexidade:** Alta
- **Estimativa:** 120 a 160 horas de desenvolvimento para 1 desenvolvedor, sem contar homologação de negócio
- **Status:** Draft

---

## 1. RESUMO EXECUTIVO

Será implementado um sistema interno chamado **chemanalytics** para governança de fórmulas químicas versionadas e conferência operacional de recurtimento. O sistema terá **backend Django com API REST**, **frontend React** desacoplado, **MySQL** como banco principal da aplicação e **Oracle** como fonte externa de dados operacionais e de cadastros auxiliares.

A aplicação permitirá cadastrar fórmulas por **CODPRO + CODDER**, controlar vigência por versão, sincronizar cache local de artigos/derivações/produtos químicos a partir do Oracle, executar conferências por período e persistir histórico congelado por execução, inclusive com trilha de revisão manual no nível de item químico.

**Input:** credenciais locais, cadastros de fórmula, filtros de conferência, dados lidos do Oracle, revisão manual com justificativa.  
**Processamento:** validação de autenticação, sincronização de cache, seleção da fórmula vigente, cálculo de previsto, cálculo de desvio percentual, classificação de status, persistência histórica, auditoria.  
**Output:** API REST, telas web React, histórico de conferências, resumo por NF1, detalhe por item químico, relatório de divergências e inconsistências.

---

## 2. DECISÕES ARQUITETURAIS

### 2.1 Stack Técnico
- **Backend:** Python 3.12.3 + Django 5.x + Django REST Framework
- **Frontend:** React 18.x + Vite + React Router
- **Database:** MySQL 8.0.42
- **Banco externo:** Oracle via biblioteca `oracledb`
- **Autenticação API:** JWT com `djangorestframework-simplejwt`
- **Build/deploy:** deploy manual em servidor on-premise
- **Agendamento:** cron do sistema operacional
- **Servidor WSGI:** gunicorn
- **Coleta de assets do backend:** `collectstatic`
- **UI framework:** nenhum framework visual obrigatório
- **HTTP client frontend:** axios
- **Migração inicial da planilha:** script externo em `scripts/`

### 2.2 Padrões Adotados
- **Arquitetura:** monólito lógico com backend e frontend desacoplados em pastas separadas (`/backend` e `/frontend`)
- **Padrão de integração:** API REST JSON síncrona
- **Nomenclatura:** classes em `CamelCase`; tabelas, colunas, endpoints, módulos e variáveis em `snake_case`/`kebab-case` conforme contexto
- **Persistência:** MySQL para dados da aplicação e histórico; Oracle apenas leitura
- **Autorização:** `accounts.User` customizado + grupos do Django (`admin`, `reviewer`, `consulta`)
- **Auditoria:** tabela separada `audit_events`
- **Inativação:** campo booleano `is_active` ou `active`, nunca exclusão física para entidades históricas
- **Tratamento de erro:** resposta REST padronizada com `code`, `message`, `details`
- **Logging:** arquivo local + stdout/journalctl, com rotação por `logrotate`
- **Versionamento Git:** `develop` = homologação, `main` = produção

### 2.3 Trade-offs e Justificativas

**Decisão:** usar backend Django REST + frontend React desacoplado.  
**Motivo:** o usuário definiu frontend React separado consumindo API REST; isso evita mistura de responsabilidades e permite evolução independente.  
**Referência PRD:** Seção 12 (stack), complementada pelas respostas técnicas da entrevista.

**Decisão:** usar JWT em vez de sessão/cookie.  
**Motivo:** o frontend é separado e consumirá a API de forma explícita; JWT simplifica autenticação entre aplicações desacopladas.  
**Referência PRD:** Seção 5.8 e resposta técnica sobre autenticação.

**Decisão:** usar Oracle apenas como fonte de leitura e MySQL como fonte oficial da aplicação.  
**Motivo:** preserva independência operacional do cadastro e do histórico, reduz acoplamento e atende ao PRD.  
**Referência PRD:** Seções 5.3, 5.4, 6 e 14.

**Decisão:** persistir conferência congelada por execução.  
**Motivo:** evita distorção entre dado atual de fórmula e histórico operacional analisado no passado.  
**Referência PRD:** Seções 5.5, 20.3 e conclusão.

**Decisão:** revisão manual imutável via tabela própria de revisões.  
**Motivo:** o PRD exige rastreabilidade por usuário/data/hora/justificativa; sobrescrever revisão destruiria trilha histórica.  
**Referência PRD:** Seções 5.5, 5.6, 9 e 20.

**Decisão:** sem Celery, Redis, WebSocket ou fila.  
**Motivo:** volume baixo, até 10 usuários simultâneos e objetivo de simplicidade operacional.  
**Referência PRD:** Seções 7, 12, 16 e 19.

**Decisão:** usar `cron` em vez de scheduler embutido em aplicação.  
**Motivo:** foi definido explicitamente pelo usuário; evita processo adicional no Django.  
**Referência PRD:** Seção 13 e resposta técnica.

**Decisão:** não usar `QTDPRV` do Oracle no cálculo oficial.  
**Motivo:** a regra oficial do previsto deve ser calculada pela fórmula vigente da aplicação, usando peso do lote e percentual da fórmula.  
**Referência PRD:** Seção 5.4 e resposta técnica sobre cálculo.

---

## 3. ARQUITETURA DE ALTO NÍVEL

### 3.1 Fluxo de Dados

```text
Usuário
  ↓
Frontend React (/frontend)
  ↓ HTTP JSON + JWT
Backend Django REST (/backend)
  ├─ MySQL (cadastros, fórmulas, histórico, usuários, auditoria)
  ├─ Oracle (leitura operacional e cache auxiliar)
  └─ Cron + management command (sincronização 06:00 e 13:00)

Fluxo de conferência:
Usuário → Frontend → POST /reconciliation/runs
        → Backend valida filtros
        → Backend consulta Oracle
        → Backend localiza fórmula vigente por item/lote
        → Backend calcula previsto/desvio/status
        → Backend grava run + lotes + itens + auditoria no MySQL
        → Frontend exibe resumo por NF1 e detalhe por item químico
```

### 3.2 Componentes Envolvidos

- **Frontend**
  - Login
  - Troca obrigatória de senha
  - Dashboard inicial
  - Cadastro de fórmulas
  - Histórico/versionamento
  - Sincronização manual
  - Execução de conferência
  - Resumo por NF1
  - Detalhe do lote
  - Relatório de divergências
  - Gestão de usuários

- **Backend**
  - `accounts`
  - `catalog`
  - `formulas`
  - `oracle_sync`
  - `reconciliation`
  - `audit`
  - `core` (health/config utilitários)

- **Database (MySQL)**
  - usuários
  - grupos/permissões
  - artigos em cache
  - produtos químicos em cache
  - fórmulas
  - versões
  - itens de fórmula
  - execuções
  - resultados por lote
  - resultados por item
  - revisões manuais
  - eventos de auditoria
  - histórico de sincronização

- **Externos**
  - Oracle views:
    - `USU_VBI_OPREC_V2`
    - `USU_VBI_QUIREC_V2`
    - `USU_VBI_ARTIGOS_SEMI_NOA`
    - `USU_VBI_EQ_PRODUTOS`

---

## 4. ESTRUTURA DE ARQUIVOS

### 4.1 Estrutura raiz obrigatória

```text
/home/tap/chemanalytics/
├── backend/
├── frontend/
├── docs/
├── scripts/
├── .env.example
├── README.md
└── deploy/
```

### 4.2 Arquivos a CRIAR

#### `/home/tap/chemanalytics/backend/manage.py`
Arquivo padrão de entrada do Django.

#### `/home/tap/chemanalytics/backend/config/settings/base.py`
Responsável por configurações base:
- apps instaladas
- REST Framework
- banco MySQL
- logging
- JWT
- user model customizado
- timezone
- static files

#### `/home/tap/chemanalytics/backend/config/settings/dev.py`
Configuração de homologação/desenvolvimento.

#### `/home/tap/chemanalytics/backend/config/settings/prod.py`
Configuração de produção.

#### `/home/tap/chemanalytics/backend/config/urls.py`
Registro central de rotas:
- `/api/v1/auth/`
- `/api/v1/users/`
- `/api/v1/catalog/`
- `/api/v1/formulas/`
- `/api/v1/reconciliation/`
- `/api/v1/sync/`
- `/api/v1/health/`

#### `/home/tap/chemanalytics/backend/apps/accounts/models.py`
Definir `User` customizado com:
- herança de `AbstractUser`
- `must_change_password: bool`
- `created_at`, `updated_at`, `created_by`, `updated_by`
- manter `is_active` do Django

#### `/home/tap/chemanalytics/backend/apps/accounts/serializers.py`
Serializers de login, troca de senha, usuário, reset de senha, alteração de perfil.

#### `/home/tap/chemanalytics/backend/apps/accounts/views.py`
Viewsets/APIs:
- login JWT
- refresh token
- logout com blacklist
- change password
- CRUD de usuários
- reset de senha
- ativar/inativar usuário

#### `/home/tap/chemanalytics/backend/apps/catalog/models.py`
Tabelas de cache local:
- `ArticleCatalog`
- `ChemicalProductCatalog`
- `SyncJobRun`

#### `/home/tap/chemanalytics/backend/apps/catalog/services.py`
Serviços de leitura do cache.

#### `/home/tap/chemanalytics/backend/apps/formulas/models.py`
Models:
- `Formula`
- `FormulaVersion`
- `FormulaItem`

#### `/home/tap/chemanalytics/backend/apps/formulas/services.py`
Serviços de regra de negócio:
- criação de fórmula
- edição de versão nunca usada
- criação de nova versão
- validação de sobreposição
- cálculo de encerramento automático da versão anterior
- validação de itens duplicados

#### `/home/tap/chemanalytics/backend/apps/formulas/serializers.py`
Serializers de criação, atualização, listagem e detalhamento.

#### `/home/tap/chemanalytics/backend/apps/formulas/views.py`
Endpoints REST para fórmulas e versionamento.

#### `/home/tap/chemanalytics/backend/apps/oracle_sync/client.py`
Cliente Oracle com `oracledb`:
- conexão
- execução de queries parametrizadas
- tratamento de erro
- timeout
- mapeamento de cursores em dicionário

#### `/home/tap/chemanalytics/backend/apps/oracle_sync/queries.py`
Queries SQL centralizadas para:
- artigos/derivações
- produtos químicos
- cabeçalho/lote de recurtimento
- consumo químico por lote

#### `/home/tap/chemanalytics/backend/apps/oracle_sync/services.py`
Serviço de sincronização e serviço de consulta operacional.

#### `/home/tap/chemanalytics/backend/apps/oracle_sync/management/commands/sync_oracle_cache.py`
Command executado pelo cron às 06:00 e 13:00.

#### `/home/tap/chemanalytics/backend/apps/reconciliation/models.py`
Models:
- `ReconciliationRun`
- `ReconciliationLotResult`
- `ReconciliationItemResult`
- `ManualReview`

#### `/home/tap/chemanalytics/backend/apps/reconciliation/services.py`
Serviço principal da conferência:
- consulta Oracle
- combinação lote + consumo
- localização de fórmula vigente
- cálculo de previsto/desvio
- classificação de status
- persistência do snapshot operacional
- recomputação de resumo do lote

#### `/home/tap/chemanalytics/backend/apps/reconciliation/serializers.py`
Serializers de execução, filtros, listagem, resumo por NF1, detalhe, revisão manual.

#### `/home/tap/chemanalytics/backend/apps/reconciliation/views.py`
Endpoints REST:
- criar execução
- listar execuções
- listar resumo por NF1
- detalhe do lote
- listar divergências
- criar revisão manual

#### `/home/tap/chemanalytics/backend/apps/audit/models.py`
Tabela `AuditEvent`.

#### `/home/tap/chemanalytics/backend/apps/audit/services.py`
Funções utilitárias para registrar auditoria.

#### `/home/tap/chemanalytics/backend/apps/core/views.py`
Health checks:
- live
- readiness/dependencies

#### `/home/tap/chemanalytics/backend/requirements/base.txt`
Dependências base.

#### `/home/tap/chemanalytics/backend/requirements/dev.txt`
Dependências de desenvolvimento/teste.

#### `/home/tap/chemanalytics/frontend/package.json`
Dependências do app React.

#### `/home/tap/chemanalytics/frontend/src/main.jsx`
Bootstrap do frontend.

#### `/home/tap/chemanalytics/frontend/src/router/index.jsx`
Rotas protegidas e públicas.

#### `/home/tap/chemanalytics/frontend/src/api/http.js`
Instância axios com:
- base URL
- interceptor para `Authorization: Bearer`
- tratamento de 401
- refresh controlado

#### `/home/tap/chemanalytics/frontend/src/store/auth.js`
Armazenamento do estado de autenticação e usuário logado.

#### `/home/tap/chemanalytics/frontend/src/pages/LoginPage.jsx`
Tela de login.

#### `/home/tap/chemanalytics/frontend/src/pages/ForceChangePasswordPage.jsx`
Tela obrigatória de troca de senha.

#### `/home/tap/chemanalytics/frontend/src/pages/DashboardPage.jsx`
Tela inicial com atalhos.

#### `/home/tap/chemanalytics/frontend/src/pages/FormulasPage.jsx`
Listagem e filtros de fórmulas.

#### `/home/tap/chemanalytics/frontend/src/pages/FormulaFormPage.jsx`
Cadastro/edição de versão não usada.

#### `/home/tap/chemanalytics/frontend/src/pages/FormulaVersionPage.jsx`
Histórico/versionamento e criação de nova versão.

#### `/home/tap/chemanalytics/frontend/src/pages/ReconciliationRunPage.jsx`
Execução da conferência.

#### `/home/tap/chemanalytics/frontend/src/pages/ReconciliationRunDetailPage.jsx`
Resumo da execução por NF1.

#### `/home/tap/chemanalytics/frontend/src/pages/LotDetailPage.jsx`
Detalhe do lote por item químico.

#### `/home/tap/chemanalytics/frontend/src/pages/DivergencesPage.jsx`
Relatório de divergências e inconsistências.

#### `/home/tap/chemanalytics/frontend/src/pages/UsersPage.jsx`
Gestão de usuários.

#### `/home/tap/chemanalytics/frontend/src/components/*`
Componentes reutilizáveis:
- tabela
- filtro
- modal
- badge de status
- formulário de revisão
- paginação
- layout

#### `/home/tap/chemanalytics/scripts/import_initial_formulas.py`
Script externo para migração inicial da planilha `PREVISAO_CONSUMO_PQ.xlsx`.

#### `/home/tap/chemanalytics/deploy/cron/chemanalytics_sync.cron`
Arquivo de referência do cron.

#### `/home/tap/chemanalytics/deploy/gunicorn/chemanalytics.service`
Unidade systemd do gunicorn.

#### `/home/tap/chemanalytics/docs/manual-rapido.md`
Manual rápido de uso.

#### `/home/tap/chemanalytics/docs/install-deploy.md`
Documentação técnica de instalação/deploy.

#### `/home/tap/chemanalytics/docs/runbook-operacao.md`
Runbook básico de operação.

### 4.3 Arquivos a MODIFICAR
Projeto novo. Nesta versão da spec não há arquivos existentes a modificar.

---

## 5. MODELOS DE DADOS

### 5.1 Convenções gerais
- Banco principal: MySQL
- Charset: `utf8mb4`
- Todas as tabelas de domínio devem usar `id` autoincrement como PK
- Todas as FKs devem ter índice
- Campos monetários não se aplicam
- Campos numéricos de quantidade/percentual devem usar `DECIMAL`, nunca `FLOAT`
- Convenção padrão:
  - `created_at DATETIME NOT NULL`
  - `updated_at DATETIME NOT NULL`
  - `created_by_id BIGINT NULL`
  - `updated_by_id BIGINT NULL`
- Entidades com inativação devem usar `active BOOLEAN NOT NULL DEFAULT TRUE`
- Histórico operacional nunca pode ser apagado fisicamente pela aplicação

### 5.2 Novos Modelos

#### Model: `accounts_user`
- `id`
- `username` (unique)
- `first_name`
- `last_name`
- `email` (opcional)
- `password`
- `must_change_password BOOLEAN NOT NULL DEFAULT TRUE`
- `is_active BOOLEAN NOT NULL DEFAULT TRUE`
- `is_staff BOOLEAN NOT NULL DEFAULT FALSE`
- `is_superuser BOOLEAN NOT NULL DEFAULT FALSE`
- `last_login DATETIME NULL`
- `created_at`
- `updated_at`
- `created_by_id`
- `updated_by_id`

**Regras**
- `must_change_password = TRUE` em criação inicial e reset
- inativação substitui exclusão
- grupos válidos: `admin`, `reviewer`, `consulta`
- `admin` pode tudo
- `reviewer` pode sincronizar manualmente, executar conferência, revisar manualmente e consultar
- `consulta` pode apenas consultar

#### Model: `catalog_article_catalog`
Armazena artigo/derivação do Oracle.
- `id`
- `codpro VARCHAR(14) NOT NULL`
- `codder VARCHAR(7) NOT NULL`
- `article_description VARCHAR(100) NOT NULL`
- `derivation_description VARCHAR(50) NOT NULL`
- `active BOOLEAN NOT NULL DEFAULT TRUE`
- `source_last_seen_at DATETIME NOT NULL`
- `created_at`
- `updated_at`
- `created_by_id`
- `updated_by_id`

**Constraints**
- `UNIQUE(codpro, codder)`

**Mapeamento Oracle**
- `codpro <= COD_ARTIGO`
- `codder <= COD_DERIVACAO`
- `article_description <= ARTIGO`
- `derivation_description <= DERIVACAO`

#### Model: `catalog_chemical_product_catalog`
Armazena produtos químicos do Oracle.
- `id`
- `chemical_code VARCHAR(14) NOT NULL`
- `description VARCHAR(100) NOT NULL`
- `complement VARCHAR(50) NULL`
- `family_code VARCHAR(6) NULL`
- `unit_of_measure VARCHAR(3) NULL`
- `product_type VARCHAR(2) NULL`
- `product_type_description VARCHAR(15) NULL`
- `source_status CHAR(5) NULL`
- `active BOOLEAN NOT NULL DEFAULT TRUE`
- `source_last_seen_at DATETIME NOT NULL`
- `created_at`
- `updated_at`
- `created_by_id`
- `updated_by_id`

**Constraints**
- `UNIQUE(chemical_code)`

**Regra**
- se o código deixar de existir ou vier desativado do Oracle, manter registro local e marcar `active = FALSE`

#### Model: `catalog_sync_job_run`
Histórico das sincronizações.
- `id`
- `job_type VARCHAR(30) NOT NULL` (`automatic`, `manual`)
- `started_at DATETIME NOT NULL`
- `finished_at DATETIME NULL`
- `status VARCHAR(20) NOT NULL` (`running`, `success`, `error`)
- `records_articles_upserted INT NOT NULL DEFAULT 0`
- `records_products_upserted INT NOT NULL DEFAULT 0`
- `error_message TEXT NULL`
- `triggered_by_id BIGINT NULL`
- `created_at`
- `updated_at`
- `created_by_id`
- `updated_by_id`

#### Model: `formulas_formula`
Entidade lógica do par CODPRO + CODDER.
- `id`
- `codpro VARCHAR(14) NOT NULL`
- `codder VARCHAR(7) NOT NULL`
- `observation TEXT NULL`
- `active BOOLEAN NOT NULL DEFAULT TRUE`
- `created_at`
- `updated_at`
- `created_by_id`
- `updated_by_id`

**Constraints**
- `UNIQUE(codpro, codder)`

**Regra**
- A fórmula lógica representa o par; as vigências ficam em `formula_version`

#### Model: `formulas_formula_version`
Versão por vigência.
- `id`
- `formula_id BIGINT NOT NULL`
- `version_number INT NOT NULL`
- `start_date DATE NOT NULL`
- `end_date DATE NULL`
- `observation TEXT NULL`
- `active BOOLEAN NOT NULL DEFAULT TRUE`
- `used_in_reconciliation BOOLEAN NOT NULL DEFAULT FALSE`
- `created_at`
- `updated_at`
- `created_by_id`
- `updated_by_id`

**Constraints**
- `UNIQUE(formula_id, version_number)`
- índice em `(formula_id, start_date, end_date)`

**Regra de vigência**
- `start_date` inclusiva
- `end_date` inclusiva
- não pode haver sobreposição para o mesmo `formula_id`
- se nova versão iniciar em D, a anterior aberta deve terminar em `D - 1`

#### Model: `formulas_formula_item`
- `id`
- `formula_version_id BIGINT NOT NULL`
- `chemical_code VARCHAR(14) NOT NULL`
- `chemical_description VARCHAR(100) NOT NULL`
- `percentual DECIMAL(10,4) NOT NULL`
- `tolerance_pct DECIMAL(10,2) NOT NULL`
- `active BOOLEAN NOT NULL DEFAULT TRUE`
- `created_at`
- `updated_at`
- `created_by_id`
- `updated_by_id`

**Constraints**
- `UNIQUE(formula_version_id, chemical_code)`

**Regra**
- percentual armazenado em formato humano, por exemplo `4.7000`, nunca `0.047`
- cálculo usa `percentual / 100`

#### Model: `reconciliation_run`
Cabeçalho da execução.
- `id`
- `executed_at DATETIME NOT NULL`
- `executed_by_id BIGINT NOT NULL`
- `date_start DATE NOT NULL`
- `date_end DATE NOT NULL`
- `nf1 VARCHAR(9) NULL`
- `codpro VARCHAR(14) NULL`
- `codder VARCHAR(7) NULL`
- `chemical_code VARCHAR(14) NULL`
- `only_divergences BOOLEAN NOT NULL DEFAULT FALSE`
- `only_inconsistencies BOOLEAN NOT NULL DEFAULT FALSE`
- `status VARCHAR(20) NOT NULL` (`success`, `partial_error`, `error`)
- `processed_lots INT NOT NULL DEFAULT 0`
- `processed_items INT NOT NULL DEFAULT 0`
- `execution_time_ms INT NULL`
- `error_message TEXT NULL`
- `created_at`
- `updated_at`
- `created_by_id`
- `updated_by_id`

**Regra**
- intervalo máximo de 90 dias
- cada execução gera histórico independente

#### Model: `reconciliation_lot_result`
Resumo por NF1 persistido.
- `id`
- `run_id BIGINT NOT NULL`
- `nf1 VARCHAR(9) NOT NULL`
- `recurtimento_date DATE NOT NULL`
- `codpro VARCHAR(14) NOT NULL`
- `codder VARCHAR(7) NOT NULL`
- `lot_weight DECIMAL(12,2) NOT NULL`
- `formula_version_id BIGINT NULL`
- `status_final VARCHAR(20) NOT NULL` (`conform`, `divergent`, `inconsistent`)
- `has_inconsistency BOOLEAN NOT NULL DEFAULT FALSE`
- `has_divergence BOOLEAN NOT NULL DEFAULT FALSE`
- `items_count INT NOT NULL DEFAULT 0`
- `created_at`
- `updated_at`
- `created_by_id`
- `updated_by_id`

**Constraints**
- `UNIQUE(run_id, nf1)`

#### Model: `reconciliation_item_result`
Granularidade oficial do detalhe.
- `id`
- `run_id BIGINT NOT NULL`
- `lot_result_id BIGINT NOT NULL`
- `nf1 VARCHAR(9) NOT NULL`
- `chemical_code VARCHAR(14) NOT NULL`
- `chemical_description VARCHAR(100) NULL`
- `formula_version_id BIGINT NULL`
- `formula_item_id BIGINT NULL`
- `predicted_qty DECIMAL(12,2) NULL`
- `used_qty DECIMAL(12,2) NULL`
- `deviation_pct DECIMAL(10,2) NULL`
- `tolerance_pct DECIMAL(10,2) NULL`
- `status_calculated VARCHAR(20) NOT NULL`
- `status_reviewed VARCHAR(20) NULL`
- `status_final VARCHAR(20) NOT NULL`
- `inconsistency_code VARCHAR(50) NULL`
- `inconsistency_message VARCHAR(255) NULL`
- `manual_review_latest_id BIGINT NULL`
- `created_at`
- `updated_at`
- `created_by_id`
- `updated_by_id`

**Constraints**
- `UNIQUE(run_id, nf1, chemical_code)`

**Regra**
- revisão só é permitida quando `status_calculated != inconsistent`
- `status_final`:
  1. `inconsistent`, se `inconsistency_code` não for nulo
  2. `status_reviewed`, se existir
  3. `status_calculated`, caso contrário

#### Model: `reconciliation_manual_review`
Trilha imutável de revisões.
- `id`
- `item_result_id BIGINT NOT NULL`
- `previous_review_id BIGINT NULL`
- `reviewed_status VARCHAR(20) NOT NULL` (`conform`, `divergent`)
- `justification TEXT NOT NULL`
- `reviewed_by_id BIGINT NOT NULL`
- `reviewed_at DATETIME NOT NULL`
- `created_at`
- `updated_at`
- `created_by_id`
- `updated_by_id`

**Regra**
- não editar registro existente
- nova revisão cria novo registro
- `reconciliation_item_result.manual_review_latest_id` aponta para a revisão mais recente
- ao criar nova revisão, atualizar `status_reviewed` e `status_final` do item e recomputar `status_final` do lote

#### Model: `audit_audit_event`
Auditoria genérica.
- `id`
- `event_type VARCHAR(50) NOT NULL`
- `entity_type VARCHAR(50) NOT NULL`
- `entity_id BIGINT NULL`
- `performed_by_id BIGINT NULL`
- `performed_at DATETIME NOT NULL`
- `payload_json JSON NULL`
- `created_at`
- `updated_at`
- `created_by_id`
- `updated_by_id`

**Event types obrigatórios**
- `login_success`
- `logout`
- `login_failed`
- `formula_created`
- `formula_updated`
- `formula_version_created`
- `formula_version_inactivated`
- `sync_started`
- `sync_finished`
- `sync_failed`
- `reconciliation_started`
- `reconciliation_finished`
- `reconciliation_failed`
- `manual_review_created`
- `user_created`
- `user_updated`
- `user_password_reset`
- `user_inactivated`
- `user_activated`

### 5.3 Modificações em Modelos Existentes
Projeto novo. Não se aplica.

---

## 6. API / ENDPOINTS

### 6.1 Padrão geral de resposta

**Sucesso**
```json
{
  "success": true,
  "data": {},
  "message": "ok"
}
```

**Erro**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Mensagem legível",
    "details": {}
  }
}
```

### 6.2 Autenticação

#### POST `/api/v1/auth/login`
**Auth:** não  
**Body**
```json
{
  "username": "usuario",
  "password": "senha"
}
```

**Response 200**
```json
{
  "success": true,
  "data": {
    "access": "jwt_access",
    "refresh": "jwt_refresh",
    "user": {
      "id": 1,
      "username": "usuario",
      "group": "reviewer",
      "must_change_password": true
    }
  }
}
```

**Regras**
- registrar `login_success` ou `login_failed`
- se `must_change_password = true`, frontend deve redirecionar imediatamente para troca de senha
- conta inativa retorna `403 USER_INACTIVE`

#### POST `/api/v1/auth/refresh`
Renova access token a partir do refresh token.

#### POST `/api/v1/auth/logout`
**Auth:** JWT  
**Body**
```json
{
  "refresh": "jwt_refresh"
}
```
**Regra**
- adicionar refresh token à blacklist
- registrar `logout`

#### POST `/api/v1/auth/change-password`
**Auth:** JWT  
**Body**
```json
{
  "current_password": "atual",
  "new_password": "nova"
}
```

**Regras**
- obrigatória no primeiro login e após reset
- ao concluir com sucesso, marcar `must_change_password = false`

### 6.3 Usuários

#### GET `/api/v1/users`
**Permissão:** admin  
Lista usuários com filtros por nome, username, grupo e ativo.

#### POST `/api/v1/users`
**Permissão:** admin  
Cria usuário manualmente.

**Body mínimo**
```json
{
  "username": "maria",
  "first_name": "Maria",
  "last_name": "Silva",
  "group": "reviewer",
  "temporary_password": "Temp123"
}
```

**Regras**
- `must_change_password = true`
- grupo obrigatório
- `username` único

#### PATCH `/api/v1/users/{id}`
**Permissão:** admin  
Alteração de nome, grupo e ativação.

#### POST `/api/v1/users/{id}/reset-password`
**Permissão:** admin  
Define senha temporária.
```json
{
  "temporary_password": "NovaTemp123"
}
```
**Regra**
- marcar `must_change_password = true`

### 6.4 Catálogo/cache

#### GET `/api/v1/catalog/articles`
**Permissão:** autenticado  
Lista artigos/derivações em cache local.

#### GET `/api/v1/catalog/chemicals`
**Permissão:** autenticado  
Lista produtos químicos em cache local.

#### GET `/api/v1/sync/runs`
**Permissão:** reviewer ou admin  
Lista histórico de sincronizações.

#### POST `/api/v1/sync/run`
**Permissão:** reviewer ou admin  
Dispara sincronização manual.

**Response 202**
```json
{
  "success": true,
  "data": {
    "sync_run_id": 10,
    "status": "running"
  }
}
```

**Regra**
- execução síncrona dentro da própria request é permitida nesta v1
- se o Oracle falhar, retornar erro e registrar `sync_failed`

### 6.5 Fórmulas

#### GET `/api/v1/formulas`
**Permissão:** autenticado  
Filtros:
- `codpro`
- `codder`
- `active`
- `date_reference` (opcional)
- `page`
- `page_size`

#### POST `/api/v1/formulas`
**Permissão:** admin  
Cria a fórmula lógica e a primeira versão.

**Body**
```json
{
  "codpro": "65300278132153",
  "codder": "1",
  "observation": "texto opcional",
  "version": {
    "start_date": "2026-03-18",
    "end_date": null,
    "observation": "vigente inicial",
    "items": [
      {
        "chemical_code": "12345",
        "percentual": 4.7,
        "tolerance_pct": 2.0
      }
    ]
  }
}
```

**Validações**
- `codpro` e `codder` devem existir no cache local
- itens sem duplicidade por `chemical_code`
- produtos químicos devem existir no cache local
- `start_date` obrigatória
- `end_date`, se informada, não pode ser anterior a `start_date`
- não pode existir sobreposição de vigência

#### GET `/api/v1/formulas/{id}`
**Permissão:** autenticado  
Retorna fórmula e versões.

#### PATCH `/api/v1/formulas/versions/{id}`
**Permissão:** admin  
Edita apenas versão nunca usada em conferência.

**Regra**
- se `used_in_reconciliation = true`, retornar `409 FORMULA_VERSION_ALREADY_USED`

#### POST `/api/v1/formulas/{id}/versions`
**Permissão:** admin  
Cria nova versão.

**Body**
```json
{
  "start_date": "2026-04-01",
  "end_date": null,
  "observation": "nova composição",
  "items": [
    {
      "chemical_code": "12345",
      "percentual": 4.5,
      "tolerance_pct": 2.0
    }
  ]
}
```

**Regras**
- encerrar automaticamente a versão anterior em `start_date - 1`
- permitir vigência futura
- impedir sobreposição
- nova versão nasce com `version_number = max + 1`

#### POST `/api/v1/formulas/versions/{id}/inactivate`
**Permissão:** admin  
Inativa versão somente se nunca usada.

#### DELETE `/api/v1/formulas/versions/{id}`
**Permissão:** admin  
Exclusão física somente se nunca usada.  
**Obs:** preferir inativação; exclusão só antes do uso e se não houver impacto referencial.

### 6.6 Conferência

#### POST `/api/v1/reconciliation/runs`
**Permissão:** reviewer ou admin  
Cria uma execução de conferência.

**Body**
```json
{
  "date_start": "2026-03-01",
  "date_end": "2026-03-10",
  "nf1": null,
  "codpro": null,
  "codder": null,
  "chemical_code": null,
  "only_divergences": false,
  "only_inconsistencies": false
}
```

**Validações**
- janela máxima de 90 dias
- `date_start <= date_end`
- filtros opcionais
- se Oracle indisponível, retornar `503 ORACLE_UNAVAILABLE`

**Response 201**
```json
{
  "success": true,
  "data": {
    "run_id": 25,
    "processed_lots": 120,
    "processed_items": 860,
    "status": "success"
  }
}
```

#### GET `/api/v1/reconciliation/runs`
**Permissão:** autenticado  
Lista execuções com filtros por data, usuário e status.

#### GET `/api/v1/reconciliation/runs/{run_id}`
**Permissão:** autenticado  
Retorna cabeçalho da execução.

#### GET `/api/v1/reconciliation/runs/{run_id}/lots`
**Permissão:** autenticado  
Lista resumo por NF1.

**Filtros**
- `status_final`
- `nf1`
- `codpro`
- `codder`

#### GET `/api/v1/reconciliation/runs/{run_id}/lots/{nf1}`
**Permissão:** autenticado  
Retorna detalhe do lote por item químico.

#### GET `/api/v1/reconciliation/runs/{run_id}/divergences`
**Permissão:** autenticado  
Lista apenas itens com `status_final in ('divergent', 'inconsistent')`.

### 6.7 Revisão manual

#### POST `/api/v1/reconciliation/item-results/{id}/review`
**Permissão:** reviewer ou admin  
Cria nova revisão manual para um item.

**Body**
```json
{
  "reviewed_status": "conform",
  "justification": "validado operacionalmente"
}
```

**Validações**
- item não pode ter inconsistência
- `reviewed_status` deve ser `conform` ou `divergent`
- `justification` obrigatória
- nova revisão nunca sobrescreve a anterior; cria nova linha

### 6.8 Health

#### GET `/api/v1/health/live`
**Auth:** não  
Retorna status simples da API.

#### GET `/api/v1/health/dependencies`
**Permissão:** admin  
Retorna:
- app
- mysql
- oracle
- última sincronização

---

## 7. LÓGICA DE NEGÓCIO

### 7.1 Regras matemáticas

#### 7.1.1 Cálculo do previsto
```text
predicted_qty = round(lot_weight * (percentual / 100), 2)
```

#### 7.1.2 Cálculo do desvio percentual
Executar apenas quando:
- existe fórmula vigente
- existe item da fórmula correspondente
- existe consumo Oracle correspondente
- `predicted_qty > 0`

```text
deviation_pct = round(((used_qty - predicted_qty) / predicted_qty) * 100, 2)
```

#### 7.1.3 Regra de status calculado
```text
if inconsistency_code is not null:
    status_calculated = "inconsistent"
else if abs(deviation_pct) <= tolerance_pct:
    status_calculated = "conform"
else:
    status_calculated = "divergent"
```

### 7.2 Taxonomia oficial de inconsistências

Os seguintes cenários DEVEM gerar `status_calculated = inconsistent`:

1. `formula_not_found`
   - não existe fórmula vigente para `codpro + codder` na data do recurtimento

2. `chemical_not_in_formula`
   - produto químico utilizado no Oracle não existe na fórmula vigente

3. `formula_item_without_usage`
   - item da fórmula não possui consumo correspondente no Oracle para o lote

4. `predicted_zero`
   - previsto calculado igual a zero

5. `oracle_query_failure`
   - falha na leitura Oracle durante a execução da conferência

6. `inactive_or_stale_catalog_code`
   - código exigido pela regra está inativo ou ausente no cache local

### 7.3 Regra de resumo por NF1
A prioridade oficial do resumo do lote deve ser:

```text
if existe item inconsistent:
    lot.status_final = "inconsistent"
else if existe item divergent:
    lot.status_final = "divergent"
else:
    lot.status_final = "conform"
```

### 7.4 Localização da fórmula vigente
A data de referência para vigência é a `DATA` do recurtimento vinda do Oracle.

```text
selecionar FormulaVersion onde:
    formula.codpro = lot.codpro
    formula.codder = lot.codder
    start_date <= recurtimento_date
    (end_date is null or end_date >= recurtimento_date)
ordenar por start_date desc
esperar no máximo 1 resultado
```

Se retornar mais de 1, tratar como erro de integridade e bloquear gravação da execução com `partial_error` ou `error`, conforme abrangência.

### 7.5 Fluxo principal de criação de fórmula

```text
1. Admin envia codpro, codder e versão inicial
2. Backend valida existência no cache local
3. Backend valida itens sem duplicidade
4. Backend valida produtos químicos no cache local
5. Backend cria Formula
6. Backend cria FormulaVersion(version_number=1)
7. Backend cria FormulaItem(s)
8. Backend registra audit event
9. Backend retorna 201
```

### 7.6 Fluxo principal de nova versão

```text
1. Admin envia nova data inicial e itens
2. Backend localiza Formula
3. Backend valida que não existe sobreposição
4. Backend localiza última versão aberta/abrangente
5. Backend ajusta end_date da versão anterior para novo_start_date - 1
6. Backend cria nova FormulaVersion com version_number = max + 1
7. Backend cria novos FormulaItem(s)
8. Backend registra auditoria
9. Backend retorna 201
```

### 7.7 Fluxo de edição de versão nunca usada

```text
1. Admin solicita edição de FormulaVersion
2. Backend verifica used_in_reconciliation
3. Se true → retornar 409
4. Se false → permitir atualização de cabeçalho e itens
5. Revalidar duplicidade de item e sobreposição
6. Registrar auditoria
```

### 7.8 Fluxo principal da conferência (happy path)

```text
1. Reviewer/Admin envia filtros
2. Backend valida janela <= 90 dias
3. Backend cria ReconciliationRun(status='running' em memória)
4. Backend consulta Oracle:
   4.1 Cabeçalhos/lotes via USU_VBI_OPREC_V2
   4.2 Consumos por lote via USU_VBI_QUIREC_V2
5. Backend agrupa consumos por NF1
6. Para cada NF1:
   6.1 localizar fórmula vigente por CODPRO+CODDER e DATA
   6.2 criar conjunto união de químicos:
       - todos os itens da fórmula
       - todos os químicos usados no Oracle
   6.3 para cada chemical_code do conjunto:
       a) se fórmula ausente → inconsistency formula_not_found
       b) se químico Oracle não estiver na fórmula → chemical_not_in_formula
       c) se item da fórmula não tiver uso Oracle → formula_item_without_usage
       d) senão calcular previsto/desvio/status
   6.4 persistir ReconciliationLotResult
   6.5 persistir ReconciliationItemResult(s)
7. Backend calcula processed_lots e processed_items
8. Backend grava ReconciliationRun(status='success')
9. Backend marca FormulaVersion.used_in_reconciliation = true para versões usadas
10. Backend registra auditoria
11. Backend retorna run_id
```

### 7.9 Regra de composição do conjunto de químicos do lote
Para garantir que itens faltantes também apareçam no histórico:

```text
chemical_set = union(
    formula_item.chemical_code de formula_version,
    oracle_usage.chemical_code do NF1
)
```

### 7.10 Tratamento de campos numéricos em inconsistência
- `predicted_qty`: `NULL` quando não for possível calcular por ausência de fórmula/item; `0.00` somente quando o cálculo resultar zero
- `used_qty`: `NULL` quando o Oracle falhar; `0.00` quando houver ausência operacional do item
- `deviation_pct`: `NULL` em toda inconsistência

### 7.11 Uso dos dados Oracle
Mapeamento oficial:

#### `USU_VBI_OPREC_V2`
Usar como fonte de cabeçalho do lote/recurtimento:
- `NF1`
- `DATA`
- `CODPRO`
- `CODDER`
- `DESDER`
- `PESO`

#### `USU_VBI_QUIREC_V2`
Usar como fonte de consumo químico do lote:
- `NF1`
- `CODPRO` → código do produto químico
- `DESPRO` → descrição do produto químico
- `QTDUTI` → utilizado real

**Regra explícita:** `QTDPRV` do Oracle não entra no cálculo oficial e não deve ser persistido como previsto do sistema.

#### `USU_VBI_ARTIGOS_SEMI_NOA`
Usar para sincronizar `COD_ARTIGO`, `COD_DERIVACAO`, `ARTIGO`, `DERIVACAO`.

#### `USU_VBI_EQ_PRODUTOS`
Usar para sincronizar `CODIGO_PRODUTO`, `DESCRICAO` e status.

### 7.12 Fluxos alternativos

#### 7.12.1 Oracle indisponível na sincronização
- criar `SyncJobRun(status='error')`
- registrar `sync_failed`
- retornar 503
- frontend exibir mensagem de erro

#### 7.12.2 Oracle indisponível na conferência
- não gravar resultados parciais por lote
- gravar `ReconciliationRun(status='error')` com `error_message`
- registrar `reconciliation_failed`
- retornar 503

#### 7.12.3 Sem fórmula vigente
- criar `ReconciliationLotResult` com `formula_version_id = NULL`, `status_final = inconsistent`
- criar `ReconciliationItemResult` para cada químico usado no Oracle com `formula_not_found`

#### 7.12.4 Item da fórmula sem uso Oracle
- criar item com `used_qty = 0.00`
- `status_calculated = inconsistent`
- `inconsistency_code = formula_item_without_usage`

#### 7.12.5 Químico usado fora da fórmula
- criar item com `formula_item_id = NULL`
- `predicted_qty = NULL`
- `status_calculated = inconsistent`
- `inconsistency_code = chemical_not_in_formula`

#### 7.12.6 Tentativa de revisão em inconsistência
- retornar `409 INCONSISTENT_ITEM_CANNOT_BE_REVIEWED`

---

## 8. INTERFACES (UI/UX)

### 8.1 Regras gerais
- aplicação desktop-first para rede interna
- sem requisito mobile
- navegação via menu lateral ou topo fixo
- sem biblioteca visual obrigatória
- usar HTML semântico + CSS próprio
- mensagens de erro sempre visíveis em tela quando aplicável

### 8.2 Telas obrigatórias

#### Tela: Login
- campos: username, password
- botão entrar
- exibir erro para credenciais inválidas
- se `must_change_password = true`, redirecionar automaticamente

#### Tela: Troca obrigatória de senha
- campos: senha atual, nova senha, confirmar nova senha
- bloqueia acesso às demais rotas enquanto não concluída

#### Tela: Dashboard
- atalhos:
  - fórmulas
  - conferência
  - divergências
  - sincronização
  - usuários (admin)

#### Tela: Listagem de fórmulas
- filtros: codpro, codder, ativo
- tabela com colunas:
  - codpro
  - codder
  - descrição artigo
  - descrição derivação
  - versão vigente
  - vigência
  - ativo
  - ações

#### Tela: Cadastro/edição de fórmula
- apenas admin
- seleção de codpro+codder a partir do cache
- grid de itens químicos com:
  - chemical_code
  - chemical_description
  - percentual
  - tolerance_pct
- impedir item duplicado no frontend antes do submit

#### Tela: Histórico/versionamento
- lista versões por fórmula
- exibir:
  - version_number
  - start_date
  - end_date
  - used_in_reconciliation
  - active
- botão “Nova versão”

#### Tela: Sincronização
- reviewer/admin
- botão “Executar sincronização manual”
- tabela com últimas execuções e status

#### Tela: Execução de conferência
- filtros:
  - date_start
  - date_end
  - nf1
  - codpro
  - codder
  - chemical_code
  - only_divergences
  - only_inconsistencies
- validação local do limite de 90 dias

#### Tela: Resultado da execução
- cabeçalho com metadados da run
- resumo por NF1
- clique abre detalhe do lote

#### Tela: Detalhe do lote
- tabela por item químico:
  - chemical_code
  - chemical_description
  - predicted_qty
  - used_qty
  - deviation_pct
  - tolerance_pct
  - status_calculated
  - status_reviewed
  - status_final
  - inconsistency_message
- ação de revisão apenas para reviewer/admin e apenas em itens não inconsistentes

#### Tela: Relatório de divergências
- filtros por run, status_final, nf1, codpro, codder, chemical_code
- mostra apenas `divergent` e `inconsistent`

#### Tela: Usuários
- apenas admin
- criar usuário
- alterar perfil
- ativar/inativar
- resetar senha

### 8.3 Estados de UI
- `idle`
- `loading`
- `success`
- `error`
- `empty`

### 8.4 Cores de status
- `conform`: verde
- `divergent`: amarelo/laranja
- `inconsistent`: vermelho

### 8.5 Acessibilidade mínima
- foco visível em todos os campos
- labels explícitas
- navegação por teclado
- tabelas com cabeçalho semântico

---

## 9. INTEGRAÇÃO COM SISTEMAS EXTERNOS

### 9.1 Oracle
**Biblioteca:** `oracledb`

### 9.2 Contrato mínimo de conexão
Variáveis de ambiente:
- `ORACLE_HOST`
- `ORACLE_PORT`
- `ORACLE_SERVICE_NAME`
- `ORACLE_USER`
- `ORACLE_PASSWORD`

### 9.3 Queries oficiais

#### 9.3.1 Sincronização de artigos/derivações
```sql
SELECT
  COD_ARTIGO,
  COD_DERIVACAO,
  ARTIGO,
  DERIVACAO
FROM USU_VBI_ARTIGOS_SEMI_NOA
```

#### 9.3.2 Sincronização de produtos químicos
```sql
SELECT
  CODIGO_PRODUTO,
  DESCRICAO,
  COMPLEMENTO,
  CODIGO_FAMILIA,
  UNIDADE_MEDIDA,
  TIPO_PRODUTO,
  DESCRICAO_TIPO,
  STATUS,
  DATA_CONSULTA
FROM USU_VBI_EQ_PRODUTOS
```

#### 9.3.3 Consulta de lotes/recurtimento
```sql
SELECT
  NF1,
  DATA,
  CODPRO,
  CODDER,
  DESDER,
  PESO
FROM USU_VBI_OPREC_V2
WHERE DATA BETWEEN :date_start AND :date_end
```

Adicionar filtros opcionais por `NF1`, `CODPRO`, `CODDER`.

#### 9.3.4 Consulta de consumo químico
```sql
SELECT
  NF1,
  CODPRO,
  DESPRO,
  QTDUTI
FROM USU_VBI_QUIREC_V2
WHERE NF1 IN (:nf1_list)
```

### 9.4 Regras de integração
- Oracle é somente leitura
- queries devem ser parametrizadas
- nenhuma credencial Oracle no código-fonte
- falha Oracle deve gerar erro em tela quando aplicável e log obrigatório

### 9.5 Timeouts
- timeout de conexão Oracle: 10 segundos
- timeout de leitura Oracle por execução: 30 segundos por query
- ultrapassando isso, tratar como `oracle_query_failure`

---

## 10. TESTES

### 10.1 Testes unitários obrigatórios
Arquivos mínimos:
- `backend/tests/unit/test_formula_version_rules.py`
- `backend/tests/unit/test_formula_item_validation.py`
- `backend/tests/unit/test_reconciliation_calculation.py`
- `backend/tests/unit/test_reconciliation_inconsistencies.py`
- `backend/tests/unit/test_manual_review_rules.py`
- `backend/tests/unit/test_sync_mapping.py`

### 10.2 Casos unitários mínimos

#### Vigência/versionamento
- não permite sobreposição
- encerra versão anterior corretamente
- permite vigência futura
- bloqueia edição de versão usada
- permite edição de versão nunca usada

#### Fórmula
- não permite químico duplicado na mesma versão
- usa percentual humano e divide por 100 no cálculo
- aceita tolerância por item

#### Conferência
- calcula previsto com 2 casas
- calcula desvio com 2 casas
- classifica `conform` quando `abs(desvio) <= tolerancia`
- classifica `divergent` quando `abs(desvio) > tolerancia`
- classifica `inconsistent` nos 6 cenários oficiais

#### Revisão
- bloqueia revisão em inconsistência
- exige justificativa
- cria trilha imutável
- atualiza `status_final` do item e do lote

### 10.3 Testes de integração obrigatórios
- login JWT
- troca obrigatória de senha
- criação de fórmula
- criação de nova versão
- execução de conferência completa com Oracle mockado
- revisão manual
- sincronização manual
- health dependencies

### 10.4 Estratégia de mock
- Oracle deve ser mockado nos testes automatizados
- não usar Oracle real na suíte de CI local
- fixtures de dados devem representar:
  - fórmula vigente encontrada
  - fórmula ausente
  - químico fora da fórmula
  - item sem uso
  - previsto zero

### 10.5 Testes manuais (QA checklist)
- [ ] login com usuário válido
- [ ] login inválido gera erro e log
- [ ] primeiro login obriga troca de senha
- [ ] admin cria usuário e reseta senha
- [ ] sincronização manual executa e atualiza cache
- [ ] criação de fórmula com item duplicado é bloqueada
- [ ] nova versão fecha versão anterior corretamente
- [ ] conferência com 90 dias funciona
- [ ] conferência > 90 dias é bloqueada
- [ ] resumo por NF1 mostra prioridade correta
- [ ] detalhe do lote mostra previsto/usado/desvio/status
- [ ] revisão manual exige justificativa
- [ ] item inconsistente não pode ser revisado

---

## 11. VARIÁVEIS DE AMBIENTE

**Arquivo:** `/home/tap/chemanalytics/.env.example`

```bash
# Django
DJANGO_SETTINGS_MODULE=config.settings.prod
DJANGO_SECRET_KEY=change_me
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,server-name

# MySQL
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_DATABASE=chemanalytics
MYSQL_USER=chemanalytics_user
MYSQL_PASSWORD=change_me

# Oracle
ORACLE_HOST=127.0.0.1
ORACLE_PORT=1521
ORACLE_SERVICE_NAME=service_name
ORACLE_USER=oracle_user
ORACLE_PASSWORD=change_me

# JWT
JWT_ACCESS_MINUTES=30
JWT_REFRESH_DAYS=1

# Logging
LOG_LEVEL=INFO
LOG_DIR=/var/log/chemanalytics
```

**Regra:** nenhum segredo pode ser commitado no repositório.

---

## 12. DEPLOYMENT

### 12.1 Pré-requisitos
- Ubuntu 24.04
- Python 3.12.3
- Node LTS
- MySQL 8.0.42
- Oracle client compatível com `oracledb`
- gunicorn
- nginx ou proxy reverso equivalente (recomendado)
- cron habilitado

### 12.2 Build do frontend
```text
1. cd /home/tap/chemanalytics/frontend
2. npm install
3. npm run build
4. publicar build em diretório servido pelo proxy web
```

### 12.3 Deploy do backend
```text
1. cd /home/tap/chemanalytics/backend
2. git pull
3. source venv/bin/activate
4. pip install -r requirements/base.txt
5. python manage.py migrate
6. python manage.py collectstatic --noinput
7. systemctl restart gunicorn
```

### 12.4 Cron de sincronização
Agendar exatamente:
- `0 6 * * *`
- `0 13 * * *`

Comando:
```bash
cd /home/tap/chemanalytics/backend && source venv/bin/activate && python manage.py sync_oracle_cache --mode=automatic
```

### 12.5 Rollback plan
**Código**
- voltar commit anterior no Git
- reaplicar deploy manual
- reiniciar gunicorn

**Banco**
- rollback conforme política externa da infraestrutura
- migrations destrutivas são proibidas nesta v1

---

## 13. OBSERVABILIDADE

### 13.1 Logs obrigatórios
- login/logout
- falhas de autenticação
- criação/edição/versionamento de fórmulas
- execuções de conferência
- revisões manuais
- falhas de Oracle
- falhas de sincronização

### 13.2 Formato de log
Formato recomendado:
```text
timestamp | level | module | event_type | user_id | entity_type | entity_id | message
```

### 13.3 Destino de log
- arquivo local em `/var/log/chemanalytics/*.log`
- stdout/journalctl do serviço gunicorn

### 13.4 Rotação de log
Como não existe padrão prévio, criar configuração `logrotate` diária:
- manter 14 arquivos
- comprimir arquivos rotacionados
- `copytruncate`

### 13.5 Métricas mínimas
- quantidade de conferências
- tempo médio de conferência
- lotes processados por run
- itens processados por run
- quantidade de divergências
- quantidade de inconsistências
- quantidade de revisões
- quantidade de falhas Oracle
- quantidade de falhas de autenticação
- taxa de sucesso de sincronização

### 13.6 Alertas
Nesta v1 não haverá e-mail nem integração externa.  
O comportamento obrigatório é:
- erro visível em tela quando aplicável
- log obrigatório no servidor

---

## 14. SEGURANÇA

### 14.1 Autenticação/autorização
- login local
- JWT access + refresh
- grupos Django para autorização
- admin pode tudo
- reviewer pode sincronizar, conferir, revisar e consultar
- consulta pode apenas consultar

### 14.2 Senhas
- sem política avançada obrigatória nesta v1
- reset sempre define senha temporária
- `must_change_password = true` após reset e criação

### 14.3 Secrets
- em variáveis de ambiente
- nunca no código

### 14.4 Riscos aceitos
- sem HTTPS obrigatório na rede local
- sem política mínima de senha além do básico
- risco aceito deve constar na documentação de deploy/segurança

### 14.5 Validações de input
- datas obrigatórias e coerentes
- limite de 90 dias
- `codpro`, `codder`, `chemical_code` com tamanho máximo validado
- justificativa de revisão obrigatória
- sem SQL dinâmico concatenado em Oracle/MySQL
- paginação obrigatória nas listagens grandes

### 14.6 Dados sensíveis em logs
- nunca logar senha
- nunca logar JWT completo
- pode logar identificadores de usuário, run e fórmula
- não logar payload bruto da planilha de migração

---

## 15. PERFORMANCE

### 15.1 Metas
- até 10 usuários simultâneos
- conferência concluída em até 10 segundos em condições normais e volume esperado
- janela máxima 90 dias

### 15.2 Índices obrigatórios
- `formulas_formula(codpro, codder)`
- `formulas_formula_version(formula_id, start_date, end_date)`
- `formulas_formula_item(formula_version_id, chemical_code)`
- `reconciliation_run(executed_at, executed_by_id)`
- `reconciliation_lot_result(run_id, nf1, status_final)`
- `reconciliation_item_result(run_id, nf1, chemical_code, status_final)`
- `catalog_article_catalog(codpro, codder, active)`
- `catalog_chemical_product_catalog(chemical_code, active)`

### 15.3 Estratégia de consulta
- consultar lotes Oracle primeiro
- usar a lista de `NF1` retornada para buscar consumos químicos
- evitar query Oracle por lote individual
- fazer processamento em memória por execução

### 15.4 Limites
- `page_size` máximo nas listagens REST: 100
- intervalos de data > 90 dias devem retornar 400
- não implementar exportação nesta v1

---

## 16. BLOQUEIO DE OVER-ENGINEERING

### 16.1 ❌ NÃO IMPLEMENTAR NESTA V1
- Celery, Redis, RabbitMQ ou qualquer fila
- WebSocket ou atualização em tempo real
- dashboard analítico avançado
- importação de Excel pela interface
- exportação para Excel
- mobile/responsivo avançado
- SSO/LDAP/AD
- multiempresa/multiplanta
- API pública para terceiros
- exclusão física de histórico operacional
- edição destrutiva de revisão manual
- cache distribuído

### 16.2 ✅ MANTER SIMPLES
- execução síncrona da conferência
- cron do SO para sincronização
- React sem framework visual obrigatório
- Django REST monolítico
- Oracle somente leitura
- revisão item a item
- build manual e deploy manual

---

## 17. DEPENDÊNCIAS E BIBLIOTECAS

### 17.1 Backend
- Django
- djangorestframework
- djangorestframework-simplejwt
- mysqlclient ou driver MySQL equivalente compatível
- oracledb
- python-dotenv
- gunicorn
- pytest
- pytest-django
- factory-boy

### 17.2 Frontend
- react
- react-dom
- react-router-dom
- axios
- vite

### 17.3 Biblioteca NÃO obrigatória
- nenhum framework visual
- nenhum gerenciador de estado pesado é obrigatório

---

## 18. MIGRATIONS

### 18.1 Ordem mínima de migrations
1. `accounts`
2. `catalog`
3. `formulas`
4. `reconciliation`
5. `audit`

### 18.2 Regras
- migrations devem ser determinísticas
- evitar renomeações desnecessárias
- migrations destrutivas não fazem parte da v1
- criar dados iniciais de grupos (`admin`, `reviewer`, `consulta`) em migration de dados ou comando bootstrap

### 18.3 Bootstrap inicial
Criar comando:
`python manage.py bootstrap_initial_data`

Responsabilidades:
- criar grupos padrão
- criar permissões customizadas se necessário
- opcionalmente criar admin inicial por variável de ambiente

### 18.4 Migração inicial da planilha
Script externo:
`/home/tap/chemanalytics/scripts/import_initial_formulas.py`

**Regras do script**
- ler `PREVISAO_CONSUMO_PQ.xlsx`
- ignorar colunas vazias/`Unnamed`
- mapear:
  - `CODPRO`
  - `CODDER`
  - `CODQUI`
  - `DESQUI`
  - `%`
  - `DATA`
- criar fórmula lógica por `CODPRO + CODDER`
- agrupar por `DATA` como `start_date`
- definir `tolerance_pct = 2.00` para todos os itens importados
- se houver datas múltiplas para o mesmo par:
  - ordenar por `start_date`
  - `end_date` da versão N = `start_date` da versão N+1 - 1 dia`
- última versão fica com `end_date = NULL`
- validar duplicidade de item por versão
- gerar relatório final:
  - fórmulas criadas
  - versões criadas
  - itens criados
  - linhas rejeitadas

---

## 19. DOCUMENTAÇÃO COMPLEMENTAR

### 19.1 `/home/tap/chemanalytics/docs/manual-rapido.md`
Conteúdo mínimo:
- login
- troca de senha
- cadastro de fórmula
- nova versão
- sincronização manual
- execução de conferência
- revisão manual
- leitura de inconsistências

### 19.2 `/home/tap/chemanalytics/docs/install-deploy.md`
Conteúdo mínimo:
- pré-requisitos
- configuração `.env`
- criação do banco MySQL
- migrations
- bootstrap
- build frontend
- gunicorn
- cron
- rollback

### 19.3 `/home/tap/chemanalytics/docs/runbook-operacao.md`
Conteúdo mínimo:
- validar Oracle
- rodar sincronização manual
- investigar falha de conferência
- resetar senha
- inativar usuário
- checar última sincronização
- checar health dependencies
- localizar logs

---

## 20. CRITÉRIOS DE ACEITAÇÃO (QA)

### 20.1 Funcionalidades
- [ ] Admin consegue criar usuário com grupo e senha temporária
- [ ] Primeiro login força troca de senha
- [ ] Admin consegue cadastrar fórmula inicial por `codpro + codder`
- [ ] Sistema impede item químico duplicado na mesma versão
- [ ] Sistema impede sobreposição de vigência
- [ ] Sistema bloqueia edição de versão já usada
- [ ] Nova versão fecha automaticamente a anterior
- [ ] Sincronização automática roda às 06:00 e 13:00
- [ ] Sincronização manual funciona para reviewer/admin
- [ ] Códigos removidos do Oracle permanecem no cache como inativos
- [ ] Conferência aceita filtros definidos no PRD
- [ ] Conferência bloqueia intervalo > 90 dias
- [ ] Cada execução persiste histórico independente
- [ ] Resumo por NF1 respeita prioridade `inconsistent > divergent > conform`
- [ ] Detalhe por item mostra previsto, usado, desvio e status
- [ ] Revisão manual exige justificativa
- [ ] Revisão manual é bloqueada em inconsistência
- [ ] Histórico mantém `status_calculated`, `status_reviewed` e `status_final`
- [ ] Falha Oracle gera erro em tela e log
- [ ] Relatório de divergências mostra divergentes e inconsistentes

### 20.2 Não funcionais
- [ ] Aplicação opera com até 10 usuários simultâneos
- [ ] Conferência dentro da meta de até 10s em cenário esperado
- [ ] Credenciais ficam fora do código
- [ ] Logs mínimos obrigatórios são gerados
- [ ] Deploy manual documentado
- [ ] Runbook básico documentado

---

## 21. DEFINIÇÃO DE PRONTO (DoD)

A entrega só pode ser considerada pronta quando:
- [ ] backend Django REST funcional
- [ ] frontend React funcional
- [ ] autenticação JWT implementada
- [ ] grupos/perfis configurados
- [ ] sincronização automática e manual funcionando
- [ ] cadastro/versionamento de fórmulas funcionando
- [ ] conferência histórica persistida funcionando
- [ ] revisão manual funcionando
- [ ] auditoria mínima funcionando
- [ ] testes unitários críticos passando
- [ ] homologação manual com usuários de negócio concluída
- [ ] manual rápido entregue
- [ ] documentação de deploy entregue
- [ ] runbook entregue

---

## 22. REFERÊNCIAS

### 22.1 Documentos relacionados
- PRD v1.0 — Sistema de Cadastro Versionado de Fórmulas e Conferência de Recurtimento
- Planilha de migração inicial: `PREVISAO_CONSUMO_PQ.xlsx`

### 22.2 Fontes Oracle
- `USU_VBI_OPREC_V2`
- `USU_VBI_QUIREC_V2`
- `USU_VBI_ARTIGOS_SEMI_NOA`
- `USU_VBI_EQ_PRODUTOS`

### 22.3 Decisões assumidas a partir da entrevista técnica
- frontend React separado em `/frontend`
- backend Django REST em `/backend`
- JWT/token
- cálculo do previsto com `percentual / 100`
- tolerância inicial de migração = 2%
- revisão somente por reviewer/admin
- admin com acesso total
- cron às 06:00 e 13:00
- deploy manual com `git pull + venv + migrate + collectstatic + restart gunicorn`

---

## 23. APROVAÇÕES

**Spec Review**
- [ ] Arquiteto de Software: __________________
- [ ] Tech Lead: __________________
- [ ] Product Owner: __________________

**Implementação**
- [ ] Desenvolvedor Responsável: __________________
- [ ] Revisor de Código: __________________

---

## 24. CHANGELOG DA SPEC

| Versão | Data | Autor | Mudanças |
|--------|------|-------|----------|
| 1.0 | 2026-03-18 | AI-Generated | Versão inicial consolidada a partir do PRD e respostas técnicas |

---

## 25. NOTAS E OBSERVAÇÕES

1. A planilha Excel enviada foi tratada apenas como fonte de migração inicial; a interface da v1 não deve ter importação de Excel.
2. O contrato Oracle foi fechado com base nas views e campos informados; se o nome exato de colunas ou tipos mudar no ambiente real, a implementação deve ajustar apenas a camada `oracle_sync/queries.py`, sem alterar a regra de negócio.
3. `consulta` é perfil somente leitura. A revisão manual pertence a `reviewer` e `admin`.
4. Como o frontend é separado e a aplicação é interna, a recomendação operacional é servir o build do React pelo proxy web e expor a API Django sob prefixo `/api/v1`.
5. Não usar `QTDPRV` do Oracle para evitar dupla fonte de verdade do previsto.
6. Em caso de divergência entre esta spec e decisões informais posteriores, esta spec prevalece até revisão formal de versão.
