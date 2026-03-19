# Epic 3: Reconciliation and Review

## Objetivo

Implementar a conferência operacional de recurtimento com persistência congelada de execução, resumo por lote e revisão manual auditável.

## Valor de negócio

Entrega a funcionalidade principal para o almoxarifado químico comparar previsto versus realizado, com trilha histórica e tratamento controlado de divergências.

## Escopo

- Leitura Oracle para dados operacionais
- Motor de conferência e classificação
- Persistência histórica de runs, lotes e itens
- Consulta de resumo/detalhe
- Revisão manual com justificativa

## Fora de escopo

- Analytics avançado
- Notificações em tempo real
- Automação de decisão operacional

## Dependências

- Epics 1 e 2 concluídos

## Stories

1. `3.1` Oracle reconciliation engine
2. `3.2` Reconciliation history and detail
3. `3.3` Manual review workflow

## Definition of Done do épico

- Uma execução de conferência gera histórico íntegro e auditável
- Usuário consulta resumo por NF1 e detalhe por item químico
- Revisões manuais ficam rastreadas por usuário, data e justificativa
