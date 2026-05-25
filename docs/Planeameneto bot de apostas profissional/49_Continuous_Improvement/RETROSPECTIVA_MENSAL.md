# RETROSPECTIVA_MENSAL — Retrospectiva Mensal

**ID:** `CI-001` | **Fase:** #phase/1-15 | **Owner:** Product Manager | **Status:** #status/pending

---

## 1. OBJETIVO

Estabelecer um processo estruturado de retrospectiva mensal para revisar o desempenho do sistema de value betting, capturar lições aprendidas, identificar áreas de melhoria e planejar ações para o mês seguinte.

---

## 2. CONTEXTO

A retrospectiva mensal é um pilar da melhoria contínua porque:
- Fornece visibilidade abrangente do desempenho
- Permite análise de tendências ao longo do tempo
- Captura lições antes que sejam esquecidas
- Alinha a equipa em objetivos e prioridades
- Transforma experiência em conhecimento

Sem retrospectiva estruturada:
- Lições são perdidas
- Mesmos problemas se repetem
- Decisões não são baseadas em dados
- A equipa não está alinhada
- Melhoria é acidental, não intencional

---

## 3. ESTRUTURA DA RETROSPECTIVA

### 3.1 Timing

**Quando:** Última semana de cada mês
**Duração:** 2-3 horas
**Participantes:** Product Manager, Chief Architect, Data Analyst, Development Team leads

---

### 3.2 Agenda

**1. Revisão de Métricas (30 min)**
- ROI, PnL, CLV do mês
- Comparação com mês anterior
- Comparação com backtest
- Análise de tendências

**2. O que Correu Bem (30 min)**
- Sucessos do mês
- Features lançadas com sucesso
- Melhorias de performance
- Processos que funcionaram bem

**3. O que Pode Melhorar (30 min)**
- Problemas enfrentados
- Incidências ocorridas
- Processos que falharam
- Oportunidades perdidas

**4. Lições Aprendidas (30 min)**
- Insights técnicos
- Insights de negócio
- Insights de processo
- Insights de mercado

**5. Decisões (30 min)**
- Aprovação de mudanças
- Priorização de backlog
- Alocação de recursos
- Decisões arquiteturais

**6. Planeamento do Próximo Mês (30 min)**
- Objetivos do mês
- Features a desenvolver
- Experimentos a realizar
- Riscos a mitigar

---

## 4. PREPARAÇÃO

### 4.1 Coleta de Dados (Antes da Reunião)

**Métricas de Negócio:**
- ROI diário, semanal, mensal
- PnL total e por desporto
- CLV vs PnL
- Maximum Drawdown
- Volume de apostas
- Hit rate por estratégia

**Métricas Técnicas:**
- Uptime
- Latency (P50, P95, P99)
- Error rate
- Deploy frequency
- Lead time

**Experimentos:**
- Lista de experimentos realizados
- Resultados de cada experimento
- Decisões tomadas

**Incidentes:**
- Lista de incidentes do mês
- Postmortems criados
- Lições documentadas

**Feedback:**
- Feedback da equipa
- Feedback de stakeholders
- Feedback de utilizadores (se aplicável)

---

### 4.2 Documentos a Preparar

**1. Relatório de Métricas**
- Dashboard executivo atualizado
- Gráficos de tendências
- Comparação com objetivos

**2. Relatório de Experimentos**
- Resumo de cada experimento
- Conclusões e decisões

**3. Relatório de Incidentes**
- Lista de incidentes
- Status de resolução
- Lições aprendidas

**4. Backlog Atualizado**
- Novos itens adicionados
- Prioridades atuais
- Progresso dos itens em andamento

---

## 5. CONDUÇÃO DA RETROSPECTIVA

### 5.1 Facilitação

**Responsável:** Product Manager ou Scrum Master
**Regras:**
- Criar ambiente seguro (sem blame)
- Encorajar participação de todos
- Manter foco na agenda
- Documentar tudo em tempo real
- Gerenciar tempo

---

### 5.2 Técnicas de Facilitação

**Para "O que Correu Bem":**
- Start-Stop-Continue
- Mad Sad Glad
- Kudos (agradecimentos)

**Para "O que Pode Melhorar":**
- 5 Whys (para causa raiz)
- Fishbone diagram
- Dot voting (priorização)

**Para Lições Aprendidas:**
- Timeline (cronologia do mês)
- Starfish (mais fazer, menos fazer, etc.)
- Brainstorming

**Para Decisões:**
- Fist to Five (consenso)
- Impact vs Effort matrix
- Decision matrix

---

### 5.3 Documentação em Tempo Real

**Usar:**
- Notion/Confluence para notas
- Miro/Mural para colaboração visual
- Gravação para referência

**Capturar:**
- Todos os pontos discutidos
- Decisões tomadas
- Ações atribuídas
- Lições identificadas

---

## 6. CONTEÚDO DA RETROSPECTIVA

### 6.1 Revisão de Métricas

**ROI:**
- ROI do mês: [X%]
- Comparação com mês anterior: [+/- Y%]
- Comparação com objetivo: [atingido/não atingido]
- Análise: [tendência, causas, implicações]

**PnL:**
- PnL do mês: [€X]
- PnL acumulado: [€Y]
- Comparação com backtest: [diferença]
- Análise: [variação, causas]

**CLV vs PnL:**
- CLV esperado: [€X]
- PnL realizado: [€Y]
- Diferença: [€Z]
- Análise: [sistema performando como esperado?]

**Maximum Drawdown:**
- Drawdown máximo: [X%]
- Duração do drawdown: [X dias]
- Recuperação: [sim/não]
- Análise: [risco aceitável?]

**Volume:**
- Volume de apostas: [X apostas]
- Comparação com objetivo: [+/- Y%]
- Por desporto: [breakdown]
- Análise: [oportunidades sendo aproveitadas?]

---

### 6.2 O que Correu Bem

**Exemplos:**
- Novo modelo de ténis aumentou ROI em 0.5%
- Integração com bookmaker X bem-sucedida
- Redução de latency em 40%
- Zero downtime durante o mês
- Equipa entregou todas as features planeadas

**Formato:**
| Item | Impacto | Contribuidores |
|------|---------|----------------|
| [Descrição] | [Alto/Médio/Baixo] | [Nomes] |

---

### 6.3 O que Pode Melhorar

**Exemplos:**
- Error rate aumentou para 3% na semana 3
- Deploy da feature Y causou downtime de 1 hora
- Comunicação entre equipas foi ineficiente
- Documentação de API está desatualizada
- Modelo de basquetebol underperforming

**Formato:**
| Problema | Impacto | Causa Raiz | Prioridade |
|----------|---------|------------|------------|
| [Descrição] | [Alto/Médio/Baixo] | [Causa] | [P1/P2/P3] |

---

### 6.4 Lições Aprendidas

**Por Categoria:**

**Técnicas:**
- [Lição sobre arquitetura/código/ferramentas]

**De Negócio:**
- [Lição sobre estratégias/mercado/bookmakers]

**De Processo:**
- [Lição sobre metodologias/workflows]

**De Pessoas:**
- [Lição sobre comunicação/colaboração]

**Formato:**
```markdown
## Lição: [Título]
**Categoria:** [Técnica/Negócio/Processo/Pessoas]
**Contexto:** [O que aconteceu]
**Lições:** [O que aprendemos]
**Aplicação:** [Como aplicar no futuro]
```

---

### 6.5 Decisões

**Tipos de Decisões:**

**Decisões de Produto:**
- Aprovar/rejeitar feature X
- Priorizar Y sobre Z
- Mudar roadmap

**Decisões Técnicas:**
- Adotar/não adotar tecnologia X
- Refatorar componente Y
- Mudar arquitetura de Z

**Decisões de Processo:**
- Mudar metodologia de desenvolvimento
- Alterar processo de review
- Implementar nova ferramenta

**Decisões de Pessoas:**
- Alocar recursos para projeto X
- Formar equipa em tecnologia Y
- Contratar/contratar Z

**Formato:**
| Decisão | Tipo | Justificativa | Responsável | Prazo |
|---------|------|---------------|-------------|-------|
| [Descrição] | [Produto/Técnico/Processo/Pessoas] | [Por que] | [Nome] | [Data] |

---

### 6.6 Ações

**Formato:**
| Ação | Tipo | Owner | Prioridade | Deadline | Status |
|------|------|-------|------------|----------|--------|
| [Descrição] | [Corretiva/Preventiva/Melhoria] | [Nome] | [P1/P2/P3] | [Data] | [Pendente/Em Curso/Concluída] |

**Tipos de Ações:**
- **Corretivas:** Corrigir problemas identificados
- **Preventivas:** Prevenir problemas futuros
- **Melhoria:** Otimizar processos existentes
- **Experimentação:** Testar novas ideias

---

### 6.7 Planeamento do Próximo Mês

**Objetivos:**
1. [Objetivo 1] - [Métrica de sucesso]
2. [Objetivo 2] - [Métrica de sucesso]
3. [Objetivo 3] - [Métrica de sucesso]

**Features a Desenvolver:**
- [Feature 1] - [Prioridade] - [Responsável]
- [Feature 2] - [Prioridade] - [Responsável]

**Experimentos a Realizar:**
- [Experimento 1] - [Hipótese] - [Duração]
- [Experimento 2] - [Hipótese] - [Duração]

**Riscos a Mitigar:**
- [Risco 1] - [Plano de mitigação]
- [Risco 2] - [Plano de mitigação]

---

## 7. DECISÕES DE ARQUITETURA

### 7.1 Documentação de Decisões

Toda decisão que altere o sistema deve ser:

**1. Documentada**
- O que foi decidido
- Por que foi decidido
- Alternativas consideradas
- Trade-offs analisados

**2. Revisada**
- Revisada na próxima retrospectiva
- Validada se está funcionando como esperado
- Ajustada se necessário

**3. Justificada com Dados**
- Decisões baseadas em dados, não intuição
- Métricas que suportam a decisão
- Experimentos realizados (se aplicável)

---

### 7.2 Template de Decisão de Arquitetura

```markdown
# Decisão de Arquitetura: [Título]

**ID:** AD-XXX
**Data:** DD/MM/AAAA
**Autor:** [Nome]
**Status:** [Proposta/Aprovada/Implementada/Rejeitada]

## Contexto
[Descrição do problema ou oportunidade]

## Decisão
[O que foi decidido]

## Justificativa
[Por que esta decisão foi tomada]

## Alternativas Consideradas
1. [Alternativa 1] - [Prós/Contras]
2. [Alternativa 2] - [Prós/Contras]
3. [Alternativa 3] - [Prós/Contras]

## Trade-offs
[Trade-offs analisados]

## Impacto
[Impacto no sistema, equipa, negócio]

## Implementação
[Como implementar]

## Revisão
[Data da próxima revisão]
[Critérios de sucesso]
```

---

## 8. RELATÓRIO DE RETROSPECTIVA

### 8.1 Estrutura do Relatório

**1. Resumo Executivo**
- Highlights do mês
- Métricas chave
- Principais decisões

**2. Métricas Detalhadas**
- Todos os gráficos e tabelas
- Análise de tendências
- Comparação com objetivos

**3. O que Correu Bem**
- Lista de sucessos
- Impacto de cada sucesso
- Reconhecimento à equipa

**4. O que Pode Melhorar**
- Lista de problemas
- Análise de causa raiz
- Planos de ação

**5. Lições Aprendidas**
- Todas as lições documentadas
- Categorização por tipo
- Aplicação futura

**6. Decisões**
- Todas as decisões tomadas
- Justificativas
- Responsáveis

**7. Ações**
- Lista de ações
- Responsáveis
- Prazos
- Status

**8. Planeamento do Próximo Mês**
- Objetivos
- Features
- Experimentos
- Riscos

---

### 8.2 Distribuição

**Para:**
- Toda a equipa
- Stakeholders
- Executivos (se aplicável)

**Quando:**
- Até 2 dias após a retrospectiva

**Formato:**
- Email com resumo
- Documento completo em wiki
- Apresentação em reunião (opcional)

---

## 9. SEGUIMENTO

### 9.1 Reunião de Seguimento

**Quando:** 1 semana após a retrospectiva
**Duração:** 30 minutos
**Participantes:** Owners das ações

**Agenda:**
- Status das ações
- Bloqueios identificados
- Ajustes necessários

---

### 9.2 Tracking de Ações

**Métricas:**
- Percentagem de ações concluídas no prazo
- Tempo médio de conclusão
- Percentagem de ações que resolveram o problema

**Meta:**
- > 80% das ações concluídas no prazo
- Todas as ações críticas concluídas

---

## 10. BOAS PRÁTICAS

### 10.1 Princípios

**1. Psicologicamente Seguro**
- Sem blame
- Foco em sistemas, não pessoas
- Erros são oportunidades de aprendizado

**2. Baseado em Dados**
- Decisões suportadas por métricas
- Evitar opiniões sem evidência
- Usar dados para priorizar

**3. Ação-Orientado**
- Cada problema deve ter ação associada
- Cada ação deve ter responsável e prazo
- Ações devem ser específicas e mensuráveis

**4. Inclusivo**
- Todos devem participar
- Diferentes perspectivas são valorizadas
- Ideias de todos são consideradas

**5. Consistente**
- Mesma estrutura sempre
- Mesma cadência (mensal)
- Mesma qualidade de documentação

---

### 10.2 Anti-Patterns

**❌ Não fazer:**
- Transformar em sessão de blame
- Focar apenas em problemas (ignorar sucessos)
- Documentar sem agir
- Pular retrospectivas por "falta de tempo"
- Ter retrospectivas sem preparação

**✅ Fazer:**
- Celebrar sucessos
- Equilibrar problemas e soluções
- Transformar lições em ações
- Priorizar retrospectivas
- Preparar bem cada reunião

---

## 11. LINKS CRUZADOS

- [[49_Continuous_Improvement/INDEX]] ← Secção mãe
- [[49_Continuous_Improvement/CICLO_PDCA]] → Retrospectiva no ciclo ACT
- [[49_Continuous_Improvement/METRICAS_E_KPIS]] → Métricas para revisão
- [[49_Continuous_Improvement/EXPERIMENTACAO]] → Revisão de experimentos
- [[49_Continuous_Improvement/FEEDBACK_LOOPS]] → Feedback coletado
- [[49_Continuous_Improvement/LEARNING_ORGANIZATION]] → Captura de lições
- [[27_Postmortems/INDEX]] → Análise de incidentes
