# TPL-007 — Architecture Decision Record (ADR)

**ID:** `DEC-XXX`  
**Título:** *Título descritivo da decisão*  
**Data:** `YYYY-MM-DD`  
**Status:** *[Proposed / Accepted / Deprecated / Superseded by DEC-YYY]*  
**Autor:** *Nome*  
**Decisores:** *Nomes das pessoas que participaram na decisão*  
**Stakeholders Afetados:** *Equipas/pessoas impactadas*

---

## 1. RESUMO EXECUTIVO

| Campo | Descrição |
|-------|-----------|
| **Decisão** | *Resumo em 1 frase* |
| **Impacto** | *[Alto/Médio/Baixo]* |
| **Irreversibilidade** | *[Sim/Não - pode ser revertida?]* |
| **Custo de Mudança** | *[Alto/Médio/Baixo]* |

---

## 2. CONTEXTO E PROBLEMA

### 2.1 Contexto Atual
*[Descrever a situação, o sistema, ou o estado atual que levou a esta decisão ser necessária]*

### 2.2 Problema a Resolver
*[Definir claramente o problema. O que não está a funcionar? Que risco ou limitação existe?]*

**Sintomas do Problema:**
- *
- *

**Impacto se não resolvido:**
- *
- *

### 2.3 Forças em Jogo (Forces)
*[Factores que influenciaram a decisão - restrições, requisitos, preferências]*

| Força | Descrição | Prioridade |
|-------|-----------|------------|
| *F1* | *Ex: Escalabilidade* | *[Must/Should/Could]* |
| *F2* | *Ex: Custo* | *[Must/Should/Could]* |
| *F3* | *Ex: Time-to-market* | *[Must/Should/Could]* |

---

## 3. DECISÃO

### 3.1 Decisão Tomada
*[Descrever a decisão de forma clara, concisa e acionável. Alguém que leia isto deve saber exatamente o que foi decidido]*

**Decisão:** *Fazer X em vez de Y*

**Âmbito:** *Onde/ quando se aplica*

**Exceções:** *Quando não se aplica*

### 3.2 Exemplo/Implementação de Referência
```
[Exemplo concreto de como a decisão se manifesta no código/sistema]
```

---

## 4. RACIONAL (Por Que Esta Decisão?)

### 4.1 Argumentos Principais
1. **Argumento A:** *[Explicação com dados/evidência]*
2. **Argumento B:** *[Explicação com dados/evidência]*
3. **Argumento C:** *[Explicação com dados/evidência]*

### 4.2 Análise de Trade-offs

| Aspecto | Opção Escolhida | Impacto |
|---------|-----------------|---------|
| *Performance* | *[Melhor/Igual/Pior]* | *[Justificação]* |
| *Complexidade* | *[Maior/Igual/Menor]* | *[Justificação]* |
| *Custo* | *[Maior/Igual/Menor]* | *[Justificação]* |
| *Manutenibilidade* | *[Melhor/Igual/Pior]* | *[Justificação]* |

### 4.3 Princípios Aplicados
- *[Princípio de design ou arquitetura usado para justificar]*
- *[Ex: "Preferir composição sobre herança"]*

---

## 5. CONSEQUÊNCIAS

### 5.1 Consequências Positivas (Pros)
- ✅ *Consequência 1 com explicação do benefício*
- ✅ *Consequência 2 com explicação do benefício*
- ✅ *Consequência 3*

### 5.2 Consequências Negativas (Cons)
- ⚠️ *Consequência 1 com mitigação proposta*
- ⚠️ *Consequência 2 com mitigação proposta*

### 5.3 Riscos Introduzidos
| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| *Risco A* | *[Alta/Média/Baixa]* | *[Alto/Médio/Baixo]* | *[Ação]* |

---

## 6. ALTERNATIVAS CONSIDERADAS

### 6.1 Alternativa A: *[Nome]*
**Descrição:** *Como funcionaria*

| Critério | Alternativa A | Opção Escolhida |
|----------|---------------|-----------------|
| *Custo* | *€X* | *€Y* |
| *Performance* | *Z req/s* | *W req/s* |
| *Complexidade* | *[Alta/Média/Baixa]* | *[Alta/Média/Baixa]* |
| *Time-to-market* | *M meses* | *N meses* |

**Por que não escolhida:** *Justificação clara*

### 6.2 Alternativa B: *[Nome]*
**Descrição:** *Como funcionaria*

**Vantagens:**
- 

**Desvantagens:**
- 

**Por que não escolhida:** *Justificação clara*

### 6.3 Alternativa C: *[Nome]* (Status Quo)
**Descrição:** *Manter como está*

**Por que não escolhida:** *Justificação clara*

---

## 7. IMPLICAÇÕES E DEPENDÊNCIAS

### 7.1 Implicações para Outros Sistemas
*[Que outros componentes precisam de mudanças?]*

- [[SISTEMA-A]] — *[Mudança necessária]*
- [[SISTEMA-B]] — *[Mudança necessária]*

### 7.2 Mudanças de Processo
*[Processos que precisam de atualização]*
- *Ex: Deploy pipeline*
- *Ex: Monitorização*

### 7.3 Formação Necessária
*[Quem precisa de treino?]*
- *Equipa X — sobre Y*

---

## 8. PLANO DE IMPLEMENTAÇÃO

| Fase | Atividade | Responsável | Deadline |
|------|-----------|-------------|----------|
| 1 | *[Descrição]* | *[Nome]* | *YYYY-MM-DD* |
| 2 | *[Descrição]* | *[Nome]* | *YYYY-MM-DD* |
| 3 | *[Descrição]* | *[Nome]* | *YYYY-MM-DD* |

---

## 9. CRITÉRIOS DE SUCESSO

*[Como saberemos se a decisão foi a correta?]*

| Métrica | Baseline | Target | Data de Avaliação |
|---------|----------|--------|-------------------|
| *Métrica A* | *X* | *Y* | *YYYY-MM-DD* |

---

## 10. REVISÃO E DEPRECIAÇÃO

### 10.1 Data de Revisão
**Revisar em:** *YYYY-MM-DD* (recomendado: 6-12 meses após implementação)

### 10.2 Condições para Revisão Antecipada
- *[Condição que obriga a rever a decisão]*
- *[Ex: "Se custo exceder X% do orçamento"]*

### 10.3 Se Esta Decisão For Depreciada
**Substituída por:** *[Link para novo ADR se aplicável]*

**Razão da depreciação:** *[Por que mudou]*

---

## 11. REFERÊNCIAS

### 11.1 Documentos Relacionados
- [[DEC-YYY]] — *ADR relacionado anterior*
- [[DOC-XXX]] — *Documentação técnica relevante*

### 11.2 Recursos Externos
- *[Link para artigo, RFC, ou documentação externa]*
- *[Link para benchmark ou estudo de caso]*

---

## 12. HISTÓRICO

| Data | Versão | Evento | Autor |
|------|--------|--------|-------|
| *YYYY-MM-DD* | *0.1* | *Proposta inicial* | *Nome* |
| *YYYY-MM-DD* | *1.0* | *Aprovado* | *Nome* |
| *YYYY-MM-DD* | *1.1* | *Atualizado com learnings* | *Nome* |

---

## 13. APROVAÇÕES

| Papel | Nome | Assinatura | Data |
|-------|------|------------|------|
| **Arquiteto** | | | |
| **Tech Lead** | | | |
| **Product Owner** | | | |

---

**ADR Baseado em:** [Documenting Architecture Decisions - Michael Nygard](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
