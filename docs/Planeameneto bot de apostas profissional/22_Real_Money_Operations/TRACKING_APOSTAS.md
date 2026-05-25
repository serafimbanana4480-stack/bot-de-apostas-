# TRACKING_APOSTAS — Tracking de Apostas

**ID:** `RMO-002` | **Fase:** #phase/4+ | **Owner:** Operations Lead | **Status:** #status/pending

---

## 1. OBJETIVO

Documentar o sistema de tracking de apostas em dinheiro real.

---

## 2. SCHEMA DE TRACKING

### 2.1 Tabela `bets` (Apostas)

```sql
CREATE TABLE bets (
    bet_id              VARCHAR(50) PRIMARY KEY,     -- ID único da aposta
    signal_id           VARCHAR(50) NOT NULL,         -- Ligação ao sinal gerado
    game_id             VARCHAR(50) NOT NULL,         -- Jogo
    
    -- Informação da aposta
    market_type         VARCHAR(20) NOT NULL,         -- 'moneyline', 'spread', 'totals'
    selection           VARCHAR(100) NOT NULL,        -- 'Lakers', 'Over 215.5'
    side                VARCHAR(10) NOT NULL,         -- 'BACK' ou 'LAY'
    
    -- Odds
    odd_signal          DECIMAL(8,3) NOT NULL,        -- Odd no momento do sinal
    odd_executed        DECIMAL(8,3) NOT NULL,        -- Odd realmente obtida
    odd_close           DECIMAL(8,3),                 -- Odd de fecho (para CLV)
    
    -- Stakes
    stake_planned       DECIMAL(10,2) NOT NULL,     -- Stake calculado pelo Kelly
    stake_executed      DECIMAL(10,2) NOT NULL,     -- Stake realmente apostada
    bankroll_at_bet     DECIMAL(10,2) NOT NULL,     -- Bankroll no momento da aposta
    kelly_fraction      DECIMAL(5,4) NOT NULL,      -- Fração de Kelly usada
    
    -- Resultado
    result              VARCHAR(10),                  -- 'win', 'loss', 'void', 'pending'
    pnl                 DECIMAL(10,2),                -- Lucro/perda em EUR
    roi_bet             DECIMAL(8,4),                 -- ROI desta aposta específica
    clv                 DECIMAL(8,4),                 -- (odd_executed / odd_close) - 1
    
    -- Execução
    execution_mode      VARCHAR(20) NOT NULL,         -- 'manual', 'one_click', 'automatic'
    execution_timestamp TIMESTAMPTZ NOT NULL,
    slippage_pct        DECIMAL(6,4),                 -- (odd_executed - odd_signal) / odd_signal
    
    -- Metadados
    bookmaker           VARCHAR(50) NOT NULL,         -- 'Betfair', 'Pinnacle'
    bet_id_external     VARCHAR(50),                  -- ID da aposta na casa
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_bets_game ON bets(game_id);
CREATE INDEX idx_bets_date ON bets(execution_timestamp);
CREATE INDEX idx_bets_result ON bets(result) WHERE result = 'pending';
```

### 2.2 Tabela `bankroll_history` (Histórico de Bankroll)

```sql
CREATE TABLE bankroll_history (
    id                  SERIAL PRIMARY KEY,
    date                DATE NOT NULL UNIQUE,
    bankroll_start      DECIMAL(10,2) NOT NULL,
    bankroll_end        DECIMAL(10,2) NOT NULL,
    total_staked        DECIMAL(10,2) NOT NULL DEFAULT 0,
    total_pnl           DECIMAL(10,2) NOT NULL DEFAULT 0,
    n_bets              INT NOT NULL DEFAULT 0,
    max_drawdown_day    DECIMAL(6,4),                 -- Drawdown máximo neste dia
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## 3. REGISTRO DE APOSTAS

### 3.1 API de Registro

```python
class BetTracker:
    """Registra e tracking de apostas em dinheiro real."""
    
    def register_bet(self, bet: BetRecord) -> str:
        """Registra nova aposta no sistema."""
        bet_id = f"BET-{datetime.now().strftime('%Y%m%d')}-{uuid4().hex[:6]}"
        
        self.db.execute("""
            INSERT INTO bets (
                bet_id, signal_id, game_id, market_type, selection, side,
                odd_signal, odd_executed, stake_planned, stake_executed,
                bankroll_at_bet, kelly_fraction, execution_mode,
                execution_timestamp, slippage_pct, bookmaker, bet_id_external
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (bet_id, bet.signal_id, bet.game_id, bet.market_type, bet.selection,
              bet.side, bet.odd_signal, bet.odd_executed, bet.stake_planned,
              bet.stake_executed, bet.bankroll_at_bet, bet.kelly_fraction,
              bet.execution_mode, bet.execution_timestamp, bet.slippage_pct,
              bet.bookmaker, bet.bet_id_external))
        
        logger.info(f"Aposta {bet_id} registrada: {bet.selection} @ {bet.odd_executed}")
        return bet_id
    
    def update_result(self, bet_id: str, result: str, pnl: float, odd_close: float = None):
        """Atualiza resultado da aposta após jogo finalizado."""
        clv = None
        if odd_close:
            clv = (self.db.get_bet_odd_executed(bet_id) / odd_close) - 1
        
        self.db.execute("""
            UPDATE bets 
            SET result = %s, pnl = %s, odd_close = %s, clv = %s, updated_at = NOW()
            WHERE bet_id = %s
        """, (result, pnl, odd_close, clv, bet_id))
        
        logger.info(f"Aposta {bet_id} atualizada: {result}, PnL: {pnl:.2f}€")
    
    def get_open_bets(self) -> List[BetRecord]:
        """Retorna apostas pendentes (sem resultado)."""
        return self.db.query("SELECT * FROM bets WHERE result = 'pending'")
    
    def get_daily_summary(self, date: date) -> DailySummary:
        """Resumo diário de apostas."""
        result = self.db.query_one("""
            SELECT 
                COUNT(*) as n_bets,
                SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN result = 'loss' THEN 1 ELSE 0 END) as losses,
                SUM(stake_executed) as turnover,
                SUM(pnl) as pnl
            FROM bets
            WHERE DATE(execution_timestamp) = %s
        """, (date,))
        
        return DailySummary(
            date=date,
            n_bets=result.n_bets,
            wins=result.wins,
            losses=result.losses,
            pnl=result.pnl or 0,
            yield_pct=(result.pnl / result.turnover * 100) if result.turnover > 0 else 0
        )
```

---

## 4. RECONCILIAÇÃO COM CASAS

### 4.1 Processo Diário

```python
class BookmakerReconciliation:
    """Reconcilia apostas internas com extrato da casa."""
    
    def reconcile_daily(self, date: date, bookmaker: str) -> ReconciliationReport:
        """
        1. Extrair apostas do bookmaker (API ou CSV)
        2. Comparar com registro interno
        3. Identificar: faltantes, stakes diferentes, odds diferentes
        4. Gerar relatório de discrepâncias
        """
        internal = self.tracker.get_bets_by_date(date, bookmaker)
        external = self.bookmaker_api.get_bets(date)
        
        discrepancies = []
        
        # Verificar apostas internas que não estão no external
        for ib in internal:
            eb = next((e for e in external if e.external_id == ib.bet_id_external), None)
            if eb is None:
                discrepancies.append(f"Aposta {ib.bet_id} não encontrada no {bookmaker}")
            else:
                if abs(ib.stake_executed - eb.stake) > 0.01:
                    discrepancies.append(f"Stake mismatch: {ib.bet_id} (int:{ib.stake_executed} vs ext:{eb.stake})")
                if abs(ib.odd_executed - eb.odd) > 0.01:
                    discrepancies.append(f"Odd mismatch: {ib.bet_id} (int:{ib.odd_executed} vs ext:{eb.odd})")
        
        # Verificar apostas no external que não estão no internal
        for eb in external:
            ib = next((i for i in internal if i.bet_id_external == eb.external_id), None)
            if ib is None:
                discrepancies.append(f"Aposta {eb.external_id} no {bookmaker} mas não registrada internamente")
        
        return ReconciliationReport(
            date=date,
            bookmaker=bookmaker,
            internal_count=len(internal),
            external_count=len(external),
            discrepancies=discrepancies,
            status='OK' if not discrepancies else 'DISCREPANCY'
        )
```

---

## 5. RELATÓRIOS DE PERFORMANCE

### 5.1 Métricas Calculadas Automaticamente

| Métrica | Fórmula | Target |
|---------|---------|--------|
| ROI | SUM(pnl) / SUM(stake_executed) | > 0% |
| Yield | SUM(pnl) / SUM(stake_executed) × 100 | > 2% |
| CLV Médio | AVG((odd_executed / odd_close) - 1) | > 0% |
| Taxa de Acerto | COUNT(win) / COUNT(settled) | 45-55% |
| Profit Factor | SUM(pnl_wins) / ABS(SUM(pnl_losses)) | > 1.1 |
| Sharpe Ratio | AVG(roi) / STDDEV(roi) | > 0.5 |
| Max Drawdown | Max queda desde pico | < 20% |
| Slippage Médio | AVG((odd_executed - odd_signal) / odd_signal) | < 2% |

### 5.2 Relatório Mensal

```python
def generate_monthly_report(month: int, year: int) -> MonthlyReport:
    """Gera relatório mensal completo de performance."""
    query = """
    SELECT 
        COUNT(*) as n_bets,
        SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) as wins,
        SUM(stake_executed) as turnover,
        SUM(pnl) as pnl,
        AVG(clv) as avg_clv,
        AVG(slippage_pct) as avg_slippage,
        STDDEV(pnl / stake_executed) as volatilidade
    FROM bets
    WHERE EXTRACT(MONTH FROM execution_timestamp) = %s
      AND EXTRACT(YEAR FROM execution_timestamp) = %s
      AND result IN ('win', 'loss')
    """
    
    result = db.query_one(query, (month, year))
    
    return MonthlyReport(
        month=month,
        year=year,
        n_bets=result.n_bets,
        win_rate=result.wins / result.n_bets if result.n_bets > 0 else 0,
        turnover=result.turnover,
        pnl=result.pnl,
        roi=result.pnl / result.turnover if result.turnover > 0 else 0,
        avg_clv=result.avg_clv,
        avg_slippage=result.avg_slippage,
        sharpe=(result.pnl / result.n_bets) / result.volatilidade if result.volatilidade > 0 else 0
    )
```

---

## 6. BACKLOG

- [x] Definir schema completo de tracking (bets + bankroll_history)
- [x] Implementar API de registro de apostas
- [x] Documentar reconciliação com casas
- [x] Documentar métricas de performance e relatórios
- [ ] Implementar dashboard de tracking em tempo real
- [ ] Configurar alertas para discrepâncias de reconciliação
- [ ] Implementar exportação de relatórios mensais (PDF/CSV)

---

## 7. LINKS CRUZADOS

- [[22_Real_Money_Operations/INDEX]] ← Secção mãe
- [[22_Real_Money_Operations/BANCA_GESTAO]] → Gestão de bankroll
- [[09_Execution_System/EXECUCAO_MANUAL]] → Execução manual
- [[35_Financial_Tracking/PLANILHA_PnL]] → Planilha de PnL
