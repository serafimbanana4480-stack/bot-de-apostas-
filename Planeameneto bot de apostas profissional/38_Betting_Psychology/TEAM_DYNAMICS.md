# TEAM_DYNAMICS — Dinâmica de Equipa e Suporte Mútuo

**ID:** `BP-005` | **Fase:** #phase/4 | **Owner:** Operations Lead | **Status:** #status/pending

---

## 1. VISÃO GERAL

Mesmo em operações individuais, a dinâmica de equipa é crítica. Este documento define como estruturar comunicação, suporte mútuo, accountability e cultura para criar um ambiente que promova disciplina, previna tilt e suporte bem-estar mental. Se a operação for individual, estes princípios podem ser adaptados para "equipa virtual" (mentor, buddy, comunidade).

---

## 2. ESTRUTURA DE EQUIPA

### 2.1 Roles e Responsabilidades

| Role | Responsabilidades | Skills Necessárias |
|------|-------------------|-------------------|
| **Operations Lead** | Coordenação operacional, decisão final, gestão de risco | Liderança, disciplina, comunicação |
| **Risk Manager** | Monitorização de risco, aprovação de limites, circuit breakers | Análise de risco, estatística, assertividade |
| **Operator(s)** | Execução de trades, seguimento de checklists | Atenção, disciplina, resistência a stress |
| **Developer/Quant** | Manutenção do sistema, backtesting, melhorias | Programação, estatística, inovação |
| **Mental Coach** (opcional) | Suporte psicológico, treinamento de regulação emocional | Psicologia, coaching, comunicação |

### 2.2 Linha de Comando

```
┌─────────────────────────────────────┐
│      Operations Lead                │
│  (Decisão final, responsabilidade)  │
└──────────────┬──────────────────────┘
               │
       ┌───────┴───────┐
       ↓               ↓
┌──────────────┐  ┌──────────────┐
│Risk Manager  │  │ Mental Coach │
│ (Aprovações) │  │ (Suporte)    │
└──────────────┘  └──────────────┘
       │               │
       └───────┬───────┘
               ↓
       ┌──────────────┐
    →  │  Operators   │
    │  │ (Execução)   │
    │  └──────────────┘
    │         ↑
    └─────────┤
       ┌──────────────┐
       │  Developer   │
       │  (Sistema)   │
       └──────────────┘
```

**Regra:** O Operations Lead tem autoridade final, mas deve ouvir Risk Manager e Mental Coach antes de decisões críticas.

---

## 3. COMUNICAÇÃO

### 3.1 Canais de Comunicação

| Canal | Propósito | Frequência | Urgência |
|-------|-----------|------------|----------|
| **Slack #operations** | Comunicação operacional diária | Contínuo | Normal |
| **Slack #alerts** | Alertas automáticos do sistema | Automático | Alta |
| **Slack #emergency** | Incidentes críticos | Quando necessário | Crítica |
| **Email** | Documentação formal, relatórios | Semanal | Baixa |
| **Zoom/Teams** | Reuniões, revisões | Semanal/Mensal | Normal |
| **Telegram** | Alertas urgentes fora de horário | Quando necessário | Alta |

### 3.2 Protocolos de Comunicação

**Comunicação de Tilt:**
```
OPERADOR → RISK MANAGER:
"Estou em tilt (score: 75/100). Pausando operação.
Gatilho: 5 perdas consecutivas.
Ação: Pausa 1h, respiração, caminhada."

RISK MANAGER → OPERADOR:
"Recebido. Pausa confirmada.
Vou monitorizar. Retorne quando score < 30.
Estou disponível se precisar falar."
```

**Comunicação de Incidente:**
```
OPERADOR → OPERATIONS LEAD + RISK MANAGER:
"INCIDENTE: Sistema parou inesperadamente.
Hora: 14:30
Impacto: 2 trades não executados
Ação: Investigando causa
Status: Em progresso"
```

**Comunicação de Decisão Crítica:**
```
RISK MANAGER → OPERATIONS LEAD:
"PROPOSTA: Aumentar max stake de 2% para 2.5%
Justificação: Backtest mostra +15% ROI com volatilidade similar
Risco: Drawdown max aumenta de 15% para 18%
Recomendação: Aprovar com monitorização aumentada"

OPERATIONS LEAD → TODOS:
"DECISÃO: APROVADO
Condições: Monitorização aumentada por 2 semanas
Revisão obrigatória após 1 semana
Implementação: Próxima segunda-feira"
```

### 3.3 Regras de Comunicação

1. **Ser claro e conciso:** Não ambiguidade
2. **Incluir contexto:** O que, quando, porquê
3. **Usar formatos estruturados:** Bullet points, tabelas
4. **Confirmar recebimento:** "Recebido", "Ação tomada"
5. **Documentar decisões:** Tudo em escrito
6. **Ser respeitoso:** Mesmo em stress
7. **No finger-pointing:** Foco em solução, não culpa

---

## 4. SUORTE MÚTUO

### 4.1 Buddy System

**Cada operador tem um "buddy" (parceiro de accountability)**

**Responsabilidades do Buddy:**
- Check-in diário (estado mental)
- Notificação se tilt detetado
- Revisão semanal conjunta
- Suporte emocional quando necessário
- Accountability mútua

**Check-in Diário Template:**
```
Buddy A → Buddy B:
"Check-in diário:
- Estado mental: 7/10
- Stress level: 3/10
- Dormi bem: Sim
- Pronto para operar: Sim
- Algo a partilhar: Não"

Buddy B → Buddy A:
"Recebido. Tudo parece ok.
Vou monitorizar. Boa sorte hoje!"
```

**Quando Buddy Reporta Tilt:**
```
Buddy A → Buddy B:
"Estou em tilt (score: 65/100).
Vou pausar 1h.
Podes verificar às 15:30 se estou melhor?"

Buddy B → Buddy A:
"Recebido. Vou verificar às 15:30.
Boa sorte na recuperação.
Estou aqui se precisares falar."
```

### 4.2 Peer Review

**Revisão Semanal (30 min):**
```markdown
## Peer Review - Semana de 2024-01-15

### Participantes
- Operador A
- Buddy B

### Métricas da Semana
| Métrica | Operador A | Target | Status |
|---------|------------|--------|--------|
| Trades executados | 45 | 40-60 | ✅ |
| P&L | +€120 | +€50-150 | ✅ |
| Tilt incidents | 1 | < 2 | ✅ |
| Adesão a checklists | 98% | 100% | ⚠️ |
| Pauses preventivas | 3 | > 2 | ✅ |

### Pontos Positivos
- Bom P&L
- Tilt bem gerido (pausa rápida)
- Boa adesão ao sistema

### Pontos a Melhorar
- 2 trades sem checklist completo
- Um dia com >8h de operação

### Plano de Ação
- Revisar checklist pré-operação
- Implementar timer de 8h automático

### Acordo de Accountability
- Buddy B vai verificar checklists diariamente
- Se violação → notificação imediata

### Próxima Revisão
2024-01-22
```

### 4.3 Suporte Emocional

**Quando alguém está em dificuldade:**

**Passo 1: Escuta Ativa**
- Ouvir sem julgar
- Não dar soluções imediatas
- Validar sentimentos: "Compreendo que estás frustrado"

**Passo 2: Normalização**
- "É normal sentir isto depois de uma sequência de perdas"
- "Todos nós já passámos por isto"
- "Variação é parte do jogo"

**Passo 3: Foco em Solução**
- "O que podes fazer agora?"
- "Vamos rever o sistema juntos"
- "Quais são as opções?"

**Passo 4: Acompanhamento**
- Verificar como está depois
- Oferecer ajuda adicional
- Encorajar pausa se necessário

**O que NÃO fazer:**
- Não minimizar: "Não é grande coisa"
- Não culpar: "Deverias ter seguido o sistema"
- Não dar conselhos não solicitados
- Não comparar: "Eu nunca faço isto"

---

## 5. CULTURA ORGANIZACIONAL

### 5.1 Valores Fundamentais

| Valor | Descrição | Comportamento Esperado |
|-------|-----------|------------------------|
| **Processo sobre Resultado** | Julgar pela execução, não P&L | Celebrar boa execução mesmo com perda |
| **Transparência** | Ser honesto sobre erros e tilt | Reportar tilt imediatamente, não esconder |
| **Accountability** | Responsabilizar-se por ações | Admitir erros, não culpar sistema |
| **Suporte Mútuo** | Ajudar colegas em dificuldade | Oferecer ajuda, não julgar |
| **Melhoria Contínua** | Aprender com erros | Documentar lições, implementar melhorias |
| **Respeito** | Tratar todos com dignidade | Comunicação respeitosa mesmo em stress |

### 5.1 Psicologia Segura (Psychological Safety)

**Definição:** Ambiente onde as pessoas se sentem seguras para tomar riscos interpessoais (admitir erros, pedir ajuda, desafiar status quo).

**Como Criar:**
1. **Liderança por exemplo:** Operations Lead admite erros também
2. **No retaliation:** Ninguém é punido por admitir tilt
3. **Celebrar vulnerabilidade:** "Obrigado por ser honesto sobre o tilt"
4. **Foco em sistema:** Não "tu erraste", mas "o sistema permitiu este erro"
5. **Reuniões de lições aprendidas:** Foco em melhorar, não culpar

**Exemplo de Líder Criando Segurança:**
```
OPERATIONS LEAD:
"Ontem cometi um erro — não segui o checklist
e executei um trade sem validação completa.
Perdi €50. Foi meu erro, não do sistema.
Vou implementar uma verificação extra no checklist
para prevenir isto no futuro.
Agradeço se todos puderem verificar se
têm vulnerabilidades similares."
```

---

## 6. GESTÃO DE CONFLITOS

### 6.1 Fontes Comuns de Conflito

| Fonte | Exemplo | Prevenção |
|-------|---------|-----------|
| **Decisões de risco** | Desacordo sobre limites | Processo de aprovação claro |
| **Performance** | Comparação de P&L | Foco em processo, não resultado |
| **Tilt de um membro** | Tilt afeta operação de outros | Buddy system, pausas |
| **Erro técnico** | Bug causa perdas | Cultura de não culpa |
| **Comunicação** | Mal-entendidos | Protocolos claros |

### 6.2 Resolução de Conflitos

**Passo 1: Identificar o Problema**
- O que é o conflito real? (frequentemente não é o óbvio)
- Quais são os interesses de cada parte?

**Passo 2: Escuta Mútua**
- Cada parte expõe o seu ponto de vista
- O outro ouve sem interromper
- Repetir para confirmar compreensão

**Passo 3: Encontrar Interesses Comuns**
- Todos querem o sistema a funcionar
- Todos querem minimizar perdas
- Todos querem um ambiente saudável

**Passo 4: Gerar Soluções**
- Brainstorm de opções
- Avaliar cada opção
- Escolher a melhor para todos

**Passo 5: Acordo e Implementação**
- Documentar o acordo
- Implementar
- Revisar depois

**Exemplo:**
```
CONFLITO: Risk Manager quer limitar stake a 1.5%, Operator quer 2%

PASSO 1 - IDENTIFICAR:
Risk Manager: Preocupado com drawdown
Operator: Sente que limita potencial de lucro

PASSO 2 - ESCUTA:
Risk Manager explica: "Vi backtest com drawdown de 20% a 2%"
Operator explica: "A 1.5% ROI cai 30%"

PASSO 3 - INTERESSES COMUNS:
Ambos querem sistema sustentável a longo prazo

PASSO 4 - SOLUÇÕES:
A) Manter 2%, mas com circuit breaker mais agressivo
B) Aumentar para 1.75% (compromisso)
C) Testar 2% por 1 mês com monitorização

PASSO 5 - ACORDO:
Implementar C (teste de 1 mês)
Se drawdown > 15%, voltar a 1.5%
Se drawdown < 12%, manter 2%
```

---

## 7. ONBOARDING E TREINAMENTO

### 7.1 Onboarding de Novos Membros

**Semana 1:**
- [ ] Apresentação à equipa e cultura
- [ ] Leitura de toda a documentação de psicologia
- [ ] Compreensão do sistema de operações
- [ ] Setup de ambiente de trabalho
- [ ] Atribuição de buddy

**Semana 2:**
- [ ] Observação de operações (shadowing)
- [ ] Prática de checklists (simulação)
- [ ] Treinamento de regulação emocional
- [ ] Compreensão de limites e circuit breakers

**Semana 3-4:**
- [ ] Operações supervisionadas
- [ ] Execução de trades com aprovação
- [ ] Revisões diárias com buddy
- [ ] Treinamento de deteção de tilt

**Mês 2:**
- [ ] Operações independentes (com monitorização)
- [ ] Revisões semanais completas
- [ ] Avaliação de performance

**Mês 3:**
- [ ] Operações fully independentes
- [ ] Integração completa na equipa

### 7.2 Treinamento Contínuo

**Treinamento Mensal:**
- Revisão de psicologia (1 hora)
- Atualização de protocolos (30 min)
- Share de lições aprendidas (30 min)

**Treinamento Trimestral:**
- Workshop de regulação emocional (2 horas)
- Treinamento de deteção de tilt avançado (1 hora)
- Team building (2 horas)

**Treinamento Anual:**
- Retiro de equipa (1-2 dias)
- Revisão completa de cultura
- Planeamento estratégico

---

## 8. MÉTRICAS DE EQUIPA

### 8.1 Métricas de Performance

| Métrica | Target | Alerta |
|---------|--------|--------|
| **Adesão a checklists (equipa)** | 100% | < 95% |
| **Tilt incidents (equipa/mês)** | < 5 | > 10 |
| **Comunicação de tilt (reportados)** | 100% | < 80% |
| **Peer reviews completas** | 100% | < 90% |
| **Satisfação da equipa (survey)** | > 8/10 | < 6/10 |
| **Retenção de membros** | > 90% anual | < 80% |

### 8.2 Survey de Clima (Mensal)

```markdown
## Survey de Clima - Janeiro 2024

### Escala: 1 (Péssimo) a 10 (Excelente)

1. Sinto-me seguro para admitir erros: ___/10
2. A comunicação na equipa é clara: ___/10
3. Sinto suporte dos colegas: ___/10
4. A cultura foca em processo, não resultado: ___/10
5. Tenho recursos para gerir stress: ___/10
6. O buddy system é útil: ___/10
7. As reuniões são produtivas: ___/10
8. Sinto-me valorizado na equipa: ___/10

### Comentários Livres:
[espaço para feedback]

### Sugestões de Melhoria:
[espaço para sugestões]
```

---

## 9. PARA OPERAÇÕES INDIVIDUAIS

Se a operação é individual, adaptar estes princípios:

### 9.1 Equipa Virtual

- **Mentor:** Alguém com experiência para revisão mensal
- **Accountability Partner:** Amigo ou colega para check-in semanal
- **Comunidade:** Fórum ou grupo de traders para partilha
- **Terapeuta/Coach:** Profissional para suporte emocional

### 9.2 Auto-Accountability

- Documentar tudo (como se fosse para equipa)
- Revisões semanais estruturadas
- Gravar checklists em vídeo (para accountability)
- Usar apps de habit tracking

### 9.3 Rotinas de "Equipa"

- Reunião consigo mesmo (semanal)
- "Peer review" com versão passada (comparar diários)
- Simular feedback de buddy (perguntar: "O que diria o meu buddy?")

---

## 10. BACKLOG

- [ ] Definir estrutura de equipa completa
- [ ] Implementar buddy system
- [ ] Criar templates de comunicação
- [ ] Desenvolver survey de clima
- [ ] Planejar treinamento trimestral
- [ ] Criar processo de onboarding

---

## 11. LINKS CRUZADOS

- [[38_Betting_Psychology/INDEX]] ← Secão mãe
- [[38_Betting_Psychology/TILT_MANAGEMENT]] → Gestão de tilt
- [[38_Betting_Psychology/DISCIPLINE_FRAMEWORK]] → Framework de disciplina
- [[38_Betting_Psychology/EMOTIONAL_REGULATION]] → Regulação emocional