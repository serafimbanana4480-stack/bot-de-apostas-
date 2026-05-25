# BANCA_GESTAO — Gestão de Banca

**ID:** `RMO-001` | **Fase:** #phase/4+ | **Owner:** Operations Lead | **Status:** #status/pending

---

## 1. OBJETIVO

Documentar os procedimentos de gestão da banca em dinheiro real.

---

## 2. ESTRUTURA DA BANCA

### 2.1 Capital Inicial
- **Mínimo recomendado:** 500€ (micro banca para validação)
- **Banca operacional:** 1000-5000€ (Fase 4-5)
- **Banca alvo:** 10.000€+ (Fase 6+)

**Regra:** Nunca apostar mais do que se está disposto a perder integralmente.

### 2.2 Separação de Fundos
- Banca de apostas separada de despesas pessoais
- Conta bancária dedicada (recomendado)
- Tracking rigoroso de todos os depósitos e levantamentos

## 3. REGRAS DE GESTÃO

### 3.1 Kelly Fracionado
```
stake = bankroll × K × (P × odd − 1) / (odd − 1)
```
- **K = 0.5** (meio Kelly para reduzir variância)
- **Stake máxima por aposta:** 2% do bankroll
- **Exposição máxima por jogo:** 4% do bankroll (múltiplos mercados)
- **Exposição máxima diária:** 12% do bankroll

### 3.2 Ajuste por Regime de Volatilidade
| Regime | Condição | Ajuste de Stake |
|--------|----------|-----------------|
| Normal | CLV 30d > 2% | Kelly padrão (K=0.5) |
| Cauteloso | CLV 30d 0-2% | Kelly reduzido (K=0.3) |
| Defensivo | CLV 30d < 0% ou drawdown > 10% | Kelly mínimo (K=0.1) ou STOP |

### 3.3 Regras de Depósito/Levantamento
- **Depósito:** Apenas quando bankroll < 50% do objetivo mensal
- **Levantamento:** Mensal, máximo 50% dos lucros do mês
- **Reinvestimento:** 50% dos lucros reinvestidos para crescimento composto

## 4. TRACKING E REPORTING

### 4.1 Métricas Diárias
- Bankroll atual
- PnL do dia
- Drawdown desde o pico
- Número de apostas e win rate

### 4.2 Reconciliação
- Comparar PnL calculado vs PnL real da Betfair (se aplicável)
- Divergência aceitável: < 1% do bankroll
- Se divergência > 1%: investigar imediatamente

## 5. PROCEDIMENTOS DE EMERGÊNCIA

- **Drawdown > 15%:** Reduzir stakes 50%
- **Drawdown > 25%:** STOP total, reavaliação completa
- **Perda de 50% da banca:** STOP permanente até nova análise de viabilidade

## 6. BACKLOG

- [x] Definir regras de depósito/levantamento
- [x] Configurar tracking de banca
- [ ] Implementar reconciliação bancária automatizada
- [x] Documentar procedimentos de emergência

---

## 7. LINKS CRUZADOS

- [[22_Real_Money_Operations/INDEX]] ← Secção mãe
- [[08_Risk_Management/KELLY_FRACIONADO]] → Cálculo detalhado do Kelly
- [[08_Risk_Management/DRAWDOWN_CONTROL]] → Controle de drawdown
- [[08_Risk_Management/BANKROLL_SURVIVAL]] → Simulações de Monte Carlo
