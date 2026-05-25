# SCALING_DECISIONS — Decisões de Scaling

**ID:** `ARCH-003` | **Fase:** #phase/4-6 | **Owner:** System Architect | **Status:** #status/active

---

## 1. OBJETIVO

Definir critérios para escalar o sistema horizontalmente.

---

## 2. TRIGGERS DE SCALING

| Métrica | Trigger | Ação |
|---------|---------|------|
| CPU | > 80% por 5 min | Adicionar instância |
| Memória | > 85% por 5 min | Adicionar instância |
| Throughput | < 5 sinais/s | Adicionar instância |
| Latência | > 200ms | Adicionar instância |

---

## 3. AUTO-SCALING

```python
def check_scaling_needs():
    """Verifica se scaling é necessário."""
    metrics = get_system_metrics()
    
    needs_scaling = False
    
    if metrics['cpu'] > 0.80:
        logger.warning("CPU alta - considerar scaling")
        needs_scaling = True
    
    if metrics['memory'] > 0.85:
        logger.warning("Memória alta - considerar scaling")
        needs_scaling = True
    
    if needs_scaling:
        scale_up()
```

---

## 4. SCALE UP

```python
def scale_up():
    """Adiciona nova instância."""
    # 1. Provisionar nova VM
    new_instance = provision_vm()
    
    # 2. Configurar
    configure_instance(new_instance)
    
    # 3. Adicionar ao load balancer
    add_to_load_balancer(new_instance)
    
    logger.info(f"Instância {new_instance} adicionada")
```

---

## 5. SCALE DOWN

```python
def scale_down():
    """Remove instância ociosa."""
    # 1. Identificar instância menos utilizada
    idle_instance = find_idle_instance()
    
    # 2. Remover do load balancer
    remove_from_load_balancer(idle_instance)
    
    # 3. Terminar instância
    terminate_vm(idle_instance)
    
    logger.info(f"Instância {idle_instance} removida")
```

---

## 6. CRITÉRIOS

- **Auto-scaling** baseado em métricas
- **Mínimo 2 instâncias** para HA
- **Máximo 10 instâncias** por custo

---

## 7. LINKS CRUZADOS

- [[01_Vision_And_Strategy/INDEX]]
- [[SYSTEM_ARCHITECTURE]]
