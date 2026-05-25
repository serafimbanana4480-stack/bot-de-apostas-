# RECONCILIACAO_DIARIA — Reconciliação Diária

**ID:** `OP-006` | **Fase:** #phase/3 | **Owner:** Operations Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Executar reconciliação diária de todas as apostas do dia anterior.

---

## 2. SCHEDULE

```python
# Cron job: todos os dias às 08:00
# Reconcilia apostas do dia anterior
```

---

## 3. PIPELINE DIÁRIO

```python
def daily_reconciliation_pipeline():
    """Pipeline de reconciliação diária."""
    yesterday = datetime.now() - timedelta(days=1)
    
    # 1. Obter apostas do sistema
    system_bets = get_system_bets(yesterday)
    
    # 2. Obter histórico do bookmaker
    bk_history = fetch_bookmaker_history(yesterday)
    
    # 3. Reconciliar
    reconciled, unreconciled, divergences = reconcile_bets(system_bets, bk_history)
    
    # 4. Calcular PnL real
    real_pnl = calculate_real_pnl(reconciled)
    
    # 5. Atualizar dashboard
    update_dashboard({
        'date': yesterday,
        'n_bets': len(system_bets),
        'reconciled': len(reconciled),
        'unreconciled': len(unreconciled),
        'divergences': len(divergences),
        'pnl': real_pnl
    })
    
    # 6. Gerar relatório
    generate_daily_report(yesterday, reconciled, unreconciled, divergences)
    
    return {
        'reconciled': len(reconciled),
        'unreconciled': len(unreconciled),
        'divergences': len(divergences),
        'pnl': real_pnl
    }
```

---

## 4. RELATÓRIO DIÁRIO

```python
def generate_daily_report(date, reconciled, unreconciled, divergences):
    """Gera relatório diário em Markdown."""
    report = f"""
# Relatório Diário - {date.strftime('%Y-%m-%d')}

## Resumo
- Apostas totais: {len(reconciled) + len(unreconciled)}
- Reconciliadas: {len(reconciled)}
- Não reconciliadas: {len(unreconciled)}
- Divergências: {len(divergences)}

## PnL
- PnL real: €{calculate_real_pnl(reconciled):.2f}

## Detalhes
"""
    
    if len(unreconciled) > 0:
        report += "\n### Apostas Não Reconciliadas\n"
        for bet in unreconciled:
            report += f"- {bet['game_id']}: {bet['timestamp']}\n"
    
    if len(divergences) > 0:
        report += "\n### Divergências\n"
        for diff in divergences:
            report += f"- {diff['system']['game_id']}: stake {diff['system']['stake']} vs {diff['bookmaker']['stake']}\n"
    
    save_report(report, f"reports/daily_{date.strftime('%Y%m%d')}.md")
```

---

## 5. ALERTAS

```python
def daily_alerts(results):
    """Envia alertas baseados em resultados."""
    if results['unreconciled'] > 0:
        send_telegram_message(f"⚠️ {results['unreconciled']} apostas não reconciliadas")
    
    if results['divergences'] > 0:
        send_telegram_message(f"⚠️ {results['divergences']} divergências encontradas")
    
    if results['pnl'] < -50:
        send_telegram_message(f"🚨 PnL negativo: €{results['pnl']:.2f}")
```

---

## 6. CRITÉRIOS

- **Executar diariamente** às 08:00
- **100% reconciliado** ideal
- **Alertar se > 5%** não reconciliado

---

## 7. LINKS CRUZADOS

- [[07_Execution/INDEX]]
- [[RECONCILIACAO]]
