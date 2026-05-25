---
ID: LEG-007
tags: #status/active #legal #consumidor #protecao #direitos
---

# Proteções ao Consumidor - Direitos e Obrigações

## Objetivo
Documentar exaustivamente todos os direitos dos subscritores enquanto consumidores, as obrigações correspondentes do prestador do serviço, e os mecanismos de execução destes direitos em conformidade com a Diretiva 2011/83/UE (direitos dos consumidores), o Código de Defesa do Consumidor Português (Lei 24/96), e as legislações nacionais equivalentes dos outros Estados-Membros da UE.

## Direitos Fundamentais do Consumidor

### 1. Direito à Informação Pré-Contratual

**Base Legal:** Diretiva 2011/83/UE, Art. 5º e 6º; Lei 24/96, Art. 8º

**O que deve ser fornecido antes da contratação:**

| Informação | Obrigatória? | Quando Fornecer | Formato |
|------------|--------------|-----------------|---------|
| Identidade do prestador (nome, morada, NIPC) | Sim | Antes de pagamento | Site, ToS |
| Características principais do serviço | Sim | Antes de pagamento | Site, ToS |
| Preço total e todas as taxas | Sim | Antes de pagamento | Checkout, ToS |
| Meios de pagamento | Sim | Antes de pagamento | Checkout |
| Direito de livre resolução | Sim | Antes de pagamento | ToS, checkout |
| Duração mínima do contrato | Sim | Antes de pagamento | ToS |
| Condições de rescisão | Sim | Antes de pagamento | ToS |
| Existência e funcionalidade de meios técnicos digitais | Sim | Antes de pagamento | ToS |
| Relevância de interoperabilidade de conteúdo digital | Se aplicável | Antes de pagamento | ToS |

**Implementação:**
```
1. Página de preços com todos os planos e custos totais
2. Resumo de ToS no checkout (scrollable)
3. Checkbox obrigatório: "Li e aceito os Termos de Serviço"
4. Link direto para ToS completo
5. Resumo do direito de resolução no checkout
```

**Penalidade em Falta:**
- Coima até €10.000 (Portugal)
- Invalidade do contrato se informação essencial omitida
- Direito do consumidor à anulação do contrato

### 2. Direito de Livre Resolução (Cooling-off Period)

**Base Legal:** Diretiva 2011/83/UE, Art. 9º; Lei 24/96, Art. 10º

**Prazo:** 14 dias calendário após:
- Conclusão do contrato, OU
- Receção do serviço (se o consumidor não consentiu na prestação antes do fim do prazo)

**Exceções (não aplicável direito de resolução):**
- Serviços prestados integralmente com consentimento prévio do consumidor
- Serviços cujo preço dependa de flutuações do mercado
- Serviços de apostas/jogo (se aplicável - ver análise abaixo)

**Análise Específica para Serviço de Informação:**

O serviço de informação quantitativa de apostas NÃO está na lista de exceções do Art. 16º da Diretiva 2011/83/UE. Portanto, o direito de resolução aplica-se, MAS:

**Se o consumidor consentiu expressamente na prestação imediata:**
- Perde o direito de resolução após o serviço começar a ser prestado
- Consentimento deve ser explícito (não tácito)
- Prestador deve confirmar que o consumidor perdeu o direito

**Implementação:**
```
Checkbox no checkout:
[ ] Entendo que, ao consentir na prestação imediata do serviço, perco o direito
    de livre resolução de 14 dias após o início da prestação do serviço.
```

**Processo de Resolução:**
```
1. Subscritor solicita resolução via dashboard ou email
2. Sistema verifica se ainda dentro do prazo (14 dias)
3. Se dentro do prazo e não consentiu prestação imediata:
   a) Reembolso integral (100%)
   b) Cancelamento imediato do serviço
4. Se dentro do prazo mas consentiu prestação imediata:
   a) Verificar se serviço já prestado
   b) Se não prestado: reembolso integral
   c) Se já prestado: não reembolsável (mas pode cancelar)
5. Se fora do prazo: não reembolsável, mas cancelamento futuro
```

**Responsável:** Customer Success + Financeiro

### 3. Direito à Retirada do Consentimento

**Base Legal:** GDPR, Art. 7º, nº3

**O que pode ser retirado:**
- Consentimento para tratamento de dados (marketing, perfilamento)
- Consentimento para prestação imediata (se ainda não iniciada)

**Implementação:**
```
1. Dashboard → Configurações → Privacidade
2. Toggle para cada tipo de consentimento
3. Retirada efetiva em tempo real
4. Confirmação por email
```

**Responsável:** Sistema automático

### 4. Direito de Acesso aos Dados

**Base Legal:** GDPR, Art. 15º

**O que o subscritor pode solicitar:**
- Confirmação de se os seus dados são tratados
- Cópia de todos os dados pessoais tratados
- Finalidades do tratamento
- Destinatários dos dados
- Período de conservação

**Prazo de resposta:** 30 dias

**Formato:** JSON + CSV (portabilidade)

**Implementação:**
```
1. Subscritor solicita acesso via dashboard
2. Sistema compila todos os dados do subscritor
3. Gera arquivos JSON e CSV
4. Envia por email com link seguro (expira em 7 dias)
5. Regista pedido no audit trail
```

**Responsável:** Compliance Officer (manual se necessário) + Sistema

### 5. Direito à Retificação

**Base Legal:** GDPR, Art. 16º

**O que pode ser retificado:**
- Dados pessoais inexatos
- Dados incompletos

**Implementação:**
```
1. Subscritor edita dados no dashboard
2. Sistema valida alterações
3. Atualização em tempo real
4. Confirmação por email
5. Registo no audit trail
```

**Responsável:** Sistema automático

### 6. Direito ao Apagamento (Direito ao Esquecimento)

**Base Legal:** GDPR, Art. 17º

**Quando pode ser exercido:**
- Dados não são mais necessários para a finalidade
- Subscritor retira consentimento e não há outra base jurídica
- Subscritor opõe-se ao tratamento e não há interesse legítimo predominante
- Dados tratados ilicitamente
- Obrigação legal de apagamento

**Exceções (não pode apagar):**
- Obrigação legal (ex: dados fiscais por 10 anos)
- Exercício de direito de defesa em juízo
- Investigação de crime

**Implementação:**
```
1. Subscritor solicita apagamento
2. Sistema verifica obrigações de retenção
3. Se há obrigações:
   a) Pseudonimiza dados (substitui por ID)
   b) Retém apenas dados obrigatórios
   c) Notifica subscritor do apagamento parcial
4. Se não há obrigações:
   a) Elimina todos os dados
   b) Notifica subscritor
5. Regista no audit trail
```

**Responsável:** Compliance Officer

### 7. Direito à Portabilidade

**Base Legal:** GDPR, Art. 20º

**O que pode ser portado:**
- Dados pessoais fornecidos pelo subscritor
- Dados resultantes de tratamento com consentimento

**Formato:** Estruturado, comum, legível por máquina (JSON, CSV)

**Implementação:** Similar ao direito de acesso (ver acima)

**Responsável:** Sistema automático

### 8. Direito de Oposição

**Base Legal:** GDPR, Art. 21º

**O que pode ser oposto:**
- Tratamento baseado em interesse legítimo (ex: marketing)
- Profilagem

**Implementação:**
```
1. Dashboard → Configurações → Comunicação
2. Toggle para "Receber emails de marketing"
3. Oposição efetiva em tempo real
4. Confirmação por email
```

**Responsável:** Sistema automático

### 9. Direito a Não Ser Sujeito a Decisão Automatizada

**Base Legal:** GDPR, Art. 22º

**O que se aplica:**
- Decisões baseadas exclusivamente em tratamento automatizado que produzem efeitos jurídicos ou significativamente similares

**Análise para o serviço:**
- O sistema NÃO toma decisões automatizadas com efeitos jurídicos sobre o subscritor
- Recomendações de apostas são apenas informativas
- Decisões de pagamento/renovação são baseadas em contrato, não automatização

**Implementação:**
- Documentação de que não há decisões automatizadas com efeitos jurídicos
- Se houver no futuro: direito a intervenção humana, expressar ponto de vista, contestar

### 10. Direito a Reclamação

**Base Legal:** Lei 24/96, Art. 12º; Diretiva 2013/11/UE (RAL)

**Onde reclamar:**
- Diretamente ao prestador (obrigatório primeiro passo)
- Entidades de resolução alternativa de litígios (RAL)
- Autoridades de proteção do consumidor
- Tribunais

**Implementação:**
```
1. Formulário de reclamação no dashboard
2. Canal de email dedicado (reclamacoes@dominio.pt)
3. Prazo de resposta: 15 dias
4. Registo de todas as reclamações
5. Análise de padrões para melhoria contínua
```

**Responsável:** Customer Success + Compliance Officer

---

## Obrigações do Prestador

### 1. Obrigação de Boa Fé

**Base Legal:** Código Civil, Art. 762º

**O que implica:**
- Agir com honestidade e lealdade
- Não ocultar informações relevantes
- Não criar expectativas falsas
- Cumprir promessas feitas

**Implementação:**
- Comunicação honesta sobre riscos e limitações
- Transparência sobre performance histórica
- Não prometer lucros ou ROI garantido
- Cumprir prazos de resposta prometidos

### 2. Obrigação de Informação Contínua

**Base Legal:** Lei 24/96, Art. 8º

**O que deve ser comunicado:**
- Alterações ao serviço
- Alterações aos preços
- Alterações aos termos
- Interrupções de serviço
- Violações de dados

**Prazo:** Imediato ou conforme definido em ToS

**Implementação:**
- Email para todas as alterações materiais
- Banner no dashboard para interrupções
- Notificação CNPD em 72h para violações de dados

### 3. Obrigação de Qualidade

**Base Legal:** Lei 24/96, Art. 4º

**O que implica:**
- Serviço conforme ao contratado
- Ausência de defeitos que afetem a utilidade
- Adequação ao fim a que se destina

**Implementação:**
- SLA de uptime (99.5%)
- Testes de qualidade antes de lançamento
- Processo de correção de bugs
- Compensação por falhas graves

### 4. Obrigação de Confidencialidade

**Base Legal:** GDPR, Art. 5º, nº1, alínea f); Código Civil, Art. 809º

**O que deve ser protegido:**
- Dados pessoais dos subscritores
- Informação de pagamento
- Comportamento de jogo
- Correspondência

**Implementação:**
- Encriptação de dados em repouso e em trânsito
- Controlo de acesso a dados sensíveis
- Políticas de confidencialidade para equipa
- Auditorias de segurança regulares

### 5. Obrigação de Assistência Pós-Venda

**Base Legal:** Lei 24/96, Art. 9º

**O que deve ser fornecido:**
- Suporte técnico
- Esclarecimento de dúvidas
- Assistência na resolução de problemas

**Implementação:**
- Email de suporte (suporte@dominio.pt)
- FAQ no dashboard
- Tempo de resposta: 48h (email), 24h (subscritores PRO)
- Telefone para subscritores INSTITUCIONAIS

---

## Mecanismos de Resolução de Litígios

### 1. Resolução Direta

**Processo:**
```
1. Subscritor apresenta reclamação
2. Prestador analisa e responde em 15 dias
3. Se resolvido: caso encerrado
4. Se não resolvido: avançar para RAL
```

### 2. Resolução Alternativa de Litígios (RAL)

**Entidade em Portugal:** CNIACC (Centro Nacional de Informação e Arbitragem de Conflitos de Consumo)

**Vantagens:**
- Mais rápido que tribunal
- Menos formal
- Mais barato
- Decisão vinculativa para ambas as partes

**Processo:**
```
1. Subscritor submite pedido ao CNIACC
2. CNIACC notifica prestador
3. Ambas as partes apresentam argumentos
4. Mediador tenta acordo
5. Se acordo: encerrado
6. Se não acordo: arbitragem (árbitro decide)
7. Decisão final e vinculativa
```

**Custos:**
- Gratuito para consumidor
- Prestador paga taxa administrativa

**Implementação em ToS:**
```
"Para litígios até €5.000, as partes comprometem-se a submeter o conflito ao Centro
Nacional de Informação e Arbitragem de Conflitos de Consumo (CNIACC) antes de recorrer
a tribunal."
```

### 3. Tribunal

**Último recurso** após esgotamento de RAL

**Foro competente:** Tribunal do domicílio do consumidor (Bruxelas I bis, Art. 18º)

---

## Template de Resposta a Reclamação

```
Assunto: Resposta à reclamação #[Número] - [Data]

Caro(a) [Nome do Subscritor],

Agradecemos o seu contacto e a oportunidade de responder à sua reclamação.

[Descrição da reclamação]

Após análise, informamos que:

[Se procedente:]
- Reconhecemos o problema
- Apresentamos as nossas desculpas
- Medidas corretivas tomadas: [detalhes]
- Compensação oferecida: [detalhes]

[Se improcedente:]
- Explicação detalhada do porquê
- Referência a cláusulas contratuais relevantes
- Oferta de esclarecimento adicional

Caso não fique satisfeito(a) com esta resposta, pode reclamar junto do CNIACC
(www.consumidor.pt) ou da Autoridade de Segurança Alimentar e Económica (ASAE).

Com os melhores cumprimentos,

[Nome do Responsável]
[Cargo]
[Data]
```

---

## Métricas de Proteção ao Consumidor

### KPIs a Monitorizar

| KPI | Target | Frequência |
|-----|--------|------------|
| Tempo médio de resposta a reclamações | <48h | Mensal |
| Taxa de resolução na primeira contacto | >80% | Mensal |
| Taxa de satisfação com resolução | >4/5 | Trimestral |
| Número de reclamações ao CNIACC | <5/ano | Anual |
| Tempo médio de resposta a pedidos GDPR | <15 dias | Mensal |
| Taxa de reembolso DLR aceites | 100% | Mensal |

---

## Checklist de Proteção ao Consumidor

### Pré-Contratação
- [ ] Informação pré-contratual completa disponível
- [ ] Preços totais transparentes (sem taxas ocultas)
- [ ] Direito de resolução claramente explicado
- [ ] Termos de Serviço acessíveis e legíveis
- [ ] Checkbox obrigatório de aceitação

### Durante Contrato
- [ ] Faturas/recibos enviados pontualmente
- [ ] Acesso a dados pessoais disponível
- [ ] Mecanismo de cancelamento fácil
- [ ] Suporte responsivo
- [ ] Comunicação de alterações atempada

### Pós-Contratação
- [ ] Processo de reembolso claro
- [ ] Canal de reclamações acessível
- [ ] Informação sobre RAL disponível
- [ ] Resposta a reclamações em 15 dias
- [ ] Retenção de dados apenas pelo período necessário

---

## Links Cruzados

- [[17_Legal/TERMS_OF_SERVICE]] - Contrato que incorpora direitos do consumidor
- [[17_Legal/PRIVACY_POLICY]] - Direitos GDPR detalhados
- [[16_Compliance/DISCLAIMERS]] - Informação de risco
- [[17_Legal/JURISDICAO_ESTRUTURA]] - Foro competente para litígios
- [[18_Operations/DOCUMENTACAO_OPERACIONAL]] - Processos de suporte ao cliente