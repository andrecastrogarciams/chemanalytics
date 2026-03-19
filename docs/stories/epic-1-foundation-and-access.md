# Epic 1: Foundation and Access

## Objetivo

Estabelecer a base operacional do produto com estrutura de projeto, autenticação, perfis de acesso e capacidade mínima de operação local antes de avançar para regras de negócio e UI completa.

## Valor de negócio

Reduz risco de retrabalho, garante um caminho de execução controlado e cria o alicerce para as próximas entregas sem depender de interface final para validar comportamento central.

## Escopo

- Estrutura inicial backend/frontend
- Configuração local e variáveis de ambiente
- Autenticação e perfis `admin`, `reviewer`, `consulta`
- Health checks, logs e comandos operacionais mínimos

## Fora de escopo

- Cadastro completo de fórmulas
- Conferência operacional
- Revisão manual de divergências

## Dependências

- [PRD.md](/C:/Users/ANDREGARCIA/ChemAnalytics_v3/docs/PRD.md)
- [SPEC.md](/C:/Users/ANDREGARCIA/ChemAnalytics_v3/docs/SPEC.md)

## Stories

1. `1.1` Project scaffold
2. `1.2` Authentication and roles
3. `1.3` Health, logging and CLI ops

## Definition of Done do épico

- Projeto sobe localmente com backend e frontend separados
- Usuários autenticam com perfis mínimos
- Operação básica pode ser validada via CLI
- Logs e health checks permitem diagnóstico inicial
