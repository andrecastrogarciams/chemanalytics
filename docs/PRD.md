# PRD — Sistema de Cadastro Versionado de Fórmulas e Conferência de Recurtimento  
**Versão:** 1.0  
**Status:** MVP v1 definido  
**Idioma:** Português  
**Contexto:** Indústria de couro semiacabado

---

# PARTE 1: VISÃO DE PRODUTO

## 1. Visão Geral

### Contexto e problema a resolver
A operação de recurtimento utiliza fórmulas químicas definidas por **artigo (CODPRO)** e **derivação (CODDER)**, onde o **peso do lote NF1** é a base para calcular a quantidade prevista de cada produto químico. Hoje, o cadastro dessas fórmulas está em planilha Excel, enquanto o ERP armazena os dados reais de recurtimento em Oracle.

O problema central é duplo:

1. **Falta de versionamento confiável das fórmulas**, o que impede saber com segurança qual percentual estava vigente no dia do recurtimento.
2. **Falta de conferência operacional estruturada** entre o previsto pela fórmula e o realizado no ERP, dificultando o controle do Almoxarifado Químico e a rastreabilidade do processo.

### Solução proposta
Desenvolver uma **aplicação web interna**, em **Django**, com banco **MySQL** próprio para:
- cadastrar fórmulas versionadas por vigência;
- manter histórico das versões;
- consultar dados operacionais diretamente do **Oracle**;
- executar conferências sob demanda por período;
- gravar o histórico congelado de cada execução;
- permitir revisão manual controlada de divergências;
- destacar inconsistências de cadastro/dados.

### Stakeholders principais
- **Produção**
- **Almoxarifado Químico**
- **Desenvolvimento/TI interna** (implantação, operação e manutenção)
- **Gestão operacional** (consumo químico, rastreabilidade e controle)

---

## 2. Objetivos de Negócio

### Metas SMART
1. **Conferir 100% dos lotes encontrados no período consultado**, registrando o histórico de cada execução.
2. **Eliminar a dependência operacional da planilha Excel** para cadastro vigente de fórmulas após a migração inicial.
3. **Garantir rastreabilidade completa de fórmula aplicada por lote**, preservando a versão vigente usada na análise.

### OKRs
**Objetivo 1:** Apoiar o almoxarifado no controle do consumo químico.  
**KR1:** 100% dos lotes do período consultado devem ser processados pela conferência.  
**KR2:** 100% das conferências executadas devem gerar histórico persistido com timestamp.  
**KR3:** 100% das revisões manuais devem registrar usuário, data/hora e justificativa.

**Objetivo 2:** Garantir governança sobre fórmulas químicas.  
**KR1:** 100% das fórmulas ativas devem estar cadastradas no sistema após migração inicial.  
**KR2:** 0 sobreposição de vigência para o mesmo par CODPRO + CODDER.  
**KR3:** 100% das alterações em fórmulas devem ser rastreáveis por usuário e data/hora.

### Impacto esperado
- maior controle operacional do Almoxarifado Químico;
- rastreabilidade histórica de fórmula por lote;
- redução de ambiguidade sobre percentual vigente;
- padronização do processo de conferência;
- redução de dependência de controles paralelos em planilha.

---

## 3. Público-Alvo e Personas

### Usuários finais
**Produção**  
Consulta conferências por período, lote e produto químico, analisa consumo realizado vs previsto.

**Almoxarifado Químico**  
Usuário principal de controle operacional. Usa o sistema para identificar divergências e validar conferências.

### Administradores/operadores
**Administrador do sistema**  
Gerencia usuários, senhas, perfis e fórmulas/versionamentos.

**Usuário intermediário/revisor**  
Não acessa cadastro de fórmulas. Pode revisar manualmente status de conferência, com justificativa obrigatória.

### Equipes técnicas
**Desenvolvimento**  
Implanta, mantém, monitora logs, executa deploy manual, opera homologação e produção.

### Stakeholders de compliance/legal
Não há requisito regulatório formal informado. A rastreabilidade exigida é operacional e de governança interna.

---

## 4. User Stories

### História 1 — Cadastro de fórmula
Como **Administrador**, quero cadastrar uma fórmula para um par CODPRO + CODDER com vigência, para que o sistema saiba qual percentual aplicar na conferência.

**Critérios de aceitação**
- permitir selecionar CODPRO, CODDER e produtos químicos a partir de listas sincronizadas do Oracle;
- impedir duplicidade do mesmo produto químico dentro da mesma fórmula;
- exigir data de início de vigência;
- permitir data fim opcional;
- armazenar percentual e tolerância percentual por item;
- armazenar descrições legíveis dos códigos na aplicação.

### História 2 — Versionamento de fórmula
Como **Administrador**, quero criar uma nova versão de fórmula, para preservar o histórico sem alterar fórmulas já usadas.

**Critérios de aceitação**
- impedir edição direta de fórmula já usada em conferência;
- permitir edição apenas se a fórmula nunca foi usada;
- ao criar nova versão, encerrar automaticamente a versão anterior no dia imediatamente anterior;
- impedir sobreposição de vigência para o mesmo CODPRO + CODDER;
- permitir criação com vigência futura.

### História 3 — Consulta de conferência
Como **usuário de Produção/Almoxarifado**, quero executar uma conferência por período e filtros, para comparar previsto e utilizado.

**Critérios de aceitação**
- filtros por data de recurtimento, NF1, CODPRO, CODDER, produto químico e divergências;
- limite máximo de 90 dias por execução;
- cada execução deve gerar histórico independente;
- a execução deve persistir timestamp, valores previstos/usados, versão da fórmula aplicada e status.

### História 4 — Resumo por lote
Como **usuário**, quero visualizar um resumo por lote NF1 e navegar para o detalhe, para identificar rapidamente lotes problemáticos.

**Critérios de aceitação**
- resumo por NF1;
- prioridade de status: inconsistência > divergência > conforme;
- clique para abrir detalhe por produto químico.

### História 5 — Revisão manual
Como **usuário intermediário**, quero revisar manualmente um status calculado, para registrar decisão operacional.

**Critérios de aceitação**
- manter status calculado e status revisado;
- exigir justificativa em texto livre;
- registrar usuário revisor e data/hora;
- bloquear revisão quando houver inconsistência de cadastro/dados.

### História 6 — Gestão de usuários
Como **Administrador**, quero criar e manter usuários, para controlar acesso por perfil.

**Critérios de aceitação**
- criar usuário manualmente;
- definir perfil;
- ativar/inativar usuário;
- resetar senha;
- exigir troca de senha no primeiro login e após reset.

### Cenários de erro / edge cases
- lote encontrado no Oracle sem fórmula vigente aplicável;
- produto químico usado no ERP não existe na fórmula;
- item da fórmula sem correspondente de consumo no ERP;
- falha na consulta ao Oracle;
- falha na sincronização do cache;
- tentativa de criar fórmula com vigência sobreposta;
- tentativa de editar fórmula já usada.

### Priorização
**Must have**
- login e perfis;
- cadastro/versionamento de fórmulas;
- cache local sincronizado;
- conferência histórica;
- revisão manual com justificativa;
- relatório/consulta de divergências;
- logs operacionais mínimos.

**Should have**
- filtros avançados por divergência calculada e revisada;
- inativação de códigos vindos do Oracle preservando histórico.

**Could have**
- métricas operacionais agregadas;
- alertas ativos externos;
- exportações.

**Won’t have (v1)**
- mobile;
- HTTPS obrigatório;
- integração com AD/LDAP/SSO;
- importação de Excel pela interface;
- dashboard administrativo dedicado;
- exportação para Excel.

---

# PARTE 2: REQUISITOS FUNCIONAIS

## 5. Funcionalidades Core

### 5.1 Cadastro de fórmulas
O sistema deve permitir o cadastro de fórmulas por **CODPRO + CODDER**, contendo:
- data de início de vigência;
- data fim opcional;
- observação opcional;
- lista de itens químicos;
- percentual por item;
- tolerância percentual por item.

### 5.2 Versionamento
- O sistema deve manter histórico de versões por vigência.
- Fórmulas já utilizadas em conferência não podem ser editadas diretamente.
- Nova versão deve encerrar automaticamente a versão anterior.
- Não pode haver sobreposição de vigência para o mesmo CODPRO + CODDER.

### 5.3 Sincronização de cadastros auxiliares
O sistema deve manter cache local sincronizado com o Oracle para:
- CODPRO;
- CODDER;
- produtos químicos;
- descrições legíveis desses códigos.

Regras:
- sincronização automática 2x ao dia;
- sincronização manual sob demanda;
- códigos desativados/removidos no Oracle permanecem no cache como inativos.

### 5.4 Conferência operacional
A conferência deve:
- consultar o Oracle por data de recurtimento;
- buscar lote NF1, peso do lote, CODPRO, CODDER, data do recurtimento, produto químico e quantidade utilizada;
- localizar a fórmula vigente aplicável;
- calcular a quantidade prevista;
- comparar previsto vs utilizado;
- calcular desvio percentual;
- classificar status calculado.

### 5.5 Persistência do histórico
Cada execução deve gravar:
- data/hora da análise;
- filtros utilizados;
- valores previstos e utilizados daquele momento;
- ID da fórmula/versionamento usada;
- vigência aplicada;
- status calculado;
- status revisado, se houver;
- justificativa, se houver;
- usuário executor/revisor.

### 5.6 Revisão manual
- Revisão ocorre no nível do item químico.
- Revisão exige justificativa obrigatória.
- O sistema deve manter status calculado e revisado.
- O status final operacional deve considerar:
  1. inconsistência, se existir;
  2. status revisado, se existir;
  3. status calculado, se não houver revisão.

### 5.7 Consulta e navegação
Telas mínimas:
- cadastro de fórmulas;
- histórico/versionamento;
- consulta de conferência por período;
- detalhe do lote;
- relatório de divergências.

### 5.8 Gestão de usuários
- login local com usuário/senha;
- perfis distintos;
- troca de senha no primeiro login e após reset;
- ativação/inativação de usuários;
- alteração de perfil;
- reset de senha.

### 5.9 Regras de inativação/exclusão
- usuários: apenas inativação;
- fórmulas/versionamentos já usados: não podem ser excluídos;
- fórmulas/versionamentos nunca usados: exclusão ou inativação controlada, conforme implementação.

---

## 6. Integrações

### Sistemas externos
**Oracle / ERP**
- fonte de dados operacional para lotes e recurtimento;
- fonte para listas de CODPRO, CODDER e produtos químicos.

### Sistemas legados
- planilha Excel atual de fórmulas, usada apenas para migração inicial via script externo.

### Protocolos de comunicação
- integração de leitura entre aplicação Django e Oracle;
- persistência principal da aplicação em MySQL.

### Autenticação/autorização entre sistemas
- não foi exigido SSO, LDAP ou AD;
- autenticação local da aplicação.

### SLAs de dependências externas
- indisponibilidade do Oracle não é crítica para toda a operação;
- quando o Oracle estiver indisponível, a aplicação deve notificar em tela e registrar em log;
- sincronização e conferência dependem de disponibilidade do Oracle.

---

# PARTE 3: REQUISITOS NÃO-FUNCIONAIS

## 7. Performance e Escalabilidade

### Meta de desempenho
- até **10 usuários simultâneos**;
- tempo de resposta aceitável para conferência: até **10 segundos**;
- consulta limitada a **90 dias por execução**.

### Throughput
Volume esperado da ordem de **centenas**:
- fórmulas;
- itens por fórmula;
- lotes processados no período;
- execuções de conferência.

### Crescimento projetado
- 6 meses: baixo a moderado;
- 1 ano: crescimento linear;
- 3 anos: ainda compatível com arquitetura monolítica com banco relacional, salvo aumento expressivo de volume no Oracle.

### Estratégia de cache
- cache local sincronizado para listas de apoio;
- não há requisito de cache distribuído;
- sem necessidade de camada dedicada de cache na v1.

---

## 8. Disponibilidade e Confiabilidade

### SLA/SLO/SLI
Não foi definido SLA contratual formal. Para a v1, adota-se objetivo operacional interno:

- disponibilidade adequada ao uso em rede local;
- consultas à aplicação e cadastro local devem permanecer disponíveis mesmo com Oracle indisponível;
- conferências e sincronizações dependem do Oracle.

### Indicadores
- taxa de sucesso das execuções de conferência;
- taxa de sucesso das sincronizações;
- taxa de falha de autenticação;
- tempo médio de execução da conferência.

### RTO/RPO
Não há requisito implementado na aplicação, pois backup/restore é tratado por ferramenta externa existente.  
O PRD assume:
- recuperação do MySQL conforme política da infraestrutura local;
- retenção indefinida dos dados da aplicação.

### Failover/redundância
Fora do escopo da v1.

---

## 9. Segurança

### Autenticação
- login local com usuário/senha no MySQL;
- troca obrigatória no primeiro acesso e após reset;
- sem política mínima de senha além do básico do sistema.

### Autorização
Perfis:
- **Administrador**
- **Consulta**
- **Intermediário/Revisor**

### Criptografia
- sem exigência de HTTPS na rede local;
- sem requisito adicional de criptografia em repouso informado.

### Gestão de secrets
- credenciais de MySQL e Oracle devem ficar fora do código-fonte, em configuração segura de ambiente/servidor.

### Compliance
Nenhum requisito regulatório formal foi informado.

### Auditoria
Obrigatório registrar:
- quem criou/alterou fórmula e quando;
- quem revisou status e quando;
- justificativa de revisão manual.

### Testes de segurança
Não exigidos formalmente para v1.

### Risco aceito
A ausência de HTTPS e de política mínima de senha deve constar como **risco aceito do ambiente interno**.

---

## 10. Observabilidade

### Logs obrigatórios
- login/logout;
- falhas de autenticação;
- criação/edição/versionamento de fórmulas;
- execuções de conferência;
- revisões manuais de status;
- falhas de consulta ao Oracle;
- falhas de sincronização do cache.

### Métricas
Métricas mínimas recomendadas:
- quantidade de conferências executadas;
- tempo médio de execução;
- quantidade de lotes processados por conferência;
- quantidade de divergências;
- quantidade de inconsistências;
- quantidade de revisões manuais.

### Tracing
Não necessário para a v1.

### Alertas
- erro em tela quando aplicável;
- logs no sistema/servidor;
- sem e-mail ou alerta ativo externo na v1.

### Dashboards
Fora do escopo da v1.

### Health checks
Recomendado:
- status da aplicação;
- status do MySQL;
- status de conectividade com Oracle;
- status da última sincronização do cache.

---

## 11. Manutenibilidade e Testabilidade

### Arquitetura
- monólito Django;
- separação por módulos: autenticação, fórmulas, sincronização, conferência, revisão, logs.

### Documentação técnica
Entregáveis mínimos:
- manual rápido de uso;
- documentação técnica de instalação/deploy;
- runbook básico de operação.

### Estratégia de testes
Obrigatórios para v1:
- testes automatizados das regras críticas de fórmula/vigência;
- homologação manual com usuários de negócio.

Recomendados:
- testes automatizados de regras de conferência e inconsistência;
- smoke test manual após deploy.

### Versionamento de API
Sem requisito externo de API pública para v1.

### Backward compatibility
Aplicável ao esquema interno da aplicação conforme evolução futura.

---

# PARTE 4: ARQUITETURA E INFRAESTRUTURA

## 12. Arquitetura de Solução

### Diagrama lógico em alto nível
1. Usuário acessa aplicação web interna Django.  
2. Aplicação autentica via MySQL.  
3. Cadastro e versionamento de fórmulas ficam no MySQL.  
4. Sincronização alimenta cache local com listas vindas do Oracle.  
5. Ao executar conferência, a aplicação lê dados do Oracle, aplica fórmula vigente do MySQL, calcula previsto/desvio/status e grava histórico congelado no MySQL.  
6. Revisões manuais atualizam o histórico persistido, sem alterar o cálculo original.

### Stack tecnológica
- **Backend:** Python + Django
- **Frontend:** templates Django / frontend server-rendered interno
- **Banco da aplicação:** MySQL
- **Banco legado/integrado:** Oracle
- **Storage:** banco relacional da aplicação
- **Message broker:** não aplicável
- **Cache distribuído:** não aplicável

### Padrão arquitetural
- monólito web interno;
- integração síncrona com Oracle;
- agendamento local para sincronização automática 2x ao dia.

### Edge vs cloud
- on-premise;
- sem uso de cloud na v1.

---

## 13. Infraestrutura

### Ambiente
- servidor interno on-premise;
- sem uso mobile;
- acesso apenas via rede local.

### Ambientes obrigatórios
- homologação;
- produção.

### Recursos computacionais
Não foram especificados. Devem ser dimensionados para:
- 10 usuários simultâneos;
- monólito Django;
- MySQL local/servidor interno;
- conectividade estável com Oracle.

### Rede
- rede local interna;
- sem exigência de HTTPS;
- sem CDN;
- sem balanceador obrigatório para a v1.

---

## 14. Estratégia de Dados

### Modelo de dados em alto nível
Entidades principais:
- usuário;
- perfil;
- fórmula;
- versão da fórmula;
- item da fórmula;
- cache de CODPRO/CODDER;
- cache de produtos químicos;
- execução de conferência;
- resultado por lote;
- resultado por item químico;
- revisão manual.

### Volume esperado
Ordem de grandeza:
- centenas de fórmulas;
- centenas de itens;
- centenas de lotes por janela operacional;
- retenção indefinida de conferências.

### Retenção
- retenção indefinida para:
  - fórmulas/versionamentos;
  - execuções de conferência;
  - revisões manuais;
  - logs conforme política do servidor.

### Backup e restore
- fora do escopo da aplicação;
- atendido por ferramenta externa já existente.

### Migração de dados
- migração inicial da planilha Excel via script externo;
- sem funcionalidade de importação na interface.

### Estratégia de migração
- carga inicial;
- validação de consistência após carga;
- operação passa a ocorrer exclusivamente pelo sistema.

### Rollback plan
- rollback de código por deploy manual;
- rollback de dados da aplicação conforme política do MySQL/infraestrutura.

### Analytics
Fora do escopo da v1.

---

# PARTE 5: OPERAÇÃO E DEPLOYMENT

## 15. CI/CD e Deployment

### Versionamento
Uso de Git com fluxo simples:
- `main` = produção
- `develop` = homologação

### Pipeline
Não há pipeline automatizado exigido na v1.

### Estratégia de release
- deploy manual;
- promoção manual de homologação para produção.

### Aprovações necessárias
- homologação manual com usuários de negócio antes da publicação em produção.

### Rollback
- rollback manual de código;
- rollback de dados conforme ferramenta externa de backup e operação do banco.

---

## 16. Runbooks e Operação

### Procedimentos operacionais mínimos
- como publicar nova versão;
- como reverter versão;
- como validar conectividade com Oracle;
- como forçar sincronização manual do cache;
- como investigar falhas de conferência;
- como resetar senha de usuário;
- como inativar usuário;
- como interpretar inconsistências de cadastro/dados.

### Troubleshooting comum
- Oracle indisponível;
- cache desatualizado;
- vigência sobreposta em cadastro;
- fórmula ausente para lote;
- produto químico do ERP não cadastrado;
- item previsto sem realizado correspondente.

### Responsáveis
- operação e manutenção: equipe de desenvolvimento;
- homologação funcional: usuários de negócio.

### SLAs internos
Não formalizados no momento.

---

## 17. Disaster Recovery

### Cenários contemplados
- falha da aplicação;
- indisponibilidade do MySQL;
- indisponibilidade do Oracle;
- falha de sincronização automática.

### Plano de recuperação
- reinício da aplicação;
- restauração do banco conforme ferramenta externa;
- reexecução da sincronização;
- reprocessamento de conferência quando necessário.

### RTO/RPO específicos
Dependem da política da infraestrutura e da ferramenta de backup existente. Não definidos no escopo atual.

### Testes de DR
Não exigidos para a v1.

---

# PARTE 6: VIABILIDADE E RISCOS

## 18. Análise de Viabilidade Técnica

### Capacidade do time
- desenvolvimento previsto por **1 pessoa**;
- stack escolhida: **Django + MySQL + integração Oracle**;
- viável para o porte informado, desde que o escopo da v1 seja mantido.

### Estimativa de esforço por componente
**Baixa complexidade**
- autenticação local básica;
- gestão de usuários;
- telas CRUD básicas;
- logs básicos.

**Média complexidade**
- versionamento de fórmula com regras de vigência;
- sincronização manual/automática de cache;
- consulta detalhada com filtros;
- histórico persistido.

**Alta complexidade relativa**
- conferência congelada com vínculo de fórmula/versionamento;
- classificação de inconsistências;
- regra de revisão manual sem corromper trilha histórica;
- integração Oracle estável e performática.

### Prazo realista
Sem prazo fechado. Recomenda-se entrega em fases internas, mesmo dentro da v1:
1. base de autenticação e cache;
2. cadastro/versionamento de fórmulas;
3. conferência histórica;
4. revisão manual e acabamento operacional.

---

## 19. Build vs Buy vs Integrate

### Componente 1 — Cadastro/versionamento de fórmulas
- **Build:** altamente recomendado;
- **Buy:** desnecessário para o porte e especificidade;
- **Integrate:** não há solução legada adequada já citada.

**Recomendação:** Build.

### Componente 2 — Consulta operacional de recurtimento
- **Build:** camada de conferência própria;
- **Buy:** pouco aderente ao processo específico;
- **Integrate:** leitura do Oracle já existente.

**Recomendação:** Build + Integrate com Oracle.

### Componente 3 — Sincronização de listas
- **Build:** simples e controlável;
- **Buy:** desnecessário;
- **Integrate:** com Oracle via leitura periódica.

**Recomendação:** Build + Integrate.

### Componente 4 — Autenticação
- **Build:** aceitável para v1;
- **Buy/Integrate com AD/SSO:** não requerido no momento.

**Recomendação:** Build simples local na v1.

---

## 20. Riscos Técnicos e Mitigações

### Risco 1 — Dependência do Oracle
**Probabilidade:** média  
**Impacto:** médio  
**Mitigação:** cache local para listas, aviso em tela, logs, reexecução manual.  
**Contingência:** indisponibilidade do Oracle não bloqueia cadastro local.

### Risco 2 — Regras de vigência incorretas
**Probabilidade:** média  
**Impacto:** alto  
**Mitigação:** testes automatizados obrigatórios para vigência/versionamento; constraints e validações na aplicação.

### Risco 3 — Distorção entre histórico e dado atual
**Probabilidade:** média  
**Impacto:** alto  
**Mitigação:** congelar conferência por execução com vínculo explícito à fórmula/versionamento usada.

### Risco 4 — Segurança básica fraca
**Probabilidade:** alta  
**Impacto:** médio  
**Mitigação:** registrar como risco aceito; considerar política mínima de senha e HTTPS em fase futura.

### Risco 5 — Sobrecarga em consultas amplas
**Probabilidade:** média  
**Impacto:** médio  
**Mitigação:** limite de 90 dias; filtros adicionais; índices locais; tuning das views Oracle se necessário.

### Risco 6 — Projeto em pessoa única
**Probabilidade:** alta  
**Impacto:** médio/alto  
**Mitigação:** documentação mínima obrigatória, Git flow simples, homologação formal, runbook.

### Risco 7 — Qualidade inconsistente dos dados vindos do ERP
**Probabilidade:** média  
**Impacto:** alto  
**Mitigação:** categoria explícita de inconsistência de cadastro/dados, sem mascarar como divergência.

---

## 21. Dívida Técnica

### Dívida existente
- dependência de planilha Excel para gestão atual;
- ausência de versionamento estruturado;
- dependência de leitura direta do Oracle;
- ausência de política formal de segurança local.

### Dívida técnica que será criada na v1
- autenticação local sem política mínima de senha;
- ausência de HTTPS;
- deploy manual;
- ausência de pipeline automatizado;
- observabilidade sem dashboard.

### Plano para endereçar
Fase futura recomendada:
- política de senha mínima;
- HTTPS interno;
- CI/CD básico;
- dashboard operacional;
- testes automatizados adicionais para conferência.

---

# PARTE 7: MÉTRICAS E CUSTOS

## 22. Métricas de Sucesso

### Métricas de negócio
- **100% dos lotes do período consultado conferidos**
- % de fórmulas migradas e operadas exclusivamente no sistema
- % de revisões manuais com justificativa registrada
- % de lotes com inconsistência de cadastro/dados identificados

### Métricas técnicas
- tempo médio de execução da conferência
- taxa de falha nas execuções
- taxa de falha na sincronização do cache
- taxa de disponibilidade da aplicação local
- número de autenticações com falha

### Métricas de qualidade
- cobertura de testes das regras críticas de vigência/versionamento
- taxa de sucesso na homologação manual
- frequência de deploy
- MTTR operacional da aplicação

---

## 23. TCO (Total Cost of Ownership)

### Custos de implementação (CAPEX)
Não há dados suficientes para quantificação financeira precisa. Itens previstos:
- horas de desenvolvimento;
- horas de homologação;
- tempo de migração inicial da planilha;
- eventuais ajustes em acesso ao Oracle.

### Custos operacionais (OPEX)
- servidor on-premise;
- banco MySQL;
- operação pelo desenvolvimento;
- manutenção corretiva/evolutiva;
- armazenamento crescente do histórico.

### Break-even
Não há dados financeiros para cálculo formal. O ganho esperado é operacional:
- rastreabilidade;
- governança;
- redução de retrabalho;
- redução de dependência de controles paralelos.

**Observação:** esta seção deve ser refinada quando houver custo/hora, capacidade do servidor e custo de operação.

---

# PARTE 8: APÊNDICES

## 24. Glossário

- **NF1:** chave do lote de produção/recurtimento.
- **NF2:** documento descendente de NF1.
- **CODPRO:** código do artigo.
- **CODDER:** derivação; contempla artigo, cor e espessura conforme contexto informado.
- **Fórmula:** conjunto de produtos químicos e percentuais aplicáveis ao lote.
- **Vigência:** período de validade de uma versão da fórmula.
- **Produto químico:** item da fórmula identificado por código próprio.
- **Percentual:** taxa aplicada sobre o peso do lote para calcular o previsto.
- **Tolerância percentual:** limite aceito de variação entre previsto e utilizado.
- **Status calculado:** classificação automática gerada pelo sistema.
- **Status revisado:** classificação operacional alterada manualmente por usuário autorizado.
- **Inconsistência de cadastro/dados:** erro estrutural que impede revisão operacional normal.
- **Cache local:** cópia sincronizada no MySQL de códigos e descrições oriundos do Oracle.

---

## 25. Referências

### Fontes internas do projeto
- planilha Excel atual de fórmulas;
- views Oracle existentes para:
  - lotes;
  - artigos;
  - recurtimento;
  - consumo químico.

### Referências técnicas internas recomendadas
- convenções de acesso ao Oracle da empresa;
- padrão interno de deploy em homologação/produção;
- política existente de backup do banco de dados.

---

## 26. Dúvidas em Aberto

Mesmo com o escopo funcional fechado, estes pontos ainda precisam de detalhamento durante design técnico/implementação:

1. **Estrutura exata das views Oracle**
   - nomes das views;
   - chaves técnicas;
   - performance real por janela de 90 dias.

2. **Modelo físico do banco MySQL**
   - desenho final das tabelas;
   - índices;
   - constraints;
   - estratégia de soft delete/inativação.

3. **Estratégia exata de agendamento**
   - mecanismo do job 2x ao dia;
   - horário de execução;
   - política de reprocessamento em falha.

4. **Regra exata do cálculo do desvio percentual**
   - fórmula matemática final;
   - arredondamento e precisão decimal.

5. **Logs**
   - formato final;
   - retenção no servidor;
   - rotação de arquivos.

6. **Detalhes da interface**
   - layout das telas;
   - paginação;
   - ordenação;
   - destaque visual de divergência/inconsistência.

7. **Quantificação financeira**
   - TCO detalhado ainda depende de custos internos.

---

# Conclusão

A v1 está definida como um **sistema web interno de governança de fórmulas e conferência operacional**, com foco claro em **apoio ao Almoxarifado Químico no controle do consumo** e em **rastreabilidade histórica por lote**.

O recorte está correto para um MVP sério:
- escopo funcional enxuto;
- regras de negócio fortes;
- histórico congelado;
- versionamento correto;
- revisão manual controlada;
- dependência do Oracle tratada sem romantização.

O principal risco não é tecnológico. É **disciplina de implementação e validação**: vigência, inconsistência e congelamento do histórico precisam nascer certos. Se esses três pilares forem respeitados, a v1 tem alta chance de entrar em operação sem virar mais uma planilha com login.
