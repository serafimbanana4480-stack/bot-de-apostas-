# 42_Player_Props — INDEX

**ID:** `SEC-42` | **Fase:** #phase/6 | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Expandir para mercados de Player Props NBA (pontos, ressaltos, assistências) como primeiro novo mercado após validação de Moneyline/Spread. Requer pipeline dedicado porque as features e os modelos são diferentes.

---

## 2. PORQUE PLAYER PROPS

- Menor eficiência de mercado que Moneyline
- Mais dados disponíveis (estatísticas individuais)
- Menor correlação com mercados principais (diversificação)
- Líquido suficiente na Betfair para execução

---

## 3. CICLO DE VALIDAÇÃO

O mesmo rigor do MVP aplica-se:
1. Dados históricos de player props (2 épocas mínimo)
2. Feature engineering dedicado (features de jogador, não equipa)
3. Modelo XGBoost separado
4. Purged CV dedicado
5. Backtest com slippage maior (1.0%)
6. Paper trading (1 mês)
7. Micro banca dedicada (separada da banca principal)

---

## 4. DOCUMENTAÇÃO DETALHADA

- [[42_Player_Props/PIPELINE_PROPS]] → Pipeline geral de player props
- [[42_Player_Props/DIFERENCAS_TEAM_VS_PLAYER]] → Diferenças fundamentais entre team e player props
- [[42_Player_Props/FEATURES_JOGADOR]] → Feature engineering específico para jogadores
- [[42_Player_Props/MODELACAO_PLAYER_PROPS]] → Modelagem XGBoost para player props
- [[42_Player_Props/LIQUIDEZ_EXECUCAO]] → Liquidez e estratégias de execução
- [[42_Player_Props/RISCOS_ESPECIFICOS]] → Gestão de riscos específicos (lesões, minutos, role changes)
- [[42_Player_Props/BACKTESTING_PLAYER_PROPS]] → Backtesting específico para player props
- [[42_Player_Props/CALIBRACAO_PROBABILIDADES]] → Calibração por linha e tipo de jogador
- [[42_Player_Props/MATCHUP_ANALYSIS]] → Análise de matchup head-to-head
- [[42_Player_Props/USAGE_ROLE_CHANGES]] → Usage rate e deteção de role changes

---

## 5. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[23_Scaling/INDEX]] → Eixo de expansão de mercados
