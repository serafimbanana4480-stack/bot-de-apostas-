# 28_Failure_Scenarios — INDEX

**ID:** `SEC-28` | **Fase:** Todas | **Owner:** Risk Manager + Operations Lead | **Status:** #status/active

---

## 1. OBJETIVO

Documentar cenários de falha possíveis e planos de recovery para cada um. Failure scenarios permitem que a equipa antecipe problemas e tenha planos de ação prontos, reduzindo tempo de recovery e minimizando impacto.

---

## 2. NOTAS FUNDAMENTAIS

- [[FS-001_VPS_DOWNTIME]] — VPS fica completamente offline
- [[FS-002_DATABASE_CORRUPTION]] — PostgreSQL database corruption
- [[FS-003_MODEL_DEGRADATION]] — Modelo degrada performance abruptamente
- [[FS-004_API_RATE_LIMIT]] — APIs externas bloqueiam por rate limit
- [[FS-005_TELEGRAM_BOT_BAN]] — Telegram Bot é banido
- [[FS-006_BETFAIR_ACCOUNT_LIMITED]] — Betfair limita conta
- [[FS-007_SECURITY_BREACH]] — Sistema é comprometido
- [[FS-008_DATA_LOSS]] — Perda de dados crítica
- [[FS-009_CASCADING_FAILURE]] — Falha em cascata entre serviços
- [[FS-010_HUMAN_ERROR]] — Erro humano causa perda

---

## 3. CENÁRIOS DE FALHA CRÍTICOS

### FS-001: VPS Fica Completamente Offline
**Probabilidade:** Baixa (1-5% por ano)
**Impacto:** CRÍTICO (sistema 100% indisponível)
**RTO (Recovery Time Objective):** 4 horas
**RPO (Recovery Point Objective):** 24 horas (dados)

**Cenário:**
- VPS provider tem outage de datacenter
- Hardware failure no VPS
- VPS é deletado acidentalmente
- Provider bloqueia conta por suspeita de fraude

**Impacto:**
- Sistema 100% indisponível
- Apostas não podem ser executadas
- Subscritores não recebem sinais
- Potencial perda de dados não backuped

**Plano de Recovery:**

**Fase 1: Diagnóstico (0-30min)**
1. Tentar acessar VPS via SSH
2. Verificar status no painel do provider (Hetzner, AWS, etc.)
3. Verificar se outage é reportado no status page do provider
4. Tentar ping/IP para verificar se é network issue local

**Fase 2: Mitigação Imediata (30min-2h)**
1. Se VPS permanently down:
   - Provisionar novo VPS em provider diferente (redundância geográfica)
   - Restaurar backup mais recente (< 24h)
   - Re-deploy aplicação
2. Se VPS temporariamente down:
   - Aguardar recovery do provider
   - Comunicar com subscritores sobre outage

**Fase 3: Recovery Completo (2-4h)**
1. Verificar integridade de dados restaurados
2. Verificar que todos os serviços estão healthy
3. Executar reconciliação de apostas (se houver gap)
4. Enviar notificação de recovery para subscritores
5. Documentar incidente (postmortem)

**Prevenção:**
- Backups diários automatizados para S3/external storage
- Multi-region deployment (futuro)
- Monitorização de uptime com alertas
- Contrato SLA com VPS provider

---

### FS-002: PostgreSQL Database Corruption
**Probabilidade:** Muito Baixa (< 1% por ano)
**Impacto:** CRÍTICO (perda de dados)
**RTO:** 8 horas
**RPO:** 24 horas

**Cenário:**
- Hardware failure causa corruption
- Bug no PostgreSQL causa corruption
- Ação humana acidental (DROP TABLE)
- Ransomware encryption

**Impacto:**
- Perda de dados históricos
- Sistema incapaz de operar sem dados
- Perda de track record
- Potencial perda de modelo treinado

**Plano de Recovery:**

**Fase 1: Diagnóstico (0-1h)**
1. Tentar conectar ao database
2. Verificar logs do PostgreSQL para identificar corruption
3. Tentar queries simples para verificar extent de corruption
4. Verificar se backup recente está disponível

**Fase 2: Mitigação (1-4h)**
1. Se corruption parcial:
   - Tentar REINDEX DATABASE
   - Tentar pg_dump + restore em novo database
   - Exportar tabelas não-corrompidas
2. Se corruption total:
   - Restaurar backup mais recente
   - Se backup < 24h, aceitar perda de dados
   - Se backup > 24h, considerar recuperação de dados especializada

**Fase 3: Recovery (4-8h)**
1. Verificar integridade de database restaurado
2. Re-executar ingestão de dados para gap (se possível)
3. Re-treinar modelo com dados restaurados
4. Verificar que sistema está operacional
5. Documentar incidente

**Prevenção:**
- Backups diários automatizados (multi-local)
- Backups weekly off-site (S3)
- Teste de restore mensal
- Read replicas para failover (futuro)
- PostgreSQL version upgrades planeadas

---

### FS-003: Modelo Degrada Performance Abruptamente
**Probabilidade:** Média (10-20% por ano)
**Impacto:** HIGH (perda de dinheiro se apostas continuarem)
**RTO:** 24 horas
**RPO:** 0 horas (pausa imediata de apostas)

**Cenário:**
- Drift de dados (distribuição de features mudou)
- Regime change (NBA mudou regras, estilo de jogo)
- Overfitting revelado em produção
- Bug no pipeline de features

**Impacto:**
- CLV cai de positivo para negativo
- Apostas começam a perder dinheiro
- Perda de confiança de subscritores
- Potencial drawdown severo

**Plano de Recovery:**

**Fase 1: Detecção Imediata (0-1h)**
1. Alerta de CLV < 0% por 3 dias consecutivos
2. Alerta de ECE > 0.10 (calibração ruim)
3. Alerta de drift > 0.20 (KS test)
4. Ativar circuit breaker Gamma automaticamente

**Fase 2: Diagnóstico (1-8h)**
1. Analisar features para identificar drift
2. Verificar se mudou regime (playoffs vs regular season)
3. Verificar se há bug no pipeline (features com valores estranhos)
4. Comparar performance vs baseline (mercado)

**Fase 3: Mitigação (8-24h)**
1. Se drift de dados:
   - Re-treinar modelo com dados recentes
   - Atualizar feature engineering para novo regime
2. Se regime change:
   - Treinar modelo específico para novo regime
   - Separar modelos por regime (regular vs playoffs)
3. Se bug no pipeline:
   - Corrigir bug
   - Re-calcular features para período afetado
4. Se overfitting:
   - Re-treinar com mais regularização
   - Reduzir número de features
   - Aumentar embargo period

**Fase 4: Recovery (24-48h)**
1. Validar novo modelo em backtest
2. Deploy em shadow mode (simulação) por 1 semana
3. Se shadow mode CLV > 2%, re-ativar apostas
4. Se shadow mode CLV < 2%, continuar investigação
5. Documentar incidente e lições aprendidas

**Prevenção:**
- Monitorização contínua de CLV, ECE, drift
- Circuit breaker automático para CLV negativo
- Shadow mode obrigatório antes de produção
- Re-treining mensal ou trimestral
- Feature drift detection automatizado

---

### FS-004: APIs Externas Bloqueiam por Rate Limit
**Probabilidade:** Média (20-30% por ano)
**Impacto:** HIGH (sistema incapaz de obter dados)
**RTO:** 48 horas
**RPO:** 24 horas

**Cenário:**
- NBA API bloqueia IP por excesso de requests
- Basketball-Reference bloqueia IP por scraping
- Betfair API bloqueia por excesso de calls
- The Odds API bloqueia por limite de plano

**Impacto:**
- Sistema não consegue obter dados atualizados
- Modelos não podem gerar previsões
- Apostas não podem ser executadas
- Sistema fica parado até resolução

**Plano de Recovery:**

**Fase 1: Detecção (0-1h)**
1. Alerta de dados não atualizando (> 2h)
2. Ver logs para identificar erro 429 (rate limit)
3. Identificar qual API está bloqueada

**Fase 2: Mitigação Imediata (1-4h)**
1. Se NBA API bloqueada:
   - Reduzir frequência de requests (2h → 4h)
   - Usar proxy/VPN para mudar IP
   - Fallback para Basketball-Reference (scraping)
2. Se Basketball-Reference bloqueada:
   - Usar user-agent rotation
   - Adicionar delays entre requests
   - Fallback para ESPN API
3. Se Betfair API bloqueada:
   - Reduzir frequência de calls
   - Verificar se é limit de plano (upgrade se necessário)
   - Fallback para execução manual temporariamente

**Fase 3: Recovery (4-48h)**
1. Implementar rate limiting próprio no código
2. Implementar caching agressivo (Redis)
3. Configurar proxy rotation
4. Se necessário, pagar por plano premium de API
5. Documentar incidente

**Prevenção:**
- Rate limiting próprio no código
- Caching agressivo (Redis)
- User-agent rotation para scraping
- Proxy rotation
- Monitorização de rate limit usage
- Fallback para fontes alternativas

---

### FS-005: Telegram Bot é Banido
**Probabilidade:** Baixa (5-10% por ano)
**Impacto:** MEDIUM (sinais não podem ser distribuídos)
**RTO:** 24 horas
**RPO:** 0 horas

**Cenário:**
- Telegram ban bot por spam
- Telegram ban bot por violação de ToS
- Telegram bloqueia conta por suspeita de fraude

**Impacto:**
- Subscritores não recebem sinais
- Canal de comunicação principal perdido
- Perda de receita se subscritores cancelarem

**Plano de Recovery:**

**Fase 1: Detecção (0-1h)**
1. Alerta de bot não responding
2. Tentar enviar mensagem manual
3. Verificar se bot está banido no Telegram

**Fase 2: Mitigação Imediata (1-4h)**
1. Criar novo bot via @BotFather
2. Migrar todos os subscritores para novo bot
3. Enviar mensagem para grupo de subscritores sobre mudança
4. Atualizar integração com novo bot token

**Fase 3: Recovery (4-24h)**
1. Verificar que novo bot está funcionando
2. Verificar que todos os subscritores migraram
3. Apelar ban do bot antigo (se possível)
4. Documentar incidente

**Prevenção:**
- Seguir ToS do Telegram estritamente
- Não enviar spam
- Ter canal de comunicação alternativo (email)
- Back-up de lista de subscritores offline

---

### FS-006: Betfair Limita Conta
**Probabilidade:** Média (15-25% por ano)
**Impacto:** HIGH (execução de apostas limitada)
**RTO:** 1 semana
**RPO:** 0 horas

**Cenário:**
- Betfair limita stakes por "winning too much"
- Betfair fecha conta por suspeita de arbitragem
- Betfair bloqueia API por uso excessivo

**Impacto:**
- Não é possível executar apostas em Betfair
- Sistema precisa de alternativa
- Perda de receita se não houver alternativa

**Plano de Recovery:**

**Fase 1: Detecção (0-1h)**
1. Alerta de apostas rejeitadas
2. Verificar mensagem de erro da Betfair API
3. Confirmar se conta foi limitada

**Fase 2: Mitigação Imediata (1-24h)**
1. Se limitado temporariamente:
   - Reduzir stakes para permanecer dentro de limites
   - Diversificar para outras casas (Pinnacle, SBK)
2. Se conta fechada:
   - Abrir conta em outra exchange (Betfair outra jurisdição)
   - Abrir conta em casas tradicionais (Pinnacle, SBK)
   - Contactar Betfair para apelar

**Fase 3: Recovery (1 semana+)**
1. Implementar multi-casa desde o início
2. Diversificar execução entre múltiplas casas
3. Reduzir stakes em cada casa individualmente
4. Documentar incidente

**Prevenção:**
- Multi-casa desde o início (não depender só de Betfair)
- Diversificar stakes entre casas
- Não apostar valores que chamam atenção
- Manter bom relacionamento com casas

---

### FS-007: Sistema é Comprometido (Security Breach)
**Probabilidade:** Baixa (1-5% por ano)
**Impacto:** CRÍTICO (perda de dados, reputação, legal)
**RTO:** 48 horas
**RPO:** 0 horas

**Cenário:**
- Hacker obtém acesso ao VPS
- Hacker obtém acesso à database
- Hacker obtém secrets (API keys, passwords)
- Hacker injeta código malicioso

**Impacto:**
- Perda de dados sensíveis (subscritores, apostas)
- Perda de reputação
- Responsabilidade legal (GDPR)
- Potencial blackmail

**Plano de Recovery:**

**Fase 1: Detecção (0-1h)**
1. Alerta de atividade suspeita (login de IP desconhecido)
2. Alerta de tráfego anormal
3. Alerta de alterações não autorizadas
4. Verificar logs para identificar breach

**Fase 2: Mitigação Imediata (1-4h)**
1. **ISOLAR SISTEMA:**
   - Desligar VPS imediatamente
   - Mudar todas as passwords
   - Revogar todas as API keys
   - Revogar todos os tokens de acesso
2. **ASSESSAR DANO:**
   - Verificar quais dados foram acessados
   - Verificar se houve exfiltração de dados
   - Verificar se código foi alterado
3. **NOTIFICAR:**
   - Notificar subscritores se dados pessoais foram comprometidos
   - Notificar autoridades se necessário (GDPR)
   - Notificar seguradora se tiver cyber insurance

**Fase 3: Recovery (4-48h)**
1. Limpar VPS (rebuild from scratch)
2. Restaurar backup de database (pré-breach)
3. Re-deploy aplicação com novos secrets
4. Implementar security hardening adicional
5. Documentar incidente (postmortem)

**Prevenção:**
- Secrets management (HashiCorp Vault, AWS Secrets Manager)
- Autenticação 2FA para todos os acessos
- Firewall restritivo (UFW)
- Monitorização de logs de segurança
- Penetration testing anual
- Security audits

---

### FS-008: Perda de Dados Crítica
**Probabilidade:** Baixa (1-5% por ano)
**Impacto:** CRÍTICO (perda de dados históricos)
**RTO:** 1 semana
**RPO:** Variável

**Cenário:**
- Backup failure + disk failure simultâneo
- Ransomware encryption
- Deletion acidental de dados críticos
- Corruption não detectada por longo período

**Impacto:**
- Perda de dados históricos (track record)
- Modelo precisa ser re-treinado do zero
- Perda de confiança de subscritores

**Plano de Recovery:**

**Fase 1: Detecção (0-1h)**
1. Alerta de backup failure
2. Verificar integridade de dados
3. Identificar extent de perda

**Fase 2: Mitigação (1-24h)**
1. Se backup parcial disponível:
   - Restaurar backup parcial
   - Re-ingestar dados para gap (se possível)
2. Se nenhum backup disponível:
   - Tentar recuperação de dados especializada
   - Re-ingestar todas as dados de fontes externas (NBA API, etc.)
   - Aceitar perda de dados não recuperáveis

**Fase 3: Recovery (1 semana+)**
1. Re-treinar modelo com dados restaurados
2. Re-validar modelo em backtest
3. Comunicar com subscritores sobre perda
4. Documentar incidente

**Prevenção:**
- Backups multi-local (S3 + local)
- Backups incrementais + full
- Teste de restore mensal
- Immutable backups (não podem ser deletados/encryptados)
- Ransomware protection

---

## 4. BACKLOG DE FAILURE SCENARIOS

- [ ] FS-009: Cascading Failure (falha em cascata entre serviços)
- [ ] FS-010: Human Error (erro humano causa perda)
- [ ] FS-011: DNS Failure (domínio não resolve)
- [ ] FS-012: SSL Certificate Expiry
- [ ] FS-013: Payment Processor Failure (Stripe/Paddle down)
- [ ] FS-014: Regulatory Change (SRIJ muda regras)
- [ ] FS-015: Natural Disaster (datacenter destruído)

---

## 5. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[26_Runbooks/INDEX]] → Runbooks para incidentes específicos
- [[27_Postmortems/INDEX]] → Análise pós-incidente
- [[34_Security/INDEX]] → Segurança e prevenção
