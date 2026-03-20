# Deploy Ubuntu Seguro

Este pacote prepara o ChemAnalytics para rodar em um servidor Ubuntu com outras aplicacoes ja existentes, sem interferir nelas.

## Principios de isolamento

- usuario de sistema proprio: `chemanalytics`
- diretorio proprio: `/opt/chemanalytics`
- virtualenv proprio: `/opt/chemanalytics/.venv`
- porta interna propria: `127.0.0.1:8010`
- service proprio: `chemanalytics.service`
- server block proprio no Nginx

## Arquivos deste diretorio

- `chemanalytics.service`: unit file do `systemd`
- `nginx.chemanalytics.conf`: server block do Nginx
- `chemanalytics.env.example`: variaveis de ambiente para o backend

## Fluxo recomendado

1. criar usuario e diretorio dedicados
2. copiar o projeto para `/opt/chemanalytics`
3. criar `.venv`
4. instalar dependencias
5. copiar `chemanalytics.env.example` para `.env`
6. rodar `migrate`, `collectstatic` e `check`
7. instalar `chemanalytics.service`
8. instalar o bloco `nginx.chemanalytics.conf`
9. validar com `nginx -t`
10. subir o service

## Comandos sugeridos

### Usuario e pasta

```bash
sudo adduser --system --group --home /opt/chemanalytics chemanalytics
sudo mkdir -p /opt/chemanalytics
sudo chown -R chemanalytics:chemanalytics /opt/chemanalytics
```

### Backend

```bash
cd /opt/chemanalytics
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
python -m pip install -r backend/requirements-integration.txt
python backend/manage.py migrate
python backend/manage.py collectstatic --noinput
python backend/manage.py check
```

Para testes manuais no shell, carregue antes o `.env`:

```bash
set -a
source /opt/chemanalytics/.env
set +a
```

### Frontend

```bash
cd /opt/chemanalytics/frontend
npm ci
npm run build
```

Observacao:

- o repositório versiona `frontend/.env.production` com `VITE_API_BASE_URL=/api`
- assim o build de producao aponta para o proxy do Nginx, sem depender de `localhost`

### Systemd

```bash
sudo cp deploy/ubuntu/chemanalytics.service /etc/systemd/system/chemanalytics.service
sudo systemctl daemon-reload
sudo systemctl enable chemanalytics
sudo systemctl start chemanalytics
sudo systemctl status chemanalytics
```

### Nginx

```bash
sudo cp deploy/ubuntu/nginx.chemanalytics.conf /etc/nginx/sites-available/chemanalytics
sudo ln -s /etc/nginx/sites-available/chemanalytics /etc/nginx/sites-enabled/chemanalytics
sudo nginx -t
sudo systemctl reload nginx
```

## Rollback seguro

1. `sudo systemctl stop chemanalytics`
2. remover ou desabilitar apenas o bloco `chemanalytics` no Nginx
3. restaurar a versao anterior de `/opt/chemanalytics`
4. restaurar o `backend/db.sqlite3` se necessario
5. subir novamente o service

## O que nao fazer

- nao alterar blocos Nginx das outras aplicacoes
- nao usar a mesma porta de outra aplicacao
- nao substituir Python/Node globais do servidor
- nao reiniciar o servidor inteiro
- nao executar `apt upgrade` sem necessidade
