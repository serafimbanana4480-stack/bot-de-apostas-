# POSTGRES_SEGURANCA — Segurança do PostgreSQL

**ID:** `SEC-007` | **Fase:** Todas | **Owner:** DevOps Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Documentar as configurações de segurança do PostgreSQL.

---

## 2. CONFIGURAÇÃO DE SEGURANÇA

### 2.1 Autenticação SSL

```bash
# postgresql.conf
ssl = on
ssl_cert_file = '/etc/ssl/certs/server.crt'
ssl_key_file = '/etc/ssl/private/server.key'
ssl_ca_file = '/etc/ssl/certs/ca.crt'
ssl_crl_file = ''

# Forçar SSL para todas as conexões
ssl_min_protocol_version = 'TLSv1.3'
```

**Explicação:** TLS 1.3 elimina vulnerabilidades de downgrade e reduz a latência do handshake. Em produção, nunca permitir conexões não-encriptadas de fora do Docker network.

### 2.2 pg_hba.conf (Host-Based Authentication)

```
# TYPE  DATABASE        USER            ADDRESS                 METHOD
# Local connections (dentro do container/Docker)
local   all             postgres                                peer
local   all             vb_admin                                md5

# Conexões da rede Docker interna (seguro)
hostssl all             vb_user         172.16.0.0/12           md5

# Conexões externas (requer SSL + senha forte)
hostssl all             all             0.0.0.0/0               md5

# Rejeitar conexões não-SSL de qualquer origem
hostnossl all           all             0.0.0.0/0               reject
```

**Explicação:** `172.16.0.0/12` cobre a faixa de IPs do Docker. `hostnossl reject` garante que nenhuma conexão não-encriptada é aceite, mesmo que a senha esteja correta.

---

## 3. CONTROLO DE ACESSO

### 3.1 Roles e Permissões

```sql
-- Criar roles
CREATE ROLE vb_read_only NOLOGIN;
CREATE ROLE vb_read_write NOLOGIN;
CREATE ROLE vb_admin NOLOGIN;

-- Privilégios read-only (subscritores, dashboards)
GRANT USAGE ON SCHEMA bronze, silver, gold, meta TO vb_read_only;
GRANT SELECT ON ALL TABLES IN SCHEMA bronze, silver, gold, meta TO vb_read_only;

-- Privilégios read-write (aplicação, pipeline)
GRANT USAGE ON SCHEMA bronze, silver, gold, meta TO vb_read_write;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA bronze, silver, gold, meta TO vb_read_write;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA bronze, silver, gold, meta TO vb_read_write;

-- Privilégios admin (migrações, DDL)
GRANT ALL PRIVILEGES ON SCHEMA bronze, silver, gold, meta TO vb_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA bronze, silver, gold, meta TO vb_admin;

-- Criar utilizadores
CREATE USER app_user WITH PASSWORD '${APP_DB_PASSWORD}';
GRANT vb_read_write TO app_user;

CREATE USER readonly_user WITH PASSWORD '${READONLY_DB_PASSWORD}';
GRANT vb_read_only TO readonly_user;

CREATE USER admin_user WITH PASSWORD '${ADMIN_DB_PASSWORD}';
GRANT vb_admin TO admin_user;

-- Revogar privilégios perigosos
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
```

### 3.2 Row-Level Security (RLS) para Subscritores

```sql
-- Exemplo: subscritores só veem os seus próprios dados
ALTER TABLE meta.subscriber_data ENABLE ROW LEVEL SECURITY;

CREATE POLICY subscriber_isolation ON meta.subscriber_data
    FOR ALL
    TO vb_read_write
    USING (subscriber_id = current_setting('app.current_subscriber_id')::INT);
```

---

## 4. AUDITORIA

### 4.1 Auditoria de Queries (pgAudit)

```sql
-- Instalar extensão pgAudit (requer instalação no container)
CREATE EXTENSION IF NOT EXISTS pgaudit;

-- Configurar auditoria
ALTER SYSTEM SET pgaudit.log = 'write, ddl';
ALTER SYSTEM SET pgaudit.log_catalog = off;
ALTER SYSTEM SET pgaudit.log_parameter = on;

-- Reiniciar PostgreSQL para aplicar
```

**Explicação:** `pgaudit` regista todas as operações de escrita (INSERT, UPDATE, DELETE) e DDL (CREATE, DROP, ALTER). Isto permite rastrear quem alterou dados e quando. Crítico para GDPR e compliance.

### 4.2 Log de Conexões

```bash
# postgresql.conf
log_connections = on
log_disconnections = on
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
log_statement = 'mod'  # Logar apenas statements que modificam dados
```

---

## 5. BACKUP E RECUPERAÇÃO SEGURA

### 5.1 Backup Encriptado

```bash
#!/bin/bash
# backup_encrypted.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/secure/backups"
GPG_RECIPIENT="backup@valuebetting.pt"

# Backup com encriptação GPG
docker compose exec -T postgres pg_dump -U admin_user -h localhost -Fc valuebetting | \
    gpg --encrypt --recipient $GPG_RECIPIENT --trust-model always \
    > $BACKUP_DIR/backup_${DATE}.dump.gpg

# Verificar integridade
gpg --decrypt $BACKUP_DIR/backup_${DATE}.dump.gpg | pg_restore --list > /dev/null && echo "OK"
```

### 5.2 Política de Retenção

| Tipo | Frequência | Retenção | Encriptação |
|------|-----------|----------|-------------|
| Full backup | Diário | 7 dias | GPG |
| Full backup | Semanal | 4 semanas | GPG |
| Full backup | Mensal | 12 meses | GPG |
| WAL archives | Contínuo | 7 dias | GPG |

---

## 6. HARDENING

### 6.1 Configurações de Segurança

```sql
-- postgresql.conf
password_encryption = 'scram-sha-256'
shared_preload_libraries = 'pg_stat_statements,pgaudit'
max_connections = 100  # Limitar para evitar DoS

-- Desativar funcionalidades desnecessárias
log_min_messages = 'warning'
log_min_error_statement = 'error'
```

### 6.2 Docker Security

```yaml
# docker-compose.yml (extração)
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_USER: vb_admin
      POSTGRES_DB: valuebetting
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./ssl:/etc/ssl/certs:ro  # Certificados SSL read-only
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
      - /var/run/postgresql
    networks:
      - vb-network
    ports:
      - "127.0.0.1:5432:5432"  # Apenas localhost, não exposto externamente
```

**Explicação:** `read_only: true` impede que o container escreva no filesystem exceto em volumes explícitos. `no-new-privileges:true` previne privilege escalation. Porta 5432 ligada apenas a `127.0.0.1` impede acesso externo direto — todo o acesso deve passar pelo Docker network ou SSH tunnel.

---

## 7. BACKLOG

- [x] Configurar autenticação SSL (TLS 1.3)
- [x] Implementar roles e controlo de acesso
- [x] Documentar row-level security
- [x] Configurar auditoria (pgAudit)
- [x] Backup encriptado com GPG
- [x] Hardening Docker (read_only, no-new-privileges)
- [ ] Implementar fail2ban para PostgreSQL
- [ ] Configurar monitorização de acessos suspeitos
- [ ] Penetration testing anual

---

## 8. LINKS CRUZADOS

- [[34_Security/INDEX]] ← Secção mãe
- [[34_Security/SECRETS_MANAGEMENT]] → Gestão de credenciais
- [[34_Security/BACKUPS_ENCRIPTADOS]] → Estratégia de backup
- [[15_Database/BACKUP_STRATEGY]] → Procedimentos de backup
- [[16_Compliance/GDPR]] → Compliance e auditoria
