---
ID: DB-005
tags: #status/active #dashboard #tipster #metrics #performance #subscribers
---

# Dashboard de Métricas de Tipster / Subscritores

## Objetivo
Quantificar a performance individual de cada subscritor enquanto "tipster" (aplicador dos sinais), comparando o seu P&L real com o P&L teórico do modelo, e identificando padrões de comportamento que indiquem skill, luck, ou problemas de execução (slippage, stake errada, apostas em mercados alternativos). Este dashboard serve tanto para o subscritor compreender a sua performance quanto para a equipa de operações identificar problemas sistémicos de execução.

## O que faz
- Rastreia para cada subscritor: ROI real, yield, taxa acerto, profit factor, average odds, stakes média/máxima/mínima, e comparação com o benchmark do modelo.
- Identifica divergências: quando o subscritor tem yield significativamente inferior ao modelo, investiga slippage, timing de entrada, e escolha de bookmaker.
- Monitoriza comportamento de risco por subscritor: drawdown pessoal, aumentos de stake em sequência (chasing), dias consecutivos de apostas, e uso de múltiplas contas.
- Gera rankings anónimos (leaderboards) e benchmarks percentilares para motivação e gamificação controlada.
- Segmenta subscritores por perfil: conservador, moderado, agressivo, e inconsistente.

## Porque existe
- **Transparência com o Cliente**: O subscritor quer saber se o serviço "funciona para ele", não apenas se o modelo é bom globalmente. Se o modelo tem yield 5% mas o subscritor tem yield -2%, o problema pode ser execução.
- **Identificação de Problemas Sistémicos**: Se 30% dos subscritores têm yield consistentemente inferior ao modelo, pode haver um problema sistémico: slippage excessivo, bookmaker recomendado com limites baixos, ou instruções de stake pouco claras.
- **Retenção**: Subscritores com visibilidade da sua performance têm maior probabilidade de renovar, mesmo em períodos de drawdown, porque compreendem a variação.
- **Jogo Responsável**: Identificar subscritores com comportamento de chasing ou drawdown emocional permite intervenção precoce — [[16_Compliance/RESPONSIBLE_GAMBLING]].

## Implementação / Pseudocódigo
```python
class DashboardTipsterMetrics:
    def __init__(self):
        self.metricas_individuais = {
            "roi_real": {"formula": "sum(pnl) / sum(stake)", "unidade": "%"},
            "yield": {"formula": "sum(pnl) / sum(stake)", "unidade": "%"},
            "taxa_acerto": {"formula": "wins / (wins + losses)", "unidade": "%"},
            "profit_factor": {"formula": "sum(ganhos) / abs(sum(perdas))", "unidade": "ratio"},
            "avg_odd_jogada": {"formula": "avg(odd_obtida)", "unidade": "decimal"},
            "avg_odd_modelo": {"formula": "avg(odd_recomendada)", "unidade": "decimal"},
            "slippage_medio": {"formula": "avg(odd_recomendada - odd_obtida)", "unidade": "pontos"},
            "stake_media": {"formula": "avg(stake_eur)", "unidade": "EUR"},
            "stake_max": {"formula": "max(stake_eur)", "unidade": "EUR"},
            "stake_min": {"formula": "min(stake_eur)", "unidade": "EUR"},
            "unidade_valor": {"formula": "subscritor.unidade_eur", "unidade": "EUR"},
            "drawdown_max": {"formula": "max_drawdown(pnl_acumulado)", "unidade": "%"},
            "expectativa_vs_realidade": {"formula": "roi_real - roi_modelo", "unidade": "%"},
            "edge_capturado": {"formula": "avg(clv_realizado)", "unidade": "%"},
            "apostas_dia_media": {"formula": "count(apostas_30d) / 30", "unidade": "count"},
            "dias_consecutivos_max": {"formula": "max_sequencia_dias_com_aposta", "unidade": "dias"}
        }
        self.perfis = {
            "CONSERVADOR": {"stake_media_unidades": "< 1.0", "variacao_stake": "baixa", "mercados": "principais apenas"},
            "MODERADO": {"stake_media_unidades": "1.0 - 2.0", "variacao_stake": "média", "mercados": "principais + props"},
            "AGRESSIVO": {"stake_media_unidades": "> 2.0", "variacao_stake": "alta", "mercados": "todos"},
            "INCONSISTENTE": {"stake_media_unidades": "variável", "variacao_stake": "muito alta", "padrao": "sem padrão claro"}
        }

    def calcular_metricas_subscritor(self, subscritor_id, periodo="30d"):
        apostas = self.db.obter_apostas_subscritor(subscritor_id, periodo)
        metricas = {}
        
        for nome, config in self.metricas_individuais.items():
            if nome == "expectativa_vs_realidade":
                roi_real = self.calcular_roi(apostas)
                roi_modelo = self.calcular_roi_modelo(apostas)
                metricas[nome] = {"valor": roi_real - roi_modelo, "roi_real": roi_real, "roi_modelo": roi_modelo}
            elif nome == "drawdown_max":
                metricas[nome] = {"valor": self.calcular_drawdown(apostas), "serie": self.gerar_serie_drawdown(apostas)}
            elif nome == "slippage_medio":
                metricas[nome] = {"valor": self.calcular_slippage(apostas), "impacto_pnl": self.estimar_impacto_slippage(apostas)}
            else:
                metricas[nome] = {"valor": self.calcular_generico(nome, apostas, config)}
        
        metricas["perfil"] = self.classificar_perfil(metricas)
        metricas["percentil_yield"] = self.calcular_percentil(subscritor_id, metricas["yield"]["valor"], periodo)
        return metricas

    def calcular_slippage(self, apostas):
        slippages = [a["odd_recomendada"] - a["odd_obtida"] for a in apostas if a["odd_obtida"]]
        return np.mean(slippages) if slippages else 0

    def estimar_impacto_slippage(self, apostas):
        # Se o subscritor obtivesse a odd recomendada, qual seria o P&L?
        pnl_teoretico = sum(a["stake"] * (a["odd_recomendada"] - 1) if a["resultado"] == "WIN" else -a["stake"] if a["resultado"] == "LOSS" else 0 for a in apostas)
        pnl_real = sum(a["pnl"] for a in apostas)
        return pnl_real - pnl_teoretico

    def classificar_perfil(self, metricas):
        stake_media = metricas["stake_media"]["valor"] / metricas["unidade_valor"]["valor"] if metricas["unidade_valor"]["valor"] > 0 else 0
        variacao = np.std([a["stake"] for a in self.db.obter_apostas_subscritor(metricas["subscritor_id"], "30d")]) if "subscritor_id" in metricas else 0
        
        if stake_media > 2.5 or variacao > stake_media * 2:
            return "AGRESSIVO" if stake_media > 2.5 else "INCONSISTENTE"
        elif stake_media < 1.0 and variacao < 0.5:
            return "CONSERVADOR"
        else:
            return "MODERADO"

    def gerar_leaderboard(self, periodo="30d", top_n=20):
        subscritores = self.db.listar_subscritores_ativos()
        rankings = []
        for sub in subscritores:
            metricas = self.calcular_metricas_subscritor(sub["id"], periodo)
            rankings.append({
                "subscritor_id": sub["id"],
                "username_hash": hashlib.sha256(sub["username"].encode()).hexdigest()[:8],  # anónimo
                "yield": metricas["yield"]["valor"],
                "roi": metricas["roi_real"]["valor"],
                "profit_factor": metricas["profit_factor"]["valor"],
                "apostas": len(self.db.obter_apostas_subscritor(sub["id"], periodo)),
                "perfil": metricas["perfil"]
            })
        
        rankings.sort(key=lambda x: x["yield"], reverse=True)
        return rankings[:top_n]

    def identificar_divergencias_sistemicas(self, periodo="30d"):
        subscritores = self.db.listar_subscritores_ativos()
        divergencias = []
        for sub in subscritores:
            metricas = self.calcular_metricas_subscritor(sub["id"], periodo)
            diff = metricas["expectativa_vs_realidade"]["valor"]
            if diff < -5:  # Subscritor com yield 5% pior que o modelo
                divergencias.append({
                    "subscritor_id": sub["id"],
                    "diferenca_yield": diff,
                    "slippage": metricas["slippage_medio"]["valor"],
                    "bookmaker_principal": self.obter_bookmaker_principal(sub["id"]),
                    "recomendacao": "Revisar execução e timing de entrada"
                })
        return divergencias
```

## Thresholds e Tabelas

| Métrica Individual | Bom | Médio | Mau | Investigar |
|-------------------|-----|-------|-----|------------|
| Yield | > 5% | 2-5% | < 2% | < 0% |
| ROI Real | > 5% | 2-5% | < 2% | < 0% |
| Taxa Acerto | > 55% | 52-55% | < 52% | < 48% |
| Profit Factor | > 1.5 | 1.2-1.5 | < 1.2 | < 1.0 |
| Slippage Médio | < 0.05 | 0.05-0.10 | > 0.10 | > 0.15 |
| Drawdown Máx | < 20% | 20-30% | > 30% | > 50% |
| Dias Consecutivos | < 7 | 7-14 | > 14 | > 21 |

| Perfil | Stake Média (unid.) | Variação | Mercados | Risco de Comportamento |
|--------|---------------------|----------|----------|----------------------|
| Conservador | < 1.0 | Baixa | Principais | Baixo |
| Moderado | 1.0 - 2.0 | Média | Principais + Props | Médio |
| Agressivo | > 2.5 | Alta | Todos | Alto (chasing) |
| Inconsistente | Variável | Muito alta | Mistos | Muito alto |

| Divergência Sistémica | Threshold | Ação |
|----------------------|-----------|------|
| Slippage médio > 10% | > 10% dos subscritores | Revisar bookmaker recomendado |
| Yield subscritor < modelo - 5% | > 15% dos subscritores | Investigar timing de entrada |
| Apostas em mercados não recomendados | > 5% das apostas | Alerta de compliance |
| Múltiplas contas detetadas | ≥ 2 contas/subscritor | Revisão KYC |

## Riscos
- **Risco de Privacidade**: Mostrar rankings ou métricas detalhadas pode expor subscritores a comparações sociais negativas ou a pressão de desempenho. Leaderboards devem ser anónimos e opcionais.
- **Risco de Falso Skill**: Um subscritor com yield alto em poucas apostas pode ser "sortudo", não "skill". Leaderboards devem incluir intervalo de confiança ou requerer n mínimo de apostas.
- **Risco de Gamificação Tóxica**: Subscritores podem aumentar stakes ou apostar em mais mercados para subir no leaderboard, prejudicando a sua bankroll.
- **Risco de Generalização**: O perfil de um subscritor pode mudar ao longo do tempo. Classificações devem ser dinâmicas e revisadas mensalmente.

## Checklist do Dashboard de Tipster
- [ ] Cada subscritor tem acesso ao seu dashboard pessoal com todas as métricas individuais.
- [ ] Comparativo claro: "O modelo teve yield 4.2%; a sua execução teve yield 1.8%. Slippage médio: 0.08." — explicar a diferença.
- [ ] Leaderboard anónimo (hash de username) atualizado semanalmente; apenas subscritores com > 20 apostas no período elegíveis.
- [ ] Alerta automático para subscritores com divergência negativa > 5% vs. modelo: enviar e-mail de "dicas de execução".
- [ ] Integração com [[16_Compliance/RESPONSIBLE_GAMBLING]]: subscritores com perfil "Agressivo" ou "Inconsistente" são flagados para intervenção.
- [ ] Relatório mensal de divergências sistémicas: se > 10% dos subscritores têm slippage médio > 10%, investigar bookmaker ou timing.
- [ ] Possibilidade de exportar histórico pessoal em CSV para análise própria do subscritor.
- [ ] Revisão trimestral das métricas por perfil: os conservadores têm melhor retenção? Os agressivos têm maior churn?

## Links Cruzados
- [[20_Dashboarding/DB_EXECUTIVE_SUMMARY]] - Síntese que inclui churn e LTV.
- [[20_Dashboarding/DB_QUANT_PERFORMANCE]] - Benchmark do modelo para comparação.
- [[16_Compliance/RESPONSIBLE_GAMBLING]] - Intervenção em comportamentos de risco.
- [[22_Real_Money_Operations/TRACKING_APOSTAS]] - Base de dados que alimenta as métricas.
- [[25_SOPs/SOP-007_Onboarding_Subscritor]] - Definição de unidade e stake no onboarding.
