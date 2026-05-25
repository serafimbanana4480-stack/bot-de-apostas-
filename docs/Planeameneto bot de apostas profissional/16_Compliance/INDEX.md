# 16_Compliance — INDEX

**ID:** `SEC-16` | **Fase:** #phase/3-10 | **Owner:** Compliance Officer | **Status:** #status/active

---

## 1. OBJETIVO

Garantir que o projeto opera dentro dos limites legais e regulatórios, minimizando risco de litígio, sanções, ou proibição de operação. O compliance não é obstáculo — é enabler de longevidade.

---

## 2. NOTAS FUNDAMENTAIS

- [[REGULAMENTACAO_PT]] — SRIJ, regime jurídico português, restrições
- [[REGULAMENTACAO_EU]] — GDPR, MiFID II (se aplicável), mercado europeu
- [[DISCLAIMERS]] — Templates de disclaimers de risco
- [[KYC_AML]] — Know Your Customer, Anti-Money Laundering
- [[PROCESSO_KYC_DETALHADO]] — Procedimentos operacionais KYC passo-a-passo
- [[AUDIT_TRAIL_COMPLIANCE]] — Provas de operação para autoridades
- [[AUDITORIA_INTERNA_PROCEDIMENTOS]] — Procedimentos de auditoria interna
- [[COMUNICACAO_AUTORIDADES]] — Protocolos de comunicação com reguladores
- [[RESPONSIBLE_GAMBLING]] — Compromissos de jogo responsável
- [[MONITORIZACAO_RISCO_JOGO]] — Detalhamento de monitorização de comportamento de risco

---

## 3. PRINCIPAIS RESTRIÇÕES (Portugal)

| Restrição | Implicação | Mitigação |
|-----------|------------|-----------|
| SRIJ regula operadores de apostas | Não podemos operar como "casa de apostas" | Operar como tipster/informador |
| Publicidade de apostas restrita | Limitações em promessas de lucro | Disclaimer absoluto; focar em transparência |
| Dados pessoais (GDPR) | Subscritores têm direitos de proteção | Consentimento explícito; dados minimizados |
| Betfair API disponível | Execução automática possível via API licenciada | Usar apenas Betfair Exchange (legal) |
| Impostos sobre ganhos | 28% sobre ganhos de apostas em Portugal | Consultoria fiscal; tracking rigoroso |

---

## 4. DISCLAIMER OBRIGATÓRIO (Template)

```
AVISO DE RISCO

Este serviço fornece análises estatísticas e informações sobre mercados 
de apostas desportivas. NÃO constitui aconselhamento financeiro nem 
investimento.

- Resultados passados NÃO garantem resultados futuros.
- Apostas desportivas envolvem risco de PERDA TOTAL do capital investido.
- O utilizador é o único responsável pelas suas decisões de apostas.
- Recomendamos que NÃO aposte mais do que pode dar-se ao luxo de perder.

CLV (Closed Line Value) e ROI apresentados são métricas históricas de 
transparência, não promessas de lucro.
```

**Este disclaimer deve aparecer em:**
- Canal Telegram (mensagem fixada)
- Página web de track record
- Termos de serviço
- Cada email de sinal (rodapé)

---

## 5. BACKLOG TÉCNICO

- [ ] Redigir Termos de Serviço completos
- [ ] Criar Privacy Policy (GDPR compliant)
- [ ] Implementar mecanismo de consentimento de subscritores
- [ ] Consultar advogado especializado em direito das apostas
- [ ] Criar procedimento de handling de reclamações

---

## 6. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[17_Legal/INDEX]] → Documentos legais completos
- [[02_Business_Model/INDEX]] → Modelo de negócio que o compliance protege
