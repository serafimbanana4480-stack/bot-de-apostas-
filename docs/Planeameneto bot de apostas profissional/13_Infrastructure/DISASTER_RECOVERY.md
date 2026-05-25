# DISASTER_RECOVERY — Plano de Recuperação de Desastres

**ID:** `INF-006` | **Fase:** #phase/1-15 | **Owner:** DevOps Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Garantir que o sistema possa recuperar-se de desastres (perda de dados, falha de hardware, ataque, erro humano) com perda mínima de dados e downtime aceitável. RTO (Recovery Time Objective) e RPO (Recovery Point Objective) devem ser definidos e testados.

---

## 2. DEFINIÇÕES

### 2.1 RTO (Recovery Time Objective)
Tempo máximo aceitável para restaurar o sistema após desastre.

- **Crítico (Produção):** 4 horas
- **Importante (Staging):** 24 horas
- **Normal (Dev):** 48 horas

### 2.2 RPO (Recovery Point Objective)
Perda máxima de dados aceitável (tempo desde o último backup).

- **Base de dados:** 24 horas
- **Código/Configurações:** 0 horas (Git)
- **Logs/Métricas:** 7 dias

---

## 3. CENÁRIOS DE DESASTRE

### 3.1 Perda de Dados da Base de Dados

**Probabilidade:** Média
**Impacto:** Crítico

**Mitigação:**
- Backups diários automatizados
- Backups semanais retidos por 1 mês
- Backup mensal retido por 12 meses
- Backups armazenados off-site (S3 ou local separado)

**Recuperação:**
1. Identificar último backup consistente
2. Parar todas as aplicações
3. Restaurar backup para nova instância
4. Verificar integridade dos dados
5. Atualizar DNS/load balancer
6. Reiniciar aplicações
7. Verificar funcionamento end-to-end

**Tempo estimado:** 2-4 horas

---

### 3.2 Falha Completa do VPS

**Probabilidade:** Baixa
**Impacto:** Crítico

**Mitigação:**
- Infraestrutura como código (Terraform/Ansible)
- Snapshot semanal do VPS
- Backups off-site de todos os dados
- Documentação de setup completo

**Recuperação:**
1. Aprovisionar novo VPS
2. Executar scripts de setup automatizados
3. Restaurar backups da BD
4. Restaurar código do Git
5. Reconfigurar variáveis de ambiente
6. Atualizar DNS para novo IP
7. Testar sistema completamente

**Tempo estimado:** 4-8 horas

---

### 3.3 Ataque de Ransomware

**Probabilidade:** Baixa
**Impacto:** Crítico

**Mitigação:**
- Backups imutáveis (não podem ser deletados/alterados)
- Segregação de redes (BD não exposto)
- Firewall restritivo
- Monitorização de atividade suspeita
- Antivírus/antimalware no VPS

**Recuperação:**
1. Isolar sistema infectado (desconectar rede)
2. Identificar vetor de ataque
3. Wipe completo do VPS
4. Rebuild do zero (não restore de sistema)
5. Restaurar apenas dados (BD, código)
6. Patch de vulnerabilidade explorada
7. Varredura de segurança antes de re-lançar

**Tempo estimado:** 24-48 horas

---

### 3.4 Erro Humano (DROP TABLE, DELETE errado)

**Probabilidade:** Média
**Impacto:** Variável

**Mitigação:**
- Backups pontuais antes de operações de risco
- Queries de DML requerem confirmação explícita
- Ambiente de staging para testar migrations
- Audit trail de todas as operações

**Recuperação:**
1. Identificar exatamente o que foi alterado
2. Parar todas as aplicações
3. Restaurar backup pontual (se disponível)
4. Ou: Rollback da transação (se ainda na sessão)
5. Ou: Recuperar dados de logs (se habilitado)
6. Verificar integridade
7. Reiniciar aplicações

**Tempo estimado:** 1-2 horas (se backup pontual disponível)

---

### 3.5 Corrupção de Dados Silenciosa

**Probabilidade:** Baixa
**Impacto:** Alto

**Mitigação:**
- Validação de dados em cada ingestão
- Checksums de backups
- Testes periódicos de restore
- Monitorização de anomalias nos dados

**Recuperação:**
1. Identificar quando a corrupção começou (logs, métricas)
2. Restaurar backup anterior à corrupção
3. Re-ingestão de dados do período afetado
4. Verificação de integridade completa
5. Investigar root cause
6. Implementar prevenção para futuro

**Tempo estimado:** 4-12 horas (dependendo da quantidade de dados)

---

## 4. ESTRATÉGIA DE BACKUP

### 4.1 Política de Retenção

| Tipo | Frequência | Retenção | Localização |
|------|------------|----------|-------------|
| BD Full | Diário (02:00) | 7 dias | Local + S3 |
| BD Differential | A cada 6h | 2 dias | Local |
| BD Transaction Log | A cada 15min | 24h | Local |
| BD Monthly | Mensal (1º) | 12 meses | S3 |
| Código | Contínuo (Git) | Infinito | GitHub/GitLab |
| Configurações | Contínuo (Git) | Infinito | GitHub/GitLab |
| Logs | Diário | 30 dias | Local |
| Métricas | Contínuo | 90 dias | Prometheus |

### 4.2 Implementação

```bash
# Script de backup diário
#!/bin/bash
# /opt/backup/backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
S3_BUCKET="s3://vb-backups"

# Backup PostgreSQL
pg_dump -U valuebetting valuebetting | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Backup Redis
cp /var/lib/redis/dump.rdb $BACKUP_DIR/redis_$DATE.rdb

# Backup configurações
tar czf $BACKUP_DIR/config_$DATE.tar.gz /etc/ /opt/valuebetting/.env

# Upload para S3 (com criptografia)
aws s3 cp $BACKUP_DIR/db_$DATE.sql.gz $S3_BUCKET/postgres/ --server-side-encryption AES256
aws s3 cp $BACKUP_DIR/redis_$DATE.rdb $S3_BUCKET/redis/ --server-side-encryption AES256

# Limpar backups locais antigos (> 7 dias)
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
find $BACKUP_DIR -name "*.rdb" -mtime +7 -delete
```

### 4.3 Teste de Restore

**Frequência:** Mensal
**Processo:**
1. Selecionar backup aleatório do mês anterior
2. Restaurar para ambiente de staging
3. Verificar integridade dos dados
4. Executar suíte de testes
5. Documentar tempo de restore
6. Se falhar, investigar e corrigir processo de backup

---

## 5. HIGH AVAILABILITY (FUTURO)

### 5.1 Arquitetura HA (Fase 10+)

```
[DNS Round Robin / Load Balancer]
    ↓
[API Server 1] [API Server 2] [API Server 3]
    ↓              ↓              ↓
[PostgreSQL Primary] [PostgreSQL Replica 1] [PostgreSQL Replica 2]
    ↓
[Redis Primary] [Redis Replica]
```

**Benefícios:**
- Se um servidor cair, outros continuam
- Zero downtime para manutenção
- Escala horizontal possível

**Custo adicional:** +200-400€/mês

---

## 6. PLANO DE COMUNICAÇÃO

### 6.1 Durante Desastre

**Stakeholders:**
- Equipa técnica (DevOps, Engenheiros)
- Gestão (se downtime > 2h)
- Subscritores (se downtime > 4h)

**Mensagem template:**
```
ASSUNTO: [URGENTE] Interrupção de Serviço - Value Betting System

Caros utilizadores,

Estamos a experienciar uma interrupção técnica no nosso sistema. 
A nossa equipa está a trabalhar ativamente para resolver o problema.

Estado atual: [Investigando / Em reparação / Quase resolvido]
Tempo estimado de resolução: [X horas]

Pedimos desculpa pelo inconveniente.
Equipa Value Betting System
```

### 6.2 Pós-Desastre

**Post-mortem obrigatório:**
- O que aconteceu?
- Por que aconteceu?
- Como foi resolvido?
- Como prevenir no futuro?
- Lições aprendidas

---

## 7. DRILLS E TESTES

### 7.1 Simulação Mensal

**Exercício:** Simular falha de BD
1. Parar PostgreSQL
2. Tentar operar sistema (deve falhar gracefulmente)
3. Restaurar backup
4. Verificar tempo de recuperação
5. Documentar melhorias

### 7.2 Simulação Trimestral

**Exercício:** Simular falha completa de VPS
1. Desligar VPS de produção
2. Recuperar em novo VPS
3. Medir RTO real vs. objetivo
4. Identificar gaps no processo

---

## 8. DOCUMENTAÇÃO CRÍTICA

Documentos que devem estar disponíveis off-line (impressos ou em USB):
- [ ] Contactos de emergência da equipa
- [ ] Credenciais de acesso a todos os serviços (em envelope selado)
- [ ] Passo a passo de recovery para cada cenário
- [ ] Lista de fornecedores com contactos de suporte
- [ ] Diagrama de arquitetura atual
- [ ] Inventário de todos os ativos (domínios, IPs, etc.)

---

## 9. CHECKLIST DE PREPARAÇÃO

- [ ] Backups automatizados configurados e testados
- [ ] Processo de restore documentado e testado
- [ ] Contactos de emergência atualizados
- [ ] Seguro de cibersegurança contratado (opcional mas recomendado)
- [ ] Documentação crítica off-site
- [ ] DRills realizados nos últimos 3 meses
- [ ] Monitorização de backups funcionando
- [ ] Alertas de falha de backup configurados

---

## 10. LINKS CRUZADOS

- [[13_Infrastructure/INDEX]] ← Secção mãe
- [[POSTGRES_CONFIG]] → Configuração e backup de BD
- [[26_Runbooks/INDEX]] → Runbooks de recuperação