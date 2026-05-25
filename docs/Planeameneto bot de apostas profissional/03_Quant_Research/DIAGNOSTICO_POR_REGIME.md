# Diagnóstico de Performance por Regime de Jogo (NBA)

**Versão:** 1.0.0  
**Status:** #status/active #priority/high  
**Área:** Quant Research / ML

---

## 🎯 RACIONAL
Os modelos de Machine Learning (XGBoost) tendem a assumir que os relacionamentos entre as features são constantes em todo o espaço amostral. Na NBA, no entanto, a dinâmica do jogo muda drasticamente entre a Temporada Regular e os Playoffs, bem como em situações físicas extremas (Back-to-Backs).

Este documento especifica a metodologia de diagnóstico e segmentação do modelo por regime de jogo para evitar previsões enviesadas.

---

## 🔍 REGIMES CRÍTICOS IDENTIFICADOS

```
                        ┌────────────────────────┐
                        │ REGIMES DE INFERÊNCIA  │
                        └───────────┬────────────┘
                                    │
           ┌────────────────────────┼────────────────────────┐
           ▼                        ▼                        ▼
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│  Sazonalidade       │  │  Desgaste Físico    │  │  Localidade / Odds  │
│  (Regular vs Post)  │  │  (B2B vs Rested)    │  │  (Home vs Away EV)  │
└─────────────────────┘  └─────────────────────┘  └─────────────────────┘
```

### 1. Temporada Regular vs. Playoffs (Post-Season)
- **Diferença Dinâmica:** Nos playoffs, a rotação de jogadores diminui (as estrelas jogam mais minutos), o ritmo de jogo (Pace) abranda e a intensidade defensiva aumenta.
- **Ajuste Técnico:** O modelo baseline deve incluir um indicador binário `is_playoffs`. Features de volume estatístico dos últimos 5 jogos devem ter pesos rebaixados em favor de métricas históricas de confronto direto (head-to-head matchup).

### 2. Efeito Back-to-Back (B2B) e Viagem (Rest vs. Fatigue)
- **Diferença Dinâmica:** Equipes jogando a segunda noite de um B2B fora de casa sofrem uma queda drástica de acerto de arremessos de quadra no 4º quarto.
- **Ajuste Técnico:** O pipeline de features calcula a `rest_diff` (diferença de dias de descanso entre a equipe da casa e visitante) e a distância terrestre percorrida nas últimas 72 horas.

### 3. Favoritos Rígidos vs. Equilíbrio (Odds Regime)
- **Odds Baixas (1.10 - 1.30):** O mercado é historicamente super-eficiente. O edge nestas odds é mínimo.
- **Odds Altas / Underdogs (2.50+):** Maior variância, onde a calibração isotônica é crucial para evitar viés de sobre-otimismo em zebras irreais.

---

## 🛠️ MÉTRICAS DE DIAGNÓSTICO RETROSPECTIVO (EXEMPLO)

Ao executar a avaliação cruzada do modelo histórico, a suíte de diagnóstico gera o seguinte relatório de erros segmentado por regime:

| Regime de Jogo | N (Jogos) | Brier Score | ROC-AUC | Viés de Calibração |
|----------------|-----------|-------------|---------|---------------------|
| Geral | 5820 | 0.198 | 0.582 | +1.2% (sobre-otimista) |
| Casa (Favorito) | 2100 | 0.182 | 0.590 | -0.5% (equilibrado) |
| Fora (B2B) | 950 | 0.224 | 0.535 | +4.8% (alto erro) |
| Playoffs | 420 | 0.201 | 0.565 | +2.1% (favoritos super-estimados) |

*Ação Corretiva baseada no relatório:* Sempre que o modelo avaliar um time visitante em regime B2B, a probabilidade crua calculada pelo XGBoost é calibrada com peso adicional para o time adversário, mitigando o viés identificado de +4.8%.
