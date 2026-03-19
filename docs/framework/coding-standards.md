# Padrões de Código

## Status

Documento base de bootstrap do projeto.

## Objetivo

Registrar os padrões mínimos de implementação enquanto a arquitetura detalhada ainda está sendo consolidada.

## Diretrizes atuais

- Priorizar `CLI First -> Observability Second -> UI Third`.
- Evitar inventar requisitos fora de [PRD.md](/C:/Users/ANDREGARCIA/ChemAnalytics_v3/docs/PRD.md) e [SPEC.md](/C:/Users/ANDREGARCIA/ChemAnalytics_v3/docs/SPEC.md).
- Preferir imports absolutos quando a base do projeto suportar aliases.
- Preservar histórico e trilhas de auditoria para entidades operacionais e históricas.
- Não depender de UI para validar regras centrais do sistema.

## Fonte de verdade atual

- Regras de produto: [PRD.md](/C:/Users/ANDREGARCIA/ChemAnalytics_v3/docs/PRD.md)
- Regras técnicas e operacionais: [SPEC.md](/C:/Users/ANDREGARCIA/ChemAnalytics_v3/docs/SPEC.md)
- Fluxo de execução: [docs/stories/README.md](/C:/Users/ANDREGARCIA/ChemAnalytics_v3/docs/stories/README.md)

## Observação

Este arquivo existe para satisfazer as referências do `core-config` até que a documentação técnica seja evoluída de forma mais granular.
