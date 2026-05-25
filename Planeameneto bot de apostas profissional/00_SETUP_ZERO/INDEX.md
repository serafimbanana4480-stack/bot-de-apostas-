# Setup Zero Euros - Guia Principal de Implementação

**Versão:** 1.0.0-ZERO-EUROS  
**Data:** 2026-05-18  
**Status:** #status/active #priority/critical  
**Objetivo:** Implementação 100% gratuita no PC  

---

## 🎯 VISÃO GERAL

Este é o guia completo para implementar o sistema VBQ-UNIFIED **100% gratuitamente no teu PC**. Sem custos de VPS, APIs pagas, ou serviços externos.

### **Custo Total: 0€**
- Hardware: PC existente
- Software: 100% open-source
- Dados: APIs gratuitas
- Infraestrutura: Local

---

## 📋 ROADMAP VISUAL DE IMPLEMENTAÇÃO (14 DIAS)

### **🎯 Milestone 1: Setup Base (Dias 1-2)** ✅
```
┌─────────────────────────────────────────────┐
│ DIA 1: Verificação e Instalação             │
├─────────────────────────────────────────────┤
│ ☐ Verificar hardware do PC                 │
│ ☐ Instalar Docker Desktop                   │
│ ☐ Instalar Python 3.11+                     │
│ ☐ Clonar repositório                         │
│ ☐ Criar ambiente virtual                    │
└─────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────┐
│ DIA 2: Configuração Inicial                │
├─────────────────────────────────────────────┤
│ ☐ Configurar .env com API keys             │
│ ☐ Testar Docker (hello-world)               │
│ ☐ Setup docker-compose básico              │
│ ☐ Verificar conectividade                   │
└─────────────────────────────────────────────┘
```

### **🎯 Milestone 2: Dados Gratuitos (Dias 3-5)** 📊
```
┌─────────────────────────────────────────────┐
│ DIA 3: NBA API e Scraping                   │
├─────────────────────────────────────────────┤
│ ☐ Configurar NBA API gratuita              │
│ ☐ Setup scraping Basketball-Reference      │
│ ☐ Testar ingestão de dados                  │
│ ☐ Validar qualidade dos dados               │
└─────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────┐
│ DIA 4: Odds e CLV Proxy                    │
├─────────────────────────────────────────────┤
│ ☐ Configurar The-Odds-API                   │
│ ☐ Implementar CLV proxy                    │
│ ☐ Setup rate limiting                       │
│ ☐ Testar pipeline de odds                  │
└─────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────┐
│ DIA 5: Pipeline de Dados                   │
├─────────────────────────────────────────────┤
│ ☐ Integrar todas as fontes                 │
│ ☐ Implementar cache local                  │
│ ☐ Setup backfill histórico                 │
│ ☐ Validar pipeline completo                │
└─────────────────────────────────────────────┘
```

### **🎯 Milestone 3: Modelo Baseline (Dias 6-7)** 🤖
```
┌─────────────────────────────────────────────┐
│ DIA 6: Feature Engineering                 │
├─────────────────────────────────────────────┤
│ ☐ Setup features básicas                   │
│ ☐ Implementar rolling averages             │
│ ☐ Criar features de mercado                │
│ ☐ Validar feature store                    │
└─────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────┐
│ DIA 7: Treino e Validação                  │
├─────────────────────────────────────────────┤
│ ☐ Treinar XGBoost baseline                 │
│ ☐ Implementar validação walk-forward       │
│ ☐ Calcular métricas de performance          │
│ ☐ Guardar modelo em MLflow local            │
└─────────────────────────────────────────────┘
```

### **🎯 Milestone 4: Interface Usuário (Dias 8-10)** 💬
```
┌─────────────────────────────────────────────┐
│ DIA 8: Telegram Bot                         │
├─────────────────────────────────────────────┤
│ ☐ Criar bot Telegram                       │
│ ☐ Implementar comandos básicos            │
│ ☐ Setup sistema de notificações             │
│ ☐ Testar envio de sinais                   │
└─────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────┐
│ DIA 9: Streamlit Dashboard                 │
├─────────────────────────────────────────────┤
│ ☐ Criar dashboard básico                   │
│ ☐ Implementar charts de performance        │
│ ☐ Setup métricas em tempo real             │
│ ☐ Testar interatividade                    │
└─────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────┐
│ DIA 10: Formatação e Sinais                │
├─────────────────────────────────────────────┤
│ ☐ Implementar motor de edge               │
│ ☐ Setup cálculo de Kelly                    │
│ ☐ Formatar sinais para Telegram            │
│ ☐ Testar pipeline completo                 │
└─────────────────────────────────────────────┘
```

### **🎯 Milestone 5: Operações (Dias 11-12)** ⚙️
```
┌─────────────────────────────────────────────┐
│ DIA 11: Docker e Monitoring                 │
├─────────────────────────────────────────────┤
│ ☐ Configurar docker-compose mínimo         │
│ ☐ Implementar logging estruturado          │
│ ☐ Setup health checks                       │
│ ☐ Configurar alertas Telegram              │
└─────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────┐
│ DIA 12: Backup e Manutenção                │
├─────────────────────────────────────────────┤
│ ☐ Implementar backup PostgreSQL            │
│ ☐ Setup script de restore                  │
│ ☐ Criar rotinas de manutenção              │
│ ☐ Documentar procedimentos                 │
└─────────────────────────────────────────────┘
```

### **🎯 Milestone 6: Validação Final (Dias 13-14)** ✅
```
┌─────────────────────────────────────────────┐
│ DIA 13: Testes Integrados                  │
├─────────────────────────────────────────────┤
│ ☐ Executar testes end-to-end               │
│ ☐ Validar performance do sistema           │
│ ☐ Testar stress com dados reais            │
│ ☐ Verificar stability 24h                  │
└─────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────┐
│ DIA 14: Go-Live                            │
├─────────────────────────────────────────────┤
│ ☐ Performance tuning                       │
│ ☐ Documentação final                       │
│ ☐ Revisão de segurança                     │
│ ☐ DECISÃO: Go-live ou ajustes              │
└─────────────────────────────────────────────┘
```

---

## � DIAGRAMA DE FLUXO DO SETUP COMPLETO

```
┌─────────────────────────────────────────────────────────────────┐
│                    SETUP ZERO EUROS - FLOW CHART                 │
└─────────────────────────────────────────────────────────────────┘

INÍCIO
  ↓
┌─────────────────┐
│ Verificar       │──→ NÃO CUMPRE → [UPGRADE PC / CANCELAR]
│ Requisitos PC   │
└─────────────────┘
         ↓ CUMPRE
┌─────────────────┐
│ Instalar Docker  │──→ ERRO → [[TROUBLESHOOTING]]
│ Desktop         │
└─────────────────┘
         ↓ SUCESSO
┌─────────────────┐
│ Instalar Python  │──→ ERRO → [[TROUBLESHOOTING]]
│ 3.11+           │
└─────────────────┘
         ↓ SUCESSO
┌─────────────────┐
│ Clonar Repo +   │──→ ERRO → [[TROUBLESHOOTING]]
│ Setup Venv       │
└─────────────────┘
         ↓ SUCESSO
┌─────────────────┐
│ Configurar .env  │──→ ERRO → [[TROUBLESHOOTING]]
│ (API Keys)      │
└─────────────────┘
         ↓ SUCESSO
┌─────────────────┐
│ Testar Docker   │──→ ERRO → [[TROUBLESHOOTING]]
│ Compose Básico  │
└─────────────────┘
         ↓ SUCESSO
┌─────────────────┐
│ Setup NBA API   │──→ ERRO → [[TROUBLESHOOTING]]
│ Gratuita        │
└─────────────────┘
         ↓ SUCESSO
┌─────────────────┐
│ Setup Scraping   │──→ ERRO → [[TROUBLESHOOTING]]
│ Local           │
└─────────────────┘
         ↓ SUCESSO
┌─────────────────┐
│ Setup The-Odds   │──→ ERRO → [[TROUBLESHOOTING]]
│ API + CLV Proxy │
└─────────────────┘
         ↓ SUCESSO
┌─────────────────┐
│ Implementar     │──→ ERRO → [[TROUBLESHOOTING]]
│ Feature Store    │
└─────────────────┘
         ↓ SUCESSO
┌─────────────────┐
│ Treinar XGBoost  │──→ ERRO → [[TROUBLESHOOTING]]
│ Baseline        │
└─────────────────┘
         ↓ SUCESSO
┌─────────────────┐
│ Setup Telegram   │──→ ERRO → [[TROUBLESHOOTING]]
│ Bot             │
└─────────────────┘
         ↓ SUCESSO
┌─────────────────┐
│ Setup Streamlit │──→ ERRO → [[TROUBLESHOOTING]]
│ Dashboard       │
└─────────────────┘
         ↓ SUCESSO
┌─────────────────┐
│ Configurar      │──→ ERRO → [[TROUBLESHOOTING]]
│ Docker Compose  │
└─────────────────┘
         ↓ SUCESSO
┌─────────────────┐
│ Implementar     │──→ ERRO → [[TROUBLESHOOTING]]
│ Logging + Alert │
└─────────────────┘
         ↓ SUCESSO
┌─────────────────┐
│ Setup Backup    │──→ ERRO → [[TROUBLESHOOTING]]
│ Automático      │
└─────────────────┘
         ↓ SUCESSO
┌─────────────────┐
│ Executar        │──→ FALHA → [[TROUBLESHOOTING]]
│ Validação       │
└─────────────────┘
         ↓ SUCESSO
┌─────────────────┐
│ TESTE 24H       │──→ FALHA → [[TROUBLESHOOTING]]
│ STABILITY       │
└─────────────────┘
         ↓ SUCESSO
┌─────────────────┐
│ GO-LIVE         │
│ 🎉 SISTEMA       │
│ FUNCIONAL 0€    │
└─────────────────┘

NOTAS:
- Cada passo tem link para documento detalhado
- Erros redirecionam para TROUBLESHOOTING
- Validação final em [[VALIDACAO]]
- Verificação de custos em [[CUSTOS]]
```

---

## � COMEÇAR IMEDIATAMENTE

### **Passo 1: Verificar Pré-requisitos**
Ir para: [[00_SETUP_ZERO/REQUISITOS]]

### **Passo 2: Instalação Completa**
Seguir: [[00_SETUP_ZERO/INSTALACAO]]

### **Passo 3: Validação do Setup**
Testar: [[00_SETUP_ZERO/VALIDACAO]]

### **Passo 4: Verificação de Custos**
Confirmar: [[00_SETUP_ZERO/CUSTOS]]

---

## 📊 ESTRUTURA DO PROJETO ZERO EUROS

### **🏗️ 00_SETUP_ZERO** (Guia de Implementação)
- [[00_SETUP_ZERO/REQUISITOS]] - PC e software necessários
- [[00_SETUP_ZERO/INSTALACAO]] - Passo-a-passo completo
- [[00_SETUP_ZERO/VALIDACAO]] - Testes para verificar funcionamento
- [[00_SETUP_ZERO/TROUBLESHOOTING]] - Problemas comuns e soluções
- [[00_SETUP_ZERO/CUSTOS]] - Verificação zero euros

### **📊 04_Data_Engineering** (Fontes de Dados 100% Gratuitas)
- [[04_Data_Engineering/FONTES_GRATUITAS]] - APIs gratuitas e exemplos
- [[04_Data_Engineering/SCRAPING_LOCAL]] - Scripts para dados locais
- [[04_Data_Engineering/CLV_PROXY]] - Workaround para Pinnacle
- [[04_Data_Engineering/RATE_LIMITS]] - Gestão de limites APIs
- [Arquivos existentes mantidos como referência]

### **⚡ 10_Infrastructure** (Stack Local Mínima)
- [[10_Infrastructure/STACK_LOCAL]] - Stack de 3 containers
- [[10_Infrastructure/DOCKER_LOCAL]] - Compose simplificado
- [[10_Infrastructure/MONITORING_LOCAL]] - Logging básico
- [Arquivos existentes mantidos como referência]

### **🔌 14_APIs** (Alternativas Gratuitas)
- [[14_APIs/ALTERNATIVAS_GRATUITAS]] - Substitutos 0€
- [[14_APIs/NBA_API_GRATUITA]] - Setup NBA API
- [[14_APIs/ODDS_GRATUITAS]] - The-Odds-API setup
- [Arquivos existentes mantidos como referência]

---

## 💰 COMPARAÇÃO: ORIGINAL VS ZERO EUROS

| Componente | Original | Zero Euros | Economia |
|-------------|----------|------------|----------|
| VPS | 50-120€/mês | PC local | 100% |
| Pinnacle odds | 50-100€/mês | CLV proxy | 100% |
| Domínio | 10-15€/mês | localhost | 100% |
| Database | 30-80€/mês | PostgreSQL local | 100% |
| **Total** | **140-315€/mês** | **0€** | **100%** |

---

## ⚠️ TRADE-OFFS ACEITÁVEIS

### **Limitações Técnicas:**
- PC precisa estar ligado 24/7
- Internet doméstica vs profissional
- Hardware limitado vs cloud
- IP dinâmico vs estático

### **Limitações de Dados:**
- Sem CLV real (apenas proxy)
- Rate limits APIs gratuitas
- Dados históricos limitados
- Latência maior

### **Limitações de Escala:**
- Máximo 10 utilizadores simultâneos
- Sem backup automático externo
- Sem monitoring avançado
- Sem SLA/garantias

---

## 🎮 EXPERIÊNCIA DO USUÁRIO ZERO EUROS

### **Interface Principal: Telegram**
```python
# Comandos disponíveis:
/start - Onboarding e ajuda
/signals - Últimos sinais gerados
/performance - Métricas do modelo
/status - Saúde do sistema
/help - Comandos disponíveis
```

### **Dashboard Secundário: Streamlit**
```python
# Features disponíveis:
- Performance charts em tempo real
- Métricas do modelo
- Histórico de previsões
- Análise de sinais
- Sistema de alertas
```

### **Acesso Local:**
```
Telegram: @bot_username
Streamlit: http://localhost:8501
API docs: http://localhost:8000/docs
PostgreSQL: localhost:5432
Redis: localhost:6379
```

---

## 📈 MÉTRICAS DE SUCESSO ZERO EUROS

### **Métricas Técnicas:**
- Modelo accuracy > 55%
- API response time < 200ms
- System uptime > 90%
- Data latency < 1h
- Memory usage < 8GB

### **Métricas de Negócio:**
- Custo mensal: 0€
- Tempo setup: 2 semanas
- Utilizadores suportados: 1-10
- Manutenção: 2h/semana
- ROI potencial: Ilimitado

---

## 🔄 CICLO DE DESENVOLVIMENTO

### **Fase 1: MVP (Mês 1-3)**
- Sistema funcional básico
- Validação de conceito
- Aprendizado técnico
- Feedback inicial

### **Fase 2: Melhorias (Mês 4-6)**
- Mais fontes de dados
- Modelos avançados
- Interface melhorada
- Performance tuning

### **Fase 3: Decisão (Mês 7+)**
- Se sucesso → Considerar VPS
- Se insucesso → Pivot/abandonar
- Se estável → Manter setup local

---

## 📝 CHECKLIST INTERATIVO DE VALIDAÇÃO

### **🔍 FASE 1: Pré-requisitos (Antes de Começar)**
- [ ] PC com **16GB RAM mínimo** (8GB funcional mas limitado)
- [ ] **CPU 4+ cores** (2 cores funcional mas lento)
- [ ] **100GB disco livre** (50GB mínimo)
- [ ] Internet estável **>10Mbps** (5Mbps mínimo)
- [ ] Tempo dedicado: **2-3 semanas** (1 mês se inexperiente)
- [ ] Conhecimento básico: **Python, Docker, Git**
- [ ] Sistema operacional: **Windows 10/11, macOS, ou Linux**

### **🔧 FASE 2: Setup Técnico (Dias 1-2)**
- [ ] Docker Desktop instalado e running
- [ ] Docker compose testado (`docker-compose --version`)
- [ ] Python 3.11+ instalado (`python --version`)
- [ ] Ambiente virtual criado e ativado
- [ ] Repositório clonado localmente
- [ ] `requirements.txt` instalado sem erros
- [ ] `.env` configurado com API keys
- [ ] Containers básicos funcionando (PostgreSQL, Redis)
- [ ] Health checks passando

### **📊 FASE 3: Dados e APIs (Dias 3-5)**
- [ ] NBA API configurada e testada
- [ ] The-Odds-API key obtida e validada
- [ ] Scraping Basketball-Reference funcionando
- [ ] CLV proxy implementado e testado
- [ ] Rate limiting configurado
- [ ] Cache local implementado
- [ ] Pipeline de ingestão funcionando
- [ ] Dados históricos backfilled
- [ ] Qualidade dos dados validada (<5% missing)

### **🤖 FASE 4: Modelo ML (Dias 6-7)**
- [ ] Feature engineering implementado
- [ ] Rolling averages calculados
- [ ] Features de mercado criadas
- [ ] Feature store validado
- [ ] XGBoost baseline treinado
- [ ] Validação walk-forward executada
- [ ] Métricas de performance calculadas
- [ ] Modelo guardado em MLflow local
- [ ] Accuracy > 55% (mínimo aceitável)

### **💬 FASE 5: Interface Usuário (Dias 8-10)**
- [ ] Telegram bot criado e configurado
- [ ] Bot token obtido de @BotFather
- [ ] Comandos básicos implementados
- [ ] Sistema de notificações funcionando
- [ ] Envio de sinais testado
- [ ] Streamlit dashboard criado
- [ ] Charts de performance implementados
- [ ] Métricas em tempo real funcionando
- [ ] Interatividade testada

### **⚙️ FASE 6: Operações (Dias 11-12)**
- [ ] Docker compose mínimo configurado
- [ ] Logging estruturado implementado
- [ ] Health checks automatizados
- [ ] Alertas Telegram configurados
- [ ] Backup PostgreSQL automatizado
- [ ] Script de restore testado
- [ ] Rotinas de manutenção documentadas
- [ ] Monitoramento básico funcionando

### **✅ FASE 7: Validação Final (Dias 13-14)**
- [ ] Testes end-to-end executados
- [ ] Performance do sistema validada
- [ ] Stress test com dados reais
- [ ] Stability test 24h passado
- [ ] Performance tuning concluído
- [ ] Documentação final revisada
- [ ] Revisão de segurança concluída
- [ ] Backup verificado
- [ ] **DECISÃO: Go-live ou ajustes**

### **🎯 CRITÉRIOS DE GO-LIVE**
**Todos os seguintes devem ser TRUE:**
- [ ] Todos os itens acima marcados
- [ ] Sistema estável >90% uptime
- [ ] API response time <200ms
- [ ] Memory usage <8GB
- [ ] Custo verificado = 0€
- [ ] Backup funcionando
- [ ] Alertas configurados
- [ ] Documentação completa

**Se algum critério falhar:** Revisar [[TROUBLESHOOTING]] antes de go-live

---

## 🎯 PRÓXIMOS PASSOS - GUIA RÁPIDO

### **📍 ONDE ESTÁ AGORA?**
**Estado:** Início do projeto
**Próxima Ação:** Verificar requisitos do PC

### **🚀 CAMINHO RECOMENDADO (14 DIAS)**

#### **DIA 1-2: Fundamentos**
```
1. [[00_SETUP_ZERO/REQUISITOS]] ← COMECE AQUI
   ↓ Verificar hardware/software
2. [[00_SETUP_ZERO/INSTALACAO]]
   ↓ Instalar Docker, Python, Git
3. [[00_SETUP_ZERO/VALIDACAO]] (após instalação)
   ↓ Validar setup base
```

#### **DIA 3-5: Dados**
```
4. [[04_Data_Engineering/FONTES_GRATUITAS]]
   ↓ Configurar APIs gratuitas
5. [[04_Data_Engineering/SCRAPING_LOCAL]]
   ↓ Setup scraping local
6. [[04_Data_Engineering/CLV_PROXY]]
   ↓ Implementar workaround Pinnacle
7. [[04_Data_Engineering/RATE_LIMITS]]
   ↓ Configurar rate limiting
```

#### **DIA 6-7: Modelo**
```
8. [[05_Machine_Learning/XGBoost_BASELINE]]
   ↓ Treinar primeiro modelo
9. [[05_Machine_Learning/WALK_FORWARD_CV]]
   ↓ Validar corretamente
```

#### **DIA 8-10: Interface**
```
10. [[19_Telegram_System/BOT_TELEGRAM_CONFIG]]
    ↓ Setup Telegram bot
11. [[10_Infrastructure/MONITORING_LOCAL]]
    ↓ Criar Streamlit dashboard
```

#### **DIA 11-12: Operações**
```
12. [[10_Infrastructure/DOCKER_LOCAL]]
    ↓ Configurar docker-compose
13. [[00_SETUP_ZERO/TROUBLESHOOTING]]
    ↓ Ter à mão para problemas
```

#### **DIA 13-14: Validação**
```
14. [[00_SETUP_ZERO/VALIDACAO]]
    ↓ Teste completo
15. [[00_SETUP_ZERO/CUSTOS]]
    ↓ Confirmar 0€
16. GO-LIVE! 🎉
```

### **🔗 LINKS RÁPIDOS POR CATEGORIA**

**Setup:**
- [[00_SETUP_ZERO/REQUISITOS]] - Verificar PC
- [[00_SETUP_ZERO/INSTALACAO]] - Instalar tudo
- [[00_SETUP_ZERO/VALIDACAO]] - Testar setup
- [[00_SETUP_ZERO/TROUBLESHOOTING]] - Resolver problemas
- [[00_SETUP_ZERO/CUSTOS]] - Verificar 0€

**Dados:**
- [[04_Data_Engineering/FONTES_GRATUITAS]] - APIs 0€
- [[04_Data_Engineering/SCRAPING_LOCAL]] - Scraping
- [[04_Data_Engineering/CLV_PROXY]] - CLV workaround
- [[04_Data_Engineering/RATE_LIMITS]] - Gestão limits

**Infraestrutura:**
- [[10_Infrastructure/STACK_LOCAL]] - Stack mínimo
- [[10_Infrastructure/DOCKER_LOCAL]] - Docker compose
- [[10_Infrastructure/MONITORING_LOCAL]] - Monitoring básico

**APIs:**
- [[14_APIs/ALTERNATIVAS_GRATUITAS]] - Substitutos 0€
- [[14_APIs/NBA_API_GRATUITA]] - NBA API setup
- [[14_APIs/ODDS_GRATUITAS]] - Odds gratuitas

### **⚠️ SE ENCONTRAR PROBLEMAS**
1. Verificar [[00_SETUP_ZERO/TROUBLESHOOTING]]
2. Revisar passos anteriores
3. Validar cada componente individualmente
4. Não avançar sem resolver

### **💡 DICAS DE SUCESSO**
- **Não salte passos** - Cada fase depende da anterior
- **Teste frequentemente** - Valide após cada mudança
- **Documente problemas** - Crie notas para futuro
- **Seja paciente** - 14 dias é realista, não apresse
- **Peça ajuda** - Use troubleshooting e documentação

---

**Status:** Pronto para implementação  
**Custo:** 0€  
**Tempo:** 14 dias  
**Resultado:** Sistema funcional 100% gratuito

---

#status/active #priority/critical #phase/setup-zero
