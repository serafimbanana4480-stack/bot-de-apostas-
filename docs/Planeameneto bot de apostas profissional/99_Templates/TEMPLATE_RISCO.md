# TEMPLATE_RISCO — Identificação e Mitigação de Risco

**ID:** TPL-010 | **Versão:** v1.0 | **Data:** YYYY-MM-DD  
**Tags:** #type/risk #status/active #priority/[high|medium|low]

---

## 1. INFORMAÇÕES DO RISCO

| Campo | Valor |
|-------|-------|
| **ID do Risco** | *RIS-XXX* |
| **Título** | *Título descritivo do risco* |
| **Categoria** | *[técnico|negócio|operacional|legal|segurança]* |
| **Fase Afetada** | *#[phase/1-8]* |
| **Owner** | *Nome do responsável* |
| **Data de Identificação** | *YYYY-MM-DD* |

---

## 2. DESCRIÇÃO DO RISCO

### 2.1 O que é?
*Descreva o risco em 2-3 frases. O que pode acontecer de errado?*

### 2.2 Causa Raiz
*Quais são as causas subjacentes deste risco?*

### 2.3 Gatilho
*Quando/quem pode ativar este risco?*

---

## 3. AVALIAÇÃO DE IMPACTO

| Dimensão | Probabilidade | Impacto | Score |
|----------|--------------|---------|-------|
| Financeiro | [1-5] | [1-5] | *P × I* |
| Operacional | [1-5] | [1-5] | *P × I* |
| Reputacional | [1-5] | [1-5] | *P × I* |
| Técnico | [1-5] | [1-5] | *P × I* |
| **Risco Total** | | | *Soma dos scores* |

**Classificação Final:**
- [ ] Crítico (score >= 15)
- [ ] Alto (score 10-14)
- [ ] Médio (score 5-9)
- [ ] Baixo (score < 5)

---

## 4. MITIGAÇÃO

### 4.1 Estratégia
*[aceitar|evitar|transferir|mitigar]*

### 4.2 Ações de Mitigação

| # | Ação | Owner | Deadline | Status |
|---|------|-------|----------|--------|
| 1 | *Ação específica* | *Nome* | *YYYY-MM-DD* | *[pending|in_progress|done]* |
| 2 | *Ação específica* | *Nome* | *YYYY-MM-DD* | *[pending|in_progress|done]* |

### 4.3 Controles em Place

- [ ] *Controle 1*
- [ ] *Controle 2*

---

## 5. PLANO DE CONTINGÊNCIA

### 5.1 Se o Risco se Materializar...

**Passos Imediatos:**
1. *Passo 1*
2. *Passo 2*
3. *Passo 3*

**Comunicação:**
- Quem notificar: *@pessoa1, @pessoa2*
- Meio: *[Telegram|Email|Slack]*
- Template: *Referência a template de incidente*

---

## 6. MONITORIZAÇÃO

### 6.1 Indicadores de Alerta Precoce

| Indicador | Threshold | Frequência |
|-----------|-----------|------------|
| *Métrica 1* | *Valor* | *Diária/Semanal* |

### 6.2 Revisão

- **Próxima revisão:** *YYYY-MM-DD*
- **Frequência:** *[Mensal|Trimestral|Semestral]*

---

## 7. HISTÓRICO

| Data | Alteração | Autor |
|------|-----------|-------|
| *YYYY-MM-DD* | *Criado* | *Nome* |
| *YYYY-MM-DD* | *Atualizado status* | *Nome* |

---

## 8. LINKS CRUZADOS

- [[28_Failure_Scenarios/INDEX]] ← Cenários de falha relacionados
- [[26_Runbooks/INDEX]] → Runbooks de resposta
- *[[Outros documentos relacionados]]*

---

**Fim do Template de Risco**
