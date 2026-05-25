# TEMPLATE_POSTMORTEM — Template de Análise Pós-Incidente

**ID:** `PM-XXX` | **Fase:** #phase/1-15 | **Owner:** [Nome] | **Status:** #status/draft
**Data do Incidente:** YYYY-MM-DD | **Data do Postmortem:** YYYY-MM-DD
**Versão:** 1.0

---

## 1. METADADOS

| Campo | Valor |
|-------|-------|
| Título | [Breve descrição do incidente] |
| Data do Incidente | YYYY-MM-DD |
| Hora de Início | HH:MM UTC |
| Hora de Fim | HH:MM UTC |
| Duração | X minutos/horas |
| Severidade | [P1-Crítico / P2-Alto / P3-Médio / P4-Baixo] |
| Impacto | [Crítico / Alto / Médio / Baixo] |
| Sistema(s) Afetado(s) | [Lista de sistemas] |
| Trigger | [O que causou o incidente] |
| Responsável pela Resposta | [Nome] |
| Autor do Postmortem | [Nome] |
| Participantes na Reunião | [Lista de nomes] |

---

## 2. RESUMO EXECUTIVO

[2-3 parágrafos sobre o que aconteceu]

**Parágrafo 1:** Descrição do incidente (o que aconteceu, quando, onde)

**Parágrafo 2:** Impacto do incidente (quem foi afetado, qual foi o dano)

**Parágrafo 3:** Resolução e status atual (como foi resolvido, sistema está estável)

---

## 3. TIMELINE DETALHADO

| Hora (UTC) | Evento | Detalhes | Responsável |
|------------|--------|----------|-------------|
| HH:MM | [Primeiro sinal de problema] | [Detalhes do alerta] | [Quem recebeu] |
| HH:MM | [Investigação iniciada] | [Ações tomadas] | [Quem investigou] |
| HH:MM | [Causa identificada] | [Descrição da causa] | [Quem identificou] |
| HH:MM | [Ação de mitigação] | [O que foi feito] | [Quem executou] |
| HH:MM | [Resolução] | [Como foi resolvido] | [Quem resolveu] |
| HH:MM | [Verificação] | [Como foi verificado] | [Quem verificou] |

**Notas:**
- Incluir todos os eventos relevantes
- Incluir decisões tomadas
- Incluir comunicações enviadas
- Incluir mudanças de estado do sistema

---

## 4. ANÁLISE DE CAUSA RAIZ

### 4.1. Sintomas
- [Sintoma 1]
- [Sintoma 2]
- [Sintoma 3]

### 4.2. Causas Imediatas
- [Causa imediata 1]
- [Causa imediata 2]

### 4.3. Análise dos 5 Porquês

**Porquê [sintoma]?**
- [Resposta]

**Porquê [resposta anterior]?**
- [Resposta]

**Porquê [resposta anterior]?**
- [Resposta]

**Porquê [resposta anterior]?**
- [Resposta]

**Porquê [resposta anterior]?**
- [Resposta] ← **Causa Raiz**

### 4.4. Causas Contribuintes
- **Fatores Técnicos:** [Lista]
- **Fatores de Processo:** [Lista]
- **Fatores Humanos:** [Lista]
- **Fatores Organizacionais:** [Lista]

### 4.5. Causa Raiz Final
[Descrição clara da causa raiz]

---

## 5. IMPACTO

### 5.1. Impacto Financeiro

| Métrica | Valor |
|---------|-------|
| Perda Financeira Estimada | X EUR |
| Custo de Resolução | Y EUR |
| Custo de Ações Corretivas | Z EUR |
| Total | W EUR |

### 5.2. Impacto Operacional

| Métrica | Valor |
|---------|-------|
| Duração do Downtime | X minutos/horas |
| Sistemas Afetados | [Lista] |
| Serviços Indisponíveis | [Lista] |
| Dados Perdidos | [Sim/Não, detalhes] |

### 5.3. Impacto em Subscritores

| Métrica | Valor |
|---------|-------|
| Número de Subscritores Afetados | X |
| Percentual da Base | Y% |
| Queixas Recebidas | Z |
| Pedidos de Reembolso | W |

### 5.4. Impacto Secundário

- [Impacto secundário 1]
- [Impacto secundário 2]

---

## 6. RESPOSTA AO INCIDENTE

### 6.1. O Que Correu Bem
- [Coisa que correu bem 1]
- [Coisa que correu bem 2]

### 6.2. O Que Pode Ser Melhorado
- [Coisa que pode ser melhorada 1]
- [Coisa que pode ser melhorada 2]

### 6.3. Runbooks Usados
- [Runbook 1]
- [Runbook 2]

### 6.4. Desafios Enfrentados
- [Desafio 1]
- [Desafio 2]

---

## 7. AÇÕES CORRETIVAS

### 7.1. Ações Críticas (P1)

| Ação | Owner | Deadline | Status | Notas |
|------|-------|----------|--------|-------|
| [Ação 1] | [Nome] | [Data] | [Pendente/Em Progresso/Concluído] | [Notas] |
| [Ação 2] | [Nome] | [Data] | [Pendente/Em Progresso/Concluído] | [Notas] |

### 7.2. Ações Alta Prioridade (P2)

| Ação | Owner | Deadline | Status | Notas |
|------|-------|----------|--------|-------|
| [Ação 1] | [Nome] | [Data] | [Pendente/Em Progresso/Concluído] | [Notas] |
| [Ação 2] | [Nome] | [Data] | [Pendente/Em Progresso/Concluído] | [Notas] |

### 7.3. Ações Média Prioridade (P3)

| Ação | Owner | Deadline | Status | Notas |
|------|-------|----------|--------|-------|
| [Ação 1] | [Nome] | [Data] | [Pendente/Em Progresso/Concluído] | [Notas] |
| [Ação 2] | [Nome] | [Data] | [Pendente/Em Progresso/Concluído] | [Notas] |

### 7.4. Ações Baixa Prioridade (P4)

| Ação | Owner | Deadline | Status | Notas |
|------|-------|----------|--------|-------|
| [Ação 1] | [Nome] | [Data] | [Pendente/Em Progresso/Concluído] | [Notas] |
| [Ação 2] | [Nome] | [Data] | [Pendente/Em Progresso/Concluído] | [Notas] |

---

## 8. LIÇÕES APRENDIDAS

### 8.1. Lições Técnicas
- [Lição técnica 1]
- [Lição técnica 2]

### 8.2. Lições de Processo
- [Lição de processo 1]
- [Lição de processo 2]

### 8.3. Lições Organizacionais
- [Lição organizacional 1]
- [Lição organizacional 2]

### 8.4. Lições de Comunicação
- [Lição de comunicação 1]
- [Lição de comunicação 2]

---

## 9. PREVENÇÃO FUTURA

### 9.1. Melhorias de Monitorização
- [Melhoria 1]
- [Melhoria 2]

### 9.2. Melhorias de Processo
- [Melhoria 1]
- [Melhoria 2]

### 9.3. Melhorias de Documentação
- [Melhoria 1]
- [Melhoria 2]

### 9.4. Melhorias de Treinamento
- [Melhoria 1]
- [Melhoria 2]

---

## 10. ANEXOS

### 10.1. Logs Relevantes
- [Link ou anexo de logs]

### 10.2. Capturas de Tela
- [Link ou anexo de screenshots]

### 10.3. Métricas
- [Link ou anexo de métricas]

### 10.4. Comunicações
- [Link ou anexo de comunicações]

---

## 11. APROVAÇÃO

| Função | Nome | Data | Assinatura |
|--------|------|------|------------|
| Autor do Postmortem | [Nome] | [Data] | |
| Responsável pela Resposta | [Nome] | [Data] | |
| Operations Lead | [Nome] | [Data] | |
| CTO (se incidente P1) | [Nome] | [Data] | |

---

## 12. LINKS CRUZADOS

- [[27_Postmortems/INDEX]] ← Secção mãe
- [[27_Postmortems/PROCESSO_ANALISE_POS_INCIDENTE]] → Processo de análise
- [[26_Runbooks/INDEX]] → Runbooks relacionados
- [Runbook específico usado] → Link para runbook
