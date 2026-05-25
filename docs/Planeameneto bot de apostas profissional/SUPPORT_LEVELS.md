# SUPPORT_LEVELS — Níveis de Suporte

**ID:** `ORG-003` | **Fase:** #phase/1 | **Owner:** Project Manager | **Status:** #status/active

---

## 1. OBJETIVO

Definir níveis de suporte, responsabilidades, SLAs e procedimentos de escalonamento para garantir resposta rápida e eficaz a incidentes e issues operacionais.

---

## 2. NÍVEIS DE SUPORTE

### L1 - Operations (Primeira Linha)

**Responsável:** Operations Engineer

**Responsabilidades:**
- Monitorização diária do sistema (dashboard, logs, alertas)
- Resolução de issues operacionais simples
- Triagem inicial de incidentes
- Escalonamento para L2 quando necessário
- Comunicação com utilizadores finais

**Competências:**
- Conhecimento do sistema de execução
- Capacidade de ler logs e identificar erros comuns
- Habilidades de comunicação
- Acesso a sistemas de monitorização

**Horário de Disponibilidade:**
- Dias úteis: 09:00 - 18:00 UTC
- Fins de semana: Em rotação (on-call)
- Tempo de resposta: < 15 minutos (crítico), < 2 horas (normal)

---

### L2 - Quant Engineer (Segunda Linha)

**Responsável:** Quant Engineer / MLOps Engineer

**Responsabilidades:**
- Debugging de modelos e features
- Análise de performance de predições
- Investigação de drift detection
- Ajuste de parâmetros operacionais
- Escalonamento para L3 para problemas complexos
- Documentação de incidentes técnicos

**Competências:**
- Conhecimento profundo de ML e estatística
- Capacidade de analisar dados e métricas
- Experiência com debugging de modelos em produção
- Conhecimento de feature engineering

**Horário de Disponibilidade:**
- Dias úteis: 09:00 - 18:00 UTC
- On-call para incidentes críticos
- Tempo de resposta: < 1 hora (crítico), < 4 horas (normal)

---

### L3 - Architect (Terceira Linha)

**Responsável:** System Architect / Tech Lead

**Responsabilidades:**
- Arquitetura e design de soluções
- Resolução de problemas complexos e sistémicos
- Decisões técnicas estratégicas
- Planeamento de mudanças de arquitetura
- Code review crítico
- Gestão de crises técnicas

**Competências:**
- Visão sistémica completa
- Experiência em arquitetura de sistemas
- Capacidade de tomar decisões sob pressão
- Conhecimento de todas as camadas do sistema

**Horário de Disponibilidade:**
- Sempre disponível para incidentes críticos
- Tempo de resposta: < 30 minutos (crítico)

---

## 3. MATRIZ DE ESCALONAMENTO

| Tipo de Issue | Severidade | L1 | L2 | L3 | Tempo Máximo Resolução |
|---------------|------------|----|----|----|------------------------|
| Sistema offline | CRÍTICA | ✅ | ✅ | ✅ | 1 hora |
| Alerta de performance | ALTA | ✅ | ✅ | | 4 horas |
| Erro de modelo | ALTA | | ✅ | ✅ | 8 horas |
| Drift detection | MÉDIA | | ✅ | | 24 horas |
| Mudança de arquitetura | BAIXA | | | ✅ | 1 semana |
| Melhoria de UX | BAIXA | ✅ | | | 2 semanas |
| Bug menor | MÉDIA | ✅ | | | 3 dias |

---

## 4. PROCEDIMENTO DE ESCALONAMENTO

### 4.1 Fluxo de Escalonamento

```
┌─────────────┐
│  Incidente  │
│  Detetado   │
└──────┬──────┘
       ↓
┌─────────────┐
│  L1 Tenta    │
│  Resolver   │
└──────┬──────┘
       ↓
   Resolvido?
    ↙      ↘
   SIM       NÃO
    ↓         ↓
  Fim     Escalar L2
           ↓
      ┌─────────────┐
      │  L2 Tenta    │
      │  Resolver   │
      └──────┬──────┘
             ↓
         Resolvido?
          ↙      ↘
         SIM       NÃO
          ↓         ↓
        Fim     Escalar L3
                 ↓
            ┌─────────────┐
            │  L3 Resolve │
            └─────────────┘
```

### 4.2 Critérios de Escalonamento

**Escalonar para L2 se:**
- L1 não consegue resolver em 30 minutos (crítico) ou 2 horas (normal)
- Issue requer conhecimento técnico de ML/estatística
- Issue envolve análise de dados complexa
- Issue afeta performance do modelo

**Escalonar para L3 se:**
- L2 não consegue resolver em 1 hora (crítico) ou 4 horas (normal)
- Issue requer mudança de arquitetura
- Issue afeta múltiplos sistemas
- Issue tem impacto estratégico

---

## 5. SLAs (Service Level Agreements)

### 5.1 Tempo de Resposta

| Nível | Crítico | Alta | Média | Baixa |
|-------|---------|------|-------|-------|
| L1 | 15 min | 30 min | 2 horas | 4 horas |
| L2 | 1 hora | 2 horas | 4 horas | 8 horas |
| L3 | 30 min | 1 hora | 4 horas | 24 horas |

### 5.2 Tempo de Resolução

| Nível | Crítico | Alta | Média | Baixa |
|-------|---------|------|-------|-------|
| L1 | 1 hora | 4 horas | 1 dia | 3 dias |
| L2 | 4 horas | 8 horas | 1 dia | 3 dias |
| L3 | 2 horas | 8 horas | 2 dias | 1 semana |

---

## 6. COMUNICAÇÃO

### 6.1 Canais de Comunicação

- **Slack #incidents:** Para coordenação em tempo real
- **Telegram alerts:** Para notificações críticas
- **Email:** Para documentação e follow-up
- **Jira:** Para tracking de incidentes

### 6.2 Templates de Mensagem

**Incidente Crítico:**
```
🚨 CRITICAL INCIDENT DETECTED

Issue: [Breve descrição]
Severity: CRITICAL
Impact: [Descrição do impacto]
Affected Systems: [Lista]
Timestamp: [ISO timestamp]
Assigned to: [Nome]

Next update: 15 minutos
```

**Escalonamento:**
```
⬆️ ESCALATING TO L2

Issue: [ID]
L1 attempted: [Descrição da tentativa]
Reason for escalation: [Motivo]
Assigned to: [Nome L2]
Timestamp: [ISO timestamp]
```

---

## 7. DOCUMENTAÇÃO

### 7.1 Registo de Incidentes

Todos os incidentes devem ser documentados em Jira com:
- Descrição detalhada
- Severidade
- Timeline de resolução
- Causa raiz
- Ações preventivas
- Lições aprendidas

### 7.2 Base de Conhecimento

Soluções comuns devem ser documentadas:
- Procedures padrão
- Troubleshooting guides
- Playbooks para incidentes frequentes
- FAQs

---

## 8. TREINO

### 8.1 Treino Inicial

- **L1:** 1 semana de onboarding com L2/L3
- **L2:** 2 semanas de onboarding com L3
- **L3:** N/A (experiência prévia)

### 8.2 Treino Contínuo

- **Monthly:** Review de incidentes do mês anterior
- **Quarterly:** Drills de resposta a incidentes
- **Annually:** Treino completo de procedimentos

---

## 9. MÉTRICAS DE SUCESSO

- **MTTR (Mean Time To Resolution):** < 4 horas (média)
- **MTTD (Mean Time To Detect):** < 15 minutos
- **First Contact Resolution:** > 60% (L1)
- **Customer Satisfaction:** > 4.5/5
- **SLA Compliance:** > 95%

---

## 10. LINKS CRUZADOS

- [[01_Vision_And_Strategy/INDEX]] ← Visão geral
- [[SUPPORT_TIERS]] → Detalhes de tiers
- [[33_Alerting/INDEX]] → Sistema de alertas
- [[25_SOPs/INDEX]] → Procedimentos operacionais
- [[TEMPLATE_INCIDENTE]] → Template de reporte de incidente
