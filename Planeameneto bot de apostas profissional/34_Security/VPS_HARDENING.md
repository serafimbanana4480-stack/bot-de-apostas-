# VPS_HARDENING — Segurança do Servidor VPS

**ID:** `SEC-005` | **Fase:** #phase/1 | **Owner:** DevOps Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Documentar os procedimentos de hardening do servidor VPS para garantir segurança do sistema.

---

## 2. CONFIGURAÇÃO INICIAL

### 2.1 Sistema Operacional
- **OS:** Ubuntu 22.04 LTS
- **Atualizações:** Automáticas (security only)
- **Firewall:** UFW (Uncomplicated Firewall)

### 2.2 Usuários
- **root:** Desabilitado login direto
- **deploy:** Usuário sudo com SSH keys
- **app:** Usuário sem sudo para aplicação

---

## 3. HARDENING SSH

### 3.1 Configuração /etc/ssh/sshd_config
```bash
# Desabilitar root login
PermitRootLogin no

# Apenas autenticação por chave
PasswordAuthentication no
PubkeyAuthentication yes

# Limitar usuários
AllowUsers deploy

# Mudar porta padrão
Port 2222

# Protocolo SSH v2 apenas
Protocol 2

# Desabilitar métodos inseguros
KexAlgorithms curve25519-sha256@libssh.org,diffie-hellman-group-exchange-sha256
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com
MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com
```

### 3.2 Fail2Ban
```bash
# Instalar
sudo apt install fail2ban

# Configurar /etc/fail2ban/jail.local
[sshd]
enabled = true
port = 2222
maxretry = 3
bantime = 3600
findtime = 600
```

---

## 4. FIREWALL (UFW)

### 4.1 Regras Padrão
```bash
# Políticas padrão
sudo ufw default deny incoming
sudo ufw default allow outgoing

# SSH
sudo ufw allow 2222/tcp

# HTTP/HTTPS (se necessário)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Ativar
sudo ufw enable
```

### 4.2 Regras Específicas
```bash
# Limitar tentativas SSH
sudo ufw limit 2222/tcp

# Permitir apenas IPs específicos (opcional)
sudo ufw allow from 203.0.113.0/24 to any port 2222
```

---

## 5. HARDENING SISTEMA

### 5.1 Atualizações Automáticas
```bash
# Instalar unattended-upgrades
sudo apt install unattended-upgrades

# Configurar /etc/apt/apt.conf.d/50unattended-upgrades
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";
};
Unattended-Upgrade::AutoFixInterruptedDpkg "true";
Unattended-Upgrade::Remove-Unused-Kernel-Packages "true";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
```

### 5.2 Kernel Parameters
```bash
# /etc/sysctl.conf
# Network hardening
net.ipv4.ip_forward = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.secure_redirects = 0
net.ipv4.conf.default.secure_redirects = 0
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1
```

---

## 6. HARDENING APLICAÇÃO

### 6.1 Isolamento de Usuário
```bash
# Criar usuário dedicado
sudo adduser --no-create-home --disabled-password betting-app

# Permissões restritas
sudo chown -R betting-app:betting-app /opt/betting-bot
sudo chmod 750 /opt/betting-bot
```

### 6.2 Systemd Service
```ini
# /etc/systemd/system/betting-bot.service
[Unit]
Description=Betting Bot Service
After=network.target postgresql.service

[Service]
Type=simple
User=betting-app
Group=betting-app
WorkingDirectory=/opt/betting-bot
ExecStart=/opt/betting-bot/venv/bin/python -m betting_bot.main
Restart=always
RestartSec=10

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/log/betting-bot /var/lib/betting-bot

[Install]
WantedBy=multi-user.target
```

---

## 7. MONITORIZAÇÃO DE SEGURANÇA

### 7.1 Logs de Auditoria
```bash
# Instalar auditd
sudo apt install auditd

# Monitorizar acessos críticos
sudo auditctl -w /etc/ssh/sshd_config -p wa -k ssh_config
sudo auditctl -w /etc/passwd -p wa -k passwd_changes
```

### 7.2 Log Rotation
```bash
# /etc/logrotate.d/betting-bot
/var/log/betting-bot/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0640 betting-app betting-app
}
```

---

## 8. BACKUP DE SEGURANÇA

### 8.1 Backup de Configurações
```bash
#!/bin/bash
# backup-configs.sh
BACKUP_DIR="/backups/configs"
DATE=$(date +%Y%m%d)

mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/configs-$DATE.tar.gz \
    /etc/ssh/sshd_config \
    /etc/ufw \
    /etc/fail2ban \
    /etc/systemd/system/betting-bot.service
```

---

## 9. CHECKLIST DE HARDENING

- [ ] SSH configurado (chaves apenas, porta não-padrão)
- [ ] Fail2Ban instalado e configurado
- [ ] UFW ativo com regras apropriadas
- [ ] Atualizações automáticas configuradas
- [ ] Kernel parameters ajustados
- [ ] Usuário dedicado para aplicação
- [ ] Systemd service com segurança
- [ ] Auditd instalado
- [ ] Log rotation configurado
- [ ] Backup de configurações automatizado

---

## 10. BACKLOG

- [ ] Implementar intrusion detection (IDS)
- [ ] Configurar VPN para acesso administrativo
- [ ] Implementar file integrity monitoring (FIM)
- [ ] Adicionar hardening para PostgreSQL

---

## 11. LINKS CRUZADOS

- [[34_Security/INDEX]] ← Secção mãe
- [[34_Security/SECURITY_ARCHITECTURE]] → Arquitetura de segurança
- [[34_Security/SECRETS_MANAGEMENT]] → Gestão de secrets
