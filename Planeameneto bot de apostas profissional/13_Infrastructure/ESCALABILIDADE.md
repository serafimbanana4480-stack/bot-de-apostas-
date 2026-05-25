# ESCALABILIDADE — Quando e Como Escalar a Infraestrutura

**ID:** `INF-005` | **Fase:** #phase/6-15 | **Owner:** DevOps Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Definir critérios claros para quando escalar a infraestrutura e como fazer isso de forma custo-eficiente. Escala prematura é desperdício; escala tardia é perda de receita.

---

## 2. PRINCÍPIOS DE ESCALA

1. **Nunca escalar baseado em projeções** — escalar baseado em métricas reais
2. **Vertical antes de horizontal** — mais simples e mais barato até certo ponto
3. **Medir antes de escalar** — identificar bottleneck real (CPU, RAM, I/O, rede)
4. **Escalabilidade reversível** — deve ser possível fazer downgrade se necessário
5. **Custo por aposta** — escalar só se reduzir custo por aposta ou aumentar capacidade significativamente

---

## 3. CRITÉRIOS DE ESCALA POR COMPONENTE

### 3.1 VPS (Compute)

**Métricas de Monitorização:**
- CPU usage sustained > 70% por 24h
- RAM usage > 85% sustained
- Load average > número de CPUs sustained
- Latência de resposta > 5s para APIs críticas

**Ação:**
1. **Fase 1-6:** Upgrade vertical (Hetzner CPX21 → CPX31)
2. **Fase 7+:** Adicionar segundo VPS para load balancing

**Custo-benefício:**
- Upgrade CPX21→CPX31: +50€/mês para 2x CPU/RAM
- Segundo VPS: +60€/mês para 2x capacidade total

---

### 3.2 PostgreSQL (Database)

**Métricas de Monitorização:**
- Tamanho do BD > 100GB
- Queries analíticas > 10s consistentemente
- Cache hit ratio < 95%
- Lock waits > 100ms frequentes

**Ação:**
1. **Fase 1-6:** Tuning de queries + índices
2. **Fase 7-9:** Read replica para queries analíticas
3. **Fase 10+:** Managed service (RDS/Cloud SQL)

**Custo-benefício:**
- Read replica: +30€/mês
- Managed PostgreSQL: +50-80€/mês (inclui backups, HA)

---

### 3.3 Redis (Cache)

**Métricas de Monitorização:**
- Memória usage > 80%
- Operações/segundo > 10.000
- Latência > 10ms para GET/SET

**Ação:**
1. **Fase 1-6:** Aumentar max_memory e limpar keys expiradas
2. **Fase 7-9:** Upgrade VPS (mais RAM)
3. **Fase 10+:** Redis Cluster ou managed service

**Custo-benefício:**
- Redis Cluster: Complexidade operacional significativa
- Managed Redis: +30-50€/mês

---

### 3.4 Storage

**Métricas de Monitorização:**
- Disk usage > 80%
- I/O wait > 10%
- Backup size > 50GB

**Ação:**
1. **Fase 1-6:** Limpar logs antigos, comprimir backups
2. **Fase 7-9:** Adicionar disco secundário para backups
3. **Fase 10+:** S3 para backup + disco SSD maior

**Custo-benefício:**
- Disco adicional 100GB: +10€/mês
- S3 (500GB): +15-20€/mês

---

## 4. ESTRATÉGIAS DE ESCALA

### 4.1 Vertical Scale (Scale-Up)

**Vantagens:**
- Simples: apenas upgrade de plano
- Sem alterações na arquitetura
- Latência zero entre componentes
- Mais barato para pequenas escalas

**Desvantagens:**
- Limite máximo de hardware
- Single point of failure
- Downtime durante upgrade

**Quando usar:**
- Fase 1-6 (MVP)
- Até 2x capacidade atual
- Quando downtime de 5-10min é aceitável

---

### 4.2 Horizontal Scale (Scale-Out)

**Vantagens:**
- Teoricamente ilimitado
- Alta disponibilidade (se um cair, outros continuam)
- Pode adicionar/remover nós dinamicamente

**Desvantagens:**
- Complexidade operacional (load balancing, coordenação)
- Latência de rede entre componentes
- Custo por unidade é maior
- Requer arquitetura stateless

**Quando usar:**
- Fase 7+ (crescimento significativo)
- Quando alta disponibilidade é crítica
- Quando vertical scale atingiu limite

---

### 4.3 Hybrid Approach (Recomendado)

**Estratégia:**
1. **Fase 1-6:** Vertical scale (simples, barato)
2. **Fase 7-9:** Vertical + read replicas (melhor performance analítica)
3. **Fase 10+:** Horizontal para stateless, vertical para stateful

**Exemplo de arquitetura híbrida:**
```
[Load Balancer]
    ↓
[API Server 1] [API Server 2]  ← Horizontal (stateless)
    ↓              ↓
[PostgreSQL Primary] ← Vertical (stateful)
    ↓
[PostgreSQL Read Replica] ← Para queries analíticas
```

---

## 5. ROADMAP DE ESCALA

### Fase 1-6: MVP
- **VPS:** Hetzner CPX21 (4 vCPU, 8GB RAM)
- **PostgreSQL:** Instância local
- **Redis:** Instância local
- **Storage:** SSD local 100GB
- **Custo:** ~55€/mês

### Fase 7-9: Crescimento
- **VPS:** Hetzner CPX31 (8 vCPU, 16GB RAM) OU 2x CPX21
- **PostgreSQL:** Local + read replica
- **Redis:** Local (mais RAM)
- **Storage:** SSD 200GB + S3 para backups
- **Custo:** ~200-280€/mês

### Fase 10-12: Scale
- **VPS:** 3x CPX31 com load balancing
- **PostgreSQL:** Managed (RDS/Cloud SQL) Multi-AZ
- **Redis:** Managed (ElastiCache) Cluster mode
- **Storage:** SSD 500GB + S3 para backups
- **CDN:** Cloudflare para assets estáticos
- **Custo:** ~600-800€/mês

### Fase 13+: Enterprise
- **Kubernetes:** Para orquestração de containers
- **Multi-region:** Para latência global
- **Auto-scaling:** Baseado em métricas de tráfego
- **Custo:** ~1000-2000€/mês (dependendo da escala)

---

## 6. MONITORIZAÇÃO PARA ESCALA

### 6.1 Dashboard de Escala

Métricas críticas para monitorizar em Grafana:
- CPU, RAM, Disk usage por componente
- Queries por segundo na BD
- Latência de APIs (p50, p95, p99)
- Taxa de erros por serviço
- Custo por aposta (deve diminuir com escala)

### 6.2 Alertas de Escala

| Métrica | Threshold | Ação |
|---------|-----------|------|
| CPU sustained > 70% | 24h | Planejar upgrade |
| RAM sustained > 85% | 24h | Planejar upgrade |
| Disk > 80% | 1h | Limpar ou expandir |
| API latency p95 > 5s | 1h | Investigar bottleneck |
| Queries > 1000/s | 1h | Considerar cache/replica |

---

## 7. TESTE DE CARGA

### 7.1 Antes de Escalar

Sempre fazer teste de carga antes de escalar:
```bash
# Usar k6 ou locust para simular carga
k6 run --vus 100 --duration 5m load_test.js
```

### 7.2 Métricas de Teste

- Throughput: requisições/segundo
- Latência: p50, p95, p99
- Error rate: % de falhas
- Resource utilization: CPU, RAM, I/O durante teste

**Critério de escala:** Se qualquer métrica degradar > 20% com carga +50%, considerar escala.

---

## 8. ROLLBACK PLAN

### 8.1 Se Escala Falhar

1. **Vertical scale failed:** Reverter para plano anterior em 24h
2. **Horizontal scale failed:** Remover nó adicional, redirecionar tráfego
3. **Managed service failed:** Migrar de volta para local (ter backup recente)

### 8.2 Mitigação de Risco

- Sempre ter backup recente antes de escala
- Testar escala em staging primeiro
- Ter rollback plan documentado
- Monitorizar intensivamente por 48h pós-escala

---

## 9. LINKS CRUZADOS

- [[13_Infrastructure/INDEX]] ← Secção mãe
- [[CUSTOS_INFRA]] → Análise de custos de escala
- [[VPS_CONFIGURACAO]] → Configuração base