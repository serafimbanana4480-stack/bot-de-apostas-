# 38_Betting Psychology — INDEX

**ID:** `SEC-38` | **Fase:** Todas | **Owner:** Operations Lead | **Status:** #status/active

---

## 1. OBJETIVO

Reconhecer que o maior inimigo de um sistema quantitativo não é o mercado — é o operador humano. Documentar armadilhas psicológicas e criar sistemas para neutralizá-las.

---

## 2. ARMADILHAS PSICOLÓGICAS

### 2.1 Matriz de Armadilhas

| Armadilha | Sintoma | Sistema de Defesa | Documentação |
|-----------|---------|-------------------|--------------|
| **Tilt** | Apostar mais após perdas; aumentar stakes; irritabilidade | Kelly é lei absoluta; circuit breaker após 5 perdas | [[38_Betting_Psychology/TILT_MANAGEMENT]] |
| **Overconfidence** | Aumentar stakes após ganhos; "estou invencível" | Limites hard-coded; revisão trimestral | [[38_Betting_Psychology/DISCIPLINE_FRAMEWORK]] |
| **FOMO** | Apostar sem sinal porque "parece óbvio"; medo de perder oportunidade | Só sinais aprovados contam; logs auditáveis | [[38_Betting_Psychology/DISCIPLINE_FRAMEWORK]] |
| **Confirmation Bias** | Ignorar métricas negativas; procurar justificação | Dashboards automáticos; alertas objetivos | [[38_Betting_Psychology/EMOTIONAL_REGULATION]] |
| **Recency Bias** | Dar demasiado peso aos últimos resultados | Métricas rolling 50/100/500; não 5 | [[38_Betting_Psychology/EMOTIONAL_REGULATION]] |
| **Emotional Override** | "Sinto que esta vai entrar"; intuição vs sistema | Automação progressiva; zero apostas manuais fora do sistema | [[38_Betting_Psychology/TILT_MANAGEMENT]] |
| **Decision Fatigue** | Erros aumentam ao longo do dia; lapsos de atenção | Turnos; automação; one-click betting | [[38_Betting_Psychology/DISCIPLINE_FRAMEWORK]] |
| **Sunk Cost Fallacy** | Continuar estratégia falhada porque "já investi tempo" | Revisão obrigatória após X trades; kill switches | [[38_Betting_Psychology/EMOTIONAL_REGULATION]] |
| **Gambler's Fallacy** | "Depois de 3 vermelhos, vai sair preto" | Cada aposta independente; estatísticas reais | [[38_Betting_Psychology/TILT_MANAGEMENT]] |
| **Outcome Bias** | Julgar decisão pelo resultado (não pelo processo) | Revisões focadas em processo; não P&L diário | [[38_Betting_Psychology/DISCIPLINE_FRAMEWORK]] |

### 2.2 Detalhamento das Armadilhas

**Tilt (A Variável Mais Perigosa)**
- **Definição:** Estado emocional negativo que afeta julgamento racional
- **Causas:** Sequência de perdas, má sorte percebida, erros técnicos
- **Sinais:** Aumentar stakes, apostar sem sinal, irritabilidade, negação
- **Custo Histórico:** Estudos mostram 60-80% das perdas em trading ocorrem em tilt
- **Defesa:** Detecção automática, circuit breakers, pausas obrigatórias

**Overconfidence (O Inimigo Após Sucesso)**
- **Definição:** Excesso de confiança após sequência de ganhos
- **Causas:** Viés de seleção, atribuir sucesso a skill (não luck)
- **Sinais:** Aumentar stakes "temporariamente", ignorar sinais de risco
- **Custo:** Uma decisão em overconfidence pode destruir meses de trabalho
- **Defesa:** Limites hard-coded, revisão trimestral obrigatória

**FOMO (Fear Of Missing Out)**
- **Definição:** Medo de perder oportunidades, levando a decisões impulsivas
- **Causas:** Ver outros lucrarem, sensação de "urgência"
- **Sinais:** Apostar sem sinal completo, ignorar checklist
- **Custo:** Qualidade das apostas cai drasticamente
- **Defesa:** Sistema só executa sinais completos; logs impedem justificação

**Confirmation Bias (Procurar o que Queremos Ver)**
- **Definição:** Dar peso a evidências que confirmam crenças pré-existentes
- **Causas:** Ego, necessidade de estar "certo"
- **Sinais:** Ignorar métricas negativas, focar apenas em positives
- **Custo:** Estratégias falhadas continuam por mais tempo
- **Defesa:** Dashboards objetivos, alertas automáticos para métricas negativas

**Recency Bias (O Que Aconteceu Agora é Importante)**
- **Definição:** Dar peso excessivo a eventos recentes
- **Causas:** Memória curta, emocionalidade
- **Sinais:** "Últimos 5 trades foram bons, sistema funciona" (样本太小)
- **Custo:** Decisões baseadas em ruído, não sinal
- **Defesa:** Métricas rolling 50/100/500; nunca <30 trades

**Emotional Override (Intuição vs Sistema)**
- **Definição:** Substituir sistema quantitativo por "sentimento"
- **Causas:** Falta de confiança no sistema, ego
- **Sinais:** "Sinto que esta vai entrar", "dessa vez é diferente"
- **Custo:** Destrói a vantagem estatística; torna o sistema inútil
- **Defesa:** Automação progressiva; zero apostas manuais fora do sistema

**Decision Fatigue (Cansaço Mental)**
- **Definição:** Qualidade das decisões degrada com o tempo
- **Causas:** Longas sessões, multitasking, stress
- **Sinais:** Erros bobos, lapsos de atenção, irritabilidade
- **Custo:** Erros aumentam exponencialmente após 6-8h
- **Defesa:** Turnos de 4h, automação, one-click betting

**Sunk Cost Fallacy (Não Desistir)**
- **Definição:** Continuar estratégia falhada porque "já investi tempo"
- **Causas:** Aversão a perdas, ego
- **Sinais:** "Só mais um trade", "quase lá"
- **Custo:** Perdas acumuladas muito maiores que parar cedo
- **Defesa:** Kill switches automáticos, revisão obrigatória

**Gambler's Fallacy (A Lei dos Médios Não Existe)**
- **Definição:** Acreditar que eventos passados afetam eventos independentes
- **Causas:** Má compreensão de probabilidade
- **Sinais:** "Depois de 3 losses, vem win"
- **Custo:** Aumentar stakes após perdas (martingale disfarçado)
- **Defesa:** Cada aposta independente; estatísticas reais

**Outcome Bias (Julgar pelo Resultado)**
- **Definição:** Avaliar qualidade da decisão pelo resultado (não pelo processo)
- **Causas:** Simplificação mental
- **Sinais:** "Foi uma boa aposta porque ganhou" (mesmo sendo -EV)
- **Custo:** Repetir más decisões se deram sorte
- **Defesa:** Revisões focadas em processo; não P&L diário

---

## 3. SISTEMAS DE DEFESA

### 3.1 Automação de Sizing
- O sistema calcula stake. O operador nunca altera.
- Se o operador tentar alterar, o sistema bloqueia e loga.

### 3.2 Pausas Obrigatórias
- Após 3 perdas seguidas: pausa de 30 minutos
- Após 5 perdas seguidas: circuit breaker; revisão obrigatória
- Após 8h de operação: pausa de 1h (decision fatigue)

### 3.3 Coaching e Revisão
- Revisão semanal de métricas (não de resultados individuais)
- Foco no processo, não no outcome
- Meditação / mindfulness recomendada (não obrigatória)

---

## 4. DOCUMENTAÇÃO DETALHADA

- [[38_Betting_Psychology/TILT_MANAGEMENT]] → Detecção de tilt, prevenção, recuperação, protocolos
- [[38_Betting_Psychology/DISCIPLINE_FRAMEWORK]] → Framework de disciplina, checklists, accountability
- [[38_Betting_Psychology/EMOTIONAL_REGULATION]] → Regulação emocional, mindfulness, técnicas mentais
- [[38_Betting_Psychology/TEAM_DYNAMICS]] → Dinâmica de equipa, comunicação, suporte mútuo
- [[38_Betting_Psychology/DISCIPLINA_OPERACIONAL]] → Regras operacionais, override manual

---

## 5. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[08_Risk_Management/INDEX]] → Circuit breakers que protegem da psicologia
- [[22_Real_Money_Operations/INDEX]] → Regras operacionais anti-tilt
