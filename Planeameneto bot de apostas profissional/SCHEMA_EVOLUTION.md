# SCHEMA_EVOLUTION — Evolução de Schema

**ID:** `DB-004` | **Fase:** #phase/1 | **Owner:** Data Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Gerir evolução do schema de base de dados de forma controlada.

---

## 2. MIGRAÇÕES

```python
def run_migration(migration_file):
    """
    Executa migração de schema.
    
    Args:
        migration_file: Ficheiro SQL de migração
    """
    # 1. Backup do schema atual
    backup_schema()
    
    # 2. Executar migração
    with open(migration_file) as f:
        sql = f.read()
        db.execute(sql)
    
    # 3. Validar schema
    if validate_schema():
        logger.info(f"Migração {migration_file} executada com sucesso")
    else:
        # Rollback
        rollback_schema()
        raise Exception("Validação falhou - rollback executado")
```

---

## 3. VERSIONAMENTO

Migrações versionadas com timestamp:

```
migrations/
├── 20240101_001_add_bets_table.sql
├── 20240115_002_add_features_table.sql
├── 20240201_003_add_odds_table.sql
└── ...
```

---

## 4. TIPOS DE MUDANÇA

| Tipo | Exemplo | Risco |
|------|---------|-------|
| Adicionar coluna | Nova feature | Baixo |
| Remover coluna | Feature obsoleta | Médio |
| Renomear tabela | Refatoração | Médio |
| Alterar tipo | Mudança de tipo | Alto |

---

## 5. CRITÉRIOS

- **Migrações versionadas**
- **Backup antes** de cada migração
- **Rollback automático** se falhar

---

## 6. LINKS CRUZADOS

- [[04_Data_Engineering/INDEX]]
- [[SQL_MODELO]]
