# FEATURE_DRIFT — Deteção Detalhada de Feature Drift

**ID:** `MLO-006` | **Fase:** #phase/6 | **Owner:** MLOps Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Implementar um sistema robusto de deteção de feature drift que identifique mudanças na distribuição das features ao longo do tempo. O feature drift é um dos indicadores mais importantes de degradação de modelo, pois mudanças nos dados de entrada podem levar a predições incorretas mesmo que o modelo permaneça inalterado.

---

## 2. CONCEITOS

### 2.1 O que é Feature Drift?

**Definição:** Mudança estatisticamente significativa na distribuição de uma ou mais features entre o conjunto de dados usado para treinar o modelo e os dados recebidos em produção.

**Causas comuns:**
- Mudanças na fonte de dados (API altera formato)
- Mudanças no comportamento dos utilizadores
- Mudanças sazonais (ex: comportamento diferente no verão vs inverno)
- Mudanças no mercado (ex: novas regras de apostas)
- Erros de coleta de dados
- Mudanças na pipeline de feature engineering

**Impacto:**
- Degradação de performance do modelo
- Predições biased ou incorretas
- Perda de confiança no sistema
- Perdas financeiras em apostas

### 2.2 Tipos de Drift

| Tipo | Descrição | Exemplo |
|------|-----------|---------|
| **Covariate Drift** | Distribuição de features muda, mas relação feature-target mantém-se | Odds médias aumentam devido a inflação |
| **Prior Probability Shift** | Distribuição do target muda | Mais jogos com favoritos fortes |
| **Concept Drift** | Relação feature-target muda | Mudança nas regras do futebol altera importância de features |
| **Sudden Drift** | Mudança abrupta | API de odds muda formato |
| **Gradual Drift** | Mudança lenta e progressiva | Tendência de mercado ao longo de meses |
| **Recurring Drift** | Padrão que se repete | Sazonalidade (férias, playoffs) |

---

## 3. MÉTRICAS DE DETEÇÃO

### 3.1 PSI (Population Stability Index)

**Definição:** Mede a diferença entre duas distribuições, originalmente desenvolvido para indústria de crédito.

**Interpretação:**
- PSI < 0.1: Mudança insignificante (sem ação)
- PSI 0.1 - 0.2: Mudança moderada (monitorizar)
- PSI > 0.2: Mudança significativa (ação necessária)

**Vantagens:**
- Sensível a mudanças em toda a distribuição
- Fácil de interpretar
- Funciona bem para features contínuas e categóricas
- Independente do scale da feature

**Desvantagens:**
- Rejeição sensível ao número de buckets
- Menos sensível a mudanças nas caudas da distribuição

```python
# src/drift/psi_calculator.py
import numpy as np
from typing import Tuple

def calculate_psi(expected: np.ndarray, 
                  actual: np.ndarray, 
                  buckets: int = 10,
                  epsilon: float = 1e-10) -> Tuple[float, dict]:
    """
    Calcula PSI entre duas distribuições.
    
    Args:
        expected: Distribuição de referência (treino)
        actual: Distribuição atual (produção)
        buckets: Número de buckets para discretização
        epsilon: Pequeno valor para evitar divisão por zero
    
    Returns:
        PSI value e detalhes por bucket
    """
    # Remover NaNs
    expected = expected[~np.isnan(expected)]
    actual = actual[~np.isnan(actual)]
    
    # Criar buckets baseados em expected (percentis)
    breakpoints = np.linspace(0, 100, buckets + 1)
    quantiles = np.percentile(expected, breakpoints)
    
    # Ajustar extremos para incluir todos os valores
    quantiles[0] = min(quantiles[0], actual.min()) - epsilon
    quantiles[-1] = max(quantiles[-1], actual.max()) + epsilon
    
    # Calcular percentagens em cada bucket
    expected_counts, _ = np.histogram(expected, quantiles)
    actual_counts, _ = np.histogram(actual, quantiles)
    
    expected_percents = expected_counts / len(expected)
    actual_percents = actual_counts / len(actual)
    
    # Adicionar epsilon para evitar log(0)
    expected_percents = np.maximum(expected_percents, epsilon)
    actual_percents = np.maximum(actual_percents, epsilon)
    
    # Calcular PSI por bucket
    psi_per_bucket = (actual_percents - expected_percents) * \
                     np.log(actual_percents / expected_percents)
    
    # PSI total
    psi_total = np.sum(psi_per_bucket)
    
    # Detalhes
    details = {
        'psi_total': psi_total,
        'psi_per_bucket': psi_per_bucket.tolist(),
        'breakpoints': quantiles.tolist(),
        'expected_percents': expected_percents.tolist(),
        'actual_percents': actual_percents.tolist(),
        'interpretation': interpret_psi(psi_total)
    }
    
    return psi_total, details

def interpret_psi(psi: float) -> str:
    """Interpreta valor de PSI"""
    if psi < 0.1:
        return "Insignificant - No action needed"
    elif psi < 0.2:
        return "Moderate - Monitor closely"
    else:
        return "Significant - Action required"

# Exemplo de uso
if __name__ == "__main__":
    # Simular dados
    np.random.seed(42)
    expected = np.random.normal(100, 15, 10000)
    actual = np.random.normal(105, 15, 1000)  # Shift de 5 unidades
    
    psi, details = calculate_psi(expected, actual)
    print(f"PSI: {psi:.4f}")
    print(f"Interpretation: {details['interpretation']}")
```

### 3.2 KS Test (Kolmogorov-Smirnov)

**Definição:** Teste não-paramétrico que compara duas distribuições acumuladas.

**Hipóteses:**
- H0: As duas distribuições são idênticas
- H1: As duas distribuições são diferentes

**Interpretação:**
- p-value > 0.05: Não rejeitar H0 (sem drift significativo)
- p-value < 0.05: Rejeitar H0 (drift significativo)
- p-value < 0.01: Drift muito significativo

**Vantagens:**
- Não assume distribuição específica
- Sensível a diferenças em qualquer parte da distribuição
- P-value fornece medida de significância estatística

**Desvantagens:**
- Menos intuitivo que PSI
- Sensível a tamanho da amostra (amostras grandes podem detetar diferenças pequenas)

```python
# src/drift/ks_test.py
from scipy.stats import ks_2samp
import numpy as np
from typing import Tuple

def calculate_ks_statistic(expected: np.ndarray, 
                          actual: np.ndarray) -> Tuple[float, float, str]:
    """
    Calcula KS test entre duas distribuições.
    
    Args:
        expected: Distribuição de referência (treino)
        actual: Distribuição atual (produção)
    
    Returns:
        KS statistic, p-value e interpretação
    """
    # Remover NaNs
    expected = expected[~np.isnan(expected)]
    actual = actual[~np.isnan(actual)]
    
    # Executar KS test
    statistic, p_value = ks_2samp(expected, actual)
    
    # Interpretar
    interpretation = interpret_ks(p_value)
    
    return statistic, p_value, interpretation

def interpret_ks(p_value: float) -> str:
    """Interpreta p-value do KS test"""
    if p_value > 0.05:
        return "No significant drift (p > 0.05)"
    elif p_value > 0.01:
        return "Moderate drift (0.01 < p < 0.05)"
    else:
        return "Significant drift (p < 0.01)"

# Exemplo de uso
if __name__ == "__main__":
    np.random.seed(42)
    expected = np.random.normal(100, 15, 10000)
    actual = np.random.normal(105, 15, 1000)
    
    statistic, p_value, interpretation = calculate_ks_statistic(expected, actual)
    print(f"KS Statistic: {statistic:.4f}")
    print(f"P-value: {p_value:.4f}")
    print(f"Interpretation: {interpretation}")
```

### 3.3 Comparação PSI vs KS

| Aspecto | PSI | KS Test |
|---------|-----|---------|
| Sensibilidade a shift de média | Alta | Alta |
| Sensibilidade a mudança de variância | Alta | Alta |
| Sensibilidade a mudança de forma | Média | Alta |
| Interpretabilidade | Alta (thresholds claros) | Média (p-value) |
| Dependência de tamanho de amostra | Baixa | Alta |
| Funciona com dados categóricos | Sim (com adaptação) | Não |
| Uso recomendado | Produção (thresholds claros) | Análise exploratória |

**Recomendação:** Usar PSI para monitorização em produção (thresholds claros) e KS test para análise detalhada quando drift é detetado.

---

## 4. IMPLEMENTAÇÃO DO SISTEMA

### 4.1 Monitor de Feature Drift

```python
# src/drift/feature_drift_monitor.py
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import mlflow

class FeatureDriftMonitor:
    """Monitoriza drift de features em produção"""
    
    def __init__(self, model_name: str = "value-betting-model"):
        self.model_name = model_name
        self.baseline_data = None
        self.features_to_monitor = [
            'odds', 'home_team_strength', 'away_team_strength',
            'home_form', 'away_form', 'h2h_home_win_rate',
            'league_avg_goals', 'team_momentum', 'injury_impact',
            'weather_impact'
        ]
        
    def load_baseline(self):
        """Carrega dados de baseline (treino)"""
        from src.data.data_loader import load_historical_data
        from src.features.feature_engineering import create_features
        
        # Carregar dados de treino
        data = load_historical_data(years=3)
        data = create_features(data)
        
        self.baseline_data = data[self.features_to_monitor]
        print(f"Baseline carregado: {len(self.baseline_data)} registos")
        
    def check_drift(self, current_data: pd.DataFrame) -> Dict:
        """
        Verifica drift em todas as features.
        
        Returns:
            Dict com resultados de drift por feature
        """
        if self.baseline_data is None:
            self.load_baseline()
        
        results = {}
        
        for feature in self.features_to_monitor:
            if feature not in current_data.columns:
                continue
            
            baseline = self.baseline_data[feature].values
            current = current_data[feature].values
            
            # Calcular PSI
            psi, psi_details = self.calculate_psi(baseline, current)
            
            # Calcular KS
            ks_stat, ks_p, ks_interp = self.calculate_ks(baseline, current)
            
            results[feature] = {
                'psi': psi,
                'psi_interpretation': psi_details['interpretation'],
                'ks_statistic': ks_stat,
                'ks_p_value': ks_p,
                'ks_interpretation': ks_interp,
                'drift_detected': psi > 0.2 or ks_p < 0.01
            }
        
        return results
    
    def calculate_psi(self, expected: np.ndarray, actual: np.ndarray) -> Tuple[float, dict]:
        """Calcula PSI"""
        from src.drift.psi_calculator import calculate_psi
        return calculate_psi(expected, actual)
    
    def calculate_ks(self, expected: np.ndarray, actual: np.ndarray) -> Tuple[float, float, str]:
        """Calcula KS test"""
        from src.drift.ks_test import calculate_ks_statistic
        return calculate_ks_statistic(expected, actual)
    
    def generate_report(self, results: Dict) -> str:
        """Gera relatório de drift"""
        report = f"""
# Feature Drift Report
Generated: {datetime.now().isoformat()}

## Summary
Features monitored: {len(results)}
Features with drift: {sum(1 for r in results.values() if r['drift_detected'])}

## Detailed Results
"""
        
        for feature, metrics in results.items():
            status = "⚠️ DRIFT" if metrics['drift_detected'] else "✅ OK"
            report += f"""
### {feature} {status}
- PSI: {metrics['psi']:.4f} ({metrics['psi_interpretation']})
- KS Statistic: {metrics['ks_statistic']:.4f}
- KS P-value: {metrics['ks_p_value']:.4f} ({metrics['ks_interpretation']})
"""
        
        return report
    
    def log_to_mlflow(self, results: Dict):
        """Loga métricas de drift no MLflow"""
        mlflow.set_experiment("feature-drift-monitoring")
        
        with mlflow.start_run():
            for feature, metrics in results.items():
                mlflow.log_metric(f"{feature}_psi", metrics['psi'])
                mlflow.log_metric(f"{feature}_ks_p", metrics['ks_p_value'])
                mlflow.log_metric(f"{feature}_drift", int(metrics['drift_detected']))
            
            # Logar resumo
            total_drift = sum(1 for r in results.values() if r['drift_detected'])
            mlflow.log_metric("total_drift_features", total_drift)
            
            print(f"Métricas logadas no MLflow")
```

### 4.2 Flow de Monitorização com Prefect

```python
# flows/feature_drift_monitor.py
from prefect import flow, task
from prefect.blocks.notifications import SlackWebhook
from src.drift.feature_drift_monitor import FeatureDriftMonitor

slack_block = SlackWebhook.load("slack-alerts")

@task
def load_current_data():
    """Carrega dados recentes de produção"""
    from src.data.data_loader import load_recent_data
    from src.features.feature_engineering import create_features
    
    data = load_recent_data(days=30)
    data = create_features(data)
    
    return data

@task
def check_drift(current_data):
    """Verifica drift de features"""
    monitor = FeatureDriftMonitor()
    monitor.load_baseline()
    
    results = monitor.check_drift(current_data)
    return results

@task
def generate_alert(results):
    """Gera alerta se drift detetado"""
    drift_features = [f for f, m in results.items() if m['drift_detected']]
    
    if drift_features:
        message = f"""
⚠️ FEATURE DRIFT DETECTED

Features com drift:
{', '.join(drift_features)}

PSI values:
"""
        for feature in drift_features:
            message += f"- {feature}: {results[feature]['psi']:.4f}\n"
        
        return message, True
    else:
        return "No feature drift detected", False

@task
def send_slack_alert(message):
    """Envia alerta para Slack"""
    slack_block.notify(message)

@flow(name="feature-drift-monitor")
def feature_drift_monitor_flow():
    """Flow de monitorização de feature drift"""
    
    # 1. Carregar dados atuais
    current_data = load_current_data()
    
    # 2. Verificar drift
    results = check_drift(current_data)
    
    # 3. Gerar alerta se necessário
    message, has_drift = generate_alert(results)
    
    if has_drift:
        send_slack_alert(message)
        
        # Logar no MLflow
        monitor = FeatureDriftMonitor()
        monitor.log_to_mlflow(results)
    
    return has_drift
```

---

## 5. ESTRATÉGIA DE MONITORIZAÇÃO

### 5.1 Frequência de Monitorização

| Tipo | Frequência | Justificação |
|------|------------|--------------|
| Features críticas (odds, team strength) | Diariamente | Alto impacto nas predições |
| Features secundárias (form, h2h) | Semanalmente | Impacto moderado |
| Features contextuais (weather) | Mensalmente | Impacto baixo |
| Análise completa | Semanalmente | Visão holística |

### 5.2 Thresholds por Feature

| Feature | PSI Threshold | Justificação |
|---------|---------------|--------------|
| odds | 0.15 | Mais sensível - impacto direto |
| home_team_strength | 0.20 | Threshold padrão |
| away_team_strength | 0.20 | Threshold padrão |
| home_form | 0.25 | Mais tolerante a variação |
| away_form | 0.25 | Mais tolerante a variação |
| h2h_home_win_rate | 0.20 | Threshold padrão |
| league_avg_goals | 0.15 | Sensível a mudanças de regras |
| team_momentum | 0.25 | Feature volátil por natureza |
| injury_impact | 0.30 | Dados menos consistentes |
| weather_impact | 0.30 | Alta variabilidade natural |

---

## 6. RESPOSTA A DRIFT

### 6.1 Matriz de Decisão

| PSI | KS | Ação |
|-----|----|------|
| < 0.10 | > 0.05 | Nenhuma - sistema estável |
| 0.10 - 0.20 | 0.01 - 0.05 | Monitorizar - preparar retraining |
| 0.20 - 0.30 | < 0.01 | Retraining triggered - shadow mode |
| > 0.30 | < 0.001 | Alerta crítico - pausar apostas |

### 6.2 Procedimento de Resposta

```python
# scripts/drift_response.py
from src.drift.feature_drift_monitor import FeatureDriftMonitor

def respond_to_drift(results: dict):
    """Responde a drift detetado"""
    
    # Identificar severidade
    max_psi = max(r['psi'] for r in results.values())
    
    if max_psi > 0.30:
        # Drift crítico
        print("🚨 CRITICAL DRIFT - Pausando apostas")
        pause_betting()
        notify_critical_drift(results)
        
    elif max_psi > 0.20:
        # Drift significativo
        print("⚠️ SIGNIFICANT DRIFT - Triggering retraining")
        trigger_retraining(reason="feature_drift")
        
    elif max_psi > 0.10:
        # Drift moderado
        print("📊 MODERATE DRIFT - Monitoring closely")
        schedule_frequent_monitoring()
        
    else:
        # Sem drift
        print("✅ NO DRIFT - Continue normal operations")

def pause_betting():
    """Pausa sistema de apostas"""
    # Implementação depende da arquitetura
    pass

def notify_critical_drift(results):
    """Notifica equipe de drift crítico"""
    from prefect.blocks.notifications import SlackWebhook
    
    slack = SlackWebhook.load("slack-alerts")
    slack.notify(f"CRITICAL DRIFT DETECTED: {results}")

def trigger_retraining(reason):
    """Trigger pipeline de retraining"""
    from flows.model_retraining import model_retraining_pipeline
    
    try:
        model_retraining_pipeline()
        print("Retraining concluído com sucesso")
    except Exception as e:
        print(f"Retraining falhou: {e}")

def schedule_frequent_monitoring():
    """Agenda monitorização mais frequente"""
    # Alterar schedule de semanal para diário
    pass
```

---

## 7. VISUALIZAÇÃO

### 7.1 Plot de Distribuições

```python
# src/drift/visualization.py
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

def plot_distribution_comparison(baseline: np.ndarray, 
                                 current: np.ndarray,
                                 feature_name: str,
                                 save_path: str = None):
    """Plota comparação de distribuições"""
    
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # Histograma
    axes[0].hist(baseline, bins=30, alpha=0.5, label='Baseline', density=True)
    axes[0].hist(current, bins=30, alpha=0.5, label='Current', density=True)
    axes[0].set_xlabel(feature_name)
    axes[0].set_ylabel('Density')
    axes[0].set_title(f'{feature_name} Distribution')
    axes[0].legend()
    
    # CDF
    baseline_sorted = np.sort(baseline)
    current_sorted = np.sort(current)
    baseline_cdf = np.arange(1, len(baseline_sorted) + 1) / len(baseline_sorted)
    current_cdf = np.arange(1, len(current_sorted) + 1) / len(current_sorted)
    
    axes[1].plot(baseline_sorted, baseline_cdf, label='Baseline')
    axes[1].plot(current_sorted, current_cdf, label='Current')
    axes[1].set_xlabel(feature_name)
    axes[1].set_ylabel('CDF')
    axes[1].set_title(f'{feature_name} CDF')
    axes[1].legend()
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path)
        print(f"Plot salvo em {save_path}")
    
    plt.close()

def plot_drift_heatmap(results: dict, save_path: str = None):
    """Plota heatmap de drift por feature"""
    import pandas as pd
    
    df = pd.DataFrame(results).T
    
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(df[['psi', 'ks_p_value']], 
                annot=True, 
                fmt='.4f',
                cmap='RdYlGn_r',
                ax=ax)
    ax.set_title('Feature Drift Heatmap')
    
    if save_path:
        plt.savefig(save_path)
        print(f"Heatmap salvo em {save_path}")
    
    plt.close()
```

---

## 8. BACKLOG TÉCNICO

- [ ] Implementar deteção de drift para features categóricas
- [ ] Adicionar deteção de multivariate drift
- [ ] Implementar sistema de alertas preditivos
- [ ] Criar dashboard em tempo real de drift
- [ ] Adicionar análise de root cause automática
- [ ] Implementar adaptive thresholds baseados em historicidade

---

## 9. LINKS CRUZADOS

- [[11_MLOps/INDEX]] ← Secção mãe
- [[11_MLOps/MONITORIZACAO_DRIFT]] → Monitorização geral de drift
- [[11_MLOps/PREDICTION_DRIFT]] → Monitorização de predições
- [[11_MLOps/RETRAINING_AUTO]] → Resposta a drift com retraining
- [[48_Data_Drift/INDEX]] → Análise detalhada de drift