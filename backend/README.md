# Backend

Base inicial para a API Django REST do projeto `chemanalytics`.

## Estrutura

- `manage.py`: entrypoint padrão do Django
- `requirements.txt`: dependências mínimas para bootstrap local
- `requirements-integration.txt`: dependências de integração e runtime operacional
- `config/`: settings, urls e ASGI/WSGI
- `apps/health/`: app inicial para health check

## Objetivo desta fase

Disponibilizar o scaffold mínimo para as próximas stories sem ainda implementar autenticação, domínio de fórmulas ou integração com Oracle.

## Instalação

- Bootstrap local: `pip install -r backend/requirements.txt`
- Integrações posteriores: `pip install -r backend/requirements-integration.txt`
