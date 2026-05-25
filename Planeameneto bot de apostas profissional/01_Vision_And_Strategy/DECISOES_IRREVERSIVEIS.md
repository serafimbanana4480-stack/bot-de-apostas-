# DECISÕES IRREVERSÍVEIS — Registro de Escolhas Críticas

**ID:** `STR-001` | **Fase:** Todas | **Owner:** Chief Systems Architect | **Status:** #status/active

---

## 1. OBJETIVO

Documentar decisões que, uma vez tomadas, não podem ser revertidas sem custo massivo em tempo, dinheiro ou dados. Estas decisões requerem consenso e análise profunda antes da implementação.

---

## 2. DECISÕES IRREVERSÍVEIS REGISTADAS

| ID | Decisão | Data | Justificação | Alternativas Rejeitadas | Custo de Reversão |
|----|---------|------|--------------|-------------------------|-------------------|
| DEC-001 | Stack: Python 3.11+ como linguagem única | 2026-05-13 | Ecossistema ML maduro, velocidade de desenvolvimento | Rust (mais rápido mas curva de aprendizado), Java (overhead) | Alto (rewrite completo) |
| DEC-002 | DB: PostgreSQL 15 como BD primária | 2026-05-13 | Relacional robusto, JSONB, window functions | MongoDB (schema rígido difícil), MySQL (menos recursos analíticos) | Alto (migração de dados + rewrite queries) |
| DEC-003 | Modelo: XGBoost como algoritmo primário | 2026-05-13 | Melhor relação precisão/velocidade para dados tabulares | LightGBM (menos estável), Neural Networks (overkill, difícil interpretação) | Médio (retraining + validação) |
| DEC-004 | Foco inicial: NBA Moneyline + Spread | 2026-05-13 | Dados gratuitos de alta qualidade, ineficiências documentadas | NFL (dados menos acessíveis), Soccer (muito ruidoso) | Alto (novo pipeline de dados + modelo) |
| DEC-005 | Execução: Manual → One-click → Automática | 2026-05-13 | Validação progressiva, compliance, risco controlado | Direto para automática (risco de perdas massivas) | Alto (reversão requer nova validação) |
| DEC-006 | Validação: Purged Walk-Forward CV obrigatório | 2026-05-13 | Única forma de evitar leakage temporal em dados desportivos | Random CV (leakage garantido), Hold-out simples (overfitting) | Alto (revalidação de todos os modelos) |

---

## 3. CRITÉRIOS PARA DECISÕES IRREVERSÍVEIS

Uma decisão é considerada irreversível se:

1. **Custo de reversão > 1 mês de trabalho** OU **> 1000€**
2. **Afeta a integridade dos dados históricos** (ex: mudança de schema sem migração)
3. **Compromete a validação estatística** (ex: mudar método de CV)
4. **Tem implicações legais ou de compliance** (ex: mudança de jurisdição)
5. **Altera a arquitetura fundamental** (ex: mudar de monolito para microserviços)

---

## 4. PROCESSO DE TOMADA DE DECISÃO

### 4.1 Proposta
1. Criar nota com proposta detalhada
2. Documentar justificação técnica e de negócio
3. Listar alternativas e custo-benefício de cada

### 4.2 Revisão
1. Revisão por pelo menos 2 stakeholders técnicos
2. Revisão por 1 stakeholder de negócio (se aplicável)
3. Simulação de cenários de falha

### 4.3 Aprovação
1. Consenso mínimo: 2/3 dos stakeholders
2. Chief Architect tem veto final
3. Registo em [[LOG_DECISOES_IRREVERSIVEIS]]

### 4.4 Implementação
1. Implementação em staging primeiro
2. Testes de rollback documentados
3. Rollback plan aprovado antes de produção

---

## 5. FUTURAS DECISÕES PENDENTES

| ID | Decisão Proposta | Prioridade | Data Alvo | Stakeholders |
|----|------------------|------------|-----------|--------------|
| DEC-007 | Escolha de VPS provider (Hetzner vs DO vs Vultr) | Critical | Fase 1, Semana 1 | DevOps, Financeiro |
| DEC-008 | Escolha de orquestrador (Prefect vs Airflow vs Cron) | High | Fase 1, Semana 3 | DevOps, MLOps |
| DEC-009 | Estrutura jurídica (sole proprietor vs empresa) | Critical | Fase 3 | Legal, Financeiro |
| DEC-010 | Gateway de pagamentos (Stripe vs Paddle) | High | Fase 4 | Financeiro, Legal |

---

## 6. LINKS CRUZADOS

- [[01_Vision_And_Strategy/INDEX]] ← Secção mãe
- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[TRADE_OFFS_ARQUITETURAIS]] → Trade-offs técnicos detalhados