# FILOSOFIA_MVP — Validação Antes da Complexidade

**ID:** `DEC-001` | **Tipo:** #type/decision | **Fase:** #phase/1 | **Status:** #status/completed | **Owner:** Chief Systems Architect

---

## 1. OBJETIVO

Definir a filosofia de desenvolvimento do projeto baseada em pragmatismo e validação incremental. A filosofia central é: **nunca sacrificar pragmatismo por elegância técnica**. O objetivo não é construir a arquitetura mais bonita ou sofisticada, mas sim provar que existe vantagem matemática real (edge) com o menor investimento possível, e depois escalar com base em resultados reais. Esta abordagem minimiza risco, acelera time-to-market, e garante que cada incremento de complexidade é justificado por valor comprovado.

---

## 2. DEFINIÇÃO DE MVP

### 2.1 O Que é MVP?

MVP (Minimum Viable Product) é a versão mais simples do produto que ainda permite validar a hipótese central. No contexto deste projeto, a hipótese central é: **"É possível obter edge consistente em apostas NBA usando machine learning?"**

**Características do MVP:**
- **Mínimo:** Usa a menor quantidade de recursos possível
- **Viável:** Funciona e gera resultados mensuráveis
- **Produto:** Não é protótipo ou prova de conceito — é algo que pode ser usado em produção

### 2.2 O Que MVP NÃO É

MVP NÃO é:
- **Protótipo:** Código descartável que será reescrito
- **Prova de Conceito (PoC):** Demonstração técnica sem valor de negócio
- **Versão Beta:** Produto incompleto lançado para feedback
- **Código "rápido e sujo":** Código de baixa qualidade que será refeito

MVP É:
- **Código de produção:** Qualidade suficiente para uso real
- **Base iterativa:** Fundação sólida para melhorias futuras
- **Validação de hipótese:** Testa se a ideia funciona na prática
- **Simples mas robusto:** Sem complexidade desnecessária, mas com qualidade

---

## 3. POR QUE ESTA FILOSOFIA?

### 3.1 Problemas da Abordagem Alternativa

**Abordagem "Big Bang" (Construir Tudo Primeiro):**
- Construir arquitetura completa antes de validar edge
- Investir meses em microservices, streaming, multi-desporto
- Lançar só depois de 6-12 meses de desenvolvimento
- Descobrir que não há edge após investimento massivo

**Riscos:**
- **Perda de tempo:** Meses de trabalho em algo que não gera valor
- **Perda de dinheiro:** Custos de infraestrutura sem retorno
- **Complexidade desnecessária:** Sistemas complexos são difíceis de manter
- **Incapacidade de pivot:** Mudar direção é difícil com arquitetura complexa

### 3.1 Benefícios da Abordagem MVP

**Validação Rápida:**
- Testar hipótese em semanas, não meses
- Descobrir se há edge antes de investimento significativo
- Pivotar ou abandonar se hipótese é falsa

**Aprendizado Real:**
- Aprender com dados reais, não teoria
- Descobrir problemas que só aparecem em produção
- Iterar baseado em feedback do mercado

**Eficiência de Recursos:**
- Investir apenas no essencial inicialmente
- Escalar apenas após validação
- Minimizar custo de oportunidade

**Mentalidade de Melhoria Contínua:**
- Lançar com "bom o suficiente"
- Melhorar iterativamente baseado em dados
- Evitar análise paralysis

---

## 4. ALTERNATIVAS REJEITADAS E RAZÕES

| Alternativa | Rejeitada Porque | Risco Principal |
|-------------|------------------|-----------------|
| **Arquitetura microservices desde o início** | Complexidade desnecessária para um único modelo e dois mercados. Monólito modular é suficiente e mais simples. | Over-engineering, latência adicional, complexidade operacional |
| **Deep learning (LSTMs, Transformers) como baseline** | XGBoost com features bem construídas supera redes neurais em dados tabulares pequenos. Deep learning é overkill. | Overfitting, difícil de interpretar, treino mais lento |
| **Kafka + Flink para streaming** | Dados pré-jogo não precisam de streaming; batch a cada 5 minutos é suficiente. Streaming adiciona complexidade sem valor. | Complexidade operacional, custo adicional, manutenção difícil |
| **Multi-desporto desde o início** | Difunde recursos e impede validação rigorosa de edge em qualquer mercado. Foco em NBA primeiro. | Recursos divididos, validação diluída, tempo mais longo |
| **Kelly multivariado com matriz de covariância** | Overkill para início; limites de exposição simples são suficientes. Matriz de covariância é instável com poucos dados. | Overfitting, complexidade computacional, instabilidade |
| **Conformal prediction** | Adiado; calibração isotônica + thresholds de edge fornecem margem adequada inicial. Conformal adiciona complexidade sem valor imediato. | Complexidade adicional, overhead computacional |

---

## 5. FILOSOFIA EM 6 PASSOS

### Visão Geral

```
MVP SIMPLES → VALIDAÇÃO → LUCRO REAL → AUTOMAÇÃO → ESCALA → SOFISTICAÇÃO
```

Cada passo deve ser completamente validado antes de avançar para o próximo. Não saltar passos.

### Passo 1: MVP Simples (Meses 1-3)

**Objetivo:** Construir sistema funcional mínimo para validar hipótese.

**Escopo:**
- **Um desporto:** NBA (mercado líquido, dados abundantes)
- **Dois mercados:** Moneyline e Spread (mercados mais líquidos)
- **Um modelo:** XGBoost (baseline sólido e interpretável)
- **Dados gratuitos:** NBA API, scraping de odds públicas
- **Stack barato:** VPS básico (~50-80€/mês), PostgreSQL, Python

**Critérios de Sucesso:**
- Sistema gera sinais consistentemente
- Sinais são executáveis (não apenas teóricos)
- Métricas básicas são calculadas e monitorizadas

**Não Incluir:**
- Multi-desporto
- Modelos ensemble
- Streaming real-time
- Infraestrutura cloud enterprise
- Deep learning

### Passo 2: Validação (Meses 2-4)

**Objetivo:** Validar que o sistema tem edge real em dados históricos.

**Métodos:**
- **Purged walk-forward CV:** Validar que performance não é overfitting
- **Backtest com comissões e slippage:** Simular custos reais
- **Comparação com mercado:** CLV > 2%, Brier < mercado, ROI > 5%

**Critérios de Passagem:**
- CLV médio > 2% (modelo bate odds de fechamento)
- Brier Score < Brier Score do mercado
- ROI simulado > 5% após custos
- Sharpe Ratio > 0.5
- Drawdown máximo < 20%

**Se Falhar:**
- Investigar causas (overfitting, features ruins, dados ruins)
- Iterar no modelo ou features
- Não avançar até critérios serem atendidos

### Passo 3: Lucro Real (Meses 4-6)

**Objetivo:** Validar que edge histórico se traduz em lucro real.

**Fases:**
- **Paper trading (1 mês):** Executar sinais sem apostar dinheiro real. Medir fill rate, slippage real, latência.
- **Micro banca 500-1000€ (1 mês):** Apostar quantias pequenas. Validar que ROI real ≥ 50% ROI simulado.
- **Shadow mode multi-casa:** Comparar odds em múltiplas casas simultaneamente sem executar.
- **Tracking rigoroso de divergências:** Medir diferença entre backtest e real.

**Critérios de Passagem:**
- Divergência de ROI < 50%
- ROI real > 0%
- Fill rate > 70%
- Slippage < 2%
- CLV real > 1%

**Se Falhar:**
- Investigar causas de divergência
- Ajustar backtest para ser mais realista
- Não avançar até divergência ser aceitável

### Passo 4: Automação (Meses 6-12)

**Objetivo:** Automatizar execução para reduzir latência e slippage.

**Fases:**
- **One-click betting (deep links):** Reduzir tempo de execução manual de 60s para 10s
- **Execução automática Betfair API:** Só após 6 meses consecutivos de lucro real
- **CI/CD para modelos:** Automatizar deploy de novos modelos

**Critérios de Passagem:**
- Tempo de execução < 30 segundos
- Taxa de erro de execução < 1%
- Sistema de rollback funcional

**Pré-condições para Execução Automática:**
- 6 meses consecutivos de lucro real
- ROI real médio > 3%
- Circuit breakers testados e funcionais
- Monitorização completa implementada

### Passo 5: Escala (Meses 12-24)

**Objetivo:** Aumentar escala gradualmente baseado em performance.

**Fases:**
- **Aumentar banca gradualmente:** Só se ROI real > 3%. Aumentar 25% por mês máximo.
- **Adicionar mercados:** Player Props (após Moneyline/Spread validados)
- **Crescer base de subscritores tipster:** Se modelo tipster for lançado

**Critérios de Passagem:**
- ROI mantém-se > 3% com escala
- Slippage não aumenta significativamente com stake
- Limites de casa não são atingidos

**Se Falhar:**
- Reduzir escala
- Investigar efeitos de escala
- Não forçar escala se performance degrada

### Passo 6: Sofisticação (Meses 24+)

**Objetivo:** Adicionar sofisticação apenas após validação de MVP.

**Possíveis Adições:**
- **Modelos ensemble avançados:** Stacking, blending de múltiplos modelos
- **Feature store enterprise:** Sistema centralizado de features
- **Multi-exchange execution:** Executar em múltiplas exchanges simultaneamente
- **Infraestrutura institucional:** Cloud enterprise, monitoring avançado

**Critérios de Adição:**
- Cada adição deve ser justificada por melhoria mensurável
- Teste A/B antes de implementação completa
- ROI incremental > custo incremental

---

## 6. O QUE ACONTECE SE VIOLARMOS ESTA FILOSOFIA

### Cenário de Falha 1: Saltar para Automação Betfair no Mês 2

**Causa:** Impaciência, overconfiança, pressão para "ir mais rápido"

**Consequência:**
- Perdas rápidas devido a slippage real não modelado
- Erros de execução em escala (API bugs, timeouts)
- Incapacidade de debugar problemas complexos
- Perda de capital significativa

**Mitigação:**
- Circuit breakers automáticos (stop loss diário)
- Regra de progressão obrigatória (não saltar passos)
- Revisão obrigatória antes de cada fase

### Cenário de Falha 2: Adicionar NFL no Mês 3 Sem Validar NBA

**Causa:** Diversificação prematura, medo de "colocar todos os ovos no mesmo cesto"

**Consequência:**
- Recursos divididos (desenvolvimento, dados, execução)
- Nenhum mercado validado adequadamente
- Incapacidade de diagnosticar problemas (é NBA? NFL? Ambos?)
- Tempo mais longo para validar qualquer mercado

**Mitigação:**
- Regra absoluta: um mercado de cada vez
- Foco em validação rigorosa antes de expansão
- Documentação de sucesso antes de adicionar novo mercado

### Cenário de Falha 3: Implementar Deep Learning Antes de Validar XGBoost

**Causa:** "FOMO" de tecnologia, desejo de usar "state-of-the-art"

**Consequência:**
- Overfitting em dataset pequeno (NBA tem ~1500 jogos/ano)
- Dificuldade de interpretar por que modelo toma decisões
- Treino mais lento e mais complexo
- Melhoria marginal ou nula sobre XGBoost

**Mitigação:**
- Regra: começar com baseline simples (XGBoost)
- Só considerar deep learning após XGBoost ser validado e esgotado
- Comparação A/B obrigatória antes de substituição

---

## 7. MÉTRICAS DE ADESÃO

### Métricas de Progresso

| Métrica | Target | Como Medir | Frequência |
|---------|--------|------------|-----------|
| **Tempo até primeira aposta real** | < 4 meses | Data de primeira aposta micro-banca | Única |
| **Custo infraestrutura mês 1-3** | < 100€/mês | Faturas VPS + dados | Mensal |
| **Número de modelos em produção mês 6** | ≤ 2 | Contagem em [[30_Model_Registry/INDEX]] | Mensal |
| **Rácio complexidade/edge** | < 1 | Revisão mensal em reunião de estratégia | Mensal |
| **Tempo de iteração (feature → produção)** | < 2 semanas | Tempo desde ideia até deploy | Por feature |
| **Percentagem de features que melhoram modelo** | > 30% | Contagem de features testadas vs implementadas | Trimestral |

### Métricas de Qualidade

- **Cobertura de testes:** > 80% para código crítico
- **Documentação:** 100% de funções públicas documentadas
- **Reproducibilidade:** 100% de experimentos reproduzíveis
- **Monitorização:** 100% de componentes críticos monitorizados

---

## 8. DECISÕES DERIVADAS

As decisões específicas derivadas desta filosofia estão consolidadas em:
- [[01_Vision_And_Strategy/DECISOES_IRREVERSIVEIS]] - Registro de todas as decisões irreversíveis (DEC-002 a DEC-006)
- [[01_Vision_And_Strategy/TRADE_OFFS_ARQUITETURAIS]] - Trade-offs arquiteturais específicos

---

## 9. REVISÃO E GOVERNANÇA

### Revisão Obrigatória
- **Data da Decisão:** 2026-05-13
- **Revisão Obrigatória:** 2026-08-13 (trimestral)
- **Revisões subsequentes:** Trimestral

### Autoridade
- **Nunca invalidar sem aprovação do Chief Systems Architect**
- Alterações requerem justificação documentada
- Mudanças de direção requerem revisão de impacto

### Compliance
- Todos os desenvolvedores devem ler e entender esta filosofia
- Novos membros da equipa devem ser onboarded com esta filosofia
- Decisões arquiteturais devem ser referenciadas a esta filosofia

---

## 10. LINKS CRUZADOS

- [[01_Vision_And_Strategy/INDEX]] ← Secção mãe
- [[01_Vision_And_Strategy/DECISOES_IRREVERSIVEIS]] → Decisões irreversíveis específicas
- [[01_Vision_And_Strategy/TRADE_OFFS_ARQUITETURAIS]] → Trade-offs arquiteturais
- [[00_Master_Index/INDEX]] → Índice mestre do projeto
