# VPS_CONFIGURACAO — Setup do Servidor

**ID:** `INF-001` | **Fase:** #phase/1 | **Owner:** DevOps Engineer | **Status:** #status/pending

---

## 1. ESPECIFICACAO

| Componente | Especificacao |
|------------|---------------|
| VPS Provider | Hetzner / DigitalOcean / Vultr (recomendado: Hetzner por preco) |
| Tipo | CPX21 (Hetzner) ou equivalente |
| vCPU | 4 |
| RAM | 8 GB |
| Disco | 100 GB SSD |
| OS | Ubuntu 22.04 LTS |
| Localizacao | Frankfurt (proximo de exchanges europeias) |
| Custo | ~50-60 EUR/mes |

---

## 2. SETUP INICIAL

```bash
# Apos SSH como root
apt update && apt upgrade -y
apt install -y curl wget vim git htop ufw fail2ban docker.io docker-compose

# Criar user nao-root
adduser vb_admin
usermod -aG sudo vb_admin
usermod -aG docker vb_admin

# Copiar chave SSH
mkdir -p /home/vb_admin/.ssh
cp /root/.ssh/authorized_keys /home/vb_admin/.ssh/
chown -R vb_admin:vb_admin /home/vb_admin/.ssh
chmod 700 /home/vb_admin/.ssh
chmod 600 /home/vb_admin/.ssh/authorized_keys

# Desativar login root
sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
systemctl restart sshd
```

---

## 3. FIREWALL (UFW)

```bash
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 5432/tcp  # PostgreSQL (localhost only recomendado)
ufw allow 6379/tcp  # Redis (localhost only recomendado)
ufw allow 8000/tcp  # FastAPI (ou 80/443 com Nginx)
ufw allow 3000/tcp  # Grafana
ufw allow 9090/tcp  # Prometheus
ufw enable
```

**Nota:** PostgreSQL e Redis devem escutar apenas em 127.0.0.1. Nao expor para internet.

---

## 4. FAIL2BAN

```bash
# Protecao contra brute force SSH
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
EOF

systemctl restart fail2ban
```

---

## 5. BACKUP AUTOMATICO

```bash
# Script de backup diario para S3 (ou local)
cat > /opt/backup/backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d)
pg_dump valuebetting > /backups/db_${DATE}.sql
tar czf /backups/redis_${DATE}.rdb.tar.gz /var/lib/redis/dump.rdb
# Sync para S3 (quando configurado)
# aws s3 sync /backups/ s3://vb-backups/daily/
EOF

chmod +x /opt/backup/backup.sh
echo "0 3 * * * /opt/backup/backup.sh" | crontab -
```

---

## 6. MONITORIZACAO BASICA DO SISTEMA

```bash
# Node exporter para Prometheus (container)
docker run -d \
  --name node-exporter \
  --net="host" \
  --pid="host" \
  -v "/:/host:ro,rslave" \
  prom/node-exporter:latest \
  --path.rootfs=/host
```

---

## 7. BACKLOG

- [ ] Aprovisionar VPS
- [ ] Configurar SSH hardening
- [ ] Instalar Docker e Docker Compose
- [ ] Configurar backups automaticos
- [ ] Documentar procedimentos de disaster recovery

---

## 8. LINKS CRUZADOS

- [[13_Infrastructure/INDEX]] ← Secao mae
- [[12_DevOps/INDEX]] → CI/CD e deploy
