# SLIPPAGE_TRACKING — Tracking de Slippage

**ID:** `EX-002` | **Fase:** Todas | **Owner:** Operations Lead | **Status:** #status/pending

---

## 1. OBJETIVO

Implementar um sistema sistemático de tracking e análise de slippage na execução de apostas. Slippage é a diferença entre a odd esperada (no momento do sinal) e a odd realmente obtida na execução. Slippage é um dos principais fatores que reduzem edge real vs edge simulado, e tracking sistemático é essencial para entender e mitigar este impacto. O objetivo não é apenas medir slippage, mas identificar causas raiz, implementar mitigações e otimizar o timing de execução.

---

## 2. DEFINIÇÕES FUNDAMENTAIS

### 2.1 O Que é Slippage

Slippage é a diferença percentual entre a odd no momento do sinal e a odd obtida na execução:

```
Slippage % = (Odd Obtida - Odd Esperada) / Odd Esperada × 100
```

Exemplo:
- Odd esperada no sinal: 2.00
- Odd obtida na execução: 1.95
- Slippage = (1.95 - 2.00) / 2.00 × 100 = -2.5%

Slippage negativo indica que obtivemos uma odd pior que o esperado (o cenário típico). Slippage positivo indica que obtivemos uma odd melhor (raro, mas possível).

### 2.2 Tipos de Slippage

**Slippage de Tempo:** Diferença causada pelo delay entre o sinal e a execução. Odds de mercados de apostas mudam continuamente, e quanto maior o delay, maior a probabilidade de slippage.

**Slippage de Liquidez:** Quando tentamos apostar um valor que excede a liquidez disponível a uma dada odd, a odd cai para acomodar o nosso stake. Isto é comum em mercados com baixa liquidez ou stakes grandes.

**Slippage de Cross-Market:** Quando executamos numa casa de apostas diferente da usada para gerar o sinal. Diferentes casas têm odds ligeiramente diferentes, e esta diferença é slippage.

**Slippage de Movimento de Mercado:** Movimentos rápidos de odds devido a notícias, lesões, ou grandes apostas de outros apostadores. Este tipo de slippage é imprevisível e difícil de mitigar.

---

## 3. MÉTRICAS DE SLIPPAGE

### 3.1 Métricas de Nível de Aposta

Cada aposta deve ter as seguintes métricas de slippage registadas:

- **slippage_pct:** Slippage percentual da aposta
- **slippage_abs:** Diferença absoluta em odd (Odd Obtida - Odd Esperada)
- **slippage_eur:** Impacto monetário do slippage (stake × slippage_pct)
- **execution_latency_seconds:** Tempo entre sinal e execução
- **liquidity_at_execution:** Liquidez disponível no momento da execução
- **market_movement_flag:** Flag se houve movimento significativo de odds

### 3.2 Métricas Agregadas

**Slippage Médio:** Média de slippage_pct de todas as apostas num período (ex: último dia, última semana). Target: < 1% slippage médio.

**Slippage P95/P99:** Percentis de slippage. P95 indica que 95% das apostas têm slippage abaixo deste valor. Target: P95 < 2%.

**Slippage por Mercado:** Slippage médio segmentado por tipo de mercado (Moneyline, Spread, Total). Alguns mercados naturalmente têm mais slippage (ex: Totais vs Moneyline).

**Slippage por Bookmaker:** Slippage médio por casa de apostas. Algumas casas têm execução mais rápida e menos slippage.

**Slippage por Hora do Dia:** Slippage médio por hora. Horas de pico (ex: início de jogos) podem ter mais volatilidade e slippage.

### 3.3 Métricas de Impacto Financeiro

**Perda por Slippage:** Soma de slippage_eur de todas as apostas. Quantifica quanto dinheiro foi perdido devido a slippage.

**ROI Real vs ROI Simulado:** ROI simulado usa odd esperada, ROI real usa odd obtida. A diferença é impacto de slippage e execution costs.

**Edge Erosão:** Percentagem de edge que é perdida devido a slippage. Se edge simulado é 5% e edge real é 3%, edge erosion é 40%.

---

## 4. CAUSAS DE SLIPPAGE

### 4.1 Latência de Execução

**Causa:** Delay entre geração do sinal e execução da aposta. Durante este delay, odds podem mudar.

**Fontes de Latência:**
- Latência de API da casa de apostas (tempo para receber odds)
- Latência de processamento do sinal (validação, cálculo de stake)
- Latência de aprovação manual (se execução não é automática)
- Latência de rede entre servidor e casa de apostas
- Latência de confirmação da aposta

**Mitigação:**
- Reduzir latência de API usando endpoints otimizados
- Processamento paralelo de validações
- Execução automática sem aprovação manual
- Servidor geograficamente próximo da casa de apostas
- Websockets para odds em tempo real (quando disponível)

### 4.2 Baixa Liquidez

**Causa:** Stake excede liquidez disponível a uma dada odd. Quando isso acontece, a odd cai para acomodar o stake.

**Sinais de Baixa Liquidez:**
- Mercado com pouco volume total
- Stake grande relativo ao volume disponível
- Mercado de nicho (ex: player props vs principais)
- Momentos de baixa atividade (ex: fora de horário de jogos)

**Mitigação:**
- Limitar stake baseado em liquidez disponível
- Evitar mercados com baixa liquidez
- Execução em fatias (split stake em múltiplas apostas menores)
- Usar ordens de tipo "fill-or-kill" para rejeitar se odd cai muito

### 4.3 Movimento de Mercado

**Causa:** Odds mudam rapidamente devido a eventos externos. Notícias de lesões, grandes apostas de whales, ou mudanças nas condições do jogo podem causar movimentos rápidos.

**Sinais de Movimento:**
- Mudança de odd > 2% em < 1 minuto
- Aumento súbito de volume
- Notícias de lesões ou lineup changes
- Início ou fim de jogo

**Mitigação:**
- Execução mais rápida possível para minimizar exposição
- Alertas de movimentos de mercado para pausar execução durante alta volatilidade
- Filtro de notícias para pausar antes de executar se há lesão recente
- Limitar execução em momentos de alta volatilidade (ex: 5 minutos antes do jogo)

### 4.4 Cross-Market Slippage

**Causa:** Sinal é gerado baseado em odds de uma casa, mas execução é feita em outra. Diferentes casas têm odds ligeiramente diferentes.

**Sinais:**
- Usar Pinnacle para sinal, mas executar em Betfair
- Usar múltiplas fontes de odds no sinal, mas executar apenas numa

**Mitigação:**
- Usar a mesma casa para sinal e execução quando possível
- Se usar casas diferentes, ajustar sinal para incluir diferença esperada
- Monitorizar slippage por par de casas para entender padrões

---

## 5. SISTEMA DE TRACKING

### 5.1 Registro de Slippage

Cada aposta deve registrar todas as métricas de slippage relevantes:

```python
class BetExecution:
    def __init__(self, signal, execution_result):
        self.signal_odd = signal.odd
        self.executed_odd = execution_result.odd
        self.slippage_pct = (self.executed_odd - self.signal_odd) / self.signal_odd * 100
        self.slippage_abs = self.executed_odd - self.signal_odd
        self.slippage_eur = signal.stake * self.slippage_pct / 100
        self.execution_latency = execution_result.timestamp - signal.timestamp
        self.liquidity = execution_result.liquidity
        self.market_movement = execution_result.market_movement
```

### 5.2 Dashboard de Slippage

Dashboard em tempo real mostrando:
- Slippage médio das últimas 24h
- Slippage por mercado (Moneyline, Spread, Total)
- Slippage por bookmaker
- Slippage por hora do dia
- Distribuição de slippage (histograma)
- Perda total por slippage

### 5.3 Alertas de Slippage

Configurar alertas automáticos quando:
- Slippage médio > 2% nas últimas 24h
- Slippage P95 > 3% nas últimas 24h
- Perda por slippage > €50 num dia
- Slippage em aposta específica > 5%

---

## 6. ESTRATÉGIAS DE MITIGAÇÃO

### 6.1 Otimização de Timing

**Execução Imediata:** Executar sinais imediatamente após geração, sem delay de aprovação manual. Isto minimiza slippage de tempo.

**Janela de Execução:** Definir janela de tempo aceitável para execução (ex: 30 segundos). Se não executar dentro da janela, rejeitar sinal.

**Horas de Baixa Volatilidade:** Preferir execução em horas de baixa volatilidade quando possível (ex: evitar 5 minutos antes do jogo).

### 6.2 Otimização de Stake

**Stake Baseado em Liquidez:** Calcular stake máximo baseado em liquidez disponível. Se liquidez é €100 a odd 2.00, limitar stake a €50 (50% da liquidez).

**Split de Stake:** Para stakes grandes, dividir em múltiplas apostas menores ao longo do tempo para minimizar impacto em uma única execução.

**Dynamic Sizing:** Ajustar stake baseado em slippage histórico do mercado. Se mercado tem alto slippage médio, reduzir stake.

### 6.3 Seleção de Mercados

**Evitar Mercados de Baixa Liquidez:** Listar mercados com baixa liquidez e evitá-los ou reduzir stakes significativamente.

**Priorizar Mercados de Alta Liquidez:** Focar execução em mercados com liquidez alta e slippage histórico baixo.

**Monitoramento de Liquidez:** Antes de executar, verificar liquidez atual. Se abaixo de threshold, rejeitar sinal.

### 6.4 Melhoria de Infraestrutura

**APIs Mais Rápidas:** Usar APIs WebSocket quando disponível para odds em tempo real e execução mais rápida.

**Servidores Próximos:** Hospedar servidores geograficamente próximos das casas de apostas para reduzir latência de rede.

**Conexões Dedicadas:** Se volume for alto, considerar conexões dedicadas ou VPNs para garantir latência consistente.

---

## 7. ANÁLISE E INVESTIGAÇÃO

### 7.1 Análise de Causa Raiz

Quando slippage é consistentemente alto, investigar:
- Qual é a fonte predominante de slippage (tempo, liquidez, movimento)?
- Há padrões por hora do dia ou por mercado?
- Alguma casa de apostas tem consistentemente mais slippage?
- Há correlação com latência de execução?

### 7.2 A/B Testing

Testar diferentes estratégias de mitigação:
- Comparar execução manual vs automática
- Comparar diferentes casas de apostas
- Testar diferentes janelas de execução
- Testar diferentes estratégias de stake sizing

### 7.3 Relatórios Periódicos

Gerar relatórios semanais/mensais de slippage:
- Tendência de slippagem médio ao longo do tempo
- Identificação de outliers (apostas com slippage excepcionalmente alto)
- Recomendações de melhoria baseadas em análise

---

## 8. BACKLOG TÉCNICO

- [ ] Implementar métricas de slippage em todas as execuções
- [ ] Criar dashboard de slippagem em tempo real
- [ ] Configurar alertas de slippagem alto
- [ ] Implementar análise de causa raiz automática
- [ ] Configurar A/B testing de estratégias de mitigação
- [ ] Criar relatórios periódicos de slippagem
- [ ] Implementar otimização de stake baseado em liquidez
- [ ] Adicionar filtros de mercado por liquidez

---

## 9. LINKS CRUZADOS

- [[09_Execution_System/INDEX]] ← Secção mãe
- [[09_Execution_System/EXECUCAO_AUTOMATICA]] → Detalhes de execução automática
- [[08_Risk_Management/EXPOSURE_LIMITS]] → Limites de exposição e stake
- [[10_Monitoring/METRICAS_DETALHADAS]] → Métricas de monitoring
