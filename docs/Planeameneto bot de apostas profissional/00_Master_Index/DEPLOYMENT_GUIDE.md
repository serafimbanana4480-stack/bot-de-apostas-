# Deployment Guide

**ID:** `DEP-001` | **Fase:** #phase/1 | **Owner:** DevOps Lead | **Status:** #status/active

---

## 1. PREPARAÇÃO DE VPS

### 1.1 Especificações Mínimas

| Componente | Especificação | Custo Mensal |
|------------|---------------|--------------|
| VPS | 4 vCPU, 8 GB RAM, 160 GB SSD | ~€12 (Hetzner CPX31) |
| OS | Ubuntu 22.04 LTS | - |
| Localização | Frankfurt (Europa) | - |

### 1.2 Setup Inicial

```bash
# SSH para o VPS
ssh root@your-vps-ip

# Atualizar sistema
apt update && apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Verificar Docker Compose v2 (já incluído no Docker moderno)
docker compose version

# Se não estiver disponível, instalar plugin:
# apt install docker-compose-plugin

# Criar utilizador não-root
adduser vb_admin
usermod -aG sudo vb_admin
usermod -aG docker vb_admin

# Configurar SSH
mkdir -p /home/vb_admin/.ssh
cp /root/.ssh/authorized_keys /home/vb_admin/.ssh/
chown -R vb_admin:vb_admin /home/vb_admin/.ssh
chmod 700 /home/vb_admin/.ssh
chmod 600 /home/vb_admin/.ssh/authorized_keys

# Desativar root login
sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
systemctl restart sshd

# Logout e login como vb_admin
exit
ssh vb_admin@your-vps-ip
```

---

## 2. DEPLOYMENT COM DOCKER COMPOSE

### 2.1 Preparar Ambiente

```bash
# Criar diretório do projeto
mkdir -p /opt/valuebetting
cd /opt/valuebetting

# Clonar repositório
git clone https://github.com/seu-usuario/value-betting-system.git .

# Criar .env
cp .env.example .env
nano .env  # Editar com suas credenciais

# Verificar .env antes de iniciar (obrigatório)
./scripts/verify_env.sh
```

### 2.2 Configurar Firewall

```bash
# Configurar UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8000/tcp
sudo ufw allow 3000/tcp
sudo ufw allow 9090/tcp
sudo ufw enable
```

### 2.3 Deploy

```bash
# Verificar .env antes de iniciar (obrigatório)
./scripts/verify_env.sh && docker compose build
./scripts/verify_env.sh && docker compose up -d

# Verificar status
docker compose ps

# Ver logs
docker compose logs -f

# Executar migrações
docker compose exec api python scripts/migrate_db.py
```

---

## 3. CONFIGURAÇÃO DE NGINX + SSL (Recomendado para Produção)

**Nota:** O Nginx corre como serviço nativo no host VPS (não como container), a menos que prefira adicioná-lo ao docker-compose.yml.

### 3.1 Instalar Nginx

```bash
sudo apt install nginx -y
sudo systemctl enable nginx
sudo systemctl start nginx
```

### 3.2 Configurar SSL com Certbot

```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obter certificado SSL
sudo certbot --nginx -d api.yourdomain.com

# Auto-renovação
sudo certbot renew --dry-run
```

### 3.3 Configurar Proxy

```nginx
# /etc/nginx/sites-available/valuebetting
server {
    listen 80;
    server_name api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /metrics {
        proxy_pass http://localhost:9090;
    }
}
```

---

## 4. CONFIGURAÇÃO DE BACKUP AUTOMÁTICO

### 4.1 Script de Backup

```bash
#!/bin/bash
# /opt/valuebetting/scripts/backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups"
RETENTION_DAYS=30

# Criar diretório de backup
mkdir -p "$BACKUP_DIR"

# Backup PostgreSQL
docker compose exec -T postgres pg_dump -U vb_admin valuebetting > "$BACKUP_DIR/db_$DATE.sql"

# Backup Redis
docker compose exec -T redis redis-cli --rdb /data/dump.rdb SAVE
docker cp vb-redis:/data/dump.rdb "$BACKUP_DIR/redis_$DATE.rdb"

# Comprimir backups
tar czf "$BACKUP_DIR/backup_$DATE.tar.gz" -C "$BACKUP_DIR" "db_$DATE.sql" "redis_$DATE.rdb"

# Limpar backups antigos
find "$BACKUP_DIR" -name "backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete

# Upload para S3 (opcional)
# aws s3 cp $BACKUP_DIR/backup_$DATE.tar.gz s3://vb-backups/

echo "Backup completado: backup_$DATE.tar.gz"
```

### 4.2 Agendar Backup

```bash
# Adicionar ao crontab
crontab -e

# Backup diário às 3 AM
0 3 * * * /opt/valuebetting/scripts/backup.sh >> /var/log/backup.log 2>&1
```

---

## 5. MONITORIZAÇÃO DE SAÚDE

### 5.1 Health Check Script

```bash
#!/bin/bash
# /opt/valuebetting/scripts/health_check.sh

# Check API
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
if [ $API_STATUS -ne 200 ]; then
    echo "CRITICAL: API health check failed"
    # Enviar alerta Telegram
fi

# Check PostgreSQL
docker exec vb-postgres pg_isready -U vb_admin
if [ $? -ne 0 ]; then
    echo "CRITICAL: PostgreSQL not ready"
fi

# Check Redis
docker exec vb-redis redis-cli ping
if [ $? -ne 0 ]; then
    echo "CRITICAL: Redis not responding"
fi

echo "All health checks passed"
```

### 5.2 Agendar Health Check

```bash
# Health check a cada 5 minutos
*/5 * * * * /opt/valuebetting/scripts/health_check.sh >> /var/log/health_check.log 2>&1
```

---

## 6. ROLLBACK PROCEDURE

### 6.1 Automático com Docker Compose

```bash
# Ver versão anterior
docker images | grep valuebetting

# Rollback para versão anterior
docker compose down
docker compose pull valuebetting:v1.0.5
docker compose up -d

# Verificar status
docker compose ps
docker compose logs -f
```

### 6.2 Manual com Database

```bash
# Se migration falhar, rollback database
docker compose exec api alembic downgrade -1

# Se deployment falhar, restaurar backup
docker compose down
cd /opt/backups
tar xzf backup_20240115_030000.tar.gz
docker compose up -d postgres
docker exec -i vb-postgres psql -U vb_admin valuebetting < db_20240115_030000.sql
docker compose up -d
```

---

## 7. ZERO DOWNTIME DEPLOYMENT

### 7.1 Blue-Green Deployment

```bash
# Deploy nova versão em green
docker compose -f docker-compose.green.yml up -d

# Testar health check
curl -f http://localhost:8001/health

# Switch traffic (update Nginx)
# Atualizar nginx.conf para apontar para porta 8001
sudo nginx -s reload

# Parar versão antiga (blue)
docker compose -f docker-compose.blue.yml down
```

### 7.2 Rolling Update

```bash
# Atualizar serviço por serviço
docker compose up -d --no-deps postgres
docker compose up -d --no-deps redis
docker compose up -d --no-deps api

# Verificar cada serviço antes de continuar
```

---

## 8. CHECKLIST DE DEPLOYMENT

### Pré-Deploy
- [ ] Código testado e aprovado em PR
- [ ] Todas as migrações de banco preparadas
- [ ] Backup do banco realizado
- [ ] Segredos atualizados no VPS
- [ ] Health check script configurado

### Pós-Deploy
- [ ] Serviços iniciados corretamente
- [ ] Health check passando
- [ ] Monitorização ativa
- [ ] Logs sendo recolhidos
- [ ] Alertas funcionais
- [ ] Backup automático agendado

---

## 9. TROUBLESHOOTING DEPLOYMENT

### 9.1 Container Falha ao Iniciar

```bash
# Ver logs
docker-compose logs api

# Verificar variáveis de ambiente
docker-compose config

# Recriar container
docker-compose up -d --force-recreate api
```

### 9.2 Database Migration Falha

```bash
# Verificar status da migration
docker-compose exec api alembic current

# Verificar logs
docker-compose exec api alembic upgrade head

# Manual SQL se necessário
docker-compose exec -T postgres psql -U vb_admin valuebetting
```

### 9.3 Memória Insuficiente

```bash
# Ver uso de memória
docker stats

# Aumentar swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## 10. LINKS CRUZADOS

- [[00_Master_Index/GETTING_STARTED]] ← Setup local
- [[00_Master_Index/INTEGRATION_GUIDE]] ← Integração
- [[13_Infrastructure/VPS_CONFIGURACAO]] → VPS detalhado
- [[12_DevOps/CI_CD_SETUP]] → CI/CD
- [[26_Runbooks/RUNBOOK_DOWNTIME]] → Resolução de problemas
