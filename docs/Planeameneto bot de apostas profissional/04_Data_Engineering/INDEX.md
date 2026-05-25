# 04_Data_Engineering — INDEX

**ID:** `SEC-04` | **Fase:** #phase/1 | **Owner:** Lead Data Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Garantir que os dados que alimentam o sistema são **correctos, completos, temporariamente válidos e auditáveis**. Um modelo quantitativo é tão bom quanto os seus dados. Um erro de dados é pior que um erro de modelo — é invisível até causar perdas massivas.

---

## 2. NOTAS FUNDAMENTAIS

- [[PIPELINE_ETL_NBA]] — Ingestão de estatísticas NBA, odds, calendário
- [[ESQUEMA_BASE_DADOS]] — Schema PostgreSQL, tabelas, índices, constraints
- [[DEDUPLICACAO_E_LIMPEZA]] — Regras de deduplicação, tratamento de missing values
- [[SCHEMA_EVOLUTION]] — Como alterar schema sem breaking changes
- [[INGESTAO_ODDS]] — Fontes de odds, sincronização, late arriving data
- [[MULTI_SOURCE_AGGREGATION]] — Agregação de dados multi-source com deduplicação e quality scoring
- [[SNAPSHOTS_HISTORICOS]] — Versioning de dados históricos, reproducibility
- [[VALIDACAO_DADOS]] — Great Expectations ou equivalente; regras de qualidade
- [[OBSERVABILIDADE_PIPELINE]] — Logs, métricas, alertas de falhas de ingestão

---

## 3. ARQUITETURA DE DADOS

```
┌─────────────────────────────────────────────────────────────┐
│                      FONTES DE DADOS                        │
├──────────────┬──────────────┬──────────────┬───────────────┤
│ NBA API      │ Basketball   │ OddsPortal   │ ESPN/CBS      │
│ (oficial)    │ Reference    │ (manual)     │ (lesões)      │
└──────┬───────┴──────┬───────┴──────┬───────┴───────┬───────┘
       │              │              │               │
       ▼              ▼              ▼               ▼
┌─────────────────────────────────────────────────────────────┐
│                    INGESTÃO BRONZE                          │
│  (JSON/CSV brutos, tabelas raw, sem transformação)          │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                   TRANSFORMAÇÃO SILVER                        │
│  (limpeza, normalização, deduplicação, joins)               │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                     FEATURE STORE GOLD                      │
│  (features prontas para treino, versionadas, com lineage)    │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                      CONSUMIDORES                           │
│  Modelos │ Backtests │ Dashboards │ Alertas │ Tipster        │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. TECNOLOGIA E ESCOLHAS

| Componente | Escolha | Justificação | Alternativas Rejeitadas |
|------------|---------|--------------|-------------------------|
| Base de dados | PostgreSQL 15 | Relacional robusto, suporta JSONB, window functions, CTEs | MySQL (menos recursos analíticos), MongoDB (sem schema rigoroso) |
| Cache | Redis | Odds em memória, filas, rate limiting | Memcached (menos funcionalidades) |
| Orquestração batch | Prefect (local) | Simples, Python-native, suficiente para cron | Airflow (overkill para início), Dagster (mais complexo) |
| Formato raw | JSONB + Parquet | Flexibilidade + performance | CSV apenas (schema rígido) |
| Data validation | Great Expectations | Regras declarativas, integração com Pandas | Pandera (menos maduro), custom scripts (reinventar roda) |

---

## 5. REGRAS DE OURO DE DADOS

1. **Nunca deletar dados brutos.** Guardar tudo em rawBronze indefinidamente.
2. **Nunca modificar dados históricos em produção.** Corrigir via tabelas de audit.
3. **Sempre validar antes de consumir.** Pipeline deve falhar se qualidade < threshold.
4. **Sempre documentar lineage.** Cada feature deve saber de que tabelas vem.
5. **Nunca usar dados do futuro.** Look-ahead leakage = projeto falhado.

---

## 6. BACKLOG TÉCNICO
x] Documentar multi-source data aggregation
- [
- [ ] Implementar ingestão NBA API (5 épocas históricas)
- [ ] Implementar ingestão Basketball-Reference (Four Factors)
- [ ] Criar pipeline de odds Pinnacle (fontes gratuitas)
- [ ] Implementar deduplicação de jogos (múltiplas fontes)
- [ ] Criar tabela de calendário com back-to-backs
- [ ] Implementar validação Great Expectations em todas as tabelas
- [ ] Criar sistema de snapshots diários (backup lógico)
- [ ] Documentar lineage de cada feature em [[32_Feature_Store/INDEX]]

---

## 7. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[15_Database/INDEX]] → Schema detalhado, índices, partitioning
- [[32_Feature_Store/INDEX]] → Features derivadas dos dados
- [[31_Data_Validation/INDEX]] → Validação de qualidade
- [[48_Data_Drift/INDEX]] → Monitorização de drift nas features
