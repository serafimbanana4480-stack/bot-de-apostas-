# REGISTRY_GESTAO — Versionamento de Modelos

**ID:** `MR-001` | **Fase:** #phase/2-6 | **Owner:** MLOps Engineer | **Status:** #status/pending

---

## 1. ESTAGIOS

| Estagio | Descricao | Promocao |
|---------|-----------|----------|
| Development | Notebook / script local | Testes passam |
| Staging | Shadow mode | CLV shadow > modelo prod |
| Production | Serve predicao em tempo real | CLV real validado |
| Archived | Nao serve; mantido para audit | - |

---

## 2. WORKFLOW

```python
# Promocao staging -> production
def promote_model(model_id, staging_metrics, production_metrics):
    if staging_metrics['clv'] > production_metrics['clv'] * 1.01:
        mlflow.transition_model_version_stage(
            name="nba_moneyline",
            version=model_id,
            stage="Production"
        )
        return True
    return False
```

---

## 3. ROLLBACK

```python
def rollback_model():
    # Encontrar versao anterior em Production
    versions = mlflow.search_model_versions("name='nba_moneyline'")
    previous = [v for v in versions if v.current_stage == "Production"][-2]
    
    mlflow.transition_model_version_stage(
        name="nba_moneyline",
        version=previous.version,
        stage="Production"
    )
```

---

## 4. CRITÉRIOS DETALHADOS DE PROMOÇÃO

### 4.1 Development → Staging
| Critério | Threshold | Obrigatório |
|----------|-----------|-------------|
| Purged CV completo (5 splits) | ✅ | Sim |
| CLV médio CV | > 2% | Sim |
| CLV t-stat | > 2.0 (p < 0.05) | Sim |
| Brier Score | < 0.25 | Sim |
| ECE | < 0.05 | Sim |
| Sem data leakage detetado | ✅ | Sim |
| Código revisto e aprovado | ✅ | Sim |

### 4.2 Staging → Production
| Critério | Threshold | Obrigatório |
|----------|-----------|-------------|
| Shadow mode | ≥ 7 dias | Sim |
| CLV shadow ≥ modelo em produção | ≥ +0.5% | Sim |
| Sharpe ratio shadow | ≥ modelo prod | Recomendado |
| Nenhum incidente crítico em shadow | ✅ | Sim |
| Aprovação Chief Architect + MLOps | ✅ | Sim |

---

## 5. PROCESSO DE PROMOÇÃO COMPLETO

```python
from dataclasses import dataclass
from enum import Enum
import mlflow

class ModelStage(Enum):
    DEVELOPMENT = "Development"
    STAGING = "Staging"
    PRODUCTION = "Production"
    ARCHIVED = "Archived"


@dataclass
class PromotionCriteria:
    clv_mean: float
    clv_t_stat: float
    brier_score: float
    ece: float
    shadow_days: int = 0
    shadow_clv_delta: float = 0.0


def can_promote_to_staging(criteria: PromotionCriteria) -> tuple[bool, list[str]]:
    """Verificar se modelo pode avançar para staging."""
    failures = []
    if criteria.clv_mean < 0.02:
        failures.append(f"CLV {criteria.clv_mean:.3f} < 0.02 threshold")
    if criteria.clv_t_stat < 2.0:
        failures.append(f"t-stat {criteria.clv_t_stat:.2f} < 2.0 (não significativo)")
    if criteria.brier_score > 0.25:
        failures.append(f"Brier {criteria.brier_score:.3f} > 0.25 threshold")
    if criteria.ece > 0.05:
        failures.append(f"ECE {criteria.ece:.3f} > 0.05 threshold")
    return len(failures) == 0, failures


def can_promote_to_production(criteria: PromotionCriteria) -> tuple[bool, list[str]]:
    """Verificar se modelo pode avançar para produção."""
    failures = []
    if criteria.shadow_days < 7:
        failures.append(f"Shadow mode apenas {criteria.shadow_days} dias (mínimo 7)")
    if criteria.shadow_clv_delta < 0.005:
        failures.append(f"CLV delta shadow {criteria.shadow_clv_delta:.3f} < 0.005")
    return len(failures) == 0, failures


def promote_model(
    model_name: str,
    version: str,
    target_stage: ModelStage,
    criteria: PromotionCriteria
) -> bool:
    """Promover modelo após verificação de critérios."""
    if target_stage == ModelStage.STAGING:
        ok, failures = can_promote_to_staging(criteria)
    elif target_stage == ModelStage.PRODUCTION:
        ok, failures = can_promote_to_production(criteria)
    else:
        ok, failures = True, []

    if not ok:
        print(f"Promoção BLOQUEADA:\n" + "\n".join(f"  - {f}" for f in failures))
        return False

    mlflow.transition_model_version_stage(
        name=model_name,
        version=version,
        stage=target_stage.value,
        archive_existing_versions=(target_stage == ModelStage.PRODUCTION)
    )
    print(f"Modelo {model_name} v{version} promovido para {target_stage.value}")
    return True
```

---

## 6. ROLLBACK DE EMERGÊNCIA

```python
def emergency_rollback(model_name: str) -> bool:
    """
    Rollback imediato para versão anterior em produção.
    Usar quando: CLV cairia < 0%, erro de predição, incidente crítico.
    """
    client = mlflow.tracking.MlflowClient()
    versions = client.search_model_versions(f"name='{model_name}'")

    # Ordenar por version_id descendente
    production_versions = [
        v for v in versions
        if v.current_stage in ("Production", "Archived")
    ]
    production_versions.sort(key=lambda v: int(v.version), reverse=True)

    if len(production_versions) < 2:
        print("ERRO: Sem versão anterior para rollback")
        return False

    current = production_versions[0]
    previous = production_versions[1]

    # Arquivar atual
    client.transition_model_version_stage(
        name=model_name, version=current.version, stage="Archived"
    )
    # Restaurar anterior
    client.transition_model_version_stage(
        name=model_name, version=previous.version, stage="Production"
    )

    print(f"ROLLBACK: {model_name} v{current.version} → v{previous.version}")
    # Enviar alerta Telegram
    return True
```

**SLA de rollback:** < 5 minutos desde a decisão até ao modelo anterior em produção.

---

## 7. BACKLOG

- [ ] Configurar MLflow Model Registry (Fase 2)
- [ ] Implementar `promote_model` com validações automáticas
- [ ] Implementar `emergency_rollback` e testar em staging
- [ ] Configurar alertas automáticos quando modelo entra em produção
- [ ] Documentar schedule de revisão de modelos (mensal)
- [ ] Implementar alerta quando modelo prod tem > 90 dias sem re-avaliação

---

## 8. LINKS CRUZADOS

- [[30_Model_Registry/INDEX]] ← Secção mãe
- [[11_MLOps/INDEX]] → Retraining e drift
- [[47_Shadow_Betting/INDEX]] → Shadow mode para validação pré-produção
- [[29_Experiment_Tracking/INDEX]] → Experimentos de origem
