# INCIDENT_RESPONSE — Resposta a Incidentes de Segurança

**ID:** `SEC-005` | **Fase:** #phase/1 | **Owner:** DevOps Engineer | **Status:** #status/pending

---

## 1. VISÃO GERAL

Este documento define o plano de resposta a incidentes de segurança, incluindo procedimentos de deteção, contenção, erradicação, recuperação e lições aprendidas. O objetivo é minimizar o impacto de incidentes e restaurar operações normais o mais rápido possível.

---

## 2. CLASSIFICAÇÃO DE INCIDENTES

### 2.1 Níveis de Severidade

| Nível | Descrição | Exemplos | Tempo de Resposta |
|-------|-----------|----------|-------------------|
| **P1 - Crítico** | Sistema comprometido, perda de dados, operação parada | Ransomware, exfiltração de dados, root access comprometido | < 15 minutos |
| **P2 - Alto** | Acesso não autorizado, serviço degradado | SQL injection bem-sucedido, DDoS ativo, token leak | < 1 hora |
| **P3 - Médio** | Tentativa de intrusão, anomalia detetada | Brute force, scan de vulnerabilidades, config não autorizada | < 4 horas |
| **P4 - Baixo** | Evento de segurança sem impacto | Falha de autenticação isolada, alerta falso positivo | < 24 horas |

### 2.2 Critérios de Escalonamento

- **P1:** Notificar imediatamente todas as equipas, parar operações se necessário
- **P2:** Notificar DevOps + Security Lead, considerar paragem parcial
- **P3:** Notificar DevOps, investigar durante horário laboral
- **P4:** Log no backlog, investigar quando possível

---

## 3. EQUIPA DE RESPOSTA

### 3.1 Roles e Responsabilidades

| Role | Responsabilidades | 24/7 |
|------|-------------------|------|
| **Incident Commander** | Coordenação, decisões, comunicação | ✅ |
| **Security Lead** | Análise forense, contenção técnica | ✅ |
| **DevOps Engineer** | Implementação de fixes, rollback | ✅ |
| **Operations Lead** | Impacto no negócio, continuidade | ✅ |
| **Legal/Compliance** | Requisitos legais, notificações | ❌ |
| **Communications** | Comunicação externa, stakeholders | ❌ |

### 3.2 Canais de Comunicação

- **Urgente (P1/P2):** PagerDuty + Telegram emergency channel
- **Normal (P3/P4):** Slack #security-incidents + email
- **Post-incident:** Jira ticket + documentação

---

## 4. PROCESSO DE RESPOSTA (SANS PICERL)

### 4.1 Preparation (Preparação)

**Objetivo:** Estar preparado para responder rapidamente.

**Checklist:**
- [ ] Playbooks atualizados para todos os cenários
- [ ] Contactos de emergência atualizados
- [ ] Ferramentas de forensics instaladas e testadas
- [ ] Backups verificados e acessíveis
- [ ] Comunicados pré-preparados (templates)
- [ ] Treinamento trimestral da equipa

**Ferramentas:**
- Forensics: `autopsy`, `volatility`, `wireshark`
- Análise de logs: ELK Stack, Splunk
- Comunicação: PagerDuty, Slack, Telegram
- Documentação: Confluence, Jira

---

### 4.2 Identification (Identificação)

**Objetivo:** Determinar se um incidente ocorreu e classificá-lo.

**Sinais de Compromisso (IOCs):**
- Acesso de IPs desconhecidos
- Tentativas de autenticação falhadas em massa
- Queries SQL suspeitas
- Aumento de tráfego anómalo
- Alterações de configuração não autorizadas
- Processos desconhecidos em execução
- Ficheiros modificados em diretórios críticos

**Script de Detecção:**
```bash
#!/bin/bash
# detect_indicators.sh

echo "=== Checking for IOCs ==="

# 1. Failed auth attempts
echo "Failed auth attempts (last hour):"
journalctl -u ssh --since "1 hour ago" | grep "Failed password" | wc -l

# 2. Unknown IPs accessing API
echo "Unique IPs accessing API (last hour):"
tail -n 10000 /var/log/valuebetting/app.log | grep -oP 'ip_address":"\K[0-9.]+' | sort -u

# 3. Suspicious processes
echo "Suspicious processes:"
ps aux | grep -E '(nc|netcat|ncat|wget|curl|bash.*-i)' | grep -v grep

# 4. Modified system files
echo "Modified system files (last 24h):"
find /etc /usr/bin /usr/sbin -mtime -1 -type f

# 5. Network connections
echo "Active network connections:"
ss -tunlp
```

**Decisão:**
- Se IOCs confirmados → Escalonar para nível apropriado
- Se incerto → Continuar monitorização, aumentar vigilância

---

### 4.3 Containment (Contenção)

**Objetivo:** Limitar o dano e prevenir propagação.

**Estratégias por Nível:**

**P1 - Crítico:**
```bash
# 1. Isolar sistema (desconectar da rede)
sudo ifdown eth0

# 2. Parar todos os serviços
sudo systemctl stop valuebetting
sudo systemctl stop postgresql
sudo systemctl stop redis

# 3. Snapshot da VM (para forensics)
# (via cloud provider console)

# 4. Mudar todas as credenciais
# (via process out-of-band)
```

**P2 - Alto:**
```bash
# 1. Bloquear IPs maliciosos
sudo ufw deny from 203.0.113.50

# 2. Revogar todos os tokens
# (via script de revogação)

# 3. Ativar modo de manutenção
# (apenas leitura, sem apostas)

# 4. Aumentar logging
# (debug level + captura de pacotes)
```

**P3 - Médio:**
```bash
# 1. Bloquear IP específico
sudo ufw deny from <ip>

# 2. Forçar logout de utilizadores suspeitos
# (via token blacklist)

# 3. Monitorização aumentada
# (alertas em tempo real)
```

---

### 4.4 Eradication (Erradicação)

**Objetivo:** Remover a causa raiz do incidente.

**Passos:**
1. **Identificar root cause:**
   - Análise de logs
   - Forensics de sistema
   - Revisão de código (se vulnerabilidade)

2. **Remover ameaça:**
   - Eliminar malware/backdoors
   - Patch de vulnerabilidades
   - Remover contas comprometidas

3. **Verificar remoção:**
   - Scan completo do sistema
   - Análise de integridade de ficheiros
   - Testar que a ameaça está eliminada

**Exemplo - Remoção de Backdoor:**
```bash
# 1. Identificar ficheiro suspeito
find / -name "*.sh" -mtime -1 -perm +111

# 2. Analisar conteúdo
cat /tmp/.hidden/script.sh

# 3. Remover (após backup para forensics)
cp /tmp/.hidden/script.sh /forensics/evidence_001.sh
rm /tmp/.hidden/script.sh

# 4. Verificar serviços que o executavam
systemctl list-units --type=service | grep suspicious

# 5. Desativar serviço
systemctl disable suspicious-service
systemctl stop suspicious-service
```

---

### 4.5 Recovery (Recuperação)

**Objetivo:** Restaurar operações normais de forma segura.

**Fases:**

**Fase 1 - Preparação:**
- [ ] Root cause eliminada e verificada
- [ ] Sistema limpo e seguro
- [ ] Backups verificados
- [ ] Plano de rollback definido

**Fase 2 - Restauração Gradual:**
```bash
# 1. Restaurar sistema de backup limpo
# (se necessário)

# 2. Atualizar sistema com patches
sudo apt update && sudo apt upgrade -y

# 3. Restaurar configurações (verificadas)
# (de repo git com revisão)

# 4. Rotacionar todas as credenciais
# (secrets, tokens, passwords)

# 5. Iniciar serviços em modo de teste
sudo systemctl start postgresql
sudo systemctl start redis
sudo systemctl start valuebetting

# 6. Verificar logs para anomalias
tail -f /var/log/valuebetting/app.log
```

**Fase 3 - Monitorização Intensiva:**
- Monitorizar todos os logs em tempo real
- Alertas reduzidos para 5 minutos
- Revisão manual de cada operação crítica
- Pronto para rollback se detetar anomalias

**Fase 4 - Retorno à Normalidade:**
- Após 24h sem anomalias
- Restaurar níveis normais de alertas
- Documentar incidente completo
- Atualizar playbooks se necessário

---

### 4.6 Lessons Learned (Lição Aprendida)

**Objetivo:** Melhorar preparação para futuros incidentes.

**Timeline:**
- **24h após:** Draft inicial do relatório
- **72h após:** Relatório completo com ações
- **1 semana após:** Revisão com equipa
- **1 mês após:** Verificação de implementação de ações

**Template de Relatório:**

```markdown
# Incident Report [ID]

## Resumo Executivo
- Data/Hora: [timestamp]
- Duração: [X horas]
- Severidade: [P1/P2/P3/P4]
- Impacto: [descrição]
- Status: [resolvido/em investigação]

## Timeline
| Timestamp | Evento | Responsável |
|-----------|--------|-------------|
| 2024-01-15 14:30 | Alerta detetado | Sistema |
| 2024-01-15 14:35 | Incidente declarado | Incident Commander |
| 2024-01-15 14:40 | Contenção iniciada | Security Lead |
| 2024-01-15 15:00 | Root cause identificada | Security Lead |
| 2024-01-15 15:30 | Erradicação completa | DevOps |
| 2024-01-15 16:00 | Recuperação iniciada | DevOps |
| 2024-01-15 17:00 | Operações restauradas | Operations |

## Root Cause
[Descrição detalhada da causa]

## Impacto
- Financeiro: [€X]
- Operacional: [X horas de downtime]
- Reputacional: [descrição]
- Compliance: [notificações necessárias?]

## Ações Imediatas
- [ ] Ação 1
- [ ] Ação 2

## Ações de Longo Prazo
- [ ] Melhoria 1 (responsável, deadline)
- [ ] Melhoria 2 (responsável, deadline)

## Lições Aprendidas
- O que funcionou bem
- O que pode ser melhorado
- Recursos que faltaram

## Anexos
- Logs relevantes
- Screenshots
- Comunicados enviados
```

---

## 5. PLAYBOOKS ESPECÍFICOS

### 5.1 Ransomware

**Sinais:** Ficheiros encriptados, ransom note, lentidão extrema

**Resposta:**
1. **IMEDIATO:** Desconectar da rede (não desligar!)
2. Isolar sistemas afetados
3. **NÃO pagar resgate** (incentiva ataques)
4. Verificar backups (estão limpos?)
5. Restaurar de backup se possível
6. Encontrar variant decryptor (No More Ransom project)
7. Reportar às autoridades

**Prevenção:**
- Backups offline (air-gapped)
- Antivirus/EDR
- Filter email attachments
- User awareness training

---

### 5.2 SQL Injection

**Sinais:** Queries suspeitas nos logs, erros de SQL inesperados

**Resposta:**
1. Identificar query vulnerável
2. Bloquear IP de origem
3. Patch do código (parameterized queries)
4. Verificar se dados foram exfiltrados
5. Rotacionar credenciais de BD
6. Review de todo o código para vulnerabilidades similares

**Prevenção:**
- Parameterized queries obrigatórias
- Input validation
- WAF rules
- Code review obrigatório

---

### 5.3 Credential Leak

**Sinais:** Tokens em logs, commits acidentais, phishing bem-sucedido

**Resposta:**
1. Revogar imediatamente todas as credenciais
2. Rotacionar secrets
3. Revogar sessões ativas
4. Verificar audit logs para acessos suspeitos
5. Forçar re-autenticação de todos os utilizadores
6. Investigar fonte do leak

**Prevenção:**
- No hardcoding de secrets
- Git-secrets pre-commit hooks
- MFA obrigatório
- Phishing training

---

### 5.4 DDoS

**Sinais:** Tráfego massivo, latência extrema, 503 errors

**Resposta:**
1. Ativar Cloudflare/CDN se não estiver ativo
2. Rate limiting agressivo
3. Bloquear IPs de origem (Geo-blocking se necessário)
4. Escalar recursos (auto-scaling)
5. Contactar ISP/Cloud provider
6. Modo degradado se necessário

**Prevenção:**
- Cloudflare/CDN sempre ativo
- Rate limiting
- Auto-scaling
- DDoS protection service

---

## 6. COMUNICAÇÃO

### 6.1 Interna

**P1/P2:** Imediato via PagerDuty + Telegram
**P3/P4:** Slack + email em 1 hora

**Template:**
```
🚨 SECURITY INCIDENT - P2

Type: SQL Injection detected
Status: Containment in progress
Impact: API temporarily in read-only mode
Next update: 30 minutes

Incident Commander: @name
```

### 6.2 Externa

**Stakeholders:** Apenas se impacto crítico em operações
**Reguladores:** Se GDPR/compliance afetado (72h máximo)
**Público:** Apenas se leak de dados públicos

**Template:**
```
STATEMENT: Security Incident

On [date], we detected a security incident affecting [system].
We immediately took steps to contain the incident and protect user data.
[Impact assessment]
[Steps taken]
[Next steps]

We are committed to transparency and will provide updates as available.
```

---

## 7. BACKLOG

- [ ] Criar playbooks para todos os cenários
- [ ] Configurar PagerDuty para alertas P1/P2
- [ ] Implementar auto-containment para ataques óbvios
- [ ] Treinamento trimestral da equipa
- [ ] Contratar serviço de DDoS protection
- [ ] Implementar EDR (Endpoint Detection and Response)

---

## 8. LINKS CRUZADOS

- [[34_Security/INDEX]] ← Secão mãe
- [[34_Security/AUDIT_LOGGING]] → Logs para forensics
- [[34_Security/ACCESS_CONTROL]] → Revogação de acessos
- [[12_DevOps/INDEX]] → Monitorização e alertas