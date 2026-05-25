# Reconciliação

**ID:** RM-009 | **Fase:** Fase 4+ | **Owner:** Operations Lead

---

## 1. OBJETIVO

Garantir que todas as transações de apostas estejam corretamente registradas, reconciliadas com os bookmakers, e auditáveis para fins fiscais e de performance.

---

## 2. PROCESSO DE RECONCILIAÇÃO

### 2.1 Fluxo Diário

```
1. Fecho do dia (00:00 UTC)
2. Exportar apostas do sistema
3. Exportar apostas do bookmaker (Betfair API)
4. Comparar registros
5. Identificar discrepâncias
6. Investigar e corrigir
7. Atualizar banco de dados
8. Gerar relatório diário
```

### 2.2 Freqüência

- **Reconciliação Automática:** Diária (automatizada às 00:00 UTC)
- **Reconciliação Manual:** Semanal (revisão de discrepâncias)
- **Reconciliação Profunda:** Mensal (auditoria completa)

---

## 3. CAMPOS DE RECONCILIAÇÃO

### 3.1 Chave Primária

| Campo | Sistema | Bookmaker | Match |
|-------|---------|-----------|-------|
| Bet ID | bet_id (interno) | betId (Betfair) | Mapping table |
| Game ID | game_id | eventId | game_id |
| Market ID | market_id | marketId | market_id |
| Selection ID | selection_id | selectionId | selection_id |

### 3.2 Campos Financeiros

| Campo | Sistema | Bookmaker | Tolerância |
|-------|---------|-----------|------------|
| Stake | stake | size | €0.01 |
| Odd | odd_taken | price | 0.0001 |
| Profit/Loss | profit_loss | profitLoss | €0.01 |
| Commission | - | commission | €0.01 |

### 3.3 Campos Temporais

| Campo | Sistema | Bookmaker | Tolerância |
|-------|---------|-----------|------------|
| Placed At | placed_at | placedDate | 1 segundo |
| Settled At | settled_at | settledDate | 1 minuto |

---

## 4. TIPOS DE DISCREPÂNCIAS

### 4.1 Missing Bet (Sistema → Bookmaker)

**Descrição:** Aposta registrada no sistema mas não encontrada no bookmaker

**Causas:**
- Falha de execução (odd desapareceu)
- Timeout de API
- Erro de validação no bookmaker

**Ação:**
- Marcar como 'failed'
- Investigar logs de execução
- Ajustar PnL para -stake (se aplicável)

### 4.2 Missing Bet (Bookmaker → Sistema)

**Descrição:** Aposta encontrada no bookmaker mas não registrada no sistema

**Causas:**
- Aposta manual não registrada
- Falha de logging
- Sincronização atrasada

**Ação:**
- Registrar no sistema
- Investigar causa da falha
- Corrigir processo de logging

### 4.3 Stake Mismatch

**Descrição:** Stake diferente entre sistema e bookmaker

**Causas:**
- Slippage
- Erro de rounding
- Partial fill

**Ação:**
- Atualizar stake no sistema para o valor real
- Registrar slippage
- Investigar se slippage está dentro de tolerância

### 4.4 Odd Mismatch

**Descrição:** Odd diferente entre sistema e bookmaker

**Causas:**
- Movimento de odds entre geração e execução
- Erro de captura
- Odd ajustada pelo bookmaker

**Ação:**
- Atualizar odd no sistema
- Registrar slippage
- Calcular impacto no edge

### 4.5 Outcome Mismatch

**Descrição:** Resultado diferente entre sistema e bookmaker

**Causas:**
- Erro de cálculo
- Resultado alterado (void, cancelamento)
- Dados incorretos

**Ação:**
- Atualizar outcome no sistema
- Investigar se houve void/cancelamento
- Ajustar PnL

### 4.6 Timing Mismatch

**Descrição:** Timestamps diferem além da tolerância

**Causas:**
- Diferença de timezone
- Atraso de sincronização
- Clock drift

**Ação:**
- Normalizar timestamps para UTC
- Investigar sincronização de relógios

---

## 5. IMPLEMENTAÇÃO

### 5.1 Sistema de Reconciliação Automática

```python
class BetReconciler:
    def __init__(self, db, bookmaker_api):
        self.db = db
        self.bookmaker_api = bookmaker_api
    
    def reconcile_daily(self, date):
        """
        Reconcilia apostas de um dia específico
        """
        # Obter apostas do sistema
        system_bets = self.db.get_bets_by_date(date)
        
        # Obter apostas do bookmaker
        bookmaker_bets = self.bookmaker_api.get_bets_by_date(date)
        
        # Criar mapping por bet_id
        system_map = {bet['internal_id']: bet for bet in system_bets}
        bookmaker_map = {bet['bet_id']: bet for bet in bookmaker_bets}
        
        # Reconciliar
        discrepancies = []
        
        # Check missing bets (sistema → bookmaker)
        for bet_id, bet in system_map.items():
            if bet_id not in bookmaker_map:
                discrepancies.append({
                    'type': 'MISSING_BOOKMAKER',
                    'bet_id': bet_id,
                    'details': bet
                })
        
        # Check missing bets (bookmaker → sistema)
        for bet_id, bet in bookmaker_map.items():
            if bet_id not in system_map:
                discrepancies.append({
                    'type': 'MISSING_SYSTEM',
                    'bet_id': bet_id,
                    'details': bet
                })
        
        # Check field mismatches
        common_bets = set(system_map.keys()) & set(bookmaker_map.keys())
        for bet_id in common_bets:
            system_bet = system_map[bet_id]
            bookmaker_bet = bookmaker_map[bet_id]
            
            # Check stake
            if abs(system_bet['stake'] - bookmaker_bet['size']) > 0.01:
                discrepancies.append({
                    'type': 'STAKE_MISMATCH',
                    'bet_id': bet_id,
                    'system_value': system_bet['stake'],
                    'bookmaker_value': bookmaker_bet['size']
                })
            
            # Check odd
            if abs(system_bet['odd_taken'] - bookmaker_bet['price']) > 0.0001:
                discrepancies.append({
                    'type': 'ODD_MISMATCH',
                    'bet_id': bet_id,
                    'system_value': system_bet['odd_taken'],
                    'bookmaker_value': bookmaker_bet['price']
                })
        
        return discrepancies
    
    def auto_correct(self, discrepancies):
        """
        Corrige automaticamente discrepâncias simples
        """
        corrected = []
        manual_review = []
        
        for discrepancy in discrepancies:
            if discrepancy['type'] in ['STAKE_MISMATCH', 'ODD_MISMATCH']:
                # Auto-corrigir
                self.db.update_bet(
                    discrepancy['bet_id'],
                    stake=discrepancy['bookmaker_value']
                )
                corrected.append(discrepancy)
            else:
                # Requer revisão manual
                manual_review.append(discrepancy)
        
        return corrected, manual_review
```

### 5.2 Relatório Diário de Reconciliação

```python
def generate_reconciliation_report(discrepancies, date):
    """
    Gera relatório diário de reconciliação
    """
    report = {
        'date': date,
        'total_bets': len(discrepancies) + count_matched_bets(date),
        'matched_bets': count_matched_bets(date),
        'discrepancies': len(discrepancies),
        'discrepancy_breakdown': {
            'MISSING_BOOKMAKER': count_by_type(discrepancies, 'MISSING_BOOKMAKER'),
            'MISSING_SYSTEM': count_by_type(discrepancies, 'MISSING_SYSTEM'),
            'STAKE_MISMATCH': count_by_type(discrepancies, 'STAKE_MISMATCH'),
            'ODD_MISMATCH': count_by_type(discrepancies, 'ODD_MISMATCH'),
            'OUTCOME_MISMATCH': count_by_type(discrepancies, 'OUTCOME_MISMATCH')
        },
        'auto_corrected': count_auto_corrected(discrepancies),
        'manual_review': count_manual_review(discrepancies),
        'financial_impact': calculate_financial_impact(discrepancies)
    }
    
    return report
```

---

## 6. AUDITORIA

### 6.1 Trilha de Auditoria

**Campos:**
- ID da transação
- Timestamp de todas as mudanças
- Usuário/sistema que fez a mudança
- Razão da mudança
- Valores antigos e novos

**Implementação:**
```sql
CREATE TABLE reconciliation_audit (
    audit_id BIGSERIAL PRIMARY KEY,
    bet_id BIGINT NOT NULL,
    field_changed VARCHAR(50) NOT NULL,
    old_value DECIMAL(15, 2),
    new_value DECIMAL(15, 2),
    changed_by VARCHAR(100) NOT NULL,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reason TEXT
);
```

### 6.2 Auditoria Mensal

**Verificações:**
- [ ] Todas as apostas do mês reconciliadas
- [ ] Discrepâncias resolvidas
- [ ] PnL calculado corretamente
- [ ] Comissões registradas
- [ ] Taxas aplicadas corretamente

**Relatório:**
- Resumo de reconciliação
- Discrepâncias pendentes
- Ajustes manuais
- Recomendações

---

## 7. INTEGRAÇÃO FISCAL

### 7.1 Dados para IRS Portugal

**Campos Obrigatórios:**
- Data da aposta
- Stake
- Odd
- Resultado (win/loss)
- Profit/Loss
- Comissão
- Bookmaker

**Exportação:**
```python
def export_for_tax(year):
    """
    Exporta dados para declaração fiscal
    """
    bets = db.get_bets_by_year(year)
    
    tax_data = []
    for bet in bets:
        tax_data.append({
            'data': bet['placed_at'].strftime('%Y-%m-%d'),
            'stake': bet['stake'],
            'odd': bet['odd_taken'],
            'resultado': 'GANHOU' if bet['profit_loss'] > 0 else 'PERDEU',
            'lucro_prejuizo': bet['profit_loss'],
            'comissao': bet.get('commission', 0),
            'casa': bet['bookmaker']
        })
    
    return pd.DataFrame(tax_data)
```

### 7.2 Retenção na Fonte

**Portugal:** 35% sobre ganhos (apenas em casas licenciadas em Portugal)

**Cálculo:**
```python
def calculate_withholding_tax(profit_loss, bookmaker_country):
    """
    Calcula retenção na fonte
    """
    if profit_loss > 0 and bookmaker_country == 'PT':
        return profit_loss * 0.35
    else:
        return 0.0
```

---

## 8. MONITORAMENTO

### 8.1 Métricas de Reconciliação

| Métrica | Target | Frequência |
|---------|--------|------------|
| Taxa de Match | > 98% | Diário |
| Discrepâncias Auto-corrigidas | > 80% | Diário |
| Tempo de Resolução Manual | < 24h | Semanal |
| Impacto Financeiro Discrepâncias | < 0.1% PnL | Mensal |

### 8.2 Alertas

| Condição | Severidade | Ação |
|----------|------------|------|
| Match rate < 95% | HIGH | Investigar |
| Discrepâncias manuais > 10/dia | MEDIUM | Revisar processo |
| Impacto financeiro > €100 | HIGH | Notificar |

---

## 9. BACKLOG TÉCNICO

- [ ] Implementar sistema de reconciliação automática
- [ ] Criar dashboard de reconciliação
- [ ] Configurar alertas de discrepâncias
- [ ] Implementar exportação fiscal
- [ ] Criar relatórios mensais de auditoria
- [ ] Adicionar validação de integridade

---

## 10. LINKS CRUZADOS

- [[08_Risk_Management/INDEX]] ← Índice principal
- [[35_Financial_Tracking/PNL_TRACKING]] → Tracking de PnL
- [[35_Financial_Tracking/TAX_REPORTING]] → Report fiscal
- [[15_Database/INDEX]] → Database schema
