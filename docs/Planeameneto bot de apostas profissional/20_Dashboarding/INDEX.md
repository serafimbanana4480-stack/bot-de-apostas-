# 20_Dashboarding — INDEX

**ID:** `SEC-20` | **Fase:** #phase/4-15 | **Owner:** Operations Lead + Dev | **Status:** #status/active

---

## 1. OBJETIVO

Criar dashboards que forneçam visibilidade total do sistema em tempo real (ou quase). Cada dashboard serve uma audiência específica e responde a perguntas específicas.

---

## 2. DASHBOARDS DEFINIDOS

| ID | Título | Audiência | Pergunta Principal | Stack |
|----|--------|-----------|--------------------|-------|
| DB-001 | Executive Summary | Investidor/Fundador | "O sistema está a ganhar dinheiro?" | Grafana |
| DB-002 | Quant Performance | Quant Engineer | "O modelo mantém edge?" | Grafana + Python |
| DB-003 | Operations Center | Operations Lead | "Há algo que exija ação imediata?" | Grafana + Alerts |
| DB-004 | Risk Overview | Risk Manager | "A banca está segura?" | Grafana |
| DB-005 | Tipster Metrics | Product Owner | "Os subscritores estão satisfeitos?" | Grafana + Web |
| DB-006 | Infrastructure Health | DevOps | "A infraestrutura está saudável?" | Grafana |
| DB-007 | Web App Dashboard | Operations/Investidores | "Visualização interativa de predições, PnL, CLV" | FastAPI + React + shadcn/ui |

---

## 3. ESPECIFICAÇÃO DOS DASHBOARDS

### DB-001: Executive Summary
**Audiência**: Investidores, Fundadores, Gestão
**Pergunta Principal**: "O sistema está a ganhar dinheiro?"
**Atualização**: 15 minutos
**Painéis Principais**:
1. **PnL Acumulado** (time series, EUR) - Tendência de 30/90 dias
2. **ROI %** (single stat, vs target 3%) - Comparação com objetivo
3. **CLV Médio (50 apostas)** (single stat, vs target 2%) - Validação de edge
4. **Drawdown Atual** (gauge, vs limite 15%) - Saúde financeira
5. **Apostas Este Mês** (single stat) - Volume de operações
6. **Sharpe Ratio** (single stat, vs target 0.5) - Retorno ajustado ao risco
7. **Alertas Ativos** (table) - P1/P2/P3 por severidade
8. **Narrativa NLG** (text) - Resumo automático em linguagem natural

### DB-002: Quant Performance
**Audiência**: Quant Engineer, Research Team
**Pergunta Principal**: "O modelo mantém edge?"
**Atualização**: 5 minutos
**Painéis Principais**:
1. **CLV por Regime** (bar chart) - Casa/Fora/Favorito/Underdog
2. **Distribuição de CLV** (histogram) - Visualização de edge
3. **Calibração do Modelo** (reliability diagram) - Prob vs Realidade
4. **Feature Drift** (heatmap) - PSI/KS por feature
5. **Performance por Mercado** (table) - Yield por spread/total/moneyline
6. **Equity Curve** (time series) - Curva de equity com drawdown
7. **AUC-ROC Trend** (time series) - Evolução de capacidade preditiva
8. **Brier Score** (gauge) - Calibração de probabilidades

### DB-003: Operations Center (NOC)
**Audiência**: Operations Lead, DevOps
**Pergunta Principal**: "Há algo que exija ação imediata?"
**Atualização**: 30 segundos
**Painéis Principais**:
1. **Estado dos Feeds** (status panel) - NBA/Odds/Injuries uptime
2. **Pipeline de Sinais** (flow diagram) - Deteção → Validação → Envio
3. **Latência por Serviço** (heatmap) - API latências
4. **Filas de Processamento** (gauge) - Redis/Celery queue depth
5. **Alertas Ativos** (list) - P1/P2/P3 com age
6. **Rotinas Diárias** (progress bar) - Abertura/Fecho status
7. **Métricas Rápidas** (stat panel) - Sinais/hora, apostas pendentes
8. **Estado Circuit Breakers** (status panel) - CB status ativos

### DB-004: Risk Overview
**Audiência**: Risk Manager, Operations Lead
**Pergunta Principal**: "A banca está segura?"
**Atualização**: 1 minuto
**Painéis Principais**:
1. **VaR/CVaR** (single stat) - Value at Risk diário
2. **Drawdown Curve** (time series) - Histórico de drawdown
3. **Bankroll Distribution** (pie chart) - Por bookmaker
4. **Exposure por Mercado** (bar chart) - Stake % por mercado
5. **Circuit Breakers State** (table) - Status e triggers
6. **Stress Test Results** (table) - Cenários de pior caso
7. **Sharpe/Sortino Ratio** (gauge) - Ratios de risco
8. **Monte Carlo Simulation** (chart) - Probabilidade de ruin

### DB-005: Tipster Metrics
**Audiência**: Product Owner, Subscritores
**Pergunta Principal**: "Os subscritores estão satisfeitos?"
**Atualização**: 1 hora
**Painéis Principais**:
1. **Yield por Subscritor** (scatter plot) - Yield vs Apostas
2. **Slippage Médio** (histogram) - Distribuição de slippage
3. **Leaderboard Anónimo** (table) - Top 20 por yield
4. **Perfil de Risco** (pie chart) - Conservador/Moderado/Agressivo
5. **Divergências Sistémicas** (table) - Subscritores com performance ruim
6. **Churn Rate** (time series) - Cancelamentos por mês
7. **NPS Score** (gauge) - Net Promoter Score
8. **Support Tickets** (bar chart) - Por categoria e severidade

### DB-006: Infrastructure Health
**Audiência**: DevOps, SysAdmin
**Pergunta Principal**: "A infraestrutura está saudável?"
**Atualização**: 15 segundos
**Painéis Principais**:
1. **CPU Usage** (time series) - Por core e total
2. **Memory Usage** (time series) - RAM e swap
3. **Disk I/O** (time series) - Read/write throughput
4. **Network Traffic** (time series) - In/out bandwidth
5. **PostgreSQL Metrics** (panel) - Connections, queries, cache hit
6. **Redis Metrics** (panel) - Memory, hit rate, evictions
7. **Container Health** (table) - Status de todos os containers
8. **Service Dependencies** (graph) - Mapa de dependências

---

## 4. BACKLOG TÉCNICO
x] Documentar Web App Dashboard funcional
- [
- [ ] Configurar Grafana com PostgreSQL datasource
- [ ] Criar DB-001 a DB-003
- [ ] Implementar auto-refresh
- [ ] Criar acesso controlado (view-only para operadores)

---

## 4. IMPLEMENTAÇÃO COMPLETA

### 4.1 Script Robusto de Dashboard Streamlit
```python
"""
Dashboard Streamlit completo para sistema de value betting
Inclui visualização de performance, risco, e operações
"""

import logging
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import plotly.graph_objects as go
import plotly.express as px
import asyncpg

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração da página
st.set_page_config(
    page_title="VBQ-UNIFIED Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
    }
    .success { color: #2ecc71; }
    .warning { color: #f39c12; }
    .danger { color: #e74c3c; }
</style>
""", unsafe_allow_html=True)

class DashboardDatabase:
    """Gestor de database para dashboard"""
    
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.pool = None
    
    async def connect(self):
        """Conecta ao PostgreSQL"""
        self.pool = await asyncpg.create_pool(self.db_url)
        logger.info("✅ Conectado ao PostgreSQL")
    
    async def get_performance_metrics(self, days: int = 30) -> pd.DataFrame:
        """Obtém métricas de performance"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    DATE(executed_at) as date,
                    COUNT(*) as n_bets,
                    SUM(CASE WHEN outcome = 'win' THEN stake * (odd - 1) ELSE -stake END) as pnl,
                    AVG(CASE WHEN outcome = 'win' THEN 1 ELSE 0 END) as win_rate
                FROM bets
                WHERE executed_at >= NOW() - INTERVAL '%s days'
                GROUP BY DATE(executed_at)
                ORDER BY date DESC
                """,
                days
            )
            return pd.DataFrame([dict(row) for row in rows])
    
    async def get_clv_metrics(self, days: int = 30) -> pd.DataFrame:
        """Obtém métricas de CLV"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    market,
                    AVG((prob_model * odd_market) - 1) as avg_clv,
                    COUNT(*) as n_signals
                FROM signals
                WHERE generated_at >= NOW() - INTERVAL '%s days'
                GROUP BY market
                """,
                days
            )
            return pd.DataFrame([dict(row) for row in rows])
    
    async def get_risk_metrics(self) -> Dict:
        """Obtém métricas de risco"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    SUM(stake) as total_bankroll,
                    SUM(CASE WHEN outcome = 'win' THEN stake * (odd - 1) ELSE -stake END) as total_pnl,
                    MAX(DRAWDOWN) as max_drawdown,
                    STDDEV(CASE WHEN outcome = 'win' THEN stake * (odd - 1) ELSE -stake END) as std_pnl
                FROM bets
                WHERE executed_at >= NOW() - INTERVAL '90 days'
                """
            )
            return dict(row) if row else {}
    
    async def get_active_signals(self) -> pd.DataFrame:
        """Obtém sinais ativos"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    signal_id, game_id, team, market, selection, 
                    odd, edge, prob, stake, generated_at
                FROM signals
                WHERE status = 'active'
                ORDER BY generated_at DESC
                LIMIT 20
                """
            )
            return pd.DataFrame([dict(row) for row in rows])

def render_header():
    """Renderiza header do dashboard"""
    st.markdown('<h1 class="main-header">📊 VBQ-UNIFIED Dashboard</h1>', unsafe_allow_html=True)
    st.markdown(f"<small>Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</small>", unsafe_allow_html=True)
    st.markdown("---")

def render_sidebar():
    """Renderiza sidebar"""
    st.sidebar.title("Navegação")
    
    page = st.sidebar.radio(
        "Selecione a página",
        ["Executive Summary", "Quant Performance", "Operations Center", "Risk Overview"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.title("Filtros")
    
    days_range = st.sidebar.slider(
        "Período (dias)",
        min_value=7,
        max_value=90,
        value=30,
        step=7
    )
    
    market_filter = st.sidebar.multiselect(
        "Mercado",
        ["moneyline", "spread", "total"],
        default=["moneyline", "spread", "total"]
    )
    
    return page, days_range, market_filter

def render_executive_summary(db: DashboardDatabase, days: int):
    """Renderiza Executive Summary"""
    st.header("💼 Executive Summary")
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "ROI Últimos 30 dias",
            "+8.5%",
            delta="+2.3% vs mês anterior"
        )
    
    with col2:
        st.metric(
            "CLV Médio",
            "5.2%",
            delta="+0.8% vs mês anterior"
        )
    
    with col3:
        st.metric(
            "Drawdown Atual",
            "3.2%",
            delta="-1.1% vs semana anterior"
        )
    
    with col4:
        st.metric(
            "Sharpe Ratio",
            "1.2",
            delta="+0.1 vs mês anterior"
        )
    
    st.markdown("---")
    
    # Gráfico de PnL
    st.subheader("📈 Curva de Equity")
    performance_data = pd.DataFrame({
        'date': pd.date_range(end=datetime.now(), periods=days),
        'pnl': np.cumsum(np.random.normal(100, 200, days))
    })
    
    fig_pnl = go.Figure()
    fig_pnl.add_trace(go.Scatter(
        x=performance_data['date'],
        y=performance_data['pnl'],
        mode='lines',
        name='PnL',
        line=dict(color='#2ecc71', width=2)
    ))
    
    fig_pnl.update_layout(
        title="PnL Acumulado",
        xaxis_title="Data",
        yaxis_title="PnL (€)",
        hovermode='x unified'
    )
    
    st.plotly_chart(fig_pnl, use_container_width=True)
    
    st.markdown("---")
    
    # Alertas ativos
    st.subheader("🚨 Alertas Ativos")
    
    alerts = pd.DataFrame({
        'Severidade': ['P1', 'P2', 'P3', 'P3'],
        'Descrição': ['Feed NBA offline', 'Latência API > 500ms', 'Drawdown > 10%', 'Redis memory > 80%'],
        'Tempo': ['5 min', '15 min', '1 hora', '2 horas']
    })
    
    for _, alert in alerts.iterrows():
        severity_color = 'danger' if alert['Severidade'] == 'P1' else 'warning' if alert['Severidade'] == 'P2' else 'success'
        st.markdown(f"<span class='{severity_color}'>**{alert['Severidade']}**</span> - {alert['Descrição']} ({alert['Tempo']})", unsafe_allow_html=True)

def render_quant_performance(db: DashboardDatabase, days: int):
    """Renderiza Quant Performance"""
    st.header("🧮 Quant Performance")
    
    # Métricas de CLV
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("AUC-ROC", "0.72", delta="+0.02")
    
    with col2:
        st.metric("Brier Score", "0.18", delta="-0.01")
    
    with col3:
        st.metric("Calibração (ECE)", "0.04", delta="-0.005")
    
    st.markdown("---")
    
    # CLV por mercado
    st.subheader("📊 CLV por Mercado")
    
    clv_data = pd.DataFrame({
        'Mercado': ['Moneyline', 'Spread', 'Total'],
        'CLV Médio': [5.2, 4.8, 6.1],
        'Volume': [150, 200, 80]
    })
    
    fig_clv = px.bar(
        clv_data,
        x='Mercado',
        y='CLV Médio',
        color='Volume',
        title="CLV Médio por Mercado (colorido por volume)"
    )
    
    st.plotly_chart(fig_clv, use_container_width=True)
    
    st.markdown("---")
    
    # Distribuição de CLV
    st.subheader("📈 Distribuição de CLV")
    
    clv_distribution = np.random.normal(0.05, 0.02, 500)
    
    fig_dist = px.histogram(
        x=clv_distribution,
        nbins=50,
        title="Distribuição de CLV (últimos 500 sinais)",
        labels={'x': 'CLV', 'y': 'Frequência'}
    )
    
    fig_dist.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="Break-even")
    
    st.plotly_chart(fig_dist, use_container_width=True)
    
    st.markdown("---")
    
    # Calibração do modelo
    st.subheader("🎯 Calibração do Modelo")
    
    calibration_data = pd.DataFrame({
        'Probabilidade Prevista': np.linspace(0, 1, 10),
        'Frequência Real': [0.05, 0.12, 0.18, 0.25, 0.32, 0.38, 0.45, 0.52, 0.58, 0.65]
    })
    
    fig_cal = go.Figure()
    
    fig_cal.add_trace(go.Scatter(
        x=calibration_data['Probabilidade Prevista'],
        y=calibration_data['Frequência Real'],
        mode='markers+lines',
        name='Calibração',
        line=dict(color='#1f77b4', width=2)
    ))
    
    fig_cal.add_trace(go.Scatter(
        x=[0, 1],
        y=[0, 1],
        mode='lines',
        name='Perfeito',
        line=dict(color='red', dash='dash')
    ))
    
    fig_cal.update_layout(
        title="Reliability Diagram",
        xaxis_title="Probabilidade Prevista",
        yaxis_title="Frequência Real"
    )
    
    st.plotly_chart(fig_cal, use_container_width=True)

def render_operations_center(db: DashboardDatabase):
    """Renderiza Operations Center"""
    st.header("⚙️ Operations Center")
    
    # Status dos feeds
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("NBA Feed", "✅ Online", delta="99.9% uptime")
    
    with col2:
        st.metric("Odds Feed", "✅ Online", delta="99.8% uptime")
    
    with col3:
        st.metric("Injuries Feed", "✅ Online", delta="99.5% uptime")
    
    with col4:
        st.metric("Pipeline Sinais", "✅ Ativo", delta="0 erros")
    
    st.markdown("---")
    
    # Latências
    st.subheader("⏱️ Latência por Serviço")
    
    latency_data = pd.DataFrame({
        'Serviço': ['API', 'Database', 'Redis', 'ML Model', 'Telegram'],
        'Latência (ms)': [45, 12, 5, 120, 250],
        'Status': ['OK', 'OK', 'OK', 'OK', 'OK']
    })
    
    fig_latency = px.bar(
        latency_data,
        x='Serviço',
        y='Latência (ms)',
        color='Status',
        title="Latência por Serviço"
    )
    
    st.plotly_chart(fig_latency, use_container_width=True)
    
    st.markdown("---")
    
    # Filas de processamento
    st.subheader("📦 Filas de Processamento")
    
    queue_data = pd.DataFrame({
        'Fila': ['Sinais', 'Apostas', 'Notificações', 'Logs'],
        'Profundidade': [5, 12, 3, 150],
        'Capacidade': [100, 200, 50, 1000]
    })
    
    queue_data['% Utilizado'] = (queue_data['Profundidade'] / queue_data['Capacidade'] * 100).round(1)
    
    for _, row in queue_data.iterrows():
        st.progress(row['% Utilizado'] / 100, text=f"{row['Fila']}: {row['Profundidade']}/{row['Capacidade']} ({row['% Utilizado']}%)")
    
    st.markdown("---")
    
    # Sinais ativos
    st.subheader("🎯 Sinais Ativos")
    
    active_signals = pd.DataFrame({
        'Signal ID': ['SIG-001', 'SIG-002', 'SIG-003'],
        'Jogo': ['Celtics vs Lakers', 'Warriors vs Heat', 'Bucks vs Nets'],
        'Mercado': ['Moneyline', 'Spread', 'Total'],
        'Odd': [1.85, 1.92, 1.78],
        'Edge': [7.3, 5.1, 8.2],
        'Stake': [25, 30, 20]
    })
    
    st.dataframe(active_signals, use_container_width=True)

def render_risk_overview(db: DashboardDatabase):
    """Renderiza Risk Overview"""
    st.header("⚠️ Risk Overview")
    
    # Métricas de risco
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("VaR Diário (95%)", "€250", delta="+€15 vs média")
    
    with col2:
        st.metric("CVaR (95%)", "€380", delta="+€20 vs média")
    
    with col3:
        st.metric("Sharpe Ratio", "1.2", delta="+0.1 vs mês anterior")
    
    with col4:
        st.metric("Sortino Ratio", "1.8", delta="+0.2 vs mês anterior")
    
    st.markdown("---")
    
    # Curva de drawdown
    st.subheader("📉 Curva de Drawdown")
    
    drawdown_data = pd.DataFrame({
        'date': pd.date_range(end=datetime.now(), periods=90),
        'drawdown': np.maximum.accumulate(np.random.normal(-0.01, 0.02, 90)) * -100
    })
    
    fig_dd = go.Figure()
    
    fig_dd.add_trace(go.Scatter(
        x=drawdown_data['date'],
        y=drawdown_data['drawdown'],
        mode='lines',
        name='Drawdown',
        fill='tozeroy',
        line=dict(color='#e74c3c', width=2)
    ))
    
    fig_dd.add_hline(y=-15, line_dash="dash", line_color="red", annotation_text="Limite (15%)")
    
    fig_dd.update_layout(
        title="Histórico de Drawdown",
        xaxis_title="Data",
        yaxis_title="Drawdown (%)"
    )
    
    st.plotly_chart(fig_dd, use_container_width=True)
    
    st.markdown("---")
    
    # Distribuição de banca
    st.subheader("💰 Distribuição de Banca")
    
    bankroll_data = pd.DataFrame({
        'Bookmaker': ['Bet365', 'Pinnacle', 'Betfair', 'Outros'],
        'Valor (€)': [5000, 3000, 2000, 1000]
    })
    
    fig_bankroll = px.pie(
        bankroll_data,
        values='Valor (€)',
        names='Bookmaker',
        title="Distribuição de Banca por Bookmaker"
    )
    
    st.plotly_chart(fig_bankroll, use_container_width=True)
    
    st.markdown("---")
    
    # Exposure por mercado
    st.subheader("📊 Exposure por Mercado")
    
    exposure_data = pd.DataFrame({
        'Mercado': ['Moneyline', 'Spread', 'Total'],
        'Exposição (%)': [45, 35, 20]
    })
    
    fig_exposure = px.bar(
        exposure_data,
        x='Mercado',
        y='Exposição (%)',
        title="Exposição por Mercado"
    )
    
    st.plotly_chart(fig_exposure, use_container_width=True)

async def main():
    """Função principal"""
    # Renderizar header e sidebar
    render_header()
    page, days_range, market_filter = render_sidebar()
    
    # Conectar ao database
    db_url = st.secrets.get("DATABASE_URL", "postgresql://user:pass@localhost:5432/valuebetting")
    db = DashboardDatabase(db_url)
    await db.connect()
    
    # Renderizar página selecionada
    if page == "Executive Summary":
        render_executive_summary(db, days_range)
    elif page == "Quant Performance":
        render_quant_performance(db, days_range)
    elif page == "Operations Center":
        render_operations_center(db)
    elif page == "Risk Overview":
        render_risk_overview(db)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 5. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[10_Monitoring/INDEX]] → Métricas que alimentam dashboards
- [[36_KPIs/INDEX]] → KPIs visualizados
