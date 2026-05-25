# MODEL_REGISTRY_GESTAO — Gestão Avançada do Model Registry

**ID:** `MLO-005` | **Fase:** #phase/6 | **Owner:** MLOps Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Implementar um sistema robusto de gestão do Model Registry que permita versionar, rastrear, auditar e gerir o ciclo de vida completo dos modelos de machine learning. O registry é a fonte de verdade para todos os modelos em produção, garantindo reprodutibilidade, rastreabilidade e governança.

---

## 2. ARQUITETURA DO REGISTRY

### 2.1 Componentes

```
┌─────────────────────────────────────────────────────────────────┐
│                  MLFLOW MODEL REGISTRY                          │
└─────────────────────────────────────────────────────────────────┘

Registered Models
├── value-betting-model
│   ├── Version 1 (Production)
│   ├── Version 2 (Staging)
│   ├── Version 3 (Canary)
│   ├── Version 4 (Archived)
│   └── Version 5 (None)

Model Stages
├── None → Modelo recém-treinado, não validado
├── Staging → Modelo em shadow mode, validação em produção
├── Production → Modelo servindo tráfego real
├── Canary → Modelo em canary deployment
└── Archived → Modelo retirado, mantido para auditoria

Metadata
├── Model Info → Tipo, framework, versão
├── Parameters → Hiperparâmetros usados
├── Metrics → Métricas de performance
├── Artifacts → Modelo serializado, features, dados
├── Tags → Labels customizados (ex: "approved-by", "risk-level")
└── Description → Notas e documentação
```

### 2.2 Escolha: MLflow Registry

**Justificação:**
- Open-source e gratuito
- Integração nativa com MLflow Tracking
- Suporte para múltiplos frameworks (scikit-learn, XGBoost, etc.)
- API simples e bem documentada
- Suporte para staging e transições
- Integração com CI/CD

**Alternativas consideradas:**
- **AWS SageMaker Model Registry:** Proprietário, custo elevado
- **Google Vertex AI Model Registry:** Proprietário, lock-in
- **DVC:** Focado em dados, menos features de registry
- **Custom:** Complexidade de desenvolvimento elevada

---

## 3. GESTÃO DE VERSÕES

### 3.1 Versionamento Semântico

```python
# scripts/model_versioning.py
from mlflow.tracking import MlflowClient
from datetime import datetime

class ModelVersionManager:
    """Gerencia versionamento de modelos"""
    
    def __init__(self):
        self.client = MlflowClient()
        
    def get_next_version(self, model_name: str) -> str:
        """Obtém próxima versão do modelo"""
        versions = self.client.search_model_versions(f"name='{model_name}'")
        
        if not versions:
            return "1.0.0"
        
        # Obter última versão em produção
        prod_versions = [v for v in versions if v.current_stage == "Production"]
        
        if not prod_versions:
            return "1.0.0"
        
        last_version = prod_versions[0].version
        
        # Incrementar versão
        major, minor, patch = map(int, last_version.split('.'))
        patch += 1
        
        return f"{major}.{minor}.{patch}"
    
    def create_model_version(self, model_name: str, model, 
                            metrics: dict, params: dict, 
                            description: str = ""):
        """Cria nova versão do modelo no registry"""
        import mlflow
        
        mlflow.set_experiment("value-betting-models")
        
        with mlflow.start_run():
            # Logging de parâmetros
            mlflow.log_params(params)
            
            # Logging de métricas
            mlflow.log_metrics(metrics)
            
            # Logging do modelo
            mlflow.sklearn.log_model(
                model,
                "model",
                registered_model_name=model_name
            )
            
            # Adicionar descrição
            run_id = mlflow.active_run().info.run_id
            self.client.set_tag(
                run_id,
                "mlflow.note.content",
                description
            )
            
            # Adicionar metadata customizado
            self.client.set_tag(
                run_id,
                "created_at",
                datetime.now().isoformat()
            )
            
            self.client.set_tag(
                run_id,
                "created_by",
                "mlops-pipeline"
            )
            
            print(f"Modelo {model_name} versão criada com sucesso")
```

### 3.2 Ciclo de Vida de Versões

```
┌─────────────────────────────────────────────────────────────────┐
│              CICLO DE VIDA DE VERSÕES DE MODELO                  │
└─────────────────────────────────────────────────────────────────┘

1. CRIAÇÃO (None)
   ├── Modelo treinado e validado em hold-out
   ├── Registo no MLflow Registry como "None"
   ├── Métricas e parâmetros logged
   └── Aguarda validação

2. STAGING
   ├── Transicionado após validação inicial
   ├── Shadow mode em produção
   ├── Monitorização por 7 dias
   └── Se CLV > threshold → Production

3. PRODUCTION
   ├── Modelo serve tráfego real
   ├── Monitorização contínua
   ├── Se performance degrada → Rollback
   └── Quando substituído → Archived

4. ARCHIVED
   ├── Modelo retirado de produção
   ├── Mantido para auditoria
   ├── Não pode ser promovido
   └── Pode ser deletado após X meses
```

---

## 4. METADATA E TAGS

### 4.1 Metadata Padrão

```python
# scripts/model_metadata.py
from mlflow.tracking import MlflowClient
from datetime import datetime
import json

class ModelMetadataManager:
    """Gerencia metadata de modelos"""
    
    STANDARD_TAGS = {
        'model_type': 'classification',
        'framework': 'scikit-learn',
        'target': 'match_outcome',
        'feature_count': None,
        'training_data_period': None,
        'training_data_size': None,
        'validation_data_period': None,
        'risk_level': 'medium',  # low, medium, high
        'approved_by': None,
        'approval_date': None,
        'business_owner': 'betting-team',
        'technical_owner': 'mlops-team',
        'compliance_status': 'pending',  # pending, approved, rejected
        'data_sources': None,
        'model_purpose': 'value-betting-prediction',
        'deployment_target': 'production-api',
        'monitoring_enabled': True,
        'retraining_frequency': 'weekly',
        'drift_threshold': 0.20,
        'performance_threshold': 0.02
    }
    
    def __init__(self):
        self.client = MlflowClient()
        
    def set_standard_metadata(self, run_id: str, metadata: dict):
        """Define metadata padrão para um modelo"""
        # Merge com tags padrão
        tags = {**self.STANDARD_TAGS, **metadata}
        
        for key, value in tags.items():
            if value is not None:
                self.client.set_tag(run_id, key, str(value))
        
        print(f"Metadata definido para run {run_id}")
    
    def get_model_metadata(self, model_name: str, version: str) -> dict:
        """Obtém metadata de um modelo"""
        model_version = self.client.get_model_version(model_name, version)
        run = self.client.get_run(model_version.run_id)
        
        return run.data.tags
    
    def search_models_by_metadata(self, filters: dict) -> list:
        """Pesquisa modelos por metadata"""
        filter_string = " and ".join(
            [f"tag.{k} = '{v}'" for k, v in filters.items()]
        )
        
        models = self.client.search_model_versions(filter_string)
        return models
```

### 4.2 Exemplo de Metadata Completo

```python
# Exemplo de metadata para um modelo
metadata = {
    'model_type': 'classification',
    'framework': 'scikit-learn',
    'target': 'match_outcome',
    'feature_count': 45,
    'training_data_period': '2021-01-01 to 2024-01-01',
    'training_data_size': 25000,
    'validation_data_period': '2024-01-01 to 2024-07-01',
    'validation_data_size': 5000,
    'risk_level': 'medium',
    'approved_by': 'john.doe@company.com',
    'approval_date': '2024-01-15T10:30:00',
    'business_owner': 'betting-team',
    'technical_owner': 'mlops-team',
    'compliance_status': 'approved',
    'data_sources': 'historical-betting-data, team-stats-api',
    'model_purpose': 'value-betting-prediction',
    'deployment_target': 'production-api',
    'monitoring_enabled': True,
    'retraining_frequency': 'weekly',
    'drift_threshold': 0.20,
    'performance_threshold': 0.02,
    'accuracy': 0.58,
    'clv': 0.035,
    'calibration_correlation': 0.92,
    'hyperparameters': json.dumps({
        'n_estimators': 100,
        'max_depth': 10,
        'learning_rate': 0.01
    }),
    'git_commit': 'abc123def456',
    'docker_image': 'valuebetting:1.2.3',
    'python_version': '3.11',
    'dependencies': 'scikit-learn==1.3.0, pandas==2.0.0, numpy==1.24.0'
}
```

---

## 5. AUDITORIA

### 5.1 Logging de Alterações

```python
# scripts/model_audit.py
from mlflow.tracking import MlflowClient
from datetime import datetime
import json

class ModelAuditor:
    """Gerencia auditoria de alterações no registry"""
    
    def __init__(self):
        self.client = MlflowClient()
        
    def log_transition(self, model_name: str, version: str, 
                      from_stage: str, to_stage: str, 
                      reason: str, user: str):
        """Loga transição de estágio"""
        model_version = self.client.get_model_version(model_name, version)
        run_id = model_version.run_id
        
        # Criar log de auditoria
        audit_log = {
            'timestamp': datetime.now().isoformat(),
            'event': 'stage_transition',
            'model_name': model_name,
            'version': version,
            'from_stage': from_stage,
            'to_stage': to_stage,
            'reason': reason,
            'user': user
        }
        
        # Guardar como tag
        existing_logs = self.client.get_run(run_id).data.tags.get('audit_logs', '[]')
        logs = json.loads(existing_logs)
        logs.append(audit_log)
        
        self.client.set_tag(run_id, 'audit_logs', json.dumps(logs))
        self.client.set_tag(run_id, 'last_transition', datetime.now().isoformat())
        
        print(f"Transição logada: {from_stage} → {to_stage}")
    
    def get_audit_trail(self, model_name: str, version: str) -> list:
        """Obtém trail de auditoria de um modelo"""
        model_version = self.client.get_model_version(model_name, version)
        run_id = model_version.run_id
        
        logs = self.client.get_run(run_id).data.tags.get('audit_logs', '[]')
        return json.loads(logs)
    
    def get_all_transitions(self, model_name: str) -> list:
        """Obtém todas as transições de um modelo"""
        versions = self.client.search_model_versions(f"name='{model_name}'")
        
        all_transitions = []
        for version in versions:
            transitions = self.get_audit_trail(model_name, version.version)
            all_transitions.extend(transitions)
        
        # Ordenar por timestamp
        all_transitions.sort(key=lambda x: x['timestamp'])
        
        return all_transitions
```

### 5.2 Relatório de Auditoria

```python
# scripts/audit_report.py
from scripts.model_audit import ModelAuditor
from datetime import datetime
import pandas as pd

class AuditReportGenerator:
    """Gera relatórios de auditoria"""
    
    def __init__(self):
        self.auditor = ModelAuditor()
        
    def generate_model_report(self, model_name: str) -> dict:
        """Gera relatório completo de um modelo"""
        transitions = self.auditor.get_all_transitions(model_name)
        
        report = {
            'model_name': model_name,
            'total_transitions': len(transitions),
            'transitions_by_stage': {},
            'transitions_by_user': {},
            'timeline': transitions
        }
        
        # Agregar por estágio
        for transition in transitions:
            to_stage = transition['to_stage']
            report['transitions_by_stage'][to_stage] = \
                report['transitions_by_stage'].get(to_stage, 0) + 1
            
            user = transition['user']
            report['transitions_by_user'][user] = \
                report['transitions_by_user'].get(user, 0) + 1
        
        return report
    
    def generate_compliance_report(self, model_name: str) -> dict:
        """Gera relatório de compliance"""
        from mlflow.tracking import MlflowClient
        
        client = MlflowClient()
        versions = client.search_model_versions(f"name='{model_name}'")
        
        report = {
            'model_name': model_name,
            'total_versions': len(versions),
            'versions_in_production': 0,
            'versions_in_staging': 0,
            'versions_archived': 0,
            'versions_without_approval': 0,
            'compliance_issues': []
        }
        
        for version in versions:
            stage = version.current_stage
            
            if stage == 'Production':
                report['versions_in_production'] += 1
            elif stage == 'Staging':
                report['versions_in_staging'] += 1
            elif stage == 'Archived':
                report['versions_archived'] += 1
            
            # Verificar approval
            run = client.get_run(version.run_id)
            approval = run.data.tags.get('approved_by')
            
            if not approval and stage != 'None':
                report['versions_without_approval'] += 1
                report['compliance_issues'].append({
                    'version': version.version,
                    'stage': stage,
                    'issue': 'No approval recorded'
                })
        
        return report
    
    def export_to_csv(self, model_name: str, output_file: str):
        """Exporta relatório para CSV"""
        transitions = self.auditor.get_all_transitions(model_name)
        df = pd.DataFrame(transitions)
        df.to_csv(output_file, index=False)
        print(f"Relatório exportado para {output_file}")
```

---

## 6. PROMOÇÃO E ROLLBACK

### 6.1 Promoção Controlada

```python
# scripts/model_promotion.py
from mlflow.tracking import MlflowClient
from scripts.model_audit import ModelAuditor

class ModelPromoter:
    """Gerencia promoção de modelos entre estágios"""
    
    def __init__(self):
        self.client = MlflowClient()
        self.auditor = ModelAuditor()
        
    def promote_to_staging(self, model_name: str, version: str, 
                          reason: str, user: str):
        """Promove modelo para Staging"""
        model_version = self.client.get_model_version(model_name, version)
        current_stage = model_version.current_stage
        
        if current_stage != 'None':
            raise ValueError(f"Modelo já em estágio {current_stage}")
        
        # Transicionar
        self.client.transition_model_version_stage(
            name=model_name,
            version=version,
            stage='Staging'
        )
        
        # Log auditoria
        self.auditor.log_transition(
            model_name, version, current_stage, 'Staging', reason, user
        )
        
        print(f"Modelo {model_name} v{version} promovido para Staging")
    
    def promote_to_production(self, model_name: str, version: str,
                            reason: str, user: str):
        """Promove modelo para Production"""
        model_version = self.client.get_model_version(model_name, version)
        current_stage = model_version.current_stage
        
        if current_stage not in ['Staging', 'Canary']:
            raise ValueError(f"Modelo deve estar em Staging ou Canary")
        
        # Arquivar versão atual em production
        prod_versions = self.client.get_latest_versions(
            model_name,
            stages=['Production']
        )
        
        for prod_version in prod_versions:
            self.client.transition_model_version_stage(
                name=model_name,
                version=prod_version.version,
                stage='Archived'
            )
        
        # Promover nova versão
        self.client.transition_model_version_stage(
            name=model_name,
            version=version,
            stage='Production'
        )
        
        # Log auditoria
        self.auditor.log_transition(
            model_name, version, current_stage, 'Production', reason, user
        )
        
        print(f"Modelo {model_name} v{version} promovido para Production")
    
    def rollback(self, model_name: str, reason: str, user: str):
        """Rollback para versão anterior em production"""
        prod_versions = self.client.get_latest_versions(
            model_name,
            stages=['Production']
        )
        
        if len(prod_versions) < 1:
            raise ValueError("Não há modelo em production para rollback")
        
        current_version = prod_versions[0]
        
        # Obter versões arquivadas
        archived_versions = self.client.search_model_versions(
            f"name='{model_name}' and stage='Archived'"
        )
        
        if not archived_versions:
            raise ValueError("Não há versão arquivada para rollback")
        
        # Obter versão mais recente arquivada
        previous_version = sorted(
            archived_versions,
            key=lambda x: x.creation_timestamp,
            reverse=True
        )[0]
        
        # Arquivar versão atual
        self.client.transition_model_version_stage(
            name=model_name,
            version=current_version.version,
            stage='Archived'
        )
        
        # Promover versão anterior
        self.client.transition_model_version_stage(
            name=model_name,
            version=previous_version.version,
            stage='Production'
        )
        
        # Log auditoria
        self.auditor.log_transition(
            model_name, current_version.version, 
            'Production', 'Archived', 
            f"Rollback: {reason}", user
        )
        
        self.auditor.log_transition(
            model_name, previous_version.version,
            'Archived', 'Production',
            f"Rollback: {reason}", user
        )
        
        print(f"Rollback: {model_name} v{current_version.version} → v{previous_version.version}")
```

---

## 7. LIMPEZA E MANUTENÇÃO

### 7.1 Política de Retenção

```python
# scripts/model_cleanup.py
from mlflow.tracking import MlflowClient
from datetime import datetime, timedelta

class ModelCleaner:
    """Gerencia limpeza de modelos antigos"""
    
    def __init__(self, retention_months=6):
        self.client = MlflowClient()
        self.retention_months = retention_months
        
    def cleanup_archived_models(self, model_name: str):
        """Remove modelos arquivados além do período de retenção"""
        cutoff_date = datetime.now() - timedelta(days=self.retention_months * 30)
        
        archived_versions = self.client.search_model_versions(
            f"name='{model_name}' and stage='Archived'"
        )
        
        deleted_count = 0
        
        for version in archived_versions:
            # Converter timestamp
            creation_date = datetime.fromtimestamp(version.creation_timestamp / 1000)
            
            if creation_date < cutoff_date:
                print(f"Deletando versão {version.version} (criada em {creation_date})")
                self.client.delete_model_version(
                    name=model_name,
                    version=version.version
                )
                deleted_count += 1
        
        print(f"Deletadas {deleted_count} versões arquivadas")
    
    def cleanup_failed_models(self, model_name: str):
        """Remove modelos que nunca saíram de 'None' após X dias"""
        cutoff_date = datetime.now() - timedelta(days=30)
        
        none_versions = self.client.search_model_versions(
            f"name='{model_name}' and stage='None'"
        )
        
        deleted_count = 0
        
        for version in none_versions:
            creation_date = datetime.fromtimestamp(version.creation_timestamp / 1000)
            
            if creation_date < cutoff_date:
                print(f"Deletando versão {version.version} (nunca promovida)")
                self.client.delete_model_version(
                    name=model_name,
                    version=version.version
                )
                deleted_count += 1
        
        print(f"Deletadas {deleted_count} versões não promovidas")
```

### 7.2 Agendamento de Limpeza

```python
# flows/cleanup_schedule.py
from prefect import flow, task
from scripts.model_cleanup import ModelCleaner

@task
def run_cleanup():
    """Executa limpeza de modelos"""
    cleaner = ModelCleaner(retention_months=6)
    
    cleaner.cleanup_archived_models("value-betting-model")
    cleaner.cleanup_failed_models("value-betting-model")

@flow(name="model-cleanup")
def model_cleanup_flow():
    """Flow de limpeza mensal de modelos"""
    run_cleanup()

if __name__ == "__main__":
    from prefect.deployments import Deployment
    from prefect.orion.schemas.schedules import CronSchedule
    
    # Schedule mensal: dia 1 às 03:00
    schedule = CronSchedule(
        cron="0 3 1 * *",
        timezone="Europe/Lisbon"
    )
    
    deployment = Deployment.build_from_flow(
        flow=model_cleanup_flow,
        name="monthly-model-cleanup",
        schedule=schedule,
        work_queue_name="ml-queue"
    )
    
    deployment.apply()
```

---

## 8. INTEGRAÇÃO COM CI/CD

### 8.1 GitHub Actions para Registry

```yaml
# .github/workflows/model-registry.yml
name: Model Registry Management

on:
  push:
    branches:
      - main
    paths:
      - 'src/models/**'
  workflow_dispatch:

jobs:
  register-model:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install mlflow scikit-learn
      
      - name: Train and register model
        run: |
          python scripts/train_and_register.py
        env:
          MLFLOW_TRACKING_URI: ${{ secrets.MLFLOW_TRACKING_URI }}
      
      - name: Update model metadata
        run: |
          python scripts/update_metadata.py
        env:
          GITHUB_SHA: ${{ github.sha }}
          GITHUB_ACTOR: ${{ github.actor }}
```

---

## 9. MONITORIZAÇÃO DO REGISTRY

### 9.1 Métricas

- **Total de modelos:** Número de modelos registrados
- **Versões por estágio:** Distribuição de versões por estágio
- **Taxa de promoção:** % de modelos que chegam a production
- **Taxa de rollback:** % de modelos que sofrem rollback
- **Idade média:** Idade média das versões em cada estágio
- **Tamanho do registry:** Espaço ocupado por artifacts

### 9.2 Alertas

- Modelo sem approval em production → Alerta para MLOps Engineer
- Versões arquivadas > 12 meses → Alerta para cleanup
- Taxa de rollback > 10% → Alerta para revisão de processo
- Registry size > threshold → Alerta para limpeza

---

## 10. BACKLOG TÉCNICO

- [ ] Implementar dashboard de monitorização do registry
- [ ] Adicionar approval workflow automático
- [ ] Implementar comparação visual de versões
- [ ] Adicionar sistema de notificações de alterações
- [ ] Criar API REST para gestão do registry
- [ ] Implementar backup automatizado do registry

---

## 11. LINKS CRUZADOS

- [[11_MLOps/INDEX]] ← Secção mãe
- [[11_MLOps/CI_CD_MODELOS]] → Pipeline CI/CD
- [[11_MLOps/RETRAINING_AUTO]] → Retraining automático
- [[11_MLOps/SHADOW_DEPLOYMENT]] → Deployment strategies
- [[30_Model_Registry/INDEX]] → Detalhes do registry