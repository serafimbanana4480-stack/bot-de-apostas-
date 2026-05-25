---
ID: DB-001
tags: #status/active #dashboard #executive #summary #kpi
---

# Dashboard Executive Summary

## Objetivo
Fornecer ao gestor de operações, aos investidores, e aos stakeholders estratégicos uma visão consolidada, em tempo real, do estado de saúde global do negócio de value betting NBA. O Executive Summary não é um painel operacional detalhado; é uma síntese de alto nível que responde à pergunta: "O negócio está bem?" em menos de 60 segundos de leitura.

## O que faz
- Apresenta 8 a 12 KPIs críticos selecionados de todas as áreas: financeiro (MRR, LTV, CAC, P&L), operacional (uptime, sinais/dia, taxa acerto), risco (drawdown, VaR), e compliance (alertas abertos, subscritores KYC pendentes).
- Utiliza semáforos visuais (verde/amarelo/vermelho) para cada KPI, com thresholds definidos que refletem a estratégia do negócio.
- Inclui tendência de 30 dias para cada métrica, permitindo identificar degradação antes que se torne crítica.
- Gera automaticamente um resumo narrativo (NLG - Natural Language Generation) que descreve o estado do negócio em 3-4 frases, destacando anomalias ou conquistas.

## Porque existe
- **Foco Estratégico**: Stakeholders não têm tempo para analisar 20 dashboards. Precisam de uma página que sintetize o essencial.
- **Deteção Precoce**: Uma métrica que cruza para amarelo (ex: churn rate que subiu de 3% para 6%) é um sinal de alerta estratégico que requer ação antes de afetar o P&L.
- **Comunicação Externa**: Relatórios para investidores ou parceiros comerciais podem ser exportados diretamente do Executive Summary.
- **Alinhamento da Equipa**: A primeira coisa que a equipa vê no início do dia é o Executive Summary, alinhando todos na mesma prioridade.

## Implementação / Pseudocódigo
```python
class DashboardExecutiveSummary:
    def __init__(self):
        self.kpis = {
            "mrr": {"nome": "MRR", "fonte": "bd_subscricoes", "formula": "sum(preco_mensal_ativo)", "unidade": "EUR", "threshold_verde": "> 15000", "threshold_amarelo": "10000-15000", "threshold_vermelho": "< 10000"},
            "ltv_cac_ratio": {"nome": "LTV/CAC Ratio", "fonte": "bd_subscricoes", "formula": "ltv_medio / cac_medio", "unidade": "ratio", "threshold_verde": "> 3.0", "threshold_amarelo": "2.0-3.0", "threshold_vermelho": "< 2.0"},
            "pnl_mes": {"nome": "P&L Mês", "fonte": "bd_apostas", "formula": "sum(pnl_real)", "unidade": "EUR", "threshold_verde": "> 0", "threshold_amarelo": "-5000 a 0", "threshold_vermelho": "< -5000"},
            "taxa_acerto_30d": {"nome": "Taxa Acerto 30d", "fonte": "bd_apostas", "formula": "win / (win + loss)", "unidade": "%", "threshold_verde": "> 55%", "threshold_amarelo": "52-55%", "threshold_vermelho": "< 52%"},
            "yield_30d": {"nome": "Yield 30d", "fonte": "bd_apostas", "formula": "sum(pnl) / sum(stake)", "unidade": "%", "threshold_verde": "> 5%", "threshold_amarelo": "2-5%", "threshold_vermelho": "< 2%"},
            "drawdown_atual": {"nome": "Drawdown Atual", "fonte": "bd_apostas", "formula": "(peak - current) / peak", "unidade": "%", "threshold_verde": "< 10%", "threshold_amarelo": "10-20%", "threshold_vermelho": "> 20%"},
            "uptime_sistema": {"nome": "Uptime Sistema", "fonte": "monitoring", "formula": "1 - (downtime_min / total_min)", "unidade": "%", "threshold_verde": "> 99.9%", "threshold_amarelo": "99.0-99.9%", "threshold_vermelho": "< 99.0%"},
            "sinais_dia_media": {"nome": "Sinais/Dia (média 7d)", "fonte": "bd_sinais", "formula": "count(sinais_ultimos_7d) / 7", "unidade": "count", "threshold_verde": "> 2", "threshold_amarelo": "1-2", "threshold_vermelho": "< 1"},
            "alertas_p1_abertos": {"nome": "Alertas P1 Abertos", "fonte": "bd_alertas", "formula": "count(severidade=P1 AND estado!=RESOLVED)", "unidade": "count", "threshold_verde": "0", "threshold_amarelo": "1", "threshold_vermelho": "> 1"},
            "kyc_pendente": {"nome": "KYC Pendente > 48h", "fonte": "bd_kyc", "formula": "count(status=PENDENTE AND idade>48h)", "unidade": "count", "threshold_verde": "0", "threshold_amarelo": "1-3", "threshold_vermelho": "> 3"},
            "churn_rate_mensal": {"nome": "Churn Rate Mensal", "fonte": "bd_subscricoes", "formula": "cancelados_mes / ativos_inicio_mes", "unidade": "%", "threshold_verde": "< 5%", "threshold_amarelo": "5-10%", "threshold_vermelho": "> 10%"},
            "clv_medio_30d": {"nome": "CLV Médio 30d", "fonte": "bd_apostas", "formula": "avg(clv)", "unidade": "%", "threshold_verde": "> 2.5%", "threshold_amarelo": "1.5-2.5%", "threshold_vermelho": "< 1.5%"}
        }
        self.refresh_interval_segundos = 300  # 5 minutos

    def gerar_executive_summary(self):
        dados = {}
        for chave, config in self.kpis.items():
            valor = self.calcular_kpi(chave, config)
            status = self.classificar_status(valor, config)
            tendencia = self.calcular_tendencia(chave, dias=30)
            dados[chave] = {"valor": valor, "status": status, "tendencia": tendencia, "config": config}
        
        narrativa = self.gerar_narrativa(dados)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "kpis": dados,
            "narrativa": narrativa,
            "recomendacoes_acao": self.gerar_recomendacoes(dados)
        }

    def classificar_status(self, valor, config):
        if self.avaliar_threshold(valor, config["threshold_verde"]):
            return "VERDE"
        elif self.avaliar_threshold(valor, config["threshold_amarelo"]):
            return "AMARELO"
        else:
            return "VERMELHO"

    def gerar_narrativa(self, dados):
        partes = []
        vermelhos = [k for k, v in dados.items() if v["status"] == "VERMELHO"]
        amarelos = [k for k, v in dados.items() if v["status"] == "AMARELO"]
        
        if vermelhos:
            partes.append(f"Atenção: {len(vermelhos)} KPI(s) em estado crítico: {', '.join(vermelhos)}. Ação imediata recomendada.")
        if amarelos:
            partes.append(f"{len(amarelos)} KPI(s) requerem monitorização: {', '.join(amarelos)}.")
        if not vermelhos and not amarelos:
            partes.append("Todos os KPIs estão no verde. O negócio opera dentro dos parâmetros estratégicos.")
        
        # Destaques específicos
        if dados["pnl_mes"]["tendencia"] == "SUBINDO":
            partes.append("P&L mensal apresenta tendência ascendente.")
        if dados["churn_rate_mensal"]["status"] in ["AMARELO", "VERMELHO"]:
            partes.append("Atenção especial ao churn rate; investigar causas de cancelamento.")
        
        return " ".join(partes)

    def gerar_recomendacoes(self, dados):
        recs = []
        if dados["drawdown_atual"]["status"] == "VERMELHO":
            recs.append("Ativar circuit breaker de drawdown; revisar stakes e exposição.")
        if dados["alertas_p1_abertos"]["status"] == "VERMELHO":
            recs.append("Escalar operador on-call; resolver alertas P1 antes de avançar.")
        if dados["ltv_cac_ratio"]["status"] == "AMARELO":
            recs.append("Avaliar eficiência de aquisição; considerar redução de spend em canais com CAC elevado.")
        if dados["clv_medio_30d"]["status"] == "AMARELO":
            recs.append("Revisar modelo de precificação; possível necessidade de retreino ou ajuste de features.")
        return recs
```

## Thresholds e Tabelas

| KPI | Verde | Amarelo | Vermelho | Frequência Atualização |
|-----|-------|---------|----------|----------------------|
| MRR | > €15.000 | €10.000-15.000 | < €10.000 | Real-time |
| LTV/CAC | > 3.0 | 2.0-3.0 | < 2.0 | Diário |
| P&L Mês | > €0 | -€5.000 a €0 | < -€5.000 | Real-time |
| Taxa Acerto 30d | > 55% | 52-55% | < 52% | Diário |
| Yield 30d | > 5% | 2-5% | < 2% | Diário |
| Drawdown | < 10% | 10-20% | > 20% | Real-time |
| Uptime | > 99.9% | 99.0-99.9% | < 99.0% | Real-time |
| Sinais/Dia | > 2 | 1-2 | < 1 | Diário |
| Alertas P1 | 0 | 1 | > 1 | Real-time |
| KYC Pendente | 0 | 1-3 | > 3 | 6h |
| Churn Rate | < 5% | 5-10% | > 10% | Mensal |
| CLV Médio 30d | > 2.5% | 1.5-2.5% | < 1.5% | Diário |

---

## Layout e Visualizações

### Linha 1: KPIs Críticos (Top Row)
**Layout**: 6 painéis de single stat lado a lado

1. **PnL Mês (Gauge)**
   - Visual: Número grande com indicador de tendência (seta ↑↓)
   - Cor: Verde (positivo), Amarelo (negativo < -€2.000), Vermelho (negativo < -€5.000)
   - Subtítulo: Comparação com mês anterior (ex: "+€3.200 vs Mês Anterior")
   - Sparkline: Mini gráfico de linha dos últimos 30 dias

2. **ROI 30d (Single Stat)**
   - Visual: Percentagem com target line a 3%
   - Cor: Verde (>3%), Amarelo (0-3%), Vermelho (<0%)
   - Subtítulo: "Target: 3% | Atual: X%"
   - Indicador: "Acima/Abaixo do Target"

3. **CLV Médio 50b (Single Stat)**
   - Visual: Percentagem com target line a 2%
   - Cor: Verde (>2%), Amarelo (0-2%), Vermelho (<0%)
   - Subtítulo: "Últimas 50 apostas"
   - Histórico: Média 7d em parêntesis

4. **Drawdown Atual (Gauge Radial)**
   - Visual: Gauge semi-circular (0-30%)
   - Cores: Verde (0-10%), Amarelo (10-20%), Vermelho (20-30%)
   - Subtítulo: "Limite: 15% | Atual: X%"
   - Indicador: "Dias desde peak: X"

5. **Apostas Mês (Single Stat)**
   - Visual: Número absoluto
   - Subtítulo: "Média diária: X"
   - Comparação: "+/- Y% vs mês anterior"

6. **Sharpe Ratio (Single Stat)**
   - Visual: Número decimal
   - Cor: Verde (>0.5), Amarelo (0-0.5), Vermelho (<0)
   - Subtítulo: "Target: 0.5 | Últimos 90 dias"

### Linha 2: Tendências Financeiras (Middle Row)
**Layout**: 2 painéis largos

7. **PnL Acumulado (Time Series)**
   - Visual: Gráfico de linha com área preenchida
   - Eixo X: Data (últimos 90 dias)
   - Eixo Y: PnL em EUR
   - Linhas: PnL real (sólida), PnL simulado (tracejada)
   - Anotações: Eventos marcados (ex: "Retreino Modelo v1.2")
   - Zoom: 7d, 30d, 90d, 1y
   - Tooltip: Data, PnL, ROI, CLV médio

8. **Drawdown Curve (Time Series)**
   - Visual: Gráfico de linha
   - Eixo X: Data
   - Eixo Y: Drawdown % (0-30%)
   - Linha de limite: 15% (tracejada vermelha)
   - Área sombreada abaixo da linha
   - Destaque: Drawdown máximo histórico marcado

### Linha 3: Operações e Alertas (Bottom Row)
**Layout**: 3 painéis

9. **Alertas Ativos (Table)**
   - Colunas: ID, Severidade, Mensagem, Idade (min), Owner
   - Ordenação: Por severidade (CRITICAL primeiro)
   - Cores de linha: Vermelho (P1), Laranja (P2), Amarelo (P3)
   - Ação: Clicar para ver detalhes e acknowledge
   - Contador: "X alertas ativos (Y P1, Z P2)"

10. **Narrativa NLG (Text Panel)**
    - Visual: Caixa de texto com resumo gerado automaticamente
    - Exemplo: "O negócio opera dentro dos parâmetros estratégicos. P&L mensal apresenta tendência ascendente (+€3.200). CLV médio mantém-se acima do target (2.3%). Nenhum alerta P1 ativo."
    - Atualização: A cada 15 minutos
    - Tone: Profissional, conciso, acionável

11. **Métricas Secundárias (Stat Group)**
    - Layout: 4 mini-stats
    - Métricas: Uptime, Sinais/Dia, Churn Rate, KYC Pendente
    - Cada uma com cor de status

---

## Detalhes de Visualização

### Cores e Semântica
- **Verde (#10B981)**: Saudável, dentro de target
- **Amarelo (#F59E0B)**: Atenção requerida, degradação
- **Vermelho (#EF4444)**: Crítico, ação imediata
- **Azul (#3B82F6)**: Informacional, neutro
- **Cinza (#6B7280)**: Dados históricos, baseline

### Tipos de Gráficos e Uso

**Time Series (Linha)**
- Uso: Tendências ao longo do tempo
- Melhor para: PnL, Drawdown, ROI, CLV rolling
- Configuração: Suavização (moving average), zoom, tooltips ricos

**Gauge (Radial/Linear)**
- Uso: Valores atuais vs limites
- Melhor para: Drawdown, CPU, Fill rate
- Configuração: Thresholds visuais, indicador de tendência

**Bar Chart**
- Uso: Comparação entre categorias
- Melhor para: Performance por mercado, por bookmaker
- Configuração: Ordenação, cores por valor

**Histogram**
- Uso: Distribuição de valores
- Melhor para: CLV distribution, slippage
- Configuração: Bins configuráveis, overlay de distribuição normal

**Table**
- Uso: Dados tabulares detalhados
- Melhor para: Alertas, lista de apostas, leaderboard
- Configuração: Ordenação, filtros, paginação

**Pie/Donut Chart**
- Uso: Composição de partes
- Melhor para: Bankroll por bookmaker, perfil de risco
- Configuração: Legenda com valores absolutos e percentagens

### Interatividade

**Drill-down**
- Clicar em um ponto do gráfico PnL → Ver detalhes do dia
- Clicar em uma barra de mercado → Ver apostas desse mercado
- Clicar em um alerta → Ver runbook associado

**Filtros Globais**
- Variável `$time_range`: 1h, 6h, 24h, 7d, 30d, 90d
- Variável `$market`: Todos, Spread, Total, Moneyline
- Variável `$bookmaker`: Todos, Bet365, Betway, etc.

**Comparação**
- Modo "Compare to Previous Period": Sobrepor período anterior
- Diff mode: Mostrar diferença absoluta e percentual

---

## Casos de Uso do Dashboard

### Cenário 1: Check-in Diário do Gestor
**Ação**: Abrir dashboard às 9h da manhã
**Foco**: Linha 1 (KPIs críticos) + Narrativa NLG
**Decisão**: Se todos verdes → Continuar operações normais. Se amarelo/vermelho → Investigar.

### Cenário 2: Reunião com Investidores
**Ação**: Exportar dashboard como PDF ou partilhar link
**Foco**: PnL acumulado, ROI, Drawdown, Sharpe Ratio
**Narrativa**: "O sistema gerou €X nos últimos 90 dias com ROI de Y%, mantendo drawdown abaixo de Z%."

### Cenário 3: Incidente Ativo
**Ação**: Dashboard alerta com drawdown vermelho
**Foco**: Alertas ativos + Drawdown curve
**Decisão**: Identificar causa no Operations Center, ativar circuit breaker se necessário.

### Cenário 4: Review Mensal
**Ação**: Analisar tendências de 30 dias
**Foco**: Tendências financeiras + métricas secundárias
**Decisão**: Ajustar estratégias, revisar targets, planejar retreino de modelo.

## Riscos
- **Risco de Ilusão de Controlo**: Um dashboard verde não garante que o negócio está saudável. Métricas podem ser "maquiadas" ou não refletir riscos latentes (ex: CLV alto mas slippage elevado que anula o edge).
- **Risco de Sobrecarga de KPIs**: Incluir demasiados KPIs dilui a atenção. O Executive Summary deve ter no máximo 12 métricas.
- **Risco de Latência**: Se o dashboard mostrar dados de 1 hora atrás, pode induzir a uma falsa sensação de segurança durante um incidente ativo.
- **Risco de Thresholds Desatualizados**: Thresholds definidos no lançamento podem não refletir a realidade de uma fase de scaling. Revisão trimestral obrigatória.

## Checklist do Executive Summary
- [ ] Dashboard acessível via web protegido por autenticação (SSO ou 2FA); nunca público.
- [ ] Atualização automática a cada 5 minutos; indicador de "última atualização" visível.
- [ ] Semáforos visuais claros; possibilidade de drill-down em cada KPI para o dashboard detalhado.
- [ ] Narrativa NLG gerada automaticamente; revisão humana antes de envio a stakeholders externos.
- [ ] Exportação para PDF e e-mail semanal configurada (relatório automático às segundas, 08:00 UTC).
- [ ] Revisão trimestral de thresholds por gestor de operações e gestor de risco.
- [ ] Acesso restrito: apenas gestor de operações, CEO, CFO, e investidores designados.
- [ ] Mobile-responsive: acessível em smartphone para check rápido fora do escritório.

## Links Cruzados
- [[20_Dashboarding/DB_QUANT_PERFORMANCE]] - Drill-down das métricas quantitativas.
- [[20_Dashboarding/DB_OPERATIONS_CENTER]] - Drill-down operacional.
- [[20_Dashboarding/DB_RISK_OVERVIEW]] - Drill-down de risco.
- [[20_Dashboarding/DB_TIPSTER_METRICS]] - Drill-down de performance de tipster/modelo.
- [[20_Dashboarding/DB_INFRASTRUCTURE_HEALTH]] - Drill-down de infraestrutura.
- [[35_Financial_Tracking/PLANO_CONTAS]] - Base de dados financeira que alimenta o P&L.
