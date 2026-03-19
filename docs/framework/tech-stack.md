# Pilha Tecnológica

## Status

Resumo operacional derivado da spec atual.

## Stack definida

- Backend: Python 3.12 + Django 5 + Django REST Framework
- Frontend: React 18 + Vite + React Router
- Banco principal: MySQL 8
- Integração externa: Oracle via `oracledb`
- Autenticação de API: JWT
- Servidor de aplicação: Gunicorn
- Agendamento: `cron`

## Diretriz de adoção

- Manter a solução simples no MVP.
- Evitar Celery, Redis, WebSockets e componentes não exigidos pelo escopo atual.
- Tratar Oracle apenas como fonte de leitura.

## Fonte

- [SPEC.md](/C:/Users/ANDREGARCIA/ChemAnalytics_v3/docs/SPEC.md)
