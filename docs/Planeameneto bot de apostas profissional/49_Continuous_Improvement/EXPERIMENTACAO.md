# EXPERIMENTACAO — Experimentação e Testes

**ID:** `CI-004` | **Fase:** #phase/1-15 | **Owner:** Product Manager | **Status:** #status/pending

---

## 1. OBJETIVO

Estabelecer um framework estruturado para experimentação no sistema de value betting, incluindo A/B testing, feature flags e testes controlados, permitindo validar hipóteses e melhorias com segurança baseada em dados.

---

## 2. CONTEXTO

No value betting, experimentação é crucial porque:
- O mercado é dinâmico e o que funciona hoje pode não funcionar amanhã
- Pequenas mudanças podem ter grande impacto financeiro
- É necessário validar antes de implementar em produção
- A variância pode mascarar o efeito real de mudanças

Sem experimentação controlada:
- Mudanças são implementadas baseadas em intuição
- É impossível saber o que causa melhorias/pioras
- Risco de degradação do sistema
- Perda de oportunidades de otimização

---

## 3. TIPOS DE EXPERIMENTAÇÃO

### 3.1 A/B Testing

**Definição:** Comparar duas versões (A = controle, B = variante) para determinar qual performa melhor.

**Quando usar:**
- Testar novos algoritmos de value detection
- Comparar diferentes estratégias de bankroll
- Avaliar mudanças em thresholds
- Testar novas features de UX

**Requisitos:**
- Tráfego suficiente para significância estatística
- Capacidade de isolar variáveis
- Métricas claras de sucesso
- Período de teste adequado

**Exemplo:**
- Grupo A (50%): Threshold de value = 2%
- Grupo B (50%): Threshold de value = 3%
- Métrica: ROI após 1000 apostas por grupo
- Duração: 2 semanas

---

### 3.2 Feature Flags

**Definição:** Capacidade de ligar/desligar funcionalidades sem deploy.

**Quando usar:**
- Rollout gradual de novas features
- Testes em produção com risco controlado
- Desligar features rapidamente se problemas
- Testar com subconjunto de utilizadores

**Tipos de Feature Flags:**
- **Release flags:** Para rollout gradual
- **Ops flags:** Para controle operacional
- **Experiment flags:** Para A/B testing
- **Permission flags:** Para acesso controlado

**Exemplo:**
```python
if feature_flag_enabled("new_basketball_strategy", user_id):
    use_new_strategy()
else:
    use_legacy_strategy()
```

---

### 3.3 Canary Deployments

**Definição:** Lançar nova versão para pequena percentagem de tráfego antes de rollout completo.

**Quando usar:**
- Deploy de versões major
- Mudanças arquiteturais
- Integrações com novas APIs
- Mudanças de alto risco

**Processo:**
1. Deploy para 1% do tráfego
2. Monitorizar métricas por 1 hora
3. Se OK, aumentar para 5%
4. Monitorizar por 4 horas
5. Se OK, aumentar para 25%
6. Monitorizar por 1 dia
7. Se OK, rollout completo

---

### 3.4 Shadow Mode

**Definição:** Executar novo sistema em paralelo com o antigo, mas sem afetar produção.

**Quando usar:**
- Testar novos modelos de ML
- Validar novos algoritmos
- Comparar performance sem risco
- Coletar dados para treinamento

**Processo:**
- Sistema antigo: Executa apostas reais
- Sistema novo: Processa mesmo input, mas não executa
- Comparar resultados após período de teste
- Decidir se migrar ou não

---

### 3.5 Backtesting

**Definição:** Testar estratégias com dados históricos.

**Quando usar:**
- Validar novas estratégias antes de produção
- Comparar diferentes abordagens
- Otimizar parâmetros
- Estimar performance esperada

**Limitações:**
- Não garante performance em live
- Overfitting é risco
- Dados históricos podem não representar futuro
- Custos de transação não sempre incluídos

---

## 4. FRAMEWORK DE EXPERIMENTAÇÃO

### 4.1 Fase 1: Planeamento

**1.1 Definir Hipótese**

Formato: "Se [mudança], então [resultado esperado] porque [razão]"

Exemplos:
- "Se aumentarmos threshold de value de 2% para 3%, então ROI aumentará de 2.5% para 3.0% porque filtraremos apostas de baixa qualidade"
- "Se implementarmos modelo de ML para ténis, então ROI para ténis aumentará de 1.5% para 2.5% porque o modelo captura padrões não lineares"

**1.2 Definir Métricas de Sucesso**

**Métrica Primária:**
- Deve ser diretamente impactada pela mudança
- Ex: ROI, Hit Rate, Latency

**Métricas Secundárias:**
- Impactos colaterais
- Ex: Volume de apostas, Error rate, CPU usage

**Guardrail Metrics:**
- Não devem ser degradadas
- Ex: Maximum Drawdown, Bankroll

**1.3 Definir Tamanho da Amostra**

Cálculo baseado em:
- Nível de confiança (tipicamente 95%)
- Poder estatístico (tipicamente 80%)
- Efeito mínimo detectável
- Variância esperada

**Regra prática:**
- Para ROI: Mínimo 1000 apostas por grupo
- Para latency: Mínimo 10,000 medições
- Para error rate: Mínimo 100,000 operações

**1.4 Definir Duração**

Baseado em:
- Tamanho da amostra necessário
- Velocidade de coleta de dados
- Variabilidade do sistema
- Risco de mudanças externas

**Durações típicas:**
- Testes rápidos: 1-3 dias
- Testes normais: 1-2 semanas
- Testes longos: 1 mês

---

### 4.2 Fase 2: Implementação

**2.1 Isolar Variáveis**

- Apenas uma mudança por experimento
- Controlar fatores externos (período do dia, dia da semana)
- Usar randomização para grupos

**2.2 Implementar Feature Flag**

```python
# Exemplo de implementação
class FeatureFlag:
    def __init__(self, name, rollout_percentage=0):
        self.name = name
        self.rollout_percentage = rollout_percentage

    def is_enabled(self, user_id):
        if self.rollout_percentage == 0:
            return False
        if self.rollout_percentage == 100:
            return True
        hash_value = hash(user_id + self.name) % 100
        return hash_value < self.rollout_percentage
```

**2.3 Logging de Experimento**

- Registrar para cada evento: grupo (A/B), timestamp, métricas
- Armazenar em banco de dados dedicado
- Garantir integridade dos dados

**2.4 Testes de Sanity**

- Verificar se grupos são balanceados
- Verificar se feature flag funciona
- Verificar se logging está correto

---

### 4.3 Fase 3: Execução

**3.1 Monitorização em Tempo Real**

- Dashboards específicos para experimento
- Alertas se métricas de guardrail forem violadas
- Capacidade de parar experimento imediatamente

**3.2 Checkpoints**

- Revisões periódicas (diária ou semanal)
- Decisão de continuar/parar/ajustar
- Documentar observações

**3.3 Gerenciamento de Risco**

- Ter rollback plan pronto
- Limitar exposição financeira
- Poder parar a qualquer momento

---

### 4.4 Fase 4: Análise

**4.1 Análise Estatística**

**Teste de Significância:**
- Para métricas binárias: Chi-square test
- Para métricas contínuas: T-test ou Mann-Whitney
- Para séries temporais: Time-series analysis

**Intervalo de Confiança:**
- Calcular IC de 95%
- Se IC não inclui 0, resultado é significativo

**Tamanho do Efeito:**
- Cohen's d para métricas contínuas
- Odds ratio para métricas binárias
- Avaliar se é praticamente significativo

**4.2 Segmentação**

Analisar resultados por segmentos:
- Por desporto
- Por tipo de aposta
- Por bookmaker
- Por período do dia
- Por nível de stake

**4.3 Análise de Causa-Raiz**

Se resultado inesperado:
- Investigar por que aconteceu
- Verificar se há bugs
- Analisar outliers
- Revisar hipótese

---

### 4.5 Fase 5: Decisão

**5.1 Critérios de Sucesso**

- Melhoria estatisticamente significativa (p < 0.05)
- Efeito praticamente significativo (> X% de melhoria)
- Sem degradação de guardrail metrics
- ROI positivo após custos de implementação

**5.3 Possíveis Decisões**

**Rollout Completo:**
- Se sucesso claro e sem riscos
- Remover feature flag
- Documentar lições aprendidas

**Rollout Parcial:**
- Se sucesso mas com algumas reservas
- Manter feature flag com rollout maior
- Continuar monitorização

**Manter em Teste:**
- Se resultados inconclusivos
- Aumentar duração ou tamanho da amostra
- Ajustar experimento

**Rejeitar:**
- Se falha ou sem melhoria
- Rollback completo
- Documentar por que falhou
- Não repetir mesmo erro

**Iterar:**
- Se direção promissora mas precisa de ajustes
- Modificar hipótese
- Criar novo experimento

---

## 5. EXPERIMENTOS COMUNS

### 5.1 Experimento 1: Otimização de Thresholds

**Hipótese:** Aumentar threshold de value de 2% para 3% aumentará ROI

**Design:**
- Grupo A: Threshold = 2%
- Grupo B: Threshold = 3%
- Amostra: 1000 apostas por grupo
- Duração: 2 semanas
- Métrica primária: ROI

**Resultados Esperados:**
- ROI aumenta de 2.5% para 3.0%
- Volume de apostas reduz 10-20%
- CLV mantido estável

---

### 5.2 Experimento 2: Novo Modelo ML

**Hipótese:** Modelo de ML para ténis superará modelo estatístico atual

**Design:**
- Shadow mode (não afeta produção)
- Comparar previsões vs resultados
- Período: 1 mês
- Métricas: Prediction accuracy, ROI simulado

**Resultados Esperados:**
- Accuracy aumenta 5%
- ROI simulado aumenta 0.5-1.0%

---

### 5.3 Experimento 3: Mudança de Stake Sizing

**Hipótese:** Kelly Criterion adaptado superará fixed fractional

**Design:**
- Grupo A: Fixed fractional (1% do bankroll)
- Grupo B: Kelly Criterion adaptado
- Amostra: 500 apostas por grupo
- Duração: 1 mês
- Métricas: ROI, Maximum Drawdown, Sharpe Ratio

**Resultados Esperados:**
- ROI similar ou maior
- Drawdown menor
- Sharpe Ratio maior

---

### 5.4 Experimento 4: Nova Bookmaker

**Hipótese:** Integração com nova bookmaker aumentará oportunidades de value

**Design:**
- Canary deployment (10% do tráfego)
- Monitorizar por 1 semana
- Métricas: Volume de apostas, ROI, Error rate

**Resultados Esperados:**
- Volume aumenta 15%
- ROI mantido
- Error rate < 2%

---

## 6. BOAS PRÁTICAS

### 6.1 Princípios

**1. Uma Variável por Vez**
- Não testar múltiplas mudanças simultaneamente
- Se necessário, usar fatorial design

**2. Significância Estatística**
- Não tomar decisões com dados insuficientes
- Calcular tamanho da amostra antes

**3. Prudência Financeira**
- Limitar exposição durante testes
- Usar stakes menores em experimentos

**4. Documentação Completa**
- Documentar hipótese, design, resultados
- Armazenar dados para reanálise

**5. Iteração Rápida**
- Testes pequenos e frequentes
- Aprender rápido, falhar barato

---

### 6.2 Anti-Patterns

**❌ Não fazer:**
- Testar em produção sem feature flags
- Parar testes cedo baseado em resultados parciais
- Ignorar significância estatística
- Testar múltiplas variáveis simultaneamente
- Não documentar resultados
- Repetir testes que já falharam sem mudanças

**✅ Fazer:**
- Calcular tamanho da amostra antes
- Usar grupos balanceados
- Monitorizar guardrail metrics
- Ter rollback plan
- Documentar tudo
- Aprender com falhas

---

## 7. FERRAMENTAS

### 7.1 Feature Flag Systems

**Opções:**
- LaunchDarkly (comercial)
- Unleash (open source)
- Firebase Remote Config
- Implementação customizada (para começar)

**Requisitos:**
- API para verificar flags
- Console de gestão
- Integração com logging
- Rollback instantâneo

---

### 7.2 Análise Estatística

**Ferramentas:**
- Python: scipy, statsmodels
- R: pacotes de estatística
- Excel/Google Sheets: para testes simples
- Ferramentas de A/B testing: Optimizely, VWO

---

### 7.3 Dashboards

**Ferramentas:**
- Grafana
- Metabase
- Tableau
- Looker

**Requisitos:**
- Visualização em tempo real
- Alertas automáticos
- Comparação A/B
- Exportação de dados

---

## 8. DOCUMENTAÇÃO DE EXPERIMENTOS

### 8.1 Template de Experimento

```markdown
# Experimento: [Título]

**ID:** EXP-XXX
**Data Início:** DD/MM/AAAA
**Responsável:** [Nome]
**Status:** [Planejando/Em Andamento/Concluído]

## Hipótese
[Descrição da hipótese]

## Design
- **Grupo A:** [Descrição]
- **Grupo B:** [Descrição]
- **Amostra:** [Tamanho]
- **Duração:** [Período]

## Métricas
- **Primária:** [Métrica]
- **Secundárias:** [Lista]
- **Guardrails:** [Lista]

## Implementação
- [Detalhes técnicos]
- [Feature flag]
- [Logging]

## Resultados
- [Dados coletados]
- [Análise estatística]
- [Gráficos]

## Conclusão
- [Sucesso/Falha/Inconclusivo]
- [Decisão]
- [Próximos passos]

## Lições Aprendidas
- [Key takeaways]
```

---

## 9. GOVERNANÇA

### 9.1 Aprovação de Experimentos

**Experimentos de Baixo Risco:**
- Aprovação: Product Manager
- Exemplo: Pequenas mudanças de threshold

**Experimentos de Médio Risco:**
- Aprovação: Product Manager + Architect
- Exemplo: Novo modelo ML em shadow mode

**Experimentos de Alto Risco:**
- Aprovação: Product Manager + Architect + Stakeholder
- Exemplo: Mudança major de arquitetura

---

### 9.2 Revisão de Resultados

Todos os experimentos devem ser revisados em:
- Retrospectiva semanal (experimentos ativos)
- Retrospectiva mensal (experimentos concluídos)

---

## 10. LINKS CRUZADOS

- [[49_Continuous_Improvement/INDEX]] ← Secção mãe
- [[49_Continuous_Improvement/CICLO_PDCA]] → Experimentos no ciclo DO
- [[49_Continuous_Improvement/METRICAS_E_KPIS]] → Métricas para experimentos
- [[49_Continuous_Improvement/FEEDBACK_LOOPS]] → Coleta de dados
- [[49_Continuous_Improvement/LEARNING_ORGANIZATION]] → Documentação de lições