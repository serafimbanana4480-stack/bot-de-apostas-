# PLANILHA_PnL — Planilha de PnL

**ID:** `DB-005` | **Fase:** #phase/3 | **Owner:** Data Analyst | **Status:** #status/active

---

## 1. OBJETIVO

Definir estrutura de planilha para tracking de PnL.

---

## 2. COLUNAS

| Coluna | Descrição | Tipo |
|--------|-----------|------|
| Data | Data da aposta | Date |
| Jogo | ID do jogo | String |
| Mercado | Tipo de aposta | String |
| Stake | Valor apostado | Moeda |
| Odd | Odd executada | Decimal |
| Prob | Probabilidade prevista | Decimal |
| Edge | Edge calculado | Decimal |
| Resultado | Win/Loss | Boolean |
| PnL | Lucro/Prejuízo | Moeda |

---

## 3. CÁLCULOS

```python
def calculate_pnl_row(row):
    """
    Calcula PnL para uma linha da planilha.
    
    Args:
        row: Linha da planilha
    
    Returns:
        PnL
    """
    if row['Resultado']:
        return row['Stake'] * (row['Odd'] - 1)
    else:
        return -row['Stake']
```

---

## 4. AGREGAÇÕES

- **PnL diário**: Soma de PnL por dia
- **PnL semanal**: Soma de PnL por semana
- **PnL mensal**: Soma de PnL por mês
- **ROI**: PnL / Stake Total

---

## 5. EXPORTAÇÃO

```python
def export_pnl_to_excel(start_date, end_date):
    """
    Exporta PnL para Excel.
    
    Args:
        start_date: Data inicial
        end_date: Data final
    
    Returns:
        Caminho do ficheiro Excel
    """
    bets = get_bets_between(start_date, end_date)
    
    df = pd.DataFrame(bets)
    df['PnL'] = df.apply(calculate_pnl_row, axis=1)
    
    filepath = f"pnl_{start_date}_{end_date}.xlsx"
    df.to_excel(filepath, index=False)
    
    return filepath
```

---

## 6. CRITÉRIOS

- **Atualização diária** da planilha
- **Exportação mensal** para Excel
- **Cálculos automáticos** de PnL e ROI

---

## 7. LINKS CRUZADOS

- [[09_Monitoring/INDEX]]
- [[PNL_TRACKING]]
