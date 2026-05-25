# GAP ANALYSIS — O que Falta para uma IA Implementar

**ID:** `GAP-001` | **Data:** 2026-05-17 | **Versão:** v1.0

---

## 🚨 RESUMO EXECUTIVO

**Status:** Documentação 100% completa. **Código fonte: faltante.**

Para uma IA implementar o projeto, **precisa** da estrutura de código fonte que não existe.

---

## 📊 MATRIZ DE COMPLETUDE

| Componente | Documentação | Configuração | Implementação |
|------------|--------------|--------------|---------------|
| **Infraestrutura** | ✅ 100% | ✅ 90% | ⚠️ 70% |
| **Banco de Dados** | ✅ 100% | ✅ 100% | ❌ 0% |
| **Ingestão** | ✅ 100% | ⚠️ 50% | ❌ 10% |
| **Features** | ✅ 100% | ❌ 0% | ❌ 0% |
| **Modelos ML** | ✅ 100% | ⚠️ 30% | ❌ 0% |
| **API** | ✅ 100% | ⚠️ 50% | ❌ 0% |
| **Telegram Bot** | ✅ 100% | ⚠️ 50% | ❌ 0% |

**Média:** 100% documentado, 40% configurado, **15% implementado**

---

## ❌ GAPS CRÍTICOS

### 1. Código Fonte Principal — NÃO EXISTE

O `Dockerfile` referencia diretórios que **não existem**:
```dockerfile
COPY app/ ./app/      # ❌ NÃO EXISTE
COPY src/ ./src/      # ❌ NÃO EXISTE
COPY models/ ./models/ # ❌ NÃO EXISTE
COPY configs/ ./configs/ # ❌ NÃO EXISTE
```

### 2. Schema SQL — Inexistente

Make commands referenciam arquivos que **não existem**:
- `001_schema_raw.sql`
- `002_schema_clean.sql`
- `003_schema_features.sql`

### 3. Imports Quebrados

```python
from src.ingestion.nba_api import NBAAPIIngestor  # ❌ src/ não existe
from src.models.ensemble import EnsembleModel     # ❌ não existe
```

---

## 🎯 RECOMENDAÇÕES

### Prioridade 1: CRÍTICA

| # | Tarefa | Tempo Est. |
|---|--------|------------|
| 1 | Criar estrutura de diretórios (src/, app/, configs/) | 30 min |
| 2 | Implementar src/ingestion/nba_api.py | 4-6h |
| 3 | Criar schema SQL (6 arquivos) | 2-3h |
| 4 | Implementar app/main.py básico | 2-3h |

### Prioridade 2: ALTA

| # | Tarefa | Tempo Est. |
|---|--------|------------|
| 5 | Feature engineering | 8-12h |
| 6 | Modelo XGBoost baseline | 6-8h |
| 7 | Configurações Prometheus/Grafana | 2-3h |
| 8 | Telegram Bot | 3-4h |

### Estimativa Total

| Fase | Horas | Custo (Dev) |
|------|-------|-------------|
| MVP básico | 40-60h | €2,000-3,000 |
| Features + Modelo | 60-80h | €3,000-4,000 |
| Meta-modelo | 40-60h | €2,000-3,000 |
| Bot + Execução | 40-60h | €2,000-3,000 |
| **TOTAL** | **180-260h** | **€9,000-13,000** |

---

## ✅ FIX IMEDIATO (30 min)

Para Docker funcionar agora:

```bash
# Criar estrutura mínima
mkdir -p src/{ingestion,cleaning,features,models,database}
mkdir -p app/{routers,bot,middleware}
mkdir -p models configs alembic

# Criar app/main.py mínimo
cat > app/main.py << 'EOF'
from fastapi import FastAPI
app = FastAPI()

@app.get("/health")
def health():
    return {"status": "healthy"}
EOF

touch src/__init__.py models/.gitkeep
```

---

## 📋 CHECKLIST MÍNIMO IMPLEMENTÁVEL

Para IA conseguir implementar:

### Estrutura Base
- [ ] `src/` com `__init__.py`
- [ ] `app/` com `__init__.py`
- [ ] `models/` (vazio)
- [ ] `configs/` com arquivos YAML
- [ ] `alembic/` para migrations

### Módulos Mínimos (Fase 1)
- [ ] `src/ingestion/nba_api.py` — Wrapper NBA API
- [ ] `src/database/connection.py` — PostgreSQL
- [ ] `src/database/models.py` — SQLAlchemy
- [ ] `app/main.py` — FastAPI básico
- [ ] Schema SQL (001-006)

---

## 🔧 CONCLUSÃO

**Documentação: Excelente (100%)**  
**Código: Inexistente (15%)**

Para uma IA implementar:
1. Precisa **criar estrutura de diretórios**
2. Implementar **módulos mínimos**
3. Só então seguir documentação

**A documentação é a "receita", mas falta a "cozinha".**

---

## 📚 LINKS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[00_Master_Index/MASTER_PLAN_UNIFICADO]] → Plano completo
- [[00_Master_Index/FASE_1_IMPLEMENTATION_CHECKLIST]] → Checklist Fase 1

---

**Próximo Passo:** Criar estrutura de diretórios e módulos mínimos.

**Autor:** Cascade AI  
**Data:** 2026-05-17
