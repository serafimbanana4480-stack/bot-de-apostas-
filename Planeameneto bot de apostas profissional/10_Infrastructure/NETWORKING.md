# NETWORKING — Configuração de Rede 100% Gratuita

**ID:** `INF-005` | **Versão:** v1.0 | **Data:** 2026-05-17  
**Status:** #status/pending | **Owner:** DevOps Engineer  
**Custo:** **0€** (Todas as ferramentas open source)

---

## 1. OVERVIEW

Configuração de rede segura usando apenas ferramentas gratuitas e open source.

---

## 2. FIREWALL — UFW

### 2.1 Configuração Base

```bash
# Instalar UFW
sudo apt install ufw -y

# Política padrão: negar tudo
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Permitir SSH (restrito ao seu IP)
sudo ufw allow from <SEU_IP>/32 to any port 22

# Permitir HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Ativar
sudo ufw enable
```

### 2.2 Regras para Serviços Internos

```bash
# API (restrito)
sudo ufw allow from <SEU_IP>/32 to any port 8000

# Grafana (restrito)
sudo ufw allow from <SEU_IP>/32 to any port 3000

# Prometheus (restrito ou VPN only)
sudo ufw allow from <SEU_IP>/32 to any port 9090

# Verificar status
sudo ufw status verbose
```

---

## 3. PROTEÇÃO SSH — fail2ban

### 3.1 Instalação e Configuração

```bash
# Instalar
sudo apt install fail2ban -y

# Criar configuração local
sudo tee /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = 22
filter = sshd
logpath = /var/log/auth.log
EOF

# Reiniciar
sudo systemctl restart fail2ban
sudo systemctl enable fail2ban
```

### 3.2 SSH Hardening

```bash
# Editar /etc/ssh/sshd_config
sudo nano /etc/ssh/sshd_config

# Configurações recomendadas:
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 2

# Reiniciar SSH
sudo systemctl restart sshd
```

---

## 4. REVERSE PROXY — Nginx

### 4.1 Instalação

```bash
# Instalar Nginx
sudo apt install nginx -y

# Remover default site
sudo rm /etc/nginx/sites-enabled/default
```

### 4.2 Configuração SSL (Let's Encrypt)

```bash
# Instalar certbot
sudo apt install certbot python3-certbot-nginx -y

# Obter certificado (modo standalone primeiro)
sudo certbot certonly --standalone -d seu-dominio.duckdns.org

# Configurar auto-renovação
sudo certbot renew --dry-run
```

### 4.3 Configuração Nginx

```bash
# Criar configuração
sudo tee /etc/nginx/sites-available/vbq << 'EOF'
server {
    listen 80;
    server_name seu-dominio.duckdns.org;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name seu-dominio.duckdns.org;

    ssl_certificate /etc/letsencrypt/live/seu-dominio.duckdns.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/seu-dominio.duckdns.org/privkey.pem;

    # API
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Grafana
    location /grafana/ {
        proxy_pass http://localhost:3000/;
    }
}
EOF

# Ativar
sudo ln -s /etc/nginx/sites-available/vbq /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 5. DDNS — DuckDNS

### 5.1 Configuração

```bash
# Criar script de atualização
mkdir -p ~/scripts
cat > ~/scripts/duckdns.sh << 'EOF'
#!/bin/bash
echo url="https://www.duckdns.org/update?domains=SEU-DOMINIO&token=SEU-TOKEN&ip=" | curl -k -o ~/duckdns.log -K -
EOF

chmod +x ~/scripts/duckdns.sh

# Adicionar ao crontab (a cada 5 minutos)
(crontab -l 2>/dev/null; echo "*/5 * * * * ~/scripts/duckdns.sh") | crontab -
```

---

## 6. CUSTO

| Ferramenta | Licença | Custo |
|--------------|---------|-------|
| UFW | GPL | **0€** |
| fail2ban | GPL | **0€** |
| Nginx | BSD | **0€** |
| Let's Encrypt | MPL | **0€** |
| DuckDNS | Gratuito | **0€** |
| **TOTAL** | | **0€** |

---

## 7. CHECKLIST

- [ ] UFW instalado e configurado
- [ ] fail2ban ativo
- [ ] SSH hardening aplicado
- [ ] Nginx instalado
- [ ] SSL configurado (Let's Encrypt)
- [ ] DuckDNS configurado
- [ ] Regras de firewall testadas

---

## 8. LINKS

- [[VPS_CONFIGURACAO]] → Configuração de VPS
- [[10_Infrastructure/INDEX]] ← Secção mãe

---

**Rede 100% Gratuita e Segura**
