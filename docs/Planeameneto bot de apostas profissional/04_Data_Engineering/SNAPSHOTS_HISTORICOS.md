# SNAPSHOTS HISTÓRICOS E VERSIONAMENTO DE DADOS

**ID:** `SEC-04-02` | **Fase:** #phase/1 | **Owner:** Data Engineer | **Status:** #status/pending  
**Última Atualização:** `2026-05-13`

---

## 1. CONCEITOS FUNDAMENTAIS

| Conceito | Definição |
|----------|-----------|
| **Snapshot** | Cópia imutável de um dataset num ponto específico no tempo |
| **Backup** | Cópia de segurança para recuperação de desastres |
| **Imutabilidade** | Dados raw (Bronze) nunca são alterados — apenas appended |
| **Point-in-Time Query** | Capacidade de reconstruir o estado dos dados em qualquer data passada |
| **Data Lineage** | Rastreabilidade de cada valor desde a fonte até ao modelo |

**Princípio central:** Os dados de treino devem ser reprodutíveis. Qualquer modelo deve poder ser re-treinado com exatamente os mesmos dados que o produziram originalmente.

---

## 2. ARQUITETURA DE SNAPSHOTS

```
Dados de Produção (PostgreSQL)
        │
        ▼
  Snapshot Process (cron diário 03:00 UTC)
        │
        ├─► Bronze Snapshot
        │       • Cópia comprimida de raw_odds + raw_games
        │       • Formato: Parquet particionado por data
        │       • Localização: /data/snapshots/bronze/YYYY-MM-DD/
        │       • Retenção: INDEFINIDA
        │
        ├─► Silver Snapshot
        │       • Cópia de odds_cleaned + features_base
        │       • Formato: Parquet + metadata JSON
        │       • Localização: /data/snapshots/silver/YYYY-MM-DD/
        │       • Retenção: 5 anos
        │
        └─► Gold Snapshot
                • Dataset de treino completo para cada modelo
                • Formato: Parquet + config JSON (features, splits)
                • Localização: /data/snapshots/gold/YYYY-MM-DD/MODEL_VERSION/
                • Retenção: 3 anos (mínimo)
```

---

## 3. FREQUÊNCIA DE SNAPSHOTS

| Tipo | Frequência | Hora | Trigger |
|------|-----------|------|---------|
| Bronze daily | Diário | 03:00 UTC | Cron automático |
| Silver daily | Diário | 04:00 UTC | Após Bronze |
| Gold (pre-treino) | Antes de cada treino | — | Manual / MLflow trigger |
| Emergency snapshot | Sob demanda | — | Antes de migrações/atualizações |

---

## 4. POLÍTICA DE RETENÇÃO

| Camada | Retenção | Justificação |
|--------|----------|--------------|
| Bronze | Indefinida | Dados raw são irreproduziveis — nunca apagar |
| Silver | 5 anos | Compliance, auditoria, e re-treino de longo prazo |
| Gold | 3 anos | Reprodutibilidade de modelos em produção |
| Backups PostgreSQL | 90 dias rolling | Recuperação de desastres |

**Custo estimado de armazenamento:** ~500MB/mês (5 épocas NBA de dados de odds).

---

## 5. CATÁLOGO DE SNAPSHOTS

Cada snapshot regista metadados num catálogo central:

```sql
CREATE TABLE snapshot_catalog (
    id              BIGSERIAL PRIMARY KEY,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    snapshot_date   DATE NOT NULL,
    layer           VARCHAR(10) NOT NULL,   -- 'bronze', 'silver', 'gold'
    path            TEXT NOT NULL,
    size_bytes      BIGINT,
    n_records       BIGINT,
    checksum_md5    VARCHAR(32),
    model_version   VARCHAR(50),            -- Se Gold, modelo associado
    notes           TEXT,
    is_valid        BOOLEAN DEFAULT TRUE
);
```

---

## 6. PROCESSO DE CRIAÇÃO DE SNAPSHOT

```python
def create_daily_snapshot(layer: str, snapshot_date: date) -> SnapshotRecord:
    """
    Processo:
    1. Preparação: verificar espaço em disco e lock de escrita
    2. Export: pg_dump ou COPY TO Parquet
    3. Compressão: gzip ou snappy
    4. Validação: checksum MD5, contagem de registos
    5. Registo no catálogo
    6. Alerta Telegram de sucesso/falha
    """
    pass


def validate_snapshot(path: str, expected_records: int) -> bool:
    """
    Valida que o snapshot foi criado corretamente:
    - Ficheiro existe e não está corrompido
    - Número de registos corresponde ao esperado
    - Checksum MD5 calculado e registado
    """
    pass
```

---

## 7. PROCESSO DE RESTORE

```bash
# 1. Identificar snapshot a restaurar
SELECT * FROM snapshot_catalog
WHERE snapshot_date = '2026-03-15' AND layer = 'silver'
ORDER BY created_at DESC LIMIT 1;

# 2. Verificar integridade do snapshot
python -m scripts.validate_snapshot --path /data/snapshots/silver/2026-03-15/

# 3. Restore para ambiente de staging primeiro
python -m scripts.restore_snapshot \
    --path /data/snapshots/silver/2026-03-15/ \
    --target staging_db \
    --dry-run

# 4. Após validação, restore para produção
python -m scripts.restore_snapshot \
    --path /data/snapshots/silver/2026-03-15/ \
    --target prod_db \
    --confirm
```

**⚠️ Nunca fazer restore direto para produção sem dry-run e aprovação.**

---

## 8. SNAPSHOTS PARA RE-TREINO DE MODELOS

Antes de re-treinar um modelo, o pipeline deve:

```python
def prepare_training_snapshot(
    model_id: str,
    feature_config: dict,
    date_range: tuple[date, date]
) -> str:
    """
    Cria um Gold snapshot com:
    - Features calculadas com a configuração atual
    - Split temporal train/validation definido
    - Metadata completo (config, features, versões)
    - Registado no MLflow como artefacto
    
    Returns: path do snapshot para uso no treino
    """
    pass
```

---

## 9. MONITORIZAÇÃO

| Métrica | Alerta |
|---------|--------|
| Snapshot diário falhou | Telegram imediato |
| Tamanho snapshot < 80% do esperado | Warning — possível perda de dados |
| Checksum inválido | Crítico — snapshot corrompido |
| Disco < 20% disponível | Warning — planear expansão |

---

## 10. BACKLOG

- [ ] Criar script `create_daily_snapshot.py` (Fase 1, Semana 2)
- [ ] Criar tabela `snapshot_catalog` em PostgreSQL
- [ ] Configurar cron jobs (03:00 e 04:00 UTC)
- [ ] Implementar validação e alertas
- [ ] Testar restore completo (simulação de disaster recovery)
- [ ] Documentar SLA de restore (objetivo: < 4 horas)

---

## 11. LINKS CRUZADOS

- [[04_Data_Engineering/INDEX]] ← Secção mãe
- [[04_Data_Engineering/INGESTAO_ODDS]] → Dados que são snapshotados
- [[15_Database/INDEX]] → Backups PostgreSQL
- [[29_Experiment_Tracking/INDEX]] → Gold snapshots ligados a experimentos MLflow
- [[28_Failure_Scenarios/CENARIOS_FALHA]] → Plano de DR
