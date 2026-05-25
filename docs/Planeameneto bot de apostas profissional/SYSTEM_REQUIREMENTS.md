# SYSTEM_REQUIREMENTS — Requisitos do Sistema

**ID:** `ARCH-002` | **Fase:** #phase/1 | **Owner:** System Architect | **Status:** #status/active

---

## 1. OBJETIVO

Definir requisitos técnicos detalhados de hardware, software, performance e operacionais para garantir funcionamento robusto do sistema de value betting.

---

## 2. REQUISITOS DE HARDWARE

### 2.1 Ambiente de Desenvolvimento

| Componente | Mínimo | Recomendado | Justificação |
|------------|--------|-------------|--------------|
| CPU | 2 vCPU | 4 vCPU | Compilação, testes locais |
| RAM | 8 GB | 16 GB | IDE, Docker containers |
| Disco | 50 GB SSD | 100 GB SSD | Código, dados de teste |
| Rede | 10 Mbps | 100 Mbps | Git, downloads |

### 2.2 Ambiente de Staging

| Componente | Mínimo | Recomendado | Justificação |
|------------|--------|-------------|--------------|
| CPU | 4 vCPU | 8 vCPU | Testes de integração |
| RAM | 16 GB | 32 GB | Múltiplos containers |
| Disco | 200 GB SSD | 500 GB SSD | Dados de teste históricos |
| Rede | 100 Mbps | 1 Gbps | APIs externas, replicação |

### 2.3 Ambiente de Produção

| Componente | Mínimo | Recomendado | Justificação |
|------------|--------|-------------|--------------|
| CPU | 8 vCPU | 16 vCPU | Inferência em tempo real |
| RAM | 32 GB | 64 GB | Cache de dados em memória |
| Disco | 500 GB SSD | 1 TB SSD NVMe | Dados históricos, logs |
| Rede | 1 Gbps | 10 Gbps | APIs de baixa latência |
| HA | N/A | 2+ instâncias | Alta disponibilidade |

### 2.4 Especificações Detalhadas por Serviço

**Data Pipeline (ETL):**
- CPU: 4 vCPU
- RAM: 16 GB
- Disco: 200 GB (logs temporários)

**Signal Engine (ML):**
- CPU: 8 vCPU
- RAM: 32 GB
- GPU: Opcional para treinamento

**Execution System:**
- CPU: 4 vCPU
- RAM: 16 GB
- Disco: 100 GB

**PostgreSQL:**
- CPU: 4 vCPU
- RAM: 16 GB
- Disco: 500 GB SSD (IOPS > 3000)

**Redis:**
- CPU: 2 vCPU
- RAM: 8 GB
- Disco: 50 GB (persistence)

---

## 3. REQUISITOS DE SOFTWARE

### 3.1 Core Stack

| Componente | Versão Mínima | Versão Recomendada | Justificação |
|------------|---------------|-------------------|--------------|
| Python | 3.10 | 3.11 | Compatibilidade de bibliotecas |
| PostgreSQL | 14 | 15 | Performance, features |
| Redis | 7.0 | 7.2 | Performance, módulos |
| RabbitMQ | 3.10 | 3.12 | Messaging, stability |
| MLflow | 2.0 | 2.8 | Experiment tracking |

### 3.2 Bibliotecas Python

| Biblioteca | Versão | Uso |
|-----------|--------|-----|
| numpy | >= 1.24 | Computação numérica |
| pandas | >= 2.0 | Manipulação de dados |
| scikit-learn | >= 1.3 | ML tradicional |
| xgboost | >= 2.0 | Gradient boosting |
| tensorflow | >= 2.13 | Deep learning (opcional) |
| sqlalchemy | >= 2.0 | ORM PostgreSQL |
| redis-py | >= 5.0 | Cliente Redis |
| pika | >= 1.3 | Cliente RabbitMQ |
| fastapi | >= 0.100 | API REST |
| uvicorn | >= 0.23 | ASGI server |
| celery | >= 5.3 | Task queue |
| prefect | >= 2.10 | Workflow orchestration |
| great_expectations | >= 0.17 | Data validation |
| prometheus-client | >= 0.17 | Metrics |
| grafana-api | >= 1.3 | Dashboards |

### 3.3 Infraestrutura

| Componente | Versão | Uso |
|-----------|--------|-----|
| Docker | >= 24.0 | Containerization |
| Docker Compose | >= 2.20 | Local development |
| Kubernetes | >= 1.27 | Orquestração (produção) |
| Nginx | >= 1.24 | Reverse proxy |
| Traefik | >= 3.0 | Load balancer |
| Certbot | >= 2.6 | SSL certificates |

### 3.4 DevOps

| Componente | Versão | Uso |
|-----------|--------|-----|
| Git | >= 2.40 | Version control |
| GitHub Actions | Latest | CI/CD |
| Terraform | >= 1.5 | IaC |
| Ansible | >= 2.14 | Configuration management |
| Packer | >= 1.9 | Image building |

---

## 4. REQUISITOS DE PERFORMANCE

### 4.1 Latência

| Operação | Target | SLO | P95 | P99 |
|----------|--------|-----|-----|-----|
| Inferência modelo | < 50ms | < 100ms | 80ms | 95ms |
| API odds fetch | < 200ms | < 500ms | 300ms | 450ms |
| API bet placement | < 500ms | < 1s | 750ms | 900ms |
| Query PostgreSQL | < 100ms | < 200ms | 150ms | 180ms |
| Redis get/set | < 5ms | < 10ms | 8ms | 9ms |

### 4.2 Throughput

| Métrica | Target | SLO |
|---------|--------|-----|
| Sinais por segundo | > 10 | > 5 |
| Apostas por minuto | > 20 | > 10 |
| Queries por segundo | > 100 | > 50 |
| API requests/min | > 1000 | > 500 |

### 4.3 Disponibilidade

| Métrica | Target | SLO |
|---------|--------|-----|
| Uptime anual | > 99.5% | > 99.0% |
| Downtime mensal | < 3.6h | < 7.2h |
| MTBF | > 720h | > 360h |
| MTTR | < 1h | < 4h |

### 4.4 Capacidade

| Métrica | Target | SLO |
|---------|--------|-----|
| Usuários simultâneos | > 100 | > 50 |
| Apostas diárias | > 1000 | > 500 |
| Dados históricos | > 5 anos | > 3 anos |
| Storage growth | < 10GB/mês | < 20GB/mês |

---

## 5. REQUISITOS DE SEGURANÇA

### 5.1 Autenticação e Autorização

- **MFA obrigatório** para todos os acessos administrativos
- **RBAC** (Role-Based Access Control) granular
- **SSO** (Single Sign-On) com SAML 2.0
- **JWT** com expiração < 1 hora
- **Password policy:** Mínimo 12 caracteres, complexidade

### 5.2 Network Security

- **TLS 1.3** para todas as conexões
- **VPN** obrigatória para acesso admin
- **IP whitelisting** para APIs críticas
- **WAF** (Web Application Firewall)
- **DDoS protection** (Cloudflare/AWS Shield)

### 5.3 Data Security

- **Encryption at rest:** AES-256
- **Encryption in transit:** TLS 1.3
- **Backup encryption:** Chaves separadas
- **PII protection:** GDPR compliance
- **Audit logging:** Todas as ações

---

## 6. REQUISITOS DE DISASTER RECOVERY

### 6.1 Backup Strategy

| Tipo | Frequência | Retenção | Localização |
|------|-----------|----------|-------------|
| Full DB backup | Diário | 30 dias | Off-site (S3) |
| Incremental backup | 4/hora | 7 dias | Off-site (S3) |
| Transaction log | Contínuo | 24 horas | Off-site (S3) |
| Config backup | Semanal | 90 dias | Git + S3 |

### 6.2 Recovery Objectives

| Métrica | Target | SLO |
|---------|--------|-----|
| RPO (Recovery Point Objective) | < 1h | < 4h |
| RTO (Recovery Time Objective) | < 4h | < 8h |
| Data loss | < 1h | < 4h |
| Service restoration | < 4h | < 8h |

### 6.3 Failover

- **Active-passive** setup para produção
- **Automated failover** < 5 minutos
- **Health checks** a cada 30 segundos
- **DNS failover** automático
- **Regular drills** mensais

---

## 7. REQUISITOS DE MONITORIZAÇÃO

### 7.1 Metrics Collection

- **Prometheus** para métricas de sistema
- **Grafana** para dashboards
- **AlertManager** para alertas
- **Custom metrics** de negócio (ROI, CLV, etc.)

### 7.2 Logging

- **Structured logging** (JSON)
- **Log aggregation** (ELK/Loki)
- **Retention:** 90 dias
- **Log levels:** DEBUG, INFO, WARNING, ERROR, CRITICAL

### 7.3 Tracing

- **Distributed tracing** (Jaeger/Tempo)
- **Trace sampling:** 10% (produção)
- **Span retention:** 7 dias

---

## 8. REQUISITOS DE ESCALABILIDADE

### 8.1 Horizontal Scaling

- **Auto-scaling** baseado em CPU > 70%
- **Min instances:** 2 por serviço
- **Max instances:** 10 por serviço
- **Scale-up time:** < 2 minutos

### 8.2 Vertical Scaling

- **CPU:** Até 32 vCPU
- **RAM:** Até 128 GB
- **Storage:** Até 5 TB

### 8.3 Database Scaling

- **Read replicas:** Mínimo 2
- **Connection pooling:** PgBouncer
- **Partitioning:** Por data (mensal)
- **Indexing:** Todos os campos de query

---

## 9. REQUISITOS DE COMPLIANCE

### 9.1 Legal

- **GDPR compliance** (se aplicável)
- **KYC/AML** para subscrições
- **Terms of Service** documentados
- **Privacy Policy** disponível

### 9.2 Regulatory

- **Licença de jogo** (se aplicável)
- **Tax reporting** automático
- **Audit trail** completo
- **Responsible gambling** features

---

## 10. CRITÉRIOS DE ACEITAÇÃO

- ✅ **Escalável** horizontalmente sem downtime
- ✅ **Alta disponibilidade** (HA) com failover automático
- ✅ **Backup automático** com testes de restore mensais
- ✅ **Segurança** com MFA e encryption
- ✅ **Monitorização** com alertas em tempo real
- ✅ **Documentação** completa e atualizada
- ✅ **Testes de load** passados (2x peak expected)
- ✅ **Testes de segurança** passados (penetration testing)

---

## 11. LINKS CRUZADOS

- [[01_Vision_And_Strategy/INDEX]] ← Visão geral
- [[10_Infrastructure/INDEX]] → Detalhes de infraestrutura
- [[SYSTEM_ARCHITECTURE]] → Arquitetura do sistema
- [[VPS_CONFIGURACAO]] → Configuração VPS
- [[12_DevOps/INDEX]] → DevOps e CI/CD
