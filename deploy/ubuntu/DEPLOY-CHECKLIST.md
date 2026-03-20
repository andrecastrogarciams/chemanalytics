# Checklist de Merge e Deploy

## Antes do merge

- [ ] PR `chore/ubuntu-deploy-templates` aberto
- [ ] CI do GitHub Actions aprovado
- [ ] revisao concluida
- [ ] branch pronta para merge em `main`

## Apos o merge

- [ ] atualizar a branch `main` local ou no servidor
- [ ] confirmar presenca dos arquivos em `deploy/ubuntu/`
- [ ] revisar `docs/install-deploy.md`

## No servidor Ubuntu

- [ ] criar usuario `chemanalytics`
- [ ] criar diretorio `/opt/chemanalytics`
- [ ] copiar o projeto para `/opt/chemanalytics`
- [ ] ajustar ownership para `chemanalytics:chemanalytics`
- [ ] criar `.venv`
- [ ] instalar `backend/requirements.txt`
- [ ] instalar `backend/requirements-integration.txt`
- [ ] copiar `deploy/ubuntu/chemanalytics.env.example` para `.env`
- [ ] ajustar variaveis reais do ambiente
- [ ] rodar `python backend/manage.py migrate`
- [ ] rodar `python backend/manage.py collectstatic --noinput`
- [ ] rodar `python backend/manage.py check`
- [ ] rodar `npm ci` no `frontend`
- [ ] rodar `npm run build` no `frontend`
- [ ] confirmar que o build usou `frontend/.env.production` com `VITE_API_BASE_URL=/api`

## Systemd

- [ ] copiar `deploy/ubuntu/chemanalytics.service` para `/etc/systemd/system/`
- [ ] rodar `sudo systemctl daemon-reload`
- [ ] rodar `sudo systemctl enable chemanalytics`
- [ ] rodar `sudo systemctl start chemanalytics`
- [ ] validar `sudo systemctl status chemanalytics`

## Nginx

- [ ] copiar `deploy/ubuntu/nginx.chemanalytics.conf` para `/etc/nginx/sites-available/chemanalytics`
- [ ] criar symlink em `/etc/nginx/sites-enabled/chemanalytics`
- [ ] validar `sudo nginx -t`
- [ ] rodar `sudo systemctl reload nginx`

## Validacao final

- [ ] acessar `GET /api/v1/health/live`
- [ ] acessar `GET /api/v1/health/dependencies`
- [ ] validar login com usuario ativo
- [ ] validar carregamento do frontend
- [ ] validar logs da aplicacao
- [ ] confirmar que nenhuma outra aplicacao do servidor foi impactada

## Rollback se necessario

- [ ] `sudo systemctl stop chemanalytics`
- [ ] remover/desabilitar apenas o bloco `chemanalytics` no Nginx
- [ ] restaurar versao anterior em `/opt/chemanalytics`
- [ ] restaurar `backend/db.sqlite3` se aplicavel
- [ ] subir novamente o service
