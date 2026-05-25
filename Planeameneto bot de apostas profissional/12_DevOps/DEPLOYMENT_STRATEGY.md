# DEPLOYMENT_STRATEGY — Estratégias de Deploy, Blue-Green, Canary e Rollback

**ID:** `DEV-002` | **Fase:** #phase/1 | **Owner:** DevOps Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Definir estratégias de deployment que garantam zero downtime, rollback rápido e minimização de risco ao atualizar a aplicação em produção. Uma boa estratégia de deploy é essencial para manter disponibilidade e confiança no sistema.

---

## 2. AMBIENTES

### 2.1 Estrutura de Ambientes

```
Development (Local)
├── Ambiente de desenvolvimento local
├── Docker Compose para serviços
└── Hot reload para desenvolvimento rápido

Staging (Shadow Mode)
├── Espelho de produção
├── Shadow mode para modelos
├── Testes manuais e automatizados
└── Dados de produção (read-only)

Production
├── Ambiente de produção real
├── Alta disponibilidade
├── Monitorização contínua
└── Backup automatizado
```

### 2.2 Características por Ambiente

| Aspecto | Development | Staging | Production |
|---------|-------------|---------|------------|
| **Propósito** | Desenvolvimento | Validação | Serviço real |
| **Dados** | Sintéticos/Mock | Produção (read-only) | Produção (real) |
| **Escalabilidade** | 1 instância | 2 instâncias | Auto-scaling |
| **Monitorização** | Básica | Completa | Completa + alertas |
| **Acesso** | Desenvolvedores | Equipa + QA | Limitado |
| **Deploy** | Manual | Automatizado | Automatizado |
| **Rollback** | Manual | Automatizado | Automatizado |

---

## 3. ESTRATÉGIAS DE DEPLOYMENT

### 3.1 Blue-Green Deployment

**Definição:** Manter duas versões idênticas do ambiente (blue e green). O tráfego é comutado instantaneamente de uma para outra.

**Como funciona:**
```
1. Deploy nova versão no ambiente Green (idle)
2. Executar testes no Green
3. Comutar tráfego: Blue → Green
4. Monitorizar Green
5. Se OK: Blue torna-se novo idle
6. Se problema: Comutar tráfego de volta para Blue
```

**Vantagens:**
- Zero downtime
- Rollback instantâneo (basta comutar tráfego)
- Fácil de testar antes de expor a tráfego real
- Isolamento completo entre versões

**Desvantagens:**
- Custo duplicado de infraestrutura
- Requer balanceador de carga
- Complexidade de gestão de estado
- Tempo de deploy mais longo (precisa copiar tudo)

**Quando usar:**
- Aplicações stateless
- Quando zero downtime é crítico
- Recursos suficientes para ambientes duplicados
- Deploy de versões grandes

**Implementação com Docker Compose:**

```yaml
# docker-compose.blue-green.yml
version: '3.8'

services:
  # Blue environment
  app-blue:
    image: valuebetting:${VERSION_BLUE}
    container_name: app-blue
    environment:
      - ENV=production
      - VERSION=${VERSION_BLUE}
    ports:
      - "8000:8000"
    networks:
      - backend

  # Green environment
  app-green:
    image: valuebetting:${VERSION_GREEN}
    container_name: app-green
    environment:
      - ENV=production
      - VERSION=${VERSION_GREEN}
    ports:
      - "8001:8000"
    networks:
      - backend

  # Nginx load balancer
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - app-blue
      - app-green
    networks:
      - backend

networks:
  backend:
    driver: bridge
```

```nginx
# nginx.conf
upstream backend {
    server app-blue:8000;
    # server app-green:8000;  # Comentar/descomutar para comutar
}

server {
    listen 80;
    
    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Script de Comutação:**

```bash
#!/bin/bash
# scripts/switch-blue-green.sh

BLUE_VERSION="1.0.0"
GREEN_VERSION="1.1.0"

# Deploy nova versão no Green
echo "Deploying version $GREEN_VERSION to Green..."
docker-compose -f docker-compose.blue-green.yml up -d app-green

# Testar Green
echo "Testing Green environment..."
curl -f http://localhost:8001/health || exit 1

# Comutar tráfego
echo "Switching traffic to Green..."
sed -i 's/server app-blue:8000;/# server app-blue:8000;/' nginx.conf
sed -i 's/# server app-green:8000;/server app-green:8000;/' nginx.conf
docker-compose -f docker-compose.blue-green.yml restart nginx

echo "Traffic switched to Green"
echo "Old Blue version: $BLUE_VERSION"
echo "New Green version: $GREEN_VERSION"
```

### 3.2 Canary Deployment

**Definição:** Deploy gradual onde a nova versão recebe uma pequena percentagem do tráfego inicialmente, aumentando progressivamente se a performance for estável.

**Como funciona:**
```
1. Deploy nova versão ao lado da atual
2. Direcionar 5-10% do tráfego para nova versão
3. Monitorizar métricas por X horas
4. Se estável: Aumentar para 50% do tráfego
5. Se estável: Aumentar para 100% do tráfego
6. Se problema: Reduzir para 0% e investigar
```

**Vantagens:**
- Risco controlado e progressivo
- Detecção precoce de problemas
- Minimiza impacto em caso de falha
- Não requer duplicação completa de infraestrutura
- Ideal para A/B testing

**Desvantagens:**
- Rollback não instantâneo (precisa reduzir tráfego gradualmente)
- Complexidade de gestão de versões simultâneas
- Requer monitorização contínua
- Tempo de rollout mais longo

**Quando usar:**
- Quando risco é moderado
- Para testar impacto real
- Quando recursos são limitados
- Para A/B testing de features

**Implementação com Nginx:**

```nginx
# nginx-canary.conf
upstream backend {
    # 90% tráfego versão atual
    server app-v1:8000 weight=9;
    
    # 10% tráfego nova versão (canary)
    server app-v2:8000 weight=1;
}

server {
    listen 80;
    
    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Script de Gradual Rollout:**

```python
# scripts/canary_rollout.py
import time
import subprocess
import requests

def canary_rollout(max_ratio=1.0, steps=5, duration_hours=24):
    """Executa rollout gradual do canary"""
    
    step_duration = duration_hours * 3600 / steps
    current_ratio = 0.1  # Começa com 10%
    
    print(f"Starting canary rollout: {steps} steps over {duration_hours}h")
    
    for step in range(steps):
        # Atualizar rácio no load balancer
        update_canary_ratio(current_ratio)
        
        # Monitorizar
        if not monitor_canary(duration_minutes=30):
            print("Canary failed - rolling back")
            rollback_canary()
            return False
        
        # Aumentar rácio
        current_ratio = min(max_ratio, current_ratio + (max_ratio - 0.1) / steps)
        print(f"Step {step + 1}/{steps}: Ratio increased to {current_ratio:.0%}")
        
        # Aguardar próximo passo
        time.sleep(step_duration)
    
    # Promover para 100%
    update_canary_ratio(1.0)
    print("Canary rollout completed successfully")
    return True

def update_canary_ratio(ratio):
    """Atualiza rácio de tráfego para canary"""
    # Atualizar configuração do Nginx
    v1_weight = int((1 - ratio) * 10)
    v2_weight = int(ratio * 10)
    
    nginx_config = f"""
upstream backend {{
    server app-v1:8000 weight={v1_weight};
    server app-v2:8000 weight={v2_weight};
}}
"""
    
    with open('nginx-canary.conf', 'w') as f:
        f.write(nginx_config)
    
    # Reload Nginx
    subprocess.run(['docker-compose', 'restart', 'nginx'])

def monitor_canary(duration_minutes=30):
    """Monitoriza canary por X minutos"""
    end_time = time.time() + duration_minutes * 60
    
    while time.time() < end_time:
        # Verificar health check
        try:
            response = requests.get('http://localhost:8001/health', timeout=5)
            if response.status_code != 200:
                print(f"Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"Health check error: {e}")
            return False
        
        # Verificar métricas
        metrics = get_canary_metrics()
        if metrics['error_rate'] > 0.05:
            print(f"Error rate too high: {metrics['error_rate']:.2%}")
            return False
        
        time.sleep(60)  # Verificar a cada minuto
    
    return True

def rollback_canary():
    """Rollback imediato do canary"""
    update_canary_ratio(0.0)
    print("Canary rolled back")

if __name__ == "__main__":
    canary_rollout(max_ratio=1.0, steps=5, duration_hours=24)
```

### 3.3 Rolling Deployment

**Definição:** Atualizar instâncias uma a uma, mantendo sempre algumas instâncias da versão antiga ativas.

**Como funciona:**
```
1. Ter N instâncias da versão atual
2. Atualizar 1 instância para nova versão
3. Verificar se OK
4. Atualizar próxima instância
5. Repetir até todas estarem atualizadas
```

**Vantagens:**
- Simples de implementar
- Não requer load balancer complexo
- Risco mitigado (sempre há instâncias antigas)
- Eficiente em termos de recursos

**Desvantagens:**
- Downtime parcial (instâncias individuais)
- Não é zero downtime
- Versões mistas durante deploy
- Rollback mais complexo

**Quando usar:**
- Aplicações com múltiplas instâncias
- Quando zero downtime não é crítico
- Deploy de atualizações pequenas
- Recursos limitados

---

## 4. ESTRATÉGIA RECOMENDADA

### 4.1 Para Value Betting Bot

**Estratégia híbrida:**

```
1. DESENVOLVIMENTO → STAGING
   └── Blue-Green deployment
       - Zero downtime em staging
       - Testes completos antes de produção

2. STAGING → PRODUÇÃO (Modelos)
   └── Canary deployment
       - 10% → 50% → 100%
       - Monitorização de CLV e performance
       - Shadow mode antes de canary

3. STAGING → PRODUÇÃO (Código)
   └── Blue-Green deployment
       - Zero downtime
       - Rollback instantâneo
       - Para mudanças não-modelo
```

**Justificação:**
- Modelos têm risco mais alto → Canary para validação gradual
- Código tem risco menor → Blue-Green para zero downtime
- Shadow mode para modelos antes de qualquer exposição a tráfego real

---

## 5. ROLLBACK

### 5.1 Estratégias de Rollback

**Instantâneo (Blue-Green):**
```bash
# Comutar tráfego de volta
sed -i 's/server app-green:8000;/# server app-green:8000;/' nginx.conf
sed -i 's/# server app-blue:8000;/server app-blue:8000;/' nginx.conf
docker-compose restart nginx
```

**Gradual (Canary):**
```python
# Reduzir rácio gradualmente
for ratio in [0.5, 0.25, 0.1, 0.0]:
    update_canary_ratio(ratio)
    monitor_canary(duration_minutes=10)
```

**Automático:**
```python
# Trigger rollback se métricas degradarem
if clv < -0.05 or error_rate > 0.10:
    emergency_rollback()
```

### 5.2 Procedimento de Rollback

```python
# scripts/rollback.py
import mlflow
from datetime import datetime

def emergency_rollback():
    """Rollback de emergência"""
    
    print("🚨 EMERGENCY ROLLBACK INITIATED")
    
    # 1. Identificar versão anterior
    previous_version = get_previous_production_version()
    
    # 2. Rollback do modelo
    rollback_model(previous_version)
    
    # 3. Rollback do código (blue-green)
    rollback_code()
    
    # 4. Verificar health
    if not verify_health():
        print("❌ Rollback failed - manual intervention required")
        notify_team("Rollback failed - manual intervention required")
        return False
    
    # 5. Notificar equipe
    notify_team(f"Emergency rollback completed to {previous_version}")
    
    # 6. Log incidente
    log_incident("emergency_rollback", {
        'timestamp': datetime.now().isoformat(),
        'previous_version': previous_version,
        'trigger': 'automatic'
    })
    
    return True

def rollback_model(version):
    """Rollback do modelo para versão anterior"""
    from mlflow.tracking import MlflowClient
    
    client = MlflowClient()
    
    # Arquivar versão atual
    current = client.get_latest_versions(
        "value-betting-model",
        stages=["Production"]
    )[0]
    
    client.transition_model_version_stage(
        name="value-betting-model",
        version=current.version,
        stage="Archived"
    )
    
    # Promover versão anterior
    client.transition_model_version_stage(
        name="value-betting-model",
        version=version,
        stage="Production"
    )
    
    print(f"Model rolled back to version {version}")

def rollback_code():
    """Rollback do código (blue-green)"""
    import subprocess
    
    # Comutar tráfego para blue
    subprocess.run(['bash', 'scripts/switch-to-blue.sh'])
    
    print("Code rolled back to blue environment")

def verify_health():
    """Verifica saúde do sistema após rollback"""
    import requests
    
    try:
        response = requests.get('http://localhost:8000/health', timeout=10)
        return response.status_code == 200
    except:
        return False

def notify_team(message):
    """Notifica equipe via Slack"""
    from prefect.blocks.notifications import SlackWebhook
    
    slack = SlackWebhook.load("slack-alerts")
    slack.notify(f"🚨 {message}")

def log_incident(incident_type, details):
    """Loga incidente para análise posterior"""
    # Implementar logging de incidentes
    pass
```

---

## 6. AUTOMAÇÃO DE DEPLOY

### 6.1 Pipeline de Deploy

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches:
      - main
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Login to Docker Registry
        uses: docker/login-action@v2
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Build and push Docker image
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: ghcr.io/${{ github.repository }}:latest,ghcr.io/${{ github.repository }}:${{ github.sha }}
      
      - name: Deploy to production
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.PRODUCTION_HOST }}
          username: ${{ secrets.PRODUCTION_USER }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /app/valuebetting
            docker-compose pull
            docker-compose up -d
            docker system prune -f
      
      - name: Health check
        run: |
          sleep 30
          curl -f ${{ secrets.PRODUCTION_URL }}/health || exit 1
      
      - name: Notify on failure
        if: failure()
        uses: 8398a7/action-slack@v3
        with:
          status: failure
          text: 'Deployment to production failed'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### 6.2 Docker Compose para Produção

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  app:
    image: ghcr.io/username/valuebetting:latest
    container_name: valuebetting-app
    restart: unless-stopped
    environment:
      - ENV=production
      - DATABASE_URL=${DATABASE_URL}
      - MLFLOW_TRACKING_URI=${MLFLOW_TRACKING_URI}
      - LOG_LEVEL=INFO
    ports:
      - "8000:8000"
    volumes:
      - ./logs:/app/logs
    networks:
      - backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  nginx:
    image: nginx:alpine
    container_name: valuebetting-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    networks:
      - backend

  redis:
    image: redis:alpine
    container_name: valuebetting-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    networks:
      - backend

networks:
  backend:
    driver: bridge
```

---

## 7. MONITORIZAÇÃO DE DEPLOY

### 7.1 Métricas

- **Deploy success rate:** % de deploys bem-sucedidos
- **Deploy duration:** Tempo médio de deploy
- **Rollback rate:** % de deploys que requerem rollback
- **Downtime:** Tempo de indisponibilidade
- **Error rate post-deploy:** Taxa de erro após deploy

### 7.2 Alertas

- Deploy falha → Alerta imediato
- Health check falha → Rollback automático
- Error rate > threshold → Alerta + rollback se crítico
- Performance degradation → Alerta para investigação

---

## 8. BACKLOG TÉCNICO

- [ ] Implementar dashboard de monitorização de deploys
- [ ] Adicionar automação de rollback baseado em métricas
- [ ] Implementar feature flags para deploy independente de código
- [ ] Criar sistema de smoke tests automatizados
- [ ] Implementar blue-green deployment completo
- [ ] Adicionar integração com Kubernetes para escalabilidade

---

## 9. LINKS CRUZADOS

- [[12_DevOps/INDEX]] ← Secção mãe
- [[12_DevOps/GIT_WORKFLOW]] → Estratégia Git
- [[12_DevOps/CI_CD_SETUP]] → Configuração de CI/CD
- [[11_MLOps/SHADOW_DEPLOYMENT]] → Shadow deployment de modelos
- [[11_MLOps/CI_CD_MODELOS]] → CI/CD de modelos