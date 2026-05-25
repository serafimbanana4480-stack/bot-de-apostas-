# SHADOW_DEPLOYMENT — Deploy de Modelos em Shadow, A/B Testing e Canary

**ID:** `MLO-004` | **Fase:** #phase/6 | **Owner:** MLOps Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Implementar estratégias de deployment seguras para modelos de machine learning, permitindo validar novos modelos em produção sem expor o sistema a riscos. O shadow deployment, A/B testing e canary deployment são técnicas essenciais para mitigar riscos e garantir que apenas modelos validados chegam a produção plena.

---

## 2. CONCEITOS

### 2.1 Shadow Deployment

**Definição:** O novo modelo é deployado em paralelo com o modelo atual, recebe as mesmas requisições, mas as suas predições não são usadas para tomar decisões. As predições são apenas armazenadas para análise posterior.

**Vantagens:**
- Zero risco para o sistema
- Permite comparação direta em dados reais
- Não afeta a experiência do utilizador
- Ideal para validação inicial

**Desvantagens:**
- Custo computacional duplicado
- Não testa integração completa
- Pode ter latência diferente do modelo atual

**Quando usar:**
- Primeiro deploy de um novo modelo
- Mudanças significativas no modelo
- Validação de performance em produção
- Testes de longo prazo (7+ dias)

### 2.2 A/B Testing

**Definição:** Divisão do tráfego entre dois modelos, onde cada modelo serve uma parte dos utilizadores. As predições de ambos são usadas para tomar decisões, permitindo comparação de impacto real.

**Vantagens:**
- Testa impacto real no negócio
- Permite medição de métricas de utilizador
- Valida integração completa
- Estatisticamente rigoroso

**Desvantagens:**
- Risco se modelo novo for pior
- Complexidade na divisão de tráfego
- Pode afetar experiência de alguns utilizadores
- Requer amostra significativa para validade estatística

**Quando usar:**
- Validação final antes de rollout completo
- Comparação de modelos com performance similar
- Testes de impacto em utilizadores
- Modelos com risco baixo-médio

### 2.3 Canary Deployment

**Definição:** Deploy gradual do novo modelo, começando com uma pequena percentagem do tráfego e aumentando progressivamente se a performance for estável.

**Vantagens:**
- Risco controlado e progressivo
- Permite deteção precoce de problemas
- Rollback fácil em qualquer fase
- Minimiza impacto em caso de falha

**Desvantagens:**
- Tempo de rollout mais longo
- Complexidade de gestão de versões
- Requer monitorização contínua

**Quando usar:**
- Rollout de modelo validado
- Atualizações incrementais
- Modelos com baixo risco
- Quando tempo não é crítico

---

## 3. ESTRATÉGIA DE DEPLOYMENT

### 3.1 Pipeline de Deployment

```
┌─────────────────────────────────────────────────────────────────┐
│              PIPELINE DE DEPLOYMENT DE MODELOS                   │
└─────────────────────────────────────────────────────────────────┘

1. DESENVOLVIMENTO
   └── Modelo treinado e validado em hold-out set
       └── Métricas > thresholds mínimos

2. STAGING (SHADOW MODE)
   ├── Deploy em ambiente de staging
   ├── Shadow mode por 7 dias
   ├── Comparação contínua com modelo prod
   ├── Métricas: CLV, accuracy, calibração
   └── Se CLV shadow > CLV prod + 2% → Promove

3. CANARY DEPLOYMENT (PRODUÇÃO)
   ├── Deploy com 10% do tráfego
   ├── Monitorização por 48 horas
   ├── Se performance estável → Aumenta para 50%
   ├── Se performance estável → Aumenta para 100%
   └── Se performance degrada → Rollback imediato

4. PRODUÇÃO PLENA
   ├── Modelo serve 100% do tráfego
   ├── Monitorização contínua
   ├── Alertas automáticos
   └── Retraining se necessário
```

### 3.2 Critérios de Promoção

| Fase | Critério | Ação |
|------|----------|------|
| Staging (Shadow) | CLV shadow > CLV prod + 2% | Promove para Canary |
| Staging (Shadow) | CLV shadow ≤ CLV prod | Arquiva modelo |
| Canary (10%) | CLV ≥ CLV prod - 1% | Aumenta para 50% |
| Canary (10%) | CLV < CLV prod - 1% | Rollback |
| Canary (50%) | CLV ≥ CLV prod - 1% | Aumenta para 100% |
| Canary (50%) | CLV < CLV prod - 1% | Rollback |
| Produção (100%) | CLV < 0% por 48h | Rollback + Retraining |

---

## 4. IMPLEMENTAÇÃO DE SHADOW DEPLOYMENT

### 4.1 Arquitetura

```python
# src/deployment/shadow_deployer.py
from typing import Dict, Any
import mlflow
import pandas as pd
from datetime import datetime

class ShadowDeployer:
    """Gerencia shadow deployment de modelos"""
    
    def __init__(self):
        self.prod_model = None
        self.shadow_model = None
        self.shadow_predictions = []
        
    def load_models(self):
        """Carrega modelo em produção e modelo shadow"""
        self.prod_model = mlflow.sklearn.load_model(
            "models:/value-betting-model/Production"
        )
        self.shadow_model = mlflow.sklearn.load_model(
            "models:/value-betting-model/Staging"
        )
        
    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Faz predição com ambos os modelos
        Retorna predição do modelo prod, mas armazena shadow
        """
        # Predição do modelo em produção (usada)
        prod_pred = self.prod_model.predict_proba([features])[0, 1]
        
        # Predição do modelo shadow (apenas armazenada)
        shadow_pred = self.shadow_model.predict_proba([features])[0, 1]
        
        # Armazenar para análise posterior
        self.shadow_predictions.append({
            'timestamp': datetime.now(),
            'features': features,
            'prod_prediction': prod_pred,
            'shadow_prediction': shadow_pred,
            'actual_outcome': None  # Preenchido posteriormente
        })
        
        return {
            'prediction': prod_pred,
            'model_version': 'production'
        }
    
    def evaluate_shadow_performance(self, outcomes: pd.DataFrame):
        """Avalia performance do modelo shadow"""
        # Merge predictions com outcomes
        shadow_df = pd.DataFrame(self.shadow_predictions)
        merged = shadow_df.merge(
            outcomes,
            on=['timestamp', 'features'],
            how='inner'
        )
        
        # Calcular métricas
        from src.models.metrics import calculate_clv
        
        prod_clv = calculate_clv(
            merged['prod_prediction'],
            merged['odds'],
            merged['actual_outcome']
        )
        
        shadow_clv = calculate_clv(
            merged['shadow_prediction'],
            merged['odds'],
            merged['actual_outcome']
        )
        
        improvement = shadow_clv - prod_clv
        
        print(f"Performance Shadow Mode:")
        print(f"  CLV Produção: {prod_clv:.2%}")
        print(f"  CLV Shadow: {shadow_clv:.2%}")
        print(f"  Improvement: {improvement:.2%}")
        
        return {
            'prod_clv': prod_clv,
            'shadow_clv': shadow_clv,
            'improvement': improvement
        }
    
    def should_promote(self, min_improvement=0.02):
        """Decide se deve promover modelo shadow"""
        if len(self.shadow_predictions) < 100:
            print("Amostra insuficiente para avaliação")
            return False
        
        metrics = self.evaluate_shadow_performance()
        
        if metrics['improvement'] >= min_improvement:
            print(f"✅ Modelo shadow supera produção em {metrics['improvement']:.2%}")
            return True
        else:
            print(f"❌ Modelo shadow não supera produção (improvement: {metrics['improvement']:.2%})")
            return False
```

### 4.2 Integração com API

```python
# src/api/prediction_api.py
from fastapi import FastAPI
from src.deployment.shadow_deployer import ShadowDeployer

app = FastAPI()
deployer = ShadowDeployer()
deployer.load_models()

@app.post("/predict")
async def predict(features: dict):
    """Endpoint de predição com shadow mode"""
    
    # Fazer predição (shadow mode transparente)
    result = deployer.predict(features)
    
    return result

@app.post("/evaluate_shadow")
async def evaluate_shadow():
    """Avalia performance do modelo shadow"""
    
    # Carregar outcomes reais
    from src.data.data_loader import load_recent_outcomes
    outcomes = load_recent_outcomes(days=7)
    
    # Avaliar
    metrics = deployer.evaluate_shadow_performance(outcomes)
    
    return metrics

@app.post("/promote_shadow")
async def promote_shadow():
    """Promove modelo shadow para produção"""
    
    if deployer.should_promote():
        from mlflow.tracking import MlflowClient
        
        client = MlflowClient()
        
        # Obter versão staging
        staging_version = client.get_latest_versions(
            "value-betting-model",
            stages=["Staging"]
        )[0].version
        
        # Promover para production
        client.transition_model_version_stage(
            name="value-betting-model",
            version=staging_version,
            stage="Production"
        )
        
        return {"status": "promoted", "version": staging_version}
    else:
        return {"status": "not_promoted"}
```

---

## 5. IMPLEMENTAÇÃO DE CANARY DEPLOYMENT

### 5.1 Traffic Splitter

```python
# src/deployment/canary_deployer.py
import random
from typing import Dict, Any
import mlflow

class CanaryDeployer:
    """Gerencia canary deployment com split de tráfego"""
    
    def __init__(self, canary_ratio=0.1):
        self.canary_ratio = canary_ratio
        self.prod_model = None
        self.canary_model = None
        
    def load_models(self):
        """Carrega modelos de produção e canary"""
        self.prod_model = mlflow.sklearn.load_model(
            "models:/value-betting-model/Production"
        )
        self.canary_model = mlflow.sklearn.load_model(
            "models:/value-betting-model/Canary"
        )
        
    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Faz predição com split de tráfego"""
        
        # Determinar qual modelo usar
        use_canary = random.random() < self.canary_ratio
        
        if use_canary:
            prediction = self.canary_model.predict_proba([features])[0, 1]
            model_version = "canary"
        else:
            prediction = self.prod_model.predict_proba([features])[0, 1]
            model_version = "production"
        
        return {
            'prediction': prediction,
            'model_version': model_version
        }
    
    def update_ratio(self, new_ratio: float):
        """Atualiza rácio de tráfego para canary"""
        if 0 <= new_ratio <= 1:
            self.canary_ratio = new_ratio
            print(f"Canary ratio atualizado para {new_ratio:.0%}")
        else:
            raise ValueError("Ratio deve estar entre 0 e 1")
```

### 5.2 Pipeline de Canary

```python
# flows/canary_deployment.py
from prefect import flow, task
from datetime import datetime, timedelta

@task
def deploy_canary_initial():
    """Deploy inicial com 10% do tráfego"""
    from src.deployment.canary_deployer import CanaryDeployer
    
    deployer = CanaryDeployer(canary_ratio=0.1)
    deployer.load_models()
    
    return deployer

@task
def monitor_canary_performance(deployer, duration_hours=48):
    """Monitoriza performance do canary por X horas"""
    from src.data.data_loader import load_betting_results
    
    start_time = datetime.now()
    end_time = start_time + timedelta(hours=duration_hours)
    
    while datetime.now() < end_time:
        # Carregar resultados recentes
        results = load_betting_results(
            start_time - timedelta(hours=1),
            datetime.now()
        )
        
        # Separar por versão do modelo
        canary_results = results[results['model_version'] == 'canary']
        prod_results = results[results['model_version'] == 'production']
        
        # Calcular CLV de cada
        from src.models.metrics import calculate_clv
        
        if len(canary_results) >= 10:
            canary_clv = calculate_clv(
                canary_results['prediction'],
                canary_results['odds'],
                canary_results['outcome']
            )
            
            prod_clv = calculate_clv(
                prod_results['prediction'],
                prod_results['odds'],
                prod_results['outcome']
            )
            
            print(f"Canary CLV: {canary_clv:.2%}, Prod CLV: {prod_clv:.2%}")
            
            # Se canary degradou significativamente
            if canary_clv < prod_clv - 0.01:
                return False, "Canary performance degradada"
        
        # Aguardar próxima verificação
        import time
        time.sleep(3600)  # 1 hora
    
    return True, "Canary performance estável"

@task
def increase_canary_ratio(deployer):
    """Aumenta rácio de tráfego para canary"""
    deployer.update_ratio(0.5)
    return deployer

@task
def promote_to_full_production():
    """Promove canary para produção plena"""
    from mlflow.tracking import MlflowClient
    
    client = MlflowClient()
    
    # Promover versão canary para production
    canary_version = client.get_latest_versions(
        "value-betting-model",
        stages=["Canary"]
    )[0].version
    
    client.transition_model_version_stage(
        name="value-betting-model",
        version=canary_version,
        stage="Production"
    )
    
    # Arquivar versão anterior
    prod_version = client.get_latest_versions(
        "value-betting-model",
        stages=["Production"]
    )[1].version
    
    client.transition_model_version_stage(
        name="value-betting-model",
        version=prod_version,
        stage="Archived"
    )

@flow(name="canary-deployment-pipeline")
def canary_deployment_pipeline():
    """Pipeline completo de canary deployment"""
    
    # 1. Deploy inicial (10%)
    deployer = deploy_canary_initial()
    
    # 2. Monitorizar por 48 horas
    success, message = monitor_canary_performance(deployer)
    
    if not success:
        print(f"❌ Canary falhou: {message}")
        # Rollback automático
        deployer.update_ratio(0.0)
        return
    
    # 3. Aumentar para 50%
    deployer = increase_canary_ratio(deployer)
    
    # 4. Monitorizar por mais 24 horas
    success, message = monitor_canary_performance(deployer, duration_hours=24)
    
    if not success:
        print(f"❌ Canary falhou em 50%: {message}")
        deployer.update_ratio(0.0)
        return
    
    # 5. Promover para produção plena
    promote_to_full_production()
    
    print("✅ Canary deployment concluído com sucesso")
```

---

## 6. A/B TESTING

### 6.1 Design do Experimento

```python
# src/deployment/ab_test.py
import hashlib
from typing import Dict, Any
import mlflow

class ABTester:
    """Gerencia A/B testing de modelos"""
    
    def __init__(self, test_name: str, split_ratio: float = 0.5):
        self.test_name = test_name
        self.split_ratio = split_ratio
        self.model_a = None
        self.model_b = None
        
    def load_models(self, model_a_path: str, model_b_path: str):
        """Carrega os dois modelos para teste"""
        self.model_a = mlflow.sklearn.load_model(model_a_path)
        self.model_b = mlflow.sklearn.load_model(model_b_path)
        
    def assign_group(self, user_id: str) -> str:
        """Atribui utilizador a grupo A ou B de forma determinista"""
        hash_value = int(hashlib.md5(f"{self.test_name}_{user_id}".encode()).hexdigest(), 16)
        return "A" if (hash_value % 100) < (self.split_ratio * 100) else "B"
    
    def predict(self, user_id: str, features: Dict[str, Any]) -> Dict[str, Any]:
        """Faz predição baseada no grupo do utilizador"""
        group = self.assign_group(user_id)
        
        if group == "A":
            prediction = self.model_a.predict_proba([features])[0, 1]
            model_version = "A"
        else:
            prediction = self.model_b.predict_proba([features])[0, 1]
            model_version = "B"
        
        return {
            'prediction': prediction,
            'group': group,
            'model_version': model_version
        }
    
    def analyze_results(self, results: pd.DataFrame, min_sample=100):
        """Analisa resultados do A/B test"""
        from scipy import stats
        from src.models.metrics import calculate_clv
        
        group_a = results[results['group'] == 'A']
        group_b = results[results['group'] == 'B']
        
        if len(group_a) < min_sample or len(group_b) < min_sample:
            print(f"Amostra insuficiente: A={len(group_a)}, B={len(group_b)}")
            return None
        
        # Calcular CLV de cada grupo
        clv_a = calculate_clv(
            group_a['prediction'],
            group_a['odds'],
            group_a['outcome']
        )
        
        clv_b = calculate_clv(
            group_b['prediction'],
            group_b['odds'],
            group_b['outcome']
        )
        
        # Teste estatístico
        t_stat, p_value = stats.ttest_ind(
            group_a['profit'],
            group_b['profit']
        )
        
        results = {
            'group_a': {
                'clv': clv_a,
                'sample_size': len(group_a)
            },
            'group_b': {
                'clv': clv_b,
                'sample_size': len(group_b)
            },
            'difference': clv_b - clv_a,
            'p_value': p_value,
            'significant': p_value < 0.05
        }
        
        print(f"Resultados A/B Test:")
        print(f"  Group A CLV: {clv_a:.2%} (n={len(group_a)})")
        print(f"  Group B CLV: {clv_b:.2%} (n={len(group_b)})")
        print(f"  Difference: {clv_b - clv_a:.2%}")
        print(f"  P-value: {p_value:.4f}")
        print(f"  Significant: {'Yes' if p_value < 0.05 else 'No'}")
        
        return results
```

### 6.2 Critérios de Significância

- **Tamanho mínimo da amostra:** 100 predições por grupo
- **Nível de significância:** p < 0.05
- **Power estatístico:** 80% (detectar diferença de 2% em CLV)
- **Duração mínima:** 7 dias (capturar variabilidade)

---

## 7. ROLLBACK

### 7.1 Rollback Automático

```python
# scripts/rollback_model.py
from mlflow.tracking import MlflowClient
import mlflow

def rollback_to_previous():
    """Rollback para versão anterior do modelo"""
    client = MlflowClient()
    
    # Obter versões em production
    prod_versions = client.get_latest_versions(
        "value-betting-model",
        stages=["Production"]
    )
    
    if len(prod_versions) < 2:
        print("Não há versão anterior para rollback")
        return False
    
    current_version = prod_versions[0]
    previous_version = prod_versions[1]
    
    # Transicionar anterior para Production
    client.transition_model_version_stage(
        name="value-betting-model",
        version=previous_version.version,
        stage="Production"
    )
    
    # Arquivar versão atual
    client.transition_model_version_stage(
        name="value-betting-model",
        version=current_version.version,
        stage="Archived"
    )
    
    print(f"Rollback: {current_version.version} → {previous_version.version}")
    return True

def trigger_rollback_if_degraded():
    """Trigger rollback se performance degradou"""
    from src.data.data_loader import load_betting_results
    from src.models.metrics import calculate_clv
    from datetime import datetime, timedelta
    
    # Verificar CLV das últimas 48 horas
    end_date = datetime.now()
    start_date = end_date - timedelta(hours=48)
    
    results = load_betting_results(start_date, end_date)
    
    if len(results) < 20:
        return  # Amostra insuficiente
    
    clv = calculate_clv(
        results['prediction'],
        results['odds'],
        results['outcome']
    )
    
    if clv < 0:
        print(f"CLV negativo ({clv:.2%}) - Triggering rollback")
        rollback_to_previous()
    else:
        print(f"CLV estável ({clv:.2%}) - Sem rollback necessário")
```

---

## 8. MONITORIZAÇÃO

### 8.1 Métricas de Deployment

| Métrica | Descrição | Threshold |
|---------|-----------|-----------|
| Shadow CLV | CLV do modelo em shadow | > Prod CLV + 2% |
| Canary CLV | CLV do modelo em canary | ≥ Prod CLV - 1% |
| Canary Error Rate | Taxa de erro do canary | < 1% |
| Canary Latency | Latência do canary | < 2x Prod latency |
| A/B Test P-value | Significância estatística | < 0.05 |
| Rollback Rate | Taxa de rollback | < 10% |

### 8.2 Alertas

- Shadow CLV < Prod CLV → Alerta para MLOps Engineer
- Canary CLV < Prod CLV - 1% → Rollback automático
- Canary Error Rate > 1% → Rollback automático
- Canary Latency > 2x → Alerta para DevOps Engineer
- A/B Test não significativo após 14 dias → Encerrar teste

---

## 9. BEST PRACTICES

1. **Começar sempre com shadow mode** antes de qualquer A/B ou canary
2. **Definir critérios de sucesso claros** antes do deployment
3. **Monitorizar continuamente** durante todo o período de teste
4. **Ter plano de rollback pronto** e testado
5. **Documentar todos os testes** e resultados
6. **Usar amostras estatisticamente significativas**
7. **Isolar impacto** (não testar múltiplas mudanças simultaneamente)
8. **Comunicar com stakeholders** sobre testes em curso

---

## 10. BACKLOG TÉCNICO

- [ ] Implementar dashboard de monitorização de canary
- [ ] Adicionar testes de carga para canary deployment
- [ ] Implementar sistema de feature flags para ativação/desativação
- [ ] Criar templates de relatórios de A/B testing
- [ ] Adicionar automação para rollback baseado em anomalias
- [ ] Implementar multi-armed bandit para otimização contínua

---

## 11. LINKS CRUZADOS

- [[11_MLOps/INDEX]] ← Secção mãe
- [[11_MLOps/CI_CD_MODELOS]] → Pipeline CI/CD completo
- [[11_MLOps/RETRAINING_AUTO]] → Retraining automático
- [[11_MLOps/MODEL_REGISTRY_GESTAO]] → Gestão do registry
- [[12_DevOps/DEPLOYMENT_STRATEGY]] → Estratégias de deploy geral