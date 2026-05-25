---
ID: DB-004
tags: #status/active #dashboard #risk #overview #var #drawdown
---

# Dashboard de Risco (Risk Overview)

## Objetivo
Fornecer ao gestor de risco, ao gestor de operações, e à equipa de execução uma visão consolidada, em tempo real, de todos os riscos materiais do sistema de value betting NBA. O dashboard deve quantificar o risco de mercado, o risco operacional, o risco de modelo, o risco de liquidez, e o risco reputacional, permitindo a tomada de decisão proativa sobre exposição, stakes, e circuit breakers.

## O que faz
- Apresenta métricas de risco financeiro: VaR (Value at Risk) diário e mensal, CVaR (Conditional VaR), drawdown atual vs. máximo permitido, bankroll disponível vs. comprometida, e concentração de exposição por mercado/equipa.
- Monitoriza estado dos circuit breakers: quais estão ativos, qual foi o trigger, desde quando, e qual a condição de reativação.
- Rastreia risco de modelo: drift de features, degradação de performance (AUC, Brier), e divergência entre backtest e produção.
- Quantifica risco operacional: fila de sinais pendentes, latência de execução, taxa de falha de envio Telegram, e incidência de slippage excessivo.
- Inclui stress testing: cenários de "pior dia possível" baseados em histórico e simulação de Monte Carlo.

## Porque existe
- **Preservação de Capital**: O risco mais importante em betting quantitativo não é maximizar ganhos, mas minimizar a probabilidade de ruin. Um dashboard de risco que não é consultado diariamente é inútil.
- **Alavancagem Emocional**: Operadores que veem drawdowns crescentes tendem a tomar decisões irracionais (aumentar stakes para "recuperar"). O dashboard objetiva a decisão.
- **Regulamentação e Compliance**: Autoridades de jogo e parceiros comerciais podem exigir demonstração de gestão de risco responsável.
- **Ajuste Dinâmico de Stakes**: O sistema de Kelly ou fracional Kelly pode ser ajustado automaticamente com base no risco atual, se o dashboard o quantificar.

## Implementação / Pseudocódigo
```python
class DashboardRiskOverview:
    def __init__(self):
        self.metricas_risco = {
            "var_95_1d": {"formula": "np.percentile(pnl_historico_1d, 5)", "unidade": "EUR", "limite": -5000},
            "var_99_1d": {"formula": "np.percentile(pnl_historico_1d, 1)", "unidade": "EUR", "limite": -10000},
            "cvar_95_1d": {"formula": "np.mean(pnl_historico_1d[pnl_historico_1d <= var_95])", "unidade": "EUR", "limite": -7500},
            "drawdown_atual": {"formula": "(peak - current) / peak", "unidade": "%", "limite": 0.20},
            "drawdown_maximo_historico": {"formula": "max(drawdown_serie)", "unidade": "%", "limite": 0.30},
            "bankroll_total": {"formula": "sum(saldos_bookmakers) + caixa", "unidade": "EUR", "limite": 10000},
            "bankroll_comprometida": {"formula": "sum(stakes_pendentes)", "unidade": "EUR", "limite": None},
            "exposicao_por_mercado": {"formula": "stake_mercado / bankroll_total", "unidade": "%", "limite": 0.40},
            "exposicao_por_equipa": {"formula": "stake_equipa / bankroll_total", "unidade": "%", "limite": 0.15},
            "sharpe_ratio": {"formula": "(retorno_medio - risk_free) / desvio_padrao", "unidade": "ratio", "limite": 1.0},
            "sortino_ratio": {"formula": "(retorno_medio - risk_free) / desvio_negativo", "unidade": "ratio", "limite": 1.5},
            "calmar_ratio": {"formula": "retorno_anual / max_drawdown", "unidade": "ratio", "limite": 2.0}
        }
        self.circuit_breakers = {
            "CB_DD_DIARIO": {"trigger": "drawdown_dia > 15%", "acao": "PAUSAR_SINAIS_24H", "status": "CLOSED"},
            "CB_DD_SEMANAL": {"trigger": "drawdown_7d > 25%", "acao": "PAUSAR_SINAIS_7D", "status": "CLOSED"},
            "CB_CLV_3D": {"trigger": "clv_medio_3d < 0%", "acao": "REDUZIR_STAKE_50%", "status": "CLOSED"},
            "CB_MODELO_DRIFT": {"trigger": "features_drift > 3", "acao": "PAUSAR_MODELO_RETRAIN", "status": "CLOSED"},
            "CB_LIQUIDEZ": {"trigger": "bankroll_comprometida > 80%", "acao": "PAUSAR_NOVAS_APOSTAS", "status": "CLOSED"},
            "CB_SLIPPAGE": {"trigger": "slippage_medio > 10%", "acao": "REDUZIR_STAKE_50%_VERIFICAR_BOOKS", "status": "CLOSED"}
        }
        self.cenarios_stress = {
            "PIOR_DIA_HISTORICO": {"descricao": "Repetir o pior dia de P&L dos últimos 12 meses", "impacto": None},
            "CISNE_NEGRO_3S": {"descricao": "3 desvios padrão abaixo da média diária", "impacto": None},
            "MONTE_CARLO_RUIN": {"descricao": "Simulação de 10.000 trajetórias; prob. de ruin", "impacto": None},
            "MODELO_FALHA_TOTAL": {"descricao": "Modelo com AUC de 0.50 (azar)", "impacto": None}
        }

    def calcular_var(self, confianca=0.95, horizonte=1):
        retornos = self.db.obter_retornos_diarios(horizonte=horizonte, dias=252)
        var = np.percentile(retornos, (1 - confianca) * 100)
        return {"var": var, "confianca": confianca, "horizonte_dias": horizonte}

    def calcular_cvar(self, confianca=0.95, horizonte=1):
        var = self.calcular_var(confianca, horizonte)["var"]
        retornos = self.db.obter_retornos_diarios(horizonte=horizonte, dias=252)
        cvar = np.mean([r for r in retornos if r <= var])
        return {"cvar": cvar, "confianca": confianca}

    def avaliar_circuit_breakers(self):
        estado = {}
        for nome, config in self.circuit_breakers.items():
            triggered = self.avaliar_trigger(config["trigger"])
            estado[nome] = {
                "status": "OPEN" if triggered else "CLOSED",
                "trigger": config["trigger"],
                "acao": config["acao"],
                "desde": self.db.obter_timestamp_trigger(nome) if triggered else None,
                "pode_reativar": self.verificar_condicao_reativacao(nome) if triggered else True
            }
        return estado

    def executar_stress_test(self, cenario):
        if cenario == "PIOR_DIA_HISTORICO":
            pior_dia = self.db.obter_pior_dia(periodo="12m")
            return {"cenario": cenario, "impacto_eur": pior_dia["pnl"], "prob_ocorrencia_historica": 1/252}
        elif cenario == "CISNE_NEGRO_3S":
            retornos = self.db.obter_retornos_diarios(dias=252)
            media = np.mean(retornos)
            dp = np.std(retornos)
            impacto = media - 3 * dp
            return {"cenario": cenario, "impacto_eur": impacto, "prob_teorica": "0.13%"}
        elif cenario == "MONTE_CARLO_RUIN":
            resultados = self.simular_monte_carlo(trajetorias=10000, dias=365, bankroll_inicial=self.metricas_risco["bankroll_total"]["limite"])
            ruin = sum(1 for r in resultados if r <= 0) / len(resultados)
            return {"cenario": cenario, "prob_ruin": ruin, "bankroll_medio_final": np.mean(resultados)}
        elif cenario == "MODELO_FALHA_TOTAL":
            # Simular com taxa acerto 50% e odds médias atuais
            return {"cenario": cenario, "impacto_anual_estimado": self.simular_modelo_random()}

    def simular_monte_carlo(self, trajetorias, dias, bankroll_inicial):
        resultados = []
        for _ in range(trajetorias):
            bankroll = bankroll_inicial
            for _ in range(dias):
                pnl = np.random.choice(self.db.obter_retornos_diarios(dias=252))
                bankroll += pnl
                if bankroll <= 0:
                    break
            resultados.append(bankroll)
        return resultados

    def gerar_dashboard(self):
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "risco_financeiro": {
                "var_95_1d": self.calcular_var(0.95, 1),
                "var_99_1d": self.calcular_var(0.99, 1),
                "cvar_95_1d": self.calcular_cvar(0.95, 1),
                "drawdown": self.calcular_drawdown_atual(),
                "bankroll": self.obter_estado_bankroll(),
                "exposicao": self.obter_exposicao_detalhada(),
                "ratios": self.calcular_ratios_risco()
            },
            "circuit_breakers": self.avaliar_circuit_breakers(),
            "risco_modelo": self.avaliar_risco_modelo(),
            "risco_operacional": self.avaliar_risco_operacional(),
            "stress_test": {c: self.executar_stress_test(c) for c in self.cenarios_stress}
        }
```

## Thresholds e Tabelas

| Métrica | Fórmula | Limite Máximo | Alerta | Frequência |
|---------|---------|--------------|--------|------------|
| VaR 95% 1d | Percentil 5 retornos | -€5.000 | < -€5.000 | Diário |
| VaR 99% 1d | Percentil 1 retornos | -€10.000 | < -€10.000 | Diário |
| CVaR 95% 1d | Média abaixo VaR 95% | -€7.500 | < -€7.500 | Diário |
| Drawdown Atual | (Peak - Current) / Peak | 20% | > 20% | Real-time |
| Drawdown Máximo Hist. | Máximo série | 30% | > 30% | Diário |
| Exposição por Mercado | Stake mercado / Bankroll | 40% | > 40% | Real-time |
| Exposição por Equipa | Stake equipa / Bankroll | 15% | > 15% | Real-time |
| Sharpe Ratio | (R - Rf) / σ | 1.0 | < 1.0 | Mensal |
| Sortino Ratio | (R - Rf) / σ- | 1.5 | < 1.5 | Mensal |
| Calmar Ratio | R anual / MDD | 2.0 | < 2.0 | Anual |

| Circuit Breaker | Trigger | Ação | Condição Reativação |
|----------------|---------|------|---------------------|
| CB_DD_DIARIO | Drawdown dia > 15% | Pausar sinais 24h | DD dia < 10% + ACK gestor |
| CB_DD_SEMANAL | Drawdown 7d > 25% | Pausar sinais 7d | DD 7d < 20% + reavaliação modelo |
| CB_CLV_3D | CLV médio 3d < 0% | Reduzir stake 50% | CLV 3d > 1% por 2 dias |
| CB_MODELO_DRIFT | Features drift > 3 | Pausar modelo + retreino | Novo modelo validado (AUC > baseline) |
| CB_LIQUIDEZ | Bankroll comprometida > 80% | Pausar novas apostas | < 60% comprometida |
| CB_SLIPPAGE | Slippage médio > 10% | Reduzir stake 50% + verificar books | Slippage < 5% por 24h |

## Riscos
- **Risco de Falsa Precisão**: VaR assume distribuição histórica dos retornos. Eventos "cisne negro" não estão na história. O CVaR e o stress testing mitigam, mas não eliminam.
- **Risco de Stake Aumentada em Volatilidade Baixa**: Se o VaR cai porque a volatilidade histórica caiu, um modelo Kelly pode aumentar stakes, expondo o sistema a um choque de volatilidade futuro.
- **Risco de Circuit Breaker Cascata**: Um CB que pausa sinais pode fazer com que o sistema perca oportunidades de recuperação, aprofundando o drawdown psicológico.
- **Risco de Concentração Não Detetada**: O dashboard pode mostrar exposição por mercado, mas não capturar correlação implícita (ex: apostar em 3 jogos com a mesma equipa favorita que se correlacionam negativamente).

## Checklist do Dashboard de Risco
- [ ] Todos os circuit breakers monitorizados em tempo real; estado OPEN/CHANGE em vermelho piscante no NOC.
- [ ] VaR e CVaR calculados diariamente com histórico de pelo menos 252 dias de produção.
- [ ] Stress testing executado semanalmente; relatório arquivado com cenários e resultados.
- [ ] Limite de drawdown comunicado a todos os operadores; nenhum operador pode ignorar CB ativo.
- [ ] Exposição por mercado e por equipa atualizada em tempo real; alerta se threshold excedido.
- [ ] Ratios (Sharpe, Sortino, Calmar) calculados mensalmente; revisão por gestor de risco.
- [ ] Simulação de Monte Carlo com parâmetros atualizados trimestralmente (média, desvio, skewness, kurtosis dos retornos).
- [ ] Reunião diária de 5 minutos revisa o dashboard de risco antes de qualquer decisão de aumento de stake ou mudança de modelo.

## Links Cruzados
- [[20_Dashboarding/DB_EXECUTIVE_SUMMARY]] - Síntese que inclui drawdown e alertas P1.
- [[20_Dashboarding/DB_QUANT_PERFORMANCE]] - Métricas de modelo que alimentam o risco de modelo.
- [[08_Risk_Management]] - Pasta central de gestão de risco.
- [[22_Real_Money_Operations/BANCA_GESTAO]] - Gestão de bankroll que define os limites de exposição.
- [[25_SOPs/SOP-004_Resposta_Circuit_Breaker]] - Procedimento quando um CB é ativado.
