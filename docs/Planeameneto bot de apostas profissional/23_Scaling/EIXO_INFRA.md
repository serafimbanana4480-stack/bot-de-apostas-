# EIXO_INFRA — Decisões de Scaling Baseadas em Tendências

**ID:** `SCAL-001` | **Fase:** #phase/7+ | **Owner:** DevOps Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Definir quando e como escalar a infraestrutura baseado em métricas e tendências do sistema.

---

## 2. MÉTRICAS DE SCALING

### 2.1 Métricas de Capacidade
- **CPU Usage:** % de utilização média (5min)
- **Memory Usage:** % de RAM utilizada
- **Disk I/O:** IOPS e throughput
- **Network I/O:** Bandwidth utilizada
- **Database Connections:** % de conexões ativas
- **Queue Length:** Tamanho da fila de tarefas

### 2.2 Métricas de Negócio
- **Número de Apostas/dia:** Volume de operações
- **Latência de Execução:** Tempo médio para executar aposta
- **Taxa de Rejeição:** % de apostas rejeitadas
- **Bankroll:** Tamanho da banca (afeta stakes)

---

## 3. TRIGGERS DE SCALING

### 3.1 Vertical Scaling (Escalonamento)

#### CPU
- **Warning:** > 70% sustained por 30min
- **Critical:** > 90% sustained por 10min
- **Ação:** Aumentar vCPUs em 50%

#### Memory
- **Warning:** > 80% sustained por 30min
- **Critical:** > 95% sustained por 10min
- **Ação:** Aumentar RAM em 50%

#### Database
- **Warning:** > 80% conexões utilizadas
- **Critical:** > 95% conexões utilizadas
- **Ação:** Aumentar max_connections ou escalar DB

### 3.2 Horizontal Scaling (Distribuição)

#### Volume de Apostas
- **Trigger:** > 1000 apostas/dia
- **Ação:** Considerar worker adicional
- **Trigger:** > 5000 apostas/dia
- **Ação:** Implementar multiple workers

#### Latência
- **Warning:** p95 > 1000ms
- **Critical:** p95 > 2000ms
- **Ação:** Distribuir carga ou otimizar queries

---

## 4. ESTRATÉGIAS DE SCALING

### 4.1 Escalonamento Vertical (Scale Up)

**Quando usar:**
- Fases iniciais (4-6)
- Bankroll pequena
- Tráfego previsível

**Custos:**
- VPS 4 vCPU, 8GB RAM: ~50€/mês
- VPS 8 vCPU, 16GB RAM: ~100€/mês
- VPS 16 vCPU, 32GB RAM: ~200€/mês

**Vantagens:**
- Simples de implementar
- Sem complexidade de distribuição
- Menor latência

**Desvantagens:**
- Limite físico
- Single point of failure
- Custo cresce linearmente

### 4.2 Escalonamento Horizontal (Scale Out)

**Quando usar:**
- Fases avançadas (7+)
- Bankroll média/grande
- Tráfego variável ou crescente

**Arquitetura:**
```
Load Balancer → Worker 1, Worker 2, Worker 3
                ↓
              Shared Database
              Shared Redis
```

**Custos:**
- 3x VPS 4 vCPU, 8GB RAM: ~150€/mês
- Load Balancer: ~30€/mês
- Managed Redis: ~50€/mês

**Vantagens:**
- Escala quase ilimitada
- Redundância
- Melhor fault tolerance

**Desvantagens:**
- Complexidade de implementação
- Latência adicional
- Sincronização de estado

---

## 5. MATRIZ DE SCALING POR FASE

| Fase | Bankroll | Apostas/dia | Infraestrutura | Custo |
|------|----------|-------------|----------------|-------|
| 4-6 | €100-500 | < 50 | 1x VPS 2vCPU/4GB | ~30€ |
| 7-9 | €500-2000 | 50-200 | 1x VPS 4vCPU/8GB | ~50€ |
| 10-12 | €2000-10000 | 200-500 | 1x VPS 8vCPU/16GB | ~100€ |
| 13-15 | €10000-50000 | 500-1000 | 2x VPS 4vCPU/8GB | ~100€ |
| 16+ | €50000+ | > 1000 | 3x VPS + LB | ~200€+ |

---

## 6. AUTOMAÇÃO DE SCALING

### 6.1 Scripts de Monitorização
```python
# check_scaling_triggers.py
def check_cpu_trigger():
    cpu = psutil.cpu_percent(interval=300)  # 5min average
    if cpu > 90:
        trigger_alert("CPU_CRITICAL", cpu)
        return True
    elif cpu > 70:
        trigger_alert("CPU_WARNING", cpu)
    return False

def check_memory_trigger():
    mem = psutil.virtual_memory().percent
    if mem > 95:
        trigger_alert("MEMORY_CRITICAL", mem)
        return True
    elif mem > 80:
        trigger_alert("MEMORY_WARNING", mem)
    return False
```

### 6.2 Auto-scaling (Futuro)
```yaml
# terraform/aws_autoscaling.tf
resource "aws_autoscaling_group" "betting_bot" {
  min_size = 2
  max_size = 10
  desired_capacity = 2
  
  launch_template {
    id = aws_launch_template.betting_bot.id
  }
}
```

---

## 7. PROCEDIMENTO DE SCALING

### 7.1 Vertical Scaling
1. Analisar métricas de capacidade
2. Identificar bottleneck específico
3. Planear downtime (se necessário)
4. Aumentar recursos no VPS
5. Verificar melhoria
6. Monitorizar por 24h

### 7.2 Horizontal Scaling
1. Preparar arquitetura distribuída
2. Implementar shared state (Redis, DB)
3. Configurar load balancer
4. Deploy em múltiplos workers
5. Testar distribuição de carga
6. Monitorizar e ajustar

---

## 8. BACKLOG

- [ ] Implementar auto-scaling automático
- [ ] Migrar para cloud provider (AWS/GCP)
- [ ] Implementar serverless para componentes não-críticos
- [ ] Adicionar CDN para assets estáticos

---

## 9. LINKS CRUZADOS

- [[23_Scaling/INDEX]] ← Secção mãe
- [[23_Scaling/ESCALA_BANCA]] → Scaling baseado em banca
- [[13_Infrastructure/ESCALABILIDADE]] → Estratégias de escalabilidade
