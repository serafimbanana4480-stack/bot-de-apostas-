# SUNSET_POLICY — Política de Sunset

**ID:** `ORG-004` | **Fase:** #phase/1 | **Owner:** Project Manager | **Status:** #status/active

---

## 1. OBJETIVO

Definir política para descontinuar componentes do sistema.

---

## 2. CRITÉRIOS PARA SUNSET

| Critério | Threshold |
|----------|-----------|
| Sem uso por | 90 dias |
| Bugs não resolvidos | > 5 |
| Custo de manutenção | > valor gerado |
| Dependência obsoleta | Sim |

---

## 3. PROCESSO DE SUNSET

```python
def initiate_sunset(component):
    """
    Inicia processo de sunset.
    
    Passos:
    1. Notificar stakeholders
    2. Definir timeline (30 dias)
    3. Documentar migração
    4. Executar sunset
    """
    # 1. Notificar
    notify_stakeholders(component)
    
    # 2. Timeline
    sunset_date = datetime.now() + timedelta(days=30)
    
    # 3. Documentar
    document_migration(component)
    
    # 4. Executar
    schedule_sunset(component, sunset_date)
```

---

## 4. COMUNICAÇÃO

- **30 dias antes:** Notificação preliminar
- **7 dias antes:** Aviso final
- **Dia do sunset:** Confirmar descontinuação

---

## 5. CRITÉRIOS

- **Aviso mínimo 30 dias**
- **Documentação de migração**
- **Backup dos dados**

---

## 6. LINKS CRUZADOS

- [[01_Vision_And_Strategy/INDEX]]
- [[TEAM_ROLES]]
