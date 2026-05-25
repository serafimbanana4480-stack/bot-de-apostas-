# RETRAINING_AUTO — Retreino Automático de Modelos

**ID:** `MLO-003` | **Fase:** #phase/6 | **Owner:** MLOps Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Definir estratégia de retraining automático para garantir que os modelos se mantêm atualizados com as mudanças no mercado de apostas desportivas. O retraining deve ser determinista, justificável e com custo controlado, evitando retraining desnecessário e garantindo que o modelo não se degrada.

---

## 2. TIPOS DE RETRAINING

### 2.1 Scheduled Retraining (Retreino Programado)

**Definição:** Retreino executado em intervalos fixos, independentemente da performance do modelo.

**Configuração:**
- **Frequência:** Semanal (toda segunda-feira às 04:00)
- **Dados usados:** Últimos 3 anos de dados históricos
- **Justificação:** Captura mudanças sazonais e tendências de longo prazo
- **Vantagens:** Previsível, fácil de orquestrar, garante atualização regular
- **Desvantagens:** Pode ser desnecessário se modelo está estável

**Caso de uso:** Manutenção preventiva do modelo, garantindo que nunca fica desatualizado por mais de 7 dias.

### 2.2 Triggered Retraining (Retreino Acionado)

**Definição:** Retreino executado em resposta a um evento específico que indica degradação do modelo.

**Triggers implementados:**

| Trigger | Condição | Ação | Dados usados |
|---------|----------|------|--------------|
| Feature Drift | PSI > 0.20 em qualquer feature top 10 | Retraining imediato | Últimos 6 meses + histórico |
| Prediction Drift | KS test p-value < 0.01 nas predições | Retraining imediato | Últimos 6 meses + histórico |
| Performance Degradation | CLV 7 dias < 0% (confirmado 48h) | Retraining após confirmação | Últimos 3 anos |
| Model Error | Taxa de erro > 5% em predições | Retraining imediato | Últimos 3 meses |
| Manual | Decisão do MLOps Engineer | Sob demanda | Configurável |

**Vantagens:** Reativo a problemas, usa recursos apenas quando necessário
**Desvantagens:** Menos previsível, pode ser reativo demais

### 2.3 Comparação: Scheduled vs Triggered

| Aspecto | Scheduled | Triggered |
|---------|-----------|-----------|
| Previsibilidade | Alta | Baixa |
| Custo de computação | Constante | Variável |
| Responsividade | Baixa (até 7 dias) | Alta (imediato) |
| Complexidade | Baixa | Alta |
| Risco de overfitting | Baixo | Médio |
| Recomendação | Usar ambos | Usar ambos |

**Estratégia recomendada:** Scheduled como baseline + Triggered para casos críticos

---

## 3. CRITÉRIOS DE RETRAINING

### 3.1 Feature Drift

**Condição:** PSI > 0.20 em qualquer das top 10 features

```python
# scripts/check_feature_drift.py
from scipy.stats import ks_2samp
import numpy as np

def calculate_psi(expected, actual, buckets=10):
    """Calcula PSI entre duas distribuições"""
    breakpoints = np.linspace(0, 1, buckets + 1)
    breakpoints = np.percentile(expected, breakpoints * 100)
    breakpoints[0] = expected.min() - 0.001
    breakpoints[-1] = expected.max() + 0.001
    
    expected_percents = np.histogram(expected, breakpoints)[0] / len(expected)
    actual_percents = np.histogram(actual, breakpoints)[0] / len(actual)
    
    psi = np.sum((actual_percents - expected_percents) * 
                 np.log(actual_percents / (expected_percents + 1e-10) + 1e-10))
    return psi

def check_feature_drift_trigger():
    """Verifica se deve trigger retraining por feature drift"""
    from src.data.data_loader import load_recent_data
    from src.features.feature_engineering import create_features
    
    # Dados de treino do modelo atual
    training_data = load_historical_data(years=3)
    training_data = create_features(training_data)
    
    # Dados recentes (últimos 30 dias)
    recent_data = load_recent_data(days=30)
    recent_data = create_features(recent_data)
    
    # Top 10 features por importância
    top_features = ['odds', 'home_team_strength', 'away_team_strength', 
                   'home_form', 'away_form', 'h2h_home_win_rate',
                   'league_avg_goals', 'team_momentum', 'injury_impact',
                   'weather_impact']
    
    drift_detected = False
    drift_report = []
    
    for feature in top_features:
        psi = calculate_psi(
            training_data[feature].values,
            recent_data[feature].values
        )
        
        if psi > 0.20:
            drift_detected = True
            drift_report.append(f"{feature}: PSI = {psi:.3f}")
    
    if drift_detected:
        print("DRIFT DETECTADO:")
        for report in drift_report:
            print(f"  - {report}")
        return True
    
    return False
```

### 3.2 Prediction Drift

**Condição:** KS test p-value < 0.01 na distribuição de predições

```python
# scripts/check_prediction_drift.py
from scipy.stats import ks_2samp

def check_prediction_drift_trigger():
    """Verifica se deve trigger retraining por prediction drift"""
    from src.data.data_loader import load_recent_data
    from src.features.feature_engineering import create_features
    import mlflow
    
    # Carregar modelo em produção
    model = mlflow.sklearn.load_model("models:/value-betting-model/Production")
    
    # Dados de treino (distribuição esperada)
    training_data = load_historical_data(years=3)
    training_data = create_features(training_data)
    training_predictions = model.predict_proba(
        training_data.drop('target', axis=1)
    )[:, 1]
    
    # Dados recentes (distribuição atual)
    recent_data = load_recent_data(days=30)
    recent_data = create_features(recent_data)
    recent_predictions = model.predict_proba(
        recent_data.drop('target', axis=1)
    )[:, 1]
    
    # KS test
    statistic, p_value = ks_2samp(training_predictions, recent_predictions)
    
    if p_value < 0.01:
        print(f"PREDICTION DRIFT DETECTADO:")
        print(f"  KS statistic: {statistic:.4f}")
        print(f"  p-value: {p_value:.4f}")
        return True
    
    return False
```

### 3.3 Performance Degradation

**Condição:** CLV 7 dias < 0%, confirmado por 48 horas consecutivas

```python
# scripts/check_performance_degradation.py
from datetime import datetime, timedelta

def check_performance_degradation_trigger():
    """Verifica se deve trigger retraining por performance degradation"""
    from src.data.data_loader import load_betting_results
    from src.models.metrics import calculate_clv
    
    # Verificar CLV dos últimos 7 dias
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    results = load_betting_results(start_date, end_date)
    
    if len(results) < 50:  # Amostra insuficiente
        return False
    
    clv_7d = calculate_clv(
        results['predicted_prob'],
        results['odds'],
        results['actual_outcome']
    )
    
    if clv_7d < 0:
        # Confirmar com 48 horas adicionais
        confirmation_start = end_date - timedelta(days=2)
        confirmation_results = load_betting_results(confirmation_start, end_date)
        
        if len(confirmation_results) >= 20:
            clv_48h = calculate_clv(
                confirmation_results['predicted_prob'],
                confirmation_results['odds'],
                confirmation_results['actual_outcome']
            )
            
            if clv_48h < 0:
                print(f"PERFORMANCE DEGRADATION DETECTADA:")
                print(f"  CLV 7 dias: {clv_7d:.2%}")
                print(f"  CLV 48 horas: {clv_48h:.2%}")
                return True
    
    return False
```

---

## 4. AUTOMAÇÃO COM PREFECT

### 4.1 Flow de Monitorização

```python
# flows/retraining_monitor.py
from prefect import flow, task
from prefect.blocks.notifications import SlackWebhook
from datetime import datetime

slack_block = SlackWebhook.load("slack-alerts")

@task
def check_all_triggers():
    """Verifica todos os triggers de retraining"""
    from scripts.check_feature_drift import check_feature_drift_trigger
    from scripts.check_prediction_drift import check_prediction_drift_trigger
    from scripts.check_performance_degradation import check_performance_degradation_trigger
    
    triggers = {
        'feature_drift': check_feature_drift_trigger(),
        'prediction_drift': check_prediction_drift_trigger(),
        'performance_degradation': check_performance_degradation_trigger()
    }
    
    active_triggers = [k for k, v in triggers.items() if v]
    
    return active_triggers

@task
def trigger_retraining(reason):
    """Trigger pipeline de retraining"""
    from flows.model_retraining import model_retraining_pipeline
    
    print(f"Triggering retraining: {reason}")
    
    try:
        version = model_retraining_pipeline()
        return version, True
    except Exception as e:
        print(f"Retraining failed: {e}")
        return None, False

@task
def send_alert(message):
    """Envia alerta para Slack"""
    slack_block.notify(message)

@flow(name="retraining-monitor")
def retraining_monitor_flow():
    """Flow de monitorização e trigger de retraining"""
    
    # 1. Verificar triggers
    active_triggers = check_all_triggers()
    
    if not active_triggers:
        print("Nenhum trigger ativo. Nenhum retraining necessário.")
        return
    
    # 2. Trigger retraining
    reason = f"Triggers ativos: {', '.join(active_triggers)}"
    version, success = trigger_retraining(reason)
    
    # 3. Notificar
    if success:
        message = f"✅ Retraining concluído com sucesso. Versão: {version}"
    else:
        message = f"❌ Retraining falhou. Motivo: {reason}"
    
    send_alert(message)
```

### 4.2 Schedule de Monitorização

```python
# flows/retraining_schedule.py
from prefect.deployments import Deployment
from prefect.orion.schemas.schedules import CronSchedule
from flows.retraining_monitor import retraining_monitor_flow

# Monitorização a cada 6 horas
monitor_schedule = CronSchedule(
    cron="0 */6 * * *",  # A cada 6 horas
    timezone="Europe/Lisbon"
)

deployment = Deployment.build_from_flow(
    flow=retraining_monitor_flow,
    name="retraining-monitor",
    schedule=monitor_schedule,
    work_queue_name="ml-queue"
)

if __name__ == "__main__":
    deployment.apply()
```

---

## 5. ESTRATÉGIA DE DADOS PARA RETRAINING

### 5.1 Seleção de Dados

| Tipo de Retraining | Período de Dados | Justificação |
|-------------------|------------------|--------------|
| Scheduled (semanal) | Últimos 3 anos | Captura sazonalidade completa |
| Triggered (drift) | Últimos 6 meses + histórico | Foco no regime atual |
| Triggered (performance) | Últimos 3 anos | Contexto completo para diagnóstico |
| Manual | Configurável | Flexível para casos específicos |

### 5.2 Prevenção de Leakage

**Regra crítica:** Nunca incluir dados do período onde o drift foi detetado no treino.

```python
# scripts/safe_data_selection.py
from datetime import datetime, timedelta

def select_training_data(trigger_type, trigger_date=None):
    """Seleciona dados de treino de forma segura"""
    from src.data.data_loader import load_historical_data
    
    if trigger_type == 'scheduled':
        # Retreino programado: últimos 3 anos
        end_date = datetime.now() - timedelta(days=1)
        start_date = end_date - timedelta(days=3*365)
        
    elif trigger_type == 'drift':
        # Retreino por drift: até 1 dia antes da deteção
        if trigger_date is None:
            trigger_date = datetime.now()
        
        end_date = trigger_date - timedelta(days=1)
        start_date = end_date - timedelta(days=6*30)  # 6 meses
        
    elif trigger_type == 'performance':
        # Retreino por performance: últimos 3 anos
        end_date = datetime.now() - timedelta(days=1)
        start_date = end_date - timedelta(days=3*365)
    
    else:
        raise ValueError(f"Unknown trigger type: {trigger_type}")
    
    data = load_historical_data(start_date, end_date)
    
    print(f"Selecionados {len(data)} registos:")
    print(f"  Período: {start_date.date()} a {end_date.date()}")
    print(f"  Trigger: {trigger_type}")
    
    return data
```

---

## 6. CONTROLES DE QUALIDADE

### 6.1 Pré-Retraining

Antes de iniciar o retraining, verificar:

- [ ] Volume de dados suficiente (> 1000 registos)
- [ ] Qualidade dos dados (missing values < 5%)
- [ ] Distribuição de features estável
- [ ] Sem anomalias nos dados
- [ ] Recursos computacionais disponíveis

### 6.2 Pós-Retraining

Após o retraining, validar:

- [ ] Métricas de treino vs validação (overfitting check)
- [ ] Métricas vs modelo em produção (improvement check)
- [ ] Calibração de probabilidades
- [ ] Testes de robustez
- [ ] Performance em hold-out set

### 6.3 Critérios de Promoção

O novo modelo só é promovido se:

1. **CLV improvement:** CLV novo > CLV atual + 2%
2. **Accuracy maintenance:** Accuracy novo ≥ Accuracy atual - 1%
3. **No overfitting:** Gap treino-validação < 5%
4. **Calibration:** Correlation calibration > 0.90
5. **Robustness:** Passa todos os testes de robustez

Se algum critério falhar:
- Log da falha no MLflow
- Notificação para MLOps Engineer
- Modelo arquivado como "Failed"
- Investigação manual necessária

---

## 7. CUSTO E OTIMIZAÇÃO

### 7.1 Estimativa de Custo

| Operação | Duração | Custo (VPS médio) | Frequência |
|----------|---------|-------------------|------------|
| Scheduled retraining | ~2 horas | €0.10 | Semanal |
| Triggered retraining | ~2 horas | €0.10 | Variável (0-2/mês) |
| Monitorização | < 1 minuto | €0.001 | A cada 6h |
| Total mensal estimado | - | ~€0.50-1.00 | - |

### 7.2 Otimizações

1. **Cache de features:** Armazenar features pré-calculadas para reduzir tempo de treino
2. **Incremental learning:** Explorar atualização incremental do modelo
3. **Early stopping:** Parar treino se não houver melhoria
4. **Hiperparâmetros fixos:** Evitar tuning em retraining (usar valores validados)
5. **Seleção de features:** Usar apenas top features para retraining rápido

---

## 8. MONITORIZAÇÃO DO SISTEMA DE RETRAINING

### 8.1 Métricas

- **Taxa de retraining:** Número de retraining por mês
- **Taxa de sucesso:** % de retraining que produzem modelo promovido
- **Tempo médio:** Duração média do retraining
- **Trigger distribution:** % de retraining por tipo de trigger
- **Improvement médio:** Melhoria média de CLV após retraining

### 8.2 Dashboard

```python
# scripts/retraining_dashboard.py
import mlflow
import pandas as pd
import matplotlib.pyplot as plt

def generate_retraining_dashboard():
    """Gera dashboard de métricas de retraining"""
    
    # Obter todos os runs de retraining
    experiments = mlflow.search_runs(
        experiment_ids=["value-betting-retraining"]
    )
    
    # Métricas ao longo do tempo
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # 1. CLV ao longo do tempo
    experiments['start_time'] = pd.to_datetime(experiments['start_time'])
    experiments = experiments.sort_values('start_time')
    
    axes[0, 0].plot(experiments['start_time'], experiments['metrics.clv'])
    axes[0, 0].set_title('CLV ao Longo do Tempo')
    axes[0, 0].set_xlabel('Data')
    axes[0, 0].set_ylabel('CLV')
    axes[0, 0].axhline(y=0.02, color='r', linestyle='--', label='Threshold')
    axes[0, 0].legend()
    
    # 2. Distribuição de triggers
    trigger_counts = experiments['params.trigger_type'].value_counts()
    axes[0, 1].bar(trigger_counts.index, trigger_counts.values)
    axes[0, 1].set_title('Distribuição de Triggers')
    axes[0, 1].set_xlabel('Tipo de Trigger')
    axes[0, 1].set_ylabel('Contagem')
    
    # 3. Taxa de promoção
    promoted = experiments['metrics.promoted'].sum()
    total = len(experiments)
    axes[1, 0].pie([promoted, total-promoted], 
                   labels=['Promovido', 'Não Promovido'],
                   autopct='%1.1f%%')
    axes[1, 0].set_title('Taxa de Promoção')
    
    # 4. Duração do retraining
    axes[1, 1].hist(experiments['metrics.duration'], bins=20)
    axes[1, 1].set_title('Duração do Retraining')
    axes[1, 1].set_xlabel('Duração (minutos)')
    axes[1, 1].set_ylabel('Frequência')
    
    plt.tight_layout()
    plt.savefig('retraining_dashboard.png')
    print("Dashboard salvo em retraining_dashboard.png")
```

---

## 9. PROCEDIMENTO MANUAL

### 9.1 Trigger Manual de Retraining

```bash
# 1. Ativar ambiente virtual
source venv/bin/activate

# 2. Trigger flow manual
python -m flows.model_retraining

# 3. Monitorizar progresso
prefect work-queue start ml-queue

# 4. Verificar resultado
mlflow ui
```

### 9.2 Cancelar Retraining em Curso

```bash
# Cancelar flow em execução
prefect flow-run cancel <flow-run-id>
```

---

## 10. BACKLOG TÉCNICO

- [ ] Implementar sistema de early stopping
- [ ] Adicionar cache de features para acelerar retraining
- [ ] Implementar incremental learning (se aplicável)
- [ ] Criar alertas preditivos (prever quando retraining será necessário)
- [ ] Adicionar testes de A/B testing automático
- [ ] Implementar rollback automático se performance degrada após deploy

---

## 11. LINKS CRUZADOS

- [[11_MLOps/INDEX]] ← Secção mãe
- [[11_MLOps/CI_CD_MODELOS]] → Pipeline CI/CD completo
- [[11_MLOps/MONITORIZACAO_DRIFT]] → Detecção de drift
- [[11_MLOps/FEATURE_DRIFT]] → Detalhes de feature drift
- [[11_MLOps/SHADOW_DEPLOYMENT]] → Deploy em shadow mode