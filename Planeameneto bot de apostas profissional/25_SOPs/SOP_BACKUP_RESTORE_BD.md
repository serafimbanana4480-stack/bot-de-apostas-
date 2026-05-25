# SOP_BACKUP_RESTORE_BD — Procedimento Operacional Padrão

**ID:** `SOP-009` | **Fase:** #phase/1 | **Owner:** DevOps Engineer | **Status:** #status/active
**Última Revisão:** 2024-05-13 | **Próxima Revisão:** 2024-08-13

---

## 1. OBJETIVO

Estabelecer procedimentos padronizados para backup e restore da base de dados PostgreSQL, garantindo que os dados estão protegidos contra perda, corrupção, ou desastre, e que podem ser restaurados rapidamente em caso de incidente.

---

## 2. APLICAÇÃO

**Backup:**
- Backup diário automático (02:00 UTC)
- Backup semanal completo
- Backup antes de manutenção ou migração

**Restore:**
- Após corrupção de dados
- Após erro humano grave
- Após desastre (perda de VPS)
- Testes periódicos de restore

**Responsável:**
- DevOps Engineer (execução)
- Operations Lead (verificação)

**Duração estimada:**
- Backup: 30-60 minutos
- Restore: 1-3 horas

---

## 3. ESTRATÉGIA DE BACKUP

| Tipo | Frequência | Retenção | Localização |
|------|------------|----------|-------------|
| Backup incremental | Diário (02:00 UTC) | 7 dias | Local + S3 |
| Backup completo | Semanal (domingo) | 4 semanas | S3 |
| Backup mensal | Mensal (dia 1) | 12 meses | S3 Glacier |
| Backup antes de manutenção | Sob demanda | 30 dias | S3 |

---

## 4. PROCEDIMENTO DE BACKUP

### 4.1. Backup Automático (diário)

**Configuração (cron):**
```bash
# 02:00 UTC todos os dias
0 2 * * * /usr/local/bin/backup_postgres.sh >> /var/log/postgres_backup.log 2>&1
```

**Script de backup:**
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/postgres"
S3_BUCKET="s3://seusistema-backups/postgres"

# Criar backup
pg_dump -U postgres -h localhost -F c -b -v -f "$BACKUP_DIR/backup_$DATE.dump" nba_betting

# Comprimir
gzip "$BACKUP_DIR/backup_$DATE.dump"

# Upload para S3
aws s3 cp "$BACKUP_DIR/backup_$DATE.dump.gz" "$S3_BUCKET/daily/backup_$DATE.dump.gz"

# Limpar backups locais antigos (> 7 dias)
find $BACKUP_DIR -name "backup_*.dump.gz" -mtime +7 -delete

# Enviar notificação
if [ $? -eq 0 ]; then
    echo "Backup concluído com sucesso: $DATE" | telegram-send
else
    echo "Backup falhou: $DATE" | telegram-send --format markdown
fi
```

### 4.2. Backup Manual (antes de manutenção)

**Passos:**

1. **Notificar equipa:**
   - [ ] Enviar mensagem: "Iniciando backup manual antes de manutenção"
   - [ ] Indicar duração estimada

2. **Executar backup:**
   ```bash
   pg_dump -U postgres -h localhost -F c -b -v -f /tmp/manual_backup.dump nba_betting
   ```

3. **Verificar backup:**
   - [ ] Verificar tamanho do ficheiro
   - [ ] Verificar integridade: `pg_restore --list /tmp/manual_backup.dump`
   - [ ] Upload para S3

4. **Documentar:**
   - [ ] Registar timestamp
   - [ ] Registar motivo
   - [ ] Registar localização

---

## 5. PROCEDIMENTO DE RESTORE

### 5.1. Restore Completo

**Passos:**

1. **Preparação:**
   - [ ] Parar todos os serviços que acedem à BD
   - [ ] Notificar equipa que BD estará indisponível
   - [ ] Identificar backup a restaurar

2. **Download do backup:**
   ```bash
   aws s3 cp s3://seusistema-backups/postgres/daily/backup_YYYYMMDD_HHMMSS.dump.gz /tmp/
   gunzip /tmp/backup_YYYYMMDD_HHMMSS.dump.gz
   ```

3. **Parar PostgreSQL:**
   ```bash
   sudo systemctl stop postgresql
   ```

4. **Renomear base de dados atual (backup de segurança):**
   ```bash
   sudo -u postgres psql -c "ALTER DATABASE nba_betting RENAME TO nba_betting_old_$(date +%Y%m%d);"
   ```

5. **Criar nova base de dados:**
   ```bash
   sudo -u postgres createdb nba_betting
   ```

6. **Restaurar backup:**
   ```bash
   pg_restore -U postgres -h localhost -d nba_betting -v /tmp/backup_YYYYMMDD_HHMMSS.dump
   ```

7. **Verificar restore:**
   - [ ] Verificar tabelas: `\dt`
   - [ ] Verificar contagem de registos
   - [ ] Verificar integridade

8. **Iniciar PostgreSQL:**
   ```bash
   sudo systemctl start postgresql
   ```

9. **Reiniciar serviços:**
   - [ ] Iniciar serviços que acedem à BD
   - [ ] Verificar que serviços funcionam

10. **Notificar equipa:**
    - [ ] Enviar mensagem: "Restore concluído com sucesso"
    - [ ] Documentar incidente

### 5.2. Restore Pontual (tabela específica)

**Passos:**

1. **Exportar tabela do backup:**
   ```bash
   pg_restore -U postgres -h localhost -t nome_tabela -f /tmp/tabela_backup.dump backup.dump
   ```

2. **Fazer backup da tabela atual:**
   ```bash
   sudo -u postgres psql -c "CREATE TABLE nome_tabela_backup AS SELECT * FROM nome_tabela;"
   ```

3. **Restaurar tabela:**
   ```bash
   psql -U postgres -h localhost -d nba_betting -f /tmp/tabela_backup.dump
   ```

4. **Verificar:**
   - [ ] Verificar dados na tabela
   - [ ] Verificar integridade referencial

---

## 6. TESTE DE RESTORE

**Frequência:** Mensal

**Procedimento:**

1. **Criar base de dados de teste:**
   ```bash
   sudo -u postgres createdb nba_betting_test
   ```

2. **Restaurar backup mais recente:**
   ```bash
   pg_restore -U postgres -h localhost -d nba_betting_test backup_recente.dump
   ```

3. **Executar testes:**
   - [ ] Verificar contagem de registos
   - [ ] Executar queries de teste
   - [ ] Verificar integridade

4. **Documentar resultado:**
   - [ ] Registar data do teste
   - [ ] Registar duração
   - [ ] Registar problemas (se houver)

5. **Limpar:**
   ```bash
   sudo -u postgres dropdb nba_betting_test
   ```

---

## 7. CHECKLIST FINAL

**Backup:**
- [ ] Script configurado
- [ ] Cron job ativo
- [ ] Logs a funcionar
- [ ] Upload para S3 a funcionar
- [ ] Notificações a funcionar
- [ ] Teste de restore mensal

**Restore:**
- [ ] Backup identificado
- [ ] Serviços parados
- [ ] Backup atual preservado
- [ ] Restore executado
- [ ] Integridade verificada
- [ ] Serviços reiniciados
- [ ] Equipa notificada

---

## 8. LINKS CRUZADOS

- [[25_SOPs/INDEX]] ← Secção mãe
- [[13_Infrastructure/DISASTER_RECOVERY]] → Disaster Recovery
- [[15_Database/INDEX]] → Base de dados