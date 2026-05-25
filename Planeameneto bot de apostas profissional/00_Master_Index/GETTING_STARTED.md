# GETTING_STARTED — Guia de Início Rápido

**ID:** `GS-001` | **Versão:** v4.0.1-FIXED | **Data:** 2026-05-17

---

## 1. PRÉ-REQUISITOS

### 1.1 Software Requerido

- **Python:** 3.11+ (recomendado 3.11)
- **Docker:** 20.10+ (com Docker Compose v2)
- **Git:** 2.30+
- **VS Code** (recomendado) ou outro editor de código

### 1.2 Contas Requeridas

- **GitHub** (para clonar repositório)
- **Betfair** (para dados de odds, demo OK para testes)
- **Telegram** (para criar bot via @BotFather)
- **Oracle Cloud** (Free Tier - VPS gratuito) ou **AWS Free Tier** (para deploy sem custo)

---

## 2. SETUP LOCAL (5 MINUTOS)

### 2.1 Clonar Repositório

```bash
git clone https://github.com/seu-usuario/value-betting-system.git
cd value-betting-system
```

### 2.2 Criar Ambiente Virtual

```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 2.3 Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2.4 Configurar Variáveis de Ambiente

```bash
# Copiar template
cp .env.example .env

# Editar .env com suas credenciais
nano .env  # ou usar seu editor preferido
```

**Variáveis obrigatórias:**
```bash
# Database
POSTGRES_DB=valuebetting
POSTGRES_USER=vb_admin
POSTGRES_PASSWORD=sua_password_aqui

# Redis
REDIS_PASSWORD=sua_password_aqui

# Telegram
TELEGRAM_BOT_TOKEN=seu_bot_token_aqui

# Betfair
BETFAIR_API_KEY=seu_api_key_aqui
BETFAIR_USERNAME=seu_username
BETFAIR_PASSWORD=sua_password
```

### 2.5 Iniciar Serviços com Docker Compose

```bash
# Iniciar todos os serviços
docker compose up -d

# Verificar status
docker compose ps

# Ver logs
docker compose logs -f
```

### 2.6 Executar Migrações de Database

```bash
# Executar migrações
docker compose exec api python scripts/migrate_db.py
```

### 2.7 Verificar Setup

```bash
# Testar API
curl http://localhost:8000/health

# Deve retornar: {"status": "healthy"}

# Testar PostgreSQL
docker compose exec postgres pg_isready -U vb_admin

# Deve retornar: vb-postgres:5432 - accepting connections

# Testar Redis
docker compose exec redis redis-cli -a ${REDIS_PASSWORD} ping

# Deve retornar: PONG
```

---

## 3. INGESTÃO DE DADOS (10 MINUTOS)

### 3.1 Ingerir Dados NBA Históricos

```bash
# Ingerir 5 épocas históricas (2019-20 a 2023-24)
docker compose exec api python scripts/ingest_nba_historical.py --seasons 2019-20 2020-21 2021-22 2022-23 2023-24
```

### 3.2 Verificar Dados Ingeridos

```bash
# Conectar ao PostgreSQL
docker compose exec postgres psql -U vb_admin -d valuebetting

# Verificar número de jogos
SELECT COUNT(*) FROM bronze.raw_games;

# Deve retornar: ~6000+ (5 épocas x ~1230 jogos)

# Sair do PostgreSQL
\q
```

---

## 4. FEATURE ENGINEERING (5 MINUTOS)

### 4.1 Calcular Features

```bash
# Calcular features para todos os jogos
docker compose exec api python scripts/calculate_features.py
```

### 4.2 Verificar Features

```bash
# Conectar ao PostgreSQL
docker compose exec postgres psql -U vb_admin -d valuebetting

# Verificar features
SELECT COUNT(*) FROM gold.features;

# Deve retornar: ~6000+ (mesmo número de jogos)

# Verificar número de colunas (features)
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'features' AND table_schema = 'gold';

# Deve retornar: 82 colunas (80 features + game_id + target)

# Sair do PostgreSQL
\q
```

---

## 5. TREINO DO MODELO (10 MINUTOS)

### 5.1 Treinar Modelo Baseline

```bash
# Treinar XGBoost baseline com Purged CV
docker compose exec api python scripts/train_model.py --model xgboost --cv purged
```

### 5.2 Verificar Modelo

```bash
# Verificar modelo no MLflow
# Acessar http://localhost:5000
# Deve ver o experimento de treino com métricas
```

---

## 6. GERAÇÃO DE SINAIS (2 MINUTOS)

### 6.1 Gerar Sinal para Jogo Específico

```bash
# Gerar sinal para jogo específico
docker compose exec api python scripts/generate_signal.py --game_id 20231015-BOS-LAL
```

### 6.2 Verificar Sinal

```bash
# O comando deve retornar algo como:
# {
#   "approved": true,
#   "edge": 0.073,
#   "prob": 0.58,
#   "odd": 1.85,
#   "stake": 25.00,
#   "signal_id": "SIG-20261015-001"
# }
```

---

## 7. CONFIGURAÇÃO DO TELEGRAM BOT (5 MINUTOS)

### 7.1 Criar Bot no Telegram

1. Abrir Telegram e procurar @BotFather
2. Enviar `/newbot`
3. Seguir instruções para criar bot
4. Copiar token gerado (formato: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 7.2 Configurar Bot no Sistema

```bash
# Adicionar token ao .env
echo "TELEGRAM_BOT_TOKEN=seu_token_aqui" >> .env

# Reiniciar API
docker compose restart api
```

### 7.3 Testar Bot

```bash
# Enviar comando /start para o bot no Telegram
# Deve responder com mensagem de boas-vindas
```

---

## 8. MONITORIZAÇÃO (2 MINUTOS)

### 8.1 Acessar Grafana

1. Acessar http://localhost:3000
2. Login com admin/admin (mudar no .env)
3. Navegar para dashboards
4. Verificar métricas do sistema

### 8.2 Acessar Prometheus

1. Acessar http://localhost:9090
2. Navegar para targets
3. Verificar que todos os serviços estão up

---

## 9. TESTE END-TO-END (5 MINUTOS)

### 9.1 Executar Teste Completo

```bash
# Executar teste end-to-end
docker compose exec api python scripts/test_e2e.py
```

### 9.2 Verificar Resultado

```bash
# O teste deve:
# 1. Ingerir dados de teste
# 2. Calcular features
# 3. Treinar modelo
# 4. Gerar sinal
# 5. Enviar sinal para Telegram
# 6. Verificar reconciliação

# Se todos passarem, setup está correto!
```

---

## 10. PRÓXIMOS PASSOS

### 10.1 Para Desenvolvedores

1. Ler [[INDEX.md]] para visão geral do sistema
2. Ler [[05_Machine_Learning/INDEX]] para entender modelos
3. Ler [[06_Backtesting/INDEX]] para entender validação
4. Ler [[09_Execution_System/INDEX]] para entender execução

### 10.2 Para Operadores

1. Ler [[ONBOARDING_GUIDE.md]] para onboarding detalhado
2. Ler [[25_SOPs/INDEX]] para procedimentos operacionais
3. Ler [[26_Runbooks/INDEX]] para resposta a incidentes
4. Ler [[28_Failure_Scenarios/INDEX]] para cenários de falha

### 10.3 Para Deploy em Produção (100% Gratuito)

1. Criar conta **Oracle Cloud Free Tier** (4 ARM CPUs, 24GB RAM, 200GB storage)
2. Alternativa: **AWS Free Tier** (t2.micro - 750h/mês)
3. Ler [[DEPLOYMENT_GUIDE.md]] para deploy em VPS gratuito
4. Ler [[34_Security/INDEX.md]] para hardening de segurança
5. Ler [[33_Alerting/INDEX.md]] para configurar alertas
6. Seguir [[FASE_1_IMPLEMENTATION_CHECKLIST.md]] passo a passo

**Nota:** Oracle Cloud Free Tier não expira (é always-free), não requer cartão de crédito para verificação básica, e tem recursos suficientes para Fase 1-4 completas.

---

## 11. TROUBLESHOOTING

### 11.1 Docker Compose Falha ao Iniciar

**Problema:** `docker compose up -d` falha

**Solução:**
```bash
# Ver logs
docker compose logs

# Se for erro de porta, verificar se portas já estão em uso
netstat -tulpn | grep 8000

# Se for erro de dependências, limpar e rebuild
docker compose down -v
docker compose build --no-cache
docker compose up -d
```

### 11.2 PostgreSQL Não Conecta

**Problema:** API não consegue conectar ao PostgreSQL

**Solução:**
```bash
# Verificar se PostgreSQL está running
docker compose ps postgres

# Ver logs do PostgreSQL
docker compose logs postgres

# Reiniciar PostgreSQL
docker compose restart postgres
```

### 11.3 Dados Não São Ingeridos

**Problema:** Script de ingestão falha

**Solução:**
```bash
# Ver logs da API
docker compose logs api

# Verificar se NBA API está acessível
curl -I https://api.nba.com/...

# Verificar variáveis de ambiente
docker compose exec api env | grep NBA
```

### 11.4 Telegram Bot Não Envia Mensagens

**Problema:** Bot não envia sinais

**Solução:**
```bash
# Verificar token no .env
cat .env | grep TELEGRAM_BOT_TOKEN

# Verificar logs da API
docker compose logs api | grep telegram

# Testar bot manualmente
curl https://api.telegram.org/bot<SEU_TOKEN>/getMe
```

---

## 12. RECURSOS ADICIONAIS

### 12.1 Documentação

- [[INDEX.md]] — Index mestre do sistema
- [[MASTER_PLAN_UNIFICADO.md]] — Plano mestre completo
- [[DEPLOYMENT_GUIDE.md]] — Guia de deploy
- [[ONBOARDING_GUIDE.md]] — Guia de onboarding

### 12.2 Comunidade

- Discord: [Link para Discord]
- Email: support@valuebetting.com

### 12.3 Suporte

Se tiver problemas:
1. Verificar se há solução no [[26_Runbooks/INDEX]]
2. Verificar se há issue no GitHub
3. Contactar support@valuebetting.com

---

## 13. CHECKLIST DE SETUP COMPLETO

- [ ] Python 3.11+ instalado
- [ ] Docker + Docker Compose instalados
- [ ] Repositório clonado
- [ ] Ambiente virtual criado e ativado
- [ ] Dependências instaladas
- [ ] .env configurado com todas as variáveis
- [ ] Docker compose up -d funciona
- [ ] PostgreSQL healthy
- [ ] Redis healthy
- [ ] API healthy
- [ ] Migrações de database executadas
- [ ] Dados históricos NBA ingeridos
- [ ] Features calculadas
- [ ] Modelo treinado
- [ ] Sinal gerado com sucesso
- [ ] Telegram Bot configurado e testado
- [ ] Grafana acessível
- [ ] Prometheus acessível
- [ ] Teste end-to-end passa

---

**Fim do Getting Started**
