---
ID: DB-002
tags: #status/active #dashboard #quant #performance #metrics
---

# Dashboard de Performance Quantitativa

## Objetivo
Fornecer ao quant analyst, ao gestor de modelo, e à equipa de research uma visão detalhada e em tempo real da performance dos modelos preditivos, das métricas de qualidade dos sinais, e da eficácia da deteção de valor. Este dashboard é o cockpit da equipa quantitativa, permitindo identificar degradação de modelo, oportunidades de melhoria, e validar hipóteses de research com dados ao vivo.

## O que faz
- Apresenta métricas de modelo em múltiplas granularidades: por modelo, por mercado, por linha (spread/total/moneyline), por conferência (Leste/Oeste), por horário de jogo, e por fase da época (pré-season, regular season, playoffs).
- Monitoriza métricas de calibração: reliability diagram, Brier score, log-loss, AUC-ROC, AUC-PR, e calibration error.
- Rastreia métricas de negócio quantitativo: CLV (Closing Line Value) realizado vs. esperado, slippage (diferença entre odd recomendada e odd obtida), yield por mercado, e taxa de acerto condicional (ex: quando a confiança > 80%).
- Inclui visualizações avançadas: curva de equity, drawdown, distribuição de stakes, heatmap de performance por hora/dia da semana, e gráfico de modelo drift.

## Porque existe
- **Qualidade do Modelo**: Um modelo que treinou bem em backtest mas degradou em produção precisa ser detetado em dias, não em meses. Este dashboard permite intervenção rápida (retreino, ajuste de features, ou pausa de mercado).
- **Otimização de Mercados**: Nem todos os mercados têm o mesmo ROI. O dashboard identifica quais mercados são lucrativos e quais consomem bankroll sem retorno.
- **Validação de Hipóteses**: Quando a equipa de research propõe uma nova feature ou um novo modelo, o dashboard fornece os dados para validar a hipótese em produção (A/B testing implícito).
- **Transparência Interna**: A equipa de operações e gestão confia na equipa quant porque os dados são visíveis. Sem transparência, a confiança desaparece.

## Implementação / Pseudocódigo
```python
class DashboardQuantPerformance:
    def __init__(self):
        self.metricas_modelo = {
            "auc_roc": {"descricao": "Area Under Curve - ROC", "limite_min": 0.55, "limite_alerta": 0.53},
            "auc_pr": {"descricao": "Area Under Curve - Precision-Recall", "limite_min": 0.60, "limite_alerta": 0.55},
            "brier_score": {"descricao": "Brier Score (probabilidades calibradas)", "limite_max": 0.25, "limite_alerta": 0.30},
            "log_loss": {"descricao": "Log Loss", "limite_max": 0.65, "limite_alerta": 0.70},
            "calibration_error_ece": {"descricao": "Expected Calibration Error", "limite_max": 0.05, "limite_alerta": 0.10},
            "ks_statistic": {"descricao": "Kolmogorov-Smirnov", "limite_min": 0.10, "limite_alerta": 0.08}
        }
        self.metricas_negocio = {
            "clv_medio": {"formula": "avg((odd_fechada / odd_abertura) - 1)", "unidade": "%"},
            "clv_realizado": {"formula": "avg((odd_fechada / odd_recomendada) - 1)", "unidade": "%"},
            "slippage_medio": {"formula": "avg(odd_recomendada - odd_obtida)", "unidade": "pontos de odd"},
            "yield_total": {"formula": "sum(pnl) / sum(stake)", "unidade": "%"},
            "yield_por_mercado": {"formula": "sum(pnl_mercado) / sum(stake_mercado)", "unidade": "%"},
            "taxa_acerto_global": {"formula": "wins / (wins + losses)", "unidade": "%"},
            "taxa_acerto_condicional": {"formula": "wins_conf > X / total_conf > X", "unidade": "%"},
            "roi_esperado": {"formula": "sum(edge * stake) / sum(stake)", "unidade": "%"},
            "roi_real": {"formula": "sum(pnl) / sum(stake)", "unidade": "%"}
        }
        self.filtros = ["modelo_version", "mercado", "linha", "conferencia", "horario", "fase_temporada", "bookmaker", "stake_range"]

    def gerar_painel(self, filtros=None):
        painel = {
            "timestamp": datetime.utcnow().isoformat(),
            "periodo": filtros.get("periodo", "30d") if filtros else "30d",
            "resumo_geral": self.calcular_resumo_geral(filtros),
            "metricas_modelo": self.calcular_metricas_modelo(filtros),
            "metricas_negocio": self.calcular_metricas_negocio(filtros),
            "analise_mercado": self.analisar_por_mercado(filtros),
            "analise_temporal": self.analisar_por_tempo(filtros),
            "calibracao": self.gerar_dados_calibracao(filtros),
            "equity_curve": self.gerar_equity_curve(filtros),
            "drawdown": self.calcular_drawdown(filtros),
            "drift": self.avaliar_modelo_drift(filtros)
        }
        return painel

    def calcular_metricas_modelo(self, filtros):
        resultados = {}
        for nome, config in self.metricas_modelo.items():
            valor = self.db.consultar_metrica(nome, filtros)
            status = "OK" if self.dentro_limites(valor, config) else "ALERTA"
            resultados[nome] = {"valor": valor, "status": status, "config": config}
        return resultados

    def calcular_metricas_negocio(self, filtros):
        resultados = {}
        for nome, config in self.metricas_negocio.items():
            valor = self.db.consultar_metrica_calculada(nome, filtros)
            resultados[nome] = {"valor": valor, "formula": config["formula"], "unidade": config["unidade"]}
        return resultados

    def avaliar_modelo_drift(self, filtros):
        # Compara distribuição de features em produção vs. treino
        features = self.db.obter_features_atuais(filtros)
        baseline = self.carregar_baseline_treino()
        
        drift = {}
        for feature in features:
            ks_stat, p_value = ks_2samp(baseline[feature], features[feature])
            drift[feature] = {
                "ks_stat": ks_stat,
                "p_value": p_value,
                "drift_detectado": p_value < 0.01,
                "severidade": "ALTO" if p_value < 0.001 else "MEDIO" if p_value < 0.01 else "BAIXO"
            }
        
        features_drift = [f for f, d in drift.items() if d["drift_detectado"]]
        return {"drift_por_feature": drift, "total_features_drift": len(features_drift), "recomendacao": "RETRAIN" if len(features_drift) > 3 else "MONITORAR"}

    def gerar_equity_curve(self, filtros):
        apostas = self.db.obter_apostas_sequenciais(filtros)
        equity = [0]
        for aposta in apostas:
            equity.append(equity[-1] + aposta["pnl"])
        return {"equity": equity, "max_equity": max(equity), "min_equity": min(equity)}

    def calcular_drawdown(self, filtros):
        equity = self.gerar_equity_curve(filtros)["equity"]
        peak = equity[0]
        max_dd = 0
        dd_curve = []
        for val in equity:
            if val > peak:
                peak = val
            dd = (peak - val) / peak if peak > 0 else 0
            dd_curve.append(dd)
            if dd > max_dd:
                max_dd = dd
        return {"max_drawdown": max_dd, "drawdown_curve": dd_curve, "duracao_max_dd": self.calcular_duracao_max_dd(dd_curve)}
```

## Thresholds e Tabelas

| Métrica | Fórmula | Limite Mínimo | Limite Alerta | Frequência Check |
|---------|---------|--------------|---------------|------------------|
| AUC-ROC | roc_auc_score | >= 0.55 | < 0.53 | Por modelo / semana |
| AUC-PR | average_precision | >= 0.60 | < 0.55 | Por modelo / semana |
| Brier Score | mean((y - p)^2) | <= 0.25 | > 0.30 | Por modelo / semana |
| Log Loss | log_loss | <= 0.65 | > 0.70 | Por modelo / semana |
| Calibration ECE | ECE | <= 0.05 | > 0.10 | Por modelo / mês |
| KS Statistic | ks_2samp | >= 0.10 | < 0.08 | Por modelo / semana |

| Mercado | Yield Esperado | Yield Real | Taxa Acerto | CLV Médio | Status |
|---------|---------------|-----------|-------------|-----------|--------|
| Spread | 4.5% | ? | ? | ? | A monitorizar |
| Total | 3.8% | ? | ? | ? | A monitorizar |
| Moneyline | 2.1% | ? | ? | ? | A monitorizar |
| Player Props | 5.2% | ? | ? | ? | A monitorizar |

| Condição | Taxa Acerto | Yield | Edge Médio | N Amostras |
|----------|------------|-------|-----------|------------|
| Confiança > 80% | ? | ? | ? | ? |
| Confiança 60-80% | ? | ? | ? | ? |
| Confiança < 60% | ? | ? | ? | ? |
| Edge > 5% | ? | ? | ? | ? |
| Edge 2.5-5% | ? | ? | ? | ? |
| Edge < 2.5% | ? | ? | ? | ? |

## Riscos
- **Risco de Overfitting ao Dashboard**: A equipa quant pode ajustar o modelo para otimizar métricas visuais em vez de P&L real. O dashboard deve mostrar P&L como métrica primária.
- **Risco de Lag em Métricas de Modelo**: Cálculo de AUC-PR em produção requer labels (resultados dos jogos). Se o dashboard mostrar métricas de modelo em jogos já terminados vs. sinais ao vivo, a confusão pode levar a decisões erradas.
- **Risco de Análise por Slicing Excessivo**: Segmentar por 20 dimensões diferentes cria amostras pequenas com variância alta, levando a conclusões espúrias (ex: "às terças o yield é 15%" com n=3).
- **Risco de Drift Não Ação**: O dashboard pode mostrar drift e a equipa não atuar porque "ainda está no amarelo". Thresholds de drift devem ser automáticos: se 3+ features drift, o modelo é pausado para retreino.

## Checklist do Dashboard Quant
- [ ] Dados atualizados até à última aposta fechada; indicador de "último jogo processado" visível.
- [ ] Drill-down funcional: clicar em "Spread" mostra sub-métricas de spread; clicar em "Player Props" mostra props.
- [ ] Curva de equity e drawdown atualizadas em tempo real (ou no máximo 5 min de lag).
- [ ] Relatório de drift executado diariamente; alerta automático se threshold de retreino atingido.
- [ ] Comparativo de modelos: versão atual vs. baseline vs. candidato (se hoje A/B testing).
- [ ] Exportação para CSV/Excel de qualquer tabela ou gráfico para análise externa.
- [ ] Acesso restrito à equipa de quant, gestor de risco, e gestor de operações.
- [ ] Reunião semanal de research revê este dashboard como ponto de partida; decisões de retreino documentadas.

## Links Cruzados
- [[20_Dashboarding/DB_EXECUTIVE_SUMMARY]] - Síntese de alto nível para stakeholders.
- [[20_Dashboarding/DB_RISK_OVERVIEW]] - Drill-down de risco que complementa as métricas quant.
- [[05_Machine_Learning]] - Pasta de ML com detalhes dos modelos monitorizados.
- [[06_Backtesting]] - Pasta de backtesting com baseline de treino.
- [[29_Experiment_Tracking/MLFLOW_CONFIG]] - Tracking de experimentos que alimenta as métricas de modelo.
