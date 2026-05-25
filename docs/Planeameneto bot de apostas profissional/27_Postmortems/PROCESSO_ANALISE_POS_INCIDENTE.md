# PROCESSO_ANALISE_POS_INCIDENTE — Guia de Análise Pós-Incidente

**ID:** `PM-PROC` | **Fase:** #phase/1-15 | **Owner:** Operations Lead | **Status:** #status/active
**Última Revisão:** 2024-05-13 | **Próxima Revisão:** 2024-08-13

---

## 1. OBJETIVO

Estabelecer um processo estruturado para análise pós-incidente (postmortem) no sistema de value betting NBA, garantindo que cada incidente é analisado de forma profunda, as lições aprendidas são documentadas, e as ações corretivas são implementadas para prevenir recorrência.

---

## 2. PRINCÍPIOS FUNDAMENTAIS

### 2.1. Blameless Postmortem
- **Foco em sistemas, não em pessoas:** Se um humano errou, o sistema deveria ter impedido
- **Cultura de aprendizagem:** O objetivo é aprender, não culpar
- **Transparência:** Postmortems são partilhados com toda a equipa
- **Confiança:** Equipa deve sentir-se segura para relatar erros

### 2.2. Análise de Causa Raiz
- **Ir além do sintoma:** Não aceitar "erro humano" como causa raiz
- **Técnica dos 5 Porquês:** Perguntar "porquê" 5 vezes para chegar à causa raiz
- **Análise de Contribuintes:** Identificar todos os fatores que contribuíram

### 2.3. Ações Corretivas
- **Específicas e Mensuráveis:** Ações devem ser concretas e verificáveis
- **Com Owner e Deadline:** Cada ação tem responsável e data
- **Priorizadas:** Ações críticas primeiro, depois melhorias
- **Verificadas:** Ações são verificadas após implementação

---

## 3. QUANDO CRIAR POSTMORTEM

| Severidade | Obrigatório? | Prazo |
|------------|--------------|-------|
| P1 (Crítico) | Sim | 24-48 horas após resolução |
| P2 (Alto) | Sim | 3-5 dias após resolução |
| P3 (Médio) | Recomendado | 7 dias após resolução |
| P4 (Baixo) | Opcional | 14 dias após resolução |
| P5 (Informativo) | Não | N/A |

**Critérios adicionais para postmortem obrigatório:**
- Qualquer incidente com impacto financeiro > 1000 EUR
- Qualquer incidente que afete > 50% dos subscritores
- Qualquer incidente que resulte em perda de dados
- Qualquer incidente que exija rollback
- Qualquer incidente que resulte em downtime > 1 hora

---

## 4. PROCESSO DE POSTMORTEM

### 4.1. Fase 1: Preparação (Imediatamente após resolução)

**Objetivo:** Recolher dados e preparar para análise.

**Passos:**

1. **Agendar reunião de postmortem:**
   - [ ] Agendar dentro de 24-48 horas (P1) ou 3-5 dias (P2)
   - [ ] Convidar todos os envolvidos na resposta
   - [ ] Convidar stakeholders relevantes
   - [ ] Definir duração (60-120 minutos)

2. **Recolher dados:**
   - [ ] Logs de todos os sistemas afetados
   - [ ] Métricas de monitorização (Grafana, etc.)
   - [ ] Timeline de eventos (do alerta à resolução)
   - [ ] Capturas de tela relevantes
   - [ ] Comunicações (Telegram, email)
   - [ ] Runbooks usados
   - [ ] Decisões tomadas

3. **Criar rascunho do postmortem:**
   - [ ] Usar template TEMPLATE_POSTMORTEM
   - [ ] Preencher metadados básicos
   - [ ] Criar timeline preliminar
   - [ ] Listar hipóteses de causa raiz

### 4.2. Fase 2: Reunião de Postmortem (60-120 minutos)

**Objetivo:** Analisar incidente em grupo e identificar causa raiz.

**Estrutura da reunião:**

1. **Introdução (5 minutos):**
   - Objetivo da reunião
   - Princípio de blameless
   - Regras de engajamento

2. **Timeline (15-20 minutos):**
   - Apresentar timeline de eventos
   - Cada participante adiciona detalhes
   - Identificar lacunas na timeline
   - Clarificar decisões tomadas

3. **Análise de Causa Raiz (30-40 minutos):**
   - Usar técnica dos 5 Porquês
   - Identificar causas diretas
   - Identificar causas contribuintes
   - Identificar causas sistémicas

4. **Impacto (10 minutos):**
   - Quantificar impacto financeiro
   - Quantificar impacto em subscritores
   - Quantificar impacto em operações
   - Identificar impacto secundário

5. **Ações Corretivas (20-30 minutos):**
   - Brainstorm de ações preventivas
   - Priorizar ações (critical, high, medium, low)
   - Atribuir owner a cada ação
   - Definir deadline para cada ação

6. **Lição Aprendida (5-10 minutos):**
   - O que correu bem na resposta?
   - O que pode ser melhorado?
   - O que aprendemos?

### 4.3. Fase 3: Documentação (24-48 horas após reunião)

**Objetivo:** Documentar análise de forma completa e partilhável.

**Passos:**

1. **Completar postmortem:**
   - [ ] Preencher todas as secções do template
   - [ ] Incluir timeline detalhada
   - [ ] Incluir análise de causa raiz
   - [ ] Incluir impacto quantificado
   - [ ] Incluir ações corretivas com owners e deadlines

2. **Revisão:**
   - [ ] Enviar rascunho para participantes revisar
   - [ ] Incorporar feedback
   - [ ] Obter aprovação final

3. **Publicação:**
   - [ ] Guardar em 27_Postmortems
   - [ ] Atualizar INDEX.md
   - [ ] Partilhar com equipa (canal ops_documentacao)
   - [ ] Partilhar com stakeholders (se aplicável)

### 4.4. Fase 4: Acompanhamento (30-90 dias)

**Objetivo:** Garantir que ações corretivas são implementadas.

**Passos:**

1. **Acompanhamento semanal (primeiras 4 semanas):**
   - [ ] Verificar progresso das ações críticas
   - [ ] Identificar bloqueios
   - [ ] Ajudar a desbloquear

2. **Acompanhamento mensal (até 90 dias):**
   - [ ] Verificar progresso de todas as ações
   - [ ] Atualizar status no postmortem
   - [ ] Marcar ações como concluídas

3. **Verificação final:**
   - [ ] Confirmar que todas as ações estão concluídas
   - [ ] Verificar que ações são eficazes
   - [ ] Documentar resultado da verificação

---

## 5. TÉCNICAS DE ANÁLISE

### 5.1. Técnica dos 5 Porquês

**Exemplo:**
- **Porquê o sistema ficou offline?** O PostgreSQL crashou.
- **Porquê o PostgreSQL crashou?** Ficou sem memória.
- **Porquê ficou sem memória?** Uma query consumiu toda a memória.
- **Porquê a query consumiu toda a memória?** Não tinha LIMIT clause.
- **Porquê não tinha LIMIT clause?** O desenvolvedor esqueceu de adicionar.

**Causa raiz:** Falta de code review que não detetou ausência de LIMIT clause.

### 5.2. Análise de Contribuintes

Identificar todos os fatores que contribuíram:
- **Fatores técnicos:** Sistema, código, infraestrutura
- **Fatores de processo:** Procedimentos, documentação, treinamento
- **Fatores humanos:** Fadiga, pressão, falta de conhecimento
- **Fatores organizacionais:** Cultura, prioridades, recursos

### 5.3. Análise de Barreiras

Identificar barreiras que poderiam ter prevenido o incidente:
- Barreiras técnicas (monitorização, alertas, automação)
- Barreiras de processo (code review, testes, aprovações)
- Barreiras de treinamento (conhecimento, skills)

---

## 6. MELHORES PRÁTICAS

### 6.1. Durante a Reunião
- Começar com o princípio de blameless
- Focar em fatos, não em opiniões
- Encorajar participação de todos
- Não interromper quando alguém está a explicar
- Documentar em tempo real

### 6.2. Na Documentação
- Ser específico e detalhado
- Usar linguagem clara e objetiva
- Incluir dados e métricas
- Evitar jargão técnico excessivo
- Ser honesto sobre falhas

### 6.3. Nas Ações Corretivas
- Focar em prevenção, não em correção
- Ações devem ser sistemáticas, não ad-hoc
- Priorizar ações que previnem múltiplos incidentes
- Considerar custo-benefício de cada ação

---

## 7. MÉTRICAS DE SUCESSO

| Métrica | Threshold | Ação se não cumprido |
|---------|-----------|---------------------|
| Postmortems criados (P1/P2) | 100% | Investigar porque não foram criados |
| Tempo para criar postmortem (P1) | < 48 horas | Otimizar processo |
| Ações corretivas implementadas | > 90% em 90 dias | Escalar ações pendentes |
| Incidentes recorrentes (mesma causa) | < 5% | Revisar eficácia de ações |
| Participação na reunião | > 80% dos convidados | Ajustar horário |

---

## 8. LINKS CRUZADOS

- [[27_Postmortems/INDEX]] ← Secção mãe
- [[27_Postmortems/TEMPLATE_POSTMORTEM]] → Template
- [[26_Runbooks/INDEX]] → Runbooks que precedem postmortem