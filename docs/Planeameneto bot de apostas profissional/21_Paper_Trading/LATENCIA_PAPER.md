# Latência Paper Trading

**ID:** PAPER-004 | **Fase:** #phase/3 | **Owner:** Principal Quant Engineer | **Status:** #status/draft

---

## 1. RESUMO EXECUTIVO

Medição de latência operacional em paper trading e impacto nas odds obtidas. Latência é o tempo entre geração de sinal e disponibilidade de odds.

| Campo | Descrição |
|-------|-----------|
| **Objetivo** | Medir impacto da latência nas odds obtidas em paper trading |
| **Métricas** | Tempo sinal → odd, odd decay, fill rate |
| **Thresholds** | Latência < 30s, odd decay < 2% |
| **Custo** | 0€ (monitorização) |

---

## 2. FONTES DE LATÊNCIA

### 2.1 Pipeline de Sinais

```
┌─────────────────────────────────────────────────────────────┐
│ 1. GERAÇÃO DE SINAL                                        │
│    - Modelo infere probabilidade                           │
│    - Edge é calculado                                       │
│    - Filtros são aplicados                                  │
│    Tempo: ~1s                                               │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. REGISTRO NA BD                                          │
│    - Sinal é persistido                                     │
│    - Timestamp é registado                                 │
│    Tempo: ~100ms                                           │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. CAPTURA DE ODD                                          │
│    - API é consultada                                       │
│    - Odd atual é obtida                                     │
│    Tempo: ~500ms (API)                                      │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. VALIDAÇÃO E ENVIO                                        │
│    - Odd é validada                                         │
│    - Sinal é enviado para operador                          │
│    Tempo: ~200ms                                            │
└─────────────────────────────────────────────────────────────┘
```

**Latência total:** ~2s (ideal)

### 2.2 Fontes de Atraso

| Fonte | Impacto | Mitigação |
|-------|---------|-----------|
| Processamento do modelo | 1s | Otimizar modelo, usar GPU |
| Latência de API | 500ms | Cache, múltiplas APIs |
| Latência de BD | 100ms | Índices, otimizar queries |
| Latência de rede | 50ms | Servidor próximo às APIs |
| Atraso humano (se manual) | Variável | Automatizar |

---

## 3. MEDIDAS DE LATÊNCIA

### 3.1 Métricas

```python
# Tempo entre geração de sinal e captura de odd
signal_to_odd_latency = odd_timestamp - signal_timestamp

# Decay de odd (quanto a odd mudou desde o sinal)
odd_decay = (odd_signal - odd_obtained) / odd_signal

# Fill rate (percentual de sinais executados)
fill_rate = signals_executed / signals_total
```

### 3.2 Thresholds

| Métrica | Excelente | Aceitável | Crítico |
|---------|-----------|-----------|---------|
| signal_to_odd_latency | < 5s | < 30s | > 60s |
| odd_decay | < 1% | < 2% | > 5% |
| fill_rate | > 95% | > 80% | < 70% |

---

## 4. IMPACTO NA PERFORMANCE

### 4.1 Odd Decay vs CLV

```python
# Quanto o CLV cai com odd decay
clv_decay = clv_signal * (1 - odd_decay)

# Exemplo
clv_signal = 5%
odd_decay = 2%
clv_decay = 5% * (1 - 0.02) = 4.9%
```

### 4.2 Latência vs Fill Rate

```python
# Quanto a fill rate cai com latência
fill_rate = max(0, 1 - (latency / max_latency))

# Exemplo
latency = 30s
max_latency = 60s
fill_rate = 1 - (30/60) = 50%
```

---

## 5. MONITORIZAÇÃO

### 5.1 Dashboard de Latência

```
┌─────────────────────────────────────────────────────────────┐
│ LATÊNCIA PAPER TRADING - [DATA]                            │
├─────────────────────────────────────────────────────────────┤
│ Latência Média: 12.3s (target: < 30s) ✅                   │
│ Odd Decay Médio: 0.8% (target: < 2%) ✅                    │
│ Fill Rate: 92% (target: > 80%) ✅                           │
├─────────────────────────────────────────────────────────────┤
│ Distribuição de Latência:                                   │
│ ████ 0-5s: 40%                                             │
│ ████ 5-10s: 30%                                            │
│ ██ 10-20s: 20%                                             │
│ █ 20-30s: 10%                                              │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Alertas

```python
# Alerta se latência > threshold
if signal_to_odd_latency > 30:
    send_alert("Latência crítica", latency)

# Alerta se odd decay > threshold
if odd_decay > 0.02:
    send_alert("Odd decay crítico", decay)

# Alerta se fill rate < threshold
if fill_rate < 0.8:
    send_alert("Fill rate crítico", fill_rate)
```

---

## 6. OTIMIZAÇÃO

### 6.1 Reduzir Latência

- **Modelo:** Otimizar, usar GPU, quantização
- **API:** Cache, múltiplas APIs em paralelo
- **BD:** Índices, queries otimizadas
- **Rede:** Servidor próximo, CDN

### 6.2 Reduzir Odd Decay

- **Previsão:** Gerar sinais mais cedo
- **Cache:** Cache de odds
- **APIs:** Múltiplas APIs, best price

### 6.7 Aumentar Fill Rate

- **Latência:** Reduzir latência (ver acima)
- **Thresholds:** Aumentar thresholds de edge
- **Liquidez:** Verificar liquidez antes de sinal

---

## 7. FERRAMENTAS DE MONITORIZAÇÃO

```python
# vbq/monitoring/latency_monitor.py
import time
import logging

logger = logging.getLogger(__name__)

class LatencyMonitor:
    """Monitora latência de sinais"""
    
    def __init__(self, db):
        self.db = db
    
    def record_signal_latency(self, signal_id: str, odd_timestamp: float):
        """Registra latência de sinal"""
        signal = self.db.get_signal(signal_id)
        latency = odd_timestamp - signal['timestamp']
        
        self.db.insert('latency_metrics', {
            'signal_id': signal_id,
            'latency': latency,
            'odd_decay': self.calculate_odd_decay(signal, odd_timestamp),
            'timestamp': time.time()
        })
        
        # Alerta se crítico
        if latency > 30:
            logger.warning(f"Latência crítica: {latency}s")
    
    def calculate_odd_decay(self, signal: dict, odd_timestamp: float) -> float:
        """Calcula decay de odd"""
        odd_signal = signal['odd']
        odd_obtained = self.get_odd_at_time(odd_timestamp)
        
        return (odd_signal - odd_obtained) / odd_signal
```

---

## 8. LINKS CRUZADOS

- [[21_Paper_Trading/INDEX]] ← Secção mãe
- [[LATENCIA_EXECUCAO]] → Latência em execução real
- [[09_Execution_System/INDEX]] → Sistema de execução
- [[14_APIs/INDEX]] → APIs e latência

---

**Custo de implementação:** 0€ (monitorização)  
**Tempo estimado de implementação:** 3-5 dias  
**Prioridade:** MÉDIA (importante para operacionalidade)
