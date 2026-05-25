# TRADE-OFFS ARQUITETURAIS — Registro de Compromissos Técnicos

**ID:** `STR-002` | **Fase:** Todas | **Owner:** Chief Systems Architect | **Status:** #status/active

---

## 1. OBJETIVO

Documentar todos os trade-offs técnicos feitos durante o desenvolvimento. Todo sistema envolve compromissos; o importante é documentar o "porquê" para evitar debates repetidos e facilitar revisões futuras.

---

## 2. TRADE-OFFS REGISTADOS

### TO-001: SQL vs NoSQL para Base de Dados
**Decisão:** PostgreSQL (SQL)

**Prós:**
- Schema rigoroso previne erros de dados
- Window functions para features temporais
- JSONB para flexibilidade quando necessário
- ACID compliance para integridade transacional
- Ferramentas maduras de backup e replicação

**Contras:**
- Schema migrations podem ser dolorosas
- Escala horizontal mais complexa que NoSQL
- Performance em writes massivos pode ser inferior

**Justificação:** Para um sistema quantitativo, integridade de dados > performance de writes. A escala prevista (5 épocas NBA ~ 6000 jogos) é trivial para PostgreSQL.

**Quando reconsiderar:** Se dados > 500GB ou necessidade de sharding.

---

### TO-002: Monolito vs Microserviços
**Decisão:** Monolito modular (FastAPI)

**Prós:**
- Desenvolvimento inicial 3-5x mais rápido
- Debugging mais simples (um processo)
- Deploy trivial (um container)
- Menor complexidade operacional
- Latência interna zero (chamadas em memória)

**Contras:**
- Escala granular por componente não é possível
- Acoplamento pode crescer se não disciplinado
- Single point of failure potencial

**Justificação:** Na Fase 1-6, a prioridade é velocidade de validação, não arquitetura enterprise. Monolito modular permite separação lógica sem complexidade física.

**Quando reconsiderar:** Se > 5 desenvolvedores ou necessidade de escalas independentes por componente.

---

### TO-003: Síncrono vs Assíncrono para Ingestão
**Decisão:** Síncrono (batch) com cache assíncrono

**Prós:**
- Simplicidade de implementação
- Fácil de debug (logs lineares)
- Consistência de dados garantida
- Latência 2-5s é aceitável para pré-jogo

**Contras:**
- Não escala para streaming real-time
- Bottleneck potencial se volume aumentar
- Não suporta live betting (futuro)

**Justificação:** O sistema é pré-jogo (batch). Streaming adds complexidade massiva (Kafka, Flink, etc.) sem benefício para o MVP.

**Quando reconsiderar:** Se expandir para live betting ou latência < 1s for requerida.

---

### TO-004: Cloud vs Self-Hosted
**Decisão:** Self-hosted VPS

**Prós:**
- Custo 5-10x menor que AWS/GCP equivalentes
- Controle total do ambiente
- Sem vendor lock-in
- Simples de migrar entre providers

**Contras:**
- Gerenciamento de updates/security manual
- Sem auto-scaling automático
- Backup/disaster recovery é responsabilidade nossa
- Menos serviços gerenciados disponíveis

**Justificação:** Para MVP (< 100€/mês), cloud providers são overkill. Self-hosted é perfeitamente adequado e força disciplina operacional.

**Quando reconsiderar:** Se receita > 5000€/mês ou equipe > 3 pessoas ops.

---

### TO-005: Framework ML vs Custom
**Decisão:** XGBoost (framework) + custom pipeline

**Prós:**
- XGBoost é otimizado para performance
- Custom pipeline permite controle total de leakage
- Sem "black box" de frameworks high-level
- Interpretabilidade melhor (feature importance)

**Contras:**
- Mais código para escrever
- Sem abstrações convenientes de AutoML
- Requer conhecimento profundo de ML

**Justificação:** Em sistemas quantitativos, controle de leakage e interpretabilidade são críticos. AutoML esconde detalhes que podem ser fatais.

**Quando reconsiderar:** Se tempo de desenvolvimento for constraint severo (não é o caso aqui).

---

### TO-006: Git Flow vs Trunk-Based Development
**Decisão:** Git Flow simplificado (main + feature branches)

**Prós:**
- Separação clara entre desenvolvimento e produção
- Releases versionados são explícitos
- Hotfixes têm workflow dedicado
- Mais fácil para equipe pequena

**Contras:**
- Merge conflicts mais frequentes
- Integração contínua menos fluida
- Overhead de gestão de branches

**Justificação:** Para sistema quantitativo, releases devem ser deliberados e testados. Trunk-based pode levar a deployments acidentais de modelos não validados.

**Quando reconsiderar:** Se CI/CD estiver extremamente maduro e equipe > 5 desenvolvedores.

---

## 3. TRADE-OFFS FUTUROS A DOCUMENTAR

| ID | Trade-off | Data Alvo | Contexto |
|----|-----------|-----------|----------|
| TO-006 | Batch Síncrono vs Message Queue | Fase 1 | Ver decisão abaixo |
| TO-007 | Kubernetes vs Docker Compose | Fase 7 | Escala de containers |
| TO-008 | Message Queue: RabbitMQ vs Redis vs Kafka | Fase 7 | Orquestração de tarefas (se TO-006 mudar) |
| TO-009 | Time-series DB: TimescaleDB vs InfluxDB | Fase 9 | Métricas de monitorização |
| TO-010 | Feature Store: Feast vs Custom | Fase 9 | Gestão de features em escala |

### TO-006: Batch Síncrono vs Message Queue (Decidido)

**Decisão:** Batch síncrono (Prefect) para Fase 1-6. Nenhuma message queue.

**Justificação:**
1. Volume de dados: ~1000 jogos/época NBA, odds a cada 5 min. Não justifica infraestrutura de queue.
2. Latência aceitável: 2-5s por aposta, pré-jogo. Não precisamos de async real-time.
3. Simplicidade: Um container Python + Prefect é mais simples de debugar que RabbitMQ + workers.
4. Custo: Zero custo adicional vs ~5-10€/mês para RabbitMQ/cloud.

**Quando reconsiderar:**
- Fase 7+ (multi-desporto): se volume de dados crescer 10x
- Live betting: se adicionar apostas em tempo real (requer latência < 1s)
- > 100 subscritores: se distribuição de sinais precisar de queue dedicada

**Nota:** Documentos antigos (SYSTEM_ARCHITECTURE.md, SYSTEM_REQUIREMENTS.md) mencionam RabbitMQ incorretamente. Estes serão atualizados na próxima revisão. A stack real é: Prefect (orquestração) + Redis (cache leve) + PostgreSQL (dados).

---

## 4. PRINCÍPIOS PARA TRADE-OFFS

1. **Simplicidade > Sofisticação** até edge comprovado
2. **Controle > Conveniência** em componentes críticos (ML, dados)
3. **Custo > Performance** quando performance é "suficiente"
4. **Transparência > Abstração** em sistemas de decisão
5. **Velocidade de Validação > Arquitetura Perfeita** nas fases iniciais

---

## 5. LINKS CRUZADOS

- [[01_Vision_And_Strategy/INDEX]] ← Secção mãe
- [[DECISOES_IRREVERSIVEIS]] → Decisões que não podem ser revertidas
- [[00_Master_Index/INDEX]] ← Cérebro do sistema