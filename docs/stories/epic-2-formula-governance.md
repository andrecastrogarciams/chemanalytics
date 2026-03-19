# Epic 2: Formula Governance

## Objetivo

Entregar o núcleo de governança das fórmulas químicas com modelo versionado, regras de vigência e bootstrap inicial a partir da base atual.

## Valor de negócio

Ataca o problema central de rastreabilidade e remove a dependência operacional da planilha como fonte viva de fórmulas.

## Escopo

- Modelo de dados de fórmulas, versões e itens
- Importação inicial da planilha
- Cadastro, edição e versionamento
- Sincronização de catálogos auxiliares vindos do Oracle

## Fora de escopo

- Conferência por período
- Histórico de execução de conferência
- Revisão manual

## Dependências

- Epic 1 concluído

## Stories

1. `2.1` Formula schema and bootstrap
2. `2.2` Formula version management
3. `2.3` Auxiliary catalog sync

## Definition of Done do épico

- Fórmulas são persistidas com vigência sem sobreposição
- Migração inicial consegue carregar a base atual com relatório
- Catálogos auxiliares são sincronizados e consultáveis
