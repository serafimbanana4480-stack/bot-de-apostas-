# PREDICTION_DRIFT — Monitorização de Predições em Produção

**ID:** `MLO-007` | **Fase:** #phase/6 | **Owner:** MLOps Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Implementar um sistema de monitorização contínua das predições do modelo em produção, detetando anomalias, mudanças de comportamento e degradação de performance. O prediction drift é um indicador direto de problemas no modelo, pois mostra como o modelo está a comportar-se em dados reais.

---

## 2. CONCEITOS

### 2.1 O que é Prediction Drift?

**Definição:** Mudança na distribuição das predições do modelo ao longo do tempo, indicando que o modelo está a comportar-se de forma diferente em produção comparado com o comportamento esperado.

**Causas comuns:**
- Feature drift não detetado (mudança nos dados de entrada)
- Concept drift (mudança na relação entre features e target)
- Degradação do modelo ao longo do tempo
- Mudanças no ambiente de produção
- Erros na pipeline de inferência
- Mudanças no mercado/algoritmo das casas de apostas

**Diferença vs Feature Drift:**
- **Feature drift:** Mudança nos dados de entrada (X)
- **Prediction drift:** Mudança nas saídas do modelo (Ŷ)
- Prediction drift pode ocorrer mesmo sem feature drift (ex: concept drift)
- Feature drift nem sempre causa prediction drift (ex: mudanças em features não importantes)

### 2.2 Tipos de Anomalias em Predições

| Tipo | Descrição | Exemplo |
|------|-----------|---------|
| **Shift de média** | Valor médio das predições muda | Probabilidades médias aumentam de 0.50 para 0.60 |
| **Shift de variância** | Variabilidade das predições muda | Predições tornam-se mais conservadoras (menos extremas) |
| **Mudança de forma** | Distribuição das predições muda de forma | Bimodal passa a unimodal |
| **Predições extremas** | Aumento de predições muito altas ou baixas | Mais predições > 0.90 ou < 0.10 |
| **Calibration drift** | Probabilidades tornam-se menos calibradas | Modelo diz 80% mas acerta apenas 60% |
| **Bias drift** | Predições tornam-se sistemáticamente biased | Sempre subestima probabilidade de vitória |

---

## 3. MÉTRICAS DE MONITORIZAÇÃO

### 3.1 Distribuição de Predições

**Métricas:**
- **Média das predições:** Valor médio de Ŷ
- **Mediana das predições:** Valor mediano de Ŷ
- **Desvio padrão:** Variabilidade das predições
- **Percentis:** P10, P25, P75, P90 das predições
- **Histograma:** Distribuição completa das predições

**Thresholds:**
- Média: ±10% do baseline
- Desvio padrão: ±20% do baseline
- P90: ±15% do baseline

```python
# src/monitoring/prediction_stats.py
import numpy as np
import pandas as pd
from typing import Dict
from scipy import stats

def calculate_prediction_statistics(predictions: np.ndarray) -> Dict:
    """Calcula estatísticas das predições"""
    
    stats_dict = {
        'mean': np.mean(predictions),
        'median': np.median(predictions),
        'std': np.std(predictions),
        'min': np.min(predictions),
        'max': np.max(predictions),
        'p10': np.percentile(predictions, 10),
        'p25': np.percentile(predictions, 25),
        'p75': np.percentile(predictions, 75),
        'p90': np.percentile(predictions, 90),
        'count': len(predictions)
    }
    
    return stats_dict

def compare_statistics(baseline: Dict, current: Dict) -> Dict:
    """Compara estatísticas de baseline vs current"""
    
    comparison = {}
    
    for key in baseline:
        if key == 'count':
            continue
        
        baseline_val = baseline[key]
        current_val = current[key]
        
        # Calcular diferença percentual
        if baseline_val != 0:
            diff_pct = (current_val - baseline_val) / baseline_val * 100
        else:
            diff_pct = 0
        
        comparison[key] = {
            'baseline': baseline_val,
            'current': current_val,
            'diff': current_val - baseline_val,
            'diff_pct': diff_pct,
            'anomaly': abs(diff_pct) > 10  # 10% threshold
        }
    
    return comparison
```

### 3.2 Calibration

**Definição:** Grau em que as probabilidades preditas correspondem às frequências reais de ocorrência.

**Métricas:**
- **Calibration curve:** Relação entre probabilidade predita e taxa de sucesso
- **Brier score:** Mean squared error das probabilidades
- **Expected Calibration Error (ECE):** Erro médio de calibração
- **Correlation:** Correlação entre predições e outcomes

**Thresholds:**
- Brier score: < 0.25 (bom), < 0.20 (excelente)
- ECE: < 0.05 (bom), < 0.03 (excelente)
- Correlation: > 0.90 (bom), > 0.95 (excelente)

```python
# src/monitoring/calibration.py
import numpy as np
from sklearn.calibration import calibration_curve
from sklearn.metrics import brier_score_loss
from scipy.stats import pearsonr

def calculate_calibration_metrics(predictions: np.ndarray, 
                                  outcomes: np.ndarray,
                                  n_bins: int = 10) -> Dict:
    """Calcula métricas de calibração"""
    
    # Calibration curve
    prob_true, prob_pred = calibration_curve(
        outcomes, 
        predictions, 
        n_bins=n_bins,
        strategy='uniform'
    )
    
    # Brier score
    brier = brier_score_loss(outcomes, predictions)
    
    # Expected Calibration Error
    ece = calculate_ece(prob_true, prob_pred, predictions)
    
    # Correlation
    correlation, _ = pearsonr(predictions, outcomes)
    
    return {
        'brier_score': brier,
        'ece': ece,
        'correlation': correlation,
        'prob_true': prob_true.tolist(),
        'prob_pred': prob_pred.tolist()
    }

def calculate_ece(prob_true: np.ndarray, 
                  prob_pred: np.ndarray, 
                  predictions: np.ndarray) -> float:
    """Calcula Expected Calibration Error"""
    
    # Calcular peso de cada bin (proporção de amostras)
    n_samples = len(predictions)
    bin_counts = np.histogram(predictions, bins=len(prob_pred))[0]
    bin_weights = bin_counts / n_samples
    
    # Calcular ECE
    ece = np.sum(bin_weights * np.abs(prob_true - prob_pred))
    
    return ece

def interpret_calibration(metrics: Dict) -> str:
    """Interpreta métricas de calibração"""
    
    brier = metrics['brier_score']
    ece = metrics['ece']
    correlation = metrics['correlation']
    
    if brier < 0.20 and ece < 0.03 and correlation > 0.95:
        return "Excellent calibration"
    elif brier < 0.25 and ece < 0.05 and correlation > 0.90:
        return "Good calibration"
    else:
        return "Poor calibration - needs attention"
```

### 3.3 Performance em Tempo Real

**Métricas:**
- **CLV (Cumulative Loss Value):** Valor acumulado das apostas
- **Accuracy:** Taxa de acerto das predições
- **Precision:** Precisão em predições positivas
- **Recall:** Recall em predições positivas
- **Hit rate:** Taxa de apostas vencedoras
- **ROI (Return on Investment):** Retorno sobre investimento

**Thresholds:**
- CLV: > 0% (positivo), < 0% (negativo - alerta)
- Accuracy: > 55% (baseline), < 50% (crítico)
- ROI: > 5% (bom), < 0% (alerta)

```python
# src/monitoring/performance.py
import numpy as np
import pandas as pd
from typing import Dict

def calculate_real_time_performance(predictions: np.ndarray,
                                    odds: np.ndarray,
                                    outcomes: np.ndarray,
                                    threshold: float = 0.55) -> Dict:
    """Calcula performance em tempo real"""
    
    # CLV (Cumulative Loss Value)
    # CLV = (probability * odds - 1) * stake
    # Assumindo stake = 1
    clv_per_bet = (predictions * odds - 1)
    total_clv = np.sum(clv_per_bet)
    
    # Accuracy
    binary_predictions = (predictions > threshold).astype(int)
    accuracy = np.mean(binary_predictions == outcomes)
    
    # Precision
    true_positives = np.sum((binary_predictions == 1) & (outcomes == 1))
    predicted_positives = np.sum(binary_predictions == 1)
    precision = true_positives / predicted_positives if predicted_positives > 0 else 0
    
    # Recall
    actual_positives = np.sum(outcomes == 1)
    recall = true_positives / actual_positives if actual_positives > 0 else 0
    
    # Hit rate (em apostas feitas)
    bets_made = binary_predictions.sum()
    if bets_made > 0:
        hit_rate = true_positives / bets_made
    else:
        hit_rate = 0
    
    # ROI
    total_staked = bets_made
    total_won = np.sum((binary_predictions == 1) & (outcomes == 1) * odds)
    roi = (total_won - total_staked) / total_staked if total_staked > 0 else 0
    
    return {
        'total_clv': total_clv,
        'clv_per_bet': total_clv / len(predictions) if len(predictions) > 0 else 0,
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'hit_rate': hit_rate,
        'roi': roi,
        'total_bets': bets_made,
        'total_predictions': len(predictions)
    }
```

---

## 4. SISTEMA DE MONITORIZAÇÃO

### 4.1 Monitor de Predições

```python
# src/monitoring/prediction_monitor.py
import numpy as np
import pandas as pd
from typing import Dict, List
from datetime import datetime, timedelta
import mlflow

class PredictionMonitor:
    """Monitoriza predições em produção"""
    
    def __init__(self, model_name: str = "value-betting-model"):
        self.model_name = model_name
        self.baseline_stats = None
        self.baseline_calibration = None
        
    def load_baseline(self):
        """Carrega baseline de predições (validação)"""
        from src.data.data_loader import load_validation_predictions
        
        predictions, odds, outcomes = load_validation_predictions()
        
        # Calcular estatísticas baseline
        self.baseline_stats = calculate_prediction_statistics(predictions)
        
        # Calcular calibração baseline
        self.baseline_calibration = calculate_calibration_metrics(
            predictions, outcomes
        )
        
        print(f"Baseline carregado: {len(predictions)} predições")
        
    def monitor_current_predictions(self, predictions: np.ndarray,
                                    odds: np.ndarray,
                                    outcomes: np.ndarray) -> Dict:
        """Monitoriza predições atuais"""
        
        results = {}
        
        # 1. Estatísticas de distribuição
        current_stats = calculate_prediction_statistics(predictions)
        stats_comparison = compare_statistics(
            self.baseline_stats, 
            current_stats
        )
        results['statistics'] = stats_comparison
        
        # 2. Calibração
        current_calibration = calculate_calibration_metrics(
            predictions, outcomes
        )
        results['calibration'] = current_calibration
        results['calibration_interpretation'] = interpret_calibration(
            current_calibration
        )
        
        # 3. Performance
        performance = calculate_real_time_performance(
            predictions, odds, outcomes
        )
        results['performance'] = performance
        
        # 4. Detetar anomalias
        results['anomalies'] = self.detect_anomalies(
            stats_comparison, current_calibration, performance
        )
        
        return results
    
    def detect_anomalies(self, stats_comparison: Dict,
                        calibration: Dict,
                        performance: Dict) -> List[str]:
        """Deteta anomalias nas predições"""
        
        anomalies = []
        
        # Anomalias em estatísticas
        for key, comp in stats_comparison.items():
            if comp['anomaly']:
                anomalies.append(
                    f"Statistics anomaly: {key} changed by {comp['diff_pct']:.1f}%"
                )
        
        # Anomalias em calibração
        if calibration['brier_score'] > 0.25:
            anomalies.append(f"Poor calibration: Brier score {calibration['brier_score']:.3f}")
        
        if calibration['correlation'] < 0.90:
            anomalies.append(
                f"Poor calibration: Correlation {calibration['correlation']:.3f}"
            )
        
        # Anomalias em performance
        if performance['clv_per_bet'] < 0:
            anomalies.append(
                f"Negative CLV: {performance['clv_per_bet']:.2%}"
            )
        
        if performance['accuracy'] < 0.50:
            anomalies.append(
                f"Low accuracy: {performance['accuracy']:.2%}"
            )
        
        return anomalies
    
    def log_to_mlflow(self, results: Dict):
        """Loga métricas no MLflow"""
        mlflow.set_experiment("prediction-monitoring")
        
        with mlflow.start_run():
            # Logar estatísticas
            for key, comp in results['statistics'].items():
                mlflow.log_metric(f"stat_{key}_current", comp['current'])
                mlflow.log_metric(f"stat_{key}_diff_pct", comp['diff_pct'])
            
            # Logar calibração
            mlflow.log_metric("brier_score", results['calibration']['brier_score'])
            mlflow.log_metric("ece", results['calibration']['ece'])
            mlflow.log_metric("correlation", results['calibration']['correlation'])
            
            # Logar performance
            perf = results['performance']
            mlflow.log_metric("clv_per_bet", perf['clv_per_bet'])
            mlflow.log_metric("accuracy", perf['accuracy'])
            mlflow.log_metric("roi", perf['roi'])
            
            # Logar anomalias
            mlflow.log_metric("num_anomalies", len(results['anomalies']))
            
            print(f"Métricas logadas no MLflow")
```

### 4.2 Flow de Monitorização com Prefect

```python
# flows/prediction_monitor.py
from prefect import flow, task
from prefect.blocks.notifications import SlackWebhook
from src.monitoring.prediction_monitor import PredictionMonitor
from datetime import datetime, timedelta

slack_block = SlackWebhook.load("slack-alerts")

@task
def load_recent_predictions():
    """Carrega predições recentes de produção"""
    from src.data.data_loader import load_betting_results
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    results = load_betting_results(start_date, end_date)
    
    predictions = results['predicted_prob'].values
    odds = results['odds'].values
    outcomes = results['actual_outcome'].values
    
    return predictions, odds, outcomes

@task
def monitor_predictions(predictions, odds, outcomes):
    """Monitoriza predições"""
    monitor = PredictionMonitor()
    monitor.load_baseline()
    
    results = monitor.monitor_current_predictions(
        predictions, odds, outcomes
    )
    
    return results

@task
def check_alerts(results):
    """Verifica se há alertas para enviar"""
    anomalies = results['anomalies']
    
    if anomalies:
        message = f"""
⚠️ PREDICTION ANOMALIES DETECTED

Anomalies:
"""
        for anomaly in anomalies:
            message += f"- {anomaly}\n"
        
        # Adicionar performance
        perf = results['performance']
        message += f"""
Performance:
- CLV: {perf['clv_per_bet']:.2%}
- Accuracy: {perf['accuracy']:.2%}
- ROI: {perf['roi']:.2%}
"""
        
        return message, True
    else:
        return "No anomalies detected", False

@task
def send_alert(message):
    """Envia alerta para Slack"""
    slack_block.notify(message)

@task
def trigger_action_if_needed(results):
    """Trigger ações se necessário"""
    perf = results['performance']
    
    # Se CLV muito negativo, pausar apostas
    if perf['clv_per_bet'] < -0.05:
        print("🚨 CRITICAL: CLV muito negativo - Pausando apostas")
        pause_betting()
    
    # Se accuracy muito baixa, trigger retraining
    elif perf['accuracy'] < 0.50:
        print("⚠️ WARNING: Accuracy muito baixa - Triggering retraining")
        trigger_retraining(reason="low_accuracy")

def pause_betting():
    """Pausa sistema de apostas"""
    # Implementação depende da arquitetura
    pass

def trigger_retraining(reason):
    """Trigger pipeline de retraining"""
    from flows.model_retraining import model_retraining_pipeline
    
    try:
        model_retraining_pipeline()
        print("Retraining concluído com sucesso")
    except Exception as e:
        print(f"Retraining falhou: {e}")

@flow(name="prediction-monitor")
def prediction_monitor_flow():
    """Flow de monitorização de predições"""
    
    # 1. Carregar predições recentes
    predictions, odds, outcomes = load_recent_predictions()
    
    # 2. Monitorizar
    results = monitor_predictions(predictions, odds, outcomes)
    
    # 3. Verificar alertas
    message, has_anomalies = check_alerts(results)
    
    # 4. Enviar alerta se necessário
    if has_anomalies:
        send_alert(message)
        
        # Logar no MLflow
        monitor = PredictionMonitor()
        monitor.log_to_mlflow(results)
        
        # Trigger ações
        trigger_action_if_needed(results)
    
    return has_anomalies
```

---

## 5. ESTRATÉGIA DE ALERTAS

### 5.1 Níveis de Alerta

| Nível | Condição | Ação | Frequência |
|-------|----------|------|------------|
| **INFO** | CLV 0-2% | Log apenas | Diário |
| **WARNING** | CLV -2% a 0% | Alerta Slack | Imediato |
| **CRITICAL** | CLV < -2% | Alerta + pausar | Imediato |
| **CRITICAL** | Accuracy < 50% | Alerta + retraining | Imediato |
| **CRITICAL** | Calibration < 0.85 | Alerta + investigação | Imediato |

### 5.2 Regras de Supressão

Para evitar alertas falsos positivos:

- **Mínimo de amostras:** Apenas alertar se > 50 predições
- **Consecutividade:** Apenas alertar se condição persistir por 2 verificações
- **Horário de silêncio:** Não alertar entre 00:00-06:00 (exceto crítico)
- **Cooldown:** Máximo 1 alerta por hora por tipo

---

## 6. DASHBOARD E VISUALIZAÇÃO

### 6.1 Métricas em Tempo Real

```python
# src/monitoring/dashboard.py
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta

def plot_prediction_timeline(predictions_df: pd.DataFrame, save_path: str = None):
    """Plota timeline de predições e performance"""
    
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    
    # 1. CLV ao longo do tempo
    predictions_df['date'] = pd.to_datetime(predictions_df['date'])
    daily_clv = predictions_df.groupby('date').apply(
        lambda x: (x['predicted_prob'] * x['odds'] - 1).sum()
    )
    
    axes[0].plot(daily_clv.index, daily_clv.values)
    axes[0].axhline(y=0, color='r', linestyle='--')
    axes[0].set_title('CLV Diário')
    axes[0].set_ylabel('CLV')
    axes[0].grid(True)
    
    # 2. Accuracy rolling
    predictions_df['correct'] = (
        (predictions_df['predicted_prob'] > 0.55) == 
        predictions_df['actual_outcome']
    )
    rolling_accuracy = predictions_df.set_index('date')['correct'].rolling(
        window=50
    ).mean()
    
    axes[1].plot(rolling_accuracy.index, rolling_accuracy.values)
    axes[1].axhline(y=0.55, color='r', linestyle='--', label='Baseline')
    axes[1].set_title('Accuracy Rolling (50 bets)')
    axes[1].set_ylabel('Accuracy')
    axes[1].legend()
    axes[1].grid(True)
    
    # 3. Distribuição de predições
    axes[2].hist(predictions_df['predicted_prob'], bins=30, edgecolor='black')
    axes[2].set_title('Distribuição de Predições')
    axes[2].set_xlabel('Probabilidade')
    axes[2].set_ylabel('Frequência')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path)
        print(f"Dashboard salvo em {save_path}")
    
    plt.close()

def plot_calibration_curve(predictions: np.ndarray, 
                          outcomes: np.ndarray,
                          save_path: str = None):
    """Plota calibration curve"""
    from sklearn.calibration import calibration_curve
    
    prob_true, prob_pred = calibration_curve(
        outcomes, predictions, n_bins=10, strategy='uniform'
    )
    
    fig, ax = plt.subplots(figsize=(8, 8))
    
    ax.plot([0, 1], [0, 1], 'k--', label='Perfectly calibrated')
    ax.plot(prob_pred, prob_true, 's-', label='Model')
    ax.set_xlabel('Mean Predicted Probability')
    ax.set_ylabel('Fraction of Positives')
    ax.set_title('Calibration Curve')
    ax.legend()
    ax.grid(True)
    
    if save_path:
        plt.savefig(save_path)
        print(f"Calibration curve salvo em {save_path}")
    
    plt.close()
```

---

## 7. INTEGRAÇÃO COM SISTEMA DE ALERTAS

### 7.1 Configuração de Slack

```python
# scripts/setup_slack_alerts.py
from prefect.blocks.notifications import SlackWebhook

def setup_slack_block():
    """Configura bloco de Slack para alertas"""
    
    # Criar bloco (primeira vez)
    slack_block = SlackWebhook(
        webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
    )
    
    # Salvar bloco
    slack_block.save(name="slack-alerts", overwrite=True)
    
    print("Slack block configurado com sucesso")

if __name__ == "__main__":
    setup_slack_block()
```

---

## 8. BACKLOG TÉCNICO

- [ ] Implementar deteção de anomalias com Isolation Forest
- [ ] Adicionar predição de performance futura
- [ ] Criar dashboard em Grafana para métricas em tempo real
- [ ] Implementar sistema de alertas por email/SMS
- [ ] Adicionar comparação com modelos anteriores
- [ ] Implementar análise de root cause automática

---

## 9. LINKS CRUZADOS

- [[11_MLOps/INDEX]] ← Secção mãe
- [[11_MLOps/MONITORIZACAO_DRIFT]] → Monitorização geral de drift
- [[11_MLOps/FEATURE_DRIFT]] → Deteção de feature drift
- [[11_MLOps/RETRAINING_AUTO]] → Resposta a drift com retraining
- [[11_MLOps/SHADOW_DEPLOYMENT]] → Deployment em shadow mode