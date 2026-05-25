# SCHEMA_EVOLUTION — Gestão de Mudanças no Schema da Base de Dados

**ID:** `ENG-005` | **Fase:** #phase/1-15 | **Owner:** Lead Data Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Gerir mudanças no schema da base de dados de forma controlada, sem breaking changes, e com capacidade de rollback. Schema evolution é crítico para evitar perda de dados e downtime.

---

## 2. PRINCÍPIOS

1. **Backward compatibility** — Novo schema deve funcionar com versão anterior da aplicação
2. **Non-breaking changes** — Adicionar colunas é seguro; remover/drop requer migração
3. **Versioned migrations** — Cada mudança tem script SQL versionado
4. **Test before deploy** — Migrations testadas em staging primeiro
5. **Rollback always possible** — Cada migration tem script de rollback

---

## 3. TIPOS DE MUDANÇAS

### 3.1 Safe (Non-Breaking)

| Operação | Exemplo | Rollback |
|----------|---------|----------|
| ADD COLUMN | `ALTER TABLE games ADD COLUMN attendance INT;` | `ALTER TABLE games DROP COLUMN attendance;` |
| ADD INDEX | `CREATE INDEX idx_games_date ON games(game_date);` | `DROP INDEX idx_games_date;` |
| RENAME TABLE | `ALTER TABLE games RENAME TO matches;` | `ALTER TABLE matches RENAME TO games;` |
| ADD CONSTRAINT | `ALTER TABLE games ADD CONSTRAINT chk_date CHECK (game_date > '2018-01-01');` | `ALTER TABLE games DROP CONSTRAINT chk_date;` |

### 3.2 Unsafe (Breaking)

| Operação | Exemplo | Mitigação |
|----------|---------|-----------|
| DROP COLUMN | `ALTER TABLE games DROP COLUMN attendance;` | Deprecate primeiro, remover depois |
| CHANGE TYPE | `ALTER TABLE games ALTER COLUMN attendance TYPE BIGINT;` | Criar nova coluna, migrar dados, depois drop |
| RENAME COLUMN | `ALTER TABLE games RENAME COLUMN attendance TO fans;` | Criar nova coluna, migrar, depois drop |
| DROP TABLE | `DROP TABLE games_backup;` | Backup antes, confirmar não usado |

---

## 4. PROCESSO DE MIGRATION

### 4.1 Ferramenta

Usar **Alembic** (Python) para migrations:

```python
# alembic/env.py
from alembic import context
from sqlalchemy import engine_from_config

config = context.config
target_metadata = Base.metadata

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
```

### 4.2 Estrutura de Migrations

```
alembic/versions/
  ├── 001_initial_schema.py
  ├── 002_add_betting_stats.py
  ├── 003_add_player_props.py
  └── ...
```

### 4.3 Template de Migration

```python
# alembic/versions/002_add_betting_stats.py
"""add betting stats

Revision ID: 002
Revises: 001
Create Date: 2026-05-13

"""
from alembic import op
import sqlalchemy as sa

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade():
    # Adicionar colunas novas
    op.add_column('games', sa.Column('home_win_prob', sa.Float(), nullable=True))
    op.add_column('games', sa.Column('away_win_prob', sa.Float(), nullable=True))
    
    # Criar índices
    op.create_index('idx_games_home_prob', 'games', ['home_win_prob'])

def downgrade():
    # Rollback: remover na ordem inversa
    op.drop_index('idx_games_home_prob', 'games')
    op.drop_column('games', 'away_win_prob')
    op.drop_column('games', 'home_win_prob')
```

---

## 5. ESTRATÉGIAS DE MIGRATION

### 5.1 Adicionar Coluna Obrigatória

**Problema:** Não pode adicionar coluna NOT NULL sem default value.

**Solução:**
```python
def upgrade():
    # Passo 1: Adicionar como nullable
    op.add_column('games', sa.Column('new_field', sa.Integer(), nullable=True))
    
    # Passo 2: Backfill dados (em script separado)
    # UPDATE games SET new_field = 0 WHERE new_field IS NULL;
    
    # Passo 3: Alterar para NOT NULL (em migration separada)
    # op.alter_column('games', 'new_field', nullable=False)
```

### 5.2 Renomear Coluna

**Problema:** Aplicação antiga quebra se coluna renomeada.

**Solução:**
```python
def upgrade():
    # Passo 1: Adicionar nova coluna
    op.add_column('games', sa.Column('new_name', sa.Integer(), nullable=True))
    
    # Passo 2: Copiar dados
    op.execute("UPDATE games SET new_name = old_name")
    
    # Passo 3: Deploy nova versão da app que usa new_name
    
    # Passo 4: Remover coluna antiga (migration separada)
    # op.drop_column('games', 'old_name')
```

### 5.3 Mudar Tipo de Dado

**Problema:** Casting pode falhar se dados incompatíveis.

**Solução:**
```python
def upgrade():
    # Passo 1: Adicionar coluna temporária com novo tipo
    op.add_column('games', sa.Column('value_temp', sa.Numeric(10,2), nullable=True))
    
    # Passo 2: Migrar dados com validação
    op.execute("""
        UPDATE games 
        SET value_temp = CAST(value AS NUMERIC(10,2))
        WHERE value IS NOT NULL
    """)
    
    # Passo 3: Verificar se há NULLs inesperados
    # SELECT COUNT(*) FROM games WHERE value_temp IS NULL AND value IS NOT NULL;
    
    # Passo 4: Drop coluna antiga e renomear temp
    op.drop_column('games', 'value')
    op.alter_column('games', 'value_temp', new_column_name='value')
```

---

## 6. DEPLOYMENT DE MIGRATIONS

### 6.1 Checklist Pre-Deploy

- [ ] Migration testada em staging com dados reais
- [ ] Rollback testado em staging
- [ ] Backup da BD feito antes de deploy
- [ ] Tempo estimado de migration documentado
- [ ] Janela de manutenção agendada se > 5 minutos
- [ ] Notificação aos stakeholders se downtime esperado

### 6.2 Processo de Deploy

```bash
# 1. Backup
pg_dump valuebetting > backup_pre_migration_$(date +%Y%m%d).sql

# 2. Aplicar migration
alembic upgrade head

# 3. Verificar
alembic current
alembic history

# 4. Testar aplicação
# (executar suíte de testes)

# 5. Se falhar, rollback
alembic downgrade -1
```

---

## 7. MONITORIZAÇÃO

### 7.1 Métricas

- Número de migrations aplicadas
- Tempo de última migration
- Falhas de migration (logs)
- Tamanho das tabelas pós-migration

### 7.2 Alertas

- Migration falha → Alerta CRITICAL
- Migration > 10 minutos → Alerta HIGH
- Migration sem backup prévio → Alerta CRITICAL

---

## 8. MELHORES PRÁTICAS

1. **Uma migration, uma mudança** — Não combinar múltiplas mudanças numa migration
2. **Idempotent** — Migration pode ser re-executada sem erro
3. **Fast** — Migrations devem ser < 5 minutos na maioria dos casos
4. **Documented** — Comentários explicando PORQUÊ da mudança
5. **Reviewed** — Code review obrigatório para migrations
6. **Tested** — Testes automatizados para migrations críticas

---

## 9. TROUBLESHOOTING

### Migration falha a meio

```bash
# Verificar estado
alembic current

# Forçar versão específica (cuidado!)
alembic stamp head

# Rollback manual se necessário
# (editar schema manualmente e alembic stamp)
```

### Dados corrompidos pós-migration

```bash
# Restore backup
psql valuebetting < backup_pre_migration_20260513.sql

# Re-aplicar migration
alembic upgrade head
```

---

## 10. LINKS CRUZADOS

- [[04_Data_Engineering/INDEX]] ← Secção mãe
- [[15_Database/INDEX]] → Schema detalhado
- [[12_DevOps/INDEX]] → CI/CD de migrations