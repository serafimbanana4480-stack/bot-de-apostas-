# AMBIENTES — Configuração de Ambientes

**ID:** `OP-028` | **Fase:** #phase/3 | **Owner:** Operations Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Definir configuração de ambientes para desenvolvimento, staging e produção.

---

## 2. AMBIENTES

| Ambiente | Uso | Dados | Escala |
|----------|-----|-------|--------|
| Dev | Desenvolvimento | Sample | Pequeno |
| Staging | Teste | Subset | Médio |
| Prod | Produção | Full | Grande |

---

## 3. CONFIGURAÇÃO

### Dev
```python
DEV_CONFIG = {
    'database_url': 'postgresql://user:pass@localhost:5432/bets_dev',
    'cache_url': 'redis://localhost:6379/0',
    'api_port': 8000,
    'log_level': 'DEBUG',
    'mock_bets': True
}
```

### Staging
```python
STAGING_CONFIG = {
    'database_url': 'postgresql://user:pass@staging-db:5432/bets_staging',
    'cache_url': 'redis://staging-cache:6379/1',
    'api_port': 8000,
    'log_level': 'INFO',
    'mock_bets': False
}
```

### Prod
```python
PROD_CONFIG = {
    'database_url': os.getenv('DATABASE_URL'),
    'cache_url': os.getenv('CACHE_URL'),
    'api_port': 8000,
    'log_level': 'WARNING',
    'mock_bets': False
}
```

---

## 4. VARIÁVEIS DE AMBIENTE

```bash
# .env.prod
DATABASE_URL=postgresql://...
CACHE_URL=redis://...
API_KEY=secret_key
SENTRY_DSN=...
TELEGRAM_BOT_TOKEN=...
```

---

## 5. CRITÉRIOS

- **Nunca usar** credenciais reais em dev
- **Segregar dados** por ambiente
- **Versionar** configurações

---

## 6. LINKS CRUZADOS

- [[07_Execution/INDEX]]
- [[DEPLOYMENT_STRATEGY]]
