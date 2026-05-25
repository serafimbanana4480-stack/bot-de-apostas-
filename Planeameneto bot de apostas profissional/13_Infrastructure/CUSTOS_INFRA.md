# CUSTOS_INFRA — Tracking de Custos de Infraestrutura

**ID:** `INF-004` | **Fase:** #phase/1-15 | **Owner:** DevOps Engineer + Financeiro | **Status:** #status/active

---

## 1. OBJETIVO

Rastrear todos os custos de infraestrutura mensalmente, projetar custos futuros, e garantir que o modelo de negócio seja sustentável. Custos devem ser < 20% da receita na Fase 6+.

---

## 2. CUSTOS MVP (FASES 1-6)

### 2.1 Custos Fixos Mensais

| Serviço | Provider | Especificação | Custo Mensal | Notas |
|---------|----------|---------------|--------------|-------|
| VPS | Hetzner CPX21 | 4 vCPU, 8GB RAM, 100GB SSD | 50-60€ | Frankfurt |
| Domínio | Namecheap | .com ou .pt | 10-15€/ano | ~1€/mês |
| SSL Certificate | Let's Encrypt | Gratuito | 0€ | Auto-renovação |
| **TOTAL FIXO** | | | **~55€/mês** | |

### 2.2 Custos Variáveis (Uso)

| Serviço | Custo Unitário | Uso Mensal Estimado | Custo Mensal |
|---------|---------------|---------------------|--------------|
| API de Odds | Betfair (gratuito) | 0€ | 0€ |
| API de NBA | nba_api (gratuito) | 0€ | 0€ |
| Email (SendGrid) | 1000 emails grátis | ~500 emails | 0€ |
| Telegram Bot | python-telegram-bot | 0€ | 0€ |
| **TOTAL VARIÁVEL** | | | **0€** | |

### 2.3 Custos de Capital (One-time)

| Item | Custo | Amortização | Custo Mensal |
|------|-------|-------------|--------------|
| Setup inicial (configuração) | 40h @ 25€/h = 1000€ | 12 meses | ~83€ |
| Desenvolvimento MVP | 200h @ 25€/h = 5000€ | 12 meses | ~417€ |
| **TOTAL CAPITAL** | 6000€ | | **~500€/mês** |

**Custo Total MVP (Fases 1-6):** ~55€/mês (opex) + ~500€/mês (capex amortizado) = **~555€/mês**

---

## 3. CUSTOS FASE 7-9 (AUTOMAÇÃO)

### 3.1 Escalas Previstas

| Serviço | Escala | Custo Mensal | Justificação |
|---------|--------|--------------|--------------|
| VPS | Upgrade CPX31 (8 vCPU, 16GB RAM) | 100-120€ | Maior carga de ML |
| PostgreSQL | Managed (RDS ou similar) | 50-80€ | Backup automático, HA |
| Redis | Managed (ElastiCache) | 30-50€ | Escala horizontal |
| Monitoring | Grafana Cloud | 20-30€ | Dashboards avançados |
| **TOTAL FASE 7-9** | | **200-280€/mês** | |

---

## 4. CUSTOS FASE 10+ (ENTERPRISE)

### 4.1 Escala Enterprise

| Serviço | Escala | Custo Mensal | Justificação |
|---------|--------|--------------|--------------|
| VPS Cluster | 3 instâncias (load balanced) | 300-400€ | Alta disponibilidade |
| Managed PostgreSQL | Multi-AZ | 150-200€ | Disaster recovery |
| Managed Redis | Cluster | 100-150€ | Escala horizontal |
| S3 Storage | 500GB para backups | 20-30€ | Retenção longa |
| CDN (Cloudflare) | CDN + DDoS protection | 20€/mês | Performance global |
| CI/CD (GitHub Actions) | 2000 minutos/mês | 0-20€ | Dependendo do uso |
| **TOTAL FASE 10+** | | **590-820€/mês** | |

---

## 5. ANÁLISE DE SUSTENTABILIDADE

### 5.1 Receita vs Custos por Fase

| Fase | Receita Estimada | Custos Operacionais | Margem | Status |
|------|------------------|---------------------|--------|--------|
| Fase 1-2 | 0€ | 55€/mês | -55€/mês | Investimento |
| Fase 3 | 0€ | 55€/mês | -55€/mês | Investimento |
| Fase 4 | 0€ | 55€/mês | -55€/mês | Investimento |
| Fase 5 | 750-1500€ (25-50 subs) | 55€/mês | 700-1445€/mês | Lucrativo |
| Fase 6 | 1500-3000€ (50-100 subs) | 55€/mês | 1445-2945€/mês | Muito lucrativo |
| Fase 7-9 | 3000-6000€ | 200-280€/mês | 2720-5720€/mês | Lucrativo |
| Fase 10+ | 6000-15000€ | 590-820€/mês | 5180-14180€/mês | Lucrativo |

**Regra de sustentabilidade:** Custos operacionais devem ser < 20% da receita na Fase 6+.

### 5.2 Ponto de Equilíbrio (Break-even)

**Custos fixos:** 55€/mês
**Preço por subscritor:** 29€/mês
**Break-even:** 55€ / 29€ = **1.9 subscritores**

**Com margem de segurança:** 5 subscritores (~145€ receita vs 55€ custos)

---

## 6. OTIMIZAÇÃO DE CUSTOS

### 6.1 Estratégias de Redução

| Estratégia | Economia Potencial | Implementação |
|------------|-------------------|---------------|
| Reservar VPS por 6-12 meses | 10-20% | Hetzner oferece desconto |
| Usar tiers gratuitos de APIs | 0€ | Betfair, SendGrid, NBA API |
| Compressão de backups | 50% espaço | gzip backups |
| Otimização de queries | 30-40% CPU | Índices, partitioning |
| CDN para assets estáticos | 50% bandwidth | Cloudflare gratuito |

### 6.2 Evitar Custos Ocultos

- ⚠️ **Cloud providers AWS/GCP:** Custos podem explodir sem monitorização
- ⚠️ **S3 storage:** Custos de egress podem ser altos
- ⚠️ **APIs pagas:** Sempre usar limites de rate
- ⚠️ **Over-provisioning:** Não escalar antes de necessário

---

## 7. PROJEÇÕES DE CUSTO

### 7.1 Cenário Conservador (Crescimento Lento)

| Ano | Subscritores | Receita Anual | Custos Anuais | Lucro Anual |
|-----|--------------|--------------|--------------|-------------|
| 1 | 25 | 8,700€ | 660€ | 8,040€ |
| 2 | 50 | 17,400€ | 660€ | 16,740€ |
| 3 | 100 | 34,800€ | 2,400€ | 32,400€ |

### 7.2 Cenário Aggressivo (Crescimento Rápido)

| Ano | Subscritores | Receita Anual | Custos Anuais | Lucro Anual |
|-----|--------------|--------------|--------------|-------------|
| 1 | 50 | 17,400€ | 660€ | 16,740€ |
| 2 | 150 | 52,200€ | 2,400€ | 49,800€ |
| 3 | 300 | 104,400€ | 6,000€ | 98,400€ |

---

## 8. MONITORIZAÇÃO DE CUSTOS

### 8.1 Alertas de Custo

| Alerta | Threshold | Ação |
|--------|-----------|------|
| Custo mensal > 100€ (Fase 1-6) | > 100€ | Investigar causa |
| Custo mensal > 300€ (Fase 7-9) | > 300€ | Revisar escalas |
| Custo mensal > 1000€ (Fase 10+) | > 1000€ | Auditoria completa |
| Crescimento de custo > 20% MoM | > 20% | Investigar anomalias |

### 8.2 Relatório Mensal

No final de cada mês, gerar relatório com:
- Custo por serviço
- Comparação com mês anterior
- Projeção para próximo trimestre
- Anomalias e justificações

---

## 9. CONTINGÊNCIA

### 9.1 Reserva de Emergência

Manter reserva de 3 meses de custos operacionais:
- Fase 1-6: 3 × 55€ = **165€**
- Fase 7-9: 3 × 240€ = **720€**
- Fase 10+: 3 × 700€ = **2100€**

### 9.2 Plano de Redução de Custos

Se receita cair < 50% por 2 meses consecutivos:
1. Downgrade VPS para especificação inferior
2. Mover BD para instância local (se managed)
3. Reduzir retenção de backups
4. Cancelar serviços não-críticos (monitorização avançada)

---

## 10. LINKS CRUZADOS

- [[13_Infrastructure/INDEX]] ← Secção mãe
- [[02_Business_Model/INDEX]] → Modelo de negócio e receitas
- [[36_KPIs/INDEX]] → KPIs financeiros