# ROLLBACK_PROCEDURES — Procedimentos de Rollback

**ID:** `OP-018` | **Fase:** #phase/3 | **Owner:** Operations Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Definir procedimentos de rollback para reversão de mudanças.

---

## 2. TIPOS DE ROLLBACK

| Tipo | Quando usar | Duração |
|------|-------------|---------|
| Rollback de código | Deploy falhou | < 5 min |
| Rollback de modelo | Performance caiu | < 10 min |
| Rollback de schema | Migração falhou | < 30 min |
| Rollback de config | Configuração errada | < 5 min |

---

## 3. ROLLBACK DE CÓDIGO

```python
def rollback_code(deploy_id):
    """
    Rollback de código para versão anterior.
    
    Args:
        deploy_id: ID do deploy a reverter
    """
    # 1. Identificar versão anterior
    previous_version = get_previous_version(deploy_id)
    
    # 2. Deploy da versão anterior
    deploy_version(previous_version)
    
    # 3. Verificar saúde
    if system_health_check()['overall']:
        logger.info(f"Rollback para {previous_version} bem-sucedido")
    else:
        raise Exception("Rollback falhou")
```

---

## 4. ROLLBACK DE MODELO

```python
def rollback_model():
    """Rollback para modelo anterior."""
    # 1. Restaurar backup do modelo
    restore_model_backup()
    
    # 2. Atualizar configuração
    update_model_config(previous_model_version)
    
    # 3. Reiniciar serviço de inferência
    restart_inference_service()
    
    logger.info("Rollback de modelo executado")
```

---

## 5. ROLLBACK DE SCHEMA

```python
def rollback_schema(migration_id):
    """
    Rollback de schema de base de dados.
    
    Args:
        migration_id: ID da migração a reverter
    """
    # 1. Obter SQL de rollback
    rollback_sql = get_rollback_sql(migration_id)
    
    # 2. Executar rollback
    db.execute(rollback_sql)
    
    # 3. Validar schema
    if validate_schema():
        logger.info(f"Rollback de {migration_id} bem-sucedido")
    else:
        raise Exception("Rollback de schema falhou")
```

---

## 6. CRITÉRIOS

- **Backup antes** de qualquer mudança
- **Rollback < 30 min** para qualquer mudança
- **Validar após rollback**

---

## 7. LINKS CRUZADOS

- [[07_Execution/INDEX]]
- [[SOP_DEPLOY_MODELO]]
