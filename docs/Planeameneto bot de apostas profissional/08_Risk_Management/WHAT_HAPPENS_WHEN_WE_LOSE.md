# WHAT HAPPENS WHEN WE LOSE — Cenários de Stress e Recuperação

**ID:** `SEC-08-02` | **Status:** #status/pending | **Versão:** `2.0.0-STRESS`

---

## 1. OBJETIVO

Documentar cenários de stress e protocolos de recuperação para períodos de perda inevitáveis em sistemas probabilísticos.

---

## 2. PRINCÍPIO FUNDAMENTAL

**Perdas são inevitáveis em qualquer sistema probabilístico. O que importa é como reagimos.**

Um drawdown de 20% não é falência — é parte da variação normal. O que separa sistemas robustos de sistemas frágeis é a capacidade de sobreviver a esses períodos e recuperar.

---

## 3. CENÁRIOS DE STRESS

### 3.1 Cenário 1: Drawdown de 20% em 30 Dias

**Descrição:**
- Banca cai de 10.000€ para 8.000€ em 30 dias
- Loss streak de 15 apostas consecutivas
- CLV médio cai para 0% no período

**Causas Possíveis:**
- Mudança de regime no mercado (ex: início de playoffs)
- Modelo degradado (concept drift)
- Ruído estatístico normal (variação esperada)

**Protocolo de Resposta:**

**Fase 1: Imediata (0-24 horas)**
1. Pausar todas as apostas não-garantidas
2. Ativar circuit breaker global
3. Analisar métricas dos últimos 30 dias
4. Identificar root cause (modelo vs mercado vs ruído)

**Fase 2: Análise (1-3 dias)**
1. Comparar CLV vs performance real
2. Verificar se modelo está calibrado
3. Analisar distribuição de perdas (skewness, kurtosis)
4. Verificar se há data leakage novo

**Fase 3: Decisão (3-7 dias)**
- **Se for ruído normal:** Retomar com stake reduzido (50%)
- **Se for modelo degradado:** Retreinar modelo antes de retomar
- **Se for regime change:** Ajustar features para novo regime

**Fase 4: Recuperação (7-30 dias)**
1. Retomar gradualmente (shadow mode → 25% → 50% → 100%)
2. Monitorizar CLV e performance diariamente
3. Se drawdown atingir 25%, pausar novamente
4. Objetivo: Recuperar para 9.500€ em 60 dias

### 3.2 Cenário 2: Perda de 3 Desportos Simultaneamente

**Descrição:**
- NBA: -10% em 2 semanas
- Football: -8% em 2 semanas
- MMA: -12% em 2 semanas
- Drawdown global: -15%

**Causas Possíveis:**
- Correlação não antecipada entre desportos
- Evento macro (ex: pandemia, lockdown)
- Falha de infraestrutura comum

**Protocolo de Resposta:**

**Fase 1: Imediata (0-12 horas)**
1. Pausar desporto com maior drawdown (MMA)
2. Reduzir exposição dos outros 50%
3. Verificar se há causa comum
4. Ativar alerta de nível vermelho

**Fase 2: Análise (12-48 horas)**
1. Calcular correlação entre desportos no período
2. Verificar se há evento macro afetando todos
3. Analisar se há falha de dados comum
4. Revisar limites de exposição

**Fase 3: Ajuste (2-7 dias)**
1. Se correlação > 0.5: Revisar diversificação
2. Se evento macro: Pausar até estabilização
3. Se falha de dados: Corrigir antes de retomar
4. Ajustar limites de exposição por desporto

### 3.3 Cenário 3: Modelo Falha Completamente (CLV Negativo)

**Descrição:**
- CLV médio cai para -2% por 50 apostas consecutivas
- ROI simulado no set de validação cai para 0%
- Feature importance muda drasticamente

**Causas Possíveis:**
- Concept drift severo
- Bookmaker melhorou modelo significativamente
- Dados corrompidos ou bug no pipeline

**Protocolo de Resposta:**

**Fase 1: Imediata (0-6 horas)**
1. Pausar todas as apostas do desporto afetado
2. Verificar integridade dos dados
3. Rodar diagnóstico completo do pipeline
4. Backup do estado atual do modelo

**Fase 2: Investigação (6-24 horas)**
1. Comparar features atuais vs features históricas
2. Verificar se há anomalias nos dados
3. Testar modelo em set de validação mais recente
4. Comparar com modelo baseline (versão anterior)

**Fase 3: Correção (1-3 dias)**
- **Se for bug:** Corrigir e retomar
- **Se for concept drift:** Retreinar com dados recentes
- **Se for bookmaker melhorou:** Investigar novas features
- **Se não for recuperável:** Considerar desligar desporto

### 3.4 Cenário 4: Falha de Infraestrutura Crítica

**Descrição:**
- Betfair API fica offline por 24 horas
- Banco de dados fica corrompido
- Servidor de ML cai durante treino

**Protocolo de Resposta:**

**Fase 1: Imediata (0-1 hora)**
1. Pausar todas as apostas
2. Ativar modo manual de emergência
3. Notificar stakeholders
4. Iniciar diagnóstico

**Fase 2: Recuperação (1-24 horas)**
1. Restaurar backup mais recente
2. Verificar integridade dos dados
3. Testar APIs externas
4. Revalidar modelo

**Fase 3: Retorno (24-48 horas)**
1. Retomar em shadow mode
2. Validar consistência de dados
3. Retomar gradualmente
4. Documentar incidente

---

## 4. PROTOCOLO DE RECUPERAÇÃO PADRÃO

### 4.1 Checklist Imediato (0-1 hora)

```
[ ] Pausar todas as apostas
[ ] Ativar circuit breaker global
[ ] Calcular drawdown atual
[ ] Identificar desportos mais afetados
[ ] Enviar alerta a stakeholders
[ ] Iniciar logging detalhado
```

### 4.2 Checklist de Análise (1-24 horas)

```
[ ] Analisar CLV dos últimos 30 dias
[ ] Comparar CLV vs performance real
[ ] Verificar calibração do modelo
[ ] Analisar distribuição de perdas
[ ] Verificar integridade dos dados
[ ] Comparar com histórico de drawdowns
[ ] Identificar root cause
```

### 4.3 Checklist de Decisão (24-72 horas)

```
[ ] Classificar causa (ruído vs modelo vs mercado)
[ ] Definir estratégia de recuperação
[ ] Ajustar limites de exposição
[ ] Planejar retomada gradual
[ ] Documentar plano de ação
[ ] Obter aprovação manual se necessário
```

### 4.4 Checklist de Retomada (3-30 dias)

```
[ ] Iniciar shadow mode
[ ] Validar performance em shadow mode
[ ] Retomar com 25% da banca
[ ] Monitorizar métricas diariamente
[ ] Aumentar gradualmente (25% → 50% → 100%)
[ ] Se drawdown adicional > 5%, pausar
[ ] Documentar lições aprendidas
```

---

## 5. MÉTRICAS DE STRESS

### 5.1 Métricas a Monitorizar Durante Drawdown

```python
def get_stress_metrics():
    """
    Obtém métricas de stress do sistema.
    """
    return {
        'global_drawdown': calculate_global_drawdown(),
        'loss_streak': get_global_loss_streak(),
        'clv_trend': get_clv_trend(days=30),
        'win_rate_last_30': calculate_win_rate(days=30),
        'volatility': calculate_volatility(days=30),
        'correlation_sports': calculate_sport_correlation(),
        'model_calibration': check_model_calibration(),
        'data_integrity': check_data_integrity(),
        'api_health': check_external_apis()
    }
```

### 5.2 Thresholds de Stress

| Nível de Stress | Drawdown | Ação |
|-----------------|----------|------|
| **Verde** (Normal) | < 10% | Operação normal |
| **Amarelo** (Atenção) | 10-15% | Reduzir exposição 25% |
| **Laranja** (Alerta) | 15-20% | Pausar 50% dos desportos |
| **Vermelho** (Crítico) | > 20% | Pausar todas as apostas |

---

## 6. COMUNICAÇÃO DURING STRESS

### 6.1 Para Subscritores do Tipster

**Quando Drawdown > 10%:**
```
NOTIFICAÇÃO: Performance Recente

Olá [Nome],

Informamos que o desempenho recente tem sido abaixo do esperado:
- ROI últimos 30 dias: [X]%
- Drawdown atual: [Y]%

Isto é variação normal em sistemas probabilísticos.
Continuamos a monitorizar e ajustar conforme necessário.

Equipa VBQ
```

**Quando Desporto Pausado:**
```
NOTIFICAÇÃO: [DESPORTO] Pausado Temporariamente

Olá [Nome],

[DESPORTO] foi pausado temporariamente devido a:
[RAZÃO]

Esperamos retomar em breve.
Outros desportos continuam ativos.

Equipa VBQ
```

### 6.2 Para Investidores (se aplicável)

**Quando Drawdown > 15%:**
```
RELATÓRIO DE STRESS

Data: [DATA]
Drawdown Atual: [X]%
Causa: [CAUSA]
Ação Tomada: [AÇÃO]
Plano de Recuperação: [PLANO]

Próxima Atualização: [DATA]
```

---

## 7. LIÇÕES APRENDIDAS

### 7.1 Registo de Incidentes

```python
class IncidentTracker:
    """
    Registra incidentes e lições aprendidas.
    """
    def __init__(self):
        self.incidents = []
    
    def log_incident(self, incident_type, severity, description, resolution):
        """
        Registra incidente.
        """
        incident = {
            'timestamp': datetime.now(),
            'type': incident_type,
            'severity': severity,  # low, medium, high, critical
            'description': description,
            'resolution': resolution,
            'lessons_learned': []
        }
        
        self.incidents.append(incident)
        save_incident_history(self.incidents)
    
    def add_lesson(self, incident_id, lesson):
        """
        Adiciona lição aprendida.
        """
        incident = self.incidents[incident_id]
        incident['lessons_learned'].append(lesson)
        save_incident_history(self.incidents)
```

### 7.2 Lições Comuns

**Lição 1:**
- *Incidente:* Drawdown de 20% em playoffs NBA
- *Causa:* Modelo treinado em temporada regular não generalizou
- *Lição:* Treinar modelo separado para playoffs

**Lição 2:**
- *Incidente:* Correlação inesperada entre NBA e Football
- *Causa:* Ambos afetados por evento macro (COVID)
- *Lição:* Adicionar feature de eventos macro

**Lição 3:**
- *Incidente:* Falha de API Betfair causou perdas
- *Causa:* Não havia backup de exchange
- *Lição:* Adicionar Matchbook/Smarkets como backup

---

## 8. PREVENÇÃO DE FUTUROS INCIDENTES

### 8.1 Testes de Stress Regulares

```python
def run_stress_test(scenario):
    """
    Executa teste de stress com cenário específico.
    """
    scenarios = {
        'drawdown_20pct': simulate_drawdown(0.20),
        'correlated_loss': simulate_correlated_loss(0.5),
        'model_failure': simulate_clv_negative(-0.02, 50),
        'api_failure': simulate_api_outage(24)
    }
    
    result = scenarios[scenario]
    
    # Verificar se sistema sobrevive
    if result['survives']:
        return True, "Sistema robusto"
    else:
        return False, f"Falha: {result['failure_reason']}"
```

### 8.2 Freqüência de Testes

- Teste de stress mensal: Cenário de drawdown 20%
- Teste trimestral: Cenário de perda multi-desporto
- Teste anual: Cenário de falha completa de infraestrutura

---

## 9. CRITÉRIOS DE SUCESSO

| Critério | Threshold |
|----------|-----------|
| Tempo de resposta a stress | < 1 hora |
| Tempo de recuperação | < 30 dias |
| Drawdown máximo histórico | < 25% |
| Taxa de recuperação | > 50% em 30 dias |
| Lições documentadas | 100% de incidentes |
